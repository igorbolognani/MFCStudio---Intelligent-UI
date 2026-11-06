"""Reconcile the frozen MFC discovery returns with document and review status."""
from argparse import ArgumentParser
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from csv import DictReader, DictWriter
from gzip import compress, open as gzip_open
from hashlib import sha256
from html import unescape
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit
import json
import re
import runpy

HERE = Path(__file__).resolve().parent
SEARCH = runpy.run_path(str(HERE / "search-external-arms.py"))
METHOD = runpy.run_path(str(HERE / "search-conventional-methods.py"))
BASE = SEARCH["BASE"]
def normalized_terms(text):
    return re.sub(r"[-‐‑–—\s]+", " ", text)


TERM_PATTERNS = {
    key: re.compile(r"(?<!\w)(?:" + "|".join((re.escape(normalized_terms(value)) for value in values)) + r")(?!\w)", re.I)
    for key, values in METHOD["TERMS"].items()
}
NONPRIMARY = re.compile(
    r"^(?:publisher correction|author correction|correction|erratum|corrigendum|retraction(?: note)?):"
    r"|\b(?:bibliometric analysis|systematic review|a (?:comprehensive |critical |brief )?review|mini.review)\b"
    r"|^review (?:of|on)\b", re.I
)
PRIMARY_TOPIC = re.compile(r"microbial fuel.cell|microbial electrochem|bioelectrochem|bioelectric|"
                           r"exoelectrogen|electrogen|biocathode|microbial electricity|微生物燃料电池", re.I)


def read_json(path):
    return json.loads(path.read_bytes())


def read_table(path):
    reader = gzip_open if path.suffix == ".gz" else open
    with reader(path, "rt", encoding="utf-8", newline="") as file:
        return list(DictReader(file, delimiter="|"))


def write_table(path, columns, rows):
    data = StringIO(newline="")
    writer = DictWriter(data, columns, delimiter="|", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    tmp = path.with_suffix(path.suffix + ".tmp")
    body = data.getvalue().encode()
    tmp.write_bytes(compress(body, mtime=0) if path.suffix == ".gz" else body)
    tmp.replace(path)


def identifiers(row):
    for name, canonical in (("doi", SEARCH["doi_key"]), ("pmcid", str.upper), ("pmid", str)):
        value = row.get(name)
        if value and value != "NR":
            yield name, canonical(value)
    if row.get("title"):
        yield "title", SEARCH["title_hash"](row["title"])


def frame_match(row, lookup):
    for identity in identifiers(row):
        keys = lookup.get(identity, set())
        if len(keys) == 1:
            return next(iter(keys))
    return None


def page_records(raw, endpoint):
    if endpoint == SEARCH["ALEX"]:
        return raw["results"]
    if endpoint == SEARCH["CROSSREF"]:
        return raw["message"]["items"]
    if endpoint.endswith("/citations"):
        return raw.get("citationList", {}).get("citation", [])
    return raw["resultList"]["result"]


def raw_crosswalk(cache, lookup, old, work):
    historical = read_json(BASE / "search.json")
    expanded = read_json(BASE / "coverage/manifest.json")
    for cycle in historical["cycles"] + expanded["cycles"]:
        for query in cycle["queries"]:
            route, endpoint = query["route"], query["endpoint"]
            for number, page in enumerate(query["pages"], 1):
                path = cache / "queries" / route / f"{number:02}.json"
                data = path.read_bytes()
                if sha256(data).hexdigest() != page["sha256"]:
                    raise ValueError(f"Discovery page changed: {route}/{number}")
                batch = page_records(json.loads(data), endpoint)
                if len(batch) != page["returned"]:
                    raise ValueError(f"Discovery count changed: {route}/{number}")
                for rank, raw in enumerate(batch, 1):
                    row = SEARCH["compact"](raw, endpoint)
                    prior = SEARCH["prior_record"](row, old)
                    key = frame_match(row, lookup) if not prior else None
                    if key:
                        item = work[key]
                        item["raw_matches"] += 1
                        item["urls"].update(u for u in row["urls"] if urlsplit(u).scheme == "https")
                        item["oa"] |= raw.get("isOpenAccess") == "Y"
                        item["types"].update(filter(None, (row.get("type"), raw.get("pubType"))))
                        item["retracted"] |= row.get("retracted") is True
                    yield {"cycle": cycle["cycle"], "route": route, "page": number, "position": rank,
                           "resolution": "prior_972" if prior else "frozen_register" if key else "unlinked",
                           "key": prior or key or "NR"}


def fetch_metadata(cache, register, links):
    pmids = sorted({row["pmid"] for row in register if row["pmid"].isdecimal()})
    without_pmid = {row["doi"] for row in register if row["pmid"] == "NR" and row["doi"] != "NR"}
    alex_ids = set()
    for route, page in sorted({(row["route"], row["page"]) for row in links if "alex" in row["route"]}):
        raw = read_json(cache / "queries" / route / f"{page:02}.json")
        alex_ids.update(row["id"].rsplit("/", 1)[-1] for row in raw["results"]
                        if SEARCH["doi_key"](row.get("doi")) in without_pmid)

    def europe(ids):
        return SEARCH["EUROPE"], {"query": "SRC:MED AND (" + " OR ".join(f"EXT_ID:{x}" for x in ids) + ")",
                                  "format": "json", "resultType": "core", "pageSize": 60}

    def alex(ids):
        return SEARCH["ALEX"], {"filter": "openalex:" + "|".join(ids), "per_page": 60,
                               "select": "id,doi,display_name,abstract_inverted_index,type,is_retracted"}

    def fetch(job):
        batch, ids, path, build = job
        endpoint, params = build(ids)
        record = {"batch": batch, "requested": len(ids)}
        try:
            result = SEARCH["get_json"](endpoint + "?" + urlencode(params), path)
            actual = ({str(row.get("pmid") or row["id"]) for row in result["resultList"]["result"]}
                      if build is europe else {row["id"].rsplit("/", 1)[-1] for row in result["results"]})
            if not actual <= set(ids):
                raise ValueError("Endpoint returned identifiers beyond the requested batch")
            return record | {"returned": len(actual), "cache": str(path.relative_to(cache))}
        except (OSError, ValueError, KeyError) as error:
            return record | {"error": str(error)}

    for folder, ids, chunk_size, build in (("frozen-core", pmids, 60, europe),
                                           ("frozen-alex-core", sorted(alex_ids), 55, alex)):
        jobs = ((batch, ids[offset:offset + chunk_size], cache / folder / f"{batch:03}.json", build)
                for batch, offset in enumerate(range(0, len(ids), chunk_size)))
        with ThreadPoolExecutor(max_workers=3) as pool:
            log = list(pool.map(fetch, jobs))
        SEARCH["save_json"](cache / f"{folder}-log.json", log)


def abstract_index(cache, lookup):
    found = {}
    for folder, provider in (("frozen-core", "Europe PMC"), ("frozen-alex-core", "OpenAlex")):
        for path in sorted((cache / folder).glob("*.json")):
            raw = read_json(path)
            rows = raw["resultList"]["result"] if provider == "Europe PMC" else raw["results"]
            for row in rows:
                title = row.get("title") or row.get("display_name")
                key = frame_match({"doi": row.get("doi"), "pmcid": row.get("pmcid"), "pmid": row.get("pmid"),
                                   "title": title}, lookup)
                if not key or key in found:
                    continue
                body = row.get("abstractText")
                if not body and row.get("abstract_inverted_index"):
                    words = ((pos, word) for word, positions in row["abstract_inverted_index"].items()
                             for pos in positions)
                    body = " ".join(word for _, word in sorted(words))
                if body:
                    found[key] = (provider, unescape(re.sub(r"<[^>]+>", " ", body)))
    return found


def read_document_states(cache, lookup):
    states = {}
    for row in read_table(BASE / "screening.psv"):
        identifier = row["key"]
        field = "pmid" if identifier.isdecimal() else "doi"
        key = frame_match(row | {field: identifier}, lookup)
        if key:
            states[key] = (row["decision"], row["scope"])
    for row in read_json(BASE / "sources.json"):
        key = frame_match(row, lookup)
        if key:
            states[key] = ("admitted", row["reading_scope"])
    attempts = set()
    bodies = {}
    for path in sorted(cache.glob("pull-*.json")):
        for row in read_json(path):
            key = frame_match(row, lookup)
            if key and (row.get("attempts") or row.get("format")):
                attempts.add(key)
                if row.get("format"):
                    bodies[key] = row["format"]
    return states, attempts, bodies


def acquisition_records(cache, decisions):
    for path in sorted(cache.glob("pull-frozen-queue*.json")):
        for row in read_json(path):
            fmt = row.get("format")
            path_parts = urlsplit(row.get("url", ""))
            locator = urlunsplit((path_parts.scheme, path_parts.netloc, path_parts.path, "", ""))
            errors = Counter(
                "body_incomplete_or_unreadable" if item["error"].startswith("incomplete body")
                else item["error"].split(": ", 1)[0].split("<urlopen error ", 1)[-1]
                for item in row.get("attempts", [])
            )
            if fmt:
                data = (cache / row["local"] / f"article.{fmt}").read_bytes()
                if len(data) != row["bytes"] or sha256(data).hexdigest() != row["sha256"]:
                    raise ValueError(f"Acquired original changed: {row['key']}")
            yield {
                "batch": path.stem, "key": row["key"], "format": fmt or "NR",
                "state": "text_candidate" if fmt else "unrecovered", "url": locator or "NR",
                "sha256": row.get("sha256", "NR"), "bytes": row.get("bytes", "NR"),
                "prior_http_attempts": sum(errors.values()),
                "failure_classes": " / ".join(f"{label} ({n})" for label, n in sorted(errors.items())) or "NR",
                "decision": decisions.get(row["key"], ("unreviewed", ""))[0],
            }


def reconcile(cache, output, queue, enrich=False):
    register = read_table(BASE / "coverage/register.psv.gz")
    lookup = defaultdict(set)
    for row in register:
        for identity in identifiers(row):
            lookup[identity].add(row["key"])
    work = {row["key"]: {"raw_matches": 0, "urls": set(), "types": set(), "oa": False,
                         "retracted": False} for row in register}
    old = SEARCH["exclusions"]()
    links = list(raw_crosswalk(cache, lookup, old, work))
    if len(links) != read_json(BASE / "coverage/manifest.json")["raw_returns"]["cumulative"]:
        raise ValueError("Raw return count changed")
    if enrich:
        fetch_metadata(cache, register, links)
    abstracts = abstract_index(cache, lookup)
    decisions, attempts, bodies = read_document_states(cache, lookup)
    statuses = []
    priority = []
    for row in register:
        key = row["key"]
        item = work[key]
        provider, abstract = abstracts.get(key, ("NR", ""))
        text = normalized_terms(row["title"] + " " + abstract)
        terms = {name for name, pattern in TERM_PATTERNS.items() if pattern.search(text)}
        hits = {family: sum(term in terms for term in spec) for family, spec in METHOD["FAMILIES"].items()}
        family_routes = {part[:2] for part in row["routes"].split() if re.match(r"F[1-6]-", part)}
        decision, scope = decisions.get(key, ("unreviewed", "NR"))
        nonprimary = bool(NONPRIMARY.search(row["title"])) or item["retracted"] or bool(
            item["types"] & {"review", "editorial", "erratum", "book", "book-chapter", "retraction"})
        candidate = row | {"doi": None if row["doi"] == "NR" else row["doi"],
                           "pmcid": None if row["pmcid"] == "NR" else row["pmcid"],
                           "pmid": None if row["pmid"] == "NR" else row["pmid"],
                           "urls": sorted(item["urls"]), "routes": dict.fromkeys(row["routes"].split(), 1)}
        has_open = bool(item["urls"] or item["oa"] and row["pmcid"] != "NR")
        statuses.append({"key": key, "raw_matches": item["raw_matches"], "abstract_provider": provider,
                         "indexed_locator": "yes" if has_open else "no", "document_state": bodies.get(key, "attempted" if key in attempts else "not_attempted"),
                         "decision": decision, "scope": scope, "nonprimary_signal": "yes" if nonprimary else "no",
                         "family_route": " ".join(sorted(family_routes)) or "NR",
                         "term_overlap": " ".join(f"{f}:{n}" for f,n in hits.items() if n >= 2) or "NR"})
        if not nonprimary and decision in {"unreviewed", "pending"} and key not in bodies and key not in attempts and has_open:
            score = 4 * max(hits.values()) + 2 * bool(family_routes) + 3 * bool(PRIMARY_TOPIC.search(text))
            score += 2 * any(hits[f] >= 3 for f in ("F2", "F5", "F6"))
            score += 3 * any("-epmc-methods-" in route for route in candidate["routes"])
            if candidate["pmcid"] and item["oa"]:
                score += 1
            priority.append((-score, key, candidate))
    output.mkdir(parents=True, exist_ok=True)
    write_table(output / "raw-crosswalk.psv.gz", list(links[0]), links)
    acquisitions = list(acquisition_records(cache, decisions))
    if len({row["key"] for row in acquisitions}) != len(acquisitions):
        raise ValueError("Expected distinct keys across the frozen acquisition batches")
    if not all(row["key"] in work for row in acquisitions):
        raise ValueError("Acquisition batch extends beyond the frozen register")
    acquisition_columns = ["batch", "key", "format", "state", "url", "sha256", "bytes",
                           "prior_http_attempts", "failure_classes", "decision"]
    write_table(output / "acquisition.psv", acquisition_columns, acquisitions)
    ranks = {key: rank for rank, (_, key, _) in enumerate(sorted(priority), 1)}
    for row in statuses:
        row["acquisition_rank"] = ranks.get(row["key"], "NR")
    write_table(output / "status.psv.gz", list(statuses[0]), statuses)
    report = {
        "raw_returns": dict(sorted(Counter(row["resolution"] for row in links).items())),
        "register_records": len(statuses),
        "register_without_linked_return": sum(not row["raw_matches"] for row in statuses),
        "abstracts": dict(sorted(Counter(row["abstract_provider"] for row in statuses).items())),
        "document_states": dict(sorted(Counter(row["document_state"] for row in statuses).items())),
        "acquisition_batches": {
            batch: dict(sorted(Counter(row["state"] for row in acquisitions if row["batch"] == batch).items()))
            for batch in sorted({row["batch"] for row in acquisitions})
        },
        "decisions": dict(sorted(Counter(row["decision"] for row in statuses).items())),
        "rows_flagged_nonprimary": sum(row["nonprimary_signal"] == "yes" for row in statuses),
        "unattempted_open_priority_count": len(priority),
        "terms_scope": "Title/abstract signals for triage. A match or a missing term does not decide eligibility.",
        "hashes": {name: sha256((output / name).read_bytes()).hexdigest()
                   for name in ("raw-crosswalk.psv.gz", "status.psv.gz", "acquisition.psv")},
    }
    SEARCH["save_json"](output / "reconciliation.json", report)
    if queue:
        SEARCH["save_json"](queue, [r for _, _, r in sorted(priority)])
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--fetch-metadata", action="store_true", help="Fetch exact-ID metadata using cache")
    args = parser.parse_args()
    reconcile(args.cache, args.output, args.queue, args.fetch_metadata)
