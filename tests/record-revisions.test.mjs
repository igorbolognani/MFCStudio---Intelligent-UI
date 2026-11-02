import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {applyRecordRevisions,validateRecordRevision,applySourceRevisions} from '../science/record-revisions.mjs';
const corpus=JSON.parse(readFileSync(new URL('../science/corpus-seed.json',import.meta.url),'utf8'));
function fixture({fresh=false}={}){
 const sqlite=new DatabaseSync(':memory:');
 sqlite.exec('CREATE TABLE evidence_records(id TEXT PRIMARY KEY,training_eligible INTEGER NOT NULL,data_json TEXT NOT NULL); CREATE TABLE scenarios(id TEXT PRIMARY KEY, config_json TEXT); INSERT INTO scenarios VALUES (\'private\',\'{"volume":42}\');');
 for(const revision of corpus.record_revisions){const record=fresh?corpus.records.find(r=>r.id===revision.id):revision.previous;sqlite.prepare('INSERT INTO evidence_records VALUES (?,0,?)').run(record.id,JSON.stringify(record));}
 const db={prepare(sql){return {bind(...args){return {async run(){return sqlite.prepare(sql).run(...args);},async first(){return sqlite.prepare(sql).get(...args)||null;}};}};}};
 return {db,sqlite};
}
test('existing corpus records receive all eight reviewed attributions and repeat safely',async()=>{
 const {db,sqlite}=fixture();try{
  assert.equal((await applyRecordRevisions(db,corpus)).verified,8);
  const once=sqlite.prepare('SELECT * FROM evidence_records ORDER BY id').all();
  await applyRecordRevisions(db,corpus);
  assert.deepEqual(sqlite.prepare('SELECT * FROM evidence_records ORDER BY id').all(),once);
  for(const row of once){const record=JSON.parse(row.data_json);assert.ok(record.stage_ids.length);assert.equal(row.training_eligible,0);}
  assert.equal(sqlite.prepare('SELECT config_json FROM scenarios').get().config_json,'{"volume":42}');
 }finally{sqlite.close();}
});
test('freshly inserted reviewed records need no preceding corpus',async()=>{
 const {db,sqlite}=fixture({fresh:true});try{assert.equal((await applyRecordRevisions(db,corpus)).verified,8);}finally{sqlite.close();}
});
test('independently edited record survives a conflicting revision',async()=>{
 const {db,sqlite}=fixture();try{
  const id=corpus.record_revisions[0].id;
  sqlite.prepare('UPDATE evidence_records SET data_json=? WHERE id=?').run('{"manual_review":"retain"}',id);
  await assert.rejects(applyRecordRevisions(db,corpus),/Conflicting evidence revision/);
  assert.equal(sqlite.prepare('SELECT data_json FROM evidence_records WHERE id=?').get(id).data_json,'{"manual_review":"retain"}');
 }finally{sqlite.close();}
});
test('stage revision cannot modify observations or enable training',()=>{
 const previous=corpus.record_revisions[0].previous,desired=structuredClone(corpus.records.find(r=>r.id===previous.id));
 desired.observations[0].value+=1;assert.throws(()=>validateRecordRevision(previous,desired),/scientific data/);
 desired.training_eligible=true;assert.throws(()=>validateRecordRevision(previous,desired),/training eligibility/);
});
test('interrupted application resumes from the records already revised',async()=>{
 const {db,sqlite}=fixture();try{
  await applyRecordRevisions(db,{...corpus,record_revisions:corpus.record_revisions.slice(0,3)});
  assert.equal((await applyRecordRevisions(db,corpus)).verified,8);
 }finally{sqlite.close();}
});
test('source acquisition metadata updates idempotently and refuses divergent edits',async()=>{
 const {db,sqlite}=fixture();try{
  sqlite.exec('CREATE TABLE sources(id TEXT PRIMARY KEY,access TEXT,metadata_json TEXT)');
  const revision=corpus.source_revisions[0];
  sqlite.prepare('INSERT INTO sources VALUES (?,?,?)').run(revision.id,revision.previous.access,JSON.stringify(revision.previous));
  assert.equal((await applySourceRevisions(db,corpus)).verified,1);
  assert.equal((await applySourceRevisions(db,corpus)).verified,1);
  sqlite.prepare('UPDATE sources SET metadata_json=? WHERE id=?').run('{"manual":"retain"}',revision.id);
  await assert.rejects(applySourceRevisions(db,corpus),/Conflicting source revision/);
  assert.equal(sqlite.prepare('SELECT metadata_json FROM sources').get().metadata_json,'{"manual":"retain"}');
 }finally{sqlite.close();}
});
