"""Verify recovered originals and export a compact document ledger for the catalogue."""
from argparse import ArgumentParser
from collections import Counter, defaultdict
from hashlib import sha256
from html import unescape
from pathlib import Path
from unicodedata import normalize
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree
import re
import runpy

C = runpy.run_path(str(Path(__file__).with_name("build-conventional-catalog.py")))
is_access_preview = runpy.run_path(str(Path(__file__).with_name("acquire-external-register.py")))["is_access_preview"]
read_json, write = C["read_json"], C["write"]
doi_key = C["doi_key"]
DUPLICATE_SPACE = re.compile(r"\s+")


def clean(value):
    return "".join(c for c in normalize("NFKC", value).casefold() if c.isalnum())


def article_identity(item, data, text, related_dois=()):
    """Return the identifier read at the front, or the basis of a title match."""
    doi = doi_key(item.get("doi"))
    accepted = {doi, *related_dois} - {"", "nr"}
    target = clean(re.sub(r"<[^>]+>", "", unescape(item["title"])))
    if item["format"] == "xml":
        root = ElementTree.fromstring(data)
        meta = root.find("./front/article-meta")
        body = root.find("body")
        if meta is None or body is None:
            return None
        ids = {i.get("pub-id-type"): (i.text or "").strip() for i in meta.findall("article-id")}
        document_doi = doi_key(ids.get("doi"))
        title = meta.find("./title-group/article-title")
        if accepted and document_doi:
            return "doi:" + document_doi if document_doi in accepted else None
        pmc = ids.get("pmc", "").upper().removeprefix("PMC")
        if item.get("pmcid") and pmc:
            return "pmcid:PMC" + pmc if item["pmcid"].upper().removeprefix("PMC") == pmc else None
        if title is not None and len(target) >= 22 and target == clean("".join(title.itertext())):
            return "article_front_title"
        return None
    if item["format"] == "html":
        from lxml import html

        root = html.fromstring(data)
        ids = root.xpath("//meta[translate(@name,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='citation_doi']/@content")
        if accepted and ids:
            found = {doi_key(x) for x in ids}
            if len(found) == 1 and found <= accepted:
                return "doi:" + found.pop()
            return None
    # Some accepted manuscripts print a running line number between title lines.
    if item["format"] == "pdf":
        text = re.sub(r"(?m)^[ \t]*[0-9]{1,4}[ \t]*$", "", text)
    front = text[:9000]
    flat = DUPLICATE_SPACE.sub(" ", front).casefold()
    # A linked bioRxiv version can have a different title from the published article.
    # Its first-page publisher banner declares the preprint DOI explicitly.
    first_page = DUPLICATE_SPACE.sub(" ", text.split("\f", 1)[0][:9000]).casefold()
    for related in sorted(accepted):
        if related.startswith("10.1101/") and re.search(
            r"https://doi\.org/" + re.escape(related) + r"\s+doi:\s+biorxiv preprint", first_page
        ):
            return "doi:" + related
    if len(target) >= 22 and target in clean(front):
        # Some author manuscripts have a repository cover page before the article.
        found = {d for d in accepted if re.search(r"(?<![\w.])" + re.escape(d) + r"(?=$|[^\w/.-]|\.(?:\s|$))", flat)}
        if len(found) == 1:
            return "doi:" + found.pop()
    if len(target) >= 45 and target in clean(text[:3500]):
        return "article_front_title"
    return None


def export(cache, output):
    articles = C["historical"]()
    versions = defaultdict(set)
    version_map = output / "versions.psv"
    if version_map.exists():
        for row in C["read"](version_map):
            old, published = row["preprint_doi"], row["published_doi"]
            versions[old].add(published)
            versions[published].add(old)
    conflicts_path = output / "document-conflicts.psv"
    conflicts = {
        (row["key"], row["sha256"]): row["found_doi"]
        for row in C["read"](conflicts_path)
    } if conflicts_path.exists() else {}
    verified_conflicts = set()
    records = {}
    for path in sorted(cache.glob("retrieval-*.json")):
        route = path.stem.removeprefix("retrieval-")
        for item in read_json(path):
            key = articles.find(item)
            if not key:
                raise ValueError(f"Retrieval outside the catalogue: {item['key']}")
            if (key, route) in records:
                raise ValueError(f"Repeated acquisition in batch {route}: {key}")
            fmt = item.get("format")
            state = "unrecovered" if item.get("attempts") or item.get("acquisition_error") else "no_route_tested"
            size, digest = "NR", "NR"
            identifier = None
            uri = urlsplit(item.get("retrieval_url") or "")
            url = urlunsplit((uri.scheme, uri.netloc, uri.path, "", "")) or "NR"
            if fmt:
                folder = cache / item["local"]
                data = (folder / f"article.{fmt}").read_bytes()
                text = (folder / "article.txt").read_text(encoding="utf-8")
                digest, size = sha256(data).hexdigest(), len(data)
                if digest != item["sha256"] or size != item["bytes"]:
                    raise ValueError(f"Document identity changed: {key}")
                conflict = (key, digest)
                if conflict in conflicts:
                    identifier = "different_doi:" + conflicts[conflict]
                    state = "wrong_document"
                    verified_conflicts.add(conflict)
                else:
                    identifier = article_identity(item, data, text, versions[doi_key(item.get("doi"))])
                    state = "identity_verified" if identifier else "body_candidate"
                    if fmt == "html":
                        from lxml import html
                        if is_access_preview(html.fromstring(data)):
                            state = "preview_only"
            errors = Counter("body_incomplete_or_unreadable" if a["error"].startswith("incomplete body")
                             else a["error"].split(": ", 1)[0] for a in item.get("attempts", []))
            records[key, route] = {"key": key, "route_group": route,
                                   "state": state, "format": fmt or "NR", "access_url": url,
                                   "bytes": size, "sha256": digest, "identity_basis": identifier or "NR",
                                   "failure_classes": " / ".join(f"{kind} ({count})" for kind, count in sorted(errors.items())) or "NR"}
    if not records:
        raise ValueError("No completed acquisition manifests in the cache")
    if verified_conflicts != conflicts.keys():
        raise ValueError("Document conflict is missing its original acquisition")
    output.mkdir(parents=True, exist_ok=True)
    rows = [records[key] for key in sorted(records)]
    write(output / "acquisition.psv", list(rows[0]), rows)
    print(f"{len({row['key'] for row in rows})} publication identities in {len(rows)} batch records",
          dict(Counter(row["state"] for row in rows)))


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--output", type=Path, default=C["OUTPUT"])
    args = parser.parse_args()
    export(args.cache, args.output)
