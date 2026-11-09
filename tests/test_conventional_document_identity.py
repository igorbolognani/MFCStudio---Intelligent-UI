from pathlib import Path
import runpy
import unittest


article_identity = runpy.run_path(str(
    Path(__file__).resolve().parents[1] / "scripts/index-conventional-catalog-documents.py"
))["article_identity"]


class ConventionalDocumentIdentityTests(unittest.TestCase):
    def setUp(self):
        self.article = {
            "doi": "10.1234/published",
            "format": "pdf",
            "title": "Reproducible operation of a single chamber microbial fuel cell",
        }

    def test_linked_preprint_with_different_title(self):
        text = ("An earlier title\n"
                "https://doi.org/10.1101/339267\n"
                "doi:\nbioRxiv preprint\fMethods")
        self.assertIsNone(article_identity(self.article, b"", text))
        self.assertEqual(article_identity(self.article, b"", text, {"10.1101/339267"}),
                         "doi:10.1101/339267")

    def test_preprint_doi_in_references_does_not_verify_identity(self):
        text = ("A different experiment\fReferences\n"
                "https://doi.org/10.1101/339267\ndoi:\nbioRxiv preprint")
        self.assertIsNone(article_identity(self.article, b"", text, {"10.1101/339267"}))

    def test_title_survives_line_numbers_and_markup(self):
        item = self.article | {
            "title": "Reproducible operation of a single chamber &lt;i&gt;microbial&lt;/i&gt; fuel cell",
        }
        text = "Reproducible operation of a single chamber\n2\nmicrobial fuel cell\n"
        self.assertEqual(article_identity(item, b"", text), "article_front_title")

    def test_wrong_structured_doi_does_not_fall_back_to_matching_title(self):
        article = self.article | {"format": "xml"}
        document = (
            f'<article><front><article-meta><article-id pub-id-type="doi">10.1234/unrelated</article-id>'
            f'<title-group><article-title>{article["title"]}</article-title></title-group>'
            '</article-meta></front><body/></article>'
        ).encode()
        self.assertIsNone(article_identity(article, document, article["title"]))
