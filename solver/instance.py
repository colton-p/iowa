from dataclasses import dataclass
from functools import cached_property
import itertools
import networkx as nx

###############
@dataclass
class Instance:
    G: nx.Graph
    n_groups: int
    state: str = ''

    def weight(self, nodes):
        return sum(self.G.nodes[v]['pop'] for v in nodes)

    @cached_property
    def total_weight(self):
        return self.weight(self.G.nodes)
    
    @cached_property
    def non_adj_nodes(self):
        return [
            (u, v)
            for (u, v) in itertools.combinations(sorted(self.G.nodes), 2)
            if v not in self.G[u]
        ]

    @cached_property
    def auxiliary(self):
        from networkx.algorithms.connectivity import build_auxiliary_node_connectivity
        return build_auxiliary_node_connectivity(self.G)

    @cached_property
    def residual(self):
        from networkx.algorithms.flow import build_residual_network
        return build_residual_network(self.auxiliary, "capacity")
    
    @cached_property
    def all_pairs_shortest_path(self):
        def weight_func(s, t, _):
            return self.G.nodes[s]['pop']
        return dict(nx.all_pairs_dijkstra_path(self.G, weight=weight_func))
 