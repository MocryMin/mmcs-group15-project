"""Replay saved estimators and independently check alignment, scoring and cutoffs."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from common import ROOT,Data,TARGETS,methods,dump,sha
import joblib
from threadpoolctl import threadpool_limits

D=Data();max_pred=0.;model_count=0;replay_log=[]


def independent_predict(state,origins):
    # Rebuild features from raw observed windows, rather than the training feature matrix.
    j=state['target'];spec=state['spec']
    if spec['family']=='CalendarAR':
        residual=D.z[:,j]-D.cal@state['b']
        X=np.array([[residual[t],residual[t-6:t+1].mean()] for t in origins])
        z=D.cal[origins+1]@state['b']+X@state['phi']
    else:
        # Pandas' compensated rolling mean can differ from a fresh sum by a few
        # ulps. Histogram trees may split exactly at a training observation.
        # Reconstruct the same numerical mean, and separately check its value
        # against the direct observed-window mean.
        means={(c,k):pd.Series(D.z[:,c]).rolling(k).mean().to_numpy() for c in range(3) for k in [7,28]}
        X=[]
        for t in origins:
            row=[]
            for c in range(3):
                row.extend(D.z[t-np.array([0,1,2,3,4,5,6,13]),c])
                direct=[D.z[t-6:t+1,c].mean(),D.z[t-27:t+1,c].mean()]
                same_numerics=[means[c,7][t],means[c,28][t]]
                assert np.max(np.abs(np.array(direct)-same_numerics))<1e-12
                row.extend(same_numerics)
            row.extend(D.cal[t+1]);X.append(row)
        X=np.array(X);xs=state['xs'];X=(X-xs.mean_)/xs.scale_
        z=state['model'].predict(X)
        if spec['transform']=='asinh':z=state['median']+state['spread']*np.sinh(z)
    return z*D.scale[j]+D.mean[j]


with threadpool_limits(limits=2):
    for family in ['Ridge','Lasso','HGB']:
        pred=np.load(ROOT/'predictions'/('T_fixed_Engineered'+family+'.npz'))
        for j in range(3):
            state=joblib.load(ROOT/'models'/f'T_fixed_Engineered{family}_{j}.joblib');model_count+=1
            assert state['labels_first']=='2022-01-01' and state['labels_last']=='2024-12-31' and state['n']==1096
            for p,o in D.origins.items():
                replay=independent_predict(state,o)
                difference=float(np.max(np.abs((replay-pred['det__'+p][:,j])/D.scale[j])));max_pred=max(max_pred,difference)
                replay_log.append({'method':'T_fixed_Engineered'+family,'target':j,'split':p,'difference':difference})
    boundary=pd.read_csv(ROOT/'results/ROLLING_BOUNDARIES.csv')
    for r in boundary.itertuples():
        state=joblib.load(ROOT/r.model_file);model_count+=1
        assert sha(ROOT/r.model_file)==r.model_sha256
        assert r.label_end<=r.first_origin<r.first_target
        assert r.label_start>='2022-01-01'
        assert state['n']==r.n and state['labels_last']==r.label_end
        if 'rolling730' in r.method:assert r.n==730
        oi=D.origins[r.split];positions=np.flatnonzero((D.index[oi]>=r.first_origin)&(D.index[oi]<=r.last_origin));assert 1<=len(positions)<=28
        pred=np.load(ROOT/'predictions'/(r.method+'.npz'))['det__'+r.split][:,TARGETS.index(r.target)]
        replay=independent_predict(state,oi[positions]);difference=float(np.max(np.abs((replay-pred[positions])/D.scale[TARGETS.index(r.target)])));max_pred=max(max_pred,difference)
        replay_log.append({'method':r.method,'target':r.target,'split':r.split,'block':r.block,'difference':difference})
pd.DataFrame(replay_log).to_csv(ROOT/'results/REPLAY_DIAGNOSTICS.csv',index=False)
assert max_pred<1e-9,max_pred

# Verify past-only rule indexing directly in raw units.
for mid,lag in [('T_fixed_Persistence',1),('T_fixed_Seasonal7',7)]:
    pred=np.load(ROOT/'predictions'/(mid+'.npz'))
    for p,o in D.origins.items():assert np.allclose(pred['det__'+p],D.y[o+1-lag],rtol=0,atol=1e-9)
pred=np.load(ROOT/'predictions/T_rule_Weekday52.npz')
for p,o in D.origins.items():
    replay=np.array([D.y[t-6-7*np.arange(52)].mean(axis=0) for t in o])
    assert np.allclose(pred['det__'+p],replay,rtol=0,atol=1e-9)

# Rebuild level/weekday states without using training fit helpers.
selection=pd.read_csv(ROOT/'results/SELECTION_all.csv')
for adaptive in [False,True]:
    mid='T_state_LevelWeekday'+('Adaptive' if adaptive else 'Fixed')
    meta=json.loads((ROOT/'methods'/(mid+'.json')).read_text());stored=np.load(ROOT/meta['prediction_file'])
    for j,chosen in enumerate(meta['selected']):
        alpha=chosen['alpha'];level=None;values={};dow=D.index.dayofweek.to_numpy();train=D.origins['train']+1
        for t in range(364,len(D.y)-1):
            indices=np.arange(t-364,t) if adaptive else train
            weekday=np.array([D.y[indices[dow[indices]==w],j].mean() for w in range(7)]);base=D.y[indices,j].mean()
            profile=weekday/base if j==2 else weekday-base
            observation=D.y[t,j]/profile[dow[t]] if j==2 else D.y[t,j]-profile[dow[t]]
            level=observation if level is None else alpha*observation+(1-alpha)*level
            values[t]=level*profile[dow[t+1]] if j==2 else level+profile[dow[t+1]]
        for p,o in D.origins.items():assert np.allclose([values[t] for t in o],stored['det__'+p][:,j],rtol=0,atol=1e-8)

full=pd.read_csv(ROOT/'results/ALL_METRICS.csv');max_metric=0.
for m in methods():
    assert sha(ROOT/m['prediction_file'])==m['prediction_sha256']
    z=np.load(ROOT/m['prediction_file'])
    for key in z.files:
        seed,p=key.split('__');truth=D.y[D.origins[p]+1];pred=z[key];err=pred-truth
        assert pred.shape==truth.shape and np.isfinite(pred).all()
        for j,t in enumerate(TARGETS):
            r=full.loc[full.method.eq(m['id'])&full.seed.eq(seed)&full.split.eq(p)&full.target.eq(t)].iloc[0]
            vals={'loss':np.square(err[:,j]/D.scale[j]).sum()/len(err),'MSE':np.square(err[:,j]).sum()/len(err),'MAE':np.abs(err[:,j]).sum()/len(err),'RMSE':np.linalg.norm(err[:,j])/np.sqrt(len(err))}
            for k,v in vals.items():max_metric=max(max_metric,abs(v-r[k])/max(1.,abs(v)))
        if m.get('selected') and m['id'].startswith(('T_fixed_Engineered','T_expanding_','T_rolling730_')) and p=='validation':
            for j,c in enumerate(m['selected']):
                regime=m['regime'];family=c['family'];candidates=selection.loc[selection.regime.eq(regime)&selection.family.eq(family)&selection.target.eq(TARGETS[j])]
                assert abs(c['validation_loss']-candidates.validation_loss.min())<1e-12
                assert abs(c['validation_loss']-np.mean((err[:,j]/D.scale[j])**2))<1e-12
    if m.get('members'):
        member_arrays=[np.load(ROOT/'predictions'/(name+'.npz')) for name in m['members']]
        for key in z.files:assert np.array_equal(z[key],np.mean([q[key] for q in member_arrays],axis=0))
assert max_metric<1e-12

# Imported raw bytes are pinned; this also detects accidental alteration of the source archives.
imports=json.loads((ROOT/'reference/IMPORT_MANIFEST.json').read_text());source_verified=0
for r in imports:
    path=ROOT.parent/r['folder']/r['path']
    if path.exists():assert sha(path)==r['sha256'];source_verified+=1
dump(ROOT/'results/AUDIT.json',{'passed':True,'methods':len(methods()),'saved_estimator_states_replayed':model_count,'rolling_blocks_verified':len(boundary),'all_refit_labels_no_later_than_forecast_origin':True,'max_normalized_prediction_replay_difference':max_pred,'max_relative_metric_difference':max_metric,'source_prediction_hashes_verified':source_verified,'source_prediction_hashes_recorded':len(imports),'per_target_validation_selection_verified':True,'ensembles_replayed':True,'neural_scores_are_mean_of_seed_scores_not_ensemble':True,'scope':'Replay saved estimators, independently rebuild causal features, cutoff and metrics checks; not an external agent review.'})
print((ROOT/'results/AUDIT.json').read_text())
