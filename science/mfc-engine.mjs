/** MFC Studio coupled exploratory kernel v0.2.0.
 * Physical verification is separate from predictive validation. All defaults
 * below are assumptions for code exploration, never fitted literature values.
 */
export const MODEL_VERSION = 'mfc-kernel/0.2.0';
export const FARADAY_C_MOL = 96485.33212;
export const GAS_R_J_MOL_K = 8.314462618;
export const STAGES = Object.freeze(['anode_chamber','anolyte','anode','anode_catalyst','biofilm','membrane','external_circuit','cathode_chamber','catholyte','cathode','cathode_catalyst']);
export const STAGE_LABELS = Object.freeze(['Câmara anódica','Meio anódico','Ânodo','Catalisador anódico','Biofilme','Membrana','Circuito e alimentação/coleta','Câmara catódica','Meio catódico','Cátodo','Catalisador catódico']);
const DEFAULTS = Object.freeze({
  chambers:1,cathode_environment:'ambient_air',membrane:'none',feed_regime:'batch',substrate:'acetate',culture:'mixed',external_bias_V:0,circuit_open:false,
  liquid_volume_m3:2.8e-5,catholyte_volume_m3:0,gas_volume_m3:0,
  cod_initial_g_m3:1000,kappa_S_m:0.5,ionic_length_m:0.03,ionic_area_m2:7e-4,
  anode_area_m2:7e-4,cathode_area_m2:7e-4,
  anode_sigma_S_m:3000,anode_electronic_length_m:0.003,anode_electronic_section_m2:7e-5,
  cathode_sigma_S_m:1500,cathode_electronic_length_m:0.003,cathode_electronic_section_m2:7e-5,
  contact_resistance_ohm:5,external_resistance_ohm:1000,ocv_V:0.7,
  anode_jmax_A_m2:5,monod_K_g_m3:100,anode_i0_A_m2:0.1,anode_b_V:0.05,
  anode_capacity_b_V:0.025,cathode_i0_A_m2:0.1,cathode_b_V:0.05,
  cathode_kO2_m_s:1e-6,oxygen_mole_fraction:0.2095,pressure_Pa:101325,temperature_K:298.15,
  competing_rate_s:3e-6,crossover_rate_s:1e-6,duration_s:86400,step_s:300,pH:7,
  anode_material:'carbon',cathode_material:'carbon',anode_catalyst:'none',cathode_catalyst:'activated_carbon',
  biofilm_thickness_m:1.2e-4,catalyst_loading_kg_m2:0.01,membrane_area_m2:7e-4,membrane_asr_ohm_m2:0.001,
});
export function defaultConfig() {return {...DEFAULTS};}
// name, symbol, unit, stage. Input catalog describes numerical roles, not accuracy.
const NUMERIC_SPECS = {
  liquid_volume_m3:['Volume líquido anódico','Vₐ','m³','anode_chamber'],
  catholyte_volume_m3:['Volume de católito independente','V𝚌','m³','cathode_chamber'],
  gas_volume_m3:['Volume de gás controlado','Vg','m³','cathode_chamber'],
  cod_initial_g_m3:['DQO inicial biodegradável na base de acetato','S₀','g O₂/m³','anolyte'],
  kappa_S_m:['Condutividade iônica hidratada','κ','S/m','anolyte'],
  ionic_length_m:['Percurso iônico efetivo','Lᵢ','m','anode_chamber'],
  ionic_area_m2:['Seção de condução iônica','Aᵢ','m²','anode_chamber'],
  anode_area_m2:['Área geométrica anódica','Aₐ','m²','anode'],
  cathode_area_m2:['Área geométrica catódica','A𝚌','m²','cathode'],
  anode_sigma_S_m:['Condutividade eletrônica anódica direcional','σₐ','S/m','anode'],
  anode_electronic_length_m:['Percurso eletrônico anódico','Lₑ,ₐ','m','anode'],
  anode_electronic_section_m2:['Seção eletrônica anódica','Aₑ,ₐ','m²','anode'],
  cathode_sigma_S_m:['Condutividade eletrônica catódica direcional','σ𝚌','S/m','cathode'],
  cathode_electronic_length_m:['Percurso eletrônico catódico','Lₑ,𝚌','m','cathode'],
  cathode_electronic_section_m2:['Seção eletrônica catódica','Aₑ,𝚌','m²','cathode'],
  contact_resistance_ohm:['Resistência de contatos','Rcont','Ω','external_circuit'],
  external_resistance_ohm:['Resistência de carga','Rext','Ω','external_circuit'],
  ocv_V:['Tensão de circuito aberto efetiva','Eoc','V de célula','external_circuit'],
  anode_jmax_A_m2:['Capacidade de corrente anódica em substrato saturante','jmax,ₐ','A/m² geométrico','biofilm'],
  monod_K_g_m3:['Constante de meia saturação de DQO','Kₛ','g O₂/m³','biofilm'],
  anode_i0_A_m2:['Densidade de troca anódica efetiva','j₀,ₐ','A/m² geométrico','biofilm'],
  anode_b_V:['Escala de ativação anódica efetiva','bₐ','V','biofilm'],
  anode_capacity_b_V:['Escala de perda por capacidade de substrato','bₛ','V','biofilm'],
  cathode_i0_A_m2:['Densidade de troca catódica efetiva','j₀,𝚌','A/m² geométrico','cathode_catalyst'],
  cathode_b_V:['Escala de ativação ORR efetiva','b𝚌','V','cathode_catalyst'],
  cathode_kO2_m_s:['Transferência efetiva de O₂ referida ao gás ambiente','kO₂,g','m/s','cathode'],
  oxygen_mole_fraction:['Fração molar de O₂ no ambiente','yO₂','mol/mol','cathode_chamber'],
  pressure_Pa:['Pressão do ar ambiente','p','Pa','cathode_chamber'],
  temperature_K:['Temperatura mantida','T','K','anode_chamber'],
  competing_rate_s:['Taxa efetiva de consumo não eletrogênico','kcomp','s⁻¹','biofilm'],
  crossover_rate_s:['Taxa efetiva de perda de DQO por ingresso de O₂','kcross','s⁻¹','anolyte'],
  duration_s:['Duração da batelada','Δt','s','external_circuit'],
  step_s:['Passo de saída e teto de integração','Δtmax','s','external_circuit'],
  pH:['pH tamponado informado','pH','1','anolyte'],
  biofilm_thickness_m:['Espessura hidratada do biofilme','δbf','m','biofilm'],
  catalyst_loading_kg_m2:['Carga de catalisador catódico informada','mcat/A','kg/m²','cathode_catalyst'],
  membrane_area_m2:['Área de membrana informada','Am','m²','membrane'],
  membrane_asr_ohm_m2:['ASR hidratada informada','ASRm','Ω m²','membrane'],
  external_bias_V:['Tensão externa aplicada','Vbias','V','external_circuit'],
};
const RECORDED = new Set(['catholyte_volume_m3','gas_volume_m3','biofilm_thickness_m','catalyst_loading_kg_m2','membrane_area_m2','membrane_asr_ohm_m2','pH']);
export const PARAMETER_SPECS = Object.freeze(Object.fromEntries(Object.entries(NUMERIC_SPECS).map(([key,[name,symbol,unit,stage]])=>[key,{key,name,symbol,unit,stage,role:RECORDED.has(key)?'recorded_only':'resolved_input',default_value:DEFAULTS[key],default_kind:'assumed',source_id:null,provenance:'Engineering exploration assumption; not fitted or imported from a paper',measurement_state:key.includes('sigma')?'directional; measurement conditions to be supplied':key.includes('kappa')||key.includes('asr')?'hydrated; temperature and method to be supplied':null}])));
export const MODEL_DECLARATION = Object.freeze({version:MODEL_VERSION,status:'exploratory_not_calibrated',predictor_trained:false,experimental_validation:false,uncertainty_calibrated:false,
 family:'Single chamber, membrane-free, acetate-COD batch, mixed culture, ambient-air four-electron ORR; fixed mature active capacity, buffered pH 7, 25 °C.',
 resolved:['electrical_closure','solution_and_electronic_ohmic_paths','effective_activation','substrate_limited_current_capacity','ambient_gas_referenced_O2_transfer_limit','batch_COD_electron_and_energy_accounting'],
 not_resolved:['biomass_growth','biofilm_internal_diffusion','pH_dynamics','ion_speciation','membrane_transport','finite_gas_inventory','catholyte_inventory','flooding_and_drying','material_descriptor_to_parameter_learning','auxiliary_energy','temporal_predictive_validation'],
 assumptions:['The complete polarization law is an engineering hypothesis, not a reproduction of one published model.','Effective kinetic and transport parameters must be identified jointly before experimental predictions.','Bulk acetate-COD is the only substrate state; no COD-to-molar-acetate conversion is performed.','Constant active biomass is implicit in jmax; biofilm thickness is recorded only.','Ambient air is a declared open boundary; a finite closed gas reservoir is not approximated as ambient air.','pH and temperature effects are not learned; only pH 7 and 298.15 K are supported.','kO2 is gas-concentration-referenced effective transfer, not a dissolved-oxygen kLa.','Crossover consumes COD through an assumed first-order sink scaled by ambient O2 concentration relative to 20.95% O2 at 1 atm and 25 °C; no spatial dissolved-O2 field is claimed.'],
 sources:[{id:'S08',doi:'10.3390/pr5040073',use:'Structural precedent only: substrate competition and electrical coupling; model equations and fitted parameters not copied.'},{id:'S02',doi:'10.1021/es0499344',use:'Experimental precedent for ambient-air membrane-free architecture; glucose data not used to calibrate acetate kinetics.'}],});

function finite(x) {return typeof x==='number'&&Number.isFinite(x);}
export function validateConfig(config) {
  const issues=[];
  if(!config||typeof config!=='object'||Array.isArray(config))return {valid:false,issues:['configuration_must_be_object']};
  for(const [key,value] of Object.entries(DEFAULTS)) {
    if(typeof value==='number'&&!finite(config[key]))issues.push(`invalid_number:${key}`);
    else if(typeof value==='boolean'&&typeof config[key]!=='boolean')issues.push(`invalid_boolean:${key}`);
    else if(typeof value==='string'&&(typeof config[key]!=='string'||config[key].length>200))issues.push(`invalid_string:${key}`);
  }
  if(![1,2].includes(config.chambers))issues.push('invalid_chambers');
  if(!['liquid','ambient_air','controlled_gas'].includes(config.cathode_environment))issues.push('invalid_cathode_environment');
  if(!['none','cem','aem','separator'].includes(config.membrane))issues.push('invalid_membrane');
  if(!['batch','fed_batch','continuous'].includes(config.feed_regime))issues.push('invalid_feed_regime');
  const strictPositive=['liquid_volume_m3','kappa_S_m','ionic_area_m2','anode_area_m2','cathode_area_m2','anode_sigma_S_m','anode_electronic_section_m2','cathode_sigma_S_m','cathode_electronic_section_m2','monod_K_g_m3','anode_i0_A_m2','anode_b_V','anode_capacity_b_V','cathode_i0_A_m2','cathode_b_V','pressure_Pa','temperature_K','step_s'];
  const nonNegative=['cod_initial_g_m3','ionic_length_m','anode_electronic_length_m','cathode_electronic_length_m','contact_resistance_ohm','external_resistance_ohm','ocv_V','anode_jmax_A_m2','cathode_kO2_m_s','competing_rate_s','crossover_rate_s','duration_s','catholyte_volume_m3','gas_volume_m3','biofilm_thickness_m','catalyst_loading_kg_m2','membrane_area_m2','membrane_asr_ohm_m2'];
  for(const k of strictPositive)if(finite(config[k])&&config[k]<=0)issues.push(`must_be_positive:${k}`);
  for(const k of nonNegative)if(finite(config[k])&&config[k]<0)issues.push(`must_be_nonnegative:${k}`);
  if(config.oxygen_mole_fraction<0||config.oxygen_mole_fraction>1)issues.push('oxygen_fraction_out_of_range');
  if(config.pH<0||config.pH>14)issues.push('pH_out_of_range');
  if(config.duration_s>604800)issues.push('duration_exceeds_seven_day_numerical_guard');
  if(config.step_s<1||config.step_s>3600)issues.push('step_must_be_between_1_and_3600_s');
  if(config.external_bias_V!==0)issues.push('MFC_excludes_electrolysis_bias');
  if(finite(config.duration_s)&&finite(config.step_s)&&config.duration_s/config.step_s>5000)issues.push('too_many_output_steps_maximum_5000');
  for(const [key,value] of Object.entries(config))if(typeof value==='number'&&finite(value)&&Math.abs(value)>1e12)issues.push(`numeric_guard_too_large:${key}`);
  for(const key of nonNegative)if(finite(config[key])&&config[key]>0&&config[key]<1e-12)issues.push(`numeric_guard_too_small:${key}`);
  for(const key of strictPositive)if(finite(config[key])&&config[key]<1e-12)issues.push(`numeric_guard_too_small:${key}`);
  if(finite(config.liquid_volume_m3)&&config.liquid_volume_m3<1e-9)issues.push('volume_below_one_microlitre_numerical_guard');
  if(finite(config.ocv_V)&&config.ocv_V>2)issues.push('effective_ocv_exceeds_2V_MFC_guard');
  return {valid:issues.length===0,issues:[...new Set(issues)]};
}
export function compileTopology(config) {
  const c=config||{}; const state=Object.fromEntries(STAGES.map(s=>[s,'active']));
  if(c.chambers===1)state.cathode_chamber=c.cathode_environment==='ambient_air'?'ambient_boundary':'not_separate';
  if(c.cathode_environment!=='liquid')state.catholyte='not_applicable';
  else if(c.chambers===1)state.catholyte='shared_with_anolyte';
  if(c.membrane==='none')state.membrane='absent';
  if(c.anode_catalyst==='none')state.anode_catalyst='absent';
  const reasons=[];
  if(c.chambers!==1)reasons.push('two_chamber_balances_not_implemented');
  if(c.cathode_environment!=='ambient_air')reasons.push(c.cathode_environment==='controlled_gas'?'finite_gas_inventory_required':'liquid_cathode_oxygen_balance_required');
  if(c.membrane!=='none')reasons.push('membrane_species_and_crossover_transport_required');
  if(c.feed_regime!=='batch')reasons.push('feed_balance_not_implemented');
  if(c.substrate!=='acetate')reasons.push('substrate_kinetics_not_calibrated_for_selected_feed');
  if(c.culture!=='mixed')reasons.push('culture_kinetics_not_calibrated_for_selected_culture');
  if(Math.abs(c.pH-7)>1e-10)reasons.push('pH_dependence_not_implemented_use_buffered_pH7');
  if(Math.abs(c.temperature_K-298.15)>1e-10)reasons.push('temperature_dependence_not_implemented_use_25C');
  if(c.chambers===1&&c.cathode_environment!=='liquid'&&c.catholyte_volume_m3!==0)reasons.push('independent_catholyte_volume_inapplicable');
  if(c.chambers===1&&c.cathode_environment==='liquid'&&c.catholyte_volume_m3!==0)reasons.push('shared_medium_must_not_duplicate_volume');
  if(c.cathode_environment==='ambient_air'&&c.gas_volume_m3!==0)reasons.push('ambient_boundary_must_not_have_closed_gas_inventory');
  if(c.anode_catalyst!=='none')reasons.push('anode_coating_constitutive_relation_not_implemented');
  return {stage_order:[...STAGES],stage_state:state,liquid_domain_count:c.chambers===1?1:c.cathode_environment==='liquid'?2:1,total_liquid_volume_m3:c.liquid_volume_m3+(c.chambers===2&&c.cathode_environment==='liquid'?c.catholyte_volume_m3:0),solver_supported:reasons.length===0,reasons};
}
function inspect(config) {
  const checked=validateConfig(config),topology=compileTopology(config);
  return {available:checked.valid&&topology.solver_supported,reasons:[...checked.issues,...topology.reasons],topology};
}
function unavailable(config) {return {...inspect(config),status:'prediction_unavailable',model_version:MODEL_VERSION,predictor_trained:false,experimental_validation:false};}
function circuit(config,S) {
  const c=config;
  const R_solution=c.ionic_length_m/(c.kappa_S_m*c.ionic_area_m2);
  const R_anode=c.anode_electronic_length_m/(c.anode_sigma_S_m*c.anode_electronic_section_m2);
  const R_cathode=c.cathode_electronic_length_m/(c.cathode_sigma_S_m*c.cathode_electronic_section_m2);
  const R_ohm=R_solution+R_anode+R_cathode+c.contact_resistance_ohm;
  const I_anode_capacity=c.anode_jmax_A_m2*c.anode_area_m2*S/(c.monod_K_g_m3+S);
  const gas_oxygen_mol_m3=c.oxygen_mole_fraction*c.pressure_Pa/(GAS_R_J_MOL_K*c.temperature_K);
  const I_oxygen_limit=4*FARADAY_C_MOL*c.cathode_area_m2*c.cathode_kO2_m_s*gas_oxygen_mol_m3;
  const limit=Math.min(I_anode_capacity,I_oxygen_limit);
  function losses(I,z=null){
    if(I===0)return {ohmic_V:0,anode_activation_V:0,cathode_activation_V:0,anode_capacity_V:0,oxygen_transport_V:0};
    // The limiting loss is evaluated in overpotential coordinate z. This
    // retains finite residuals when 1-I/Ilim is smaller than machine epsilon.
    const la=z!==null&&I_anode_capacity===limit?z:-Math.log1p(-I/I_anode_capacity);
    const lc=z!==null&&I_oxygen_limit===limit?z:-Math.log1p(-I/I_oxygen_limit);
    return {ohmic_V:I*R_ohm,
      anode_activation_V:c.anode_b_V*Math.asinh(I/(2*c.anode_i0_A_m2*c.anode_area_m2)),
      cathode_activation_V:c.cathode_b_V*Math.asinh(I/(2*c.cathode_i0_A_m2*c.cathode_area_m2)),
      anode_capacity_V:c.anode_capacity_b_V*la,
      oxygen_transport_V:(GAS_R_J_MOL_K*c.temperature_K/(4*FARADAY_C_MOL))*lc};
  }
  function voltage(I,z=null){return c.ocv_V-Object.values(losses(I,z)).reduce((a,b)=>a+b,0);}
  function stateAtLoad(Rext){
    if(limit<=0||S<=0||c.ocv_V<=0)return {I:0,z:0};
    let lo=0,hi=1;
    const current=z=>limit*(-Math.expm1(-z));
    const residual=z=>voltage(current(z),z)-current(z)*Rext;
    for(let k=0;k<64&&residual(hi)>0;k++)hi*=2;
    for(let k=0;k<112;k++) {const mid=(lo+hi)/2;if(residual(mid)>0)lo=mid;else hi=mid;}
    const z=(lo+hi)/2;return {I:current(z),z};
  }
  return {R_solution,R_anode,R_cathode,R_ohm,I_anode_capacity,I_oxygen_limit,gas_oxygen_mol_m3,limit,losses,voltage,stateAtLoad};
}
export function solve(config=defaultConfig(),state={}) {
  const eligibility=inspect(config);if(!eligibility.available)return unavailable(config);
  const S=state.cod_g_m3??config.cod_initial_g_m3;
  if(!finite(S)||S<0)return {...unavailable(config),available:false,reasons:['invalid_state_cod_g_m3']};
  const q=circuit(config,S),root=config.circuit_open?{I:0,z:0}:q.stateAtLoad(config.external_resistance_ohm),I=root.I,V=config.circuit_open&&S>0&&q.limit>0?config.ocv_V:I*config.external_resistance_ohm;
  const losses=q.losses(I,root.z),active=I>0;
  const residual=active?q.voltage(I,root.z)-V:0;
  if(!Number.isFinite(residual)||Object.values(losses).some(x=>!Number.isFinite(x))||!Number.isFinite(I)||!Number.isFinite(V)||Math.abs(residual)>1e-7)return {...unavailable(config),available:false,reasons:['numerical_voltage_closure_not_resolved']};
  return {available:true,status:'exploratory_not_calibrated',model_version:MODEL_VERSION,predictor_trained:false,experimental_validation:false,uncertainty_calibrated:false,
    topology:eligibility.topology,cod_g_m3:S,I_A:I,V_V:V,P_W:I*V,j_anode_A_m2:I/config.anode_area_m2,power_density_cathode_W_m2:I*V/config.cathode_area_m2,
    R_ohm:q.R_ohm,resistances:{solution_ohm:q.R_solution,anode_ohm:q.R_anode,cathode_ohm:q.R_cathode,contact_ohm:config.contact_resistance_ohm},losses,residual_V:residual,
    limits:{anode_capacity_A:q.I_anode_capacity,oxygen_transport_A:q.I_oxygen_limit,oxygen_boundary_mol_m3:q.gas_oxygen_mol_m3},
    rates:{electrogenic_COD_g_s:I*8/FARADAY_C_MOL,competing_COD_g_s:config.competing_rate_s*S*config.liquid_volume_m3,crossover_COD_g_s:config.crossover_rate_s*(config.oxygen_mole_fraction/0.2095)*(config.pressure_Pa/101325)*(298.15/config.temperature_K)*S*config.liquid_volume_m3,cathode_O2_mol_s:I/(4*FARADAY_C_MOL)},
    parameter_provenance:Object.fromEntries(Object.entries(PARAMETER_SPECS).map(([k,p])=>[k,{...p,value:config[k],value_kind:config.parameter_annotations?.[k]?.kind||'assumed',source_claim:config.parameter_annotations?.[k]?.source||null,source_claim_verified:false}])),
    diagnostics:[...(S===0?['no_substrate_no_current']:[]),...(q.I_oxygen_limit===0?['no_oxygen_no_current']:[]),'Bulk pH, active biomass and effective OCV held constant; descriptor-to-parameter relation untrained.'],};
}
export function polarizationCurve(config=defaultConfig(),n=80) {
  const operating=solve(config);if(!operating.available)return operating;
  if(!Number.isInteger(n)||n<2||n>1000)throw new RangeError('n must be integer 2..1000');
  const q=circuit(config,config.cod_initial_g_m3),short=q.stateAtLoad(0),Ishort=short.I;
  if(Ishort>0&&Math.abs(q.voltage(Ishort,short.z))>1e-7)return {...unavailable(config),available:false,reasons:['short_circuit_numerical_closure_not_resolved']};
  const points=Array.from({length:n},(_,k)=>{const I=Ishort*k/(n-1);const V=Ishort===0?0:k===n-1?0:Math.max(0,q.voltage(I));return {I_A:I,V_V:V,P_W:I*V,j_anode_A_m2:I/config.anode_area_m2,power_density_cathode_W_m2:I*V/config.cathode_area_m2};});
  const maximum=points.reduce((best,p)=>p.P_W>best.P_W?p:best,points[0]);
  return {available:true,status:'exploratory_not_calibrated',points,operating,maximum,area_basis:'cathode_geometric',curve_kind:'quasi_static_at_initial_COD_not_a_batch_measurement'};
}
export function simulateBatch(config=defaultConfig()) {
  const initial=solve(config);if(!initial.available)return initial;
  const V=config.liquid_volume_m3,m0=config.cod_initial_g_m3*V;
  let m=m0,t=0,Q=0,E=0,electro=0,comp=0,cross=0,oxygen=0,maxResidual=0,iterations=0,nextOutput=0;
  const series=[];
  let terminatedEarly=false;
  function point(){const p=solve(config,{cod_g_m3:m/V});return {time_s:t,cod_g_m3:m/V,I_A:p.I_A,V_V:p.V_V,P_W:p.P_W,charge_C:Q,energy_J:E};}
  series.push(point());nextOutput=Math.min(config.step_s,config.duration_s);
  while(t<config.duration_s-1e-10) {
    if(++iterations>100000)throw new Error('integration_guard_exceeded');
    const p=solve(config,{cod_g_m3:m/V});
    if(!p.available)return {...p,series,failed_time_s:t};
    const r=p.rates;
    if(m<Math.max(1e-300,m0*1e-14)){
      // Bound a negligible residual inventory explicitly; never create charge.
      t=config.duration_s;terminatedEarly=true;series.push(point());break;
    }
    const totalRate=r.electrogenic_COD_g_s+r.competing_COD_g_s+r.crossover_COD_g_s;
    const stable=totalRate>0?0.02*m/totalRate:Infinity;
    const dt=Math.min(config.step_s,config.duration_s-t,Math.max(0,nextOutput-t),stable);
    if(dt>0&&t+dt===t)return {available:false,status:'prediction_unavailable',reasons:['time_step_below_machine_resolution'],series,failed_time_s:t};
    if(dt<=0){nextOutput=Math.min(config.duration_s,nextOutput+config.step_s);continue;}
    const dmE=r.electrogenic_COD_g_s*dt,dmC=r.competing_COD_g_s*dt,dmX=r.crossover_COD_g_s*dt;
    m-=dmE+dmC+dmX;electro+=dmE;comp+=dmC;cross+=dmX;Q+=p.I_A*dt;E+=p.P_W*dt;oxygen+=r.cathode_O2_mol_s*dt;
    t+=dt;maxResidual=Math.max(maxResidual,Math.abs(p.residual_V));
    if(Math.abs(t-nextOutput)<1e-7||t>=config.duration_s-1e-10){series.push(point());nextOutput=Math.min(config.duration_s,nextOutput+config.step_s);}
  }
  const removed=m0-m,theoretical=removed*FARADAY_C_MOL/8;
  return {available:true,status:'exploratory_not_calibrated',model_version:MODEL_VERSION,predictor_trained:false,experimental_validation:false,uncertainty_calibrated:false,series,
    balances:{initial_COD_g:m0,final_COD_g:m,removed_COD_g:removed,electrogenic_COD_g:electro,competing_COD_g:comp,crossover_COD_g:cross,charge_C:Q,energy_J:E,cathode_O2_mol:oxygen,
      coulombic_efficiency:theoretical>0?Q/theoretical:null,mass_residual_g:m0-m-electro-comp-cross,charge_residual_C:Q-electro*FARADAY_C_MOL/8,oxygen_charge_residual_C:Q-oxygen*4*FARADAY_C_MOL,max_voltage_residual_V:maxResidual},
    numerics:{method:'adaptive_forward_Euler_maximum_2_percent_COD_step',internal_steps:iterations,step_ceiling_s:config.step_s,residual_inventory_held_after_termination:terminatedEarly,residual_inventory_relative_threshold:1e-14},
    scope:'Constant active capacity and buffered pH; time trajectory is a model hypothesis, not validated temporal forecasting; gross electrical energy only.'};
}
export function sensitivity(config=defaultConfig(),fraction=0.1,keys=['kappa_S_m','anode_jmax_A_m2','cathode_kO2_m_s','external_resistance_ohm']) {
  if(!finite(fraction)||fraction<=0||fraction>=1)throw new RangeError('fraction must be 0..1');
  const base=solve(config);if(!base.available)return base;
  return {available:true,kind:'deterministic_one_at_a_time_sensitivity_not_confidence_interval',fraction,base_P_W:base.P_W,
    rows:keys.map(key=>{if(!PARAMETER_SPECS[key]||!finite(config[key]))throw new Error(`unknown numerical parameter:${key}`);const lower=solve({...config,[key]:config[key]*(1-fraction)}),upper=solve({...config,[key]:config[key]*(1+fraction)});return {key,lower_P_W:lower.available?lower.P_W:null,upper_P_W:upper.available?upper.P_W:null,unit:PARAMETER_SPECS[key].unit};})};
}

export const OUTPUT_SPECS=Object.freeze({I_A:{symbol:'I',name:'Corrente',unit:'A',role:'solved_output'},V_V:{symbol:'V',name:'Tensão terminal',unit:'V de célula',role:'solved_output'},P_W:{symbol:'P',name:'Potência bruta da célula',unit:'W',role:'derived_output'},R_ohm:{symbol:'RΩ',name:'Resistência ôhmica total',unit:'Ω',role:'derived_output'},cod_g_m3:{symbol:'S',name:'DQO disponível na base de acetato',unit:'g O₂/m³',role:'dynamic_state'},time_s:{symbol:'t',name:'Tempo',unit:'s',role:'independent_variable'},charge_C:{symbol:'Q',name:'Carga elétrica acumulada',unit:'C',role:'integrated_output'},energy_J:{symbol:'E',name:'Energia elétrica bruta',unit:'J',role:'integrated_output'},F:{symbol:'F',name:'Constante de Faraday',unit:'C/mol e⁻',value:FARADAY_C_MOL,role:'constant'},R:{symbol:'R',name:'Constante dos gases',unit:'J/(mol K)',value:GAS_R_J_MOL_K,role:'constant'},cathode_O2_mol:{symbol:'nO₂',name:'Oxigênio consumido na ORR de quatro elétrons',unit:'mol',role:'integrated_output'}});
export const EQUATIONS=Object.freeze([
 {id:'electrical',status:'resolved',equation:'Eoc = I Rext + I RΩ + ηa + ηc + ηS + ηO2',description:'Fechamento escalar não linear do circuito resistivo; termos de ativação efetivos não são resistências EPS/EIS.',symbols:['ocv_V','external_resistance_ohm','I_A','R_ohm']},
 {id:'ionic',status:'resolved',equation:'Rsol = Li / (κ Ai)',description:'Percurso iônico uniforme efetivo. Não é solução espacial de potencial.',symbols:['ionic_length_m','kappa_S_m','ionic_area_m2']},
 {id:'electronic',status:'resolved',equation:'Re,a = Le,a / (σa Ae,a); Re,c = Le,c / (σc Ae,c)',description:'Seções de condução eletrônica distintas da área reacional geométrica.',symbols:['anode_electronic_length_m','anode_sigma_S_m','anode_electronic_section_m2','cathode_electronic_length_m','cathode_sigma_S_m','cathode_electronic_section_m2']},
 {id:'monod',status:'resolved',equation:'Icap,a = jmax,a Aa S / (Ks + S); ηS = −bS ln(1 − I/Icap,a)',description:'Capacidade de bioânodo limitado por substrato; biomassa ativa fixa implícita em jmax. Não é crescimento microbiano resolvido.',symbols:['anode_jmax_A_m2','anode_area_m2','cod_g_m3','monod_K_g_m3','anode_capacity_b_V']},
 {id:'activation',status:'resolved',equation:'ηa = ba asinh[I/(2 j0,a Aa)]; ηc = bc asinh[I/(2 j0,c Ac)]',description:'Leis efetivas de ativação, hipótese de engenharia ainda não identificada por experimentos.',symbols:['anode_b_V','anode_i0_A_m2','anode_area_m2','cathode_b_V','cathode_i0_A_m2','cathode_area_m2','I_A']},
 {id:'oxygen',status:'resolved',equation:'C_O₂,g = yO2 p/(R T); Ilim,O2 = 4 F Ac kO2,g C_O₂,g; ηO2 = −RT/(4F) ln(1 − I/Ilim,O2)',description:'ORR de quatro elétrons e transferência efetiva referida ao gás; ambiente aberto declarado, sem volume gasoso finito.',symbols:['oxygen_mole_fraction','pressure_Pa','temperature_K','cathode_area_m2','cathode_kO2_m_s','R','F','I_A']},
 {id:'substrate',status:'resolved',equation:'d(Va S)/dt = −8 I/F − kcomp Va S − kcross (C_O₂,g/C_O₂,g,ref) Va S',description:'DQO em gramas equivalentes de O2. 8 g COD por mol de elétrons. Ingresso O2 é um sumidouro efetivo, sem campo de O2 dissolvido.',symbols:['liquid_volume_m3','cod_g_m3','I_A','F','competing_rate_s','crossover_rate_s']},
 {id:'charge_energy',status:'resolved',equation:'Q = ∫ I dt; E = ∫ I V dt; CE = Q/[ΔmCOD F/8]; nO2 = Q/(4F)',description:'Energia bruta, sem consumos auxiliares. Eficiência calculada sobre DQO removida total; valores não cortados silenciosamente.',symbols:['I_A','V_V','charge_C','energy_J','time_s','F','cathode_O2_mol']},
 {id:'membrane',status:'explained_not_resolved',equation:'Rm = ASRm/Am',description:'Explicação somente. Presença de membrana exige transporte de espécies e crossover; a previsão numérica é indisponível nesta família.',symbols:['membrane_area_m2','membrane_asr_ohm_m2']},
]);
