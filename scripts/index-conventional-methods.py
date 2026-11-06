"""Index complete JATS method sections and rank documents for arm review."""
import argparse
from hashlib import sha256
from pathlib import Path
import json
import re
import runpy
import xml.etree.ElementTree as ET

SEARCH = runpy.run_path(str(Path(__file__).with_name("search-conventional-methods.py")))
SURVEY = SEARCH["SURVEY"]
METHOD_TYPES = {"materials", "methods", "materials|methods", "experimental", "materials-methods"}
METHOD_TITLE = re.compile(
    r"\b(materials? and methods?|methods? and materials?|materials? and method|methods?|"
    r"experimental(?: section| design| procedures?| setup| methods?)?|"
    r"reactor (?:design|construction|setup)|mfc (?:construction|operation))\b", re.I
)
CONTROL = re.compile(
    r"\b(control (?:cell|reactor|mfc|cathode|anode)|untreated|unmodified|"
    r"baseline|pre-treatment|without (?:the )?addition|before (?:the )?addition|"
    r"reference (?:cell|reactor|mfc|electrode)|as (?:the |a )?control)\b", re.I
)
FED = re.compile(r"\bfed[-\s]+batch\b|\b(?:medium|solution|feed) was (?:replaced|refreshed)\b", re.I)
MFC_TERMS = re.compile(r"\b(?:microbial fuel cells?|MFCs?|SCMFCs?)\b", re.I)


def normalized(text):
    return re.sub(r"[-‐‑‒–—\s]+", " ", text.casefold())


def matches(text, terms):
    for term in terms:
        needle = normalized(term)
        if needle in text and re.search(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", text):
            return True
    return False


def method_sections(body):
    def walk(container):
        for node in container.findall("sec"):
            title = SURVEY["clean_text"](node.find("title"))
            types = set(re.split(r"[|; ]+", node.get("sec-type", "").lower()))
            is_methods = bool(types & METHOD_TYPES) or bool(
                METHOD_TITLE.search(title) and not re.search(r"\b(results|discussion|review)\b", title, re.I)
            )
            if is_methods:
                yield node
            else:
                yield from walk(node)
    return list(walk(body))


def index_article(path):
    data = path.read_bytes()
    root = SURVEY["article_root"](data)
    body = root.find("body")
    meta = root.find("./front/article-meta")
    methods = method_sections(body)
    abstracts = meta.findall("abstract")
    abstract = normalized(" ".join(SURVEY["clean_text"](n) for n in abstracts))
    methods_text = normalized(" ".join(SURVEY["clean_text"](n) for n in methods))
    full = normalized(SURVEY["clean_text"](body))
    reference = " ".join(filter(None, (SURVEY["clean_text"](meta.find("./title-group/article-title")), full)))
    scores = {}
    if MFC_TERMS.search(reference):
        fields = {
            key: tuple(matches(text, terms) for text in (methods_text, full, abstract))
            for key, terms in SEARCH["TERMS"].items()
        }
        for family, terms in SEARCH["FAMILIES"].items():
            bits, full_bits, abstract_bits = zip(*(fields[term] for term in terms), strict=True)
            if all(full_bits[:3]) or all(bits[i] for i in (0, 1, 3)):
                scores[family] = {
                    "methods": [term for term, seen in zip(terms, bits, strict=True) if seen],
                    "body": [term for term, seen in zip(terms, full_bits, strict=True) if seen],
                    "abstract": [term for term, seen in zip(terms, abstract_bits, strict=True) if seen],
                    "priority": 4 * sum(bits) + sum(full_bits) + 2 * bool(CONTROL.search(methods_text))
                                + bool(FED.search(methods_text)),
                }
    return {
        "pmcid": path.stem, "doi": SURVEY["clean_text"](meta.find("article-id[@pub-id-type='doi']")).lower() or None,
        "title": SURVEY["clean_text"](meta.find("./title-group/article-title")),
        "article_type": root.get("article-type"), "sha256": sha256(data).hexdigest(), "bytes": len(data),
        "method_sections": [
            {"title": SURVEY["clean_text"](n.find("title")), "id": n.get("id"), "text_chars": len(SURVEY["clean_text"](n))}
            for n in methods
        ],
        "matches": scores,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    args = parser.parse_args()
    docs = []
    for path in sorted((args.cache / "originals").glob("PMC*.xml")):
        try:
            docs.append(index_article(path))
        except (ValueError, ET.ParseError) as exc:
            docs.append({"pmcid": path.stem, "error": str(exc)})
    SURVEY["save_json"](args.cache / "method-index.json", docs)
    print(len(docs), "documents indexed")
    for family in SEARCH["FAMILIES"]:
        ranked = [d for d in docs if family in d.get("matches", {}) and d.get("article_type") != "review-article"]
        ranked.sort(key=lambda d: (-d["matches"][family]["priority"], d["pmcid"]))
        SURVEY["save_json"](args.cache / f"{family}-ranked.json", ranked)
        print(family, len(ranked), "method/body hits to screen")


if __name__ == "__main__":
    main()
