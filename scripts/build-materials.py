"""Deterministic factual curation, shared by corpus seeding and integrity tests."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'science'))
from material_data import normalize_property,derive_conductivity,assess_binding,summarize_offer,UnitError


def build():
    data=json.loads((ROOT/'research/materials-v0.1/catalog.json').read_text())
    sources={s['id']:s for s in data['sources']}
    materials={m['id']:m for m in data['materials']}
    observations=[];records=[]
    for o in data['property_observations']:
        assert o['source_id'] in sources and o['material_id'] in materials
        assert o['locator'] and o['id']
        try:
            normalized=normalize_property(o);status='normalized_dimensions_only'
        except UnitError:
            assert o.get('normalization_blocked_reason'),'Unexpected unresolved unit: '+o['id']
            normalized=None;status='blocked_pending_source_clarification'
        derived=derive_conductivity(o) if o['quantity']=='electronic_resistivity' and normalized else None
        target={'parameter':'cathode_sigma_S_m' if 'cathode' in materials[o['material_id']]['stage_ids'] else 'anode_sigma_S_m',
                'material_id':o['material_id'],'conditions':{'hydration':'wet','temperature_C':25}}
        gate=assess_binding(o,target)
        assert not gate['eligible_for_binding']
        observations.append({**o,'normalization_status':status,'normalized':normalized,'derived_conductivity':derived,'binding_review':gate})
    for m in data['materials']:
        obs=[o for o in observations if o['material_id']==m['id']]
        source=sources[m['primary_source_id']]
        records.append({
            'id':'commercial:'+m['id'],'source_id':source['id'],'study_id':source['url'],
            'leakage_group_id':'commercial-source:'+source['id'],'experimental_scope':'supplier_or_manufacturer_specification',
            'stage_ids':m['stage_ids'],'source_locator':source['read_scope'],
            'status':'reviewed_factual_extraction_not_experimental_validation','training_eligible':False,
            'conditions':{'material_variant':m,'commercial_scope':True,'calibration_status':'not_calibrated',
                          'normalization_is_not_solver_admission':True,'property_measurements_and_normalization':obs},
            'observations':[{'metric':o['quantity'],'value':o['value'],'unit':o['unit'],
                             'kind':o['value_role'],'locator':o['locator'],'material_property':o} for o in obs],
            'limitations':[source['limits'],'No automatic binding to MFC scenario defaults; no experimental prediction error established.']+[o['normalization_blocked_reason'] for o in obs if o.get('normalization_blocked_reason')],
        })
    processed_offers=[]
    for o in data['offer_snapshots']:
        assert o['source_id'] in sources and o['material_id'] in materials and o['observed_at']
        normalized=summarize_offer(o)
        processed_offers.append({**o,'normalized':normalized})
        records.append({
            'id':'offer:'+o['id'],'source_id':o['source_id'],'study_id':sources[o['source_id']]['url'],
            'leakage_group_id':'commercial-source:'+o['source_id'],'experimental_scope':'commercial_offer_snapshot',
            'stage_ids':materials[o['material_id']]['stage_ids'],'source_locator':o['locator'],
            'status':'dated_advertisement_not_delivered_quote','training_eligible':False,
            'conditions':{'offer':o,'cost_normalization':normalized,'experimental_validation':False},
            'observations':[{'metric':'advertised_price' if o['price_type']=='fixed_variant' else 'advertised_minimum_price',
                'value':o['price_amount'],'unit':o['currency'],'kind':'commercial_snapshot_not_scientific_measurement','locator':o['locator']}],
            'limitations':['Purchased sheet area is not installed active area or cutting yield.',
                          'Shipping, taxes, import duty, currency conversion and confirmed delivery are unresolved.',
                          'Availability is a seller claim, not independently confirmed stock or suitability.'],
        })
    report={
        'material_variants':len(materials),'commercial_sources':len(sources),
        'property_observations':len(observations),'normalized_property_observations':sum(o['normalized'] is not None for o in observations),
        'blocked_property_normalizations':sum(o['normalized'] is None for o in observations),
        'offer_snapshots':len(processed_offers),'exact_variant_offers':sum(o['price_type']=='fixed_variant' for o in processed_offers),
        'offers_with_comparable_purchased_area':sum(o['normalized']['advertised_price_per_purchased_m2'] is not None for o in processed_offers),
        'confirmed_delivered_quotes':sum(o['normalized']['delivered_total'] is not None for o in processed_offers),
        'automatic_solver_bindings':0,'training_eligible_records':0,'stage_acquisition_plan_count':len(data['stage_acquisition_plan']),
    }
    return {'version':data['version'],'sources':data['sources'],'materials':data['materials'],
            'property_observations':observations,'offer_snapshots':processed_offers,'records':records,
            'experimental_links':data['experimental_links'],'record_qualifications':data['record_qualifications'],
            'stage_acquisition_plan':data['stage_acquisition_plan'],'reading_limits':data['reading_limits'],'report':report}


if __name__=='__main__':
    result=build()
    (ROOT/'science/materials-processed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'research/materials-v0.1/curation-report.json').write_text(json.dumps(result['report'],indent=2)+'\n')
    print(json.dumps(result['report'],indent=2))
