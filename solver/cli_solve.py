
import argparse
import json

from instance import Instance
from result import Result
import networkx as nx
import glpk

from models.flow import FlowMip
from models.cut import CutMip
from solvers import ModelSolver, IterCutSolver, Strat, pick_solver

def check_adj(adj):
    for k in adj:
        assert k not in adj[k], k
        for v in adj[k]:
            assert v in adj, (k, v)
            assert k in adj[v], (k, v)

def build_graph(state):
    data = json.load(open('../data/data.json'))[state]

    names = {k: r['name'].lower().replace('-', '') for (k, r) in sorted(data.items())}
    pop = {names[k]: int(r['pop']) for (k,r) in data.items()}
    adj = {names[k]: [names[x] for x in r['adj'] if x in names] for (k,r) in data.items()}
    check_adj(adj)

    G = nx.Graph(adj)
    for u in G.nodes:
        G.nodes[u]['pop'] = pop[u]

    return G

def check_groups(G, groups):
    connected = all(
        nodes and nx.is_connected(G.subgraph(nodes))
        for nodes in groups.values()
    )
    complete = set(G.nodes) == set().union(*groups.values())

    #if not connected:
    #    print('!!! not connected')
    #if not complete:
    #    print('!!! not complete')

    return complete and connected

def solve_state(state, args, n_groups=4):
    I = Instance(n_groups=n_groups, G=build_graph(state))
    return solve_inst(I, args)

def solve_inst(I, args):
    S = Strat(
        model=args.model,
        time_limit=args.limit,
        iters=args.iters,
        min_cuts=args.cut_min,
        z_cuts=args.cut_z,
        cross_vars=args.cut_cross,
        separators=args.cut_seps,
        sep_depth=args.cut_sep_depth,
    )

    G = I.G
    print(G)

    slv = pick_solver(I, S)
    if isinstance(slv, ModelSolver):
        rslt = slv.solve(time_limit=args.limit, msg_lvl=glpk.LPX.MSG_ALL)
    else:
        rslt = slv.solve(time_limit=args.limit)

    print('\n------------------------------------------\n')

    for (ix, group) in rslt.groups.items():
        print(ix, I.weight(group), nx.is_connected(I.G.subgraph(group)), group)
    print(rslt.timings)
    print('lp:', rslt.lp_status)
    print('OK✅' if rslt.valid else 'NG ❌')
    print(rslt.score)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('state')
    parser.add_argument('-k', '--groups', type=int, default=4)
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--model', choices=['cut', 'flow', 'greedy', 'rand', 'iter_cut'], default='cut')
    parser.add_argument('--iters', type=int, default=10)
    
    parser.add_argument('--cut_min', action='store_true', default=False)
    parser.add_argument('--cut_z', action='store_true', default=False)
    parser.add_argument('--cut_cross', action='store_true', default=False)
    parser.add_argument('--cut_seps', action='store_true', default=False)
    parser.add_argument('--cut_sep_depth', type=int, default=4)

    args = parser.parse_args()
    solve_state(state=args.state, n_groups=args.groups, args=args)
