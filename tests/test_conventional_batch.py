import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_admission_queue_keeps_previously_included_studies_without_families(self):
        included = publication("included", "documented_integral", "included_in_survey", "relevant_sections")
        included["pending"] = "no"
        self.assertEqual([row["key"] for row in BATCH["queues"]([included])["admission"]], ["included"])

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

    def test_cloud_version_selection_prefers_published_manifest_version(self):
        listing = (b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
                   b"<CommonPrefixes><Prefix>PMC123.1/</Prefix></CommonPrefixes>"
                   b"<CommonPrefixes><Prefix>PMC123.2/</Prefix></CommonPrefixes></ListBucketResult>")
        metadata = {
            "PMC123.1": {"pmcid": "PMC123", "doi": "10.1234/study", "version": 1,
                         "is_manuscript": "no", "xml_url": "https://pmc-oa-opendata.s3.amazonaws.com/PMC123.1/PMC123.1.xml?md5=pub"},
            "PMC123.2": {"pmcid": "PMC123", "doi": "10.1234/study", "version": 2,
                         "is_manuscript": "yes", "xml_url": "https://pmc-oa-opendata.s3.amazonaws.com/PMC123.2/PMC123.2.xml?md5=ms"},
        }
        def fake_download(url):
            if "list-type=2" in url:
                return listing
            key = "PMC123.1" if ".1/PMC123.1.json" in url else "PMC123.2"
            import json
            return json.dumps(metadata[key]).encode()
        with patch.dict(BATCH["cloud_url"].__globals__, {"download": fake_download}):
            selected = BATCH["cloud_url"]("PMC123", ["10.1234/study"])
            source = BATCH["cloud_route"]("PMC123", ["10.1234/study"])
        self.assertIn("PMC123.1/PMC123.1.xml", selected)
        self.assertEqual((source["version"], source["is_manuscript"]), ("1", "no"))

    def test_bioc_fallback_requires_full_body_and_confirms_identity(self):
        import xml.etree.ElementTree as ET
        passages = [
            ("title", "Microbial fuel cell control with acetate"),
            ("abstract", "A" * 150),
            ("section", "Methods detail " + "M" * 700),
            ("section", "Feed detail " + "F" * 700),
            ("section", "Results detail " + "R" * 700),
            ("section", "Discussion detail " + "D" * 700),
        ]
        collection = ET.Element("collection")
        document = ET.SubElement(collection, "document")
        ET.SubElement(document, "id").text = "PMC123"
        doi = ET.SubElement(document, "infon", key="article-id_doi")
        doi.text = "10.1234/study"
        for kind, value in passages:
            passage = ET.SubElement(document, "passage")
            ET.SubElement(passage, "infon", key="type").text = kind
            ET.SubElement(passage, "text").text = value
        row = {"doi": "10.1234/study", "title": passages[0][1]}
        _, state, basis = BATCH["bioc_article"](ET.tostring(collection), row, "PMC123")
        self.assertEqual((state, basis), ("identity_verified", "doi:10.1234/study"))
        wrong = ET.tostring(collection).replace(b"10.1234/study", b"10.9999/other")
        _, state, basis = BATCH["bioc_article"](wrong, row, "PMC123")
        self.assertEqual((state, basis), ("wrong_document", "different_doi:10.9999/other"))
        with self.assertRaisesRegex(ValueError, "BioC open-access subset"):
            BATCH["bioc_article"](b"[Error] : No result can be found. <BR>", row, "PMC123")

    def test_openalex_route_plan_requires_exact_doi_oa_and_direct_pdf(self):
        row = {"key": "study", "doi": "10.1234/study"}
        work = {
            "doi": "https://doi.org/10.1234/study",
            "best_oa_location": {
                "is_oa": True, "pdf_url": "https://repository.example/study.pdf",
                "license": "cc-by", "version": "acceptedVersion",
                "source": {"type": "repository"},
            },
            "locations": [
                {"is_oa": True, "pdf_url": "https://publisher.example/study.pdf",
                 "license": "cc-by", "version": "publishedVersion",
                 "source": {"type": "publisher"}},
                {"is_oa": False, "pdf_url": "https://closed.example/study.pdf",
                 "version": "publishedVersion", "source": {"type": "publisher"}},
                {"is_oa": True, "pdf_url": None, "landing_page_url": "https://repository.example/study",
                 "version": "acceptedVersion", "source": {"type": "repository"}},
            ],
        }
        planned = BATCH["select_openalex_routes"]([row], [work], "openalex-test")
        self.assertEqual(len(planned), 2)
        self.assertEqual(planned[0]["url"], "https://publisher.example/study.pdf")
        self.assertEqual(planned[0]["version"], "publishedVersion")
        self.assertEqual(planned[0]["route_group"], "openalex-test-001")
        self.assertEqual(planned[1]["url"], "https://repository.example/study.pdf")
        self.assertEqual(BATCH["select_openalex_routes"]([row], [work | {"doi": "10.9876/other"}]), [])

    def test_pdf_acquisition_falls_back_in_order_and_saves_version_metadata(self):
        import json
        from unittest.mock import Mock

        row = dict(key="study", doi="10.1234/study", title="Microbial fuel cell experiment")
        routes = [
            dict(key="study", url="https://publisher.example/broken.pdf", provider="OpenAlex",
                 license="cc-by", version="publishedVersion", host_kind="publisher",
                 landing_page_url="https://publisher.example/study", route_group="openalex-b08-001"),
            dict(key="study", url="https://repository.example/study.pdf", provider="OpenAlex",
                 license="cc-by", version="acceptedVersion", host_kind="repository",
                 landing_page_url="https://repository.example/study", route_group="openalex-b08-002"),
        ]
        fake_runtime = Mock()
        fake_runtime.run_path.side_effect = [
            {"article_identity": lambda *_args, **_kwargs: "doi:10.1234/study"},
            {"extract": lambda data, _url: (data, "M" * 7000 + " METHOD RESULT"),
             "METHOD": __import__("re").compile("METHOD"), "RESULT": __import__("re").compile("RESULT")},
        ]
        def fake_download(url):
            if "broken" in url:
                raise OSError("HTTP Error 403")
            return b"%PDF-test verified article"

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            catalogue, batch, sources = (base / "catalog"), (base / "batch"), (base / "sources.psv")
            BATCH["write"](sources, list(routes[0]), routes)
            with patch.dict(BATCH["acquire_pdfs"].__globals__, {
                    "checked_catalogue": lambda _directory: {"study": row},
                    "download": fake_download,
                    "runpy": fake_runtime}):
                BATCH["acquire_pdfs"](catalogue, batch, sources)
            receipts = json.loads((batch / "receipts.json").read_bytes())
            self.assertEqual([item["state"] for item in receipts], ["unrecovered", "identity_verified"])
            self.assertEqual(receipts[1]["source_version"], "acceptedVersion")
            self.assertEqual(receipts[1]["provider"], "OpenAlex")
            original = BATCH["original_path"](batch, "study", "pdf")
            self.assertEqual(original.read_bytes(), b"%PDF-test verified article")
            self.assertTrue((original.parent / "receipt-openalex-b08-001.json").exists())
            self.assertTrue((original.parent / "receipt-openalex-b08-002.json").exists())
