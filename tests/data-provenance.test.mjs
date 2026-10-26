import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {provenanceComponents,groupedHoldout} from '../science/validation.mjs';
const seed=JSON.parse(readFileSync(new URL('../science/corpus-seed.json',import.meta.url),'utf8'));

test('related S18 and S29 data cannot be split into independent training and material holdout',()=>{
 const related=seed.records.filter(r=>['S18','S29'].includes(r.source_id));
 assert.equal(provenanceComponents(related).length,1);
 assert.throws(()=>groupedHoldout(related,['S29-SWW-table-feed-01-R1']),/independent_train_and_test/);
 const mixed=seed.records.filter(r=>['S17','S18','S29'].includes(r.source_id));
 const split=groupedHoldout(mixed,['S29-SWW-table-feed-01-R1']);
 assert.ok(split.test.some(r=>r.source_id==='S18'));
 assert.ok(split.train.every(r=>r.source_id==='S17'));
 assert.ok(split.test.every(r=>['S18','S29'].includes(r.source_id)));
});

test('commercial snapshots and missing cells remain outside training and predictive error claims',()=>{
 assert.equal(seed.report.training_eligible_records,0);
 assert.equal(seed.report.experimental_error_metrics,null);
 assert.equal(seed.report.missing_observation_cells,4);
 const records=seed.records.filter(r=>['commercial_offer_snapshot','supplier_or_manufacturer_specification'].includes(r.experimental_scope));
 assert.equal(records.length,47);
 assert.ok(records.every(r=>r.training_eligible===false));
 const seen=new Set(seed.records.map(r=>r.id));assert.equal(seen.size,seed.records.length);
});
