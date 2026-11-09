"""Verify recovered originals and export a compact document ledger for the catalogue."""
from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree
import re
import runpy

C = runpy.run_path(str(Path(__file__).with_name("build-conventional-catalog.py")))
read_json, write = C["read_json"], C["write"]
doi_key = C["doi_key"]
DUPLICATE_SPACE = re.compile(r"\s+")


def clean(value):
    return "".join(c for c in value.casefold() if c.isalnum())


def article_identity(item, data, text):
    """Match article-front identity. A DOI mentioned only in references is insufficient."""
    doi = doi_key(item.get("doi"))
    target = clean(re.sub(r"<[^>]+>", "", item["title"]))
    if item["format"] == "xml":
        root = ElementTree.fromstring(data)
        meta = root.find("./front/article-meta")
        body = root.find("body")
        if meta is None or body is None:
            return False
        ids = {i.get("pub-id-type"): (i.text or "").strip() for i in meta.findall("article-id")}
        title = meta.find("./title-group/article-title")
        if doi and ids.get("doi"):
            return doi_key(ids["doi"]) == doi
        pmc = ids.get("pmc", "").upper().removeprefix("PMC")
        if item.get("pmcid") and pmc:
            return item["pmcid"].upper().removeprefix("PMC") == pmc
        return title is not None and len(target) >= 22 and target == clean("".join(title.itertext()))
    if item["format"] == "html":
        from lxml import html

        root = html.fromstring(data)
        ids = root.xpath("//meta[translate(@name,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='citation_doi']/@content")
        if doi and ids:
            return {doi_key(x) for x in ids} == {doi}
    front = text[:9000]
    flat = DUPLICATE_SPACE.sub(" ", front).casefold()
    # DOI punctuation in PDF headers may be followed by a period or a closing delimiter.
    if doi and re.search(re.escape(doi) + r"(?![\w/.-])", flat) and len(target) >= 22 and target in clean(front):
        return True
    return len(target) >= 45 and target in clean(text[:3500])


def export(cache, output):
    articles = C["historical"]()
    records = {}
    for path in sorted(cache.glob("retrieval-*.json")):
        for item in read_json(path):
            key = articles.find(item)
            if not key:
                raise ValueError(f"Retrieval outside the catalogue: {item['key']}")
            if key in records:
                raise ValueError(f"Repeated acquisition identity: {key}")
            fmt = item.get("format")
            state = "unrecovered" if item.get("attempts") or item.get("acquisition_error") else "no_route_tested"
            size, digest = "NR", "NR"
            uri = urlsplit(item.get("retrieval_url") or "")
            url = urlunsplit((uri.scheme, uri.netloc, uri.path, "", "")) or "NR"
            if fmt:
                folder = cache / item["local"]
                data = (folder / f"article.{fmt}").read_bytes()
                text = (folder / "article.txt").read_text(encoding="utf-8")
                digest, size = sha256(data).hexdigest(), len(data)
                if digest != item["sha256"] or size != item["bytes"]:
                    raise ValueError(f"Document identity changed: {key}")
                if article_identity(item, data, text):
                    state = "identity_verified"
                else:
                    state = "body_candidate"
            errors = Counter("body_incomplete_or_unreadable" if a["error"].startswith("incomplete body")
                             else a["error"].split(": ", 1)[0] for a in item.get("attempts", []))
            records[key] = {"key": key, "route_group": path.stem.removeprefix("retrieval-"),
                            "state": state, "format": fmt or "NR", "access_url": url,
                            "bytes": size, "sha256": digest,
                            "failure_classes": " / ".join(f"{kind} ({count})" for kind, count in sorted(errors.items())) or "NR"}
    if not records:
        raise ValueError("No completed acquisition manifests in the cache")
    output.mkdir(parents=True, exist_ok=True)
    rows = [records[key] for key in sorted(records)]
    write(output / "acquisition.psv", list(rows[0]), rows)
    print(f"{len(rows)} publications checked", dict(Counter(row["state"] for row in rows)))


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--output", type=Path, default=C["OUTPUT"])
    args = parser.parse_args()
    export(args.cache, args.output)
