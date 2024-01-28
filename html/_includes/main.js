const COLORS = ['darkgreen', 'blue', 'darkorange', 'purple', 'red', 'brown'];
const N_GROUPS = Number.parseInt(new URLSearchParams(document.location.search).get('k')) || 4;

const FMT = {
    human: (v) => new Intl.NumberFormat('en', { notation: 'compact' }).format(v),
    long: (v) => new Intl.NumberFormat('fr-FR').format(v),
}


function isValid() {
    const group_ixs = Array(N_GROUPS).fill(0).map((v, ix) => ix);

    const bad_groups = group_ixs.filter(ix => !isGroupConnected(ix));
    
    return [bad_groups.length === 0, bad_groups];
}

function isGroupConnected(grp) {
    const seen = {};
    function dfs(u) {
        seen[u] = true;
        const adj = COUNTY_DATA[u].adj.filter(v => GROUPS[v] === grp && !seen[v] && COUNTY_DATA[v]);
        adj.forEach(dfs);
    }
    const inGroup = Object.keys(GROUPS).filter(k => GROUPS[k] === grp);
    if (inGroup.length === 0) { return false; }
    dfs(inGroup[0]);

    return inGroup.sort().join(';') === Object.keys(seen).sort().join(';')
}


const makeToggle = (cid) => () => {
    toggleGroup(cid);
    updateDisplay([cid]);
}

function toggleGroup(cid) {
    const old_grp = GROUPS[cid];
    const new_grp = (old_grp+1) % N_GROUPS;
    GROUPS[cid] = new_grp;
}

const onMouseOver = function() {
    const el = document.getElementById('hover-text');
    const {name, pop} = COUNTY_DATA[this.id];

    el.textContent = `${name}\n${FMT.long(pop)}`;
}

function updateDisplay(cids) {
    cids.forEach(cid => {
        const grp = GROUPS[cid];
        const color = COLORS[grp]

        document.getElementById('list-'+cid).style.color = color;
        document.getElementById(cid).style.fill = color;
    });

    const rslt = sumGroups();
    Object.entries(rslt).forEach(([group, pop]) => {
        const row = [FMT.human(pop), FMT.long(pop), FMT.long(Math.floor(pop - TOTAL / N_GROUPS))];
        //textContent = FMT.human(pop) + "\t" + FMT.long(pop) + "\t" + Math.floor(pop - TOTAL / N_GROUPS);
        document.getElementById(`pop-${group}`).innerHTML =  row.map(v => `<td>${v}</td>`).join('')
    });

    const lsKey = `${STATE}-${N_GROUPS}`;
    const score = Math.floor(TOTAL/N_GROUPS - Math.min(...Object.values(rslt)));
    let bestScore = localStorage.getItem(lsKey) || '';
    const [valid, badGroups] = isValid();
    document.getElementById('score-box').innerHTML = `score: <b>${FMT.long(score)}</b>`;
    if (valid) {
        document.getElementById('valid-box').textContent = '✅ valid';
    } else {
        document.getElementById('valid-box').textContent = `❌ group ${badGroups[0]} not connected`
    }
    if (valid && Number(bestScore || TOTAL) > score) {
        bestScore = score;
        localStorage.setItem(lsKey, score);
        localStorage.setItem(lsKey+'-groups', JSON.stringify(friendlyGroups()));
    }

    document.getElementById('best-score-box').textContent = 'best: ' + FMT.long(bestScore);
}

function sumGroups() {
    const rslt = Object.fromEntries(Array(N_GROUPS).fill(0).map((v, ix) => [ix, 0]));
    Object.entries(GROUPS).forEach(([id, group]) => {
        const pop = COUNTY_DATA[id].pop;
        rslt[group] += pop;
    });

    return rslt;
}

function friendlyGroups() {
    const rslt = Object.fromEntries(Array(N_GROUPS).fill(0).map((v, ix) => [ix, []]));
    Object.entries(GROUPS).forEach(([id, grp]) => {
        rslt[grp].push(COUNTY_DATA[id].name);
    });
    return rslt;
}

function setup() {
    const county_els = Array.from(document.getElementsByTagName('path'));
    const county_ids = county_els.map(e => e.id);

    // map handlers
    county_els.forEach(path_el => {
        path_el.onmouseover = onMouseOver.bind(path_el);
        path_el.onclick = makeToggle(path_el.id);
    });

    // sorted list
    const sorted_counties = county_ids.map(cid => ({...COUNTY_DATA[cid], id: cid}));

    sorted_counties.sort((a,b) => b.pop - a.pop);
    //sorted_counties.sort((a,b) => b.name > a.name ? -1 : 1);

    const list_el = document.getElementById('sorted-list');
    sorted_counties.forEach(({id, name, pop}) => {
        const li = document.createElement("li");
        li.id = 'list-'+id;
        li.onclick = makeToggle(id);
        li.appendChild(document.createTextNode(name + ": " + FMT.long(pop)));
        list_el.appendChild(li) 

        li.onmouseover = () => {
            document.getElementById(id).style.stroke= 'red';
        }
        li.onmouseleave = () => {
            document.getElementById(id).style.stroke= null;
        }
    });

    const groups_el = document.getElementById('group-pops');
    for (let ix = 0; ix < N_GROUPS; ++ix) {
        const el = document.createElement("tr");
        el.id = 'pop-'+ix;
        el.style.color = COLORS[ix];
        groups_el.appendChild(el);
    }

    const total_pop = sorted_counties.reduce((acc, r) => acc + r.pop, 0);
    const groups = Object.fromEntries(county_ids.map(id => [id, 0]));

    return [groups, total_pop];
};

const [GROUPS, TOTAL] = setup();
updateDisplay(Object.keys(GROUPS));