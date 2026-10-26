import { database,failure,identity,json } from '../../../lib/server';
export const dynamic='force-dynamic';
export async function GET(request:Request) {
  if(!await identity())return json({error:'Autenticação necessária'},401);
  try {
    const db=database(),url=new URL(request.url),stage=url.searchParams.get('stage'),q=url.searchParams.get('q')?.trim().slice(0,150);
    const sources=await db.prepare(stage?'SELECT s.* FROM sources s JOIN source_stages j ON j.source_id=s.id WHERE j.stage_id=? ORDER BY s.id':'SELECT * FROM sources ORDER BY id').bind(...(stage?[stage]:[])).all();
    const docs=await db.prepare('SELECT id,source_id,title,sha256,license,format,complete,text_length FROM documents ORDER BY id').all();
    const records=await db.prepare(stage?'SELECT e.* FROM evidence_records e JOIN source_stages j ON j.source_id=e.source_id WHERE j.stage_id=? ORDER BY e.id':'SELECT * FROM evidence_records ORDER BY id').bind(...(stage?[stage]:[])).all();
    const coverage=await db.prepare('SELECT st.id,st.ordinal,st.name,COUNT(DISTINCT j.source_id) AS source_count,COUNT(DISTINCT d.id) AS document_count FROM stages st LEFT JOIN source_stages j ON j.stage_id=st.id LEFT JOIN documents d ON d.source_id=j.source_id GROUP BY st.id ORDER BY st.ordinal').all();
    const matches=q?await db.prepare('SELECT document_id,ordinal,text FROM document_chunks WHERE instr(lower(text),lower(?))>0 LIMIT 20').bind(q).all():null;
    const seeds=await db.prepare('SELECT * FROM seed_versions ORDER BY applied_at DESC LIMIT 1').first();
    return json({sources:sources.results.map(x=>({...x,metadata:JSON.parse(x.metadata_json as string)})),documents:docs.results,records:records.results.map(x=>JSON.parse(x.data_json as string)),coverage:coverage.results,matches:matches?.results||[],seed:seeds?{...seeds,report:JSON.parse(seeds.report_json as string)}:null});
  }catch(e){return failure(e);}
}
