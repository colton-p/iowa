
## iowa

Problem: Divide a state of n counties into k contiguous groups such that the populations of the groups are balanced.
- maximize the size of the smallest group

[Try the interactive maps.](https://colton-p.github.io/iowa/)

try:
```
cli_solve.py ct -k 2 --model flow
cli_solve.py me -k 2 --model cut --cut_min --cut_cross

cli_solve.py ia -k 2 --model rand --iters 10
```

model options:
- greedy: build groups by picking largest ungrouped county
- rand: build groups randomly; --iters to control number of runs (non-optimized)
- flow: integer program with flow-based constraints
    - easy to construct problem instance
    - slower to solve
    - solutions are always valid
    - alternate flow solution (s4.1 Miyazawa) much slower
    - can show optimality
- cut: integer program with cut-based constraints
    - harder to construct problem instance
    - faster to solve
    - solutions by not be valid (groups not connected), if not enough cuts/constraints are used
    - can show optimality


cut types:
- cut_min: min u,v node cut for each uv
- cut_z: based on min u,v paths (see Miyazawa 21)
- cut_cross: pairs (u,v) (s,t) without disjoint u->v and s->t paths
    - (e.g. opposite corners of a 4-cycle on a planar graph)
    - (see Miyazawa 21)
- separators: all sets separating u,v (see Kloks 93)
    - generally a very large set
    - cut_sep_depth to control steps in generating algorithm

refs:
- "Partitioning a graph into balanced connected classes: Formulations, separation and experiments", Miyazawa et al (2021)
- "Finding all minimal separators of a graph", Kloks and Kratsch (1993)
