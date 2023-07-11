from instance import Instance
from cuts import separators

from networkx.algorithms.connectivity import minimum_st_node_cut


# A cut is (ix, (u,v), cut_vars)
# ix - group number
# (u, v) - nodes with positive coeff
# cut_vars - nodes with neg coeeff

def all_min_cuts(I: Instance):
    for (u,v) in I.non_adj_nodes:
        for cut in min_cuts_for(I, u, v):
            yield cut

def all_separators(I: Instance, depth=4):
    for (u,v) in I.non_adj_nodes:
        for cut in separators_for(I, u, v, depth=depth):
            yield cut

def all_z_cuts(I: Instance):
    for (u,v) in I.non_adj_nodes:
        for cut in z_cuts_for(I, u, v):
            yield cut

def min_cuts_for(I: Instance, u, v):
    cut_set = minimum_st_node_cut(I.G, u, v, auxiliary=I.auxiliary, residual=I.residual)
    for ix in range(I.n_groups):
        yield (ix, (u, v), tuple(cut_set))

def separators_for(I: Instance, u, v, depth=4):
    seps = separators.separators(I.G, u, v, depth=depth)
    for sep in seps:
        for ix in range(I.n_groups):
            yield(ix, (u, v), tuple(sep))

def z_cuts_for(I: Instance, u, v):
    S = set(minimum_st_node_cut(I.G, u, v, auxiliary=I.auxiliary, residual=I.residual))
    def ssp(z):
        c1 = I.all_pairs_shortest_path[u][z]
        if v in c1: return c1
        c2 = I.all_pairs_shortest_path[z][v]

        return c1[:-1] + c2

    # TODO use Instance props
    def w(nodes):
        return sum(I.G.nodes[s]['pop'] for s in nodes)
    wG = w(I.G.nodes)

    for ix in range(I.n_groups):
       cut_set = S - {z for z in S if w(ssp(z)) > wG / (I.n_groups - ix)}
       yield( ix, (u, v), tuple(cut_set))



