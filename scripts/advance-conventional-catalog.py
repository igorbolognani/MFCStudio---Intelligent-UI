"""Plan, acquire and stage incremental reviews of the frozen MFC catalogue."""
from argparse import ArgumentParser
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
import json
import re
import runpy
import shutil
from subprocess import SubprocessError

HERE = Path(__file__).resolve().parent
C = runpy.run_path(str(HERE / "build-conventional-catalog.py"))
read, write, save, read_json, values = (C[name] for name in ("read", "write", "save", "read_json", "values"))
STATES = {"identity_verified": "documented_integral", "body_candidate": "body_candidate",
          "wrong_document": "unavailable", "preview_only": "partial", "unrecovered": "unavailable"}
PMC_BUCKET = "https://pmc-oa-opendata.s3.amazonaws.com/"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
JATS_LIMIT = 16 * 1024 * 1024
PERMANENT_PMC_FAILURE = re.compile(r"No public PMC version|HTTP Error 404")
TRANSIENT_PMC_FAILURE = re.compile(
    r"timed out|timeout|temporar|HTTP Error (?:408|425|429|500|502|503|504)|\b(?:408|425|429|500|502|503|504)\b",
    re.IGNORECASE,
)


def checked_catalogue(directory):
    rows = read(directory / "publications.psv.gz")
    if len(rows) != C["FROZEN_PUBLICATIONS"]:
        raise ValueError(f"Expected {C['FROZEN_PUBLICATIONS']} frozen publications")
    if C["summarize"](rows, directory) != read_json(directory / "coverage.json"):
        raise ValueError("The published catalogue failed its integrity check")
    return {row["key"]: row for row in rows}


def rank(row):
    signals = row["machine_signals"]
    methods = re.findall(r"F[1-6]_methods:([1-4])", signals)
    title = C["R"]["PRIMARY_TOPIC"].search(row["title"])
    prior = row["priority_previous"]
    return ("nonprimary_signal" in signals, not bool(title),
            -max(map(int, methods), default=0), -len(methods),
            row["open_route_indexed"] != "yes",
            int(prior) if prior.isdecimal() else float("inf"), row["key"])


def queues(rows):
    ordered = sorted(rows, key=rank)
    confirmed = [row for row in ordered if row["document"] == "documented_integral"]
    return {
        "recover": [r for r in ordered if C["DOC"][r["document"]] < C["DOC"]["body_candidate"]],
        "confirm": [r for r in ordered if r["document"] == "body_candidate"],
        "screen": [r for r in confirmed if r["decisions"] == "unreviewed"],
        "methods": [r for r in confirmed if not values(r["reading_scopes"]) & C["FULL_METHODS"]],
        "admission": [r for r in confirmed if r["families"] == "NR" and
                      (r["pending"] == "yes" or r["decisions"] == "unreviewed")],
    }


def download(url):
    request = Request(url, headers={"User-Agent": "MFC Studio literature catalogue/1.0"})
    with urlopen(request, timeout=12) as response:
        data = response.read(JATS_LIMIT + 1)
    if len(data) > JATS_LIMIT:
        raise ValueError("Document exceeds size limit")
    return data


def cloud_url(pmc):
    listing = PMC_BUCKET + "?" + urlencode({"list-type": 2, "prefix": pmc + ".", "delimiter": "/"})
    xml = ET.fromstring(download(listing))
    versions = [x.text.rstrip("/") for x in xml.findall("{*}CommonPrefixes/{*}Prefix")
                if re.fullmatch(pmc + r"\.\d+/", x.text or "")]
    if not versions:
        raise ValueError("No public PMC version in bucket")
    version = max(versions, key=lambda s: int(s.rsplit(".", 1)[1]))
    return f"{PMC_BUCKET}{version}/{version}.xml"


def pmc_provider_history(history):
    """Return providers attempted and permanently exhausted for each PMCID row."""
    attempted, permanent, transient = {}, {}, {}
    for item in history:
        if not item["route_group"].startswith("pmc-") or item["state"] not in {
            "unrecovered", "wrong_document", "preview_only"
        }:
            continue
        failures = item["failure_classes"]
        labelled = list(re.finditer(r"(?:^| / )(cloud|epmc): ", failures))
        attempts = []
        if labelled:
            for index, match in enumerate(labelled):
                end = labelled[index + 1].start() if index + 1 < len(labelled) else len(failures)
                attempts.append((match.group(1), failures[match.end():end].strip()))
        else:
            host = urlsplit(item["access_url"]).hostname
            provider = "cloud" if host == "pmc-oa-opendata.s3.amazonaws.com" else (
                "epmc" if host == "www.ebi.ac.uk" else None
            )
            if provider:
                attempts.append((provider, failures))
        for provider, reason in attempts:
            attempted.setdefault(item["key"], set()).add(provider)
            if (item["state"] in {"wrong_document", "preview_only"} or
                    PERMANENT_PMC_FAILURE.search(reason)):
                permanent.setdefault(item["key"], set()).add(provider)
            elif TRANSIENT_PMC_FAILURE.search(reason):
                transient.setdefault(item["key"], set()).add(provider)
    return attempted, permanent, transient


def original_path(directory, key, fmt):
    if fmt not in {"xml", "html", "pdf"}:
        raise ValueError(f"Unknown document format: {fmt}")
    return directory / sha256(key.encode()).hexdigest()[:16] / f"article.{fmt}"


def fetch_pmc(row, batch, group, identity):
    pmc = row["pmcid"]
    folder = original_path(batch, row["key"], "xml").parent
    folder.mkdir(parents=True, exist_ok=True)
    receipt = folder / "receipt.json"
    if receipt.exists():
        record = read_json(receipt)
        if (record["key"], record["route_group"]) != (row["key"], group):
            raise ValueError(f"Invalid receipt for {row['key']}")
        return record
    record = dict(key=row["key"], route_group=group, state="unrecovered", format="NR",
                  access_url="NR", bytes="NR", sha256="NR", identity_basis="NR", failure_classes="NR")
    failures = []
    for provider in row["providers"]:
        url = EPMC + pmc + "/fullTextXML" if provider == "epmc" else PMC_BUCKET
        try:
            if provider == "cloud":
                url = cloud_url(pmc)
            data = download(url)
            article = ET.fromstring(data)
            body = article.find("body")
            if body is None or len("".join(body.itertext()).strip()) < 2000 or len(body.findall(".//p")) < 4:
                raise ValueError("JATS lacks substantive article body")
            dois = sorted(values(row["doi"]))
            basis = identity(dict(format="xml", doi=dois[0] if dois else None, pmcid=pmc, title=row["title"]),
                             data, "", dois[1:])
            declared = C["doi_key"](article.findtext("./front/article-meta/article-id[@pub-id-type='doi']"))
            state = "identity_verified" if basis else "body_candidate"
            if not basis and declared and dois and declared not in dois:
                state, basis = "wrong_document", "different_doi:" + declared
            original_path(batch, row["key"], "xml").write_bytes(data)
            record.update(state=state, format="xml", access_url=url, bytes=str(len(data)),
                          sha256=sha256(data).hexdigest(), identity_basis=basis or "NR")
            break
        except (OSError, ValueError, ET.ParseError) as error:
            failures.append(f"{provider}: {error}")
            record["access_url"] = url
    if failures:
        record["failure_classes"] = " / ".join(failures)
    save(receipt, record)
    return record


def acquire(directory, batch, limit, retry_failed=False):
    from_index = runpy.run_path(str(HERE / "index-conventional-catalog-documents.py"))
    identity = from_index["article_identity"]
    rows = checked_catalogue(directory)
    queue_file = batch / "queue.json"
    group = "pmc-" + batch.name
    if not re.fullmatch(r"pmc-[A-Za-z0-9-]+", group):
        raise ValueError("Use letters, digits and hyphens in the batch directory name")
    if queue_file.exists():
        queue = read_json(queue_file)
    else:
        history = read(directory / "acquisition.psv")
        attempted, permanent, transient = pmc_provider_history(history)
        options = queues(rows.values())
        queue = []
        # Confirm likely full-text bodies before spending requests across the much larger
        # no-body backlog. Failed routes are checkpointed and only retried on request.
        candidates = options["confirm"] + options["recover"]
        for row in candidates:
            key = row["key"]
            tried = attempted.get(key, set())
            exhausted = permanent.get(key, set())
            if retry_failed:
                if key not in transient:
                    continue
                pending = [p for p in ("cloud", "epmc")
                           if p not in exhausted and (p not in tried or p in transient[key])]
            else:
                pending = [p for p in ("cloud", "epmc") if p not in tried and p not in exhausted]
            pmcs = values(row["pmcid"])
            if len(pmcs) == 1 and pending:
                queue.append(dict(key=row["key"], doi=row["doi"], pmcid=next(iter(pmcs)),
                                  title=row["title"], providers=pending))
        queue = queue[:limit]
        batch.mkdir(parents=True, exist_ok=True)
        save(queue_file, queue)
    if len(queue) != len({item["key"] for item in queue}) or any(item["key"] not in rows for item in queue):
        raise ValueError("Batch contains duplicate or unknown publication keys")
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda row: fetch_pmc(row, batch, group, identity), queue))
    save(batch / "receipts.json", records)
    print(json.dumps(dict(Counter(item["state"] for item in records)), sort_keys=True))



def acquire_pdfs(directory, batch, sources):
    rows = checked_catalogue(directory)
    planned = read(sources)
    group = "pdf-" + batch.name
    if not re.fullmatch(r"pdf-[A-Za-z0-9-]+", group) or not planned:
        raise ValueError("Provide a nonempty list and a batch name using letters, digits and hyphens")
    if len(planned) != len({item["key"] for item in planned}):
        raise ValueError("Provide one PDF route per publication in a batch")
    for item in planned:
        url = urlsplit(item["url"])
        if item["key"] not in rows or url.scheme != "https" or not url.hostname or url.username:
            raise ValueError(f"Unknown publication or invalid public URL: {item['key']}")
    batch.mkdir(parents=True, exist_ok=True)
    queue_file = batch / "queue.json"
    if queue_file.exists() and planned != read_json(queue_file):
        raise ValueError("The batch already has a different route list")
    save(queue_file, planned)
    index = runpy.run_path(str(HERE / "index-conventional-catalog-documents.py"))
    acquisition = runpy.run_path(str(HERE / "acquire-external-register.py"))

    def fetch(item):
        key, url = item["key"], item["url"]
        original = original_path(batch, key, "pdf")
        original.parent.mkdir(parents=True, exist_ok=True)
        receipt = original.parent / "receipt.json"
        if receipt.exists():
            return read_json(receipt)
        row = rows[key]
        result = dict(key=key, route_group=group, state="unrecovered", format="NR",
                      access_url=url, bytes="NR", sha256="NR", identity_basis="NR", failure_classes="NR")
        try:
            data = download(url)
            if not data.startswith(b"%PDF-"):
                raise ValueError("Public route did not return a PDF")
            _, text = acquisition["extract"](data, url)
            if len(text) < 6500 or not all(acquisition[name].search(text) for name in ("METHOD", "RESULT")):
                raise ValueError("Substantive article body could not be verified")
            dois = sorted(values(row["doi"]))
            basis = index["article_identity"](dict(format="pdf", doi=dois[0] if dois else None,
                                                   title=row["title"]), data, text, dois[1:])
            if not basis:
                raise ValueError("PDF identity could not be verified")
            original.write_bytes(data)
            result.update(state="identity_verified", format="pdf", bytes=str(len(data)),
                          sha256=sha256(data).hexdigest(), identity_basis=basis)
        except (OSError, ValueError, SubprocessError) as error:
            result["failure_classes"] = str(error)
        save(receipt, result)
        return result

    with ThreadPoolExecutor(max_workers=8) as pool:
        records = list(pool.map(fetch, planned))
    save(batch / "receipts.json", records)
    print(json.dumps(dict(Counter(item["state"] for item in records)), sort_keys=True))


def merge_receipts(rows, ledger, receipt_files):
    known = {(item["key"], item["route_group"]): item for item in ledger}
    for path in receipt_files:
        for item in read_json(path):
            row = rows[item["key"]]
            key = item["key"], item["route_group"]
            if key in known:
                if known[key] != item:
                    raise ValueError(f"Conflicting receipt: {key}")
                continue
            if item["state"] not in STATES or not re.fullmatch(r"[a-zA-Z0-9-]+", item["route_group"]):
                raise ValueError(f"Invalid acquisition receipt: {key}")
            if item["state"] != "unrecovered":
                original = original_path(path.parent, row["key"], item["format"])
                if (not item["access_url"].startswith("https://") or original.stat().st_size != int(item["bytes"])
                        or sha256(original.read_bytes()).hexdigest() != item["sha256"]):
                    raise ValueError(f"Original differs from receipt: {key}")
                if item["state"] == "identity_verified" and item["identity_basis"] in {"", "NR"}:
                    raise ValueError(f"Identity basis missing: {key}")
            target = STATES[item["state"]]
            if C["DOC"][target] > C["DOC"][row["document"]]:
                row["document"] = target
            row["evidence"] = " ".join(sorted(values(row["evidence"]) | {"catalog_acquisition"}))
            known[key] = item
    return [known[key] for key in sorted(known)]


def merge_reviews(rows, ledger, review_files):
    known = {review["key"]: review for review in ledger}
    registered_arms = None
    for path in review_files:
        for item in read(path):
            row = rows[item["key"]]
            if item["key"] in known:
                if known[item["key"]] != item:
                    raise ValueError(f"Review already exists with different evidence: {item['key']}")
                continue
            families = values(item["families_considered"])
            if (row["document"] != "documented_integral" or
                    item["scope"] not in C["FULL_METHODS"] | {"relevant_sections"} or
                    item["decision"] not in {"exclude", "pending", "confirm_existing_control"} or
                    not families or not families <= set(C["METHOD"]["FAMILY_KEYS"].values()) or
                    not item["locator"].strip() or not item["reason"].strip() or
                    not item["source"].startswith("https://")):
                raise ValueError(f"Review lacks verified body, scope or provenance: {item['key']}")
            labels = (values(row["decisions"]) - {"unreviewed"}) | {item["decision"]}
            if item["decision"] == "confirm_existing_control":
                if registered_arms is None:
                    registered_arms = C["historical"]()
                owner = registered_arms.find(row)
                verified = registered_arms.rows[owner]["families"] if owner else set()
                if item["scope"] not in C["FULL_METHODS"] or not families <= verified:
                    raise ValueError(f"Control requires a registered arm and full methods: {item['key']}")
                row["families"] = " ".join(sorted(values(row["families"]) | families))
                labels.add("admitted_F1_F6")
            row.update(decisions=" ".join(sorted(labels)), pending="yes" if "pending" in labels else "no",
                       reading_scopes=" ".join(sorted(values(row["reading_scopes"]) | {item["scope"]})),
                       evidence=" ".join(sorted(values(row["evidence"]) | {"catalog_individual_review"})))
            known[item["key"]] = item
    return list(known.values())


def stage(directory, output, receipt_files, review_files):
    rows = checked_catalogue(directory)
    if output.exists() or not (receipt_files or review_files):
        raise ValueError("Use a new staging directory and provide receipts or reviews")
    acquisitions = merge_receipts(rows, read(directory / "acquisition.psv"), receipt_files)
    reviews = merge_reviews(rows, read(directory / "reviews.psv"), review_files)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        draft = Path(temp) / "catalog"
        shutil.copytree(directory, draft)
        write(draft / "acquisition.psv", list(acquisitions[0]), acquisitions)
        write(draft / "reviews.psv", list(reviews[0]), reviews)
        values_in_order = list(rows.values())
        write(draft / "publications.psv.gz", list(values_in_order[0]), values_in_order)
        save(draft / "coverage.json", C["summarize"](values_in_order, draft))
        checked_catalogue(draft)
        draft.rename(output)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=C["OUTPUT"])
    commands = parser.add_subparsers(dest="command", required=True)
    queue = commands.add_parser("queue")
    queue.add_argument("--limit", type=int, default=25)
    pmc = commands.add_parser("acquire-pmc")
    pmc.add_argument("batch", type=Path)
    pmc.add_argument("--limit", type=int, default=30)
    pmc.add_argument("--retry-failed", action="store_true",
                     help="Retry transient PMC/Europe PMC failures; permanent 404/no-version routes remain skipped")
    pdf = commands.add_parser("acquire-pdfs")
    pdf.add_argument("batch", type=Path)
    pdf.add_argument("sources", type=Path, help="PSV with key and url columns")
    apply = commands.add_parser("stage")
    apply.add_argument("output", type=Path)
    apply.add_argument("--receipts", type=Path, action="append", default=[])
    apply.add_argument("--reviews", type=Path, action="append", default=[])
    args = parser.parse_args()
    if getattr(args, "limit", 1) < 1:
        parser.error("--limit must be positive")
    if args.command == "queue":
        options = queues(checked_catalogue(args.catalog).values())
        print(json.dumps({name: {"total": len(items), "next": items[:args.limit]}
                          for name, items in options.items()}, ensure_ascii=False, indent=2))
    elif args.command == "acquire-pmc":
        acquire(args.catalog, args.batch, args.limit, args.retry_failed)
    elif args.command == "acquire-pdfs":
        acquire_pdfs(args.catalog, args.batch, args.sources)
    else:
        stage(args.catalog, args.output, args.receipts, args.reviews)


if __name__ == "__main__":
    main()
