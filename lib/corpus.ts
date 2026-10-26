import seedData from '../science/corpus-seed.json';
import embedded from '../science/corpus-embedded-assets.json';
import pdfAssets from '../science/corpus-pdf-assets.json';
import {bucket,database,digest} from './server';
export const corpus:any=seedData;
export const rawAssets=pdfAssets;
async function batches(db:D1Database,statements:D1PreparedStatement[]){for(let i=0;i<statements.length;i+=60)await db.batch(statements.slice(i,i+60));}
export async function seedCorpus(){
 const db=database();
 const existing=await db.prepare('SELECT content_sha256,report_json FROM seed_versions WHERE id=?').bind(corpus.version).first<{content_sha256:string;report_json:string}>();
 if(existing){if(existing.content_sha256!==corpus.content_sha256)throw new Error('Immutable corpus version changed; create a new version.');return {alreadyApplied:true,version:corpus.version,report:JSON.parse(existing.report_json)};}
 const initial:D1PreparedStatement[]=[];
 for(const s of corpus.stages)initial.push(db.prepare('INSERT INTO stages(id,ordinal,name) VALUES(?,?,?) ON CONFLICT(id) DO NOTHING').bind(s.id,s.order,s.name_pt));
 await batches(db,initial);
 const sourceStatements:D1PreparedStatement[]=[];
 for(const s of corpus.sources)sourceStatements.push(db.prepare('INSERT INTO sources(id,doi,title,url,access,scope,metadata_json) VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING').bind(s.id,s.doi||null,s.title,s.url,s.access||'metadata',s.type,JSON.stringify(s)));
 await batches(db,sourceStatements);
 const definitions:D1PreparedStatement[]=[];
 for(const s of corpus.stages)for(const p of s.properties)definitions.push(db.prepare('INSERT INTO properties(id,stage_id,name,symbol,unit,implementation_status,metadata_json) VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING').bind(p.id,s.id,p.name_pt,p.symbol,p.unit,'catalog_proposed_not_automatically_resolved',JSON.stringify(p)));
 for(const s of corpus.stage_map)for(const sid of s.source_ids)definitions.push(db.prepare('INSERT INTO source_stages(id,source_id,stage_id,relation) VALUES(?,?,?,?) ON CONFLICT(id) DO NOTHING').bind(sid+':'+s.stage_id,sid,s.stage_id,JSON.stringify({evidence_status:s.evidence_status,initial_family_applicability:s.initial_family_applicability,remaining_gaps:s.remaining_gaps})));
 await batches(db,definitions);
 for(const doc of corpus.documents){
  if(await digest(doc.text)!==doc.sha256)throw new Error('Document content digest mismatch');
  await db.prepare('INSERT INTO documents(id,source_id,title,sha256,raw_sha256,license,format,object_key,complete,text_length,metadata_json) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING').bind(doc.id,doc.source_id,doc.title,doc.sha256,doc.raw_sha256,doc.license,doc.format,doc.object_key,doc.complete?1:0,doc.text_length,JSON.stringify(doc.metadata)).run();
  const chunks:D1PreparedStatement[]=[];
  for(let p=0,n=0;p<doc.text.length;p+=10000,n++){const text=doc.text.slice(p,p+10000);chunks.push(db.prepare('INSERT INTO document_chunks(id,document_id,ordinal,text,sha256) VALUES(?,?,?,?,?) ON CONFLICT(id) DO NOTHING').bind(doc.id+':'+n,doc.id,n,text,await digest(text)));}
  await batches(db,chunks);
 }
 const groups=new Map<string,any[]>();
 for(const r of corpus.records){const rows=groups.get(r.leakage_group_id)||[];rows.push(r);groups.set(r.leakage_group_id,rows);}
 const exps:D1PreparedStatement[]=[];
 for(const [group,rows] of groups)exps.push(db.prepare('INSERT INTO experiments(id,source_id,study_id,family_id,reactor_id,replicate_id,scope,conditions_json) VALUES(?,?,?,?,NULL,NULL,?,?) ON CONFLICT(id) DO NOTHING').bind(group,rows[0].source_id,rows[0].study_id,group,'provenance_family_not_independent_sample',JSON.stringify({record_ids:rows.map(r=>r.id),conditions:rows.map(r=>r.conditions||{}),raw_replicates_available:false})));
 await batches(db,exps);
 const records:D1PreparedStatement[]=[];
 for(const r of corpus.records)records.push(db.prepare('INSERT INTO evidence_records(id,source_id,study_id,leakage_group_id,scope,status,training_eligible,data_json) VALUES(?,?,?,?,?,?,0,?) ON CONFLICT(id) DO NOTHING').bind(r.id,r.source_id,r.study_id,r.leakage_group_id,r.experimental_scope,r.status,JSON.stringify(r)));
 await batches(db,records);
 const obs:D1PreparedStatement[]=[];
 for(const r of corpus.records)for(const [i,o] of (r.observations||[]).entries())obs.push(db.prepare('INSERT INTO observations(id,record_id,metric,value,unit,kind,area_basis,potential_reference,locator,metadata_json) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING').bind(r.id+':'+i,r.id,o.metric,o.value??null,o.unit,o.kind,o.area_basis||null,o.reference_electrode||null,o.locator,JSON.stringify(o)));
 await batches(db,obs);
 const c=corpus.curve;
 await db.prepare('INSERT INTO curves(id,record_id,x_metric,y_metric,x_unit,y_unit,extraction_method,metadata_json) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING').bind(c.id,c.id,'current_density','cell_voltage','A/m2','V','digitized_published_curve_not_raw_replicate',JSON.stringify({...c,points:undefined})).run();
 await batches(db,c.points.map((p:any,i:number)=>db.prepare('INSERT INTO curve_points(id,curve_id,ordinal,x,y,uncertainty) VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING').bind(c.id+':'+i,c.id,i,p.current_density_A_m2,p.cell_voltage_V,p.voltage_digitization_bound_V)));
 for(const asset of embedded){const bytes=Uint8Array.from(atob(asset.content_base64),c=>c.charCodeAt(0));await bucket().put(asset.object_key,bytes,{httpMetadata:{contentType:asset.content_type},customMetadata:{sha256:asset.sha256}});}
 const now=new Date().toISOString();
 await db.prepare('INSERT INTO seed_versions(id,content_sha256,report_json,applied_at) VALUES(?,?,?,?) ON CONFLICT(id) DO NOTHING').bind(corpus.version,corpus.content_sha256,JSON.stringify(corpus.report),now).run();
 return {alreadyApplied:false,version:corpus.version,report:corpus.report};
}
export async function corpusStatus(){
 const db=database();const counts:Record<string,number>={};
 for(const table of ['stages','properties','sources','source_stages','documents','document_chunks','experiments','evidence_records','observations','curves','curve_points']){const r=await db.prepare(`SELECT COUNT(*) AS count FROM ${table}`).first<{count:number}>();counts[table]=r?.count||0;}
 const eligible=await db.prepare('SELECT COUNT(*) AS count FROM evidence_records WHERE training_eligible=1').first<{count:number}>();
 const seed=await db.prepare('SELECT * FROM seed_versions WHERE id=?').bind(corpus.version).first();
 const stored=[];for(const a of rawAssets)stored.push({id:a.id,present:!!await bucket().head(a.object_key)});
 return {version:corpus.version,counts,training_eligible_records:eligible?.count||0,seed_applied:!!seed,pdf_assets:stored,content_sha256:seed?.content_sha256||null};
}
