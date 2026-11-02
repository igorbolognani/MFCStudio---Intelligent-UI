from pathlib import Path
import copy,importlib.util,json,math,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class S02CurationTests(unittest.TestCase):
    def test_reviewed_transcription_has_localizers_and_separate_derived_values(self):
        builder=module('s02','scripts/build-s02.py');a=builder.build()
        self.assertEqual(a,builder.build());self.assertEqual(a,json.loads((ROOT/'research/corpus-v0.4/S02-processed.json').read_text()))
        self.assertEqual(a['report']['reviewed_source_numeric_cells'],26)
        self.assertEqual(a['report']['derived_numeric_cells'],4)
        self.assertEqual(len({r['leakage_group_id'] for r in a['records']}),1)
        self.assertTrue(all(not r['training_eligible'] for r in a['records']))
        for r in a['records']:
            for o in r['observations']:self.assertTrue(o['locator'])
    def test_conversions_preserve_temperature_offset_mass_basis_and_volume(self):
        data=module('s02','scripts/build-s02.py').build()
        observations={o['metric']:o for r in data['records'] for o in r['observations']}
        self.assertAlmostEqual(observations['operating_temperature']['normalization']['value'],303.15)
        self.assertAlmostEqual(observations['oxygen_assay_volume']['normalization']['value'],28e-6)
        o=observations['volumetric_power_density_at_1kohm'];self.assertEqual(o['value'],o['normalization']['value'])
        self.assertEqual(o['normalization']['unit'],'W/m3')
        self.assertEqual(observations['Pt_metal_loading']['normalization']['unit'],'kgPt/m2')
    def test_oxygen_reconstruction_has_liquid_reference_and_no_kernel_binding(self):
        data=module('s02','scripts/build-s02.py').build()
        derived=[r for r in data['records'] if r['id'].startswith('S02-derived')]
        self.assertEqual(len(derived),2)
        for r in derived:
            c=r['conditions'];k=math.log(2)*c['liquid_volume_m3']/(c['oxygen_assay_area_m2']*c['half_saturation_time_s'])
            self.assertAlmostEqual(r['observations'][0]['value'],k)
            self.assertEqual(c['coefficient_reference'],'aqueous_bulk_concentration')
            self.assertTrue(all(not o['solver_binding_admitted'] for o in r['observations']))
        self.assertFalse(data['report']['published_flux_ratio_check']['consistent'])
        self.assertEqual(data['report']['conflicts_preserved'],4)
    def test_legacy_observations_and_conditions_remain_exactly_preserved(self):
        seed=json.loads((ROOT/'science/corpus-seed.json').read_text())
        self.assertEqual(seed['version'],'mfc-corpus/0.4.0')
        for change in seed['record_revisions']:
            desired=next(r for r in seed['records'] if r['id']==change['id'])
            stripped={k:v for k,v in desired.items() if k not in ['stage_ids','stage_attribution_review']}
            self.assertEqual(stripped,change['previous'])
        self.assertEqual(seed['report']['numeric_observations'],423)
        self.assertEqual(seed['report']['missing_observation_cells'],4)
    def test_acquisition_rejects_changed_copy_before_overwriting(self):
        acquire=module('acquire_s02','scripts/acquire-s02.py').acquire
        with tempfile.TemporaryDirectory() as tmp:
            pdf=Path(tmp)/'S02.pdf';pdf.write_bytes(b'%PDF- changed')
            with self.assertRaisesRegex(ValueError,'Source version changed'):acquire(tmp)
            self.assertEqual(pdf.read_bytes(),b'%PDF- changed')
if __name__=='__main__':unittest.main()
