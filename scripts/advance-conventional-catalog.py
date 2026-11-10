"""Plan, acquire and stage incremental reviews of the frozen MFC catalogue."""
from argparse import ArgumentParser
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from csv import DictReader
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
BIOC = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/"
OPENALEX = "https://api.openalex.org/works"
JATS_LIMIT = 16 * 1024 * 1024
PERMANENT_PMC_FAILURE = re.compile(
    r"No public PMC version|No PMC Cloud version matches|not available in the BioC open-access subset|HTTP Error 404",
    re.IGNORECASE,
)
TRANSIENT_PMC_FAILURE = re.compile(
    r"timed out|timeout|temporar|HTTP Error (?:408|425|429|500|502|503|504)|\b(?:408|425|429|500|502|503|504)\b",
    re.IGNORECASE,
)


def checked_catalogue(directory):
    rows = read(directory / "publications.psv.gz")
    if len(rows) != C["FROZEN_PUBLICATIONS"]:
        raise ValueError(f"Expected {C['FROZEN_PUBLICATIONS']} frozen publications")
    by_doi = {C["doi_key"](doi): row for row in rows for doi in values(row.get("doi"))}
    def resolve_publication(doi):
        row = by_doi.get(C["doi_key"](doi))
        return (row["key"], row) if row else (None, None)
    C["validate_catalog_arm_registry"](directory, resolve_publication, allow_published_family=True)
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
                      (r["pending"] == "yes" or r["decisions"] == "unreviewed" or
                       "included_in_survey" in values(r["decisions"]))],
    }


QUEUE_FIELDS = ("key", "title", "pmcid", "decisions", "reading_scopes", "machine_signals")


def queue_preview(rows, limit=10, details=False, stage=None):
    all_queues = queues(rows)
    selected = {stage: all_queues[stage]} if stage else all_queues
    return {
        name: {
            "total": len(items),
            "next": items[:limit] if details else [
                {field: row[field] for field in QUEUE_FIELDS if field in row}
                for row in items[:limit]
            ],
        }
        for name, items in selected.items()
    }


def queue_report(directory, limit=10, details=False, stage=None):
    rows = checked_catalogue(directory)
    summary = C["summarize"](list(rows.values()), directory)
    stages = {
        "body_recovered": "body_recovered",
        "identity_confirmed": "documented_integral",
        "individual_screening": "individual_screening",
        "complete_methods_read": "complete_methods_read",
        "admitted_F1_F6": "included_F1_F6",
    }
    queue_data = queue_preview(list(rows.values()), limit, details, stage)
    return {
        "denominator": summary["unique_publications"],
        "coverage": {
            stage: {"count": summary["counts"][metric],
                    "percent": summary["percent"][metric],
                    "remaining_to_3800": summary["remaining_to_over_half"][metric]}
            for stage, metric in stages.items()
        },
        "queues": queue_data,
    }


def pmc_workers(queue, retry_failed=False):
    """Use one worker for public EPMC/BioC retries; keep PMC Cloud batches parallel."""
    providers = {provider for row in queue for provider in row["providers"]}
    if queue and providers <= {"epmc", "bioc"} and ("bioc" in providers or retry_failed):
        return 1
    return 4


def download(url, timeout=20):
    request = Request(url, headers={"User-Agent": "MFC Studio literature catalogue/1.0"})
    with urlopen(request, timeout=timeout) as response:
        data = response.read(JATS_LIMIT + 1)
    if len(data) > JATS_LIMIT:
        raise ValueError("Document exceeds size limit")
    return data


def cloud_route(pmc, expected_dois=()):
    listing = PMC_BUCKET + "?" + urlencode({"list-type": 2, "prefix": pmc + ".", "delimiter": "/"})
    xml = ET.fromstring(download(listing))
    versions = [x.text.rstrip("/") for x in xml.findall("{*}CommonPrefixes/{*}Prefix")
                if re.fullmatch(pmc + r"\.\d+/", x.text or "")]
    if not versions:
        raise ValueError("No public PMC version in bucket")
    expected = {C["doi_key"](doi) for doi in expected_dois if doi}
    candidates = []
    for prefix in versions:
        stem = prefix.rstrip("/")
        metadata_url = f"{PMC_BUCKET}{stem}/{stem}.json"
        metadata = json.loads(download(metadata_url))
        metadata_pmc = str(metadata.get("pmcid") or "").upper()
        metadata_doi = C["doi_key"](metadata.get("doi"))
        if metadata_pmc and metadata_pmc != pmc.upper():
            continue
        if expected and metadata_doi not in expected:
            continue
        url = metadata.get("xml_url")
        if not isinstance(url, str) or not url.startswith(PMC_BUCKET):
            continue
        version = metadata.get("version")
        version = int(version) if str(version).isdecimal() else int(stem.rsplit(".", 1)[1])
        manuscript = str(metadata.get("is_manuscript") or "").casefold()
        rank = {"no": 0, "false": 0, "": 1, "yes": 2, "true": 2}.get(manuscript, 1)
        candidates.append((rank, -version, url, version, manuscript, metadata_doi))
    if not candidates:
        raise ValueError("No PMC Cloud version matches expected DOI and PMCID")
    candidates.sort()
    _, _, url, version, manuscript, doi = candidates[0]
    return {"url": url, "version": str(version), "is_manuscript": manuscript or "NR", "doi": doi}


def cloud_url(pmc, expected_dois=()):
    return cloud_route(pmc, expected_dois)["url"]


def bioc_article(data, row, pmc):
    if b"No result can be found" in data[:512]:
        raise ValueError("not available in the BioC open-access subset")
    root = ET.fromstring(data)
    documents = root.findall("document")
    if len(documents) != 1:
        raise ValueError("BioC response does not contain exactly one article")
    document = documents[0]
    text_by_type = []
    identifiers = {}
    for info in document.findall(".//infon"):
        key = str(info.get("key") or "").casefold()
        if key:
            identifiers.setdefault(key, set()).add((info.text or "").strip())
    for passage in document.findall("passage"):
        value = " ".join((passage.findtext("text") or "").split())
        if value:
            info = passage.find("infon[@key='type']")
            text_by_type.append(((info.text or "").casefold() if info is not None else "", value))
    article_text = " ".join(value for _, value in text_by_type)
    substantive = [value for kind, value in text_by_type if kind not in {"title", "abstract"}]
    if len(article_text) < 2000 or len(substantive) < 4:
        raise ValueError("BioC response lacks a substantive article body")

    expected_dois = {C["doi_key"](doi) for doi in values(row.get("doi"))}
    declared_dois = {C["doi_key"](value) for key, values_ in identifiers.items()
                     if "doi" in key for value in values_ if value}
    expected_pmc = pmc.upper().removeprefix("PMC")
    declared_pmc = {value.upper().removeprefix("PMC") for key, values_ in identifiers.items()
                    if "pmc" in key for value in values_ if value}
    title_passages = [value for kind, value in text_by_type if kind == "title"]
    title_matches = any(C["title_hash"](title) == C["title_hash"](row["title"])
                        for title in title_passages)
    pmc_matches = expected_pmc in declared_pmc
    if declared_dois and expected_dois and not declared_dois & expected_dois:
        return article_text, "wrong_document", "different_doi:" + sorted(declared_dois)[0]
    if declared_dois & expected_dois:
        return article_text, "identity_verified", "doi:" + sorted(declared_dois & expected_dois)[0]
    if pmc_matches and (not title_passages or title_matches):
        return article_text, "identity_verified", "pmcid:" + pmc
    if title_matches:
        return article_text, "identity_verified", "title_sha256:" + C["title_hash"](row["title"])
    return article_text, "body_candidate", "NR"


def select_openalex_routes(rows, works, route_prefix="openalex"):
    works_by_doi = {}
    for work in works:
        doi = C["doi_key"](work.get("doi"))
        if doi:
            if doi in works_by_doi and works_by_doi[doi] != work:
                raise ValueError(f"OpenAlex returned conflicting exact-DOI records: {doi}")
            works_by_doi[doi] = work
    planned = []
    for row in rows:
        dois = sorted(value for value in values(row.get("doi")) if value.startswith("10."))
        matches = [works_by_doi[doi] for doi in dois if doi in works_by_doi]
        if len(matches) > 1:
            raise ValueError(f"OpenAlex returned multiple records for one catalog publication: {row['key']}")
        if not matches:
            continue
        work = matches[0]
        locations = [work.get("best_oa_location"), *(work.get("locations") or [])]
        candidates = {}
        for location in locations:
            if not location or location.get("is_oa") is not True:
                continue
            url = location.get("pdf_url")
            parsed = urlsplit(url or "")
            if parsed.scheme != "https" or not parsed.hostname or parsed.username:
                continue
            source = location.get("source") or {}
            host_kind = source.get("type") or "unknown"
            version = location.get("version") or "unknown"
            rank = ({"publisher": 0, "repository": 1}.get(host_kind, 2),
                    {"publishedVersion": 0, "acceptedVersion": 1,
                     "submittedVersion": 2}.get(version, 3),
                    location is not work.get("best_oa_location"), url)
            if url not in candidates or rank < candidates[url][0]:
                candidates[url] = (rank, location, host_kind, version)
        if not candidates:
            continue
        for index, (url, (rank, location, host_kind, version)) in enumerate(
                sorted(candidates.items(), key=lambda pair: pair[1][0]), 1):
            planned.append({"key": row["key"], "url": url, "provider": "OpenAlex",
                            "license": location.get("license") or "NR", "version": version,
                            "host_kind": host_kind,
                            "landing_page_url": location.get("landing_page_url") or "NR",
                            "route_group": f"{route_prefix}-{index:03d}"})
    return planned


def unattempted_routes(routes, history):
    """Keep only exact public URLs not already captured in the acquisition ledger."""
    attempted = {item["access_url"] for item in history
                 if item.get("access_url") not in {None, "", "NR"}}
    return [item for item in routes if item["url"] not in attempted]


def openalex_candidates(candidates, history):
    """Advance past publications whose OpenAlex locations already have receipts."""
    attempted = {item["key"] for item in history
                 if any(provider.casefold() == "openalex" for provider in values(item.get("provider")))}
    return [row for row in candidates if row["key"] not in attempted]


def plan_openalex_pdfs(directory, output, limit):
    rows = checked_catalogue(directory)
    receipts_path = output.with_name(output.name + ".receipts.json")
    response_directory = output.parent / (output.stem + "-responses")
    if output.exists() or receipts_path.exists() or response_directory.exists():
        raise ValueError(f"Refusing to overwrite an existing route plan or metadata: {output}")
    history = read(directory / "acquisition.psv")
    candidates = [row for row in queues(rows.values())["recover"]
                  if row["open_route_indexed"] == "yes" and
                  any(doi.startswith("10.") for doi in values(row.get("doi")))]
    candidates = openalex_candidates(candidates, history)
    candidates = sorted(candidates, key=rank)[:limit]
    works, response_records = [], []
    for start in range(0, len(candidates), 40):
        batch = candidates[start:start + 40]
        dois = sorted({doi for row in batch for doi in values(row.get("doi")) if doi.startswith("10.")})
        if not dois:
            continue
        query = {"filter": "doi:" + "|".join("https://doi.org/" + doi for doi in dois),
                 "select": "doi,best_oa_location,locations", "per_page": "100"}
        request_url = OPENALEX + "?" + urlencode(query)
        response_bytes = download(request_url)
        response = json.loads(response_bytes)
        actual = response.get("results")
        if not isinstance(actual, list):
            raise ValueError("OpenAlex did not return a works list")
        requested = {C["doi_key"](doi) for doi in dois}
        if any(C["doi_key"](work.get("doi")) not in requested for work in actual):
            raise ValueError("OpenAlex returned a work outside the exact DOI batch")
        works.extend(actual)
        response_records.append({"url": request_url, "raw": response_bytes, "bytes": len(response_bytes),
                                 "sha256": sha256(response_bytes).hexdigest(),
                                 "dois": dois, "response": response})
    prefix = re.sub(r"-sources.*$", "", output.stem, flags=re.IGNORECASE)
    prefix = re.sub(r"(^|-)openalex(?=-|$)", "-", prefix, flags=re.IGNORECASE)
    prefix = re.sub(r"[^A-Za-z0-9-]+", "-", prefix).strip("-") or "batch"
    all_sources = select_openalex_routes(candidates, works, "openalex-" + prefix)
    sources = unattempted_routes(all_sources, history)
    output.parent.mkdir(parents=True, exist_ok=True)
    columns = ["key", "url", "provider", "license", "version", "host_kind", "landing_page_url",
               "route_group"]
    write(output, columns, sources)
    response_directory.mkdir(parents=True)
    response_for_doi = {}
    for index, record in enumerate(response_records, 1):
        (response_directory / f"response-{index:03d}.json").write_bytes(record["raw"])
        for doi in record["dois"]:
            response_for_doi[C["doi_key"](doi)] = record
    routes_by_key = {key: [] for key in (row["key"] for row in candidates)}
    for route in all_sources:
        routes_by_key.setdefault(route["key"], []).append(route)
    metadata_receipts = []
    for row in candidates:
        doi = sorted(value for value in values(row.get("doi")) if value.startswith("10."))[0]
        record = response_for_doi[C["doi_key"](doi)]
        matched = any(C["doi_key"](work.get("doi")) == C["doi_key"](doi) for work in works)
        metadata_receipts.append({
            "key": row["key"], "route_group": "openalex-index-" + prefix,
            "state": "unrecovered", "format": "NR", "access_url": record["url"],
            "bytes": str(record["bytes"]), "sha256": record["sha256"],
            "identity_basis": "index_doi:" + C["doi_key"](doi) if matched else "NR",
            "failure_classes": ("openalex_index: direct OA PDF route listed" if routes_by_key.get(row["key"])
                                else "openalex_index: no direct OA PDF route listed"),
            "provider": "OpenAlex", "source_version": "OpenAlex Works API",
            "license": "NR", "host_kind": "index", "landing_page_url": "NR",
        })
    save(receipts_path, metadata_receipts)
    resolved = len({item["key"] for item in sources})
    print(json.dumps({"candidate_publications": len(candidates), "direct_oa_pdf_routes": len(sources),
                      "publications_with_routes": resolved, "unresolved": len(candidates) - resolved,
                      "source_file": str(output), "lookup_receipts": str(receipts_path),
                      "response_directory": str(response_directory)},
                     ensure_ascii=False))


def pmc_provider_history(history):
    """Return providers attempted and permanently exhausted for each PMCID row."""
    attempted, permanent, transient = {}, {}, {}
    for item in history:
        if not item["route_group"].startswith("pmc-") or item["state"] not in {
            "unrecovered", "wrong_document", "preview_only"
        }:
            continue
        failures = item["failure_classes"]
        labelled = list(re.finditer(r"(?:^| / )(cloud|epmc|bioc): ", failures))
        attempts = []
        if labelled:
            for index, match in enumerate(labelled):
                end = labelled[index + 1].start() if index + 1 < len(labelled) else len(failures)
                attempts.append((match.group(1), failures[match.end():end].strip()))
        else:
            host = urlsplit(item["access_url"]).hostname
            provider = "cloud" if host == "pmc-oa-opendata.s3.amazonaws.com" else (
                "epmc" if host == "www.ebi.ac.uk" else
                "bioc" if host == "www.ncbi.nlm.nih.gov" else None
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
    if fmt not in {"xml", "bioc_xml", "html", "pdf"}:
        raise ValueError(f"Unknown document format: {fmt}")
    extension = "xml" if fmt == "bioc_xml" else fmt
    return directory / sha256(key.encode()).hexdigest()[:16] / f"article.{extension}"


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
                  access_url="NR", bytes="NR", sha256="NR", identity_basis="NR", failure_classes="NR",
                  provider="NR", source_version="NR", license="NR", host_kind="NR",
                  landing_page_url="NR")
    failures = []
    providers_attempted = []
    for provider in row["providers"]:
        providers_attempted.append(provider)
        url = (EPMC + pmc + "/fullTextXML" if provider == "epmc" else
               BIOC + pmc + "/unicode" if provider == "bioc" else PMC_BUCKET)
        source_version = row.get("source_version", "NR")
        try:
            if provider == "cloud":
                cloud = cloud_route(pmc, values(row["doi"]))
                url = cloud["url"]
                source_version = f"PMC OA version {cloud['version']} (is_manuscript={cloud['is_manuscript']})"
            data = download(url)
            if provider == "bioc":
                text, state, basis = bioc_article(data, row, pmc)
                original_path(batch, row["key"], "bioc_xml").write_bytes(data)
                record.update(state=state, format="bioc_xml", access_url=url, bytes=str(len(data)),
                              sha256=sha256(data).hexdigest(), identity_basis=basis, provider=provider)
                break
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
                          sha256=sha256(data).hexdigest(), identity_basis=basis or "NR",
                          provider=provider, source_version=source_version)
            break
        except (OSError, ValueError, ET.ParseError) as error:
            failures.append(f"{provider}: {error}")
            record["access_url"] = url
    if failures:
        record["failure_classes"] = " / ".join(failures)
        if record["state"] == "unrecovered":
            record["provider"] = " ".join(providers_attempted) or "NR"
    save(receipt, record)
    return record


def epmc_fulltext_pmcid(result, doi):
    """Return a PMCID only when an exact DOI has an explicit Europe PMC OA full-text link."""
    if C["doi_key"](result.get("doi")) != C["doi_key"](doi):
        return None
    pmcid = (result.get("pmcid") or "").upper()
    if (not re.fullmatch(r"PMC\d+", pmcid) or result.get("isOpenAccess") != "Y" or
            result.get("inEPMC") != "Y"):
        return None
    links = (result.get("fullTextUrlList") or {}).get("fullTextUrl", [])
    if isinstance(links, dict):
        links = [links]
    if not any(link.get("site") == "Europe_PMC" and link.get("availabilityCode") == "OA" and
               link.get("documentStyle") in {"html", "pdf", "xml"} for link in links):
        return None
    return pmcid


def acquire_epmc(directory, batch, limit):
    """Resolve missing PMCIDs by exact DOI in Europe PMC, then acquire only declared OA full text."""
    rows = checked_catalogue(directory)
    if batch.exists() and any(batch.iterdir()):
        raise ValueError(f"Refusing to overwrite an existing batch: {batch}")
    group_name = batch.name
    if not re.fullmatch(r"[A-Za-z0-9-]+", group_name):
        raise ValueError("Use letters, digits and hyphens in the batch directory name")
    history = read(directory / "acquisition.psv")
    indexed = {item["key"] for item in history
               if item["route_group"].startswith("epmc-index-")}
    candidates = [row for row in queues(rows.values())["recover"]
                  if row["pmcid"] == "NR" and row["key"] not in indexed and
                  any(doi.startswith("10.") for doi in values(row["doi"]))]
    candidates = candidates[:limit]
    if not candidates:
        batch.mkdir(parents=True, exist_ok=True)
        save(batch / "lookup_receipts.json", [])
        save(batch / "queue.json", [])
        save(batch / "receipts.json", [])
        print(json.dumps({"candidate_publications": 0, "open_fulltext_routes": 0,
                          "body_recovered": 0, "batch_directory": str(batch)}))
        return

    doi_by_key = {row["key"]: sorted(doi for doi in values(row["doi"]) if doi.startswith("10."))[0]
                  for row in candidates}
    unique_dois = list(dict.fromkeys(doi_by_key[row["key"]] for row in candidates))
    query = " OR ".join(f"DOI:{doi}" for doi in unique_dois)
    url = EPMC + "search?" + urlencode({"query": query, "format": "json", "resultType": "core",
                                       "pageSize": str(max(25, len(unique_dois)))})
    response_bytes = download(url, timeout=45)
    response = json.loads(response_bytes)
    results = response.get("resultList", {}).get("result")
    if not isinstance(results, list):
        raise ValueError("Europe PMC did not return an article result list")
    requested = {C["doi_key"](doi): doi for doi in unique_dois}
    found = {}
    for result in results:
        doi = C["doi_key"](result.get("doi"))
        if doi not in requested:
            raise ValueError(f"Europe PMC returned an article outside the exact DOI batch: {doi}")
        if doi not in found or epmc_fulltext_pmcid(result, requested[doi]):
            found[doi] = result

    batch.mkdir(parents=True, exist_ok=True)
    (batch / "epmc-search-response.json").write_bytes(response_bytes)
    version = "Europe PMC REST API " + str(response.get("version", "NR"))
    digest = sha256(response_bytes).hexdigest()
    lookup_records, fetch_queue = [], []
    for row in candidates:
        doi = doi_by_key[row["key"]]
        result = found.get(C["doi_key"](doi))
        pmcid = epmc_fulltext_pmcid(result, doi) if result else None
        landing = (f"https://europepmc.org/articles/{pmcid}" if pmcid else "NR")
        reason = (f"epmc_index: exact DOI matched OA full text {pmcid}; body receipt is separate"
                  if pmcid else
                  "epmc_index: no exact DOI record with an OA Europe PMC full-text PMCID")
        lookup_records.append({
            "key": row["key"], "route_group": f"epmc-index-{group_name}",
            "state": "unrecovered", "format": "NR", "access_url": url,
            "bytes": str(len(response_bytes)), "sha256": digest,
            "identity_basis": f"index_doi:{doi}" if result else "NR",
            "failure_classes": reason, "provider": "Europe PMC search",
            "source_version": version, "license": "NR", "host_kind": "index",
            "landing_page_url": landing,
        })
        if pmcid:
            fetch_queue.append({"key": row["key"], "doi": doi, "pmcid": pmcid,
                                "title": row["title"], "providers": ["epmc"],
                                "source_version": version})

    save(batch / "lookup_receipts.json", lookup_records)
    save(batch / "queue.json", fetch_queue)
    identity = runpy.run_path(str(HERE / "index-conventional-catalog-documents.py"))["article_identity"]
    with ThreadPoolExecutor(max_workers=pmc_workers(fetch_queue, retry_failed=True)) as pool:
        receipts = list(pool.map(lambda item: fetch_pmc(item, batch, "pmc-epmc-" + group_name, identity),
                                 fetch_queue))
    save(batch / "receipts.json", receipts)
    print(json.dumps({"candidate_publications": len(candidates),
                      "exact_doi_matches": sum(C["doi_key"](doi) in found for doi in unique_dois),
                      "open_fulltext_routes": len(fetch_queue),
                      "identity_verified": sum(item["state"] == "identity_verified" for item in receipts),
                      "body_candidates": sum(item["state"] == "body_candidate" for item in receipts),
                      "lookup_response_sha256": digest, "batch_directory": str(batch)},
                     ensure_ascii=False))


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
                pending = [p for p in ("cloud", "epmc", "bioc")
                           if p not in exhausted and (p not in tried or p in transient[key])]
            else:
                pending = [p for p in ("cloud", "epmc", "bioc")
                           if p not in tried and p not in exhausted]
            pmcs = values(row["pmcid"])
            if len(pmcs) == 1 and pending:
                queue.append(dict(key=row["key"], doi=row["doi"], pmcid=next(iter(pmcs)),
                                  title=row["title"], providers=pending))
        queue = queue[:limit]
        batch.mkdir(parents=True, exist_ok=True)
        save(queue_file, queue)
    if len(queue) != len({item["key"] for item in queue}) or any(item["key"] not in rows for item in queue):
        raise ValueError("Batch contains duplicate or unknown publication keys")
    with ThreadPoolExecutor(max_workers=pmc_workers(queue, retry_failed)) as pool:
        records = list(pool.map(lambda row: fetch_pmc(row, batch, group, identity), queue))
    save(batch / "receipts.json", records)
    print(json.dumps(dict(Counter(item["state"] for item in records)), sort_keys=True))



def acquire_pdfs(directory, batch, sources):
    rows = checked_catalogue(directory)
    planned = read(sources)
    group = "pdf-" + batch.name
    if not re.fullmatch(r"pdf-[A-Za-z0-9-]+", group) or not planned:
        raise ValueError("Provide a nonempty list and a batch name using letters, digits and hyphens")
    for index, item in enumerate(planned, 1):
        item.setdefault("route_group", f"{group}-{index:03d}")
        url = urlsplit(item["url"])
        if (item["key"] not in rows or url.scheme != "https" or not url.hostname or url.username or
                not re.fullmatch(r"[a-zA-Z0-9-]+", item["route_group"])):
            raise ValueError(f"Unknown publication or invalid public URL: {item['key']}")
    if len(planned) != len({(item["key"], item["route_group"]) for item in planned}):
        raise ValueError("A publication cannot repeat a route-group identifier")
    batch.mkdir(parents=True, exist_ok=True)
    queue_file = batch / "queue.json"
    if queue_file.exists() and planned != read_json(queue_file):
        raise ValueError("The batch already has a different route list")
    save(queue_file, planned)
    index = runpy.run_path(str(HERE / "index-conventional-catalog-documents.py"))
    acquisition = runpy.run_path(str(HERE / "acquire-external-register.py"))

    def fetch_group(routes):
        records = []
        key = routes[0]["key"]
        original = original_path(batch, key, "pdf")
        original.parent.mkdir(parents=True, exist_ok=True)
        row = rows[key]
        for item in routes:
            url = item["url"]
            receipt = original.parent / f"receipt-{item['route_group']}.json"
            if receipt.exists():
                result = read_json(receipt)
                if (result["key"], result["route_group"]) != (key, item["route_group"]):
                    raise ValueError(f"Invalid PDF receipt for {key}")
                records.append(result)
                if result["state"] == "identity_verified":
                    break
                continue
            result = dict(key=key, route_group=item["route_group"], state="unrecovered", format="NR",
                          access_url=url, bytes="NR", sha256="NR", identity_basis="NR",
                          failure_classes="NR", provider=item.get("provider", "NR"),
                          source_version=item.get("version", "NR"), license=item.get("license", "NR"),
                          host_kind=item.get("host_kind", "NR"),
                          landing_page_url=item.get("landing_page_url", "NR"))
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
            records.append(result)
            if result["state"] == "identity_verified":
                break
        return records

    grouped = {}
    for item in planned:
        grouped.setdefault(item["key"], []).append(item)
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = [item for group_records in pool.map(fetch_group, grouped.values())
                   for item in group_records]
    save(batch / "receipts.json", records)
    print(json.dumps(dict(Counter(item["state"] for item in records)), sort_keys=True))


def merge_receipts(rows, ledger, receipt_files):
    known = {(item["key"], item["route_group"]): item for item in ledger}
    for path in receipt_files:
        for item in read_json(path):
            row = rows[item["key"]]
            key = item["key"], item["route_group"]
            if key in known:
                if any(known[key].get(name, "NR") != item.get(name, "NR") for name in
                       set(known[key]) | set(item)):
                    raise ValueError(f"Conflicting receipt: {key}")
                continue
            if item["state"] not in STATES or not re.fullmatch(r"[a-zA-Z0-9-]+", item["route_group"]):
                raise ValueError(f"Invalid acquisition receipt: {key}")
            if item.get("host_kind") == "index":
                basis = item.get("identity_basis", "NR")
                if basis not in {"", "NR"} and not basis.startswith("index_doi:"):
                    raise ValueError(f"Metadata lookup cannot confirm article-body identity: {key}")
                if (item["state"] != "unrecovered" or item.get("format") != "NR" or
                        not str(item.get("bytes", "")).isdecimal() or
                        not re.fullmatch(r"[a-f0-9]{64}", item.get("sha256", ""))):
                    raise ValueError(f"Metadata lookup cannot promote body or omit response hash: {key}")
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


def catalog_row(rows, source):
    if source in rows:
        return rows[source]
    matches = [row for row in rows.values() if source in values(row.get("doi"))]
    if len(matches) != 1:
        raise ValueError(f"Arm source does not resolve to one frozen publication: {source}")
    return matches[0]


def table_columns(path):
    with path.open(encoding="utf-8", newline="") as file:
        columns = DictReader(file, delimiter="|").fieldnames
    if not columns or len(columns) != len(set(columns)):
        raise ValueError(f"Invalid columns in {path.name}")
    return columns


def merge_arm_evidence(rows, arm_ledger, observation_ledger, arm_files, observation_files):
    arms = {item["arm_id"]: item for item in arm_ledger}
    observations = {item["id"]: item for item in observation_ledger}
    original_arm_ids = set(arms)
    family_by_key = {}
    arm_columns = table_columns(C["DATA"] / "external-expansion/arms.psv")
    observation_columns = table_columns(C["DATA"] / "external-expansion/observations.psv")
    method = C["METHOD"]
    for path in arm_files:
        columns, incoming = table_columns(path), read(path)
        if columns != arm_columns:
            raise ValueError(f"Catalog arm file has an unexpected schema: {path}")
        for item in incoming:
            arm_id = item["arm_id"]
            if arm_id in arms and arms[arm_id] != item:
                raise ValueError(f"Conflicting registered arm: {arm_id}")
            arms[arm_id] = item
    for path in observation_files:
        columns, incoming = table_columns(path), read(path)
        if columns != observation_columns:
            raise ValueError(f"Catalog observation file has an unexpected schema: {path}")
        for item in incoming:
            obs_id = item["id"]
            if obs_id in observations and observations[obs_id] != item:
                raise ValueError(f"Conflicting arm observation: {obs_id}")
            observations[obs_id] = item
    if arms and not observations:
        raise ValueError("Every registered arm requires an electrical observation")
    seen_source_families = set()
    for arm in arms.values():
        if arm["role"] not in method["SURVEY"]["ROLES"] or not arm["locators"].strip():
            raise ValueError(f"Arm lacks a role or method/result locator: {arm['arm_id']}")
        family = method["family"](arm)
        if family not in set(method["FAMILY_KEYS"].values()):
            raise ValueError(f"Arm does not map to F1–F6: {arm['arm_id']}")
        row = catalog_row(rows, arm["source"])
        if row["document"] != "documented_integral":
            raise ValueError(f"Arm source lacks confirmed article identity: {arm['arm_id']}")
        if arm["arm_id"] not in original_arm_ids and family in values(row["families"]):
            raise ValueError(f"Catalog arm duplicates an existing publication family: {arm['arm_id']}")
        source_family = row["key"], family
        if source_family in seen_source_families:
            raise ValueError(f"Duplicate source and family registration: {source_family}")
        seen_source_families.add(source_family)
        linked = [obs for obs in observations.values() if obs["arm_id"] == arm["arm_id"]]
        if not linked:
            raise ValueError(f"Arm lacks a linked result: {arm['arm_id']}")
        for obs in linked:
            if (obs["metric"] not in method["UNITS"] or
                    obs["unit"] not in method["UNITS"][obs["metric"]] or
                    obs["status"] not in {"context_only", "quality_hold"} or
                    obs["extraction"] != "manual_text_or_table" or not obs["locator"].strip() or
                    not obs["basis"].strip() or not obs["phase"].strip()):
                raise ValueError(f"Observation lacks a linked result, unit or locator: {obs['id']}")
            load = obs["load_ohm"]
            if load not in {"NR", "variable", "short_circuit"}:
                if not method["decimal"](load) or load not in arm["external_circuit"]:
                    raise ValueError(f"Observation load does not match its arm: {obs['id']}")
        row["families"] = " ".join(sorted(values(row["families"]) | {family}))
        row["evidence"] = " ".join(sorted(values(row["evidence"]) | {"catalog_registered_arm"}))
        family_by_key.setdefault(row["key"], set()).add(family)
    return (list(arms.values()), list(observations.values()), family_by_key,
            arm_columns, observation_columns)


def merge_reviews(rows, ledger, review_files, registered_families=None):
    registered_families = registered_families or {}
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
                verified = (registered_arms.rows[owner]["families"] if owner else set())
                verified |= registered_families.get(row["key"], set())
                if item["scope"] not in C["FULL_METHODS"] or not families <= verified:
                    raise ValueError(f"Control requires a registered arm and full methods: {item['key']}")
                row["families"] = " ".join(sorted(values(row["families"]) | families))
                labels.add("admitted_F1_F6")
            row.update(decisions=" ".join(sorted(labels)), pending="yes" if "pending" in labels else "no",
                       reading_scopes=" ".join(sorted(values(row["reading_scopes"]) | {item["scope"]})),
                       evidence=" ".join(sorted(values(row["evidence"]) | {"catalog_individual_review"})))
            known[item["key"]] = item
    return list(known.values())


def stage(directory, output, receipt_files, review_files, arm_files, observation_files):
    rows = checked_catalogue(directory)
    if output.exists() or not (receipt_files or review_files or arm_files):
        raise ValueError("Use a new staging directory and provide receipts or reviews")
    acquisitions = merge_receipts(rows, read(directory / "acquisition.psv"), receipt_files)
    existing_arms = read(directory / "arms.psv") if (directory / "arms.psv").exists() else []
    existing_observations = read(directory / "observations.psv") if (directory / "observations.psv").exists() else []
    arms, observations, arm_families, arm_columns, observation_columns = merge_arm_evidence(
        rows, existing_arms, existing_observations, arm_files, observation_files
    )
    reviews = merge_reviews(rows, read(directory / "reviews.psv"), review_files, arm_families)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        draft = Path(temp) / "catalog"
        shutil.copytree(directory, draft)
        acquisition_columns = list(acquisitions[0])
        source_metadata = ("provider", "source_version", "license", "host_kind", "landing_page_url")
        acquisition_columns.extend(name for name in source_metadata
                                   if any(name in item for item in acquisitions) and name not in acquisition_columns)
        for item in acquisitions:
            for name in source_metadata:
                if name in acquisition_columns:
                    item.setdefault(name, "NR")
        write(draft / "acquisition.psv", acquisition_columns, acquisitions)
        write(draft / "reviews.psv", list(reviews[0]), reviews)
        if arms:
            write(draft / "arms.psv", arm_columns, arms)
            write(draft / "observations.psv", observation_columns, observations)
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
    queue.add_argument("--limit", type=int, default=10)
    queue.add_argument("--details", action="store_true", help="Print every field for each queued record")
    queue.add_argument("--stage", choices=("recover", "confirm", "screen", "methods", "admission"),
                       help="Show one queue and retain the five-stage coverage summary")
    pmc = commands.add_parser("acquire-pmc")
    pmc.add_argument("batch", type=Path)
    pmc.add_argument("--limit", type=int, default=30)
    pmc.add_argument("--retry-failed", action="store_true",
                     help="Retry transient PMC/Europe PMC failures; permanent 404/no-version routes remain skipped")
    epmc = commands.add_parser("acquire-epmc")
    epmc.add_argument("batch", type=Path)
    epmc.add_argument("--limit", type=int, default=25,
                      help="Resolve this many missing PMCIDs in one exact-DOI Europe PMC query")
    pdf = commands.add_parser("acquire-pdfs")
    pdf.add_argument("batch", type=Path)
    pdf.add_argument("sources", type=Path, help="PSV with key and url columns")
    openalex = commands.add_parser("plan-openalex-pdfs")
    openalex.add_argument("output", type=Path, help="New PSV route plan for acquire-pdfs")
    openalex.add_argument("--limit", type=int, default=100)
    apply = commands.add_parser("stage")
    apply.add_argument("output", type=Path)
    apply.add_argument("--receipts", type=Path, action="append", default=[])
    apply.add_argument("--reviews", type=Path, action="append", default=[])
    apply.add_argument("--arms", type=Path, action="append", default=[])
    apply.add_argument("--observations", type=Path, action="append", default=[])
    args = parser.parse_args()
    if getattr(args, "limit", 1) < 1:
        parser.error("--limit must be positive")
    if args.command == "queue":
        print(json.dumps(queue_report(args.catalog, args.limit, args.details, args.stage),
                         ensure_ascii=False, indent=2))
    elif args.command == "acquire-pmc":
        acquire(args.catalog, args.batch, args.limit, args.retry_failed)
    elif args.command == "acquire-epmc":
        acquire_epmc(args.catalog, args.batch, args.limit)
    elif args.command == "acquire-pdfs":
        acquire_pdfs(args.catalog, args.batch, args.sources)
    elif args.command == "plan-openalex-pdfs":
        plan_openalex_pdfs(args.catalog, args.output, args.limit)
    else:
        stage(args.catalog, args.output, args.receipts, args.reviews, args.arms, args.observations)


if __name__ == "__main__":
    main()
