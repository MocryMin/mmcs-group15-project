"""Refit each recorded classical configuration, without reselecting its parameters."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('MKL_NUM_THREADS','2')
import sys,json,hashlib
import numpy as np,pandas as pd
from features import ROOT,TARGETS,load
sys.path.insert(0,str(ROOT.parent/'tier2b-unified-forecast-comparison-20261110/.deps'))
from sklearn.linear_model import Ridge,Lasso
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
import joblib

def design(groups):
    f,x,data,mean,sd,names=load(groups);columns=[]
    for j in range(3):
        v=pd.Series(x[:,j])
        columns.extend([v.shift(k).to_numpy() for k in [0,1,2,3,4,5,6,13]])
        columns.extend([v.rolling(k).mean().to_numpy() for k in [7,28]])
    target=f.index+pd.Timedelta(days=1);phase=(target.dayofyear.to_numpy()-1)/np.where(target.is_leap_year,366,365)
    C=np.column_stack([np.eye(7)[target.dayofweek],*[fn(2*np.pi*h*phase) for h in [1,2,3] for fn in [np.sin,np.cos]],((target.month*100+target.day>=1224)|(target.month*100+target.day<=101)).astype(float)])
    X=np.column_stack([*columns,C])
    if groups:X=np.column_stack([X,x[:,8:]])
    return f,x,data,mean,sd,X,C

maxdiff=0.;maxmetric=0.;count=0;refit=0;saved=[]
selection=pd.read_csv(ROOT/'results/VALIDATION_SELECTION.csv');save_cases={(r.target,r.family,r.groups) for r in selection.loc[selection.kind.eq('classical')].itertuples()}
with threadpool_limits(2):
    for path in (ROOT/'results').glob('CPU_*.csv'):
        if path.name.startswith(('CPU_SELECTION_','CPU_REFERENCE_','CPU_AR_')):continue
        scores=pd.read_csv(path);group=scores.groups.iloc[0];groups=[] if group=='base' else group.split('+');f,x,data,mean,sd,X,C=design(groups);tr=data['train']['origins'];sc=StandardScaler().fit(X[tr]);X=sc.transform(X)
        for (target,family),rows in scores.groupby(['target','family']):
            cfg=rows.iloc[0];j=TARGETS.index(target);y=data['train']['y'][:,j].astype(float);med=np.median(y);spread=max(1.4826*np.median(abs(y-med)),1e-6)
            if cfg['transform']=='asinh':y=np.arcsinh((y-med)/spread)
            alpha=float(cfg['parameter'])
            if family=='Ridge':model=Ridge(alpha=alpha,solver='svd')
            elif family=='Lasso':model=Lasso(alpha=alpha,max_iter=30000,tol=1e-5,selection='cyclic')
            else:model=HistGradientBoostingRegressor(max_depth=int(alpha),max_iter=300,learning_rate=.05,min_samples_leaf=20,l2_regularization=1.,early_stopping=False,random_state=17)
            model.fit(X[tr],y);refit+=1;stored=np.load(ROOT/'predictions'/('CPU_'+target+'_'+family+'_'+group+'.npz'))
            for p,d in data.items():
                z=model.predict(X[d['origins']]);z=med+spread*np.sinh(z) if cfg['transform']=='asinh' else z;pred=z*sd[j]+mean[j];maxdiff=max(maxdiff,float(np.max(abs(pred-stored[p])/sd[j])))
                err=stored[p]-d['truth'][:,j];r=rows.loc[rows.split.eq(p)].iloc[0]
                for k,v in {'loss':np.mean((err/sd[j])**2),'MAE':np.mean(abs(err)),'RMSE':np.sqrt(np.mean(err**2))}.items():maxmetric=max(maxmetric,abs(v-r[k])/max(1.,abs(v)))
            if (target,family,group) in save_cases:
                out=ROOT/'models'/('CPU_SELECTED_'+target+'_'+family+'_'+group+'.joblib');joblib.dump({'model':model,'scaler':sc,'median':med,'spread':spread,'transform':cfg['transform'],'mean':mean.tolist(),'scale':sd.tolist(),'target':target,'groups':groups},out);saved.append(out.name)
            count+=1
    for path in (ROOT/'results').glob('CPU_AR_*.csv'):
        scores=pd.read_csv(path);group=scores.groups.iloc[0];groups=group.split('+');f,x,data,mean,sd,_,C=design(groups);X=np.column_stack([C,x[:,8:]]);weights=np.load(ROOT/'models'/('CPU_CalendarAR_'+group+'.npz'));b=weights['calendar_weight'];phi=weights['residual_weight'];level=np.zeros((len(f),3));level[1:]=X[:-1]@b;residual=(f[TARGETS].to_numpy()-mean)/sd-level;avg=pd.DataFrame(residual).rolling(7).mean().to_numpy()
        for j,t in enumerate(TARGETS):
            stored=np.load(ROOT/'predictions'/('CPU_'+t+'_CalendarAR_'+group+'.npz'))
            for p,d in data.items():
                o=d['origins'];pred=(X[o]@b[:,j]+np.column_stack([residual[o,j],avg[o,j]])@phi[:,j])*sd[j]+mean[j];maxdiff=max(maxdiff,float(np.max(abs(pred-stored[p])/sd[j])))
                error=stored[p]-d['truth'][:,j];r=scores.loc[scores.target.eq(t)&scores.split.eq(p)].iloc[0];maxmetric=max(maxmetric,abs(np.mean((error/sd[j])**2)-r.loss))
            count+=1
assert maxdiff<1e-9 and maxmetric<1e-12,(maxdiff,maxmetric)
references=json.loads((ROOT/'BASELINE_REFERENCES.json').read_text())
for r in references:
    source=ROOT/r['bundled_path'] if r.get('bundled_path') else __import__('pathlib').Path(r['source'])
    assert hashlib.sha256(source.read_bytes()).hexdigest()==r['sha256']
record={'passed':True,'model_target_cases_replayed_or_refitted':count,'chosen_configurations_refitted':refit,'max_normalized_prediction_difference':maxdiff,'max_relative_metric_difference':maxmetric,'frozen_reference_sources_verified':len(references),'selected_model_states_saved':saved,'val_only_parameter_selection':'parameters from existing val-selected rows; no test-based refitting choice'}
(ROOT/'results/AUDIT_CLASSICAL.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))
