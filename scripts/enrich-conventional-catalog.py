"""Fetch exact publication metadata without expanding the catalogue."""
from argparse import ArgumentParser
from pathlib import Path
from csv import DictReader
from concurrent.futures import ThreadPoolExecutor
from gzip import open as gzopen
from urllib.parse import urlencode
import runpy

parser = ArgumentParser(description=__doc__)
parser.add_argument("cache", type=Path)
parser.add_argument("provider", choices=("epmc", "alex"))
args = parser.parse_args()
home = args.cache.resolve()
repo = Path(__file__).resolve().parents[1]
h = runpy.run_path(str(repo/'scripts/search-external-arms.py'))
base = h['BASE']
provider = args.provider
with gzopen(base/'coverage/register.psv.gz','rt',encoding='utf-8') as f:
    new = list(DictReader(f,delimiter='|'))
with (base/'excluded-972.psv').open(encoding='utf-8') as f:
    old = list(DictReader(f,delimiter='|'))
if provider == 'epmc':
    ids = sorted({x for r in old for x in r['pmids'].split() if x.isdecimal()} | {r['pmid'] for r in new if r['pmid'].isdecimal()})
    step=50; endpoint=h['EUROPE']
    def query(ids):
        return {'query':'SRC:MED AND ('+' OR '.join('EXT_ID:'+x for x in ids)+')','format':'json','resultType':'core','pageSize':step}
else:
    ids = sorted({x for r in old for x in r['doi_aliases'].split() if x.startswith('10.')} | {r['doi'] for r in new if r['doi'].startswith('10.')})
    step=55; endpoint=h['ALEX']
    def query(ids):
        return {'filter':'doi:'+'|'.join('https://doi.org/'+x for x in ids),'select':'id,doi,display_name,ids,publication_year,abstract_inverted_index,type,is_retracted,best_oa_location,locations','per_page':step}

def fetch(batch):
    index, selection = batch
    file=home/provider/f'{index:03d}.json'
    try:
        data=h['get_json'](endpoint+'?'+urlencode(query(selection)),file)
        rows=data['resultList']['result'] if provider=='epmc' else data['results']
        actual={str(r.get('pmid') or r.get('id')) if provider=='epmc' else h['doi_key'](r.get('doi')) for r in rows}
        if not actual <= set(selection):
            raise ValueError(f'unexpected identities ({len(actual-set(selection))})')
        return index,len(selection),len(rows),None
    except (OSError,ValueError,KeyError) as e:
        return index,len(selection),0,str(e)[:120]
with ThreadPoolExecutor(max_workers=5) as pool:
    for r in pool.map(fetch,enumerate(ids[i:i+step] for i in range(0,len(ids),step))):
        print(*r, flush=True)

if provider == "epmc":
    catalog_module = runpy.run_path(str(repo / "scripts/build-conventional-catalog.py"))
    catalog = catalog_module["historical"]()
    missing = sorted(doi for (kind, doi), key in catalog.aliases.items()
                     if kind == "doi" and catalog.rows[key]["title"] == "NR")
    if missing:
        params = {"query": " OR ".join(f'DOI:"{doi}"' for doi in missing),
                  "resultType": "core", "pageSize": max(25, len(missing)), "format": "json"}
        h["get_json"](endpoint + "?" + urlencode(params), home / "epmc/missing-titles.json")
