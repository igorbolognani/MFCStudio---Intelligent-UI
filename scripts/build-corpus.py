"""Build deterministic D1/R2 seed from preserved primary documents, not summaries."""
from pathlib import Path
import json,hashlib,base64,gzip
import importlib.util
from source_safety import inspect_bytes
R=Path(__file__).resolve().parents[1];b=R/'research/corpus-v0.2'
sha=lambda v:hashlib.sha256(v).hexdigest()
sources=json.loads((b/'index_sources.json').read_text())
next_base=R/'research/corpus-v0.3'
material_module=importlib.util.spec_from_file_location('build_materials',R/'scripts/build-materials.py')
material_builder=importlib.util.module_from_spec(material_module);material_module.loader.exec_module(material_builder)
materials=material_builder.build()
additional_source=json.loads((next_base/'S29_source.json').read_text())
sources+=materials['sources']+[additional_source]
for s in sources:
 if s['id']=='S01':s['access']='historical_full_text_sections; current_retrieval_403'
 if s['id']=='S15':s['limits']='Platform reference only, not scientific evidence; current Site uses D1/R2 and ChatGPT authentication.'
records=[json.loads(l) for l in (R/'science/legacy-v0.1/evidence_seed.jsonl').read_text().splitlines()]+json.loads((b/'observations.json').read_text())
records+=materials['records']
for raw_record in json.loads((next_base/'S29_observations.json').read_text()):
 conditions={k:v for k,v in raw_record.items() if k not in ['id','observations','limits']}
 conditions['published_concentration_group_id']=f"S29-{raw_record['medium']}-shading-group-{(raw_record['table_row_within_medium']-1)//3+1:02}"
 conditions['group_definition']='Three adjacent rows grouped by published table shading as comparable concentrations; not chronological timestamps.'
 conditions['temperature_K']=None
 obs=raw_record['observations']
 for o in obs:
  if o['value'] is None:o['kind']='missing_reported_equipment_fault'
 records.append({'id':raw_record['id'],'source_id':'S29','study_id':additional_source['doi'],
  'leakage_group_id':additional_source['leakage_group_id'],'experimental_scope':'full_cell_mfc',
  'stage_ids':additional_source['stage_ids'],'source_locator':'Supplement Table1/2; per-cell locators retained',
  'status':'candidate_not_training_admitted','training_eligible':False,'conditions':conditions,
  'observations':obs,'limitations':raw_record['limits']+additional_source['issues']})
records.append({'id':'S29-methods-context','source_id':'S29','study_id':additional_source['doi'],
 'leakage_group_id':additional_source['leakage_group_id'],'experimental_scope':'full_cell_mfc',
 'stage_ids':additional_source['stage_ids'],'source_locator':'Main Methods pp8–10; supplementFigureS7',
 'status':'reviewed_context_not_calibrated','training_eligible':False,'conditions':additional_source['methods'],
 'observations':[],'limitations':additional_source['issues']+[additional_source['independence_reason']]})
records.append({'id':'S19-loading-basis-qualification','source_id':'S19','study_id':'10.3389/fbioe.2024.1397294',
 'leakage_group_id':'Jin2024-DNMFC-30mL','experimental_scope':'source_qualification',
 'stage_ids':['cathode_catalyst'],'source_locator':'Methods2.1; original Pt/C loading wording',
 'status':'reviewed_mass_basis_unresolved','training_eligible':False,'observations':[],
 'conditions':{'qualifies_record_id':'S19-methods','qualifies_metric':'Pt_loading','raw_reported_value':.5,
  'raw_unit':'mg/cm2','mass_basis':'Pt metal vs Pt/C unresolved','metal_loading_binding_admitted':False},
 'limitations':['Do not relabel the existing nominal loading as mgPt/cm2. Source does not give Pt fraction or establish the mass basis.']})
for r in records:r['training_eligible']=False
catalog=json.loads((R/'science/legacy-v0.1/parameter_catalog.json').read_text())
mapping=json.loads((b/'stage_evidence_map.json').read_text())
for entry in mapping:
 for source in materials['sources']+[additional_source]:
  if entry['stage_id'] in source['stage_ids'] and source['id'] not in entry['source_ids']:entry['source_ids'].append(source['id'])
 entry['commercial_context_source_ids']=[s['id'] for s in materials['sources'] if entry['stage_id'] in s['stage_ids']]
 entry['remaining_gaps']+= [next(s['acquisition_and_comparability_requirement'] for s in materials['stage_acquisition_plan'] if s['stage_id']==entry['stage_id'])]
manifest=json.loads((b/'documents_manifest.json').read_text())
docs=[];assets=[]
for sid in ['S08','S09','S17','S18','S19','S29']:
 base=next_base if sid=='S29' else b
 src=next(s for s in sources if s['id']==sid);p=base/('fulltext/S29_main.txt' if sid=='S29' else f'fulltext/{sid}.txt');raw=base/('documents/NPJ2024.html' if sid=='S29' else f'documents/{sid}.html');t=p.read_text()
 if inspect_bytes(raw.read_bytes(),str(raw)):raise ValueError('Publisher HTML requires sanitization: '+sid)
 source_manifest=next(x for x in (json.loads((next_base/'documents_manifest.json').read_text()) if sid=='S29' else manifest) if x['path']==str(raw.relative_to(base)))
 object_key=('corpus/v03/' if sid=='S29' else 'corpus/v02/')+sid+'.html.gz'
 docs.append({'id':sid+'-fulltext','source_id':sid,'title':src['title'],'sha256':sha(t.encode()),'raw_sha256':sha(raw.read_bytes()),'license':'CC-BY-4.0','format':'text/plain','complete':True,'text_length':len(t),'text':t,'object_key':object_key,'metadata':{'doi':src.get('doi'),'source_url':src['url'],'authors':src.get('authors'),'retrieved_at':src.get('retrieved_at','2026-10-25'),'read_scope':src.get('read_scope'),'text_extraction':'complete extracted article text; typography and figures in original HTML/PDF','original_html_object_key':object_key,'pdf_asset_id':sid+'-pdf','license_url':'https://creativecommons.org/licenses/by/4.0/','source_html_sanitization':source_manifest.get('sanitization'),'source_html_retrieved_sha256':source_manifest.get('retrieved_sha256',source_manifest['sha256'])}})
 compressed=gzip.compress(raw.read_bytes(),mtime=0)
 assets.append({'id':sid+'-html','object_key':docs[-1]['object_key'],'content_base64':base64.b64encode(compressed).decode(),'sha256':sha(compressed),'content_type':'application/gzip'})
supp=b/'documents/S18_supplement.txt';t=supp.read_text();raw=b/'documents/S18_supplement/energies-3078330-supplementary.pdf'
docs.append({'id':'S18-supplement','source_id':'S18','title':'S18 · Supplementary information S1–S10','sha256':sha(t.encode()),'raw_sha256':sha(raw.read_bytes()),'license':'CC-BY-4.0','format':'text/plain','complete':True,'text_length':len(t),'text':t,'object_key':None,'metadata':{'doi':'10.3390/en17143574','source_url':'https://www.mdpi.com/article/10.3390/en17143574/s1','pdf_asset_id':'S18-supplement-pdf','pages':6,'contains_raw_individual_data':False}})
t=(next_base/'fulltext/S29_supplement.txt').read_text();raw=next_base/'documents/NPJ2024_supplement.pdf'
docs.append({'id':'S29-supplement','source_id':'S29','title':'S29 · Supplementary information','sha256':sha(t.encode()),'raw_sha256':sha(raw.read_bytes()),'license':'CC-BY-4.0','format':'text/plain','complete':True,'text_length':len(t),'text':t,'object_key':None,'metadata':{'doi':additional_source['doi'],'source_url':additional_source['supplement_url'],'pdf_asset_id':'S29-supplement-pdf','pages':13,'contains_tabulated_individual_reactor_values':True,'contains_raw_individual_timeseries':False}})
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
for name,asset_id in [('NPJ2024.pdf','S29-pdf'),('NPJ2024_supplement.pdf','S29-supplement-pdf')]:
 path=next_base/'documents'/name
 raw_assets.append({'id':asset_id,'source_id':'S29','path':str(path.relative_to(R)),'sha256':sha(path.read_bytes()),'size_bytes':path.stat().st_size,'license':'CC-BY-4.0','object_key':'corpus/v03/'+asset_id+'.pdf','content_type':'application/pdf'})
all_obs=[o for r in records for o in r.get('observations',[])]
seed={'version':'mfc-corpus/0.3.0','sources':sources,'stages':catalog,'stage_map':mapping,'records':records,'documents':docs,'curve':curve,'material_curation':{'report':materials['report'],'experimental_links':materials['experimental_links'],'record_qualifications':materials['record_qualifications'],'stage_acquisition_plan':materials['stage_acquisition_plan']},'report':{'properties_proposed':110,'sources':len(sources),'complete_main_articles':6,'supplements':2,'records':len(records),'observations':len(all_obs),'numeric_observations':sum(o.get('value') is not None for o in all_obs),'missing_observation_cells':sum(o.get('value') is None for o in all_obs),'digitized_curve_points':len(curve['points']),'material_variants':materials['report']['material_variants'],'commercial_offer_snapshots':materials['report']['offer_snapshots'],'S29_reactor_feed_records':117,'S29_measured_response_pairs':115,'S29_missing_response_pairs':2,'training_eligible_records':0,'predictor_trained':False,'experimental_error_metrics':None,'all_11_stages_mapped':True,'independent_validation_pending':True}}
canonical=json.dumps(seed,ensure_ascii=False,sort_keys=True,separators=(',',':'));seed['content_sha256']=sha(canonical.encode())
(R/'science/corpus-seed.json').write_text(json.dumps(seed,ensure_ascii=False,separators=(',',':'))+'\n')
(R/'science/corpus-embedded-assets.json').write_text(json.dumps(assets,separators=(',',':'))+'\n')
(R/'science/corpus-pdf-assets.json').write_text(json.dumps(raw_assets,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(seed['report'],indent=2))
