"""Validate the conventional-arm survey and reproduce study and lineage counts."""
from collections import Counter, defaultdict
from csv import DictReader
from hashlib import sha256
from pathlib import Path
import argparse
import json
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "research" / "conventional-arms"
STAGES = (
    "anode_chamber", "anolyte", "anode", "anode_catalyst", "biofilm", "membrane",
    "external_circuit", "cathode_chamber", "catholyte", "cathode", "cathode_catalyst",
)
TOPOLOGY = ("liquid_domains", "acceptor")
FEED_GROUP = (*TOPOLOGY, "feed")
ARM_GROUP = (*FEED_GROUP, "anode_form", "cathode_active", "feeding")
DETAILED_GROUP = (*ARM_GROUP, "cathode_support", "separator")
UNRESOLVED = {"unknown", "aem_unknown", "cem_unknown", "pem_unknown", "other_reported", "ami_7000"}
ROLES = {"explicit_control", "pre_intervention", "standard_comparator"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_table(path):
    with path.open(encoding="utf-8", newline="") as file:
        reader = DictReader(file, delimiter="|")
        columns = reader.fieldnames
        rows = list(reader)
    if not columns or len(columns) != len(set(columns)):
        raise ValueError(f"Invalid columns in {path.name}")
    if any(None in row or any(not value or value != value.strip() for value in row.values()) for row in rows):
        raise ValueError(f"Empty, untrimmed or extra value in {path.name}")
    return columns, rows


def index(rows, column):
    result = {row[column]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Repeated {column}")
    return result


def validate_batch(prefix, sources, cache):
    columns, arms = read_table(DATA / f"{prefix}arms.psv")
    _, screen = read_table(DATA / f"{prefix}screening.psv")
    if tuple(columns[-len(STAGES):]) != STAGES:
        raise ValueError(f"Stage order changed in {prefix}arms.psv")
    index(arms, "arm_id")
    screen = index(screen, "source")
    if screen.keys() != sources.keys():
        raise ValueError(f"Screening and acquisition inventories differ for {prefix or 'neutral'}")
    if any(row["decision"] not in {"included", "excluded", "pending"} for row in screen.values()):
        raise ValueError("Unknown screening decision")
    if {row["source"] for row in arms} != {key for key, row in screen.items() if row["decision"] == "included"}:
        raise ValueError("Included papers and documented arms differ")
    for row in arms:
        key = row["source"]
        if not row["arm_id"].startswith(key + "-") or row["role"] not in ROLES:
            raise ValueError(f"Invalid arm identity or role: {row['arm_id']}")
        document = sources[key]
        pdf_review = document.get("web_review", {}).get("format") == "publisher full PDF"
        if not (document.get("full_text") or pdf_review and row["locators"].startswith("PDF pp.")):
            raise ValueError(f"No acquired primary article or locator: {key}")
        if row["liquid_domains"] not in {"1", "2"}:
            raise ValueError(f"Unresolved liquid domains: {key}")
        if row["liquid_domains"] == "2" and row["catholyte"].startswith("NA:"):
            raise ValueError(f"Two liquid domains without catholyte: {key}")
        if row["separator"] == "none" and not row["membrane"].startswith("NA:"):
            raise ValueError(f"Explicitly absent separator without reason: {key}")
        if cache and document.get("full_text"):
            aid = read_json(cache / "paragraphs" / f"{key}.json")
            known = {p["id"] for p in aid}
            cited = set(re.findall(r"\bP\d{3}\b", row["locators"]))
            if not cited or not cited <= known:
                raise ValueError(f"Invalid JATS paragraph reference: {row['arm_id']} {cited - known}")
    return arms, screen


def count_by(arms, columns):
    groups = defaultdict(list)
    for arm in arms:
        key = tuple(arm[column] for column in columns)
        if not UNRESOLVED.intersection(key):
            groups[key].append(arm)
    rows = []
    for key, matched in groups.items():
        studies = sorted({arm["source"] for arm in matched})
        lineages = sorted({arm["lineage"] for arm in matched})
        rows.append({
            **dict(zip(columns, key)), "studies": len(studies), "lineages": len(lineages),
            "sources": studies, "arm_ids": sorted(arm["arm_id"] for arm in matched),
        })
    return sorted(rows, key=lambda row: (-row["studies"], -row["lineages"], tuple(row[k] for k in columns)))


def summarize(arms, screen, sources):
    studies = {arm["source"] for arm in arms}
    return {
        "records": len(sources),
        "full_text_xml": sum(bool(row.get("full_text")) for row in sources.values()),
        "full_pdf_preserved": sum(bool(row.get("pdf")) for row in sources.values()),
        "full_pdf_web_read": sum(
            row.get("web_review", {}).get("format") == "publisher full PDF" for row in sources.values()
        ),
        "screening": dict(sorted(Counter(row["decision"] for row in screen.values()).items())),
        "arms": len(arms), "studies": len(studies), "lineages": len({arm["lineage"] for arm in arms}),
        "missing_by_classification_field": {
            field: sum(row[field] in UNRESOLVED for row in arms) for field in DETAILED_GROUP
        },
        "stage_status": {
            stage: dict(sorted(Counter(
                "not_reported" if arm[stage] == "NR" or arm[stage].startswith("NR:")
                else "not_applicable" if arm[stage].startswith("NA:")
                else "recorded"
                for arm in arms
            ).items()))
            for stage in STAGES
        },
        "topologies": count_by(arms, TOPOLOGY),
        "feeds_within_topology": count_by(arms, FEED_GROUP),
        "joint_arms": count_by(arms, ARM_GROUP),
        "joint_arms_with_support_and_separator": count_by(arms, DETAILED_GROUP),
        "explicit_control_topologies": count_by(
            (arm for arm in arms if arm["role"] == "explicit_control"), TOPOLOGY
        ),
        "explicit_control_joint_arms": count_by(
            (arm for arm in arms if arm["role"] == "explicit_control"), ARM_GROUP
        ),
    }


def validate_originals(sources, cache):
    for row in sources.values():
        if row.get("full_text"):
            path = cache / "originals" / f"{row['pmcid']}.xml"
            expected = row
        elif row.get("pdf"):
            path = cache / f"{row['sample_id']}.pdf"
            expected = row["pdf"]
        else:
            continue
        data = path.read_bytes()
        if len(data) != expected["bytes"] or sha256(data).hexdigest() != expected["sha256"]:
            raise ValueError(f"Document identity changed: {row['sample_id']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the committed result without rewriting it.")
    parser.add_argument("--cache", type=Path, help="Also verify the original JATS bytes and paragraph locators.")
    args = parser.parse_args()
    frame = read_json(DATA / "frame.json")
    survey = runpy.run_path(str(ROOT / "scripts" / "survey-conventional-arms.py"))
    draw, strata = survey["sample_frame"](frame["frame"])
    if len(index(frame["frame"], "key")) != frame["unique_records"] or strata != frame["strata"]:
        raise ValueError("Frozen search frame metadata differs from the reconstructed draw")
    neutral = index(read_json(DATA / "sources.json"), "sample_id")
    targeted = index(read_json(DATA / "targeted-sources.json"), "sample_id")
    if [row["key"] for row in neutral.values()] != [row["key"] for row in draw]:
        raise ValueError("Acquired sample differs from frozen draw")
    identified = [row for row in (*neutral.values(), *targeted.values()) if row.get("key")]
    index(identified, "key")
    index([row for row in identified if row.get("pmcid")], "pmcid")
    if args.cache:
        validate_originals(neutral | targeted, args.cache)
    arms, screen = validate_batch("", neutral, args.cache)
    crosscheck, crosscheck_screen = validate_batch("targeted-", targeted, args.cache)
    all_arms = index(arms + crosscheck, "arm_id")
    _, issues = read_table(DATA / "quality.psv")
    for issue in issues:
        if all_arms[issue["arm_id"]]["source"] != issue["source"]:
            raise ValueError(f"Quality issue references a different article: {issue['arm_id']}")
    attachments = index(read_json(DATA / "attachments.json"), "source")
    if not attachments.keys() <= (neutral | targeted).keys():
        raise ValueError("Supplement without a known article")
    if args.cache:
        for key, attachment in attachments.items():
            path = args.cache / f"{key}-{attachment['entry']}"
            if sha256(path.read_bytes()).hexdigest() != attachment["sha256"]:
                raise ValueError(f"Supplement identity changed: {key}")
    by_era = {}
    for stratum in strata:
        ids = {key for key, row in neutral.items() if row["era"] == stratum["era"]}
        era_arms = [arm for arm in arms if arm["source"] in ids]
        by_era[stratum["era"]] = {
            **stratum, "included_studies": len({arm["source"] for arm in era_arms}),
            "topologies": count_by(era_arms, TOPOLOGY),
        }
    outcome = {
        "version": "conventional-arm-survey/1.0.0",
        "searched": frame["searched"], "universe_open_access_hits": frame["raw_hits"],
        "quality_issues": dict(sorted(Counter(row["status"] for row in issues).items())),
        "supplements_reviewed": len(attachments),
        "active_families": read_json(DATA / "selection.json")["active_families"],
        "neutral": {**summarize(arms, screen, neutral), "eras": by_era},
        "targeted": summarize(crosscheck, crosscheck_screen, targeted),
    }
    if outcome["active_families"]:
        raise ValueError("The survey must not silently activate a reference family")
    output = DATA / "audit.json"
    expected = json.dumps(outcome, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if output.read_text(encoding="utf-8") != expected:
            raise ValueError("Survey result out of date")
    else:
        temporary = output.with_suffix(".json.part")
        temporary.write_text(expected, encoding="utf-8")
        temporary.replace(output)
    for batch in ("neutral", "targeted"):
        result = outcome[batch]
        print(f"{batch}: {result['records']} records, {result['full_text_xml']} JATS, "
              f"{result['studies']} studies, {result['arms']} conventional arms, "
              f"{result['lineages']} documented lineages")


if __name__ == "__main__":
    main()
