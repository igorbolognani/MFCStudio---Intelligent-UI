"""Build deterministic D1/R2 seed from preserved primary documents, not summaries."""
from pathlib import Path
import json,hashlib,base64,gzip
from source_safety import inspect_bytes
R=Path(__file__).resolve().parents[1];b=R/'research/corpus-v0.2'
sha=lambda v:hashlib.sha256(v).hexdigest()
sources=json.loads((b/'index_sources.json').read_text())
for s in sources:
 if s['id']=='S01':s['access']='historical_full_text_sections; current_retrieval_403'
 if s['id']=='S15':s['limits']='Platform reference only, not scientific evidence; current Site uses D1/R2 and ChatGPT authentication.'
records=[json.loads(l) for l in (R/'science/legacy-v0.1/evidence_seed.jsonl').read_text().splitlines()]+json.loads((b/'observations.json').read_text())
for r in records:r['training_eligible']=False
catalog=json.loads((R/'science/legacy-v0.1/parameter_catalog.json').read_text())
mapping=json.loads((b/'stage_evidence_map.json').read_text())
manifest=json.loads((b/'documents_manifest.json').read_text())
docs=[];assets=[]
for sid in ['S08','S09','S17','S18','S19']:
 src=next(s for s in sources if s['id']==sid);p=b/f'fulltext/{sid}.txt';raw=b/f'documents/{sid}.html';t=p.read_text()
 if inspect_bytes(raw.read_bytes(),str(raw)):raise ValueError('Publisher HTML requires sanitization: '+sid)
 source_manifest=next(x for x in manifest if x['path']==f'documents/{sid}.html')
 docs.append({'id':sid+'-fulltext','source_id':sid,'title':src['title'],'sha256':sha(t.encode()),'raw_sha256':sha(raw.read_bytes()),'license':'CC-BY-4.0','format':'text/plain','complete':True,'text_length':len(t),'text':t,'object_key':'corpus/v02/'+sid+'.html.gz','metadata':{'doi':src.get('doi'),'source_url':src['url'],'authors':src.get('authors'),'retrieved_at':'2026-10-25','read_scope':src.get('read_scope'),'text_extraction':'complete extracted article text; typography and figures in original HTML/PDF','original_html_object_key':'corpus/v02/'+sid+'.html.gz','pdf_asset_id':sid+'-pdf','license_url':'https://creativecommons.org/licenses/by/4.0/','source_html_sanitization':source_manifest.get('sanitization'),'source_html_retrieved_sha256':source_manifest.get('retrieved_sha256',source_manifest['sha256'])}})
 compressed=gzip.compress(raw.read_bytes(),mtime=0)
 assets.append({'id':sid+'-html','object_key':docs[-1]['object_key'],'content_base64':base64.b64encode(compressed).decode(),'sha256':sha(compressed),'content_type':'application/gzip'})
supp=b/'documents/S18_supplement.txt';t=supp.read_text();raw=b/'documents/S18_supplement/energies-3078330-supplementary.pdf'
docs.append({'id':'S18-supplement','source_id':'S18','title':'S18 · Supplementary information S1–S10','sha256':sha(t.encode()),'raw_sha256':sha(raw.read_bytes()),'license':'CC-BY-4.0','format':'text/plain','complete':True,'text_length':len(t),'text':t,'object_key':None,'metadata':{'doi':'10.3390/en17143574','source_url':'https://www.mdpi.com/article/10.3390/en17143574/s1','pdf_asset_id':'S18-supplement-pdf','pages':6,'contains_raw_individual_data':False}})
curve=json.loads((b/'S18_CC_curve_digitized.json').read_text())
records.append({'id':curve['id'],'source_id':'S18','study_id':curve['doi'],'leakage_group_id':curve['leakage_group_id'],'experimental_scope':'full_cell_mfc','source_locator':curve['source_locator'],'status':'candidate','training_eligible':False,'observations':[],'conditions':curve['conditions'],'limitations':curve['limitations']+[curve['normalization_issue']]})
raw_assets=[]
for row in manifest:
 if row['path'].endswith('.pdf'):
  path=b/row['path'];asset_id=row['source_id']+('-supplement-pdf' if 'supplement' in row['path'] else '-pdf')
  raw_assets.append({'id':asset_id,'source_id':row['source_id'],'path':str(path.relative_to(R)),'sha256':row['sha256'],'size_bytes':row['size_bytes'],'license':row['license'],'object_key':'corpus/v02/'+asset_id+'.pdf','content_type':'application/pdf'})
supp_pdf=b/'documents/S18_supplement/energies-3078330-supplementary.pdf'
if not any(a['id']=='S18-supplement-pdf' for a in raw_assets):
 raw_assets.append({'id':'S18-supplement-pdf','source_id':'S18','path':str(supp_pdf.relative_to(R)),'sha256':sha(supp_pdf.read_bytes()),'size_bytes':supp_pdf.stat().st_size,'license':'CC-BY-4.0','object_key':'corpus/v02/S18-supplement-pdf.pdf','content_type':'application/pdf'})
seed={'version':'mfc-corpus/0.2.1','sources':sources,'stages':catalog,'stage_map':mapping,'records':records,'documents':docs,'curve':curve,'report':{'properties_proposed':110,'sources':len(sources),'complete_main_articles':5,'supplements':1,'records':len(records),'observations':sum(len(r.get('observations',[])) for r in records),'digitized_curve_points':len(curve['points']),'training_eligible_records':0,'predictor_trained':False,'experimental_error_metrics':None,'all_11_stages_mapped':True,'independent_validation_pending':True}}
canonical=json.dumps(seed,ensure_ascii=False,sort_keys=True,separators=(',',':'));seed['content_sha256']=sha(canonical.encode())
(R/'science/corpus-seed.json').write_text(json.dumps(seed,ensure_ascii=False,separators=(',',':'))+'\n')
(R/'science/corpus-embedded-assets.json').write_text(json.dumps(assets,separators=(',',':'))+'\n')
(R/'science/corpus-pdf-assets.json').write_text(json.dumps(raw_assets,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(seed['report'],indent=2))
