import sys, json, warnings, numpy as np, pandas as pd
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
warnings.filterwarnings('ignore')
R=sys.argv[1]
d=pd.read_csv(f'{R}/Tier1/workspaces/mocry/cleveruser/tier1/20261105-v1/data/daily_model_inputs.csv',parse_dates=['date']).set_index('date')
d=d.rename(columns={'G_GWh':'G','D_GWh':'D','price_GBP2020_MWh':'p','renewable_GWh':'ren','other_GWh':'oth','wind_farm_GWh':'wf'})
d['S']=d.G-d.D
SER=['p','D','G','ren','oth','S']
HS=[1,2,3,7,14]
idx=d.index; n=len(d)
def feats(k):
    F={}
    for c in ['p','D','G','ren','oth','wf']:
        for l in range(0,7): F[f'{c}_l{l}']=d[c].shift(l)
        F[f'{c}_l13']=d[c].shift(13)
        F[f'{c}_m7']=d[c].rolling(7).mean(); F[f'{c}_m28']=d[c].rolling(28).mean()
        # most recent same-weekday-as-target value
        s=(7-k%7)%7
        F[f'{c}_sw']=d[c].shift(s); F[f'{c}_sw2']=d[c].shift(s+7)
    X=pd.DataFrame(F,index=idx)
    tgt=idx+pd.Timedelta(days=k)
    dow=tgt.dayofweek
    for j in range(7): X[f'dow{j}']=(dow==j).astype(float)
    doy=tgt.dayofyear.values
    for h in (1,2,3):
        X[f's{h}']=np.sin(2*np.pi*h*doy/365.25); X[f'c{h}']=np.cos(2*np.pi*h*doy/365.25)
    md=tgt.month*100+tgt.day
    X['xmas']=((md>=1224)|(md<=101)).astype(float)
    return X,tgt
def run(model, ser, k, ev_start, ev_end, window=None, refit=28, tr=None, params=None):
    X,tgt=feats(k); y=d[ser].shift(-k)
    ok=X.notna().all(axis=1)&y.notna()
    tg=pd.Series(tgt,index=idx)
    pred=pd.Series(np.nan,index=idx)
    ev=ok&(tg>=ev_start)&(tg<=ev_end)
    evidx=idx[ev]
    r=pd.Timestamp(ev_start)
    fixed=None
    while r<=pd.Timestamp(ev_end):
        # train: targets observed strictly before r
        trm=ok&(tg<r)
        if window: trm&=(tg>=r-pd.Timedelta(days=window))
        if tr=='fixed': trm=ok&(tg<pd.Timestamp('2023-01-01'))
        te=ev&(tg>=r)&(tg<r+pd.Timedelta(days=refit))
        if te.sum()==0: r+=pd.Timedelta(days=refit); continue
        Xt=X[trm].values; yt=y[trm].values
        if ser=='p':
            med=np.median(yt); mad=np.median(np.abs(yt-med))*1.4826
            f=lambda v:np.arcsinh((v-med)/mad); inv=lambda z:np.sinh(z)*mad+med
        else:
            mu=yt.mean(); sd=yt.std(); f=lambda v:(v-mu)/sd; inv=lambda z:z*sd+mu
        if tr=='fixed' and fixed is not None: m,sc,inv=fixed
        else:
            sc=StandardScaler().fit(Xt)
            if model=='ridge': m=Ridge(alpha=params)
            elif model=='lasso': m=Lasso(alpha=params,max_iter=5000)
            elif model=='hgb': m=HistGradientBoostingRegressor(max_iter=300,learning_rate=0.05,max_depth=4,min_samples_leaf=20,l2_regularization=1.0,random_state=0)
            m.fit(sc.transform(Xt),f(yt))
            if tr=='fixed': fixed=(m,sc,inv)
        pred[te]=inv(m.predict(sc.transform(X[te].values)))
        r+=pd.Timedelta(days=refit)
    return pd.DataFrame({'y':y[ev],'f':pred[ev],'tgt':tg[ev]})
def naive(ser,k,ev_start,ev_end,kind):
    y=d[ser].shift(-k); tg=pd.Series(idx+pd.Timedelta(days=k),index=idx)
    if kind=='pers': f=d[ser]
    elif kind=='sn7': f=d[ser].shift((7-k%7)%7)
    elif kind=='ma28': f=d[ser].rolling(28).mean()
    elif kind=='clim':  # trailing 364-day mean of same weekday as target + nothing else
        s=(7-k%7)%7
        f=sum(d[ser].shift(s+7*j) for j in range(52))/52
    ev=y.notna()&f.notna()&(tg>=ev_start)&(tg<=ev_end)
    return pd.DataFrame({'y':y[ev],'f':f[ev],'tgt':tg[ev]})
def mae(r): return float((r.y-r.f).abs().mean())
def rmse(r): return float(np.sqrt(((r.y-r.f)**2).mean()))

import os
VAL=('2023-01-01','2023-12-31'); TEST=('2024-01-01','2025-12-31')
grid_r=[1,10,100,1000]; grid_l=[0.01,0.03,0.1]
SERS=sys.argv[2].split(',')
for ser in SERS:
    if os.path.exists(f'best_{ser}.json'): b=json.load(open(f'best_{ser}.json'))
    else:
        sc={a:np.mean([mae(run('ridge',ser,k,*VAL,params=a)) for k in HS]) for a in grid_r}
        sl={a:np.mean([mae(run('lasso',ser,k,*VAL,params=a)) for k in HS]) for a in grid_l}
        b={'ridge':min(sc,key=sc.get),'lasso':min(sl,key=sl.get),'val_ridge':sc,'val_lasso':sl}
        json.dump(b,open(f'best_{ser}.json','w'))
    print(ser,'alpha',b,flush=True)
    for k in HS:
        rs={}
        for kind in ['pers','sn7','ma28','clim']: rs[kind]=naive(ser,k,*TEST,kind)
        def get(name,fn):
            f=f'pred_{ser}_{k}_{name}.csv'
            if os.path.exists(f): return pd.read_csv(f,index_col=0,parse_dates=['tgt'])
            return fn()
        rs['ridge_exp']=get('ridge_exp',lambda:run('ridge',ser,k,*TEST,params=b['ridge']))
        rs['ridge_roll730']=get('ridge_roll730',lambda:run('ridge',ser,k,*TEST,window=730,params=b['ridge']))
        rs['ridge_fixed2022']=get('ridge_fixed2022',lambda:run('ridge',ser,k,*TEST,tr='fixed',params=b['ridge']))
        rs['lasso_roll730']=get('lasso_roll730',lambda:run('lasso',ser,k,*TEST,window=730,params=b['lasso']))
        rs['hgb_exp']=get('hgb_exp',lambda:run('hgb',ser,k,*TEST))
        e=rs['ridge_exp'].copy(); e['f']=(rs['ridge_exp'].f.values+rs['lasso_roll730'].f.values+rs['hgb_exp'].f.values)/3; rs['ens3']=e
        for m,r in rs.items(): r.to_csv(f'pred_{ser}_{k}_{m}.csv')
        print(ser,k,{m:round(mae(r),2) for m,r in rs.items()},flush=True)
