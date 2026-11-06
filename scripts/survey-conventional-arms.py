"""Acquire a neutral, stratified sample of MFC studies for methods review.

Usage: python3 scripts/survey-conventional-arms.py /path/to/private-cache
Existing responses are reused. The cache contains original JATS and reading aids.
Bibliographic inclusion and interpretation of arms require a separate manual review.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import argparse
import json
import re
import time
import xml.etree.ElementTree as ET

API = "https://www.ebi.ac.uk/europepmc/webservices/rest"
QUERY = (
    '(TITLE_ABS:"microbial fuel cell" OR TITLE_ABS:"microbial fuel cells") '
    "AND OPEN_ACCESS:Y AND FIRST_PDATE:[1990-01-01 TO 2026-11-06]"
)
ERAS = ((1990, 2013), (2014, 2018), (2019, 2022), (2023, 2026))
FIRST_PASS_PER_ERA = 24
PER_ERA = 36
SALT = "MFC-Studio-reference-arms-2026-11-06"
METHOD_SECTION = re.compile(
    r"\b(methods?|experimental|materials?|reactor (?:design|configuration|setup|construction|operation)"
    r"|mfc (?:configuration|assembly|construction|operation)|cell construction)\b", re.I
)


def save_json(path, data):
    write_bytes(path, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode())


def write_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_bytes(data)
    temporary.replace(path)


def download(url, path, validate):
    if path.is_file():
        data = path.read_bytes()
        validate(data)
        return data
    for attempt in range(2):
        try:
            request = Request(url, headers={"User-Agent": "MFC-Studio literature survey/1.0"})
            with urlopen(request, timeout=35) as response:
                data = response.read()
            validate(data)
        except (URLError, TimeoutError) as exc:
            if attempt or isinstance(exc, HTTPError) and exc.code not in {429, 500, 502, 503, 504}:
                raise
            time.sleep(1.0)
            continue
        write_bytes(path, data)
        return data
    raise RuntimeError("Download exhausted")


def search_frame(cache):
    cursor = "*"
    cursors = set()
    raw = []
    page = 0
    hits = None
    while cursor and cursor not in cursors:
        cursors.add(cursor)
        page += 1
        url = API + "/search?" + urlencode(
            {"query": QUERY, "format": "json", "pageSize": 250, "cursorMark": cursor, "resultType": "lite"}
        )
        data = json.loads(download(url, cache / "search-pages" / f"{page:02}.json", json.loads))
        if hits is None:
            hits = data["hitCount"]
        if hits != data["hitCount"]:
            raise ValueError("Hit count changed during paging. Use a fresh cache.")
        batch = data["resultList"]["result"]
        raw.extend(batch)
        cursor = data.get("nextCursorMark") if batch and len(raw) < hits else None
    if len(raw) != hits:
        raise ValueError(f"Incomplete search frame: {len(raw)}/{hits}")
    unique = {}
    for result in raw:
        doi = result.get("doi", "").lower().strip()
        pmcid = result.get("pmcid")
        key = doi or pmcid or f'{result["source"]}:{result["id"]}'
        item = {
            "key": key, "doi": doi or None, "pmcid": pmcid, "year": int(result.get("pubYear", 0)),
            "title": result["title"], "authors": result.get("authorString"),
            "journal": result.get("journalTitle"), "source": result["source"], "source_id": result["id"],
        }
        if key not in unique or not unique[key]["pmcid"] and pmcid:
            unique[key] = item
    return hits, sorted(unique.values(), key=lambda row: row["key"])


def sample_frame(frame):
    first_pass = []
    extension = []
    strata = []
    for lo, hi in ERAS:
        eligible = [row for row in frame if row["pmcid"] and lo <= row["year"] <= hi]
        ranked = sorted(eligible, key=lambda row: sha256((SALT + ":" + row["key"]).encode()).digest())
        subset = ranked[:PER_ERA]
        era = f"{lo}-{hi}"
        strata.append({"era": era, "records_with_pmcid": len(eligible), "selected": len(subset)})
        first_pass.extend({**row, "era": era} for row in subset[:FIRST_PASS_PER_ERA])
        extension.extend({**row, "era": era} for row in subset[FIRST_PASS_PER_ERA:])
    sample = [
        {**row, "sample_id": f"L{index:03d}"}
        for index, row in enumerate((*first_pass, *extension), start=1)
    ]
    return sample, strata


def article_root(data):
    root = ET.fromstring(data)
    if root.tag != "article":
        raise ValueError("Response is not one JATS article")
    if root.find("body") is None:
        raise ValueError("JATS article has no body")
    return root


def clean_text(element):
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def reading_aid(root):
    body = root.find("body")
    paragraphs = []

    def walk(node, headings, methods):
        if node.tag == "sec":
            title = clean_text(node.find("title"))
            methods = methods or node.get("sec-type", "").lower() in {"methods", "materials", "experimental"} or bool(
                METHOD_SECTION.search(title)
            )
            if title:
                headings = (*headings, title)
        if node.tag in {"p", "caption", "table-wrap"}:
            value = clean_text(node)
            if value:
                paragraphs.append({
                    "id": f"P{len(paragraphs) + 1:03d}", "xml_id": node.get("id"),
                    "section": " / ".join(headings), "methods": methods,
                    "kind": node.tag, "text": value,
                })
            return
        for child in node:
            if child.tag != "title":
                walk(child, headings, methods)

    walk(body, (), False)
    return paragraphs


def acquire_article(cache, item):
    pmcid = item["pmcid"]
    url = f"{API}/{pmcid}/fullTextXML"
    result = {**item, "url": f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/", "acquisition_url": url}
    try:
        data = download(url, cache / "originals" / f"{pmcid}.xml", article_root)
        root = article_root(data)
        article_meta = root.find("./front/article-meta")
        actual_pmc = article_meta.find("./article-id[@pub-id-type='pmc']") if article_meta is not None else None
        if actual_pmc is not None and clean_text(actual_pmc).removeprefix("PMC") != pmcid.removeprefix("PMC"):
            raise ValueError("PMC identifier mismatch")
        paragraphs = reading_aid(root)
        save_json(cache / "paragraphs" / f'{item["sample_id"]}.json', paragraphs)
        licenses = root.findall("./front/article-meta/permissions/license")
        result.update(
            full_text=True, sha256=sha256(data).hexdigest(), bytes=len(data),
            article_type=root.get("article-type"), method_paragraphs=sum(p["methods"] for p in paragraphs),
            license_urls=sorted({
                value for license_node in licenses for node in license_node.iter()
                for value in node.attrib.values() if value.startswith("http")
            }),
            license_types=sorted({node.get("license-type") for node in licenses if node.get("license-type")}),
            figure_references=len(root.findall(".//fig")),
            supplement_references=len(root.findall(".//supplementary-material")),
        )
    except (URLError, TimeoutError, ET.ParseError, ValueError) as exc:
        result.update(full_text=False, error=str(exc))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--frozen-frame", type=Path, help="Replay a versioned search frame without searching again.")
    parser.add_argument("--targeted-manifest", type=Path, help="Also replay XML acquisitions from the targeted search.")
    parser.add_argument("--attachment-manifest", type=Path, help="Also replay the reviewed supplement downloads.")
    args = parser.parse_args()
    if args.frozen_frame:
        frozen = json.loads(args.frozen_frame.read_text())
        if frozen["query"] != QUERY:
            raise ValueError("Frozen frame does not match the survey query")
        hits, frame = frozen["raw_hits"], frozen["frame"]
    else:
        hits, frame = search_frame(args.cache)
    sample, strata = sample_frame(frame)
    manifest = {
        "query": QUERY, "searched": "2026-11-06", "database": "Europe PMC", "api": API,
        "raw_hits": hits, "unique_records": len(frame), "sampling_salt": SALT, "per_era_limit": PER_ERA,
        "first_pass_per_era": FIRST_PASS_PER_ERA,
        "strata": strata, "frame": frame,
    }
    save_json(args.cache / "frame.json", manifest)
    save_json(args.cache / "draw.json", sample)
    print(json.dumps({k: v for k, v in manifest.items() if k != "frame"}), flush=True)
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(lambda row: acquire_article(args.cache, row), sample))
        if args.targeted_manifest:
            targeted = json.loads(args.targeted_manifest.read_text())
            selected = [row for row in targeted if row.get("full_text")]
            replayed = list(executor.map(lambda row: acquire_article(args.cache, row), selected))
            save_json(args.cache / "targeted-replay.json", replayed)
    save_json(args.cache / "acquisition.json", results)
    print(json.dumps({"selected": len(results), "full_texts": sum(row["full_text"] for row in results)}), flush=True)
    if args.attachment_manifest:
        from io import BytesIO
        from zipfile import ZipFile

        for item in json.loads(args.attachment_manifest.read_text()):
            key = item["source"]
            bundle = download(item["url"], args.cache / f"{key}-supplements.zip", lambda data: ZipFile(BytesIO(data)).close())
            with ZipFile(BytesIO(bundle)) as archive:
                document = archive.read(item["entry"])
            if sha256(document).hexdigest() != item["sha256"]:
                raise ValueError(f"Supplement version differs: {key}")
            write_bytes(args.cache / f"{key}-{item['entry']}", document)


if __name__ == "__main__":
    main()
