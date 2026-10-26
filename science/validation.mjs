/** Experimental evaluation helpers. No training is performed by these functions. */
const finite=x=>typeof x==='number'&&Number.isFinite(x);
export function provenanceComponents(records) {
  if(!Array.isArray(records)||records.length===0)throw new Error('records_required');
  const ids=new Set(),parents=records.map((_,i)=>i),seen=new Map();
  const find=i=>parents[i]===i?i:(parents[i]=find(parents[i]));
  const union=(a,b)=>{a=find(a);b=find(b);if(a!==b)parents[Math.max(a,b)]=Math.min(a,b);};
  records.forEach((r,i)=>{
    if(!r.id||ids.has(r.id))throw new Error('unique_record_id_required');ids.add(r.id);
    if(!r.study_id||!r.leakage_group_id)throw new Error('study_and_leakage_group_required');
    for(const key of ['study_id','reactor_id','family_id','leakage_group_id']){
      const values=Array.isArray(r[key])?r[key]:r[key]?[r[key]]:[];
      for(const value of values){if(typeof value!=='string'||!value.trim())throw new Error('invalid_provenance_identifier');const token=key+':'+value;if(seen.has(token))union(i,seen.get(token));else seen.set(token,i);}
    }
  });
  const groups=new Map();records.forEach((r,i)=>{const root=find(i);if(!groups.has(root))groups.set(root,[]);groups.get(root).push(r.id);});
  return [...groups.values()].map(members=>members.sort()).sort((a,b)=>a[0].localeCompare(b[0]));
}
export function groupedHoldout(records,holdoutRecordIds) {
  const components=provenanceComponents(records),requested=new Set(holdoutRecordIds);
  if(requested.size===0)throw new Error('explicit_holdout_required');
  if([...requested].some(id=>!records.some(r=>r.id===id)))throw new Error('unknown_holdout_record');
  const held=new Set(components.filter(g=>g.some(id=>requested.has(id))).flat());
  const train=records.filter(r=>!held.has(r.id)),test=records.filter(r=>held.has(r.id));
  if(train.length===0||test.length===0)throw new Error('independent_train_and_test_groups_required');
  return {train,test,components,expanded_holdout_ids:[...held].sort(),strategy:'connected_provenance_components_before_any_preprocessing'};
}
export function errorMetrics(pairs,{unit,origin='experimental',minimumIndependentGroups=2}={}) {
  if(!unit||typeof unit!=='string')throw new Error('physical_unit_required');
  if(!Array.isArray(pairs)||pairs.length===0)return {status:'insufficient_data',unit,n:0,mae:null,rmse:null};
  if(origin!=='experimental')return {status:'verification_only_not_experimental_validation',unit,n:pairs.length,mae:null,rmse:null};
  if(pairs.some(p=>!finite(p.observed)||!finite(p.predicted)||!p.leakage_group_id))throw new Error('finite_paired_observations_and_groups_required');
  const groups=new Set(pairs.map(p=>p.leakage_group_id));
  if(groups.size<minimumIndependentGroups)return {status:'insufficient_independent_groups',unit,n:pairs.length,independent_groups:groups.size,mae:null,rmse:null};
  const errors=pairs.map(p=>p.predicted-p.observed);
  return {status:'computed_on_supplied_experimental_pairs',unit,n:pairs.length,independent_groups:groups.size,mae:errors.reduce((s,x)=>s+Math.abs(x),0)/errors.length,rmse:Math.sqrt(errors.reduce((s,x)=>s+x*x,0)/errors.length),bias:errors.reduce((s,x)=>s+x,0)/errors.length,
    limitation:'Caller must certify held-out predictions, experimental access, consistent units/bases and independent provenance; this function does not perform that review.'};
}
export function intervalMetrics(pairs,{unit,nominalCoverage=0.9,origin='experimental'}={}) {
  if(!unit)throw new Error('physical_unit_required');
  if(!finite(nominalCoverage)||nominalCoverage<=0||nominalCoverage>=1)throw new Error('invalid_nominal_coverage');
  if(!Array.isArray(pairs)||pairs.length===0||origin!=='experimental')return {status:'insufficient_experimental_data',unit,coverage:null,mean_width:null};
  if(pairs.some(p=>![p.observed,p.lower,p.upper].every(finite)||p.lower>p.upper||!p.leakage_group_id))throw new Error('invalid_interval_observation');
  const groups=new Set(pairs.map(p=>p.leakage_group_id));
  if(groups.size<2)return {status:'insufficient_independent_groups',unit,coverage:null,mean_width:null};
  return {status:'computed_on_supplied_experimental_intervals',unit,n:pairs.length,independent_groups:groups.size,nominal_coverage:nominalCoverage,coverage:pairs.filter(p=>p.observed>=p.lower&&p.observed<=p.upper).length/pairs.length,mean_width:pairs.reduce((s,p)=>s+p.upper-p.lower,0)/pairs.length};
}
