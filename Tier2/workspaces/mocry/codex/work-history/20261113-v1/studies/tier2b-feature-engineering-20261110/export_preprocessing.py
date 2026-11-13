"""Export immutable normalizers and exact selected checkpoint pointers."""
import json,hashlib,shutil,importlib.util
import numpy as np,pandas as pd
from features import ROOT,TARGETS

child=ROOT/'strict-confirmation';spec=importlib.util.spec_from_file_location('export_features',child/'features.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out=child/'preprocessing';out.mkdir(exist_ok=True);plan=json.loads((child/'PLAN_FROZEN.json').read_text())['plan'];package=[]
for r in plan:
    groups=r['groups'].split('+');f,x,data,mean,scale,names=m.load(groups);extra=[]
    for g in groups:
        if g=='balance':
            y=f[TARGETS].to_numpy();b=(y[:,0]-y[:,1])/scale[0];v=pd.Series(b);extra.extend([b,y[:,1]/np.maximum(y[:,0],1000),np.maximum(b,0),np.maximum(-b,0),v.rolling(7,min_periods=1).mean(),v.rolling(28,min_periods=1).mean()])
        else:
            frame=pd.read_csv(child/'features'/(g+'.csv'),parse_dates=['date']).set_index('date').reindex(f.index);extra.extend(frame.to_numpy().T)
    E=pd.DataFrame(np.column_stack(extra)).ffill().fillna(0).to_numpy();fit=(f.index>='2022-01-01')&(f.index<='2024-12-30');mu=E[fit].mean(0);sd=E[fit].std(0);sd[sd<1e-10]=1
    assert np.array_equal(((E-mu)/sd).astype(np.float32),x[:,8:])
    tag=r['target']+'_'+r['family']+'_'+str(r['budget'])+'_'+r['groups'];path=out/(tag+'.json')
    record={**r,'target_mean':mean.tolist(),'target_std':scale.tolist(),'extra_feature_names':names[8:],'extra_mean':mu.tolist(),'extra_std':sd.tolist(),'input_scaler_origin_fit_start':'2022-01-01','input_scaler_origin_fit_end':'2024-12-30','target_scaler_label_fit_end':'2024-12-31','base_encoding':'First3: standardized observed generation,demand,price; then observed-day weekday sine/cosine, yearly sine/cosine, weekend.','groups_csv':{g:hashlib.sha256((child/'features'/(g+'.csv')).read_bytes()).hexdigest() for g in groups if (child/'features'/(g+'.csv')).exists()}}
    path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cases=[]
    for seed in [17,29,43]:
        cp=child/'models'/(tag+'_s'+str(seed)+'.pt');cases.append({'seed':seed,'checkpoint':cp.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(cp.read_bytes()).hexdigest()})
    package.append({**r,'preprocessing':path.relative_to(ROOT).as_posix(),'checkpoints':cases})
(ROOT/'RECOMMENDED_NEURAL_MODELS.json').write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
fuel=ROOT.parent/'data-repair-20261104-v2/data/daily_generation_by_fuel.csv';shutil.copy2(fuel,ROOT/'inputs/course_generation_by_fuel.csv')
print('Exported6normalizers,18checkpoint pointers and frozen raw fuel inputs.')
