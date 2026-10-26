"""Publish only allowlisted CC BY corpus bytes to an owner-private Site.
Pass {url,token} on stdin. Credentials are never written or printed.
"""
from pathlib import Path
import json,urllib.request,urllib.error,sys,termios
root=Path(__file__).resolve().parents[1]
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):return None
opener=urllib.request.build_opener(NoRedirect)
attrs=None
if sys.stdin.isatty():
 attrs=termios.tcgetattr(sys.stdin);hidden=attrs.copy();hidden[3]&=~termios.ECHO;termios.tcsetattr(sys.stdin,termios.TCSANOW,hidden)
print('Ready for private Site settings on stdin (input hidden).',flush=True)
try:settings=json.loads(input())
finally:
 if attrs:termios.tcsetattr(sys.stdin,termios.TCSANOW,attrs)
origin=settings['url'].rstrip('/')
assert origin.startswith('https://') and origin.endswith('.chatgpt.site')
baseheaders={'OAI-Sites-Authorization':'Bearer '+settings['token']}
def call(path,method='GET',data=None,content_type='application/json',expected=(200,)):
 headers={**baseheaders,'Content-Type':content_type};req=urllib.request.Request(origin+path,data=data,headers=headers,method=method)
 try:
  with opener.open(req,timeout=55) as response:status=response.status;body=response.read()
 except urllib.error.HTTPError as error:status=error.code;body=error.read()
 if status not in expected:raise RuntimeError(f'{method} {path}: HTTP {status}; '+body[:400].decode(errors='replace'))
 try:result=json.loads(body)
 except Exception:result={'http_status':status,'html_bytes':len(body)}
 return result,status
report={'url':origin,'publication_audit':'shared_corpus_and_access_boundary','seed':call('/api/seed','POST',b'')[0],'pdf_uploads':[]}
print(json.dumps({'seed':report['seed']}),flush=True)
for asset in json.loads((root/'science/corpus-pdf-assets.json').read_text()):
 value,_=call('/api/corpus-assets/'+asset['id'],'PUT',(root/asset['path']).read_bytes(),'application/pdf')
 report['pdf_uploads'].append(value);print(json.dumps({'asset':asset['id'],'stored':True}),flush=True)
report['database']=call('/api/seed')[0]
report['service_cannot_impersonate_visitor']=call('/api/scenarios',expected=(401,))[1]==401
report['development_QA_not_public']=call('/qa',expected=(404,))[1]==404
report['landing_available']=call('/')[1]==200
(root/'docs/hosted-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'complete':True,'counts':report['database']['counts'],'pdf_assets':report['database']['pdf_assets'],'auth_boundary':report['service_cannot_impersonate_visitor'],'qa_production_404':report['development_QA_not_public']}),flush=True)
