/** Apply reviewed stage metadata only; experimental observations remain immutable. */
export function validateRecordRevision(previous, desired) {
  if (!previous || !desired || previous.id !== desired.id || !previous.id) throw new Error('Revision identity mismatch');
  if (previous.training_eligible !== false || desired.training_eligible !== false) throw new Error('Revision cannot grant training eligibility');
  if (!Array.isArray(desired.stage_ids) || !desired.stage_ids.length || !desired.stage_attribution_review) throw new Error('Reviewed stage attribution required');
  const {stage_ids, stage_attribution_review, ...originalScience} = desired;
  if (JSON.stringify(originalScience) !== JSON.stringify(previous)) throw new Error('Scope revision cannot change scientific data');
  if (stage_attribution_review.record_id !== desired.id || JSON.stringify(stage_attribution_review.stage_ids) !== JSON.stringify(stage_ids)) throw new Error('Stage review does not match record');
}

export async function applyRecordRevisions(db, corpus) {
  let verified = 0;
  const seen = new Set();
  for (const revision of corpus.record_revisions || []) {
    if (seen.has(revision.id)) throw new Error('Duplicate record revision');
    seen.add(revision.id);
    const desired = corpus.records.find(r => r.id === revision.id);
    validateRecordRevision(revision.previous, desired);
    const target = JSON.stringify(desired), prior = JSON.stringify(revision.previous);
    await db.prepare('UPDATE evidence_records SET data_json=? WHERE id=? AND data_json=? AND training_eligible=0').bind(target, revision.id, prior).run();
    const stored = await db.prepare('SELECT data_json,training_eligible FROM evidence_records WHERE id=?').bind(revision.id).first();
    if (stored?.data_json !== target || stored.training_eligible !== 0) throw new Error('Conflicting evidence revision: ' + revision.id);
    verified++;
  }
  return {verified};
}

export async function applySourceRevisions(db, corpus) {
  const seen = new Set();
  for (const revision of corpus.source_revisions || []) {
    const desired = corpus.sources.find(s => s.id === revision.id), previous = revision.previous;
    if (!desired || !previous || seen.has(revision.id)) throw new Error('Invalid source revision');
    seen.add(revision.id);
    for (const key of ['id','doi','url','type']) {
      if (desired[key] !== previous[key]) throw new Error('Source revision cannot change identity');
    }
    const target = JSON.stringify(desired);
    await db.prepare('UPDATE sources SET access=?,metadata_json=? WHERE id=? AND metadata_json=?').bind(desired.access,target,revision.id,JSON.stringify(previous)).run();
    const stored = await db.prepare('SELECT access,metadata_json FROM sources WHERE id=?').bind(revision.id).first();
    if (stored?.metadata_json !== target || stored.access !== desired.access) throw new Error('Conflicting source revision: ' + revision.id);
  }
  return {verified:seen.size};
}
