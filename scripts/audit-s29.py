"""Audit published reactor/feed tables; describe coverage without fitting a predictor."""
from pathlib import Path
import json,statistics
ROOT=Path(__file__).resolve().parents[1]

def audit():
    base=ROOT/'research/corpus-v0.3'
    feeds=json.loads((base/'S29_feeds.json').read_text())
    records=json.loads((base/'S29_observations.json').read_text())
    assert len(feeds)==39 and len(records)==117
    assert len({r['id'] for r in records})==117
    assert len({r['leakage_group_id'] for r in records})==1
    by_medium={}
    for medium in ['SWW','RWW']:
        fs=[f for f in feeds if f['medium']==medium]
        rs=[r for r in records if r['medium']==medium]
        valid=[r for r in rs if all(o['value'] is not None for o in r['observations'])]
        for f in fs:
            matched=[r for r in rs if r['feed_id']==f['feed_id']]
            assert {r['reactor_label'] for r in matched}=={'R1','R2','R3'}
            for r in matched:
                rep=int(r['reactor_label'][-1]);a=f['table1_raw_values'][rep+1];b=f['table2_raw_values'][rep+1]
                assert r['observations'][0]['value']==(None if a=='-' else int(a))
                assert r['observations'][1]['value']==(None if b=='-' else float(b))
                assert r['COD_mg_L']==f['COD_mg_L'] and r['BOD_mg_L']==f['BOD_mg_L']
                assert r['anode_area_m2'] is None and not r['chronological_feed_order_known']
        by_medium[medium]={
            'published_feed_rows':len(fs),'reactor_feed_records':len(rs),'measured_pairs':len(valid),
            'missing_pairs':len(rs)-len(valid),'biological_reactors':3,
            'COD_range_mg_L':[min(f['COD_mg_L'] for f in fs),max(f['COD_mg_L'] for f in fs)],
            'author_calculated_BOD_range_mg_L':[min(f['BOD_mg_L'] for f in fs),max(f['BOD_mg_L'] for f in fs)],
            'peak_current_density_range_mA_m2':[min(r['observations'][0]['value'] for r in valid),max(r['observations'][0]['value'] for r in valid)],
            'response_time_range_h':[min(r['observations'][1]['value'] for r in valid),max(r['observations'][1]['value'] for r in valid)],
            'response_time_median_h':statistics.median(r['observations'][1]['value'] for r in valid),
            'descriptive_statistics_only':True,
        }
    return {'source_id':'S29','audit':'published_tables_and_calibration_readiness','by_medium':by_medium,
        'response_pairs':115,'missing_response_pairs':2,'response_numeric_cells':230,
        'independent_material_holdout_families_added':0,'shared_with_S18_leakage_group':'Salvian2024-Surrey-30mL',
        'current_kernel_calibration_ready':False,'training_eligible_records':0,'predictor_trained':False,
        'experimental_error_metrics':None,
        'blockers':[
            'SWW/RWW are complex substrates; current kernel is acetate-only.',
            'Published operatingpH7.4 differs from kernelpH7; operating temperature unreported.',
            'Published data use fed-batch replacement; current kernel batch dynamics are not validated for these feeds.',
            'Numeric area normalization unresolved; density-to-absolute-current conversion blocked.',
            'Tables contain peaks/response times, not individual chronological current/substrate series.',
            'Same three reactors reused; medium, age and cathode replacement are associated.',
            'No controlled variation across commercial materials in these table rows.',
            'Reactor overlap withS18 unresolved; source family conservatively co-grouped.',
        ],'next_admission':'Resolve area/methods and obtain independent comparable material/assembly groups before fitting material-to-parameter relationships.'}


if __name__=='__main__':
    report=audit();(ROOT/'research/corpus-v0.3/curation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
