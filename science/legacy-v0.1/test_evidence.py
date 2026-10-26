import copy
import unittest
from evidence import STAGES, audit_record, compile_topology, convert, grouped_partition, manifest_hash


def valid_record():
    return {"id": "fixture", "study_id": "study", "leakage_group_id": "original-experiment",
            "source_id": "source", "source_locator": "Table 1", "status": "verified",
            "evidence_access": "full_text", "rights_review": "cleared", "experimental_scope": "full_cell_mfc",
            "observations": [{"metric": "maximum_cell_power_density", "value": .5, "unit": "W/m2",
                              "kind": "measurement_derived", "area_basis": "anode_geometric", "locator": "Table 1"}]}


class EvidenceTests(unittest.TestCase):
    def test_units(self):
        self.assertEqual(convert(.04, "S/cm", "S/m"), 4)
        self.assertEqual(convert(10, "Ohm cm2", "Ohm m2"), .001)
        self.assertAlmostEqual(convert(262, "mW/m2", "W/m2"), .262)
        self.assertEqual(convert(1, "m2/g", "m2/kg"), 1000)

    def test_units_do_not_guess(self):
        with self.assertRaises(ValueError): convert(2, "mg/L COD", "mol/m3 acetate")
        with self.assertRaises(ValueError): convert(True, "m", "m")

    def test_verified_fixture_eligible(self):
        self.assertTrue(audit_record(valid_record())["training_eligible"])

    def test_unreviewed_never_promoted(self):
        r = valid_record(); r["status"] = "candidate"
        self.assertFalse(audit_record(r)["training_eligible"])

    def test_three_electrode_not_cell_power(self):
        r = valid_record(); r["experimental_scope"] = "three_electrode_bes"
        self.assertIn("half_cell_cannot_be_cell_power", audit_record(r)["issues"])

    def test_unknown_area_blocks(self):
        r = valid_record(); r["observations"][0]["area_basis"] = None
        self.assertFalse(audit_record(r)["training_eligible"])

    def test_half_cell_potential_requires_reference(self):
        r = valid_record(); r["observations"][0]["metric"] = "anode_potential"
        self.assertIn("missing_reference_electrode", audit_record(r)["issues"])

    def test_ce_is_flagged_not_clipped(self):
        r = valid_record(); r["observations"][0].update(metric="coulombic_efficiency", value=1.1, unit="1")
        self.assertIn("ce_requires_balance_review", audit_record(r)["issues"])
        self.assertEqual(r["observations"][0]["value"], 1.1)

    def test_uncertainty_is_not_assumed_sd(self):
        r = valid_record(); r["observations"][0]["uncertainty"] = .01
        self.assertIn("unspecified_uncertainty_type", audit_record(r)["issues"])

    def test_full_method_access_required(self):
        r = valid_record(); r["evidence_access"] = "abstract"
        self.assertFalse(audit_record(r)["training_eligible"])

    def test_nonfinite_rejected(self):
        r = valid_record(); r["observations"][0]["value"] = float("nan")
        self.assertIn("nonfinite_observation", audit_record(r)["issues"])

    def test_group_split_keeps_related_papers_together(self):
        rows = [{"id": "paper1-curve1", "leakage_group_id": "experimentA"},
                {"id": "paper2-republished-curve", "leakage_group_id": "experimentA"},
                {"id": "paper3", "leakage_group_id": "experimentB"}]
        train, test = grouped_partition(rows, {"experimentA"})
        self.assertEqual(len(test), 2); self.assertEqual(len(train), 1)
        self.assertFalse({r["leakage_group_id"] for r in train} & {r["leakage_group_id"] for r in test})

    def test_single_study_cannot_validate_generalization(self):
        with self.assertRaises(ValueError): grouped_partition([{"leakage_group_id": "A"}], {"A"})

    def test_unknown_holdout_rejected(self):
        with self.assertRaises(ValueError): grouped_partition([{"leakage_group_id": "A"}], {"B"})

    def test_four_topologies_keep_eleven_stages(self):
        for chambers, env, membrane in [(2,"liquid","cem"),(1,"ambient_air","none"),
                                       (2,"controlled_gas","separator"),(1,"liquid","none")]:
            result = compile_topology({"chambers":chambers,"cathode_environment":env,"membrane":membrane})
            self.assertEqual(result["stage_order"], list(STAGES))
            self.assertEqual(result["solver_status"], "not_implemented")

    def test_shared_medium_not_double_counted(self):
        t = compile_topology({"chambers":1,"cathode_environment":"liquid","membrane":"none"})
        self.assertEqual(t["stage_state"]["catholyte"], "shared_with_anolyte")
        self.assertEqual(t["stage_state"]["cathode_chamber"], "not_separate")

    def test_gas_requires_its_balance(self):
        t = compile_topology({"chambers":2,"cathode_environment":"controlled_gas","membrane":"cem"})
        self.assertIn("finite_headspace_gas_balance", t["required_modules"])
        self.assertEqual(t["stage_state"]["catholyte"], "not_applicable")

    def test_mfc_does_not_silently_become_mec(self):
        with self.assertRaises(ValueError):
            compile_topology({"chambers":2,"cathode_environment":"liquid","membrane":"cem","external_bias_V":.8})

    def test_manifest_stable_but_sensitive(self):
        self.assertEqual(manifest_hash({"a":1,"b":2}), manifest_hash({"b":2,"a":1}))
        self.assertNotEqual(manifest_hash({"a":1}), manifest_hash({"a":2}))


if __name__ == "__main__": unittest.main()
