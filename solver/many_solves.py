from instance import Instance
from result import Result

from models.flow import FlowMip
from models.cut import CutMip

from solvers import ModelSolver, IterCutSolver, NaiveSolver, RandNaiveSolver, pick_solver, Strat

from cli_solve import build_graph
import json
import glpk

from dataclasses import dataclass
import dataclasses

def solve(
    I: Instance,
    S: Strat
):
    solver = pick_solver(I, S)
    rslt = solver.solve(S.time_limit)

    out = {
        'state': I.state,
        'k': I.n_groups,
        'score': rslt.valid and rslt.score or None,
        'strat': {'name': S.name} | dataclasses.asdict(S),
        'result': rslt.as_dict()
    }

    return (out, rslt)


strats = [
    Strat(model='greedy-max'),
    Strat(model='rand100'),
    #Strat(model='rand10'),
    #Strat(model='rand100'),
    #Strat(model='iter_cut', min_cuts=True, sep_depth=4, cut_iters=10),
    Strat(model='flow', time_limit=10),
    #Strat(model='flow', time_limit=100),
    #Strat(model='cut'),
    #Strat(model='cut', min_cuts=True),
    #Strat(model='cut', min_cuts=True, z_cuts=True),
    Strat(model='cut', min_cuts=True, z_cuts=True, cross_vars=True),
    #Strat(model='cut', min_cuts=True, z_cuts=True, cross_vars=True, separators=True, sep_depth=1),
]

data = json.load(open('../data/data.json'))
instances = (
    Instance(state=state, n_groups=4, G=build_graph(state))
    for state in 
    sorted(data, key=lambda x: len(data[x]))
    if state not in ['de', 'dc', 'hi', 'ak']  and 59 <= len(data[state]) <= 300
)

import itertools
for (I, S) in itertools.product(instances, strats):
    print(I.state, S.name)
    all_out = json.load(open('out.json', 'r'))
    json.dump(all_out, open('out2.json', 'w'))
    (out, rslt) = solve(I, S)

    print('\t', '✅' if rslt.valid else '❌', rslt.lp_status, rslt.score)

    json.dump(all_out + [out], open('out.json', 'w'), indent=2)

# min cuts
# z cuts
# min cuts + z cuts + cross vars

# separators (depth)

# flow
# flow2

# iterative cuts