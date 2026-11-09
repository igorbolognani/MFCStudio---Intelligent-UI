import runpy
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
CATALOG = runpy.run_path(str(SCRIPTS / "build-conventional-catalog.py"))
ACQUISITION = runpy.run_path(str(SCRIPTS / "acquire-external-register.py"))


class ConventionalCoverageTests(unittest.TestCase):
    def test_exactly_half_keeps_goal_open(self):
        rows = [
            {"key": key, "title": key, "abstract": "no", "document": "documented_integral",
             "decisions": "exclude" if key == "b" else "admitted_F1_F6",
             "families": "NR" if key == "b" else "F1", "reading_scopes": "full_methods",
             "open_route_indexed": "yes", "evidence": ""}
            for key in ("a", "b", "c")
        ]
        with tempfile.TemporaryDirectory() as directory:
            result = CATALOG["summarize"](rows[:2], Path(directory))
            self.assertEqual(result["percent"]["included_F1_F6"], 50)
            self.assertEqual(result["remaining_to_over_half"]["included_F1_F6"], 1)
            self.assertFalse(result["over_half_complete"])
            self.assertTrue(CATALOG["summarize"](rows, Path(directory))["over_half_complete"])

    def test_structured_abstract_is_not_body(self):
        preview = b"""<article><section data-title="Abstract"><h2>Abstract</h2>
        <h3>Methods</h3><p>Abstract methods.</p><h3>Results</h3><p>Abstract results.</p>
        </section><h2>Access this article</h2><section data-title="References"></section></article>"""
        with self.assertRaisesRegex(ValueError, "preview lacks the full body"):
            ACQUISITION["extract"](preview, "https://example.org/article.pdf")

    def test_complete_article_can_contain_an_access_heading(self):
        article = b"""<article><section data-title="Materials and methods">
        <h2>Materials and methods</h2><p>Experimental setup.</p></section>
        <section data-title="Results and discussion"><h2>Results</h2><p>Measured response.</p></section>
        <h2>Access this article</h2></article>"""
        kind, body = ACQUISITION["extract"](article, "https://example.org/article")
        self.assertEqual(kind, "html")
        self.assertIn("Experimental setup.", body)
        self.assertIn("Measured response.", body)
