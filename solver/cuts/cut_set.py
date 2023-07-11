class CutSet:
    def __init__(self, cuts=None):
        if cuts:
            self.cuts = set(cuts)
        else:
            self.cuts = set()

    def __iter__(self):
        return iter(self.cuts)
    
    def __add__(self, other):
        if isinstance(other, CutSet):
            return CutSet(self.cuts | other.cuts)
        return CutSet(self.cuts | set(other))

