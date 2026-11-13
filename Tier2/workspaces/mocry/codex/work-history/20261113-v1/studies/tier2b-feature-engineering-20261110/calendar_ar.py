"""Extend the existing calendar+residual-AR baseline with each covariate group."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('MKL_NUM_THREADS','2')
import sys
import numpy as np,pandas as pd
from features import ROOT,load,TARGETS

def run(groups):
    f,x,data,mean,scale,names=load(groups);y=(f[TARGETS].to_numpy()-mean)/scale;nd=f.index+pd.Timedelta(days=1);ph=(nd.dayofyear.to_numpy()-1)/np.where(nd.is_leap_year,366,365)
    X=np.column_stack([np.eye(7)[nd.dayofweek],*[fn(2*np.pi*h*ph) for h in [1,2,3] for fn in [np.sin,np.cos]],((nd.month*100+nd.day>=1224)|(nd.month*100+nd.day<=101)).astype(float)])
    if groups:X=np.column_stack([X,x[:,8:]])
    tr=data['train']['origins'];b=np.linalg.lstsq(X[tr],y[tr+1],rcond=1e-6)[0]
    level=np.zeros_like(y);level[1:]=X[:-1]@b;residual=y-level;avg=pd.DataFrame(residual).rolling(7).mean().to_numpy();phi=np.empty((2,3));rows=[];group='+'.join(groups) or 'base'
    for j,t in enumerate(TARGETS):
        Z=np.column_stack([residual[tr,j],avg[tr,j]]);phi[:,j]=np.linalg.lstsq(Z,residual[tr+1,j],rcond=1e-6)[0];arrays={}
        for p,d in data.items():
            o=d['origins'];pn=X[o]@b[:,j]+np.column_stack([residual[o,j],avg[o,j]])@phi[:,j];raw=pn*scale[j]+mean[j];err=raw-d['truth'][:,j];arrays[p]=raw
            rows.append({'target':t,'family':'CalendarAR','groups':group,'features':X.shape[1],'parameter':'OLS calendar+2 residual terms; same model as frozen baseline','transform':'raw','split':p,'loss':float(np.mean((err/scale[j])**2)),'MAE':float(np.mean(abs(err))),'RMSE':float(np.sqrt(np.mean(err**2)))})
        if groups:np.savez_compressed(ROOT/'predictions'/('CPU_'+t+'_CalendarAR_'+group+'.npz'),**arrays)
        else:
            old=np.load(ROOT/'predictions'/('CPU_'+t+'_CalendarAR_base.npz'))
            for p in arrays:assert np.max(np.abs(arrays[p]-old[p])/scale[j])<1e-10
    if groups:
        np.savez_compressed(ROOT/'models'/('CPU_CalendarAR_'+group+'.npz'),calendar_weight=b,residual_weight=phi)
        pd.DataFrame(rows).to_csv(ROOT/'results'/('CPU_AR_'+group+'.csv'),index=False)
    print('CalendarAR_DONE',group,flush=True)

if __name__=='__main__':
    args=sys.argv[1:]
    if not args:
        names=set(pd.read_csv(p).groups.iloc[0] for p in (ROOT/'results').glob('CPU_*.csv') if not p.name.startswith(('CPU_SELECTION_','CPU_REFERENCE_','CPU_AR_')));args=sorted(names)
    for name in args:run([] if name=='base' else name.split('+'))
