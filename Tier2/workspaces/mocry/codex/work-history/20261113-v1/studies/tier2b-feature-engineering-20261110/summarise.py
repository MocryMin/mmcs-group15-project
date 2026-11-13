import json
import numpy as np,pandas as pd
from features import ROOT

rows=[]
for p in (ROOT/'case_results').glob('*.json'):
    v=json.loads(p.read_text());r=v['row']
    for m in v['metrics']:rows.append({**r,**m})
if rows:
    f=pd.DataFrame(rows);f.to_csv(ROOT/'results/NEURAL_ALL_METRICS.csv',index=False);val=f.loc[f.split.eq('validation')].copy();val['groups']=val.groups.fillna('base').replace('','base')
    summary=val.groupby(['target','family','budget','groups'],dropna=False).agg(val_mean=('loss','mean'),val_sd=('loss','std'),seeds=('seed','nunique')).reset_index();summary.to_csv(ROOT/'results/NEURAL_VALIDATION.csv',index=False)
    baseline=summary.loc[summary.groups.eq('base'),['target','family','budget','val_mean']].rename(columns={'val_mean':'base_val'})
    comparison=summary.merge(baseline,on=['target','family','budget']);comparison['improvement_pct']=100*(1-comparison.val_mean/comparison.base_val);comparison.to_csv(ROOT/'results/NEURAL_FEATURE_COMPARISON.csv',index=False)
    print('NEURAL fits',len(rows)//3,'best val by feature group:')
    print(comparison.sort_values('val_mean').groupby(['target','groups'],sort=False).first().reset_index()[['target','groups','family','budget','seeds','val_mean','improvement_pct']].to_string(index=False))
classic=[]
for p in (ROOT/'results').glob('CPU_*.csv'):
    if p.name.startswith('CPU_SELECTION_'):continue
    classic.append(pd.read_csv(p))
if classic:
    c=pd.concat(classic);c.to_csv(ROOT/'results/CLASSICAL_ALL_METRICS.csv',index=False);v=c.loc[c.split.eq('validation')].copy();base=v.loc[v.groups.eq('base'),['target','family','loss']].rename(columns={'loss':'base_val'});v=v.merge(base,on=['target','family']);v['improvement_pct']=100*(1-v.loss/v.base_val);v.to_csv(ROOT/'results/CLASSICAL_FEATURE_COMPARISON.csv',index=False)
    print('CLASSICAL validation:')
    print(v.sort_values('loss').groupby(['target','groups'],sort=False).first().reset_index()[['target','groups','family','loss','improvement_pct']].to_string(index=False))
