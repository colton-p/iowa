from instance import Instance
import glpk
import itertools

from cuts import generator as CutGenerator
from cuts import cross_vars

from models.base_model import BaseModel

class CutMip(BaseModel):
    def __init__(self, I: Instance, cut_set=None, min_cuts=True, separators=True, z_cuts=True, cross_vars=False, sep_depth=None):
        self.cut_set = cut_set
        self.min_cuts = min_cuts
        self.z_cuts = z_cuts
        self.cross_vars = cross_vars

        self.separators = separators

        self.sep_depth = sep_depth

        super().__init__(I)

    def reconstruct(self):
        lp = self.lp
        return {
            ix: [v for v in self.I.G if lp.cols[self.xvars[(v, ix)]].primal]
            for ix in range(self.I.n_groups)
        }
    
    def add_cut(self, row, cut):
        (ix, (u, v), cut_set) = cut
        row.bounds = None, 1
        x_ui, x_vi = self.var_map[(u, ix)], self.var_map[(v, ix)]
        row.matrix = [(x_ui, 1), (x_vi, 1)] + [(self.var_map[(z, ix)], -1) for z in cut_set]

    def prepare(self):
        (G, n_groups) = self.I.G, self.I.n_groups
        I = self.I; rows_for = self.rows_for
        self.lp = lp = glpk.LPX()
        lp.obj.maximize = True

        # one col for each group x node
        self.var_map = {}
        for (ix, (i, v)) in enumerate(itertools.product(range(n_groups), G.nodes)):
            lp.cols.add(1)
            col = lp.cols[-1]
            col.name = 'x{%s,%d}' % (v, i)
            col.bounds = 0, 1
            col.kind = int
            self.var_map[(v, i)] = ix
        var_map = self.var_map

        # groups are sorted by weight
        for (row, grp_ix) in rows_for(range(n_groups - 1)):
            row.name = f'{grp_ix} is sorted'
            row.bounds = None, 0

            this_group = [(var_map[(v, grp_ix)], G.nodes[v]['pop']) for v in G.nodes]
            next_group = [(var_map[(v, 1+grp_ix)], -G.nodes[v]['pop']) for v in G.nodes]
            row.matrix = this_group + next_group
        #print(f'groups: {n_groups-1} rows')

        # each node in one group
        for (row,v) in rows_for(G.nodes):
            row.name = f'{v} is in one group'
            row.bounds = 1, 1
            row.matrix = [(var_map[(v, grp_ix)], 1) for grp_ix in range(n_groups)]
        #print(f'nodes: {len(G)} rows')

        import time
        ## cuts ##
        cut_types = (
            ('cut_set', lambda _x: self.cut_set),
            ('min_cuts', CutGenerator.all_min_cuts),
            ('z_cuts', CutGenerator.all_z_cuts),
            ('separators', lambda I: CutGenerator.all_separators(I, depth=self.sep_depth))
        )
        for (name, generator) in cut_types:
            if not getattr(self, name): continue
            t0 = time.time()
            n_rows = 0
            for (row, cut) in rows_for(generator(I)):
                n_rows += 1
                self.add_cut(row, cut)
            #print(f'{name}: {n_rows} rows; {time.time() - t0}')

        ## cross ineqs
        if self.cross_vars:
            t0 = time.time()
            n_rows = nnz = 0
            for (row, cross_ineq) in rows_for(cross_vars.cross_var_permutations(I)):
                n_rows += 1
                nnz += len(cross_ineq)
                row.bounds = None, 3
                row.matrix = [(var_map[x_ui], 1) for x_ui in cross_ineq]
            #print(f'cross ineq: {n_rows} rows; {nnz} non-zero; {time.time()-t0}')

        #print('')
        #print('cols', len(lp.cols))
        #print('rows', len(lp.rows))

        lp.obj[:] = [G.nodes[v]['pop'] for v in G.nodes] + [0 for i in range(len(G) * (n_groups-1))]

        self.lp = lp
        self.xvars = var_map
        return (lp, var_map)
    
