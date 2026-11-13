"""Validation-only selection; hold test values out of ranking and eligibility."""
import argparse,json,hashlib
import numpy as np,pandas as pd
from features import ROOT,TARGETS,load

parser=argparse.ArgumentParser();parser.add_argument('--final',action='store_true');args=parser.parse_args()
prefix='' if args.final else 'PROVISIONAL_'
F=pd.read_csv(ROOT/'results/NEURAL_ALL_METRICS.csv');F['groups']=F.groups.fillna('base').replace('','base')
C=pd.read_csv(ROOT/'results/CLASSICAL_ALL_METRICS.csv');F['kind']='neural';C['kind']='classical';C['budget']=0;C['seed']='det'
fields=['target','family','budget','groups','kind','split'];stats=[]
for keys,g in pd.concat([F,C],ignore_index=True).groupby(fields):
    r=dict(zip(fields,keys));r['seeds']=g.seed.nunique()
    for metric in ['loss','MAE','RMSE']:
        r[metric+'_mean']=float(g[metric].mean());r[metric+'_sd']=float(g[metric].std(ddof=1)) if len(g)>1 else None
    stats.append(r)
S=pd.DataFrame(stats);S.to_csv(ROOT/'results'/(prefix+'ALL_SUMMARY.csv'),index=False)
eligible=S.loc[S.split.eq('validation')&(S.kind.eq('classical')|S.seeds.eq(3))&~S.groups.str.contains('neso_wind')].copy()
selections=[]
for target in TARGETS:
    for pool in ['baseline','self_features','external_forecasts']:
        p=eligible.loc[eligible.target.eq(target)]
        if pool=='baseline':p=p.loc[p.groups.eq('base')]
        elif pool=='self_features':p=p.loc[~p.groups.str.contains('neso_')&~p.groups.eq('base')]
        else:p=p.loc[p.groups.str.contains('neso_demand')]
        for kind in ['neural','all_methods']:
            q=p.loc[p.kind.eq('neural')] if kind=='neural' else p
            if q.empty:continue
            r=q.sort_values(['loss_mean','family','budget','groups']).iloc[0].to_dict();r['pool']=pool;r['selection_scope']=kind;selections.append(r)
selection=pd.DataFrame(selections)
# Persist chosen identities before retrieving any test metric rows.
selection.to_csv(ROOT/'results'/(prefix+'VALIDATION_SELECTION.csv'),index=False)
lookup=[]
for r in selections:
    q=S.loc[S.target.eq(r['target'])&S.family.eq(r['family'])&S.budget.eq(r['budget'])&S.groups.eq(r['groups'])&S.kind.eq(r['kind'])]
    for rr in q.to_dict('records'):lookup.append({**rr,'pool':r['pool'],'selection_scope':r['selection_scope']})
L=pd.DataFrame(lookup);L.to_csv(ROOT/'results'/(prefix+'SELECTED_METRICS.csv'),index=False)
_,_,data,mean,scale,_=load([])
def predictions(r,part):
    if r['kind']=='classical':return np.load(ROOT/'predictions'/('CPU_'+r['target']+'_'+r['family']+'_'+r['groups']+'.npz'))[part][None,:]
    paths=F.loc[F.target.eq(r['target'])&F.family.eq(r['family'])&F.budget.eq(r['budget'])&F.groups.eq(r['groups'])&F.split.eq(part)].sort_values('seed').run
    return np.array([np.load(ROOT/'predictions'/(tag+'.npz'))[part] for tag in paths])
comparisons=[];rng=np.random.default_rng(20261110)
for target in TARGETS:
    for scope in ['neural','all_methods']:
        q=selection.loc[selection.target.eq(target)&selection.selection_scope.eq(scope)]
        base=q.loc[q.pool.eq('baseline')].iloc[0].to_dict()
        for r in q.loc[~q.pool.eq('baseline')].to_dict('records'):
            truth=data['test']['truth'][:,TARGETS.index(target)];den=scale[TARGETS.index(target)]
            eb=np.square((predictions(base,'test')-truth)/den).mean(0);en=np.square((predictions(r,'test')-truth)/den).mean(0)
            starts=rng.integers(0,len(truth),(3000,int(np.ceil(len(truth)/14))));indices=(starts[:,:,None]+np.arange(14)[None,None,:])%len(truth);indices=indices.reshape(3000,-1)[:,:len(truth)]
            gains=100*(1-en[indices].mean(1)/eb[indices].mean(1))
            matched=None;seed_improved=None
            if r['kind']=='neural':
                matched=eligible.loc[eligible.target.eq(target)&eligible.family.eq(r['family'])&eligible.budget.eq(r['budget'])&eligible.groups.eq('base')].iloc[0].loss_mean
                feat=F.loc[F.target.eq(target)&F.family.eq(r['family'])&F.budget.eq(r['budget'])&F.groups.eq(r['groups'])&F.split.eq('validation')].set_index('seed').loss
                old=F.loc[F.target.eq(target)&F.family.eq(r['family'])&F.budget.eq(r['budget'])&F.groups.eq('base')&F.split.eq('validation')].set_index('seed').loss
                seed_improved=int((feat<old).sum())
            comparisons.append({'target':target,'pool':r['pool'],'selection_scope':scope,'baseline_kind':base['kind'],'baseline_family':base['family'],'baseline_budget':base['budget'],'candidate_kind':r['kind'],'candidate_family':r['family'],'candidate_budget':r['budget'],'groups':r['groups'],'base_validation':base['loss_mean'],'new_validation':r['loss_mean'],'validation_improvement_pct':100*(1-r['loss_mean']/base['loss_mean']),'test_base':float(eb.mean()),'test_new':float(en.mean()),'test_improvement_pct':100*(1-en.mean()/eb.mean()),'test_gain_block14_low_pct':float(np.quantile(gains,.025)),'test_gain_block14_high_pct':float(np.quantile(gains,.975)),'matched_family_budget_baseline_validation':matched,'matched_family_budget_validation_improvement_pct':None if matched is None else 100*(1-r['loss_mean']/matched),'matched_seeds_validation_improved':seed_improved})
comparison=pd.DataFrame(comparisons);comparison.to_csv(ROOT/'results'/(prefix+'IMPROVEMENTS.csv'),index=False)
baseline=F.loc[F.groups.eq('base')];assert len(baseline)==81*3 and baseline.run.nunique()==81
baseline.to_csv(ROOT/'results/BASELINE_ALL_METRICS.csv',index=False)
parameters=baseline.loc[baseline.split.eq('validation')].groupby(['family','budget']).parameters.first().reset_index();parameters.to_csv(ROOT/'results/BASELINE_ACTUAL_PARAMETERS.csv',index=False)
registry={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['inputs','features','research'] for p in (ROOT/folder).glob('*') if p.is_file()}
(ROOT/'results'/(prefix+'FEATURE_MANIFEST.json')).write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Completed neural fits',F.run.nunique(),'classical rows',len(C));print(comparison[['target','pool','selection_scope','candidate_family','candidate_budget','groups','validation_improvement_pct','test_improvement_pct','test_gain_block14_low_pct','matched_seeds_validation_improved']].to_string(index=False))
