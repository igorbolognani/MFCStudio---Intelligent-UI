"""Find conventional MFC configurations in methods and full-text indexes.

Discovery only. A hit is a document to inspect and may refer to an intervention,
multiple different arms, or a cited experiment. This script does not admit arms.
"""
from concurrent.futures import ThreadPoolExecutor
from csv import DictReader
from pathlib import Path
from hashlib import sha256
from urllib.parse import urlencode
import argparse
import json
import runpy

SURVEY = runpy.run_path(str(Path(__file__).with_name("survey-conventional-arms.py")))
FAMILIES = {
    "F1": ("cloth", "acetate", "platinum", "air"),
    "F2": ("paper", "acetate", "platinum", "air"),
    "F3": ("brush", "acetate", "activated", "air"),
    "F4": ("brush", "acetate", "platinum", "air"),
    "F5": ("brush", "glucose", "platinum", "air"),
    "F6": ("felt", "acetate", "ferricyanide", "dual"),
}
TERMS = {
    "cloth": ("carbon cloth", "graphite cloth", "carbon fiber cloth", "carbon fibre cloth", "carbon fabric"),
    "paper": ("carbon paper", "graphite paper", "TGP-H-060", "TGP-H-090"),
    "brush": ("carbon brush", "carbon brushes", "graphite brush", "carbon fiber brush", "carbon fibre brush",
              "graphite fiber brush", "graphite fibre brush", "brush anode", "brush anodes"),
    "felt": ("carbon felt", "graphite felt", "graphite fiber felt", "carbon fibre felt", "carbon fiber felt"),
    "acetate": ("acetate", "CH3COONa", "acetic acid"),
    "glucose": ("glucose", "dextrose", "C6H12O6"),
    "platinum": ("platinum", "Pt", "Pt/C"),
    "activated": ("activated carbon", "active carbon", "AC/PTFE", "activated charcoal"),
    "ferricyanide": ("ferricyanide", "hexacyanoferrate", "K3Fe(CN)6"),
    "air": ("air cathode", "air cathodes", "air breathing", "air cathodic", "air cathode MFC",
            "air-breathing cathode", "gas diffusion cathode"),
    "dual": ("dual chamber", "two chamber", "double chamber", "H type", "two compartment", "two chambers"),
}
MFC = '("microbial fuel cell" OR "microbial fuel cells" OR "microbial fuel-cell")'
DATE = "FIRST_PDATE:[1990-01-01 TO 2026-11-06]"


def clause(terms, field=None):
    prefix = f"{field}:" if field else ""
    return "(" + " OR ".join(f'{prefix}"{term}"' for term in terms) + ")"


def queries():
    for family, (anode, donor, cathode, topology) in FAMILIES.items():
        method = [clause(TERMS[key], "METHODS") for key in (anode, donor, cathode)]
        yield f"{family}-methods", " AND ".join((MFC, DATE, *method))
        # Topology and complete wording can occur in figures or results.
        body = [clause(TERMS[key]) for key in (anode, donor, cathode, topology)]
        yield f"{family}-body", " AND ".join((MFC, DATE, *body))


def search(name, query, cache):
    cursor = "*"
    found = []
    pages = []
    while cursor:
        path = cache / "queries" / name / f"{len(pages) + 1:03d}.json"
        url = SURVEY["API"] + "/search?" + urlencode({
            "query": query, "format": "json", "pageSize": 250,
            "cursorMark": cursor, "resultType": "lite",
        })
        raw = SURVEY["download"](url, path, json.loads)
        page = json.loads(raw)
        hits = page["hitCount"]
        if pages and hits != pages[0]["hits"]:
            raise ValueError(f"Hit count changed while paging {name}")
        batch = page["resultList"]["result"]
        found.extend(batch)
        pages.append({"sha256": sha256(raw).hexdigest(), "hits": hits, "returned": len(batch)})
        if len(found) >= hits:
            break
        next_cursor = page.get("nextCursorMark")
        if not batch or not next_cursor or next_cursor == cursor:
            raise ValueError(f"Truncated search {name}: {len(found)}/{hits}")
        cursor = next_cursor
    return {"id": name, "query": query, "hits": hits, "pages": pages}, found


def key(record):
    return record.get("doi", "").strip().lower() or record.get("pmcid") or f'{record["source"]}:{record["id"]}'


def replay_acquisition(cache, manifest):
    """Recover the frozen JATS corpus, keeping download failures explicit."""
    with manifest.open(encoding="utf-8", newline="") as file:
        items = [
            {"pmcid": row["pmcid"], "key": row["key"], "sample_id": row["source"],
             "expected_sha256": row["sha256"]}
            for row in DictReader(file, delimiter="|") if row["pmcid"] != "NR"
        ]
    with ThreadPoolExecutor(max_workers=5) as workers:
        results = list(workers.map(lambda row: SURVEY["acquire_article"](cache, row), items))
    changed = [
        row["pmcid"] for row in results if row["expected_sha256"] != "NR"
        and row.get("sha256") != row["expected_sha256"]
    ]
    SURVEY["save_json"](cache / "methods-acquisition-replay.json", {
        "records": results, "unconfirmed_originals": changed,
    })
    if changed:
        raise ValueError(f"{len(changed)} original versions could not be confirmed. See replay manifest.")
    print(f'{sum(row["full_text"] for row in results)}/{len(results)} JATS recovered')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--replay", type=Path, help="Reacquire the PMCID set from the frozen acquisition table.")
    args = parser.parse_args()
    if args.replay:
        replay_acquisition(args.cache, args.replay)
        return
    items = list(queries())
    found = {}
    logs = []
    with ThreadPoolExecutor(max_workers=4) as workers:
        results = workers.map(lambda args_: search(*args_, args.cache), items)
        for log, records in results:
            logs.append(log)
            print(log["id"], log["hits"], flush=True)
            for record in records:
                identifier = key(record)
                current = found.setdefault(identifier, {"record": record, "routes": []})
                if record.get("pmcid") and not current["record"].get("pmcid"):
                    current["record"] = record
                current["routes"].append(log["id"])
    SURVEY["save_json"](args.cache / "section-search.json", {
        "date": "2026-11-06", "database": "Europe PMC", "queries": logs,
        "unique": len(found), "with_pmcid": sum(bool(x["record"].get("pmcid")) for x in found.values()),
        "records": [found[k] for k in sorted(found)],
    })


if __name__ == "__main__":
    main()
