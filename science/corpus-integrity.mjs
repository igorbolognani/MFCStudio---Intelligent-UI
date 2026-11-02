/** Read back complete database values; return hashes and counts, never truncated source text. */
const sha = async text => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),x=>x.toString(16).padStart(2,'0')).join('');
export async function verifyCorpusDatabase(db, corpus) {
  const mismatches=[];
  const records=(await db.prepare('SELECT id,source_id,study_id,leakage_group_id,training_eligible,data_json FROM evidence_records').all()).results;
  const byId=new Map(records.map(r=>[r.id,r]));
  for(const expected of corpus.records){
    const actual=byId.get(expected.id);
    if(!actual || actual.data_json!==JSON.stringify(expected) || actual.training_eligible!==0 || actual.source_id!==expected.source_id || actual.study_id!==expected.study_id || actual.leakage_group_id!==expected.leakage_group_id)mismatches.push('record:'+expected.id);
  }
  const observations=(await db.prepare('SELECT id,record_id,metric,value,unit,kind,metadata_json FROM observations').all()).results;
  const observationMap=new Map(observations.map(o=>[o.id,o]));let expectedObservations=0;
  for(const record of corpus.records)for(const [i,expected] of (record.observations||[]).entries()){
    expectedObservations++;const id=record.id+':'+i,actual=observationMap.get(id);
    if(!actual || actual.record_id!==record.id || actual.metric!==expected.metric || actual.value!==(expected.value??null) || actual.unit!==expected.unit || actual.kind!==expected.kind || actual.metadata_json!==JSON.stringify(expected))mismatches.push('observation:'+id);
  }
  const sources=(await db.prepare('SELECT id,access,metadata_json FROM sources').all()).results;
  const sourceMap=new Map(sources.map(s=>[s.id,s]));
  for(const expected of corpus.sources){const actual=sourceMap.get(expected.id);if(!actual || actual.metadata_json!==JSON.stringify(expected) || actual.access!==(expected.access||'metadata'))mismatches.push('source:'+expected.id);}
  const documents=[];
  for(const expected of corpus.documents){
    const row=await db.prepare('SELECT source_id,sha256,raw_sha256,complete,metadata_json FROM documents WHERE id=?').bind(expected.id).first();
    if(!row || row.source_id!==expected.source_id || row.sha256!==expected.sha256 || row.raw_sha256!==expected.raw_sha256 || row.complete!==1 || row.metadata_json!==JSON.stringify(expected.metadata))mismatches.push('document_metadata:'+expected.id);
    const chunks=(await db.prepare('SELECT ordinal,text,sha256 FROM document_chunks WHERE document_id=? ORDER BY ordinal').bind(expected.id).all()).results;
    let valid=true;
    for(const [i,chunk] of chunks.entries())if(chunk.ordinal!==i || await sha(chunk.text)!==chunk.sha256)valid=false;
    const actualHash=await sha(chunks.map(c=>c.text).join(''));
    if(actualHash!==expected.sha256 || !valid)mismatches.push('document:'+expected.id);
    documents.push({id:expected.id,chunks:chunks.length,sha256:actualHash,matches:actualHash===expected.sha256&&valid});
  }
  if(records.length!==corpus.records.length)mismatches.push('record_count');
  if(observations.length!==expectedObservations)mismatches.push('observation_count');
  if(sources.length!==corpus.sources.length)mismatches.push('source_count');
  return {complete:!mismatches.length,mismatches,records_verified:corpus.records.length,observations_verified:expectedObservations,sources_verified:corpus.sources.length,documents,
    stage_attribution_revisions:corpus.record_revisions?.map(r=>({id:r.id,matches:!mismatches.includes('record:'+r.id)}))||[],
    limitation:'Hashes verify stored bytes against the bundled corpus; they do not demonstrate predictive validation.'};
}
