"""Replay saved predictors, losses and validation-only hyperparameter choices."""
from pathlib import Path
import sys,json,hashlib
import os
os.environ.setdefault('LOKY_MAX_CPU_COUNT','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent;B=R.parent/'tier2b-feature-engineering-20261110'
sys.path.insert(0,str(R.parent/'tier2b-unified-forecast-comparison-20261110/.deps'))
import joblib
from threadpoolctl import threadpool_limits

T=['generation_MW','demand_MW','price_GBP_MWh']
f=pd.read_csv(B/'inputs/model_daily.csv',parse_dates=['date']).set_index('date')
Y=f[T].to_numpy();mu=f.loc['2022':'2024',T].mean().to_numpy();sd=f.loc['2022':'2024',T].std(ddof=0).to_numpy();z=(Y-mu)/sd
q=pd.read_csv(B/'features/neso_demand.csv',parse_dates=['date']).set_index('date').reindex(f.index).to_numpy()
splits={'train':('2022-01-01','2024-12-31'),'validation':('2025-01-01','2025-08-31'),'test':('2025-09-01','2026-08-31')}
ix={p:np.flatnonzero((f.index[1:]>=a)&(f.index[1:]<=b)) for p,(a,b) in splits.items()}
hist=[]
for j in range(3):
    v=pd.Series(z[:,j]);hist.extend([v.shift(k).to_numpy() for k in [0,1,2,3,4,5,6,13]]);hist.extend([v.rolling(k).mean().to_numpy() for k in [7,28]])
hist=np.column_stack(hist);d=f.index+pd.Timedelta(days=1);ph=(d.dayofyear.to_numpy()-1)/np.where(d.is_leap_year,366,365)
cal=np.column_stack([np.eye(7)[d.dayofweek],*[fn(2*np.pi*h*ph) for h in [1,2,3] for fn in [np.sin,np.cos]],((d.month*100+d.day>=1224)|(d.month*100+d.day<=101)).astype(float)])
w=np.column_stack([pd.read_csv(B/'features'/(name+'.csv'),parse_dates=['date']).set_index('date').reindex(f.index).to_numpy() for name in ['weather_temp','weather_wind']])
designs={'mean':q[:,:1],'three':q[:,:3],'six':q,'history':np.column_stack([q,hist]),'calendar':np.column_stack([q,cal]),'weather':np.column_stack([q,w]),'all':np.column_stack([q,hist,cal,w])}
m=pd.read_csv(R/'results/ALL_METRICS.csv');sel=pd.read_csv(R/'results/SELECTION.csv');nmodels=0;errors=[];scalererrors=[]
with threadpool_limits(2):
    for path in sorted((R/'models').glob('*.joblib')):
        a=joblib.load(path);j=T.index(a['target']);method=path.stem[:-(len(a['target'])+1)];X=designs.get(a.get('design','three'));xs=a['scaler'].transform(X)
        scalererrors.append(float(np.max(abs(a['scaler'].mean_-X[ix['train']].mean(0)))))
        np.testing.assert_array_equal(a['mean'],mu);np.testing.assert_array_equal(a['std'],sd)
        valid=np.all(np.isfinite(xs),axis=1);pred=np.full(len(xs),np.nan);pred[valid]=a['model'].predict(xs[valid])
        if 'phi' in a:
            level=np.zeros(len(f));level[1:]=pred[:-1];e=z[:,j]-level
            pred=pred+np.column_stack([e,pd.Series(e).rolling(7).mean().to_numpy()])@a['phi']
        else:
            ss=sel.loc[sel.method.eq(method)&sel.target.eq(a['target'])].sort_values(['validation_loss','parameter']).iloc[0]
            assert a['parameter']==ss.parameter
            vv=np.mean((pred[ix['validation']]-z[ix['validation']+1,j])**2)
            np.testing.assert_allclose(vv,ss.validation_loss,rtol=1e-12)
        saved=np.load(R/'predictions'/(method+'.npz'))
        for p,o in ix.items():
            yhat=pred[o]*sd[j]+mu[j];errors.append(float(np.max(abs(saved[p][:,j]-yhat))))
        nmodels+=1
metric_errors=[]
for row in m.itertuples(index=False):
    j=T.index(row.target);o=ix[row.split]
    yp=q[o,0] if row.method=='Raw_NESO_point_mean' else np.load(R/'predictions'/(row.method+'.npz'))[row.split][:,j]
    er=yp-Y[o+1,j];values=[np.mean((er/sd[j])**2),np.mean(er**2),np.mean(abs(er)),np.sqrt(np.mean(er**2))]
    assert row.n==len(er)
    np.testing.assert_allclose(values,[row.loss,row.MSE,row.MAE,row.RMSE],rtol=1e-12)
    metric_errors.append(float(np.max(abs(np.array(values)-[row.loss,row.MSE,row.MAE,row.RMSE]))))
assert max(errors)<1e-8 and max(scalererrors)<1e-10
out={'models_replayed':nmodels,'metric_rows_verified':len(m),'prediction_max_abs_difference':max(errors),'scaler_mean_max_abs_difference':max(scalererrors),'metric_max_abs_difference':max(metric_errors),'training_last_origin':str(f.index[ix['train'][-1]].date()),'training_last_label':str(f.index[ix['train'][-1]+1].date()),'hyperparameter_selection':'validation only; all saved selected parameters independently checked','residual_AR':'fixed training coefficients; forecast errors available by the origin only','source_feature_timing':'reuses prior strict issue-time audit; no new forecast retrieval or future interpolation','run_code_sha256':hashlib.sha256((R/'run.py').read_bytes()).hexdigest(),'passed':True}
(R/'AUDIT.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
