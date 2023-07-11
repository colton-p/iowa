import time
import itertools
from typing import Any
from result import Result
from instance import Instance
import random

from dataclasses import dataclass


from collections import defaultdict
from cuts.cut_set import CutSet
from cuts import generator as CutGenerator
from models.cut import CutMip
from models.flow import FlowMip

import networkx as nx

class RandNaiveSolver:
    def __init__(self, I, iters) -> None:
        self.I = I
        self.iters = iters
        pass

    def solve(self, time_limit=None):
        best = Result('undef', False, False, 99999999, {}, {})

        for i in range(self.iters):
            rslt = NaiveSolver(self.I, 'rand').solve(0)
            if rslt > best: best = rslt
        return best

class NaiveSolver:
    def __init__(self, I: Instance, pick) -> None:
        self.I = I
        if pick == 'max':
            self.pick_fn = lambda nodes: max(nodes, key=lambda v: I.weight([v]))
        elif pick == 'rand':
            self.pick_fn = lambda nodes: random.choice(nodes)
        else:
            assert False, pick
    
    def _pull_group(self, H, k):
        target = sum(H.nodes[v]['pop'] for v in H.nodes) // k
        group = set()
        w = lambda nodes: sum(H.nodes[v]['pop'] for v in nodes)
        while True:
            if group:
                adjacent = {*itertools.chain(*(H[u] for u in group))} - group
            else:
                adjacent = set(H.nodes)
            candidates = [
                v for v in adjacent
                if (w([v]) + w(group) <= target) and 
                nx.is_connected(H.subgraph(set(H.nodes) - group - {v}))]
            if not candidates:
                break
            to_add = self.pick_fn(candidates)
            group.add(to_add)
        return group

    def solve(self, time_limit=None):

        groups = {}
        H = self.I.G.copy()
        K = self.I.n_groups
        for i in range(K - 1):
            groups[i] = self._pull_group(H, K - i)
            H = H.subgraph(set(H.nodes) - groups[i])
        
        groups[K - 1] = set(H.nodes)

        return Result.from_groups(self.I, groups)

class ModelSolver:
    def __init__(self, model) -> None:
        self.model = model
    
    def solve(self, time_limit=10, msg_lvl=0):
        t0 = time.time()
        model = self.model
        model.prepare()
        print(f'lp: {len(model.lp.rows)} rows {len(model.lp.cols)} cols')
        t1 = time.time()
        model.lp.simplex()
        t2 = time.time()
        model.lp.integer(tm_lim=1000*time_limit, msg_lev=msg_lvl)
        t3 = time.time()
        timings = {
            'prepare': int(1000*(t1-t0)),
            'simplex': int(1000*(t2-t1)),
            'integer': int(1000*(t3-t2)),
        }

        return Result.from_model(model, timings)

def _find_invalid(G, groups):
    complete = set(G.nodes) == set().union(*groups.values())
    if not complete:
        print(set(G.nodes) - set().union(*groups.values()))

    for nodes in groups.values():
        H = G.subgraph(nodes)
        if nx.is_connected(H): continue

        comps = sorted(nx.connected_components(H), key=lambda x: len(x))
        return list(comps[0])[0], list(comps[1])[0]

    assert False
    return None

class IterCutSolver:
    @staticmethod
    def from_strat(I: Instance, S):
        cut_set = CutSet()
        if S.min_cuts:
            cut_set += CutSet(CutGenerator.all_min_cuts(I))
        if S.z_cuts:
            cut_set += CutSet(CutGenerator.all_z_cuts(I))

        return IterCutSolver(
            I,
            cut_set,
            S.iters,
            S.sep_depth
        )

    def __init__(self, I: Instance, cut_set, cut_iters, sep_depth) -> None:
        self.cut_set = cut_set
        self.I = I
        self.cut_iters = cut_iters
        self.sep_depth = sep_depth
    
    def solve(self, time_limit=10):
        best = Result('undef', False, False, 99999999, {}, {})
        o_limit = time_limit

        added_pairs = defaultdict(lambda: self.sep_depth-1)
        (u,v) = None, None

        for i in range(self.cut_iters):
            print(self.I.state, i, '----')
            time_limit = o_limit
            for j in range(5):
                print(f'{self.I.state} ...solve {j} with limit {time_limit} and {len(self.cut_set.cuts)} cuts')
                rslt = self.solve_one(time_limit)

                if rslt.valid:
                    print(f'OK✅ score={rslt.score} best={best.score}')
                else:
                    print('NG ❌')
                print(f'\t status={rslt.lp_status}')

                if rslt > best: best = rslt

                if (rslt.lp_status == 'undef' or (rslt.valid and rslt.lp_status == 'feas')):
                    time_limit *= 2
                else:
                    time_limit = o_limit
                    break


            if rslt.valid and rslt.lp_status == 'opt':
                break

            if not rslt.valid:# and rslt.lp_status == 'feas':
                (u, v) = _find_invalid(self.I.G, rslt.groups)
                print(f'\t invalid pair: {u} {v}')

            if rslt.valid and rslt.lp_status == 'feas':
                (u, v) = random.choice(self.I.non_adj_nodes)
                print(f'\t random pair: {u} {v}')
            
            assert u and v
            added_pairs[(u, v)] += 1
            new_cuts = list(CutGenerator.separators_for(self.I, u, v, depth=added_pairs[(u,v)]))
            self.cut_set += new_cuts
            print(f'\t {len(new_cuts)} cuts added depth {added_pairs[(u,v)]}')
            print('')
        
        return best
    
    def solve_one(self, time_limit):
        model = CutMip(self.I, cut_set=self.cut_set, separators=False, min_cuts=False, z_cuts=False, cross_vars=False)
        return ModelSolver(model).solve(time_limit)



@dataclass
class Strat:
    model: str = 'flow'
    time_limit: int = 10

    min_cuts: bool = False
    z_cuts: bool = False
    cross_vars: bool = False

    separators: bool = False
    sep_depth: int = None

    iters: int = None

    @property
    def name(self):
        bools = []
        if self.min_cuts: bools += ['min_cuts']
        if self.z_cuts: bools += ['z_cuts']
        if self.cross_vars: bools += ['cross_vars']
        if self.separators: bools += ['separators']

        ints = []
        if self.sep_depth: ints += [f'sep_depth={self.sep_depth}']
        if self.iters: ints += [f'iters={self.iters}']

        args = []
        if bools: args += [';'.join(bools)]
        if ints: args += [';'.join(ints)]
        args = ' '.join(args).strip()


        return f'{self.model}{self.time_limit}[{args}]'


def pick_solver(I: Instance, S: Strat):
    if S.model==('greedy'):
        return NaiveSolver(I, 'max')
    if S.model.startswith('rand'):
        return RandNaiveSolver(I, S.iters)
    if S.model == 'flow':
        model = FlowMip(I)
        return ModelSolver(model)
    
    if S.model == 'cut':
        model = CutMip(
            I,
            min_cuts=S.min_cuts,
            z_cuts=S.z_cuts,
            cross_vars=S.cross_vars,
            separators=S.separators,
            sep_depth=S.sep_depth
        )
        return ModelSolver(model)
    
    if S.model == 'iter_cut':
        return IterCutSolver.from_strat(I, S)