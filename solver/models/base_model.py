from instance import Instance
from result import Result

import time

class BaseModel:
    def __init__(self, I: Instance) -> None:
        self.I = I
    
    def rows_for(self, collection):
        for data in collection:
            self.lp.rows.add(1)
            row = self.lp.rows[-1]
            yield (row, data)
        
    @property
    def obj_value(self):
        return self.lp.obj.value

    def score(self):
        opt_val = int(self.obj_value)
        target = int(self.I.total_weight / self.I.n_groups)
        score = target - opt_val

        return (score, opt_val)

