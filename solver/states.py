import json

import networkx as nx

def build_graph(state):
    def check_adj(adj):
        for k in adj:
            assert k not in adj[k], k
            for v in adj[k]:
                assert v in adj, (k, v)
                assert k in adj[v], (k, v)

    data = json.load(open('../data/data.json'))[state]

    names = {k: r['name'].lower().replace('-', '') for (k, r) in sorted(data.items())}
    pop = {names[k]: int(r['pop']) for (k,r) in data.items()}
    adj = {names[k]: [names[x] for x in r['adj'] if x in names] for (k,r) in data.items()}
    check_adj(adj)

    G = nx.Graph(adj)
    for u in G.nodes:
        G.nodes[u]['pop'] = pop[u]

    return G


def all_states():
    data = json.load(open('../data/data.json'))
    for state in sorted(data, key=lambda x: len(data[x])):
        yield (state, len(data[state]))