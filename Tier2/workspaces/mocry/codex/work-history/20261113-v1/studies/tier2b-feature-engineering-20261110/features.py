"""Causal per-observation features; forecast at end of t for t+1."""
from pathlib import Path
import json
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parent
TARGETS=['generation_MW','demand_MW','price_GBP_MWh']

def load(groups=()):
    f=pd.read_csv(ROOT/'inputs/model_daily.csv',parse_dates=['date']).set_index('date');y=f[TARGETS].to_numpy()
    train=f.loc['2022':'2024',TARGETS];mean=train.mean().to_numpy();scale=train.std(ddof=0).to_numpy();z=(y-mean)/scale
    dow=f.index.dayofweek.to_numpy();phase=(f.index.dayofyear.to_numpy()-1)/np.where(f.index.is_leap_year,366,365)
    x=np.column_stack([z,np.sin(2*np.pi*dow/7),np.cos(2*np.pi*dow/7),np.sin(2*np.pi*phase),np.cos(2*np.pi*phase),dow>=5]);names=TARGETS+['dow_sin','dow_cos','year_sin','year_cos','weekend']
    extra=[];extra_names=[]
    def add(a,n):extra.append(np.asarray(a,float));extra_names.append(n)
    v=pd.DataFrame(z,index=f.index)
    for group in groups:
        if group=='calendar_target':
            nd=f.index+pd.Timedelta(days=1);ndow=nd.dayofweek.to_numpy();ph=(nd.dayofyear.to_numpy()-1)/np.where(nd.is_leap_year,366,365)
            for j in range(7):add(ndow==j,'target_weekday_'+str(j))
            for h in [2,3]:
                for fn in [np.sin,np.cos]:add(fn(2*np.pi*h*ph),'target_year_'+fn.__name__+str(h))
            md=nd.month*100+nd.day;add((md>=1224)|(md<=101),'target_xmas')
        elif group=='weekly_context':
            for j,t in enumerate(TARGETS):
                for lag in [7,14]:add(v[j].shift(lag),t+'_lag'+str(lag))
                add(v[j].rolling(7,min_periods=1).mean(),t+'_mean7')
        elif group=='regime':
            for j,t in enumerate(TARGETS):
                for k in [7,28,90]:
                    add(v[j].rolling(k,min_periods=2).mean(),t+'_mean'+str(k))
                    add(v[j].rolling(k,min_periods=2).std(ddof=0),t+'_sd'+str(k))
                add(v[j].diff(),t+'_change1')
        elif group=='balance':
            balance=(y[:,0]-y[:,1])/scale[0];ser=pd.Series(balance)
            add(balance,'generation_minus_demand');add(y[:,1]/np.maximum(y[:,0],1000),'demand_generation_ratio')
            add(np.maximum(balance,0),'surplus');add(np.maximum(-balance,0),'deficit')
            for k in [7,28]:add(ser.rolling(k,min_periods=1).mean(),'balance_mean'+str(k))
        elif group=='price_robust':
            raw=pd.Series(y[:,2]);tr=train.iloc[:,2].to_numpy();med=np.median(tr);spread=max(1.4826*np.median(abs(tr-med)),1e-6);a=np.arcsinh((raw-med)/spread)
            add(a,'price_asinh');add(a.diff(),'price_asinh_change')
            for k in [7,28]:
                add(a.rolling(k,min_periods=1).mean(),'price_asinh_mean'+str(k));add(a.rolling(k,min_periods=2).std(ddof=0),'price_asinh_sd'+str(k))
        elif (ROOT/'features'/(group+'.csv')).exists():
            ext=pd.read_csv(ROOT/'features'/(group+'.csv'),parse_dates=['date']).set_index('date').reindex(f.index)
            assert ext.index.equals(f.index)
            for c in ext:add(ext[c].to_numpy(),group+'__'+c)
        else:raise ValueError(group)
    if extra:
        e=np.column_stack(extra)
        # Early context uses causal carry-forward, then neutral values if no earlier observation.
        e=pd.DataFrame(e).ffill().fillna(0).to_numpy()
        token_fit=(f.index>='2022-01-01')&(f.index<='2024-12-31');mu=e[token_fit].mean(0);sd=e[token_fit].std(0);sd[sd<1e-10]=1
        x=np.column_stack([x,(e-mu)/sd]);names+=extra_names
    periods=json.loads((ROOT/'BASELINE_FROZEN.json').read_text())['periods'];data={}
    for p,(a,b) in periods.items():
        o=np.flatnonzero((f.index[1:]>=a)&(f.index[1:]<=b));data[p]={'origins':o,'y':z[o+1].astype(np.float32),'truth':y[o+1]}
    assert np.isfinite(x).all()
    return f,x.astype(np.float32),data,mean,scale,names
