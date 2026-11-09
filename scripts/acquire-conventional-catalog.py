"""Acquire documents for existing catalogue entries through indexed public locations."""
from argparse import ArgumentParser
from http.client import HTTPException
from pathlib import Path
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlsplit
import runpy

parser = ArgumentParser(description=__doc__)
parser.add_argument("cache", type=Path)
parser.add_argument("batch")
parser.add_argument("--limit", type=int, default=120)
parser.add_argument("--restore", action="store_true", help="Reacquire previously documented bodies.")
parser.add_argument("--topic", action="store_true", help="Select titles mentioning microbial fuel cells.")
parser.add_argument("--resume", action="store_true", help="Checkpoint a completed request without repeating previous failures.")
args = parser.parse_args()
if not args.batch.replace("-", "").isalnum() or args.limit < 1:
    parser.error("Use a positive limit and an alphanumeric batch name")
home = args.cache.resolve()
repo = Path(__file__).resolve().parents[1]
acq=runpy.run_path(str(repo/'scripts/acquire-external-register.py'))
h=acq['RECONCILE']
base=h['BASE']
read=h['read_table']
load=h['read_json']
save=h['SEARCH']['save_json']
route = args.batch
limit = args.limit
ledger = home / f"retrieval-{route}.json"
if ledger.exists():
    print(f"Reusing completed batch {route}")
    raise SystemExit(0)
register={r['key']:r for r in read(base/'coverage/register.psv.gz')}
statuses={r['key']:r for r in read(base/'coverage/frozen-pass/status.psv.gz')}
doi={r['doi']:r['key'] for r in register.values() if r['doi']!='NR'}
pmid={r['pmid']:r['key'] for r in register.values() if r['pmid']!='NR'}
urls=defaultdict(set)
pmc={}
for file in sorted((home/'epmc').glob('*.json')):
    for r in load(file)['resultList']['result']:
        key=pmid.get(r.get('pmid') or r['id'])
        if key:
            if r.get('pmcid') and r.get('isOpenAccess')=='Y':
                pmc[key]=r['pmcid']
            for u in (r.get('fullTextUrlList') or {}).get('fullTextUrl',[]):
                if u.get('availabilityCode') in ('OA','F') and u.get('url'):
                    urls[key].add(u['url'])
for file in sorted((home/'alex').glob('*.json')):
    for r in load(file)['results']:
        key=doi.get(h['SEARCH']['doi_key'](r.get('doi')))
        if key:
            for loc in [r.get('best_oa_location'),*(r.get('locations') or [])]:
                if loc and loc.get('is_oa'):
                    urls[key].update(x for x in (loc.get('pdf_url'),loc.get('landing_page_url')) if x)
if args.restore:
    selected=set()
    for f in (base/'coverage/acquisition.psv',base/'coverage/frozen-pass/acquisition.psv'):
        for r in read(f):
            u=r.get('access_url') or r.get('url')
            if r['key'] in statuses and statuses[r['key']]['decision']=='unreviewed' and u and u.startswith('https://'):
                urls[r['key']].add(u)
                selected.add(r['key'])
else:
    selected={k for k in set(urls)|set(pmc) if statuses[k]['decision'] in ('pending','unreviewed') and statuses[k]['document_state'] not in ('xml','pdf','html')}
for prior_queue in sorted(home.glob("queue-*.json")):
    if prior_queue.stem != f"queue-{route}":
        selected -= {row["key"] for row in load(prior_queue)}
if args.topic:
    selected = {key for key in selected if h["PRIMARY_TOPIC"].search(register[key]["title"])}


def rank(k):
    s=statuses[k]
    scores=[int(x.rsplit(':',1)[1]) for x in s['term_overlap'].split() if ':' in x]
    direct=any('.pdf' in u.lower() or 'bitstream' in u for u in urls[k])
    return (s['nonprimary_signal']=='yes',s['decision']!='pending',not bool(pmc.get(k) or direct),-max(scores,default=0),s['family_route']=='NR',k)
queue_path = home / f"queue-{route}.json"
if queue_path.exists():
    rows = load(queue_path)
else:
    rows = [
        register[key] | {"doi": None if register[key]["doi"] == "NR" else register[key]["doi"],
                         "pmcid": pmc.get(key),
                         "urls": sorted(url for url in urls[key] if urlsplit(url).scheme == "https")}
        for key in sorted(selected, key=rank)[:limit]
    ]
    save(queue_path, rows)
if len(rows) != len({row["key"] for row in rows}) or any(row["key"] not in register for row in rows):
    raise ValueError("Queue contains a duplicate or unknown publication")
print(f"{route}: {len(rows)} publications scheduled", flush=True)


def pull(row):
    if args.resume:
        local = "articles/" + acq["sha256"](row["key"].encode()).hexdigest()[:16]
        folder = home / local
        attempts = load(folder / "attempts.json") if (folder / "attempts.json").exists() else []
        if (not (folder / "acquired.json").exists()
                and set(acq["routes"](row)) <= {item["url"] for item in attempts}):
            return row | {"format": None, "local": local, "attempts": attempts}
    try:
        return acq["acquire"](home, row)
    except (HTTPException, UnicodeError) as error:
        local = "articles/" + acq["sha256"](row["key"].encode()).hexdigest()[:16]
        path = home / local / "attempts.json"
        attempts = load(path) if path.exists() else []
        return row | {"format": None, "local": local, "attempts": attempts,
                      "acquisition_error": type(error).__name__}


results = []
with ThreadPoolExecutor(max_workers=14) as pool:
    for task in as_completed([pool.submit(pull, row) for row in rows]):
        results.append(task.result())
        if len(results) % 50 == 0:
            print(f"{len(results)} of {len(rows)} processed", flush=True)
save(ledger, sorted(results, key=lambda row: row["key"]))
print(route, dict(Counter(row["format"] for row in results)), flush=True)
