"""NESO-only calibration and controlled additions, identical frozen target dates."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('MKL_NUM_THREADS','2')
from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent/'tier2b-feature-engineering-20261110'
sys.path.insert(0,str(ROOT.parent/'tier2b-unified-forecast-comparison-20261110/.deps'))
from sklearn.linear_model import LinearRegression,Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
import joblib

TARGETS=['generation_MW','demand_MW','price_GBP_MWh'];PERIODS={'train':('2022-01-01','2024-12-31'),'validation':('2025-01-01','2025-08-31'),'test':('2025-09-01','2026-08-31')}
for n in ['inputs','results','predictions','models']:(ROOT/n).mkdir(exist_ok=True)
f=pd.read_csv(BASE/'inputs/model_daily.csv',parse_dates=['date']).set_index('date');raw=f[TARGETS].to_numpy();tr=f.loc['2022':'2024',TARGETS];mean=tr.mean().to_numpy();sd=tr.std(ddof=0).to_numpy();z=(raw-mean)/sd
data={p:np.flatnonzero((f.index[1:]>=a)&(f.index[1:]<=b)) for p,(a,b) in PERIODS.items()};assert {k:len(v) for k,v in data.items()}=={'train':1096,'validation':243,'test':365}
N=pd.read_csv(BASE/'features/neso_demand.csv',parse_dates=['date']).set_index('date').reindex(f.index)
q=N.to_numpy();nd=f.index+pd.Timedelta(days=1);ph=(nd.dayofyear.to_numpy()-1)/np.where(nd.is_leap_year,366,365)
cal=np.column_stack([np.eye(7)[nd.dayofweek],*[fn(2*np.pi*h*ph) for h in [1,2,3] for fn in [np.sin,np.cos]],((nd.month*100+nd.day>=1224)|(nd.month*100+nd.day<=101)).astype(float)])
hist=[]
for j in range(3):
    ser=pd.Series(z[:,j]);hist.extend([ser.shift(k).to_numpy() for k in [0,1,2,3,4,5,6,13]]);hist.extend([ser.rolling(k).mean().to_numpy() for k in [7,28]])
hist=np.column_stack(hist)
weather=np.column_stack([pd.read_csv(BASE/'features'/(g+'.csv'),parse_dates=['date']).set_index('date').reindex(f.index).to_numpy() for g in ['weather_temp','weather_wind']])
designs={'mean':q[:,:1],'three':q[:,:3],'six':q,'history':np.column_stack([q,hist]),'calendar':np.column_stack([q,cal]),'weather':np.column_stack([q,weather]),'all':np.column_stack([q,hist,cal,weather])}
specs=[('OLS_mean','OLS','mean'),('OLS_mean_min_max','OLS','three'),('Ridge_NESO6','Ridge','six'),('HGB_NESO6','HGB','six'),('Ridge_NESO6_history','Ridge','history'),('Ridge_NESO6_calendar','Ridge','calendar'),('Ridge_NESO6_weather','Ridge','weather'),('Ridge_NESO6_all','Ridge','all')]
rows=[];selections=[];fit_count=0
def score(mid,target,p,pred,params):
    j=TARGETS.index(target);truth=raw[data[p]+1,j];err=np.asarray(pred)-truth
    rows.append({'method':mid,'target':target,'split':p,'n':len(err),'features':params,'loss':float(np.mean((err/sd[j])**2)),'MSE':float(np.mean(err**2)),'MAE':float(np.mean(abs(err))),'RMSE':float(np.sqrt(np.mean(err**2)))})
with threadpool_limits(2):
    for mid,family,name in specs:
        X=designs[name];sc=StandardScaler().fit(X[data['train']]);Xs=sc.transform(X);output={p:np.empty((len(o),3)) for p,o in data.items()}
        for j,target in enumerate(TARGETS):
            grid=[0] if family=='OLS' else [.01,.1,1.,10.,100.,1000.] if family=='Ridge' else [2,4]
            candidates=[]
            for a in grid:
                model=LinearRegression() if family=='OLS' else Ridge(alpha=a,solver='svd') if family=='Ridge' else HistGradientBoostingRegressor(max_depth=a,max_iter=300,learning_rate=.05,min_samples_leaf=20,l2_regularization=1.,early_stopping=False,random_state=17)
                model.fit(Xs[data['train']],z[data['train']+1,j]);fit_count+=1
                val=float(np.mean((model.predict(Xs[data['validation']])-z[data['validation']+1,j])**2));selections.append({'method':mid,'target':target,'parameter':a,'validation_loss':val})
                candidates.append((val,a,model))
            val,a,chosen=min(candidates,key=lambda v:(v[0],v[1]));joblib.dump({'model':chosen,'scaler':sc,'target':target,'mean':mean,'std':sd,'design':name,'parameter':a},ROOT/'models'/(mid+'_'+target+'.joblib'))
            for p,o in data.items():output[p][:,j]=chosen.predict(Xs[o])*sd[j]+mean[j];score(mid,target,p,output[p][:,j],X.shape[1])
        np.savez_compressed(ROOT/'predictions'/(mid+'.npz'),**output)
    # Low-dimensional residual update: retains only current/7-day calibration errors.
    X=designs['three'];sc=StandardScaler().fit(X[data['train']]);Xs=sc.transform(X);output={p:np.empty((len(o),3)) for p,o in data.items()}
    for j,target in enumerate(TARGETS):
        model=LinearRegression().fit(Xs[data['train']],z[data['train']+1,j]);fit_count+=1;level=np.zeros(len(f));level[1:]=model.predict(Xs[:-1]);e=z[:,j]-level;e7=pd.Series(e).rolling(7).mean().to_numpy();o=data['train'];Z=np.column_stack([e[o],e7[o]]);phi=np.linalg.lstsq(Z,e[o+1],rcond=1e-10)[0]
        joblib.dump({'model':model,'scaler':sc,'phi':phi,'target':target,'mean':mean,'std':sd},ROOT/'models'/('OLS3_residual_AR_'+target+'.joblib'))
        for p,o in data.items():pred=(model.predict(Xs[o])+np.column_stack([e[o],e7[o]])@phi)*sd[j]+mean[j];output[p][:,j]=pred;score('OLS3_residual_AR',target,p,pred,5)
    np.savez_compressed(ROOT/'predictions/OLS3_residual_AR.npz',**output)
for p,o in data.items():score('Raw_NESO_point_mean','demand_MW',p,q[o,0],1)
metrics=pd.DataFrame(rows);metrics.to_csv(ROOT/'results/ALL_METRICS.csv',index=False);pd.DataFrame(selections).to_csv(ROOT/'results/SELECTION.csv',index=False)
metrics.loc[metrics.target.eq('demand_MW')].to_csv(ROOT/'results/DEMAND_METRICS.csv',index=False)
protocol={'purpose':'Direct NESO-only calibration versus retaining own historical/weather predictors. Test never selects parameters.','input_sha256':hashlib.sha256((BASE/'inputs/model_daily.csv').read_bytes()).hexdigest(),'NESO_features_sha256':hashlib.sha256((BASE/'features/neso_demand.csv').read_bytes()).hexdigest(),'periods':PERIODS,'evaluation':'sample mean MSE standardized by2022-2024labelstd; also rawMSE/MAE/RMSE','source_note':'NESO predictions targetNationalDemand, courseY is repairedVDdaily mean; this is cross-definition calibration.','prior_correlations_note':'0.9883/0.9995 were observedVD vs observedND/TSD, NOT NESOforecast-vs-target correlations.','fit_count':fit_count,'designs':{k:v.shape[1] for k,v in designs.items()},'published':False}
(ROOT/'PROTOCOL.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
diag=[]
for p,o in data.items():
    for j,t in enumerate(TARGETS):diag.append({'target':t,'split':p,'correlation_raw_NESO_mean_forecast_vs_actual_target':float(np.corrcoef(q[o,0],raw[o+1,j])[0,1])})
pd.DataFrame(diag).to_csv(ROOT/'results/FORECAST_CORRELATIONS.csv',index=False)
print(metrics.loc[metrics.target.eq('demand_MW')].pivot(index='method',columns='split',values='loss').sort_values('validation').to_string())
print(pd.DataFrame(diag).loc[lambda d:d.target.eq('demand_MW')].to_string(index=False))
