"""Deterministic raster digitization, not raw experimental data or independent validation.
Coordinates refer to lossless figure 4 image extracted by pdfimages from S18.pdf p10.
No smoothing, model-fitting, synthetic points, or interpolation between sampled columns.
"""
from pathlib import Path
import numpy as np,json,csv,hashlib
from PIL import Image
ROOT=Path(__file__).parent
p=ROOT/'documents/S18_plot-001.png'
a=np.asarray(Image.open(p).convert('RGB'))
# Panel 4a linear axes: current 0..400 mA/m2 from x=115..571,
# voltage 0..1000 mV from y=251..60. A 2px locator bound is declared.
x0,x400,y0,y1000=115,571,251,60
rows=[]
for j_mA in range(0,351,25):
 x=round(x0+j_mA*(x400-x0)/400)
 colors=a[65:248,x,:]
 ys=np.where((colors[:,2]>180)&(colors[:,0]<90)&(colors[:,1]<125))[0]+65
 # OCV at origin has adjacent axis; tolerate dark-blue row down to y=65.
 if len(ys)==0:continue
 y=float(np.median(ys))
 rows.append({'current_density_A_m2':j_mA/1000,'cell_voltage_V':round((y0-y)/(y0-y1000),5),
 'pixel_x':x,'pixel_y':y,'pixel_count':len(ys),'voltage_digitization_bound_V':round(3/(y0-y1000),5),
 'current_density_digitization_bound_A_m2':round(2*0.4/(x400-x0),6)})
meta={'id':'S18-CC-pristine-figure4a-digitized','source_id':'S18','doi':'10.3390/en17143574',
 'source_locator':'Figure 4a, p10; lossless embedded image from PDF','leakage_group_id':'Salvian2024-Surrey-30mL',
 'experimental_scope':'full_cell_mfc','evidence_kind':'digitized_published_curve','status':'candidate',
 'training_eligible':False,'raw_experimental_data':False,'area_basis':'anode_geometric_reported; numeric normalization 12cm2 inferred from absolute/density pairs',
 'area_m2':None,'replicate_count_for_polarization':None,'normalization_issue':'2x3cm felt has 6cm2 single-face projection; published I/j pairs imply 12cm2. Do not turn j into I until resolved.',
 'conditions':{'anolyte_volume_m3':30e-6,'substrate':'sodium acetate','substrate_g_L':0.6,'temperature_K':294.15,'temperature_plus_minus_K':2,
 'pH':7.2,'pH_plus_minus':0.2,'conductivity_S_m':0.1,'conductivity_plus_minus_S_m':0.02,
 'chambers':1,'cathode_environment':'ambient_air','membrane':'not_described','cathode':'CC supplied with Pt/C coating',
 'cathode_age_days':0,'anode_biofilm_age_days':120,'protocol':'two-electrode LSV at 0.5mV/s after 3h OCP'},
 'axis_calibration':{'x_px':[x0,x400],'x_values_mA_m2':[0,400],'y_px':[y0,y1000],'y_values_mV':[0,1000]},
 'source_image_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'limitations':['Single study curve; all points form one provenance group.','Raster bounds are reading uncertainty, not biological or total model uncertainty.',
 'LSV transient/hysteresis must be assessed; CP curve includes non-monotonic scan.','No independent study holdout or parameter identifiability established.'],
 'points':rows}
(ROOT/'S18_CC_curve_digitized.json').write_text(json.dumps(meta,indent=2))
with (ROOT/'S18_CC_curve_digitized.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
print(json.dumps(rows,indent=2))
