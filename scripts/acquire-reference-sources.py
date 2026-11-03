"""Resume acquisition of the preserved reference-document versions into a private directory.

Downloads original documents, including declared ZIP entries. Existing matching
files are reused. Any different version is refused before overwriting.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def acquire(directory):
    target = Path(directory).resolve()
    if target.is_relative_to(ROOT):
        raise ValueError('Keep private/full source documents outside the git checkout')
    data = json.loads((ROOT / 'research/reference-families-v0.1/catalog.json').read_text())
    target.mkdir(parents=True, exist_ok=True)
    report = []
    for doc in data['documents'] + data['commercial_documents']:
        relative = doc.get('archive_path') or ('documents/' + doc['original_filename'])
        local = target / relative.removeprefix('documents/')
        if local.exists():
            raw = local.read_bytes()
            cached = True
        else:
            request = urllib.request.Request(doc['acquisition']['url'], headers={'User-Agent': 'MFCStudioResearch/0.1'})
            try:
                with urllib.request.urlopen(request, timeout=55) as response:
                    raw = response.read()
                acq = doc['acquisition']
                if acq.get('container') == 'zip':
                    if hashlib.sha256(raw).hexdigest() != acq['container_sha256']:
                        raise ValueError('Container source version changed: ' + doc['id'])
                    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                        raw = archive.read(acq['entry'])
                cached = False
            except Exception as exc:
                report.append({'id': doc['id'], 'status': 'pending', 'reason': str(exc)})
                continue
        if len(raw) != doc['bytes'] or hashlib.sha256(raw).hexdigest() != doc['sha256']:
            raise ValueError('Source version changed; existing work preserved: ' + doc['id'])
        if not cached:
            local.parent.mkdir(parents=True, exist_ok=True)
            temporary = local.with_suffix(local.suffix + '.partial')
            temporary.write_bytes(raw)
            temporary.replace(local)
        report.append({'id': doc['id'], 'status': 'verified_cached' if cached else 'downloaded_verified'})
    (target / 'acquisition-checkpoint.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory')
    print(json.dumps(acquire(parser.parse_args().directory), ensure_ascii=False, indent=2))
