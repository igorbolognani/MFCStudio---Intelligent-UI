import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {auditCorpus} from '../scripts/audit-corpus.mjs';
const seed=JSON.parse(readFileSync(new URL('../science/corpus-seed.json',import.meta.url),'utf8'));
test('real corpus audit preserves missing cells and does not infer stage mappings',()=>{
 const before=JSON.stringify(seed),a=auditCorpus(seed);
 assert.deepEqual(a.errors,[]);assert.equal(a.numeric_cells,393);assert.equal(a.missing_cells,4);
 assert.equal(a.coverage.length,11);assert.equal(a.training_eligible_records,0);
 assert.equal(JSON.stringify(seed),before);assert.deepEqual(a,auditCorpus(seed));
});
test('corrupt documents, orphan sources, duplicate ids and nonfinite values fail audit',()=>{
 const s=structuredClone(seed);s.documents[0].text+='corruption';s.records[0].source_id='unknown';s.records[1].id=s.records[0].id;s.records[0].observations[0].value=Infinity;
 const a=auditCorpus(s);assert.equal(a.status,'failed');
 for(const term of ['hash mismatch','Unknown source','duplicate','Invalid numeric'])assert.ok(a.errors.some(x=>x.includes(term)));
});
