import { env } from 'cloudflare:workers';
import { getChatGPTUser } from '../app/chatgpt-auth';

export function database(): D1Database {
  if(!env.DB) throw new Error('Banco indisponível. A publicação deve aplicar as migrações D1.');
  return env.DB;
}
export function bucket(): R2Bucket {
  if(!env.BUCKET) throw new Error('Arquivo de documentos indisponível.');
  return env.BUCKET;
}
export async function identity() { return await getChatGPTUser(); }
export function sameOrigin(request:Request) {
  const origin=request.headers.get('origin');
  return !origin || origin===new URL(request.url).origin;
}
export async function digest(value:string) {
  const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value));
  return Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,'0')).join('');
}
export function json(value:unknown,status=200) {
  return Response.json(value,{status,headers:{'Cache-Control':'no-store'}});
}
export async function payload(request:Request) {
  const text=await request.text();
  if(text.length>150000)throw new Error('Conteúdo acima do limite.');
  return JSON.parse(text);
}
export function failure(error:unknown) {
  console.error(error);
  return json({error:'Não foi possível concluir a operação. Os dados existentes foram preservados.'},500);
}
