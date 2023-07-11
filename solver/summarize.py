import json

from collections import defaultdict
d = defaultdict(str)

states = []
names = set()

for row in json.load(open('out.json')):
    if row['k'] != 4: continue
    st = row['state']
    name = row['strat']['name']
    if ' ]' in name: continue
    if st not in states: states.append(st)
    names.add(name)

    if row['result']['valid']:
        val = str(row['score'])
        if  row['result']['lp_status'] == 'opt':
            val += '*'
        #val = row['result']['lp_status']
    else:
        val = 'x'
    d[(st, name)] = val

names = sorted(names, key=lambda x: (x[0], len(x)))
line = ['st', *(n for n in names)]
print(','.join(line))
for st in states:
    line = [st, *(d[(st, n)] for n in names)]
    print(','.join(line))

