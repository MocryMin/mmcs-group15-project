"""CPU feature screens on the same target dates, raw evaluation scale and val criterion."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('MKL_NUM_THREADS','2')
import sys,json,itertools,time,warnings
from pathlib import Path
from features import ROOT,load,TARGETS
sys.path.insert(0,str(ROOT.parent/'tier2b-unified-forecast-comparison-20261110/.deps'))
import numpy as np,pandas as pd
from sklearn.linear_model import Ridge,Lasso
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
from fit import dump

def run(groups):
    f,x,data,mean,sd,names=load(groups);base=x[:,:3];cols=[]
    for j in range(3):
        v=pd.Series(base[:,j])
        for lag in [0,1,2,3,4,5,6,13]:cols.append(v.shift(lag).to_numpy())
        for k in [7,28]:cols.append(v.rolling(k).mean().to_numpy())
    nd=f.index+pd.Timedelta(days=1);dow=nd.dayofweek;ph=(nd.dayofyear.to_numpy()-1)/np.where(nd.is_leap_year,366,365)
    cols.extend(np.eye(7)[dow].T)
    for h in [1,2,3]:
        for fn in [np.sin,np.cos]:cols.append(fn(2*np.pi*h*ph))
    cols.append(((nd.month*100+nd.day>=1224)|(nd.month*100+nd.day<=101)).astype(float))
    if groups:cols.extend(x[:,8:].T)
    X=np.column_stack(cols);tr=data['train']['origins'];sc=StandardScaler().fit(X[tr]);X=sc.transform(X)
    rows=[];selections=[];group='base' if not groups else '+'.join(groups)
    for j,target in enumerate(TARGETS):
        for family in ['Ridge','Lasso','HGB']:
            candidates=[]
            for param,transform in itertools.product({'Ridge':[.1,1.,10.,100.,1000.],'Lasso':[.0001,.001,.01,.03,.1],'HGB':[2,4]}[family],['raw','asinh'] if j==2 else ['raw']):
                y=data['train']['y'][:,j].astype(float);med=np.median(y);spread=max(1.4826*np.median(abs(y-med)),1e-6)
                if transform=='asinh':y=np.arcsinh((y-med)/spread)
                if family=='Ridge':model=Ridge(alpha=param,solver='svd')
                elif family=='Lasso':model=Lasso(alpha=param,max_iter=30000,tol=1e-5,selection='cyclic')
                else:model=HistGradientBoostingRegressor(max_depth=param,max_iter=300,learning_rate=.05,min_samples_leaf=20,l2_regularization=1.,early_stopping=False,random_state=17)
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always',ConvergenceWarning);model.fit(X[tr],y)
                if any(issubclass(w.category,ConvergenceWarning) for w in caught):continue
                pred=model.predict(X[data['validation']['origins']])
                if transform=='asinh':pred=med+spread*np.sinh(pred)
                val=float(np.mean((pred-data['validation']['y'][:,j])**2));selections.append({'target':target,'family':family,'groups':group,'parameter':param,'transform':transform,'validation_loss':val})
                candidates.append((val,param,transform,model,med,spread))
            val,param,transform,model,med,spread=min(candidates,key=lambda r:(r[0],r[1],r[2]))
            arrays={}
            for p,d in data.items():
                pred=model.predict(X[d['origins']]);pred=med+spread*np.sinh(pred) if transform=='asinh' else pred;raw=pred*sd[j]+mean[j];arrays[p]=raw;err=raw-d['truth'][:,j]
                rows.append({'target':target,'family':family,'groups':group,'features':X.shape[1],'parameter':param,'transform':transform,'split':p,'loss':float(np.mean((err/sd[j])**2)),'MAE':float(np.mean(abs(err))),'RMSE':float(np.sqrt(np.mean(err**2)))})
            np.savez_compressed(ROOT/'predictions'/('CPU_'+target+'_'+family+'_'+group+'.npz'),**arrays)
    pd.DataFrame(rows).to_csv(ROOT/'results'/('CPU_'+group+'.csv'),index=False);pd.DataFrame(selections).to_csv(ROOT/'results'/('CPU_SELECTION_'+group+'.csv'),index=False)
    print('CPU_DONE',group,flush=True)

if __name__=='__main__':
    group_arg=sys.argv[1:] or ['base','calendar_target','weekly_context','regime','balance','price_robust']
    with threadpool_limits(2):
        for g in group_arg:run([] if g=='base' else g.split('+'))
