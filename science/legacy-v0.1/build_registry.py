"""Build explicit, inspectable seed registries. No literature scraping or training."""
from pathlib import Path
import json

BASE = Path(__file__).parent

SOURCES = [
 {"id":"S01","title":"Impact of Surface Properties of Porous SiOC-Based Materials on the Performance of Geobacter Biofilm Anodes","doi":"10.1002/celc.202001568","year":2021,"url":"https://chemistry-europe.onlinelibrary.wiley.com/doi/full/10.1002/celc.202001568","access":"full_text_sections_consulted","type":"original_component_experiment","use":"Material descriptors; three-electrode BES response. Not full-cell power.","limits":"Independent conditions/cycles needed; conductivity values cite an earlier study."},
 {"id":"S02","title":"Electricity Generation Using an Air-Cathode Single Chamber Microbial Fuel Cell in the Presence and Absence of a Proton Exchange Membrane","doi":"10.1021/es0499344","year":2004,"url":"https://pure.psu.edu/en/publications/electricity-generation-using-an-air-cathode-single-chamber-microb/","access":"institutional_abstract","type":"original_full_cell_experiment","use":"Membrane presence affects power and electron recovery jointly.","limits":"Do not import the apparent wastewater unit typo in the repository abstract; raw curves and area convention pending."},
 {"id":"S03","title":"Evaluation of Electrode and Solution Area-Based Resistances Enables Quantitative Comparisons of Factors Impacting Microbial Fuel Cell Performance","doi":"10.1021/acs.est.8b06004","year":2019,"url":"https://pure.psu.edu/en/publications/evaluation-of-electrode-and-solution-area-based-resistances-enabl/","access":"institutional_abstract","type":"original_full_cell_analysis","use":"EPS electrode slopes and solution resistance depend on operating medium.","limits":"EPS resistance is not automatically EIS charge-transfer resistance. Repository omits the Ohm glyph; units cross-checked against publisher abstract. Publisher/full-manuscript retrieval failed."},
 {"id":"S04","title":"Conduction-based modeling of the biofilm anode of a microbial fuel cell","doi":"10.1002/bit.21533","year":2007,"url":"https://pubmed.ncbi.nlm.nih.gov/17570714/","access":"abstract","type":"original_mechanistic_model","use":"Biofilm conduction, substrate and potential limitation.","limits":"Full equation conventions and fitted parameters not reconstructed."},
 {"id":"S05","title":"A computational model for biofilm-based microbial fuel cells","doi":"10.1016/j.watres.2007.04.009","year":2007,"url":"https://pubmed.ncbi.nlm.nih.gov/17537478/","access":"abstract","type":"original_mechanistic_model","use":"Coupled substrate, biomass, electrical response and geometry.","limits":"Mediator-specific framework; not a universal direct-EET model."},
 {"id":"S06","title":"Effects of membrane cation transport on pH and microbial fuel cell performance","doi":"10.1021/es060387r","year":2006,"url":"https://research.wur.nl/en/publications/effects-of-membrane-cation-transport-on-ph-and-microbial-fuel-cel/","access":"institutional_abstract","type":"original_transport_experiment","use":"Ion identity, pH and membrane transport must remain coupled.","limits":"No complete transport coefficients extracted."},
 {"id":"S07","title":"Enhanced activated carbon cathode performance for microbial fuel cell by blending carbon black","doi":"10.1021/es405029y","year":2014,"url":"https://pure.psu.edu/en/publications/enhanced-activated-carbon-cathode-performance-for-microbial-fuel-/","access":"institutional_abstract","type":"original_catalyst_experiment","use":"Composition, charge transfer, mass transfer and ageing are separate effects.","limits":"Full loading, electrode geometry and raw curves pending."},
 {"id":"S08","title":"An Integrated Mathematical Model of Microbial Fuel Cell Processes: Bioelectrochemical and Microbiologic Aspects","doi":"10.3390/pr5040073","year":2017,"url":"https://www.mdpi.com/2227-9717/5/4/73","access":"full_text_sections_consulted","type":"original_integrated_model","use":"Dynamic substrate and competing populations; selective reuse of assumptions.","limits":"Cathode non-limiting assumption is incompatible with universal cathode comparison. Review ion-carrier simplifications against S06."},
 {"id":"S09","title":"Time-series forecasting of microbial fuel cell energy generation using deep learning","doi":"10.3389/fcomp.2024.1447745","year":2024,"url":"https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2024.1447745/full","access":"full_text_sections_consulted","type":"original_time_series_prediction","use":"Regime-aware validation and uncertainty; soil-MFC domain.","limits":"Short-horizon forecast using histories; does not establish prediction of arbitrary new material/geometry combinations."},
 {"id":"S10","title":"Microbial fuel cell data set","doi":"10.17632/gydpxvj8gp.1","year":2021,"url":"https://data.mendeley.com/datasets/gydpxvj8gp/1","access":"dataset_landing_page","type":"open_dataset_candidate","use":"Brewery wastewater; chemical cathodic acceptors; polarization and COD.","limits":"Files not downloaded. KMnO4/ferricyanide conditions are not oxygen-cathode data.","reported_license":"CC BY 4.0"},
 {"id":"S11","title":"[DATASET 8] - MICROBIAL FUEL CELLS (MFCS), GrowBot","doi":"10.5281/zenodo.8096219","year":2021,"url":"https://zenodo.org/records/8096219","access":"dataset_landing_page","type":"open_dataset_candidate","use":"Plant/soil MFC voltage, voltammetry and energy harvesting.","limits":"Files listed, not downloaded or parsed; domain differs from a liquid MFC; license confirmation pending."},
 {"id":"S12","title":"Artificial neural network simulating microbial fuel cells with different membrane materials and electrode configurations","year":2019,"url":"https://uwe-repository.worktribe.com/output/1491788/artificial-neural-network-simulating-microbial-fuel-cells-with-different-membrane-materials-and-electrode-configurations","access":"discovery_only_repository_403","type":"candidate_ml_study","use":"Candidate study of finite configuration combinations.","limits":"No full-text or parameter extraction; not used as validation."},
 {"id":"S13","title":"Architectural design of hierarchically meso-macroporous carbon for microbial fuel cell anodes","doi":"10.1039/C5RA26420K","year":2016,"url":"https://pubs.rsc.org/en/content/articlehtml/2016/ra/c5ra26420k","access":"discovery_only_fetch_failed","type":"candidate_original_material_experiment","use":"Candidate pore-architecture study.","limits":"Full text retrieval failed; no quantitative record admitted."},
 {"id":"S14","title":"Electrochemical modeling of microbial fuel cells performance at different operating and structural conditions","doi":"10.1007/s00449-019-02235-1","year":2020,"url":"https://pubmed.ncbi.nlm.nih.gov/31677000/","access":"discovery_only","type":"candidate_electrochemical_model","use":"Candidate multi-system polarization model.","limits":"Performance numbers in discovery output not used as verified results."},
 {"id":"S15","title":"Sites: Data and connections","url":"https://learn.chatgpt.com/docs/sites/data-and-connections","access":"official_documentation","type":"platform_documentation","use":"Public landing, ChatGPT sign-in, server-side authorization and durable user records.","limits":"No Site has been registered or deployed for this increment."},
 {"id":"S16","title":"A two-population bio-electrochemical model of a microbial fuel cell","doi":"10.1016/j.biortech.2010.01.122","year":2010,"url":"https://publications.polymtl.ca/17762/","access":"institutional_metadata","type":"candidate_mechanistic_model","use":"Competing-population model candidate.","limits":"Bibliographic identification only; full manuscript unavailable in retrieved record."},
]

STAGE_TEXT = {
"anode_chamber": ("Câmara anódica", "substrate_balance;ionic_path;oxygen_crossover", "S02,S05,S08", """
liquid_volume|V_a|Volume líquido|m3
headspace_volume|V_g,a|Volume do headspace|m3
ionic_path_length|L_a|Percurso iônico efetivo|m
ionic_cross_section|A_ion,a|Área efetiva do percurso iônico|m2
inflow|Q_in|Vazão de entrada|m3/s
mixing_mass_transfer|k_L,a|Coeficiente de transferência de massa|m/s
wall_oxygen_permeance|K_wall,O2|Permeância efetiva ao oxigênio|mol/(m2 s Pa)
temperature|T_a|Temperatura|K
"""),
"anolyte": ("Meio anódico", "substrate_balance;acid_base;ionic_path;microbial_competition", "S04,S05,S06,S08", """
substrate_concentration|S|Concentração do substrato identificado|mol/m3
cod|COD|Demanda química de oxigênio|kg O2/m3
biodegradable_cod_fraction|f_bCOD|Fração biodegradável da DQO|1
conductivity|kappa_a|Condutividade iônica|S/m
ph|pH_a|pH|1
alkalinity|Alk_a|Alcalinidade em equivalentes|mol charge/m3
buffer_total|C_buffer,a|Concentração total do tampão|mol/m3
ionic_strength|I_ion,a|Força iônica|mol/m3
dissolved_oxygen|C_O2,a|Oxigênio dissolvido|mol/m3
nutrient_nitrogen|C_N|Nitrogênio assimilável|mol/m3
inhibitor_concentration|C_inhib|Concentração de inibidor identificado|mol/m3
viscosity|mu_a|Viscosidade dinâmica|Pa s
"""),
"anode": ("Ânodo", "electronic_conduction;colonization;biofilm_transfer", "S01,S03,S04,S05", """
geometric_area|A_a|Área geométrica molhada|m2
projected_area|A_proj,a|Área projetada declarada|m2
electronic_conductivity|sigma_a|Condutividade eletrônica efetiva direcional|S/m
conduction_length|L_e,a|Comprimento do percurso eletrônico|m
conduction_cross_section|A_e,a|Seção transversal da condução eletrônica|m2
open_porosity|epsilon_a|Porosidade aberta|1
pore_size|d_pore,a|Distribuição/tamanho de poros|m
tortuosity|tau_a|Tortuosidade e convenção|1
bet_specific_area|a_BET,a|Área específica BET|m2/kg
wet_ecsa|A_ECSA,a|Área eletroquímica em condição molhada|m2
roughness|Ra_a|Rugosidade média e método|m
contact_angle|theta_a|Ângulo de contato e protocolo|degree
surface_functionality|x_func,a|Fração atômica de grupo identificado|1
capacitance|C_dl,a|Capacitância da dupla camada|F
"""),
"anode_catalyst": ("Catalisador anódico", "electronic_conduction;interfacial_kinetics;colonization", "S01,S04", """
loading|m_cat,a|Carga de material depositado|kg/m2
thickness|L_cat,a|Espessura|m
coverage|f_cov,a|Cobertura superficial|1
binder_fraction|f_bind,a|Fração mássica de ligante|1
electronic_conductivity|sigma_cat,a|Condutividade eletrônica molhada|S/m
composition|x_cat,a|Fração de componente identificado|1
roughness|Ra_cat,a|Rugosidade|m
interfacial_rate|k_ET,a|Coeficiente efetivo de transferência eletrônica|m/s
stability_rate|k_deg,a|Taxa efetiva de degradação|1/s
"""),
"biofilm": ("Biofilme", "anode_biokinetics;biofilm_transfer;microbial_competition", "S04,S05,S08", """
thickness|L_b|Espessura hidratada|m
active_biomass|X_e|Densidade de biomassa eletroativa|kg dry biomass/m3
electroactive_fraction|f_e|Fração eletroativa da biomassa|1
max_uptake|q_max|Consumo máximo específico do substrato|mol/(kg dry biomass s)
half_saturation|K_S|Constante de meia saturação para substrato definido|mol/m3
biomass_yield|Y_XS|Rendimento de biomassa no substrato definido|kg dry biomass/mol
decay|k_d|Coeficiente de decaimento|1/s
conductivity|sigma_b|Condutividade efetiva do biofilme|S/m
substrate_diffusivity|D_eff,S|Difusividade efetiva do substrato|m2/s
oxygen_diffusivity|D_eff,O2|Difusividade efetiva de oxigênio|m2/s
ph_optimum|pH_opt|pH ótimo condicionado ao consórcio|1
activation_energy|E_act,bio|Energia de ativação local da cinética|J/mol
age|t_b|Idade/estado de maturação|s
"""),
"membrane": ("Membrana", "membrane_transport;ionic_path;acid_base;oxygen_crossover", "S02,S06", """
wet_area|A_m|Área de transporte molhada|m2
wet_thickness|L_m|Espessura hidratada|m
ionic_conductivity|kappa_m|Condutividade iônica nas condições de uso|S/m
area_specific_resistance|ASR_m|Resistência específica de área|Ohm m2
ion_exchange_capacity|IEC_m|Capacidade de troca iônica e base seca|mol charge/kg
fixed_charge|X_fix|Densidade volumétrica de carga fixa|mol charge/m3
water_uptake|w_m|Absorção mássica de água|kg/kg
swelling|f_sw|Razão de expansão e direção|1
oxygen_permeance|K_m,O2|Permeância ao oxigênio|mol/(m2 s Pa)
substrate_permeability|P_m,S|Coeficiente de permeabilidade ao substrato|m2/s
transport_number|t_i|Número de transporte da espécie identificada|1
degradation_rate|k_deg,m|Taxa efetiva de perda de função|1/s
"""),
"external_circuit": ("Circuito e alimentação/coleta", "electrical_closure;feeding_events;energy_collection", "S03,S05,S08,S11", """
load_resistance|R_ext|Resistência da carga externa|Ohm
contact_resistance|R_contact|Resistência de contato|Ohm
wire_resistance|R_wire|Resistência dos condutores|Ohm
feed_flow|Q_feed|Vazão de alimentação do meio|m3/s
feed_substrate|S_in|Concentração do substrato de entrada|mol/m3
feed_interval|dt_feed|Intervalo entre alimentações|s
external_capacitance|C_store|Capacitância de armazenamento|F
collector_efficiency|eta_collect|Eficiência do coletor em função da carga|1
parasitic_power|P_aux|Consumo de bombeamento/aeração/eletrônica|W
"""),
"cathode_chamber": ("Câmara catódica", "gas_balance;oxygen_supply;thermal_conditions", "S02,S07", """
liquid_volume|V_c|Volume líquido quando aplicável|m3
gas_volume|V_g,c|Volume gasoso controlado|m3
gas_pressure|p_g|Pressão total do gás|Pa
oxygen_fraction|y_O2|Fração molar de oxigênio|1
gas_flow|Q_g|Vazão volumétrica gasosa nas condições declaradas|m3/s
relative_humidity|RH|Umidade relativa|1
temperature|T_c|Temperatura|K
"""),
"catholyte": ("Meio catódico", "oxygen_supply;acid_base;ionic_path", "S02,S03,S06", """
dissolved_oxygen|C_O2,c|Oxigênio dissolvido|mol/m3
conductivity|kappa_c|Condutividade iônica|S/m
ph|pH_c|pH|1
buffer_total|C_buffer,c|Concentração total de tampão|mol/m3
alkalinity|Alk_c|Alcalinidade em equivalentes|mol charge/m3
oxygen_transfer|kLa_c|Coeficiente volumétrico de transferência de O2|1/s
ionic_strength|I_ion,c|Força iônica|mol/m3
acceptor_concentration|C_acc|Concentração de aceptor identificado|mol/m3
"""),
"cathode": ("Cátodo", "electronic_conduction;oxygen_supply;gas_diffusion_water_balance", "S02,S03,S07", """
geometric_area|A_c|Área geométrica|m2
electronic_conductivity|sigma_c|Condutividade eletrônica efetiva direcional|S/m
conduction_length|L_e,c|Percurso eletrônico|m
conduction_cross_section|A_e,c|Seção transversal de condução eletrônica|m2
gdl_thickness|L_GDL|Espessura da camada de difusão gasosa|m
open_porosity|epsilon_GDL|Porosidade aberta da camada de difusão|1
tortuosity|tau_GDL|Tortuosidade e convenção|1
water_saturation|s_w|Saturação líquida dos poros|1
oxygen_transfer|k_O2|Coeficiente efetivo de transporte de O2|m/s
"""),
"cathode_catalyst": ("Catalisador catódico", "cathodic_reaction;interfacial_kinetics;ageing", "S07", """
loading|m_cat,c|Carga de catalisador por área|kg/m2
composition|x_cat,c|Fração de componente identificado|1
wet_ecsa|A_ECSA,c|Área eletroquímica molhada|m2
exchange_current_density|j0_c|Densidade de corrente de troca e base de área|A/m2
transfer_coefficient|alpha_c|Coeficiente de transferência|1
electron_number|n_ORR|Número efetivo de elétrons da via ORR|1
peroxide_fraction|f_H2O2|Fração de peróxido medida e convenção|1
binder_fraction|f_bind,c|Fração mássica de ligante|1
decay_rate|k_deg,c|Taxa efetiva de desativação|1/s
""")}


def build():
    catalog=[]
    for order,(stage,(label,modules,source_ids,text)) in enumerate(STAGE_TEXT.items(),1):
        properties=[]
        for line in text.strip().splitlines():
            key,symbol,name,unit=line.split('|')
            properties.append({"id":stage+'.'+key,"symbol":symbol,"name_pt":name,"unit":unit,
                               "status":"planned_not_connected_to_predictor","missing_value":None,
                               "requires_method_and_conditions":True})
        catalog.append({"order":order,"id":stage,"name_pt":label,"candidate_modules":modules.split(';'),
                        "rationale_sources":source_ids.split(','),"properties":properties})
    (BASE/'sources.json').write_text(json.dumps(SOURCES,ensure_ascii=False,indent=2)+'\n')
    (BASE/'parameter_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    seeds=[]
    for sample,ssa,roughness,rough_sd,sigma,jmax in [('E1',263.4,19.33,.41,.04,3.6),('E2',6.6,22.38,2.98,.09,5.3),('E3',39.8,25.36,2.65,.17,5.8)]:
        seeds.append({"id":"S01-"+sample,"study_id":"10.1002/celc.202001568","leakage_group_id":"Braun2021-SiOC",
          "source_id":"S01","source_locator":"Sections 2.1, 2.2, Bioelectrochemical Experiments; Table 2",
          "status":"candidate","evidence_access":"full_text","rights_review":"pending","experimental_scope":"three_electrode_bes",
          "conditions":{"sample":sample,"culture":"Geobacter spp. enrichment","reactor_volume_m3":.00025,
             "substrate":"acetate","substrate_concentration_mol_m3":10,"working_potential_V":.2,
             "reference_electrode":"Ag/AgCl saturated KCl","reference_offset_V_vs_SHE":.197,
             "experimental_duration_days":32,"replicates":3,"raw_replicates_available_here":False},
          "features":{"bet_specific_area":{"value":ssa,"unit":"m2/g","method":"N2 BET at 77 K; specimen dried/powdered"},
             "roughness":{"value":roughness,"unit":"um","reported_plus_minus":rough_sd,"reported_uncertainty_type":"SD"},
             "electronic_conductivity":{"value":sigma,"unit":"S/cm","provenance":"Table 2, imported by authors from reference 17; source measurement conditions need recovery"}},
          "observations":[{"metric":"maximum_anode_current_density","value":jmax,"unit":"A/m2","kind":"measurement_derived",
                           "area_basis":"anode_geometric","locator":"Section 2.2: reported maxima across batch cycles","statistic":"reported_maximum","uncertainty":None}],
          "limitations":["Not complete MFC output","Covarying surface properties; no isolated causal coefficient","Not raw replicate records","BET is not wet ECSA or microbial accessible area"]})
    for tag,power,unc,ce_range in [('PEM',262,10,[.40,.55]),('noPEM',494,21,[.09,.12])]:
        seeds.append({"id":"S02-glucose-"+tag,"study_id":"10.1021/es0499344","leakage_group_id":"LiuLogan2004-air-cathode",
          "source_id":"S02","source_locator":"Institutional abstract, glucose experiment","status":"candidate",
          "evidence_access":"abstract","rights_review":"pending","experimental_scope":"full_cell_mfc",
          "conditions":{"substrate":"glucose","cathode_environment":"air","membrane":"PEM" if tag=='PEM' else 'none',
                        "peak_power_substrate_concentration":None,"reactor_volume":None,"replicates":None},
          "observations":[{"metric":"maximum_cell_power_density","value":power,"unit":"mW/m2","kind":"measurement_derived",
                           "area_basis":None,"locator":"Abstract: glucose peak power","uncertainty":unc,"uncertainty_type":"reported_plus_minus_unspecified"}],
          "reported_context":{"coulombic_efficiency_range":ce_range},
          "limitations":["Peak power and CE range not established as paired operating points","Area convention and complete methods pending","Do not reuse the wastewater-unit typo in source"]})
    for medium,an,ca,so in [('acetate_50mM_PBS',10.6,14.8,14),('domestic_wastewater',75,54,87)]:
        seeds.append({"id":"S03-"+medium,"study_id":"10.1021/acs.est.8b06004","leakage_group_id":"Rossi2019-EPS",
          "source_id":"S03","source_locator":"Publisher/institutional abstract","status":"candidate",
          "evidence_access":"abstract","rights_review":"pending","experimental_scope":"full_cell_mfc",
          "conditions":{"medium":medium,"cathode_diffusion_layer_porosity":.7,"full_geometry":None},
          "observations":[{"metric":metric,"value":val,"unit":"mOhm m2","kind":"fitted","area_basis":None,
                           "locator":"Abstract, EPS analysis","statistic":"reported_EPS_slope"} for metric,val in
                          [('eps_anode_areal_resistance',an),('eps_cathode_areal_resistance',ca),('eps_solution_areal_resistance',so)]],
          "limitations":["EPS slopes are not pure EIS Rct","Area convention pending full text","Different electrolytes alter electrode performance too"]})
    (BASE/'evidence_seed.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in seeds)+'\n')
    return {"stages":len(catalog),"properties":sum(len(x['properties']) for x in catalog),"sources":len(SOURCES),"candidate_records":len(seeds)}


if __name__=='__main__': print(json.dumps(build()))
