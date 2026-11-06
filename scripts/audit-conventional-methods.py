"""Verify the methods-led conventional-arm expansion and reproduce its counts."""
import argparse
from collections import Counter
from decimal import Decimal
from hashlib import sha256
import json
import re
import runpy
from pathlib import Path

SURVEY = runpy.run_path(str(Path(__file__).with_name("audit-conventional-arms.py")))
DATA = SURVEY["DATA"]
ROUND = DATA / "methods-expansion"
read_table = SURVEY["read_table"]
read_json = SURVEY["read_json"]
index = SURVEY["index"]

FAMILY_KEYS = {
    ("1", "ambient_air", "acetate", "carbon_cloth", "platinum", "fed_batch"): "F1",
    ("1", "ambient_air", "acetate", "carbon_paper", "platinum", "fed_batch"): "F2",
    ("1", "ambient_air", "acetate", "carbon_brush", "activated_carbon", "fed_batch"): "F3",
    ("1", "ambient_air", "acetate", "carbon_brush", "platinum", "fed_batch"): "F4",
    ("1", "ambient_air", "glucose", "carbon_brush", "platinum", "fed_batch"): "F5",
    ("2", "ferricyanide", "acetate", "carbon_felt", "bare_carbon", "fed_batch"): "F6",
}
FULL_METHODS = {"full_methods", "full_methods_web"}
UNITS = {
    "voltage": {"V", "mV"}, "peak_voltage": {"V", "mV"}, "current": {"mA"},
    "peak_current_density": {"mA/m2"}, "short_circuit_current_density": {"mA/m2"},
    "operating_power_density": {"mW/m2"}, "peak_power_density": {"W/m2", "mW/m2", "uW/cm2"},
    "charge_per_cycle": {"C"}, "time_to_stable_voltage": {"day"},
}


def table(name):
    return read_table(ROUND / name)[1]


def family(arm):
    return FAMILY_KEYS.get(tuple(arm[field] for field in SURVEY["ARM_GROUP"]))


def decimal(value):
    number = Decimal(str(value))
    if not number.is_finite() or number < 0:
        raise ValueError(f"Invalid nonnegative quantity {value}")
    return number


def project_axis(pixels, marks):
    (p0, v0), (p1, v1) = marks
    if p0 == p1:
        raise ValueError("Coincident axis marks")
    return Decimal(v0) + (Decimal(v1) - Decimal(v0)) * (pixels - p0) / (p1 - p0)


def digitize(series):
    points = series["pixels"]
    if [p[0] for p in points] != sorted({p[0] for p in points}):
        raise ValueError("Digitized points must be distinct and ordered by x")
    width, height = series["image_dimensions_px"]
    axes = series["axis_marks_px_value"]
    j_marks, p_marks = axes["current_density_A_m2"], axes["power_density_W_m2"]
    if not all(0 <= x < width and 0 <= y < height for x, y in points):
        raise ValueError("Pixel is outside the image")
    def convert(x, y):
        return {
            "current_density_A_m2": str(decimal(project_axis(x, j_marks)).quantize(Decimal("0.001"))),
            "power_density_W_m2": str(decimal(project_axis(y, p_marks)).quantize(Decimal("0.001"))),
        }
    return [convert(x, y) for x, y in points]


def check_cache(cache, acquisition, sources, figure):
    paths = [(cache / "originals" / f'{row["pmcid"]}.xml', row["sha256"])
             for row in acquisition if row["access"] == "jats"]
    paths.extend((cache / artifact["local_path"], artifact["sha256"])
                 for row in sources.values() for artifact in row.get("files", []))
    paths.append((cache / figure["image_local_path"], figure["image_sha256"]))
    for path, expected in paths:
        if sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Original bytes changed: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--cache", type=Path, help="Verify acquired original files by SHA-256.")
    args = parser.parse_args()
    former = index(read_table(DATA / "arms.psv")[1] + read_table(DATA / "targeted-arms.psv")[1], "arm_id")
    baseline = index(table("baseline-locators.psv"), "arm_id")
    if set(baseline) != {key for key, row in former.items() if family(row)}:
        raise ValueError("The baseline map must cover every earlier arm in the six families")
    for key, row in baseline.items():
        if (row["source"], row["family"]) != (former[key]["source"], family(former[key])):
            raise ValueError(f"Mismatched baseline locator {key}")

    sources = index(read_json(ROUND / "sources.json"), "source")
    index([row for row in sources.values() if row.get("doi")], "doi")
    reviews = index(table("reading-log.psv"), "source")
    if reviews.keys() != sources.keys():
        raise ValueError("Every read needs a source identity and access record")
    if any(row["decision"] not in {"include", "exclude", "pending"} for row in reviews.values()):
        raise ValueError("Unknown review decision")
    columns, additions = read_table(ROUND / "arms.psv")
    if tuple(columns[-len(SURVEY["STAGES"]):]) != SURVEY["STAGES"]:
        raise ValueError("Eleven stages missing or out of order")
    index([*former.values(), *additions], "arm_id")
    if {row["source"] for row in additions} != {k for k, r in reviews.items() if r["decision"] == "include"}:
        raise ValueError("Reviewed inclusions and recorded arms differ")
    old_sources = read_json(DATA / "sources.json") + read_json(DATA / "targeted-sources.json")
    old_dois = {row.get("doi") for row in old_sources if row.get("doi")}
    source_ids = set(sources) | {row["sample_id"] for row in old_sources}
    issues = index(table("quality.psv"), "id")
    if any(row["source"] not in source_ids for row in issues.values()):
        raise ValueError("Quality issue lacks source provenance")
    for row in additions:
        identity = row["source"]
        review = reviews[identity]
        if (
            not row["arm_id"].startswith(identity + "-")
            or row["role"] not in SURVEY["ROLES"] | {"standard_protocol"}
            or family(row) not in review["families"].split()
            or review["scope"] not in FULL_METHODS
            or not sources[identity].get("doi")
            or sources[identity]["doi"] in old_dois
        ):
            raise ValueError(f"Invalid or previously counted inclusion {row['arm_id']}")
        for field in ("methods_location", "arm_outcome_location"):
            if review[field] in {"NA", "NR"}:
                raise ValueError(f"Missing reviewed evidence location for {identity}")
        if row["separator"] == "none" and not row["membrane"].startswith("NA:"):
            raise ValueError(f"Explicit separator absence needs an applicability note: {identity}")
        if row["liquid_domains"] == "2" and row["catholyte"].startswith("NA:"):
            raise ValueError(f"Missing liquid cathode domain: {identity}")

    observations = index(table("observations.psv"), "id")
    included_arms = set(baseline) | {row["arm_id"] for row in additions}
    for obs in observations.values():
        if (
            obs["arm_id"] not in included_arms
            or obs["unit"] not in UNITS[obs["metric"]]
            or obs["status"] not in {"context_only", "quality_hold"}
            or obs["extraction"] != "manual_text_or_table"
        ):
            raise ValueError(f"Invalid observation {obs['id']}")
        value = decimal(obs["value"])
        if obs["spread_or_upper"] != "NR":
            upper = decimal(obs["spread_or_upper"])
            if obs["statistic"] == "reported_range" and value > upper:
                raise ValueError(f"Reversed range {obs['id']}")
        if obs["n_reactors"] != "NR" and not re.fullmatch(r"[1-9][0-9]*", obs["n_reactors"]):
            raise ValueError(f"Invalid replicate count {obs['id']}")
        if obs["load_ohm"] not in {"NR", "variable", "short_circuit"} and decimal(obs["load_ohm"]) == 0:
            raise ValueError(f"Load must be positive or an explicit circuit state: {obs['id']}")

    curve = read_json(ROUND / "series-M9141142.json")
    if curve["arm_id"] not in included_arms or digitize(curve) != curve["points"]:
        raise ValueError("The digital points must reproduce the reviewed Blank pixels")
    if curve["document_sha256"] not in {f["sha256"] for f in sources["M9141142"]["files"]}:
        raise ValueError("Digitized series lacks the source supplement identity")

    acquisition = table("acquisition.psv")
    index(acquisition, "key")
    index([row for row in acquisition if row["pmcid"] != "NR"], "pmcid")
    for row in acquisition:
        if (row["access"] == "jats") != bool(re.fullmatch(r"[a-f0-9]{64}", row["sha256"])):
            raise ValueError(f"Inconsistent XML state {row['key']}")
    search = read_json(ROUND / "search.json")
    if set(search["families"]) != set(FAMILY_KEYS.values()) or len(search["queries"]) != 2 * len(FAMILY_KEYS):
        raise ValueError("Missing section/body search routes")
    for query in search["queries"]:
        if (
            sum(page["returned"] for page in query["pages"]) != query["hits"]
            or sum(query["id"] in row["section_routes"].split() for row in acquisition) != query["hits"]
        ):
            raise ValueError(f"Search result has an incomplete page sequence: {query['id']}")
    if sum(row["section_routes"] != "NA" for row in acquisition) != search["unique_section_hits"]:
        raise ValueError("Section hit union differs from frozen manifest")
    if args.cache:
        check_cache(args.cache, acquisition, sources, curve)

    active = read_json(DATA / "selection.json")["active_families"]
    if active:
        raise ValueError("Methods research cannot activate a family")
    scalar_arms = {obs["arm_id"] for obs in observations.values() if obs["status"] == "context_only"}
    linked = scalar_arms | {curve["arm_id"]}
    results = {}
    for f in FAMILY_KEYS.values():
        base = [former[key] for key, row in baseline.items() if row["family"] == f]
        new = [row for row in additions if family(row) == f and row["role"] != "standard_protocol"]
        auxiliary = [row["arm_id"] for row in additions if family(row) == f and row["role"] == "standard_protocol"]
        merged = base + new
        results[f] = {
            "baseline_articles": len({row["source"] for row in base}),
            "new_articles": len({row["source"] for row in new}),
            "articles": len({row["source"] for row in merged}),
            "lineages": len({row["lineage"] for row in merged}),
            "new_arm_ids": [row["arm_id"] for row in new],
            "auxiliary_protocols": auxiliary,
            "articles_with_treated_values": len({row["source"] for row in merged if row["arm_id"] in linked}),
            "stage_status_new": {
                stage: dict(sorted(Counter(
                    "not_reported" if row[stage] == "NR" or row[stage].startswith("NR:")
                    else "not_applicable" if row[stage].startswith("NA:")
                    else "recorded" for row in new
                ).items())) for stage in SURVEY["STAGES"]
            },
        }

    counts = {
        "version": "mfc-conventional-methods/1.0.0",
        "date": search["date"],
        "indexed_jats": sum(row["access"] == "jats" for row in acquisition),
        "xml_unavailable": sum(row["access"] == "unavailable" for row in acquisition),
        "section_hits": search["unique_section_hits"],
        "reviewed_sources": len(reviews),
        "complete_methods": sum(row["scope"] in FULL_METHODS for row in reviews.values()),
        "review_decisions": dict(sorted(Counter(row["decision"] for row in reviews.values()).items())),
        "observations": dict(sorted(Counter(obs["status"] for obs in observations.values()).items())),
        "quality_issues": len(issues),
        "digitized_points": len(curve["points"]),
        "families": results,
        "active_families": active,
    }
    expected = json.dumps(counts, ensure_ascii=False, indent=2) + "\n"
    output = ROUND / "audit.json"
    if args.check:
        if output.read_text(encoding="utf-8") != expected:
            raise ValueError("The frozen methods audit differs from the reconstructed result")
    else:
        temporary = output.with_suffix(".json.part")
        temporary.write_text(expected, encoding="utf-8")
        temporary.replace(output)
    for f, row in results.items():
        print(f'{f}: {row["baseline_articles"]} + {row["new_articles"]} = {row["articles"]} articles, '
              f'{row["lineages"]} lineages, {row["articles_with_treated_values"]} with treated values')


if __name__ == "__main__":
    main()
