"""Checkpoint, complete-step logs, source timing and future-perturbation audit."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('MKL_NUM_THREADS','2');os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
import argparse,json,hashlib,shutil,tempfile
from pathlib import Path
import numpy as np,pandas as pd,torch
import features
from features import ROOT,TARGETS
from model import Predictor

p=argparse.ArgumentParser();p.add_argument('--strict',action='store_true');a=p.parse_args();root=ROOT/'strict-confirmation' if a.strict else ROOT
if a.strict:
    import importlib.util
    spec=importlib.util.spec_from_file_location('strict_features',root/'features.py');strict_features=importlib.util.module_from_spec(spec);spec.loader.exec_module(strict_features);loader=strict_features.load
else:loader=features.load
torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.cuda.set_per_process_memory_fraction(.6)
max_prediction=0.;max_metric=0.;cases=0;log_rows=0;updates=0;feature_cache={};parameter_errors=[]
for path in sorted((root/'case_results').glob('*.json')):
    v=json.loads(path.read_text());r=v['row'];groups=tuple(g for g in r['groups'].split('+') if g);tag=r['run']
    for name,digest in v['signature'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,(tag,name)
    if groups not in feature_cache:feature_cache[groups]=loader(groups)
    f,x,data,mean,scale,names=feature_cache[groups];j=TARGETS.index(r['target']);cp=torch.load(root/r['checkpoint'],weights_only=True)
    model=Predictor(r['family'],j,x.shape[1],int(r['budget'])).cuda();model.load_state_dict(cp['state_dict']);model.eval();assert cp['features']==names and cp['inputs']==len(names)
    count=sum(p.numel() for p in model.parameters());assert count==r['parameters'];parameter_errors.append(abs(count-r['budget'])/r['budget'])
    stored=np.load(root/'predictions'/(tag+'.npz'));chunk=128 if r['family']=='Transformer' and r['lookback']>=91 else 2048
    with torch.inference_mode():
        for part,d in data.items():
            xx=torch.tensor(np.stack([x[t-r['lookback']+1:t+1] for t in d['origins']]),device='cuda')
            raw=torch.cat([model(b) for b in xx.split(chunk)]).cpu().numpy().ravel().astype(float)*scale[j]+mean[j]
            difference=float(np.max(abs(raw-stored[part])/scale[j]));max_prediction=max(max_prediction,difference)
            err=stored[part]-d['truth'][:,j];m=next(z for z in v['metrics'] if z['split']==part)
            values={'loss':float(np.mean((err/scale[j])**2)),'MAE':float(np.mean(abs(err))),'RMSE':float(np.sqrt(np.mean(err**2)))}
            max_metric=max(max_metric,*[abs(values[k]-m[k])/max(1,abs(values[k])) for k in values]);assert len(raw)=={'train':1096,'validation':243,'test':365}[part]
    log=pd.read_csv(root/'step_logs'/(tag+'.csv'));assert np.array_equal(log.step,np.arange(r['updates']+1));assert r['updates']==18*r['epochs_ran'];assert np.isfinite(log[['train_loss','validation_loss','test_loss']]).all().all()
    best=float('inf');beststep=None
    for rr in log.itertuples():
        changed=rr.validation_loss<best-1e-5
        assert bool(rr.improved)==changed
        if changed:best=rr.validation_loss;beststep=int(rr.step)
    assert beststep==int(r['step'])==cp['step'] and abs(best-cp['validation_loss'])<1e-12
    log_rows+=len(log);updates+=r['updates'];cases+=1
assert max_prediction<1e-5 and max_metric<1e-12

timing=[]
for filename in ['gfs_temperature_day2.json','jma_wind_day2.json','jma_solar_proxy_day2.json']:
    d=json.loads((ROOT/'research'/filename).read_text());assert d['offset_hours']==48
    timing.append({'source':filename,'lead_hours':48,'latest_possible_issue_hours_before_end_of_origin':24,'locations':len(d['locations'])})
for filename in ['neso_demand_day_ahead.json','neso_wind_day_ahead.json']:
    d=json.loads((ROOT/'research'/filename).read_text());valid=pd.to_datetime([r['date'] for r in d['records']],utc=True);issue=pd.to_datetime([r['latest_issue'] for r in d['records']],utc=True)
    assert (issue<valid).all();timing.append({'source':filename,'retained_days':len(valid),'all_retained_issues_before_target_day00UTC':True,'future_issues_rejected':d['future_or_bad_issue_rejected']})

causal_checks=[]
if not a.strict:
    # Mutate only copies: live experiment data are never changed.
    cutoff=pd.Timestamp('2025-04-30');original_root=features.ROOT
    with tempfile.TemporaryDirectory(prefix='mmcs-fe-causality-') as tmp:
        temp=Path(tmp);shutil.copytree(ROOT/'inputs',temp/'inputs');shutil.copytree(ROOT/'features',temp/'features');shutil.copy2(ROOT/'BASELINE_FROZEN.json',temp/'BASELINE_FROZEN.json')
        f=pd.read_csv(temp/'inputs/model_daily.csv',parse_dates=['date']);f.loc[f.date>cutoff,TARGETS]=f.loc[f.date>cutoff,TARGETS]*100+100000;f.to_csv(temp/'inputs/model_daily.csv',index=False)
        for csv in (temp/'features').glob('*.csv'):
            frame=pd.read_csv(csv,parse_dates=['date']);frame.loc[frame.date>cutoff,frame.columns.difference(['date'])]=123456.;frame.to_csv(csv,index=False)
        try:
            for groups,original in feature_cache.items():
                features.ROOT=temp;new=features.load(groups);features.ROOT=original_root
                prefix=original[0].index<=cutoff;assert np.array_equal(original[1][prefix],new[1][prefix]),groups;causal_checks.append('+'.join(groups) or 'base')
        finally:features.ROOT=original_root
else:
    assert np.array_equal(features.load([])[1],loader([])[1])
    assert "(f.index<='2024-12-30')" in (root/'features.py').read_text()
record={'passed':True,'cases_replayed':cases,'all_full_split_metrics_recomputed':True,'complete_evaluation_rows_checked':log_rows,'training_updates_checked':updates,'each_update_has_all3_full_splits':True,'val_only_checkpoint_selection_verified':True,'max_normalized_checkpoint_prediction_difference':max_prediction,'max_relative_metric_difference':max_metric,'max_fractional_parameter_budget_difference':max(parameter_errors),'source_timing':timing,'future_observation_and_future_feature_perturbation_groups':causal_checks,'strict_confirmation':a.strict,'strict_baseline_inputs_bit_identical_to_original':True if a.strict else None,'external_calendar_special_announcement_vintage':'not reconstructed; known-by-day-before assumption','scope':'Local computational replay and timing audit, not an independent agent review.'}
(root/'results/AUDIT_NEURAL.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in record.items() if k not in ['source_timing','future_observation_and_future_feature_perturbation_groups']},ensure_ascii=False))
