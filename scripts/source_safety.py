"""Exclude publisher runtime configuration from research HTML; never print matches."""
from __future__ import annotations
import argparse,base64,gzip,html,json,re,subprocess,zipfile,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GOOGLE_KEY=re.compile(rb'AI'+rb'za[A-Za-z0-9_-]{35}')
SCRIPT=re.compile(r'<script\b(?P<attrs>[^>]*)>(?P<body>[\s\S]*?)</script\s*>',re.I)

def sanitize_html(text:str)->str:
 def replace(m):
  if re.search(r'type\s*=\s*[\"\']math/(?:tex|latex)',m['attrs'],re.I):
   return '<span class="source-equation">'+html.escape(m['body'])+'</span>'
  return ''
 cleaned=SCRIPT.sub(replace,text)
 return GOOGLE_KEY.sub(b'[REMOVED_EXTERNAL_API_KEY]',cleaned.encode()).decode()

def inspect_bytes(payload:bytes,name:str,depth=0)->list[dict]:
 hits=[]
 count=len(GOOGLE_KEY.findall(payload))
 if count:hits.append({'path':name,'count':count})
 if depth>=3:return hits
 if payload.startswith(b'\x1f\x8b'):
  try:hits+=inspect_bytes(gzip.decompress(payload),name+'::gzip',depth+1)
  except (OSError,EOFError):pass
 if payload.startswith(b'PK\x03\x04'):
  try:
   with zipfile.ZipFile(io.BytesIO(payload)) as z:
    for member in z.infolist():
     if member.file_size<20_000_000:hits+=inspect_bytes(z.read(member),name+'::'+member.filename,depth+1)
  except zipfile.BadZipFile:pass
 if name.split('::')[0].endswith('.json'):
  try:
   value=json.loads(payload)
   if isinstance(value,list):
    for i,item in enumerate(value):
     if isinstance(item,dict) and isinstance(item.get('content_base64'),str):
      hits+=inspect_bytes(base64.b64decode(item['content_base64'],validate=True),name+f'::embedded[{i}]',depth+1)
  except (ValueError,UnicodeError):pass
 return hits

def scan_current(root=ROOT)->list[dict]:
 paths=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root).decode().split('\0')
 hits=[]
 for path in dict.fromkeys(paths):
  if path and (root/path).is_file():hits+=inspect_bytes((root/path).read_bytes(),path)
 return hits

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 hits=scan_current();print(json.dumps({'scan':'tracked_and_pending_source_including_archives_and_embedded_assets','matches':hits,'clean':not hits}))
 raise SystemExit(bool(hits))
