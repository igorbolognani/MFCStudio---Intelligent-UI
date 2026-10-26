"""Extract published tables, preserving missing cells and provenance.
No interpolation, normalization-to-current, fitting, or claimed external validation.
"""
from pathlib import Path
import json,re,csv,hashlib
R=Path(__file__).parent;D=R/'documents'
s=(D/'NPJ2024_supplement.txt').read_text()
def table_rows(k):
 section=s.split(f'Supplementary Table {k}:')[1].split(f'Supplementary Table {k+1}:')[0]
 out={'RWW':[],'SWW':[]}
 for line in section.splitlines():
  v=line.replace('\f','').split()
  if len(v) not in [5,10] or not all(re.fullmatch(r'\d+(?:\.\d+)?|-',x) for x in v):continue
  if len(v)==10:out['RWW'].append(v[:5]);out['SWW'].append(v[5:])
  else:out['SWW'].append(v)
 return out
current=table_rows(1);timing=table_rows(2)
records=[];feeds=[]
for medium,expected in [('SWW',21),('RWW',18)]:
 assert len(current[medium])==len(timing[medium])==expected
 for idx,(a,b) in enumerate(zip(current[medium],timing[medium]),1):
  assert a[:2]==b[:2],(medium,idx,a,b)
  feed_id=f'S29-{medium}-table-feed-{idx:02}'
  base={'source_id':'S29','doi':'10.1038/s41545-024-00350-5','leakage_group_id':'Salvian2024-Surrey-30mL','feed_id':feed_id,'medium':medium,'table_row_within_medium':idx,'record_status':'candidate','training_eligible':False,'chronological_feed_order_known':False,'time_since_medium_switch_days':None,'COD_mg_L':int(a[0]),'COD_kind':'reported_measured','BOD_mg_L':int(a[1]),'BOD_kind':'author_calculated_from_COD_ratio','replicate_count_biological':3,'external_load_Ohm':1000,'anolyte_volume_mL':30,'anode_area_m2':None,'area_basis':'anode_projected_geometric_reported_numeric_normalization_unresolved','cathode_state':'replaced_at_medium_switch; precise age for each table row not reported'}
  feeds.append({**base,'source_locator':'Supplementary Table1 and Table2, row within indicated medium','table1_raw_values':a,'table2_raw_values':b})
  for rep in range(1,4):
   v=None if a[rep+1]=='-' else int(a[rep+1]);t=None if b[rep+1]=='-' else float(b[rep+1])
   locator1=f'Supplement PDF p7, Table1, {medium} data row{idx}, columnR{rep}'
   page2=7 if idx<=3 else 8
   locator2=f'Supplement PDF p{page2}, Table2, {medium} data row{idx}, columnR{rep}'
   records.append({**base,'id':f'{feed_id}-R{rep}','reactor_label':f'R{rep}','reactor_global_identity':None,'experimental_scope':'full_cell_mfc','evidence_access':'full_text_and_supplement','evidence_kind':'published_table_individual_reactor_value','license':'CC-BY-4.0','observations':[{'metric':'maximum_current_density','value':v,'unit':'mA/m2','value_A_m2':None if v is None else v*.001,'value_transform':'mA/m2 x0.001 -> A/m2; no area conversion','kind':'measured','area_basis':base['area_basis'],'locator':locator1,'missing_reason':'equipment_fault_reported' if v is None else None},{'metric':'response_time_to_peak_current','value':t,'unit':'h','kind':'measured','definition':'Time from anolyte replacement to maximum current','locator':locator2,'missing_reason':'equipment_fault_reported' if t is None else None}], 'limits':['Same reactors repeatedly fed; these rows are not independent experiments.','BOD column is calculated by authors, not a direct BOD measurement on every row.','S18 and S29 conservatively share a provenance family; reactor overlap unresolved.','No predictive model fitted or training eligibility granted.']})
assert len(feeds)==39 and len(records)==117
assert sum(r['observations'][0]['value'] is None for r in records)==2
assert sum(r['observations'][1]['value'] is None for r in records)==2
(R/'S29_feeds.json').write_text(json.dumps(feeds,ensure_ascii=False,indent=2))
(R/'S29_observations.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
with (R/'S29_table1_table2.csv').open('w') as f:
 fields=['id','feed_id','medium','table_row_within_medium','reactor_label','COD_mg_L','BOD_mg_L','maximum_current_density_mA_m2','response_time_h','current_locator','time_locator'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for r in records:w.writerow({**{k:r[k] for k in fields[:7]},'maximum_current_density_mA_m2':r['observations'][0]['value'],'response_time_h':r['observations'][1]['value'],'current_locator':r['observations'][0]['locator'],'time_locator':r['observations'][1]['locator']})
meta={'id':'S29','title':'Resilience of anodic biofilm in microbial fuel cell biosensor for BOD monitoring of urban wastewater','authors':['Anna Salvian','Daniel Farkas','Marina Ramirez-Moreno','Daniela Torruella-Salas','Antonio Berná','Claudio Avignone-Rossa','John R. Varcoe','Abraham Esteve-Núñez','Siddharth Gadkari'],'doi':'10.1038/s41545-024-00350-5','year':2024,'published_at':'2024-06-28','journal':'npj Clean Water','volume':7,'article_number':53,'url':'https://www.nature.com/articles/s41545-024-00350-5','supplement_url':'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41545-024-00350-5/MediaObjects/41545_2024_350_MOESM1_ESM.pdf','access':'full_text_and_supplement_retrieved','read_scope':'complete_methods; main scientific text consulted; all supplement table1/2 cells inspected and extracted; timelineFigureS7 visually inspected; microbiome tables retained in source but not scientifically re-extracted','license':'CC-BY-4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','license_verified':True,'license_locator':'Main article Rights and permissions; PDFp12. No differing supplement copyright credit identified.','retrieved_at':'2026-10-26','type':'original_full_cell_experiment','leakage_group_id':'Salvian2024-Surrey-30mL','independent_external_validation_eligible':False,'independence_reason':'Same laboratory, inoculum origin, material formulation and day55 biofilm maturation asS18; supplement timeline describes prior acetate phase. Individual reactor identity overlap is unresolved; co-group conservatively.','stage_ids':['anode_chamber','anolyte','anode','biofilm','external_circuit','cathode_chamber','catholyte','cathode','cathode_catalyst'],'training_ready':False,'materials':{'anode':{'supplier':'Alfa Aesar','designation':'carbon felt6.35mm99.0%','reported_dimensions_cm':[2,3,.635],'article_SKU':None,'catalog_candidate_root_SKU':'043200','match_status':'brand/thickness/purity candidate, not article-reportedSKU'},'cathode':{'substrate_grade':'W1S1011','supplier':'FuelCell Store','Pt_loading_mgPt_cm2':.5,'catalyst_composition':'60wt%Pt/Vulcan-C','commercial_ready_GDE_candidate_SKU':'11060059','match_status':'grade/composition/loading correspondence; article does not give final GDESKU/lot'},'membrane':{'reported':False,'applicability':'no standalone membrane described; Nafion binder/postcoat is not a separate chamber-separating membrane'}},'methods':{'working_volume_mL':30,'chambers':1,'cathode_environment':'ambient_air','feed_regime':'fed_batch_complete_medium_replacement','external_resistance_Ohm':1000,'initial_inoculum':'acetate-fedMFC operating>1year, originallyUniversityofSurreypondsediment','inoculum_volume_fraction':.1,'inoculum_OD600':.5,'replicates_inoculated':3,'sterile_controls':1,'current_sampling_interval_s':180,'temperature_K':None,'operating_temperature_reported':False,'SWW_preparation':'10x sterile stock, recipe referred to Ref72 instead of fully listed in Methods','RWW_origin':'primaryWWTPeffluent,FundaciónCENTA,CarrióndelosCéspedes,Seville,Spain','pH_control_main_methods':{'value':7.4,'plus_minus':.3},'conductivity_control_mS_cm':{'value':1.10,'plus_minus':.2},'polarization_reactors':2,'polarization_scan_mV_s':.5,'OCP_rest_h_approx':2,'reference_electrode_CV':'Ag/AgCl3.5MKCl','reference_electrode_OCP':'not explicitly specified in method paragraph','cathode_replacement_interval_months':2,'cathode_replacement_source_days':[143,207],'phase_timeline_days':{'biofilm_formation':[0,55],'acetate':[55,143],'SWW':[143,207],'RWW':[207,247]},'quantitative_anode_normalization_area_m2':None,'normalization_issue':'Text says2x3cm felt and projectedanodearea; no12cm2 numeric declaration found inMethods or supplement. Do not resolve by inheriting a later thesis/paper.'},'data_summary':{'table1_feed_rows':39,'table2_feed_rows':39,'reactor_feed_records':117,'measured_pairs':115,'missing_reactor_feed_records':2,'numeric_response_values':230,'independent_experiment_count':None,'biological_reactors':3,'individual_timeseries_available':False,'dataset_access_statement':'available from corresponding author upon request; supplement nevertheless contains per-reactor tabulated peak/time observations.'},'issues':['Figure2 and supplementFigureS1/S2 usemg/mL in places where methods/tables usemg/L; retain raw source and use explicitly labeled table units.','Figure1 captionconductivity1.10±.3mScm vsMethods1.10±.2; do not silently pool uncertainty.','Figure3text/Methods infergeneabundance, not geneexpression measurements; microbiome data are not kinetic parameters.','Temperature not explicitly stated for MFCoperation.','Chronological feedtimestamps not available.']}
(R/'S29_source.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
# Dataset checks matter to avoid positional errors from side-by-side tables.
assert records[0]['observations'][0]['value']==154
assert records[0]['observations'][1]['value']==8.1
assert records[-1]['observations'][0]['value']==47
assert records[-1]['observations'][1]['value']==2.4
print(json.dumps(meta['data_summary'],indent=2))
