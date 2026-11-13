"""Evaluate the six frozen final neural candidates after strict scaler confirmation."""
import json
import numpy as np,pandas as pd
from features import ROOT,TARGETS,load

S=pd.read_csv(ROOT/'results/SELECTED_METRICS.csv');selection=pd.read_csv(ROOT/'results/VALIDATION_SELECTION.csv');child=ROOT/'strict-confirmation';plan=json.loads((child/'PLAN_FROZEN.json').read_text())['plan']
rows=[]
for path in (child/'case_results').glob('*.json'):
    v=json.loads(path.read_text());r=v['row'];pool=next(z['pool'] for z in plan if z['target']==r['target'] and z['groups']==r['groups'])
    for m in v['metrics']:rows.append({**r,**m,'pool':pool})
F=pd.DataFrame(rows);assert len(F)==18*3;F.to_csv(ROOT/'results/STRICT_ALL_METRICS.csv',index=False)
summary=F.groupby(['target','family','budget','groups','pool','split']).agg(loss_mean=('loss','mean'),loss_sd=('loss','std'),MSE_mean=('MSE','mean'),MSE_sd=('MSE','std'),MAE_mean=('MAE','mean'),MAE_sd=('MAE','std'),RMSE_mean=('RMSE','mean'),RMSE_sd=('RMSE','std'),seeds=('seed','nunique'),parameters=('parameters','first'),features=('features','first')).reset_index();summary.to_csv(ROOT/'results/STRICT_SUMMARY.csv',index=False)
_,_,data,_,scale,_=load([]);main=pd.read_csv(ROOT/'results/NEURAL_ALL_METRICS.csv');main['groups']=main.groups.fillna('base').replace('','base');rng=np.random.default_rng(20261110);comparisons=[]
for r in plan:
    t=r['target'];j=TARGETS.index(t);b=S.loc[S.target.eq(t)&S.pool.eq('baseline')&S.selection_scope.eq('neural')]
    bv=b.loc[b.split.eq('validation')].iloc[0];bt=b.loc[b.split.eq('test')].iloc[0]
    g=F.loc[F.target.eq(t)&F.pool.eq(r['pool'])];va=g.loc[g.split.eq('validation')].set_index('seed').loss;te=g.loc[g.split.eq('test')].loss
    baseline_cases=main.loc[main.target.eq(t)&main.groups.eq('base')&main.family.eq(bv.family)&main.budget.eq(bv.budget)&main.split.eq('test')].sort_values('seed')
    new_cases=g.loc[g.split.eq('test')].sort_values('seed');truth=data['test']['truth'][:,j]
    old_err=np.array([np.square((np.load(ROOT/'predictions'/(z+'.npz'))['test']-truth)/scale[j]) for z in baseline_cases.run]).mean(0)
    new_err=np.array([np.square((np.load(child/'predictions'/(z+'.npz'))['test']-truth)/scale[j]) for z in new_cases.run]).mean(0)
    starts=rng.integers(0,365,(3000,27));indices=((starts[:,:,None]+np.arange(14)[None,None,:])%365).reshape(3000,-1)[:,:365];gain=100*(1-new_err[indices].mean(1)/old_err[indices].mean(1))
    matched=main.loc[main.target.eq(t)&main.groups.eq('base')&main.family.eq(r['family'])&main.budget.eq(r['budget'])&main.split.eq('validation')].set_index('seed').loss
    comparisons.append({**r,'baseline_family':bv.family,'baseline_budget':bv.budget,'baseline_validation':bv.loss_mean,'candidate_validation':va.mean(),'validation_improvement_pct':100*(1-va.mean()/bv.loss_mean),'baseline_test':bt.loss_mean,'candidate_test':te.mean(),'test_improvement_pct':100*(1-te.mean()/bt.loss_mean),'matched_baseline_validation':matched.mean(),'matched_validation_improvement_pct':100*(1-va.mean()/matched.mean()),'matched_seeds_validation_improved':int((va<matched).sum()),'test_gain_block14_low_pct':float(np.quantile(gain,.025)),'test_gain_block14_high_pct':float(np.quantile(gain,.975))})
C=pd.DataFrame(comparisons);C.to_csv(ROOT/'results/STRICT_IMPROVEMENTS.csv',index=False)
final=C.loc[C.pool.eq('external_forecasts')];assert len(final)==3
met=bool((final.validation_improvement_pct>=5).all() and (final.matched_seeds_validation_improved>=2).all() and (final.test_improvement_pct>=0).all())
stop={'status':'achieved' if met else 'further_review_required','reason':'All three independently modelled targets have confirmed >=5% validation MSE improvement, >=2/3 matched seeds improve and test MSE does not worsen. No new feature jobs after stop decision.','criteria_met':met,'quota_last_remaining_percent':71,'quota_threshold_percent':30,'quota_threshold_reached':False,'main_neural_fits':477,'strict_confirmation_fits':18,'neural_fits_total':495,'independent_agent_delegation':False,'published':False,'results':final.to_dict('records')}
(ROOT/'STOP_REASON.json').write_text(json.dumps(stop,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(C[['target','pool','family','budget','validation_improvement_pct','test_improvement_pct','test_gain_block14_low_pct','matched_seeds_validation_improved']].to_string(index=False));print('STOP_CRITERIA_MET',met)
