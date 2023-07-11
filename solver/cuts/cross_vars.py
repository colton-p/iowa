import itertools
import networkx as nx

from instance import Instance

def cross_var_permutations(I: Instance):
    for (s, t, u, v) in all_cross_vars(I):
        for (f, g) in itertools.permutations(range(I.n_groups), 2):
            yield ((s, g), (t, g), (u, f), (v, f))

def all_cross_vars(I: Instance):
    cross_var_candidates = {
        (s,t): set(cross_vars_for(I, s, t))
        for (s,t) in I.non_adj_nodes
    }
    
    cross_vars = []
    for (s,t) in cross_var_candidates:
        uvs = cross_var_candidates[(s,t)]
        cross_vars += [(s,t,u,v) for (u, v) in uvs if (s,t) in cross_var_candidates[(u,v)]]
    
    return cross_vars

def cross_vars_for(I: Instance, s, t):
    paths = nx.node_disjoint_paths(I.G, s, t, auxiliary=I.auxiliary, residual=I.residual)

    g_nodes = set(I.G.nodes)
    good_pairs = set(itertools.combinations(sorted(g_nodes - {s,t}), 2))
    subgraphs = (I.G.subgraph(g_nodes - set(path)) for path in paths)

    for H in subgraphs:
        for comp in nx.connected_components(H):
            good_pairs -= set(itertools.combinations(sorted(comp), 2))

    return [(u, v) for (u, v) in good_pairs if v not in I.G[u]]

