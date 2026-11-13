"""Retain strong earlier deterministic baselines in the new baseline pool."""
import json,hashlib
import numpy as np,pandas as pd
from features import ROOT,TARGETS
src=ROOT.parent/'tier2b-unified-forecast-comparison-20261110'
assert (src/'inputs/model_daily.csv').read_bytes()==(ROOT/'inputs/model_daily.csv').read_bytes()
all_scores=pd.read_csv(src/'results/ALL_METRICS.csv');rows=[];manifest=[]
for old,family in [('T_fixed_CalendarResidualAR','CalendarAR'),('T_fixed_RidgeLevel','LagRidge'),('T_fixed_RidgeResidual','LagRidgeResidual'),('T_fixed_OLSLevel','OLS'),('T_fixed_Persistence','Persistence'),('T_fixed_Seasonal7','Seasonal7'),('T_fixed_Mean28','Mean28')]:
    p=src/'predictions'/(old+'.npz');pred=np.load(p);manifest.append({'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    for j,t in enumerate(TARGETS):
        np.savez_compressed(ROOT/'predictions'/('CPU_'+t+'_'+family+'_base.npz'),**{part:pred['det__'+part][:,j] for part in ['train','validation','test']})
        g=all_scores.loc[all_scores.method.eq(old)&all_scores.target.eq(t)]
        for r in g.itertuples():rows.append({'target':t,'family':family,'groups':'base','features':'reference','parameter':'frozen prior val choice','transform':'raw','split':r.split,'loss':r.loss,'MAE':r.MAE,'RMSE':r.RMSE})
pd.DataFrame(rows).to_csv(ROOT/'results/CPU_REFERENCE_base.csv',index=False)
(ROOT/'BASELINE_REFERENCES.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
for name in ['neso_demand_day_ahead.json','neso_wind_day_ahead.json']:
    p=ROOT/'research'/name;v=json.loads(p.read_text());headers=v.get('source_headers',{});v['source_headers']={k:x for k,x in headers.items() if k.lower() not in {'set-cookie','cookie','authorization','proxy-authorization'}}
    p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
print('Imported7 strong classical references; sanitized source headers.')
