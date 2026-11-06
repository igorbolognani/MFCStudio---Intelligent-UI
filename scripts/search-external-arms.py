"""Resume discovery outside the frozen, 972-article MFC collection.

Candidate metadata and search pages are cached. Admission requires human review.
"""
from argparse import ArgumentParser
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from csv import DictReader, DictWriter
from gzip import compress
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, unquote
from urllib.request import Request, urlopen
import json
import re
import time
import unicodedata

BASE = Path(__file__).resolve().parents[1] / "research/conventional-arms/external-expansion"
ALEX = "https://api.openalex.org/works"
CROSSREF = "https://api.crossref.org/works"
EUROPE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EUROPE_REST = EUROPE.removesuffix("/search")
MFC = '("microbial fuel cell" OR "microbial fuel cells")'
FAMILIES = {
    "F1": (("carbon cloth", "graphite cloth", "woven carbon"), "acetate", ("platinum", "Pt/C"), "air cathode"),
    "F2": (("carbon paper", "Toray", "TGP-H"), "acetate", ("platinum", "Pt/C"), "air cathode"),
    "F3": (("graphite fiber brush", "carbon brush", "brush anode"), "acetate", ("activated carbon", "AC/PTFE"), "air cathode"),
    "F4": (("graphite fiber brush", "carbon brush", "brush anode"), "acetate", ("platinum", "Pt/C"), "air cathode"),
    "F5": (("graphite fiber brush", "carbon brush", "brush anode"), "glucose", ("platinum", "Pt/C"), "air cathode"),
    "F6": (("carbon felt", "graphite felt"), "acetate", ("ferricyanide", "hexacyanoferrate"), "two chamber"),
}
SELECT = ",".join(("id", "doi", "display_name", "publication_year", "type", "ids", "is_retracted",
                   "primary_location", "best_oa_location", "locations", "authorships"))
CITATION_SEEDS = {
    "F1": (24993129, 28662640), "F2": (36500961, 34835851, 18589979),
    "F3": (30406217, 31618815), "F4": (22572637,),
    "F5": (35009526, 38887865), "F6": (36231599, 26378546),
}


def doi_key(value):
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", unquote(value or ""),
                  flags=re.I).strip().casefold()


def title_hash(title):
    text = "".join(c for c in unicodedata.normalize("NFKC", title or "").casefold() if c.isalnum())
    return sha256(text.encode()).hexdigest() if text else ""


def exclusions():
    with (BASE / "excluded-972.psv").open(encoding="utf-8", newline="") as file:
        rows = list(DictReader(file, delimiter="|"))
    if len({row["article_key"] for row in rows}) != 972 or len(rows) != 972:
        raise ValueError("Frozen exclusion set must contain 972 unique articles")
    return {field: {k: row["article_key"] for row in rows for k in row[field].split()}
            for field in ("doi_aliases", "pmcids", "pmids", "title_sha256")}


def prior_record(row, old):
    for field, key in (("doi_aliases", doi_key(row.get("doi"))), ("pmcids", (row.get("pmcid") or "").upper()),
                       ("pmids", row.get("pmid")), ("title_sha256", title_hash(row.get("title")))):
        if key in old[field]:
            return old[field][key]
    return None


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def get_json(url, path):
    if path.exists():
        return json.loads(path.read_bytes())
    for attempt in range(2):
        try:
            request = Request(url, headers={"User-Agent": "MFC Studio literature research/1.0"})
            with urlopen(request, timeout=40) as response:
                value = json.load(response)
            save_json(path, value)
            return value
        except (OSError, ValueError) as exc:
            if attempt == 1 or isinstance(exc, HTTPError) and exc.code in {400, 401, 403, 404, 429}:
                raise
            time.sleep(2)


def terms(values):
    return "(" + " OR ".join(f'"{value}"' for value in values) + ")"


def query_plan(cycle):
    dates = "FIRST_PDATE:[1970-01-01 TO 2026-11-06]"
    mfc_titles = "(TITLE_ABS:\"microbial fuel cell\" OR TITLE_ABS:\"microbial fuel cells\" OR TITLE_ABS:\"microbial fuel-cell\")"
    if cycle == 4:
        yield "mfc-title-abstract-census", EUROPE, {
            "query": f"{mfc_titles} AND {dates}", "format": "json", "pageSize": 500,
        }, 24
        yield "mfc-openalex-title-abstract-count", ALEX, {
            "search.title_abstract_keywords": MFC[1:-1],
            "filter": "to_publication_date:2026-11-06,type:article",
            "per_page": 1, "select": SELECT,
        }, 1
        for start, end in [(1970, 2005), (2006, 2010), (2011, 2015), (2016, 2020), (2021, 2023), (2024, 2026)]:
            yield f"mfc-openalex-{start}-{end}", ALEX, {
                "search.title_abstract_keywords": MFC[1:-1],
                "filter": f"from_publication_date:{start}-01-01,to_publication_date:{end}-{'11-06' if end == 2026 else '12-31'},type:article",
                "per_page": 100, "select": SELECT,
            }, 5
        return
    for f, (anodes, donor, cathodes, topology) in FAMILIES.items():
        if cycle == 5:
            for field, require_donor in [("METHODS", True), ("METHODS", False), ("BODY", True)]:
                filters = ["(" + " OR ".join(f'{field}:"{word}"' for word in group) + ")"
                           for group in (anodes, cathodes)]
                if require_donor:
                    filters.append(f'{field}:"{donor}"')
                query = " AND ".join((mfc_titles, dates, *filters))
                yield f"{f}-epmc-{field.lower()}-{'with' if require_donor else 'without'}-donor", EUROPE, {
                    "query": query, "format": "json", "pageSize": 300,
                }, 12
            query = f"microbial fuel cell {anodes[0]} {donor} {cathodes[0]} {topology} batch control"
            yield f"{f}-crossref-cursor", CROSSREF, {
                "query.bibliographic": query, "query.title": "microbial fuel cell",
                "filter": "type:journal-article,until-pub-date:2026-11-06", "rows": 100,
                "select": "DOI,title,author,published,link,URL",
            }, 3
        elif cycle == 3:
            for pmid in CITATION_SEEDS[f]:
                yield f"{f}-cites-{pmid}", f"{EUROPE_REST}/MED/{pmid}/citations", {
                    "format": "json", "pageSize": 100,
                }, 2
        elif cycle == 1:
            # OpenAlex is complementary to the previous PMCID-led archive.
            query = f'{MFC} AND {terms(anodes)} AND "{donor}" AND {terms(cathodes)} AND "{topology}"'
            yield f"{f}-alex-specific", ALEX, {"search": query, "per_page": 100, "select": SELECT}, 2
            biblio = f"microbial fuel cell {anodes[0]} {donor} {cathodes[0]} {topology} control fed batch"
            yield f"{f}-crossref", CROSSREF, {
                "query.bibliographic": biblio, "filter": "type:journal-article,until-pub-date:2026-11-06",
                "rows": 60, "select": "DOI,title,author,published,link,URL,reference",
            }, 1
        elif cycle == 2:
            query = f'{MFC} AND {terms(anodes)} AND "{donor}" AND {terms(cathodes)}'
            yield f"{f}-alex-no-topology", ALEX, {"search": query, "per_page": 100, "select": SELECT}, 2
            # No open-access or PMCID restriction and different fields from the previous round.
            alternatives = " OR ".join(f'TITLE_ABS:"{word}"' for word in (*anodes, *cathodes))
            query = f'TITLE_ABS:{MFC} AND ({alternatives}) AND FIRST_PDATE:[1990-01-01 TO 2026-11-06]'
            yield f"{f}-epmc-title-abstract", EUROPE, {"query": query, "format": "json", "pageSize": 200}, 2


def compact(row, endpoint):
    if endpoint == ALEX:
        ids = row.get("ids") or {}
        locations = [row.get("best_oa_location"), *row.get("locations", [])]
        urls = list(dict.fromkeys(
            x for loc in locations if loc and loc.get("is_oa") for x in (loc.get("pdf_url"), loc.get("landing_page_url")) if x
        ))
        return {"title": row.get("display_name"), "doi": doi_key(row.get("doi")), "year": row.get("publication_year"),
                "openalex": row["id"], "pmid": ids.get("pmid", "").rsplit("/", 1)[-1],
                "type": row.get("type"), "retracted": row.get("is_retracted"),
                "urls": urls, "author": (row.get("authorships") or [{}])[0].get("author", {}).get("display_name")}
    if endpoint == CROSSREF:
        return {"title": (row.get("title") or [""])[0], "doi": doi_key(row.get("DOI")),
                "year": row.get("published", {}).get("date-parts", [[None]])[0][0],
                "author": (row.get("author") or [{}])[0].get("family"),
                "urls": [link["URL"] for link in row.get("link", []) if link.get("content-type") == "application/pdf"]}
    return {"title": row.get("title"), "doi": doi_key(row.get("doi")), "pmcid": row.get("pmcid"),
            "pmid": row.get("pmid") or (row.get("id") if row.get("source") == "MED" else None),
            "year": row.get("pubYear"), "author": row.get("authorString"), "urls": []}


def search(cache, spec):
    name, endpoint, params, limit = spec
    log = {"route": name, "endpoint": endpoint, "query": params, "page_limit": limit, "pages": []}
    records = []
    cursor = "*"
    for page in range(1, limit + 1):
        options = dict(params)
        if endpoint == ALEX:
            if name.startswith("mfc-openalex-"):
                options["page"] = page
            else:
                options["cursor"] = cursor
        elif endpoint == CROSSREF and name.endswith("-cursor"):
            options["cursor"] = cursor
        elif endpoint == EUROPE:
            options["cursorMark"] = cursor
        elif endpoint.endswith("/citations"):
            options["page"] = page
        path = cache / "queries" / name / f"{page:02}.json"
        try:
            data = get_json(endpoint + "?" + urlencode(options), path)
        except (OSError, ValueError) as exc:
            log["error"] = str(exc)
            break
        if endpoint == ALEX:
            batch, total, next_cursor = data["results"], data["meta"]["count"], data["meta"].get("next_cursor")
            if "page" in options:
                next_cursor = str(page + 1)
        elif endpoint == CROSSREF:
            message = data["message"]
            batch, total = message["items"], message["total-results"]
            next_cursor = message.get("next-cursor") if "cursor" in options else None
        elif endpoint.endswith("/citations"):
            batch, total = data.get("citationList", {}).get("citation", []), int(data["hitCount"])
            next_cursor = str(page + 1)
        else:
            batch, total, next_cursor = data["resultList"]["result"], data["hitCount"], data.get("nextCursorMark")
        records.extend(compact(row, endpoint) for row in batch)
        log["pages"].append({"returned": len(batch), "total_reported": total, "sha256": sha256(path.read_bytes()).hexdigest()})
        if not batch or not next_cursor or next_cursor == cursor or len(records) >= total:
            break
        cursor = next_cursor
    log["records_returned"] = len(records)
    log["coverage"] = ("failed" if not log["pages"] else "all_pages"
                       if not log.get("error") and len(records) >= log["pages"][-1]["total_reported"] else "bounded_ranked")
    print(name, len(records), log["coverage"], log.get("error", ""), flush=True)
    return log, records


def export_register(cache, destination, cycles=(1, 2, 3)):
    old = exclusions()
    records = {}
    for cycle in cycles:
        for row in json.loads((cache / f"discovery-cycle-{cycle}.json").read_bytes())["records"]:
            entry = records.setdefault(row["key"], row)
            entry["routes"].update(row["routes"])

    titles = defaultdict(set)
    pmids = defaultdict(set)
    for key, row in records.items():
        if row["doi"]:
            titles[title_hash(row["title"])].add(key)
            if row.get("pmid"):
                pmids[row["pmid"]].add(key)
    for key, row in list(records.items()):
        if row["doi"]:
            continue
        matches = titles[title_hash(row["title"])] | pmids[row.get("pmid")]
        if len(matches) == 1:
            records[next(iter(matches))]["routes"].update(row["routes"])
            del records[key]

    columns = ("key", "doi", "pmcid", "pmid", "year", "title", "routes")
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as file:
        writer = DictWriter(file, columns, delimiter="|", lineterminator="\n")
        writer.writeheader()
        for _, row in sorted(records.items()):
            if not prior_record(row, old):
                entry = {field: row.get(field) or "NR" for field in columns}
                entry["title"] = " ".join(row["title"].split())
                entry["routes"] = " ".join(sorted(row["routes"]))
                writer.writerow(entry)
    if destination.suffix == ".gz":
        tmp.write_bytes(compress(tmp.read_bytes(), mtime=0))
    tmp.replace(destination)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--cycle", type=int, choices=range(1, 6))
    action.add_argument("--export-register", type=Path, metavar="PSV")
    parser.add_argument("--include-expanded", action="store_true", help="Include the two later cycles in the export.")
    args = parser.parse_args()
    if args.export_register:
        export_register(args.cache, args.export_register, range(1, 6) if args.include_expanded else (1, 2, 3))
        return
    old = exclusions()
    grouped = {}
    duplicate = set()
    logs = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for log, rows in pool.map(lambda spec: search(args.cache, spec), query_plan(args.cycle)):
            logs.append(log)
            for rank, row in enumerate(rows, start=1):
                if not row["title"] or str(row["year"] or "") > "2026":
                    continue
                prior = prior_record(row, old)
                if prior:
                    duplicate.add(prior)
                    continue
                key = row["doi"] or row.get("pmcid") or row.get("pmid") or title_hash(row["title"])
                entry = grouped.setdefault(key, row | {"routes": {}, "key": key})
                entry["routes"].setdefault(log["route"], rank)
                entry["urls"] = list(dict.fromkeys(entry["urls"] + row["urls"]))
                for field in ("pmcid", "pmid", "openalex"):
                    if row.get(field):
                        entry.setdefault(field, row[field])
    manifest = {"cycle": args.cycle, "excluded_articles_matched": len(duplicate),
                "candidates": len(grouped), "queries": logs,
                "candidates_with_locators": sum(bool(x["urls"] or x.get("pmcid")) for x in grouped.values()),
                "route_counts": dict(Counter(route for row in grouped.values() for route in row["routes"]))}
    save_json(args.cache / f"discovery-cycle-{args.cycle}.json", manifest | {"records": list(grouped.values())})
    print({k: v for k, v in manifest.items() if k not in {"queries", "route_counts"}}, flush=True)


if __name__ == "__main__":
    main()
