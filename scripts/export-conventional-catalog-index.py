"""Generate readable article decisions and evidence tables from the frozen MFC catalog."""
import csv
import gzip
import json
from collections import defaultdict
from io import StringIO
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "research" / "conventional-arms"
CATALOG = DATA / "catalog"
INDEX_FILES = (
    "approved-F1-F6.psv",
    "excluded-F1-F6.psv",
    "pending-F1-F6.psv",
    "registered-observations.psv",
    "external-expansion-arms-index.psv",
)


def read_table(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="|"))


def doi_key(value):
    return (value or "").strip().lower().removeprefix("https://doi.org/").removeprefix("http://doi.org/")


def render_table(columns, rows):
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, delimiter="|", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def write_table(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(render_table(columns, rows))


def build_index(output=CATALOG):
    publications = read_table(output / "publications.psv.gz")
    reviews = read_table(output / "reviews.psv")
    pub_by_key, pub_by_alias = {}, {}
    for pub in publications:
        pub_by_key[pub["key"]] = pub
        for kind in ("doi", "pmcid", "pmid"):
            for value in (pub.get(kind) or "").split():
                if value == "NR":
                    continue
                canonical = doi_key(value) if kind == "doi" else value.upper() if kind == "pmcid" else value
                pub_by_alias[(kind, canonical)] = pub

    def publication_for_key(key):
        if key in pub_by_key:
            return pub_by_key[key]
        if key.startswith("10."):
            return pub_by_alias.get(("doi", doi_key(key)))
        if key.upper().startswith("PMC"):
            return pub_by_alias.get(("pmcid", key.upper()))
        if key.isdecimal():
            return pub_by_alias.get(("pmid", key))
        return None

    review_by_key = {}
    for review in reviews:
        pub = publication_for_key(review["key"])
        if pub is None:
            raise ValueError(f"Review index cannot resolve publication {review['key']}")
        if pub["key"] in review_by_key:
            raise ValueError(f"Repeated article review for {pub['key']}")
        review_by_key[pub["key"]] = review

    source_by_id = {}
    for name in ("sources.json", "targeted-sources.json", "methods-expansion/sources.json",
                 "external-expansion/sources.json"):
        path = DATA / name
        if not path.exists():
            continue
        for source in json.loads(path.read_text(encoding="utf-8")):
            ref = source.get("sample_id") or source.get("source")
            if ref:
                prior = source_by_id.get(ref)
                if prior and doi_key(prior.get("doi")) != doi_key(source.get("doi")):
                    raise ValueError(f"Conflicting source identifiers for {ref}")
                source_by_id[ref] = source

    arm_groups = (
        ("survey", DATA / "arms.psv"),
        ("targeted", DATA / "targeted-arms.psv"),
        ("methods", DATA / "methods-expansion/arms.psv"),
        ("external", DATA / "external-expansion/arms.psv"),
        ("catalog", output / "arms.psv"),
    )
    arms_by_id, arms_by_pub = {}, defaultdict(list)
    external_arms = []
    for registry, path in arm_groups:
        if not path.exists():
            continue
        for arm in read_table(path):
            if arm["arm_id"] in arms_by_id:
                raise ValueError(f"Repeated article arm ID {arm['arm_id']}")
            source = arm["source"]
            doi = source if source.startswith("10.") else (source_by_id.get(source) or {}).get("doi", "")
            pub = pub_by_alias.get(("doi", doi_key(doi)))
            if pub is None:
                raise ValueError(f"Arm source cannot be resolved to a catalog article: {arm['arm_id']}")
            enriched = dict(arm, _registry=registry, _doi=doi_key(doi), _pub_key=pub["key"])
            arms_by_id[arm["arm_id"]] = enriched
            arms_by_pub[pub["key"]].append(enriched)
            if registry == "external":
                external_arms.append(enriched)

    observation_groups = (
        ("methods-expansion", DATA / "methods-expansion/observations.psv"),
        ("external-expansion", DATA / "external-expansion/observations.psv"),
        ("catalog", output / "observations.psv"),
    )
    observations_by_pub, observations_by_arm = defaultdict(list), defaultdict(list)
    observation_rows = []
    for registry, path in observation_groups:
        if not path.exists():
            continue
        for observation in read_table(path):
            arm = arms_by_id.get(observation["arm_id"])
            if arm is None:
                raise ValueError(f"Observation lacks a registered arm: {observation['id']}")
            pub = pub_by_key[arm["_pub_key"]]
            observations_by_pub[pub["key"]].append(observation)
            observations_by_arm[arm["arm_id"]].append(observation)
            observation_rows.append({
                "id": observation["id"], "doi": pub["doi"], "pmcid": pub["pmcid"],
                "pmid": pub["pmid"], "title": pub["title"], "year": pub["year"],
                "catalog_decision": "admitted_F1_F6" if pub["families"] != "NR"
                    else review_by_key.get(pub["key"], {}).get("decision", "not_reviewed"),
                "families": pub["families"], "registry": registry,
                "arm_id": arm["arm_id"], "designation": arm["designation"], "role": arm["role"],
                "liquid_domains": arm["liquid_domains"], "acceptor": arm["acceptor"],
                "feed": arm["feed"], "anode_form": arm["anode_form"],
                "cathode_support": arm["cathode_support"], "cathode_active": arm["cathode_active"],
                "separator": arm["separator"], "feeding": arm["feeding"],
                "external_circuit": arm["external_circuit"], "metric": observation["metric"],
                "value": observation["value"], "spread_or_upper": observation["spread_or_upper"],
                "statistic": observation["statistic"], "unit": observation["unit"],
                "basis": observation["basis"], "phase": observation["phase"],
                "n_reactors": observation["n_reactors"], "load_ohm": observation["load_ohm"],
                "status": observation["status"], "locator": observation["locator"],
                "extraction": observation["extraction"], "notes": observation["notes"],
            })

    def arm_count(pub_key, registry):
        return sum(arm["_registry"] == registry for arm in arms_by_pub[pub_key])

    def data_summary(pub_key):
        entries = []
        for observation in sorted(observations_by_pub[pub_key], key=lambda row: (row["metric"], row["id"])):
            value = observation["metric"] + "=" + observation["value"]
            if observation["spread_or_upper"] != "NR":
                value += "±" + observation["spread_or_upper"]
            entries.append(f"{value} {observation['unit']} [{observation['arm_id']}; {observation['status']}]")
        return "; ".join(entries) or "no_registered_numeric_observation"

    approved = [pub for pub in publications if pub["families"] != "NR"]
    approved_rows = []
    for pub in sorted(approved, key=lambda row: (row["doi"] == "NR", doi_key(row["doi"]), row["key"])):
        pub_arms = arms_by_pub[pub["key"]]
        pub_observations = observations_by_pub[pub["key"]]
        approved_rows.append({
            "key": pub["key"], "doi": pub["doi"], "pmcid": pub["pmcid"], "pmid": pub["pmid"],
            "title": pub["title"], "year": pub["year"], "families": pub["families"],
            "document_state": pub["document"], "reading_scopes": pub["reading_scopes"],
            "survey_arm_rows": arm_count(pub["key"], "survey"),
            "targeted_arm_rows": arm_count(pub["key"], "targeted"),
            "methods_arm_rows": arm_count(pub["key"], "methods"),
            "external_expansion_arm_rows": arm_count(pub["key"], "external"),
            "catalog_arm_rows": arm_count(pub["key"], "catalog"),
            "registered_observation_rows": len(pub_observations),
            "metrics_found": " ".join(sorted({row["metric"] for row in pub_observations})) or "NR",
            "reported_values": data_summary(pub["key"]),
            "source": "https://doi.org/" + doi_key(pub["doi"]) if pub["doi"] != "NR" else "NR",
        })

    decision_columns = ["key", "doi", "pmcid", "pmid", "title", "year", "families_considered",
                        "scope", "decision", "document_state", "reading_scopes", "locator", "reason", "source"]
    decision_rows = {"exclude": [], "pending": []}
    for review in reviews:
        if review["decision"] not in decision_rows:
            continue
        pub = publication_for_key(review["key"])
        decision_rows[review["decision"]].append({
            "key": pub["key"], "doi": pub["doi"], "pmcid": pub["pmcid"], "pmid": pub["pmid"],
            "title": pub["title"], "year": pub["year"], "families_considered": review["families_considered"],
            "scope": review["scope"], "decision": review["decision"],
            "document_state": pub["document"], "reading_scopes": pub["reading_scopes"],
            "locator": review["locator"], "reason": review["reason"], "source": review["source"],
        })

    arm_index_columns = ["article_key", "doi", "pmcid", "pmid", "title", "year", "article_decision",
                         "families", "registry", "source_ref", "arm_id", "designation", "role", "lineage",
                         "liquid_domains", "acceptor", "feed", "anode_form", "cathode_support",
                         "cathode_active", "separator", "feeding", "locators", "anode_chamber",
                         "anolyte", "anode", "anode_catalyst", "biofilm", "membrane",
                         "external_circuit", "cathode_chamber", "catholyte", "cathode", "cathode_catalyst",
                         "registered_observation_rows", "registered_observation_ids"]
    external_rows = []
    for arm in sorted(external_arms, key=lambda row: (row["_doi"], row["arm_id"])):
        pub = pub_by_key[arm["_pub_key"]]
        observations = observations_by_arm[arm["arm_id"]]
        external_rows.append({
            "article_key": pub["key"], "doi": pub["doi"], "pmcid": pub["pmcid"], "pmid": pub["pmid"],
            "title": pub["title"], "year": pub["year"],
            "article_decision": "admitted_F1_F6" if pub["families"] != "NR"
                else review_by_key.get(pub["key"], {}).get("decision", "not_reviewed"),
            "families": pub["families"], "registry": "external-expansion", "source_ref": arm["source"],
            **{field: arm[field] for field in arm_index_columns if field in arm},
            "registered_observation_rows": len(observations),
            "registered_observation_ids": " ".join(row["id"] for row in observations) or "NR",
        })

    observation_columns = list(observation_rows[0]) if observation_rows else []
    outputs = {
        "approved-F1-F6.psv": ([*approved_rows[0]] if approved_rows else [], approved_rows),
        "excluded-F1-F6.psv": (decision_columns, sorted(decision_rows["exclude"], key=lambda row: (row["title"].casefold(), row["key"]))),
        "pending-F1-F6.psv": (decision_columns, sorted(decision_rows["pending"], key=lambda row: (row["title"].casefold(), row["key"]))),
        "registered-observations.psv": (observation_columns, sorted(observation_rows, key=lambda row: (row["doi"], row["registry"], row["id"]))),
        "external-expansion-arms-index.psv": (arm_index_columns, external_rows),
    }
    return outputs


def export(output=CATALOG):
    for name, (columns, rows) in build_index(output).items():
        write_table(output / name, columns, rows)


def check(output=CATALOG):
    for name, (columns, rows) in build_index(output).items():
        path = output / name
        if not path.exists() or path.read_bytes() != render_table(columns, rows):
            raise ValueError(f"Generated article index is stale: {path.name}")


if __name__ == "__main__":
    export()
