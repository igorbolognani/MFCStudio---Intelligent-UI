import { database,bucket,failure,identity,json } from '../../../../lib/server';
export const dynamic='force-dynamic';
export async function GET(request:Request,{params}:{params:Promise<{id:string}>}) {
  if(!await identity())return json({error:'Autenticação necessária'},401);
  try {
    const {id}=await params,db=database(),doc=await db.prepare('SELECT * FROM documents WHERE id=?').bind(id).first();
    if(!doc)return json({error:'Documento não encontrado'},404);
    if(new URL(request.url).searchParams.get('download')==='1'&&doc.object_key) {
      const object=await bucket().get(doc.object_key as string);
      if(!object)return json({error:'Arquivo não disponível'},404);
      return new Response(object.body,{headers:{'Content-Type':'application/gzip','Content-Disposition':`attachment; filename="${id}.gz"`,'Cache-Control':'private,no-store'}});
    }
    const chunks=await db.prepare('SELECT ordinal,text,sha256 FROM document_chunks WHERE document_id=? ORDER BY ordinal').bind(id).all();
    return json({document:doc,chunks:chunks.results,text:chunks.results.map(x=>x.text).join('')});
  }catch(e){return failure(e);}
}
