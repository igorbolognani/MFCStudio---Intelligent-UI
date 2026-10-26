import unittest,json,hashlib,math
from pathlib import Path
R=Path(__file__).parent
class ResearchIntegrityTests(unittest.TestCase):
 def test_stage_order(self):
  s=json.loads((R/'stage_evidence_map.json').read_text())
  self.assertEqual([a['stage_id'] for a in s],['anode_chamber','anolyte','anode','anode_catalyst','biofilm','membrane','external_circuit','cathode_chamber','catholyte','cathode','cathode_catalyst'])
 def test_hashes_and_files(self):
  for a in json.loads((R/'documents_manifest.json').read_text()):
   f=R/a['path'];self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),a['sha256']);self.assertEqual(f.stat().st_size,a['size_bytes'])
 def test_license_and_doi(self):
  for a in json.loads((R/'documents_manifest.json').read_text()):
   self.assertEqual(a['license'],'CC-BY-4.0');self.assertTrue(a['license_verified']);self.assertTrue(a['attribution_doi'].startswith('10.'))
 def test_pdf_is_pdf(self):
  for f in (R/'documents').rglob('*.pdf'):
   self.assertTrue(f.read_bytes().startswith(b'%PDF'),f.name)
 def test_fulltexts_not_empty(self):
  for f in (R/'fulltext').glob('*.txt'):self.assertGreater(f.stat().st_size,10000)
 def test_records_retain_provenance_and_scope(self):
  sources={s['id'] for s in json.loads((R/'index_sources.json').read_text())}
  for a in json.loads((R/'observations.json').read_text()):
   self.assertIn(a['source_id'],sources);self.assertTrue(a['leakage_group_id']);self.assertTrue(a['source_locator']);self.assertFalse(a['training_eligible'])
   for o in a['observations']:self.assertTrue(o['unit']);self.assertTrue(o['locator']);self.assertTrue(math.isfinite(o['value']))
 def test_related_cathodes_share_group(self):
  r=[a for a in json.loads((R/'observations.json').read_text()) if a['source_id']=='S18'];self.assertEqual(len({a['leakage_group_id'] for a in r}),1)
 def test_curve_is_not_independent_or_raw(self):
  c=json.loads((R/'S18_CC_curve_digitized.json').read_text());self.assertFalse(c['raw_experimental_data']);self.assertFalse(c['training_eligible']);self.assertIsNone(c['area_m2']);self.assertGreater(len(c['points']),8)
if __name__=='__main__':unittest.main()
