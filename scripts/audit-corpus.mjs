/** Read-only scientific integrity audit. Never promotes evidence to training. */
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {provenanceComponents} from '../science/validation.mjs';
const hash=s=>createHash('sha256').update(s).digest('hex');
export function auditCorpus(seed){
 const errors=[],warnings=[];
 const unique=(rows,label)=>{const ids=new Set();for(const r of rows){if(!r.id||ids.has(r.id))errors.push(`${label}: duplicate or missing id ${r.id}`);ids.add(r.id);}return ids;};
 const sources=unique(seed.sources,'source'),stages=unique(seed.stages,'stage');
 unique(seed.records,'record');unique(seed.documents,'document');
 if(stages.size!==11)errors.push('Expected eleven stages');
 let numeric=0,missing=0;const scopes={},unmapped=[],missingCells=[];
 const coverage=seed.stages.map(s=>({stage_id:s.id,records:0,numeric_cells:0,source_ids:[],provenance_groups:[],commercial_records:0}));
 for(const r of seed.records){
  if(!sources.has(r.source_id))errors.push(`Unknown source: ${r.id}`);
  if(!r.study_id||!r.leakage_group_id||!r.source_locator)errors.push(`Incomplete provenance: ${r.id}`);
  scopes[r.experimental_scope]=(scopes[r.experimental_scope]||0)+1;
  if(!r.stage_ids?.length)unmapped.push(r.id);
  let count=0;
  for(const [i,o] of (r.observations||[]).entries()){
   if(!o.metric||!o.unit||!o.locator||!o.kind)errors.push(`Incomplete observation: ${r.id}:${i}`);
   if(o.value===null){missing++;missingCells.push({record_id:r.id,index:i,kind:o.kind});if(!o.kind.includes('missing'))warnings.push(`Unqualified missing value: ${r.id}:${i}`);}
   else if(typeof o.value!=='number'||!Number.isFinite(o.value))errors.push(`Invalid numeric value: ${r.id}:${i}`);
   else {numeric++;count++;}
  }
  for(const id of r.stage_ids||[]){const c=coverage.find(s=>s.stage_id===id);if(!c){errors.push(`Unknown stage: ${r.id}:${id}`);continue;}c.records++;c.numeric_cells+=count;c.source_ids.push(r.source_id);c.provenance_groups.push(r.leakage_group_id);if(['commercial_offer_snapshot','supplier_or_manufacturer_specification'].includes(r.experimental_scope))c.commercial_records++;}
 }
 for(const d of seed.documents){if(!sources.has(d.source_id))errors.push(`Unknown document source: ${d.id}`);if(hash(d.text)!==d.sha256)errors.push(`Text hash mismatch: ${d.id}`);if(Array.from(d.text).length!==d.text_length)errors.push(`Text length mismatch: ${d.id}`);}
 let components=[];try{components=provenanceComponents(seed.records);}catch(e){errors.push(e.message);}
 for(const c of coverage){c.source_ids=[...new Set(c.source_ids)].sort();c.provenance_groups=[...new Set(c.provenance_groups)].sort();}
 const {content_sha256,...payload}=seed;
 // The published digest uses Python canonical JSON; document hashes are checked here.
 return {audit_version:'1.0.0',corpus_version:seed.version,corpus_declared_sha256:content_sha256,status:errors.length?'failed':'passed_with_explicit_limits',errors,warnings,records:seed.records.length,numeric_cells:numeric,missing_cells:missing,missing_observations:missingCells,documents_verified:seed.documents.length,scopes,coverage,records_without_explicit_stage_mapping:unmapped,connected_provenance_components:components,training_eligible_records:seed.records.filter(r=>r.training_eligible).length,experimental_predictive_validation:false,limits:['Stage counts overlap: one record may describe several components.','Provenance components include commercial sources and are not counts of independent experiments.','Source-stage links are not substituted for missing record-stage attribution.','Document text integrity is not scientific review of every page.','No parameter fitting, causal attribution or predictive validation is performed.']};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const seed=JSON.parse(readFileSync(new URL('../science/corpus-seed.json',import.meta.url),'utf8'));
 const result=auditCorpus(seed);const output=JSON.stringify(result,null,2)+'\n';
 if(process.argv[2])writeFileSync(process.argv[2],output);else process.stdout.write(output);
 console.error(JSON.stringify({status:result.status,records:result.records,numeric:result.numeric_cells,missing:result.missing_cells,unmapped:result.records_without_explicit_stage_mapping.length,errors:result.errors}));
 if(result.errors.length)process.exitCode=1;
}
