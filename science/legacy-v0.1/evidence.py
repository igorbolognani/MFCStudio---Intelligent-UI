"""MFC Studio: evidence admission and topology contracts, NOT a predictor.

Standard-library only. Experimental seeds remain candidates. No function here
turns a paper value into a universal material coefficient.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

STAGES = (
    "anode_chamber", "anolyte", "anode", "anode_catalyst", "biofilm",
    "membrane", "external_circuit", "cathode_chamber", "catholyte",
    "cathode", "cathode_catalyst",
)
UNIT_CONVERSIONS = {
    ("S/cm", "S/m"): 100.0,
    ("mS/cm", "S/m"): 0.1,
    ("cm2", "m2"): 1e-4,
    ("cm", "m"): 1e-2,
    ("um", "m"): 1e-6,
    ("mW/m2", "W/m2"): 1e-3,
    ("mOhm m2", "Ohm m2"): 1e-3,
    ("Ohm cm2", "Ohm m2"): 1e-4,
    ("m2/g", "m2/kg"): 1000.0,
    ("kC", "C"): 1000.0,
    ("mM", "mol/m3"): 1.0,
}
AREAL_TARGETS = {
    "maximum_anode_current_density", "maximum_cell_power_density",
    "eps_anode_areal_resistance", "eps_cathode_areal_resistance",
    "eps_solution_areal_resistance",
}
POTENTIAL_TARGETS = {"anode_potential", "cathode_potential"}
VALID_SCOPES = {"material_characterization", "three_electrode_bes", "full_cell_mfc", "soil_mfc"}
VALID_STATUSES = {"candidate", "reviewed", "verified", "rejected"}
VALID_KINDS = {"measured", "measurement_derived", "fitted", "simulated", "assumed"}
VALID_AREAS = {"anode_geometric", "cathode_geometric", "projected_cross_section", "electrochemically_active"}


def convert(value: float, source: str, target: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("value must be a finite number")
    if source == target:
        return float(value)
    try:
        return value * UNIT_CONVERSIONS[source, target]
    except KeyError as exc:
        raise ValueError(f"unsupported conversion: {source} -> {target}") from exc


def compile_topology(config: dict) -> dict:
    """Compile which of the eleven configuration stages describe active domains.

    This is an interface/data contract. It does not claim these domains are solved.
    Single-chamber immersed cathodes share the anolyte; a second independent
    catholyte volume must not be silently invented.
    """
    chambers = config.get("chambers")
    env = config.get("cathode_environment")
    membrane = config.get("membrane")
    if isinstance(chambers, bool) or chambers not in (1, 2):
        raise ValueError("chambers must be 1 or 2")
    if env not in {"liquid", "ambient_air", "controlled_gas"}:
        raise ValueError("unknown cathode environment")
    if membrane not in {"none", "cem", "aem", "separator"}:
        raise ValueError("unknown membrane/separator type")
    bias = config.get("external_bias_V", 0)
    if isinstance(bias, bool) or not isinstance(bias, (int, float)) or not math.isfinite(bias) or bias != 0:
        raise ValueError("this MFC scope excludes an applied electrolysis bias")
    feed = config.get("feed_regime", "batch")
    if feed not in {"batch", "continuous", "fed_batch"}:
        raise ValueError("unknown feed regime")
    stage_state = {s: "active" for s in STAGES}
    if chambers == 1:
        stage_state["cathode_chamber"] = "not_separate"
    if env != "liquid":
        stage_state["catholyte"] = "not_applicable"
    elif chambers == 1:
        stage_state["catholyte"] = "shared_with_anolyte"
    if membrane == "none":
        stage_state["membrane"] = "absent"
    required = ["electrical_closure", "anode_biokinetics", "substrate_balance", "ionic_path", "cathodic_reaction"]
    required.append({"liquid": "dissolved_oxygen_or_declared_acceptor", "ambient_air": "gas_diffusion_water_balance", "controlled_gas": "finite_headspace_gas_balance"}[env])
    if membrane != "none":
        required += ["membrane_transport", "oxygen_crossover"]
    if feed == "continuous":
        required.append("inflow_outflow_balance")
    if feed == "fed_batch":
        required.append("feeding_events")
    return {"stage_order": list(STAGES), "stage_state": stage_state,
            "required_modules": required, "solver_status": "not_implemented"}


def audit_record(record: dict) -> dict:
    """Check semantic essentials. These checks do not certify an experiment."""
    issues = []
    for key in ("id", "study_id", "leakage_group_id", "source_id", "source_locator"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            issues.append("missing_" + key)
    if record.get("status") not in VALID_STATUSES:
        issues.append("invalid_status")
    if record.get("experimental_scope") not in VALID_SCOPES:
        issues.append("invalid_experimental_scope")
    if record.get("evidence_access") not in {"full_text", "abstract", "metadata"}:
        issues.append("invalid_evidence_access")
    observations = record.get("observations", [])
    if not isinstance(observations, list) or not observations:
        issues.append("no_observations")
        observations = []
    for obs in observations:
        value = obs.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            issues.append("nonfinite_observation")
        if not isinstance(obs.get("unit"), str) or not obs.get("unit"):
            issues.append("missing_unit")
        if obs.get("kind") not in VALID_KINDS:
            issues.append("invalid_evidence_kind")
        if not obs.get("locator"):
            issues.append("missing_observation_locator")
        if obs.get("metric") in AREAL_TARGETS and obs.get("area_basis") not in VALID_AREAS:
            issues.append("unknown_area_basis")
        if obs.get("metric") in POTENTIAL_TARGETS and not obs.get("reference_electrode"):
            issues.append("missing_reference_electrode")
        if obs.get("metric") == "maximum_cell_power_density" and record.get("experimental_scope") != "full_cell_mfc":
            issues.append("half_cell_cannot_be_cell_power")
        if obs.get("metric") == "coulombic_efficiency" and isinstance(value, (int, float)):
            if obs.get("unit") != "1":
                issues.append("ce_must_be_fraction")
            if value > 1 or value < 0:
                issues.append("ce_requires_balance_review")
        if obs.get("uncertainty") is not None and not obs.get("uncertainty_type"):
            issues.append("unspecified_uncertainty_type")
    if record.get("evidence_access") != "full_text":
        issues.append("incomplete_methods_access")
    if record.get("rights_review") != "cleared":
        issues.append("rights_not_reviewed")
    eligible = record.get("status") == "verified" and not issues
    return {"id": record.get("id"), "issues": sorted(set(issues)),
            "training_eligible": eligible, "certifies_scientific_accuracy": False}


def grouped_partition(records: list[dict], held_out_groups: set[str]) -> tuple[list[dict], list[dict]]:
    """Hold out whole provenance families, never individual curve points.

    A group can contain several articles/datasets from the same experiment.
    Caller supplies the grouping after provenance review.
    """
    if not records or not held_out_groups:
        raise ValueError("records and explicit holdout groups are required")
    all_groups = {r.get("leakage_group_id") for r in records}
    if not all(isinstance(g, str) and g for g in all_groups):
        raise ValueError("every record needs a leakage_group_id")
    if not held_out_groups <= all_groups:
        raise ValueError("unknown holdout group")
    if held_out_groups == all_groups:
        raise ValueError("no training groups remain")
    train = [r for r in records if r["leakage_group_id"] not in held_out_groups]
    test = [r for r in records if r["leakage_group_id"] in held_out_groups]
    return train, test


def manifest_hash(payload: dict | list) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


if __name__ == "__main__":
    base = Path(__file__).parent
    data = [json.loads(line) for line in (base / "evidence_seed.jsonl").read_text().splitlines() if line]
    print(json.dumps({"records": len(data), "audits": [audit_record(r) for r in data],
                      "seed_sha256": manifest_hash(data), "predictor_trained": False}, ensure_ascii=False, indent=2))
