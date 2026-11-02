"""Reproduce reviewed S02 conversions; source transcription is explicitly manual."""
from pathlib import Path
import copy,json,math
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/corpus-v0.4'

def build():
    extraction=json.loads((BASE/'S02-extraction.json').read_text())
    records=copy.deepcopy(extraction['records'])
    conversions={'mL':(1e-6,'m3'), 'cm':(.01,'m'), 'm2/m3':(1,'1/m'),
                 'degC':(1,'K'), 'Ohm':(1,'Ohm'), 'mgPt/cm2':(.01,'kgPt/m2'),
                 'kPa':(1000,'Pa'), 'min':(60,'s'), 'mW/m2':(.001,'W/m2'),
                 'mW/L':(1,'W/m3'), '%':(.01,'1'), 'cm2':(1e-4,'m2'),
                 'mol/L':(1000,'mol/m3'), 'mg/h':(1e-6/3600,'kg/s')}
    for record in records:
        for observation in record['observations']:
            value=observation['value'];unit=observation['unit']
            if not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Finite observed value required')
            factor,target=conversions[unit];offset=273.15 if unit=='degC' else 0
            observation['normalization']={'value':value*factor+offset,'unit':target,
                'transformation':{'multiply':factor,'add':offset},'source_value':value,'source_unit':unit,
                'reported_plus_minus':None if observation.get('uncertainty') is None else observation['uncertainty']*factor,
                'uncertainty_type':observation.get('uncertainty_type'),'solver_binding_admitted':False}
    assay=next(r for r in records if r['id']=='S02-reviewed-oxygen-assay')
    obs={o['metric']:o for o in assay['observations']}
    volume=obs['oxygen_assay_volume']['normalization']['value']
    area=obs['oxygen_assay_area']['normalization']['value']
    concentration=obs['oxygen_saturation_concentration_assumed']['normalization']['value']
    derived=[]
    for arm in ['PEM','noPEM']:
        time=obs['oxygen_half_saturation_time_'+arm]['normalization']['value']
        k=math.log(2)*volume/(area*time)
        rate=k*area*concentration*.032 # kg/s, molar mass O2=0.032 kg/mol
        derived.append({'id':'S02-derived-oxygen-ingress-'+arm,'source_id':'S02',
            'study_id':assay['study_id'],'leakage_group_id':assay['leakage_group_id'],
            'experimental_scope':'derived_component_oxygen_ingress','stage_ids':assay['stage_ids'],
            'source_locator':assay['source_locator'],'status':'derived_under_declared_assumptions',
            'training_eligible':False,'conditions':{'assembly':arm,'parent_record_id':assay['id'],
                'liquid_volume_m3':volume,'oxygen_assay_area_m2':area,'half_saturation_time_s':time,
                'concentration_assumed_mol_m3':concentration,'oxygen_molar_mass_kg_mol':.032,
                'well_mixed':True,'initial_oxygen_assumed_zero':True,'fixed_saturation_boundary':True,
                'coefficient_reference':'aqueous_bulk_concentration','correction_of_published_coefficient':False},
            'observations':[{'metric':'liquid_referenced_oxygen_ingress_coefficient','value':k,'unit':'m/s',
                'kind':'derived','locator':'Derived from '+assay['source_locator'],
                'equation':'ln(2)*V/(A*t_half)','uncertainty':None,'solver_binding_admitted':False},
                {'metric':'maximum_oxygen_ingress_mass_rate','value':rate,'unit':'kg/s','kind':'derived',
                 'locator':'Derived from '+assay['source_locator'],'equation':'k*A*C_sat*M_O2',
                 'uncertainty':None,'solver_binding_admitted':False}],
            'limitations':['Not a new independent measurement or external validation family.',
                'No distribution of uncertainty inferred from unspecified reported plus/minus.',
                'Ingress into stirred substrate-free liquid is not gas-referenced cathode ORR transport.',
                'Reported printed k remains unit-blocked; this reconstruction does not silently relabel it.']})
    records+=derived
    raw_count=sum(len(r['observations']) for r in extraction['records'])
    report={'source_id':'S02','reviewed_records_added':len(records),'reviewed_source_numeric_cells':raw_count,
        'derived_numeric_cells':4,'raw_transcription_method':'manual_visual_PDF_review',
        'normalizations':raw_count,'conflicts_preserved':len(extraction['conflicts']),
        'new_independent_experimental_families':0,'training_eligible_records':0,
        'kernel_calibration_ready':False,'experimental_error_metrics':None,
        'oxygen_ingress_reconstruction':[{'assembly':r['conditions']['assembly'],
            'k_liquid_m_s':r['observations'][0]['value'],
            'maximum_rate_mg_h':r['observations'][1]['value']*1e6*3600} for r in derived],
        'published_flux_ratio_check':{'computed':.187/.05,'reported':2.7,'consistent':False},
        'public_full_document_redistribution':False}
    return {'acquisition':extraction['acquisition'],'records':records,'conflicts':extraction['conflicts'],'report':report}

if __name__=='__main__':
    result=build()
    (BASE/'S02-processed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result['report'],indent=2))
