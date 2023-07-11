
from dataclasses import dataclass
import dataclasses
from functools import cached_property
from instance import Instance

import networkx as nx

def is_complete(G, groups):
    grouped_nodes = set().union(*groups.values())
    return set(G.nodes) == grouped_nodes

def is_connected(G, groups):
    return all(
        nodes and nx.is_connected(G.subgraph(nodes))
        for nodes in groups.values()
    )

@dataclass
class Result:
    @staticmethod
    def from_groups(I, groups):
        min_group = min(groups.values(), key=lambda x: I.weight(x))
        return Result(
            lp_status='feas',
            complete=is_complete(I.G, groups),
            connected=is_connected(I.G, groups),
            score=int(I.total_weight / I.n_groups) - I.weight(min_group),
            groups=groups,
            timings={}
        )

    @staticmethod
    def from_model(model, timings):
        groups = model.reconstruct()
        return Result(
            lp_status=model.lp.status_m,
            complete=is_complete(model.I.G, groups),
            connected=is_connected(model.I.G, groups),
            score=model.score()[0],
            groups=groups,
            timings=timings
        )

    # I: Instance
    lp_status: str
    connected: bool
    complete: bool
    score: int
    groups: dict
    timings: dict

    def sort_key(self):
        lp = {'opt': 2, 'feas': 1}.get(self.lp_status, 0)
        return (self.valid, lp, -self.score)

    def __gt__(self, other):
        return self.sort_key() > other.sort_key()

    def as_dict(self):
        return {
            'valid': self.valid,
            'score': self.score,
            'complete': self.complete,
            'connected': self.connected,
            'lp_status': self.lp_status,
            'groups': {k: list(v) for (k,v) in self.groups.items()},
            'timings': self.timings,
        }



    @property
    def valid(self):
        return all((
            self.lp_status in ['feas', 'opt'],
            self.complete,
            self.connected,
        ))
    
    def pretty_print(self):
        G = self.I.G
        print(self.timings)
        for (ix, group) in self.groups.items():
            good = group and nx.is_connected(G.subgraph(group))
            print(ix, self.I.weight(group), good, sorted(group, key=lambda x: -G.nodes[x]['pop']))

        print('---')
        print(self.score)
        print('OK✅' if self.valid else 'NG ❌')
        print(self.lp_status)