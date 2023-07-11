import csv
import json


def populations():
    with open('co-est2021-alldata.csv', 'r', encoding='latin1') as csvfile:
        reader = csv.DictReader(csvfile)

        return {
            'c' + record['STATE'] + record['COUNTY']: int(record['ESTIMATESBASE2020'])
            for record in reader
        }

def county_names():
    with open('fips-names.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='|')
        return {
            'c' + record['STATEFP'] + record['COUNTYFP']: record['COUNTYNAME'].replace(' County', '')
            for record in reader
        }

def state_names():
    with open('fips-names.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='|')
        return {
            record['STATEFP']: record['STATE'].lower()
            for record in reader
        }

from collections import defaultdict
def adjacencies():
    ret = defaultdict(set)
    cur = None
    for line in open('county_adjacency.txt', 'r', encoding='latin1'):
        if line.startswith('\t'):
            assert cur
            adj = 'c'+line.split('\t')[-1].strip()
            if cur != adj:
                ret[cur].add(adj)
                ret[adj].add(cur)
        else:
            cur = 'c'+line.split('\t')[1]
        
    return ret

pop = populations()
name = county_names()
state = state_names()
adj = adjacencies()

data = defaultdict(dict)
for code in sorted(set(name.keys()) & set(pop.keys())):
    st = state[code[1:3]]
    data[st][code] = {
        'name': name[code],
        'pop': pop[code],
        'adj': list(sorted(adj[code])),
    }

json.dump(data, open('data.json', 'w'),indent=2)