import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url);
test('every complete document links to an allowlisted intact original PDF, including the supplement',()=>{
 const seed=JSON.parse(readFileSync(new URL('science/corpus-seed.json',root),'utf8'));
 const assets=JSON.parse(readFileSync(new URL('science/corpus-pdf-assets.json',root),'utf8'));
 assert.equal(new Set(assets.map(a=>a.id)).size,assets.length);
 for(const doc of seed.documents){
  const a=assets.find(a=>a.id===doc.metadata.pdf_asset_id);assert.ok(a,doc.id+' has no downloadable PDF');
  const bytes=readFileSync(new URL(a.path,root));
  assert.equal(bytes.subarray(0,5).toString(),'%PDF-');
  assert.equal(bytes.length,a.size_bytes);assert.equal(createHash('sha256').update(bytes).digest('hex'),a.sha256);
 }
});
