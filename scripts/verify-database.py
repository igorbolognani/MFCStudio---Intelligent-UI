"""Read-only audit of a seeded local D1 SQLite file; emits a reproducible report."""
from pathlib import Path
import sqlite3,json,hashlib
r=Path(__file__).resolve().parents[1];seed=json.loads((r/'science/corpus-seed.json').read_text())
paths=list((r/'.wrangler/state').rglob('*.sqlite'));c=None
for p in paths:
 db=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True)
 if db.execute("SELECT name FROM sqlite_master WHERE name='evidence_records'").fetchone():c=db;break
assert c is not None,'local D1 not seeded'
counts={t:c.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['stages','properties','sources','source_stages','documents','document_chunks','experiments','evidence_records','observations','curves','curve_points']}
assert counts['stages']==11 and counts['properties']==110 and counts['sources']==seed['report']['sources']
assert counts['evidence_records']==seed['report']['records'] and counts['observations']==seed['report']['observations'] and counts['curve_points']==13
assert not list(c.execute('PRAGMA foreign_key_check'))
assert c.execute('SELECT COUNT(*) FROM evidence_records WHERE training_eligible=1').fetchone()[0]==0
for d in seed['documents']:
 chunks=c.execute('SELECT text FROM document_chunks WHERE document_id=? ORDER BY ordinal',(d['id'],)).fetchall();text=''.join(x[0] for x in chunks)
 assert text==d['text'] and hashlib.sha256(text.encode()).hexdigest()==d['sha256'],d['id']
assert c.execute('SELECT content_sha256 FROM seed_versions WHERE id=?',(seed['version'],)).fetchone()[0]==seed['content_sha256']
assert c.execute('SELECT COUNT(*) FROM observations WHERE value IS NULL').fetchone()[0]==seed['report']['missing_observation_cells']
group=json.loads(c.execute('SELECT conditions_json FROM experiments WHERE id=?',('Salvian2024-Surrey-30mL',)).fetchone()[0])
assert set(group['source_ids'])=={'S18','S29'}
assert len([rid for rid in group['record_ids'] if rid.startswith('S29-')])==118
report={'audit':'local_D1_real_database','counts':counts,'foreign_key_violations':0,'complete_text_reconstruction_verified':len(seed['documents']),'training_eligible_records':0,'missing_observation_cells':seed['report']['missing_observation_cells'],'related_S18_S29_family_verified':True,'seed_sha256':seed['content_sha256'],'experimental_predictive_validation':False}
(r/'docs/database-local-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
