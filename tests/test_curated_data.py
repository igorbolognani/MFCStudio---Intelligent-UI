from pathlib import Path
import json,hashlib,importlib.util
import unittest
ROOT=Path(__file__).resolve().parents[1]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class CuratedDataTests(unittest.TestCase):
    def test_material_provenance_references_and_treatment_separation(self):
        d=json.loads((ROOT/'research/materials-v0.1/catalog.json').read_text());ids={m['id'] for m in d['materials']};sources={s['id'] for s in d['sources']}
        self.assertEqual(len(ids),16);self.assertEqual(len(d['stage_acquisition_plan']),11)
        for o in d['property_observations']:
            self.assertIn(o['material_id'],ids);self.assertIn(o['source_id'],sources);self.assertTrue(o['locator'])
        for o in d['offer_snapshots']:
            self.assertIn(o['material_id'],ids);self.assertIn(o['source_id'],sources)
        self.assertTrue(all(not m['parameter_bindings'] for m in d['materials']))
        treated=next(m for m in d['materials'] if m['id']=='toray-tgp-h060-fcs-ptfe5')
        self.assertFalse(treated['base_property_transfer_admitted'])
        for link in d['experimental_links']:self.assertFalse(link['exact_final_electrode_match'])

    def test_material_processing_is_deterministic_and_blocks_ambiguous_units(self):
        m=module('build_materials','scripts/build-materials.py');a=m.build();self.assertEqual(a,m.build())
        self.assertEqual(a['report']['blocked_property_normalizations'],2)
        self.assertEqual(a['report']['confirmed_delivered_quotes'],0)
        self.assertTrue(all(not o['binding_review']['eligible_for_binding'] for o in a['property_observations']))
        self.assertTrue(all(not r['training_eligible'] for r in a['records']))
        self.assertEqual(a,json.loads((ROOT/'science/materials-processed.json').read_text()))

    def test_s29_all_cells_align_with_raw_rows_missingness_and_source_family(self):
        result=module('audit_s29','scripts/audit-s29.py').audit()
        self.assertEqual(result['response_pairs'],115);self.assertEqual(result['missing_response_pairs'],2)
        self.assertEqual(result['by_medium']['SWW']['measured_pairs'],62)
        self.assertEqual(result['by_medium']['RWW']['measured_pairs'],53)
        self.assertEqual(result['by_medium']['SWW']['peak_current_density_range_mA_m2'],[44,261])
        self.assertEqual(result['by_medium']['RWW']['peak_current_density_range_mA_m2'],[1,115])
        self.assertFalse(result['current_kernel_calibration_ready']);self.assertIsNone(result['experimental_error_metrics'])
        rows=json.loads((ROOT/'research/corpus-v0.3/S29_observations.json').read_text())
        missing=[r['id'] for r in rows if r['observations'][0]['value'] is None]
        self.assertEqual(set(missing),{'S29-SWW-table-feed-02-R2','S29-RWW-table-feed-14-R3'})

    def test_s29_original_pdf_and_extracted_artifact_hashes(self):
        base=ROOT/'research/corpus-v0.3'
        for row in json.loads((base/'documents_manifest.json').read_text()):
            payload=(base/row['path']).read_bytes();self.assertEqual(len(payload),row['size_bytes'])
            self.assertEqual(hashlib.sha256(payload).hexdigest(),row['sha256'])
            self.assertEqual(row['license'],'CC-BY-4.0')
            if row['path'].endswith('.pdf'):self.assertTrue(payload.startswith(b'%PDF-'))


if __name__=='__main__':unittest.main()
