import json
import sys
import csv

states = ["ak", "al", "ar", "az", "ca", "co", "ct", "de", "fl", "ga", "ia", "id", "il", "in", "ks", "ky", "la", "ma", "md", "me", "mi", "mn", "mo", "ms", "mt", "nc", "nd", "ne", "nh", "nj", "nm", "nv", "ny", "oh", "ok", "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "va", "vt", "wa", "wi", "wv", "wy"]


with open('../data/data.json', 'r') as f:
    all_data = json.load(f)


for state in states:
    print(state)
    with open(f'../svgs/{state}.svg', 'r') as f:
        svg = f.read()
    
    data_json = all_data[state]

    with open('main.js', 'r') as f:
        main_js = f.read()

    with open('template.html', 'r') as f:
        data = f.read()
        data = data.replace('<!--SVG-->', svg)
        data = data.replace('<!--STATE-->', f'"{state}"')
        data_js = f'const COUNTY_DATA = {data_json}; const ALL_STATES={states};'
        data = data.replace('<!--DATA_JS-->', data_js)
        data = data.replace('<!--MAIN_JS-->', main_js)

    with open(f'../docs/{state}.html', 'w') as f:
        f.write(data)

def write_index():

    with open('best.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        scores = {line['st']: line for line in reader}
    
    cols = ['states', 'counties', 'k = 2', 'k = 4']
    header = ''.join(f'<th>{v}</th>' for v in cols)

    rows = []
    for state in scores:

        opt2 = 'opt' if scores[state]['2opt'] else ''
        opt4 = 'opt' if scores[state]['4opt'] else ''
        (score2, score4) = scores[state]['2score'], scores[state]['4score']
        cols = [
            f'<td><a href="{state}.html">{state}</a></td>',
            f'<td>{len(all_data[state])}</td>',
            f'<td class="{opt2}">{score2}</td>',
            f'<td class="{opt4}">{score4}</td>',
        ]
        td_s = ''.join(cols)

        row = f'<tr id="{state}">{td_s}</tr>'
        rows += [row]

    body = '\n'.join(rows)
    script = """
        const tds = Array.from(document.getElementsByTagName('tr'));
        tds.forEach(td => {
            if(!td.id) { return; }

            [ [2, 2], [3, 4]].forEach( ([child_ix, group_size]) => {

                const table = Number(td.children[child_ix].innerText);
                const mine = localStorage.getItem(`${td.id}-${group_size}`);
                if (mine && Number(mine)  < table) {
                    td.children[child_ix].innerText = mine;
                    td.children[child_ix].classList.add('mine');
                }
            });
        });
    
    """
    index = f"""
    <html>
    <style>
        .opt {{ background-color: peachpuff; }}
        .mine {{ background-color: palegreen; }}
    </style>
    <body>
    <table>
    <thead>{header}</thead>
    <tbody>
        {body}
    </tbody>
    </table>
    </body>
    <script>
    {script}
    </script>
    </html>
    """

    with open('../html/index.html', 'w') as f:
        f.write(index)
write_index()