import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('material_data', Path(__file__).resolve().parents[1]/'science/material_data.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def prop(quantity='electronic_resistivity', value=80, unit='mOhm*cm', relation='eq'):
    return {'id':'fixture', 'material_id':'substrate-only', 'quantity':quantity, 'value':value,
            'unit':unit, 'relation':relation, 'value_role':'manufacturer_typical',
            'conditions':{'hydration':'dry', 'temperature_C':25, 'pressure_Pa':100000,
                          'method':'fixture-method', 'direction':'through_plane', 'contact_contribution':'removed'}}


class MaterialDataTests(unittest.TestCase):
    def test_directional_resistivity_units_and_inversion(self):
        self.assertAlmostEqual(module.normalize_property(prop())['value'], .0008)
        self.assertAlmostEqual(module.derive_conductivity(prop())['value'], 1250)
        self.assertAlmostEqual(module.derive_conductivity(prop(value=5.8))['value'], 17241.379310344826)
        self.assertEqual(module.derive_conductivity(prop(relation='lt'))['relation'], 'gt')

    def test_asr_never_becomes_bulk_conductivity(self):
        observation=prop('electronic_ASR',10,'mOhm*cm2','lt')
        self.assertAlmostEqual(module.normalize_property(observation)['value'], 1e-6)
        with self.assertRaises(ValueError):module.derive_conductivity(observation)
        observation['unit']='mOhm/cm2'
        with self.assertRaises(module.UnitError):module.normalize_property(observation)

    def test_fraction_and_pt_mass_basis(self):
        self.assertEqual(module.normalize_property(prop('porosity',78,'%'))['value'], .78)
        with self.assertRaises(ValueError):module.normalize_property(prop('porosity',78,'1'))
        self.assertEqual(module.normalize_property(prop('metal_loading',.5,'mgPt/cm2'))['value'], .005)
        with self.assertRaises(module.UnitError):module.normalize_property(prop('metal_loading',.5,'mgPtC/cm2'))

    def test_binding_requires_matching_state_variant_direction_geometry_review(self):
        p=prop();target={'parameter':'cathode_sigma_S_m','material_id':p['material_id'],
            'conditions':dict(p['conditions']),'geometry':{'length_m':.02,'cross_section_m2':2e-6},'explicit_review_id':'synthetic-test-only'}
        result=module.assess_binding(p,target)
        self.assertTrue(result['eligible_for_binding']);self.assertEqual(result['calibration_status'],'not_calibrated')
        for key,value in [('hydration','wet'),('direction','in_plane'),('pressure_Pa',1000000),('temperature_C',30)]:
            changed={**target,'conditions':{**target['conditions'],key:value}}
            self.assertIn(key+'_mismatch',module.assess_binding(p,changed)['reasons'])
        self.assertIn('material_variant_mismatch',module.assess_binding(p,{**target,'material_id':'PTFE-treated'})['reasons'])
        self.assertIn('electronic_path_geometry_missing',module.assess_binding(p,{**target,'geometry':{}})['reasons'])
        self.assertIn('explicit_review_missing',module.assess_binding(p,{**target,'explicit_review_id':None})['reasons'])

    def test_unknown_conditions_are_not_matches_and_descriptors_do_not_supply_kinetics(self):
        p=prop();p['conditions']={};target={'parameter':'cathode_sigma_S_m','material_id':p['material_id'],'conditions':{}}
        self.assertFalse(module.assess_binding(p,target)['eligible_for_binding'])
        for q,u,v in [('BET_specific_area','m2/g',890),('gas_transit_time','s',55),('intrinsic_gas_permeability','m2',1e-12),('membrane_ASR','Ohm*cm2',30)]:
            self.assertIn('no_supported_constitutive_transfer',module.assess_binding(prop(q,v,u),{'parameter':'cathode_i0_A_m2'})['reasons'])

    def test_pack_area_price_floor_and_unknown_landed_cost(self):
        offer={'price_amount':118,'currency':'USD','price_type':'starting_from','pack_count':9,
               'sheet_dimensions_cm':[10,10],'dimension_price_binding_verified':True}
        r=module.summarize_offer(offer)
        self.assertEqual(r['purchased_sheet_area_m2'],.09)
        self.assertAlmostEqual(r['advertised_price_per_purchased_m2'],1311.111111111111)
        self.assertEqual(r['price_relation'],'ge');self.assertIsNone(r['delivered_total'])
        self.assertIsNone(r['usable_active_area_m2'])
        self.assertIsNone(module.summarize_offer({**offer,'dimension_price_binding_verified':False})['advertised_price_per_purchased_m2'])

    def test_fixed_offer_does_not_imply_stock_or_delivered_cost(self):
        offer={'price_amount':51,'currency':'USD','price_type':'fixed_variant','pack_count':1,
               'sheet_dimensions_cm':[5,5],'dimension_price_binding_verified':True}
        r=module.summarize_offer(offer)
        self.assertEqual(r['advertised_price_per_purchased_m2'],20400)
        self.assertIsNone(r['delivered_total']);self.assertFalse(r['mfc_performance_inferred'])
        self.assertIsNone(module.summarize_offer({**offer,'price_type':'request_quote'})['advertised_price_per_purchased_m2'])


if __name__=='__main__':unittest.main()
