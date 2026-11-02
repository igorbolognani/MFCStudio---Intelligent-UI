import {readFileSync,writeFileSync} from 'node:fs';
import {auditCorpus} from './audit-corpus.mjs';
const read=p=>JSON.parse(readFileSync(new URL(p,import.meta.url),'utf8'));
const original=read('../science/corpus-seed.json');
const review=read('../research/audits/record-stage-review.json');
if(review.corpus_version!==original.version && !['mfc-corpus/0.3.1','mfc-corpus/0.4.0'].includes(original.version))throw Error('Review version mismatch');
const seed=structuredClone(original),seen=new Set();
for(const row of review.reviews){
 const record=seed.records.find(r=>r.id===row.record_id);
 if(!record||seen.has(row.record_id)||!row.basis||!row.evidence_access_this_round)throw Error('Invalid or conflicting scope review');
 if(record.stage_ids?.length && JSON.stringify(record.stage_ids)!==JSON.stringify(row.stage_ids))throw Error('Conflicting stage assignment');
 seen.add(row.record_id);record.stage_ids=row.stage_ids;
}
const report=auditCorpus(seed);
report.review_layer='record-stage-review.json; applied in memory only';
report.production_applied=false;
if(report.errors.length)throw Error(JSON.stringify(report.errors));
const output=JSON.stringify(report,null,2)+'\n';
if(process.argv[2])writeFileSync(process.argv[2],output);else process.stdout.write(output);
