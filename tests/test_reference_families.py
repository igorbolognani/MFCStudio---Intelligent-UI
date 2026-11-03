import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('references', ROOT / 'scripts/audit-reference-families.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ReferenceFamiliesTests(unittest.TestCase):
    def test_real_tables_and_unit_dispersion_preserved_without_calibration(self):
        a = audit.build()
        self.assertEqual(a, audit.build())
        o = next(x for x in a['reference_results'] if x['id'] == 'RF02-UNM-cycle6-Pmax')
        self.assertAlmostEqual(o['normalized']['value'], .61)
        self.assertAlmostEqual(o['normalized']['plus_minus'], .18)
        self.assertIn('not_SD_or_SE', o['normalized']['uncertainty_type'])
        self.assertFalse(o['training_eligible'])
        self.assertFalse(o['normalized']['absolute_power_inferred'])
        # Published small baseline values remain small; no factor-of-1000 repair.
        p = next(x for x in a['reference_results'] if x['id'] == 'RF08-A-cycle1-Pmax')
        self.assertAlmostEqual(p['normalized']['value'], .0000082)

    def test_reseeded_phases_cannot_enter_the_reviewed_reference_results(self):
        data = json.loads((audit.FOLDER / 'catalog.json').read_text())
        changed = copy.deepcopy(data)
        changed['reported_reference_results'][0]['lab'] = 'RSE'
        with self.assertRaisesRegex(ValueError, 'post-reseeding'):
            audit.build(changed)

    def test_unknowns_and_different_commercial_grades_do_not_establish_equivalence(self):
        self.assertFalse(audit.compare_known({'grade': None}, {'grade': None})['same_configuration_demonstrated'])
        self.assertFalse(audit.compare_known({'grade': 'G200'}, {'grade': 'G650A'})['same_configuration_demonstrated'])
        self.assertIn('medium', audit.compare_known({'grade': 'G200', 'medium': 'PBS'}, {'grade': 'G200'})['unresolved'])
        self.assertFalse(audit.compare_known({'test': {'pressure': None}}, {'test': {'pressure': None}})['same_configuration_demonstrated'])
        self.assertTrue(audit.compare_known({'added_catalyst': False, 'load': 0}, {'added_catalyst': False, 'load': 0})['same_configuration_demonstrated'])

    def test_changed_document_rejected_before_any_scientific_extraction(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'source.xml'
            path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'version/hash mismatch'):
                audit.verify_bytes(path, {'id': 'source', 'bytes': 7, 'sha256': '0' * 64})


if __name__ == '__main__':
    unittest.main()
