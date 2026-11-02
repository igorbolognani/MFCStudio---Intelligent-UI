import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {verifyCorpusDatabase} from '../science/corpus-integrity.mjs';
const corpus=JSON.parse(readFileSync(new URL('../science/corpus-seed.json',import.meta.url),'utf8'));
function fixture(){
 const sqlite=new DatabaseSync(':memory:');
 sqlite.exec('CREATE TABLE evidence_records(id TEXT PRIMARY KEY,source_id TEXT,study_id TEXT,leakage_group_id TEXT,training_eligible INTEGER,data_json TEXT); CREATE TABLE observations(id TEXT PRIMARY KEY,record_id TEXT,metric TEXT,value REAL,unit TEXT,kind TEXT,metadata_json TEXT); CREATE TABLE sources(id TEXT PRIMARY KEY,access TEXT,metadata_json TEXT); CREATE TABLE documents(id TEXT PRIMARY KEY,source_id TEXT,sha256 TEXT,raw_sha256 TEXT,complete INTEGER,metadata_json TEXT); CREATE TABLE document_chunks(document_id TEXT,ordinal INTEGER,text TEXT,sha256 TEXT);');
 for(const r of corpus.records){sqlite.prepare('INSERT INTO evidence_records VALUES (?,?,?,?,0,?)').run(r.id,r.source_id,r.study_id,r.leakage_group_id,JSON.stringify(r));for(const [i,o] of (r.observations||[]).entries())sqlite.prepare('INSERT INTO observations VALUES (?,?,?,?,?,?,?)').run(r.id+':'+i,r.id,o.metric,o.value??null,o.unit,o.kind,JSON.stringify(o));}
 for(const s of corpus.sources)sqlite.prepare('INSERT INTO sources VALUES (?,?,?)').run(s.id,s.access||'metadata',JSON.stringify(s));
 for(const d of corpus.documents){sqlite.prepare('INSERT INTO documents VALUES (?,?,?,?,1,?)').run(d.id,d.source_id,d.sha256,d.raw_sha256,JSON.stringify(d.metadata));for(let p=0,n=0;p<d.text.length;p+=10000,n++){const text=d.text.slice(p,p+10000);sqlite.prepare('INSERT INTO document_chunks VALUES (?,?,?,?)').run(d.id,n,text,createHash('sha256').update(text).digest('hex'));}}
 const db={prepare(sql){const statement=args=>({async all(){return {results:sqlite.prepare(sql).all(...args)};},async first(){return sqlite.prepare(sql).get(...args)||null;}});return {...statement([]),bind(...args){return statement(args);}};}};
 return {sqlite,db};
}
test('full database readback reconstructs every document and all observations including missing cells',async()=>{
 const {sqlite,db}=fixture();try{const report=await verifyCorpusDatabase(db,corpus);assert.equal(report.complete,true);assert.equal(report.observations_verified,427);assert.ok(report.documents.every(d=>d.matches));assert.equal(report.documents.length,8);assert.equal(report.stage_attribution_revisions.length,8);}finally{sqlite.close();}
});
test('long-text truncation, observation corruption and source metadata drift are detected',async()=>{
 const {sqlite,db}=fixture();try{
  sqlite.exec("UPDATE document_chunks SET text=substr(text,1,2035) WHERE document_id='S18-fulltext' AND ordinal=0; UPDATE observations SET value=999 WHERE id='S01-E1:0'; UPDATE sources SET access='wrong' WHERE id='S02';");
  const report=await verifyCorpusDatabase(db,corpus);assert.equal(report.complete,false);
  for(const id of ['document:S18-fulltext','observation:S01-E1:0','source:S02'])assert.ok(report.mismatches.includes(id),id);
 }finally{sqlite.close();}
});
