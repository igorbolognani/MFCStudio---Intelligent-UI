import {rawAssets} from '../../../../lib/corpus';
import {bucket,failure,identity,json,sameOrigin} from '../../../../lib/server';
export const dynamic='force-dynamic';
export async function PUT(request:Request,{params}:{params:Promise<{id:string}>}){
 if(!sameOrigin(request))return json({error:'Origem inválida'},403);
 try{
  const {id}=await params,asset=rawAssets.find(a=>a.id===id);if(!asset)return json({error:'Documento fora do corpus'},404);
  const stored=await bucket().head(asset.object_key);if(stored?.customMetadata?.sha256===asset.sha256)return json({id,alreadyStored:true});
  const size=Number(request.headers.get('content-length'));if(size&&size!==asset.size_bytes)return json({error:'Tamanho incorreto'},400);
  const bytes=await request.arrayBuffer();if(bytes.byteLength!==asset.size_bytes)return json({error:'Tamanho incorreto'},400);
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');
  if(hash!==asset.sha256)return json({error:'Hash incorreto'},400);
  await bucket().put(asset.object_key,bytes,{httpMetadata:{contentType:'application/pdf'},customMetadata:{sha256:hash,license:asset.license}});
  return json({id,sha256:hash,stored:true});
 }catch(e){return failure(e);}
}
export async function GET(_request:Request,{params}:{params:Promise<{id:string}>}){
 if(!await identity())return json({error:'Autenticação necessária'},401);
 try{const {id}=await params,asset=rawAssets.find(a=>a.id===id);if(!asset)return json({error:'Documento não encontrado'},404);const object=await bucket().get(asset.object_key);if(!object)return json({error:'PDF ainda não armazenado'},404);return new Response(object.body,{headers:{'Content-Type':'application/pdf','Content-Disposition':`inline; filename="${id}.pdf"`,'Cache-Control':'private,no-store'}});}catch(e){return failure(e);}
}
