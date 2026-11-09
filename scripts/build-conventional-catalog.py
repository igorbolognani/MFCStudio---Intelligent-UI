"""Consolidate publication identities and keep access, reading and inclusion separate."""
from argparse import ArgumentParser
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import json
import re
import runpy

HERE = Path(__file__).resolve().parent
R = runpy.run_path(str(HERE / "reconcile-external-register.py"))
METHOD = runpy.run_path(str(HERE / "audit-conventional-methods.py"))
EXTERNAL = R["BASE"]
DATA = EXTERNAL.parent
OUTPUT = DATA / "catalog"
read = R["read_table"]
read_json = R["read_json"]
write = R["write_table"]
save = R["SEARCH"]["save_json"]
doi_key = R["SEARCH"]["doi_key"]
title_hash = R["SEARCH"]["title_hash"]
FULL_METHODS = METHOD["FULL_METHODS"]
REQUIRED_COVERAGE = ("body_recovered", "documented_integral", "individual_screening",
                     "complete_methods_read", "included_F1_F6")
DOC = {"unknown": 0, "unavailable": 1, "partial": 2, "body_candidate": 3, "documented_integral": 4}
METADATA_DOC_TYPES = {"review", "editorial", "erratum", "book", "book-chapter", "retraction"}


def values(value):
    return set((value or "").split()) - {"NR", "NA"}


def identity(row):
    out = {
        ("doi", doi_key(value)) for value in values(row.get("doi_aliases")) | values(row.get("doi"))
        if doi_key(value).startswith("10.")
    }
    out |= {("pmcid", value.upper()) for value in values(row.get("pmcids")) | values(row.get("pmcid"))
            if re.fullmatch(r"PMC\d+", value, re.I)}
    out |= {("pmid", value) for value in values(row.get("pmids")) | values(row.get("pmid"))
            if value.isdecimal()}
    key = row.get("article_key") or row.get("key")
    if key and key.startswith("10."):
        out.add(("doi", doi_key(key)))
    if key and re.fullmatch(r"(?:MED:)?\d+", key):
        out.add(("pmid", key.split(":")[-1]))
    return out


class Catalog:
    def __init__(self):
        self.rows = {}
        self.aliases = {}
        self.titles = defaultdict(set)
        self.keys = {}

    def find(self, row):
        key = row.get("article_key") or row.get("key")
        aliases = identity(row)
        known = {self.aliases[a] for a in aliases if a in self.aliases}
        if key in self.keys:
            known.add(self.keys[key])
        if len(known) > 1:
            raise ValueError(f"Conflicting registered identifiers for {key}: {sorted(known)}")
        if known:
            return known.pop()
        hashes = values(row.get("title_sha256"))
        if row.get("title"):
            hashes.add(title_hash(row["title"]))
        matches = {k for h in hashes for k in self.titles[h]}
        if len(matches) == 1:
            k = matches.pop()
            row_year, known_year = row.get("year"), self.rows[k]["year"]
            recorded = self.rows[k]["aliases"]
            if (not aliases or not recorded or aliases & recorded) and (
                    not row_year or row_year == "NR" or known_year == "NR" or str(row_year) == known_year):
                return k
        return None

    def merge(self, old, canonical, evidence):
        if old == canonical:
            return
        previous, current = self.rows.pop(old), self.rows[canonical]
        for field in ("aliases", "evidence", "scopes", "decisions", "families", "machine"):
            current[field].update(previous[field])
        for field in ("abstract", "open_route"):
            current[field] |= previous[field]
        access(current, previous["document"])
        current["evidence"].add(evidence)
        for alias in previous["aliases"]:
            self.aliases[alias] = canonical
        for title_keys in self.titles.values():
            if old in title_keys:
                title_keys.remove(old)
                title_keys.add(canonical)
        for key, owner in self.keys.items():
            if owner == old:
                self.keys[key] = canonical

    def add(self, source, label, *, allow_new=True):
        key = self.find(source)
        aliases = identity(source)
        lookup_key = source.get("article_key") or source.get("key")
        if key is None:
            if not allow_new:
                return None
            key = lookup_key or doi_key(source.get("doi")) or source.get("pmcid")
            if not key or key == "NR":
                raise ValueError(f"Cannot assign a stable identity to {label}")
            self.rows[key] = {"key": key, "aliases": set(), "title": "NR", "year": "NR",
                              "evidence": set(), "abstract": False, "document": "unknown",
                              "scopes": set(), "decisions": set(), "families": set(),
                              "machine": set(), "open_route": False, "rank": "NR"}
        row = self.rows[key]
        for field in ("title", "year"):
            if source.get(field) not in (None, "", "NR") and row[field] == "NR":
                row[field] = str(source[field])
        row["aliases"].update(aliases)
        if lookup_key:
            self.keys[lookup_key] = key
        for alias in aliases:
            self.aliases[alias] = key
        hashes = values(source.get("title_sha256"))
        if source.get("title"):
            hashes.add(title_hash(source["title"]))
        for digest in hashes:
            if digest:
                self.titles[digest].add(key)
        row["evidence"].add(label)
        return row


def access(row, state):
    if DOC[state] > DOC[row["document"]]:
        row["document"] = state


def classify_machine(row, text, types):
    text = R["normalized_terms"](text)
    matches = {term for term, pattern in R["TERM_PATTERNS"].items() if pattern.search(text)}
    for family, wanted in R["METHOD"]["FAMILIES"].items():
        count = sum(term in matches for term in wanted)
        if count >= 2:
            row["machine"].add(f"{family}:{count}")
    if METADATA_DOC_TYPES & set(types) or R["NONPRIMARY"].search(row["title"]):
        row["machine"].add("nonprimary_signal")


def historical():
    catalog = Catalog()
    for source in read(EXTERNAL / "excluded-972.psv"):
        row = catalog.add(source, "historical_identity")
        access(row, "documented_integral" if source["highest_access"] == "integral" else "partial")
    frozen = read(EXTERNAL / "coverage/register.psv.gz")
    for source in frozen:
        catalog.add(source, "indexed_identity")
    for source in read_json(DATA / "frame.json")["frame"]:
        catalog.add(source, "historical_index", allow_new=False)
    for status in read(EXTERNAL / "coverage/frozen-pass/status.psv.gz"):
        row = catalog.rows[catalog.keys[status["key"]]]
        row["abstract"] |= status["abstract_provider"] != "NR"
        row["open_route"] |= status["indexed_locator"] == "yes"
        row["rank"] = status["acquisition_rank"]
        row["machine"].update(values(status["term_overlap"]))
        if status["nonprimary_signal"] == "yes":
            row["machine"].add("nonprimary_signal")
        if status["document_state"] in {"xml", "pdf", "html"}:
            access(row, "body_candidate")
        elif status["document_state"] == "attempted":
            access(row, "unavailable")
        if status["decision"] not in {"unreviewed", "admitted"}:
            row["decisions"].add(status["decision"])
            row["scopes"].add(status["scope"])
    sources = {}
    for file in (DATA / "sources.json", DATA / "targeted-sources.json",
                 DATA / "methods-expansion/sources.json", EXTERNAL / "sources.json"):
        for source in read_json(file):
            ref = source.get("sample_id") or source["source"]
            row = catalog.add(source, ref)
            sources[ref] = row
            if source.get("full_text") or source.get("files") or source.get("document", {}).get("local_path"):
                access(row, "documented_integral")
            if source.get("reading_scope"):
                row["scopes"].add(source["reading_scope"])
    for record in read(DATA / "methods-expansion/acquisition.psv"):
        row = catalog.add(record, record["source"])
        if record["access"] == "jats":
            access(row, "documented_integral")
        elif record["access"] == "unavailable":
            access(row, "unavailable")
    for name in ("screening.psv", "targeted-screening.psv", "methods-expansion/reading-log.psv"):
        for review in read(DATA / name):
            row = sources[review["source"]]
            row["evidence"].add(review["source"] + ":review")
            row["scopes"].add(review.get("scope") or "relevant_sections")
            decision = review["decision"]
            row["decisions"].add({"included": "included_in_survey", "include": "included_in_survey",
                                  "excluded": "exclude"}.get(decision, decision))
    for review in read(EXTERNAL / "screening.psv"):
        if review["decision"] == "prior_access":
            continue
        row = catalog.add(review, "external_review")
        row["scopes"].add(review["scope"])
        row["decisions"].add(review["decision"])
    for doc in read_json(EXTERNAL / "screened-documents.json"):
        if doc["role"] == "main":
            row = catalog.add(doc, "screened_main_document")
            access(row, "documented_integral")

    for locator in read(DATA / "methods-expansion/baseline-locators.psv"):
        sources[locator["source"]]["families"].add(locator["family"])
    for file in (DATA / "methods-expansion/arms.psv", EXTERNAL / "arms.psv"):
        for arm in read(file):
            if arm["role"] != "standard_protocol":
                sources[arm["source"]]["families"].add(METHOD["family"](arm))
    return catalog


def apply_metadata(catalog, cache):
    for provider in ("epmc", "alex"):
        for path in sorted((cache / provider).glob("*.json")):
            raw = read_json(path)
            batch = raw["resultList"]["result"] if provider == "epmc" else raw["results"]
            for item in batch:
                if provider == "epmc":
                    meta = {field: item.get(field) for field in ("title", "doi", "pmcid", "pmid")}
                    meta["pmid"] = meta["pmid"] or item["id"]
                    meta["year"] = item.get("pubYear")
                    abstract = re.sub(r"<[^>]*>", " ", item.get("abstractText") or "")
                    types = (item.get("pubTypeList") or {}).get("pubType", [])
                    open_route = any(x.get("availabilityCode") in ("OA", "F")
                                     for x in (item.get("fullTextUrlList") or {}).get("fullTextUrl", []))
                else:
                    meta = {"doi": item.get("doi"), "title": item.get("display_name"),
                            "year": item.get("publication_year")}
                    index = item.get("abstract_inverted_index") or {}
                    abstract = " ".join(word for _, word in sorted((p, w) for w, positions in index.items() for p in positions))
                    types = [item.get("type")]
                    open_route = bool((item.get("best_oa_location") or {}).get("is_oa"))
                # Index corrections may map an ID to another existing publication. Keep the
                # already audited identities independent until such a conflict is reviewed.
                try:
                    row = catalog.add(meta, provider + "_metadata", allow_new=False)
                except ValueError as error:
                    if not str(error).startswith("Conflicting registered identifiers"):
                        raise
                    continue
                if row:
                    row["abstract"] |= bool(abstract.strip())
                    row["open_route"] |= open_route
                    classify_machine(row, row["title"] + " " + abstract, [str(t).casefold() for t in types])
    for row in catalog.rows.values():
        classify_machine(row, row["title"], [])


def apply_archived_index(catalog, cache):
    path = cache / "method-index.json"
    if not path.exists():
        return
    checksums = {row["pmcid"]: row["sha256"] for row in read(DATA / "methods-expansion/acquisition.psv")
                 if row["access"] == "jats"}
    for item in read_json(path):
        if checksums.get(item["pmcid"]) != item.get("sha256") or not item.get("sha256"):
            raise ValueError(f"Archived JATS identity differs: {item['pmcid']}")
        doi = doi_key(item.get("doi"))
        doi_owner = catalog.aliases.get(("doi", doi))
        pmc_owner = catalog.aliases.get(("pmcid", item["pmcid"]))
        if doi_owner and pmc_owner and doi_owner != pmc_owner:
            if title_hash(item["title"]) != title_hash(catalog.rows[doi_owner]["title"]):
                raise ValueError(f"Conflicting JATS article identifiers: {item['pmcid']}")
            catalog.merge(pmc_owner, doi_owner, "confirmed_jats_identity")
        row = catalog.add(item, "archived_body_indexed", allow_new=False)
        if row and item["method_sections"]:
            row["evidence"].add("archived_methods_indexed")
            for family, match in item["matches"].items():
                if len(match["methods"]) >= 2:
                    row["machine"].add(f"{family}_methods:{len(match['methods'])}")


def apply_acquisition(catalog, output):
    for item in read(output / "acquisition.psv"):
        row = catalog.rows[catalog.keys.get(item["key"], item["key"])]
        if item["state"] == "identity_verified":
            access(row, "documented_integral")
        elif item["state"] == "body_candidate":
            access(row, "body_candidate")
        elif item["state"] == "preview_only":
            access(row, "partial")
        elif item["state"] in {"unrecovered", "wrong_document"}:
            access(row, "unavailable")
        row["evidence"].add("catalog_acquisition")


def apply_reviews(catalog, output):
    for review in read(output / "reviews.psv"):
        row = catalog.rows[catalog.keys.get(review["key"], review["key"])]
        decision = review["decision"]
        if decision not in {"exclude", "pending", "confirm_existing_control"} or not review["locator"] or not review["reason"]:
            raise ValueError(f"Invalid screening record: {review['key']}")
        reviewed_families = values(review["families_considered"])
        if decision == "confirm_existing_control" and (
            not reviewed_families or not reviewed_families <= row["families"]
            or review["scope"] not in FULL_METHODS
            or row["document"] != "documented_integral"
        ):
            raise ValueError(f"Control confirmation requires an existing arm and documented methods: {review['key']}")
        row["scopes"].add(review["scope"])
        row["decisions"].add(decision)
        row["evidence"].add("catalog_individual_review")


def merge_versions(catalog, output):
    if not (output / "versions.psv").exists():
        return
    for pair in read(output / "versions.psv"):
        old = catalog.find({"doi": pair["preprint_doi"]})
        canonical = catalog.find({"doi": pair["published_doi"]})
        if not old or not canonical or old == canonical or not pair["source"].startswith("https://"):
            raise ValueError(f"Invalid published-version link: {pair}")
        catalog.merge(old, canonical, "confirmed_publication_version")


def rows_and_summary(catalog, output):
    rows = []
    for key, row in sorted(catalog.rows.items()):
        aliases = row["aliases"]
        matches = " ".join(sorted(row["families"])) or "NR"
        labels = set(row["decisions"])
        if matches != "NR":
            labels.add("admitted_F1_F6")
        rows.append({"key": key,
                     **{tag: " ".join(sorted(x for kind, x in aliases if kind == tag)) or "NR"
                        for tag in ("doi", "pmcid", "pmid")},
                     "title": row["title"], "year": row["year"], "abstract": "yes" if row["abstract"] else "no",
                     "document": row["document"], "reading_scopes": " ".join(sorted(row["scopes"])) or "NR",
                     "decisions": " ".join(sorted(labels)) or "unreviewed", "families": matches,
                     "pending": "yes" if "pending" in labels or not labels else "no",
                     "open_route_indexed": "yes" if row["open_route"] else "no",
                     "priority_previous": row["rank"],
                     "machine_signals": " ".join(sorted(row["machine"])) or "NR",
                     "evidence": " ".join(sorted(row["evidence"]))})
    write(output / "publications.psv.gz", list(rows[0]), rows)
    summary = summarize(rows, output)
    save(output / "coverage.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


def summarize(rows, output):
    seen_keys, seen_aliases = set(), {}
    counts = Counter()
    for row in rows:
        key = row["key"]
        aliases = identity(row)
        if key in seen_keys or seen_aliases.keys() & aliases:
            raise ValueError(f"Duplicate catalogue identity: {key}")
        seen_keys.add(key)
        seen_aliases.update(dict.fromkeys(aliases, key))
        body = DOC[row["document"]] >= DOC["body_candidate"]
        reviewed = row["decisions"] != "unreviewed"
        admitted = row["families"] != "NR"
        counts["abstract_recovered"] += row["abstract"] == "yes"
        counts["body_recovered"] += body
        counts["documented_integral"] += row["document"] == "documented_integral"
        counts["individual_screening"] += reviewed
        counts["complete_methods_read"] += bool(values(row["reading_scopes"]) & FULL_METHODS)
        counts["included_F1_F6"] += admitted
        counts["with_body_without_screening"] += body and not reviewed
        counts["with_open_route_without_body"] += row["open_route_indexed"] == "yes" and not body
        counts["metadata_signals_processed"] += 1
        counts["archived_methods_indexed"] += "archived_methods_indexed" in values(row["evidence"])
        counts["without_title"] += row["title"] == "NR"
        counts["without_persistent_identifier"] += not aliases
    minimum = len(rows) // 2 + 1
    remaining = {metric: max(0, minimum - counts[metric]) for metric in REQUIRED_COVERAGE}
    summary = {"unique_publications": len(rows), "minimum_for_over_half": minimum,
               "counts": dict(sorted(counts.items())),
               "percent": {key: round(100 * value / len(rows), 2) for key, value in sorted(counts.items())},
               "over_half_complete": not any(remaining.values()),
               "remaining_to_over_half": remaining,
               "access_states": dict(sorted(Counter(row["document"] for row in rows).items())),
               "families": dict(sorted(Counter(f for row in rows for f in values(row["families"])).items())),
               "hashes": {}}
    for name in ("publications.psv.gz", "acquisition.psv", "reviews.psv", "versions.psv", "document-conflicts.psv"):
        path = output / name
        if path.exists():
            summary["hashes"][name] = sha256(path.read_bytes()).hexdigest()
    def canonical(item):
        key = item["key"]
        aliases = {seen_aliases[a] for a in identity(item) if a in seen_aliases}
        if key in seen_keys:
            aliases.add(key)
        if len(aliases) != 1:
            raise ValueError(f"Ledger identity is absent or ambiguous: {key}")
        return aliases.pop()

    if "acquisition.psv" in summary["hashes"]:
        acquisition = read(output / "acquisition.psv")
        publications = {canonical(item) for item in acquisition if item["state"] != "no_route_tested"}
        if len(acquisition) != len({(canonical(row), row["route_group"]) for row in acquisition}):
            raise ValueError("Repeated acquisition identity within a batch")
        summary["acquisition_batch_states"] = dict(sorted(Counter(row["state"] for row in acquisition).items()))
        summary["acquisition_unique_attempted"] = len(publications)
    if "reviews.psv" in summary["hashes"]:
        reviews = read(output / "reviews.psv")
        if len(reviews) != len({canonical(row) for row in reviews}):
            raise ValueError("Repeated review identity")
        summary["catalog_review_decisions"] = dict(sorted(Counter(row["decision"] for row in reviews).items()))
    return summary


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--require-over-half", action="store_true",
                        help="With --check, return 2 while any of the five rates is at or below 50%.")
    args = parser.parse_args()
    if args.require_over_half and not args.check:
        parser.error("--require-over-half requires --check")
    if args.check:
        summary = summarize(read(args.output / "publications.psv.gz"), args.output)
        if summary != read_json(args.output / "coverage.json"):
            raise ValueError("Saved catalogue counts or hashes changed")
        print("Catalogue identities, counts and file hashes verified")
        for metric, remaining in summary["remaining_to_over_half"].items():
            print(f"{metric}: {summary['counts'][metric]}/{summary['unique_publications']} "
                  f"({summary['percent'][metric]:.2f}%), remaining {remaining}")
        if args.require_over_half and not summary["over_half_complete"]:
            raise SystemExit(2)
        raise SystemExit(0)
    if args.cache is None:
        parser.error("--cache is required when generating the catalogue")
    args.output.mkdir(parents=True, exist_ok=True)
    catalog = historical()
    apply_metadata(catalog, args.cache)
    apply_archived_index(catalog, args.cache)
    for name, apply in (("acquisition.psv", apply_acquisition), ("reviews.psv", apply_reviews)):
        if (args.output / name).exists():
            apply(catalog, args.output)
    merge_versions(catalog, args.output)
    rows_and_summary(catalog, args.output)
