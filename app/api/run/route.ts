import { database,digest,failure,identity,json,payload,sameOrigin } from '../../../lib/server';
import { MODEL_VERSION,solve,simulateBatch,validateConfig } from '../../../science/mfc-engine.mjs';
export const dynamic='force-dynamic';
export async function POST(request:Request) {
  const user=await identity();if(!user)return json({error:'Autenticação necessária'},401);
  if(!sameOrigin(request))return json({error:'Origem inválida'},403);
  try {
    const {config}=await payload(request),check=validateConfig(config);
    if(!check.valid)return json({error:'Configuração inválida',issues:check.issues},400);
    const result={operating:solve(config),batch:simulateBatch(config)};
    const db=database(),id=crypto.randomUUID(),serialized=JSON.stringify(config);
    const seed=await db.prepare('SELECT id FROM seed_versions ORDER BY applied_at DESC LIMIT 1').first<{id:string}>();
    await db.prepare('INSERT INTO model_runs(id,user_id,config_json,config_sha256,result_json,engine_version,seed_version,created_at) VALUES(?,?,?,?,?,?,?,?)').bind(id,user.userId,serialized,await digest(serialized),JSON.stringify(result),MODEL_VERSION,seed?.id||'not_seeded',new Date().toISOString()).run();
    return json({id,result});
  }catch(e){return failure(e);}
}
