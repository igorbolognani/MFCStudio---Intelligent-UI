"""Check the external conventional-arm additions and recompute family coverage."""
from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from pathlib import Path
import re
import runpy

HERE = Path(__file__).resolve().parent
METHOD = runpy.run_path(str(HERE / "audit-conventional-methods.py"))
SEARCH = runpy.run_path(str(HERE / "search-external-arms.py"))
DATA = METHOD["DATA"]
ROUND = SEARCH["BASE"]
table = METHOD["read_table"]
read_json = METHOD["read_json"]
index = METHOD["index"]


def check_original(doc, cache):
    if not re.fullmatch(r"[a-f0-9]{64}", doc.get("sha256", "")) or doc["bytes"] <= 0:
        raise ValueError(f"Missing original document identity: {doc['local_path']}")
    if cache:
        data = (cache / doc["local_path"]).read_bytes()
        if len(data) != doc["bytes"] or sha256(data).hexdigest() != doc["sha256"]:
            raise ValueError(f"Original document changed: {doc['local_path']}")


def audit(cache=None):
    old = SEARCH["exclusions"]()
    candidates = index(table(ROUND / "candidate-register.psv")[1], "key")
    discovery = read_json(ROUND / "search.json")
    if (len(candidates) != discovery["api_records_after_deduplication"]
            or any(SEARCH["prior_record"](row, old) for row in candidates.values())):
        raise ValueError("Discovery register disagrees with the exclusion manifest")
    sources = index(read_json(ROUND / "sources.json"), "source")
    index([{"doi": SEARCH["doi_key"](s["doi"])} for s in sources.values()], "doi")
    for source in sources.values():
        if SEARCH["prior_record"](source, old):
            raise ValueError(f"Article was in the 972-article set: {source['source']}")
        if (not source["doi"] or not source["authors"] or not source["document"]["url"].startswith("https://")
                or source["reading_scope"] not in METHOD["FULL_METHODS"]
                or not source["methods_location"] or not source["arm_outcome_location"]):
            raise ValueError(f"Missing source or review provenance: {source['source']}")
        doc = source["document"]
        if doc.get("local_path"):
            check_original(doc, cache)
        elif source["reading_scope"] != "full_methods_web":
            raise ValueError(f"Local full-methods review has no original: {source['source']}")

    screening = table(ROUND / "screening.psv")[1]
    index(screening, "key")
    for row in screening:
        if not row["url"].startswith("https://") or not row["locator"] or not row["reason"]:
            raise ValueError(f"Missing screening provenance: {row['key']}")
        if row["decision"] == "prior_access" and SEARCH["prior_record"]({"doi": row["key"]}, old) is None:
            raise ValueError(f"Screened prior access does not match the frozen set: {row['key']}")
    screened_keys = {row["key"] for row in screening}
    reviewed_documents = read_json(ROUND / "screened-documents.json")
    index(reviewed_documents, "local_path")
    for doc in reviewed_documents:
        if doc["key"] not in screened_keys or not doc["url"].startswith("https://"):
            raise ValueError(f"Screened document lacks a decision or URL: {doc['local_path']}")
        check_original(doc, cache)

    columns, new = table(ROUND / "arms.psv")
    if tuple(columns[-11:]) != METHOD["SURVEY"]["STAGES"]:
        raise ValueError("Eleven stage columns missing or out of order")
    arms = index(new, "arm_id")
    if {row["source"] for row in new} != sources.keys():
        raise ValueError("Admitted sources and arms differ")
    if len({(row["source"], METHOD["family"](row)) for row in new}) != len(new):
        raise ValueError("Keep one counted reference per source and family")
    for row in new:
        if (not METHOD["family"](row) or row["role"] not in METHOD["SURVEY"]["ROLES"]
                or not row["arm_id"].startswith(row["source"] + "-")
                or any(not row[stage] for stage in METHOD["SURVEY"]["STAGES"])):
            raise ValueError(f"Invalid conventional arm: {row['arm_id']}")
        if row["separator"] == "none" and not row["membrane"].startswith("NA:"):
            raise ValueError(f"Unexplained absence of separator: {row['arm_id']}")
        if row["liquid_domains"] == "2" and row["catholyte"].startswith("NA:"):
            raise ValueError(f"Missing liquid cathode domain: {row['arm_id']}")

    observations = index(table(ROUND / "observations.psv")[1], "id")
    for obs in observations.values():
        if (obs["arm_id"] not in arms or obs["unit"] not in METHOD["UNITS"].get(obs["metric"], set())
                or obs["status"] not in {"context_only", "quality_hold"}
                or obs["extraction"] != "manual_text_or_table" or not obs["locator"]
                or not obs["basis"] or not obs["phase"]):
            raise ValueError(f"Invalid observation: {obs['id']}")
        value = METHOD["decimal"](obs["value"])
        if obs["spread_or_upper"] != "NR":
            upper = METHOD["decimal"](obs["spread_or_upper"])
            if obs["statistic"] == "reported_range" and upper < value:
                raise ValueError(f"Reversed observation range: {obs['id']}")
        if obs["n_reactors"] != "NR" and not re.fullmatch(r"[1-9][0-9]*", obs["n_reactors"]):
            raise ValueError(f"Invalid reactor count: {obs['id']}")
        if obs["load_ohm"] not in {"NR", "variable", "short_circuit"} and not METHOD["decimal"](obs["load_ohm"]):
            raise ValueError(f"Nonpositive finite load: {obs['id']}")

    by_arm = Counter(obs["arm_id"] for obs in observations.values() if obs["status"] == "context_only")
    if set(by_arm) != arms.keys():
        raise ValueError("Every new arm needs an electrical result suitable for bibliographic context")
    for issue in index(read_json(ROUND / "quality.json"), "id").values():
        if issue["source"] not in sources:
            raise ValueError(f"Quality issue lacks a source: {issue['id']}")

    previous = index(table(DATA / "arms.psv")[1] + table(DATA / "targeted-arms.psv")[1], "arm_id")
    locators = METHOD["table"]("baseline-locators.psv")
    baseline = [previous[row["arm_id"]] for row in locators]
    baseline += [row for row in METHOD["table"]("arms.psv") if row["role"] != "standard_protocol"]
    if read_json(DATA / "selection.json")["active_families"]:
        raise ValueError("Bibliographic research must not activate model families")
    prior = read_json(DATA / "methods-expansion/audit.json")["families"]
    checkpoints = read_json(ROUND / "checkpoint.json")
    targets = checkpoints["bibliographic_target"]
    families = {}
    for family in METHOD["FAMILY_KEYS"].values():
        before = [row for row in baseline if METHOD["family"](row) == family]
        additions = [row for row in new if METHOD["family"](row) == family]
        articles_before = {row["source"] for row in before}
        lineages_before = {row["lineage"] for row in before}
        if (len(articles_before) != prior[family]["articles"]
                or len(lineages_before) != prior[family]["lineages"]):
            raise ValueError(f"Frozen baseline changed for {family}")
        total = len(articles_before) + len(additions)
        lineages = lineages_before | {row["lineage"] for row in additions}
        families[family] = {
            "before": len(articles_before), "new": len(additions), "articles": total,
            "lineages_before": len(lineages_before), "lineages": len(lineages),
            "new_arms": [row["arm_id"] for row in additions],
            "minimum_bibliographic_target_met": (
                total >= targets["articles_per_family"] and len(lineages) >= targets["lineages_per_family"]
            ),
            "new_context_observations": sum(by_arm[row["arm_id"]] for row in additions),
            "coverage_new": {stage: dict(sorted(Counter(
                "not_applicable" if row[stage].startswith("NA:") else
                "not_reported" if row[stage] == "NR" or row[stage].startswith("NR:") else "recorded"
                for row in additions
            ).items())) for stage in METHOD["SURVEY"]["STAGES"]},
        }
    return {
        "prior_exclusion_count": 972,
        "prior_exclusion_sha256": sha256((ROUND / "excluded-972.psv").read_bytes()).hexdigest(),
        "api_discovery_records": len(candidates),
        "prior_unique_articles_in_families": len({row["source"] for row in baseline}),
        "new_unique_articles_in_families": len(sources),
        "new_family_memberships": len(new),
        "total_unique_articles_in_families": len({row["source"] for row in baseline}) + len(sources),
        "screening_decisions": dict(sorted(Counter(row["decision"] for row in screening).items())),
        "downloaded_documents_in_manifests": sum(
            bool(source["document"].get("local_path")) for source in sources.values()
        ) + len(reviewed_documents),
        "observations": dict(sorted(Counter(x["status"] for x in observations.values()).items())),
        "families": families,
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, help="Private location of the downloaded originals.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = audit(args.cache)
    path = ROUND / "audit.json"
    if args.check:
        if read_json(path) != report:
            raise ValueError("External round audit differs from computed data")
    else:
        SEARCH["save_json"](path, report)
    print(f'{report["new_unique_articles_in_families"]} new articles, '
          f'{report["new_family_memberships"]} family memberships, '
          f'{report["total_unique_articles_in_families"]} total unique articles')
    for family, row in report["families"].items():
        print(f'{family}: {row["before"]} + {row["new"]} = {row["articles"]}, '
              f'{row["lineages"]} lineages, bibliographic target={row["minimum_bibliographic_target_met"]}')


if __name__ == "__main__":
    main()
