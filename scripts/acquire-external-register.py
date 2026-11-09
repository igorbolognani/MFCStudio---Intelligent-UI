"""Acquire public document candidates from the frozen-register priority queue."""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from http.client import HTTPException
from pathlib import Path
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
import re
import runpy
import subprocess

from lxml import etree, html

RECONCILE = runpy.run_path(str(Path(__file__).with_name("reconcile-external-register.py")))
read_json = RECONCILE["read_json"]
save_json = RECONCILE["SEARCH"]["save_json"]
MAX_BYTES = 30_000_000
METHOD = re.compile(r"\b(?:methods?|experimental|methodology)\b|材料与方法|试验方法|实验方法|材料和方法", re.I)
RESULT = re.compile(r"\b(?:results?|discussion|conclusions?)\b|结果与讨论|实验结果|试验结果", re.I)
TRANSIENT = re.compile(r"timed out|HTTP Error (?:429|500|502|503|504)")


def text_nodes(node, expression):
    return "\n".join(" ".join(" ".join(element.itertext()).split()) for element in node.xpath(expression))


def is_access_preview(page):
    """Identify access screens whose Methods and Results are confined to an abstract."""
    if not any(" ".join(h.text_content().casefold().split()) in {
        "access this article", "log in or create a free account to read this content",
    } for h in page.xpath("//article//h2 | //main//h2")):
        return False
    labels = [section.get("data-title", "") for section in page.xpath(
        "//article//section[@data-title] | //main//section[@data-title]"
    )]
    return not (any(METHOD.search(label) for label in labels) and any(RESULT.search(label) for label in labels))


def extract(data, route):
    if data.startswith(b"%PDF-"):
        result = subprocess.run(["pdftotext", "-raw", "-", "-"], input=data, capture_output=True, check=True)
        return "pdf", result.stdout.decode("utf-8", errors="replace")
    if data.lstrip().startswith(b"<?xml") and route.endswith("/fullTextXML"):
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        body = etree.fromstring(data, parser=parser).find("body")
        if body is None:
            raise ValueError("XML lacks article body")
        return "xml", text_nodes(body, ".//title|.//p|.//caption")
    page = html.fromstring(data)
    if is_access_preview(page):
        raise ValueError("article preview lacks the full body")
    for item in page.xpath("//script|//style|//nav|//footer"):
        item.drop_tree()
    node = max(page.xpath("//article|//main|//*[@id='body']"), key=lambda n: len(n.text_content()), default=page)
    return "html", text_nodes(node, ".//h1|.//h2|.//h3|.//h4|.//p|.//figcaption|.//tr")


def routes(row):
    urls = list(row["urls"])
    if row.get("pmcid") and re.fullmatch(r"PMC[0-9]+", row["pmcid"]):
        urls.insert(0, "https://www.ebi.ac.uk/europepmc/webservices/rest/" + row["pmcid"] + "/fullTextXML")
    for url in list(urls):
        if "/doi/abs/" in url and urlsplit(url).hostname != "pubs.rsc.org":
            urls.append(url.replace("/doi/abs/", "/doi/full/"))
        if "articlelanding" in url and urlsplit(url).hostname != "pubs.rsc.org":
            urls.append(url.replace("articlelanding", "articlehtml"))

    def priority(url):
        if url.endswith("/fullTextXML"):
            return 0
        return 1 if any(token in url.lower() for token in (".pdf", "bitstream", "/download", "/ft/")) else 2

    return sorted(dict.fromkeys(url for url in urls if urlsplit(url).scheme == "https"), key=priority)[:5]


def acquire(cache, row):
    folder = cache / "articles" / sha256(row["key"].encode()).hexdigest()[:16]
    folder.mkdir(parents=True, exist_ok=True)
    acquired = folder / "acquired.json"
    attempts = folder / "attempts.json"
    if acquired.exists():
        return read_json(acquired)
    errors = read_json(attempts) if attempts.exists() else []
    tried = {item["url"] for item in errors if not TRANSIENT.search(item["error"])}
    for url in routes(row):
        if url in tried:
            continue
        try:
            encoded = quote(url, safe=":/?#[]@!$&'()*+,;=%")
            req = Request(encoded, headers={"User-Agent": "MFC Studio literature research/1.0",
                                        "Accept": "application/pdf,text/html,application/xml,*/*"})
            with urlopen(req, timeout=15) as response:
                data = response.read(MAX_BYTES + 1)
                final_url = response.geturl()
            if len(data) > MAX_BYTES:
                raise ValueError("document exceeded 30 MB")
            fmt, body = extract(data, url)
            if len(body) <= 6500 or not METHOD.search(body) or not RESULT.search(body):
                raise ValueError(f"incomplete body or unreadable text ({fmt}, {len(body)} chars)")
            (folder / f"article.{fmt}").write_bytes(data)
            (folder / "article.txt").write_text(body, encoding="utf-8")
            record = row | {"format": fmt, "url": final_url, "retrieval_url": url, "sha256": sha256(data).hexdigest(),
                            "bytes": len(data), "text_chars": len(body), "local": str(folder.relative_to(cache)),
                            "attempts": errors}
            save_json(acquired, record)
            return record
        except (OSError, ValueError, HTTPException, etree.Error, subprocess.SubprocessError) as error:
            errors.append({"url": url, "error": str(error)})
            save_json(attempts, errors)
    return row | {"format": None, "attempts": errors, "local": str(folder.relative_to(cache))}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("queue", type=Path)
    parser.add_argument("--batch", type=int, required=True)
    parser.add_argument("--limit", type=int, default=120)
    args = parser.parse_args()
    if args.batch < 1 or args.limit < 1:
        parser.error("--batch and --limit must be positive")
    rows = read_json(args.queue)[:args.limit]
    keys = {row["key"] for row in rows}
    register = RECONCILE["read_table"](RECONCILE["BASE"] / "coverage/register.psv.gz")
    if len(keys) != len(rows) or not keys <= {row["key"] for row in register}:
        raise ValueError("Queue must contain distinct frozen-register identities")
    batch_name = "pull-frozen-queue" + (f"-{args.batch}" if args.batch > 1 else "")
    path = args.cache / f"{batch_name}.json"
    if path.exists():
        if keys != {row["key"] for row in read_json(path)}:
            raise ValueError("Batch already exists with a different selection")
        print(f"Reusing {path.name} ({len(rows)} records)")
        return
    earlier = {row["key"] for manifest in args.cache.glob("pull-frozen-queue*.json") for row in read_json(manifest)}
    if earlier & keys:
        raise ValueError("Queue repeats records from a completed acquisition batch")
    with ThreadPoolExecutor(max_workers=8) as pool:
        records = sorted(pool.map(lambda row: acquire(args.cache, row), rows), key=lambda row: row["key"])
    save_json(path, records)
    print(f"{len(records)} attempted, {sum(bool(row['format']) for row in records)} text candidates")


if __name__ == "__main__":
    main()
