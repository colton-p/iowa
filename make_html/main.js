const COLORS = ['darkgreen', 'blue', 'darkorange', 'purple', 'red', 'brown'];
const N_GROUPS = Number.parseInt(new URLSearchParams(document.location.search).get('k')) || 4;

const FMT = {
    human: (v) => new Intl.NumberFormat('en', { notation: 'compact' }).format(v),
    long: (v) => new Intl.NumberFormat('fr-FR').format(v),
}


function isValid() {
    const group_ixs = Array(N_GROUPS).fill(0).map((v, ix) => ix);

    return group_ixs.every(isGroupConnected);
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
        document.getElementById(`pop-${group}`).textContent = FMT.human(pop) + "\t" + FMT.long(pop) + "\t" + Math.floor(pop - TOTAL / N_GROUPS);
    });

    const lsKey = `${STATE}-${N_GROUPS}`;
    const score = Math.floor(TOTAL/N_GROUPS - Math.min(...Object.values(rslt)));
    let bestScore = localStorage.getItem(lsKey) || '';
    const valid = isValid();
    document.getElementById('score-box').textContent = score + "\t" + valid;
    if (valid && Number(bestScore || TOTAL) > score) {
        bestScore = score;
        localStorage.setItem(lsKey, score);
        localStorage.setItem(lsKey+'-groups', JSON.stringify(friendlyGroups()));
    }

    document.getElementById('best-score-box').textContent = 'best: ' + bestScore
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
    const footer = document.getElementById('footer')
    ALL_STATES.forEach((st, ix) => {
        const a = document.createElement("a");
        a.href = `${st}.html`;
        a.style='margin: 5px;';
        a.innerText = st;
        footer.appendChild(a);
        if (ix == 24) { footer.appendChild(document.createElement('br'))}
    });

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
        const el = document.createElement("p");
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