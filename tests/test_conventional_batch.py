import runpy
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/advance-conventional-catalog.py"
BATCH = runpy.run_path(str(SCRIPT))


def publication(key, document, decisions="unreviewed", scopes="NR"):
    return dict(key=key, title="Microbial fuel cell experiment", document=document,
                machine_signals="F6_methods:3", priority_previous="NR", open_route_indexed="yes",
                reading_scopes=scopes, decisions=decisions, families="NR", pending="yes", evidence="NR")


class ConventionalBatchTests(unittest.TestCase):
    def test_queue_separates_body_identity_review_and_admission(self):
        pending = publication("pending", "documented_integral", "pending", "full_methods")
        options = BATCH["queues"]([publication("no-body", "partial"),
                                   publication("uncertain", "body_candidate"),
                                   publication("confirmed", "documented_integral"), pending])
        self.assertEqual({k: [r["key"] for r in v] for k, v in options.items()}, {
            "recover": ["no-body"], "confirm": ["uncertain"], "screen": ["confirmed"],
            "methods": ["confirmed"], "admission": ["confirmed", "pending"],
        })

    def test_review_requires_identity_and_will_not_replace_concurrent_evidence(self):
        review = dict(key="study", families_considered="F6", scope="full_methods", decision="exclude",
                      locator="§2.1 and Fig. 3", reason="Different catholyte", source="https://example.org/study")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reviews.psv"
            BATCH["write"](path, list(review), [review])
            missing = {"study": publication("study", "body_candidate")}
            with self.assertRaisesRegex(ValueError, "verified body"):
                BATCH["merge_reviews"](missing, [], [path])
            confirmed = {"study": publication("study", "documented_integral")}
            self.assertEqual(BATCH["merge_reviews"](confirmed, [], [path]), [review])
            self.assertEqual(BATCH["merge_reviews"](confirmed, [review], [path]), [review])
            different = review | {"locator": "Supplementary Table 1"}
            with self.assertRaisesRegex(ValueError, "different evidence"):
                BATCH["merge_reviews"](confirmed, [different], [path])

    def test_changed_original_cannot_promote_body_state(self):
        row = publication("study", "body_candidate")
        receipt = dict(key="study", route_group="pmc-batch", state="identity_verified", format="xml",
                       access_url="https://example.org/study", bytes="1", sha256="0" * 64,
                       identity_basis="pmcid:PMC123", failure_classes="NR")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base / "receipts.json"
            original = BATCH["original_path"](base, "study", "xml")
            original.parent.mkdir()
            original.write_bytes(b"x")
            BATCH["save"](path, [receipt])
            with self.assertRaisesRegex(ValueError, "Original differs"):
                BATCH["merge_receipts"]({"study": row}, [], [path])
            self.assertEqual(row["document"], "body_candidate")

    def test_pmc_history_keeps_transient_and_permanent_routes_separate(self):
        history = [
            dict(key="transient", route_group="pmc-batch", state="unrecovered",
                 access_url="https://www.ebi.ac.uk/PMC1/fullTextXML", format="NR", bytes="NR",
                 sha256="NR", identity_basis="NR",
                 failure_classes="cloud: No public PMC version in bucket / epmc: HTTP Error 500: Internal Server Error"),
            dict(key="permanent", route_group="pmc-batch", state="unrecovered",
                 access_url="https://www.ebi.ac.uk/PMC2/fullTextXML", format="NR", bytes="NR",
                 sha256="NR", identity_basis="NR",
                 failure_classes="cloud: HTTP Error 404: Not Found / epmc: HTTP Error 404: Not Found"),
        ]
        attempted, permanent, transient = BATCH["pmc_provider_history"](history)
        self.assertEqual(attempted["transient"], {"cloud", "epmc"})
        self.assertEqual(permanent["transient"], {"cloud"})
        self.assertEqual(transient["transient"], {"epmc"})
        self.assertEqual(permanent["permanent"], {"cloud", "epmc"})
        self.assertNotIn("permanent", transient)
