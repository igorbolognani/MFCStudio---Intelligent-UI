"""Retrieve the reviewed author-hosted copy into a private directory, never into the public corpus."""
from pathlib import Path
import argparse,hashlib,json,subprocess,urllib.request
ROOT=Path(__file__).resolve().parents[1]

def acquire(destination):
    meta=json.loads((ROOT/'research/corpus-v0.4/S02-extraction.json').read_text())['acquisition']
    destination=Path(destination).resolve()
    if destination.is_relative_to(ROOT):raise ValueError('Use a private destination outside the public checkout')
    destination.mkdir(parents=True,exist_ok=True)
    pdf=destination/'S02.pdf'
    if pdf.exists():
        payload=pdf.read_bytes();status='reused_verified_copy'
    else:
        with urllib.request.urlopen(meta['url'],timeout=45) as response:payload=response.read(10_000_001)
        status='retrieved'
    if not payload.startswith(b'%PDF-') or len(payload)>10_000_000:raise ValueError('Invalid or oversized PDF; not installed')
    if hashlib.sha256(payload).hexdigest()!=meta['sha256']:raise ValueError('Source version changed: review required; reviewed copy not overwritten')
    if not pdf.exists():pdf.write_bytes(payload)
    text=destination/'S02.txt'
    subprocess.run(['pdftotext','-layout',str(pdf),str(text)],check=True)
    return {'source_id':'S02','status':status,'sha256':meta['sha256'],'size_bytes':len(payload),
            'extracted_text_sha256':hashlib.sha256(text.read_bytes()).hexdigest(),
            'public_redistribution':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('private_destination');args=parser.parse_args()
    print(json.dumps(acquire(args.private_destination),indent=2))
