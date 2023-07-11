
import networkx as nx

def comp_with_vertex(G, S, v):
    G_drop_S = G.subgraph(G.nodes - S)
    return G.subgraph(nx.node_connected_component(G_drop_S, v))


def close_separator(G: nx.Graph, a, b):
    S = set(G.neighbors(a))
    C_b = comp_with_vertex(G, S, b)

    return {u for u in S if any(v in C_b for v in G[u])}


def _separators(G, a, b, T):
    Tp = set()
    for S in T:
        C_a = comp_with_vertex(G, S, a)

        non_adj = {x for x in S if a not in G[x]}
        for x in non_adj:
            D = close_separator(G.subgraph(list(C_a.nodes) + [x]), x, a)
            C_ap = comp_with_vertex(C_a, D, a)

            N = {u for u in S if not any((v in C_ap) for v in G[u])}

            Sp = (set(S) | D) - N
            Tp.add(tuple(Sp))

    return Tp

def separators(G, a, b, depth=4):
    depth = depth or 100
    S = close_separator(G, b, a)
    T = {tuple(S)}

    for _i in range(depth):
        Q = _separators(G, a, b, T)
        if Q <= T:
            break
        T |= Q

    return tuple(set(s) for s in T)
