import { database, digest, failure, identity, json, payload, sameOrigin } from '../../../lib/server';
import { MODEL_VERSION, validateConfig } from '../../../science/mfc-engine.mjs';
export const dynamic='force-dynamic';
export async function GET(request:Request) {
  const user=await identity();if(!user)return json({error:'Autenticação necessária'},401);
  try {
    const db=database(),id=new URL(request.url).searchParams.get('id');
    if(id) {
      const scenario=await db.prepare('SELECT * FROM scenarios WHERE id=? AND user_id=?').bind(id,user.userId).first();
      if(!scenario)return json({error:'Cenário não encontrado'},404);
      const versions=await db.prepare('SELECT * FROM scenario_versions WHERE scenario_id=? ORDER BY version DESC').bind(id).all();
      return json({scenario,versions:versions.results.map(v=>({...v,config:JSON.parse(v.config_json as string)}))});
    }
    const result=await db.prepare('SELECT s.*,v.config_json FROM scenarios s JOIN scenario_versions v ON v.scenario_id=s.id AND v.version=s.current_version WHERE s.user_id=? ORDER BY s.updated_at DESC LIMIT 100').bind(user.userId).all();
    return json({scenarios:result.results.map(r=>({...r,config:JSON.parse(r.config_json as string)}))});
  }catch(e){return failure(e);}
}
export async function POST(request:Request) {
  const user=await identity();if(!user)return json({error:'Autenticação necessária'},401);
  if(!sameOrigin(request))return json({error:'Origem inválida'},403);
  try {
    const data=await payload(request),check=validateConfig(data.config);
    if(!check.valid)return json({error:'Configuração inválida',issues:check.issues},400);
    const name=typeof data.name==='string'?data.name.trim().slice(0,120):'';
    if(!name)return json({error:'Informe o nome'},400);
    const db=database(),serialized=JSON.stringify(data.config),hash=await digest(serialized),now=new Date().toISOString();
    if(data.id) {
      if(typeof data.id!=='string'||!Number.isInteger(data.expectedVersion)||data.expectedVersion<1)return json({error:'Versão de origem necessária'},400);
      const owned=await db.prepare('SELECT id,current_version FROM scenarios WHERE id=? AND user_id=?').bind(data.id,user.userId).first();
      if(!owned)return json({error:'Cenário não encontrado'},404);
      if(owned.current_version!==data.expectedVersion)return json({error:'Este cenário recebeu outra versão. Recarregue antes de salvar.'},409);
      const version=data.expectedVersion+1;
      const results=await db.batch([
        db.prepare('INSERT INTO scenario_versions(id,scenario_id,version,config_json,config_sha256,engine_version,created_at) SELECT ?,id,?,?,?,?,? FROM scenarios WHERE id=? AND user_id=? AND current_version=?').bind(crypto.randomUUID(),version,serialized,hash,MODEL_VERSION,now,data.id,user.userId,data.expectedVersion),
        db.prepare('UPDATE scenarios SET current_version=?,name=?,updated_at=? WHERE id=? AND user_id=? AND current_version=?').bind(version,name,now,data.id,user.userId,data.expectedVersion),
      ]);
      if(results[0].meta.changes!==1)return json({error:'Conflito de versão'},409);
      return json({id:data.id,version,configSha256:hash});
    }
    const id=crypto.randomUUID();await db.batch([
      db.prepare('INSERT INTO scenarios(id,user_id,name,current_version,updated_at) VALUES(?,?,?,1,?)').bind(id,user.userId,name,now),
      db.prepare('INSERT INTO scenario_versions(id,scenario_id,version,config_json,config_sha256,engine_version,created_at) VALUES(?,?,1,?,?,?,?)').bind(crypto.randomUUID(),id,serialized,hash,MODEL_VERSION,now),
    ]);
    return json({id,version:1,configSha256:hash},201);
  }catch(e){return failure(e);}
}
