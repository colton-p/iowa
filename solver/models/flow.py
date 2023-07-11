from models.base_model import BaseModel

import networkx as nx
import glpk


class FlowMip(BaseModel):
    def reconstruct(self):
        D = self.D; G = self.I.G
        P = nx.Graph([e for e in self.D.edges if self.lp.cols[self.yvars[e]].primal])

        if not P: return {}

        return {s[-1]: nx.node_connected_component(P, s) - {s} for s in sorted(D.nodes - G.nodes)}

    @property
    def obj_value(self):
        return round(1000*self.lp.obj.value)

    # TODO use rows_for
    # TODO G -> D is a method
    def prepare(self):
        I = self.I; G = I.G
        D = nx.DiGraph(I.G)
        for ix in range(I.n_groups):
            source = f's_{ix}'
            D.add_edges_from([(source, v) for v in G])
        for u in I.G.nodes:
            D.nodes[u]['pop'] = I.G.nodes[u]['pop'] / 1000
        
        self.D = D
        self.lp = lp = glpk.LPX()
        lp.obj.maximize = True

        fvars = {}
        for (ix, a) in enumerate(D.edges):
            lp.cols.add(1)
            col = lp.cols[-1]
            col.name = f'f_{a}'
            col.bounds = 0, None
            fvars[a] = ix

        yvars = {}
        for (ix, a) in enumerate(D.edges):
            lp.cols.add(1)
            col = lp.cols[-1]
            col.name = f'y_{a}'
            col.bounds = 0, 1
            col.kind = int
            yvars[a] = ix + len(D.edges)
        
        for a in yvars:
            assert lp.cols[yvars[a]].name == f'y_{a}'
        for a in fvars:
            assert lp.cols[fvars[a]].name == f'f_{a}'
        
        for grp_ix in range(I.n_groups - 1):
            lp.rows.add(1); row = lp.rows[-1]
            row.name = f's_{grp_ix} is sorted'
            row.bounds = None, 0

            this_group = [(fvars[e], 1) for e in D.out_edges(f's_{grp_ix}')]
            next_group = [(fvars[e], -1) for e in D.out_edges(f's_{grp_ix+1}')]
            row.matrix = this_group + next_group

        for v in I.G.nodes:
            lp.rows.add(1); row = lp.rows[-1]
            row.name = f'{v} consumes w(v) flow'
            row.bounds = D.nodes[v]['pop'], D.nodes[v]['pop']

            in_flow = [(fvars[e], 1) for e in D.in_edges(v)]
            out_flow = [(fvars[e], -1) for e in D.out_edges(v)]
            row.matrix = in_flow + out_flow

        wG = sum(D.nodes[v]['pop'] for v in G.nodes)
        for e in D.edges:
            lp.rows.add(1); row = lp.rows[-1]
            row.name = f'{e} is feasible'
            row.bounds = None, 0
            row.matrix = [(fvars[e], 1), (yvars[e], -wG)]
        
        for s_i in D.nodes - G.nodes:
            lp.rows.add(1); row = lp.rows[-1]
            row.name = f'{s_i} sends on only one edge'
            row.bounds = None, 1
            row.matrix = [(yvars[e], 1) for e in D.out_edges(s_i)]

        for v in G.nodes:
            lp.rows.add(1); row = lp.rows[-1]
            row.name = f'{v} receives on only one edge'
            row.bounds = None, 1
            row.matrix = [(yvars[e], 1) for e in D.in_edges(v)]


        obj_cols = {fvars[e] for e in D.out_edges('s_0')}
        lp.obj[:] = [1 if ix in obj_cols else 0 for ix in range(len(lp.cols))]

        self.lp = lp
        self.fvars = fvars
        self.yvars = yvars
        self.D = D
        return (lp, fvars, yvars, D)

