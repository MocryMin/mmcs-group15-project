# Simple structural candidates: (1) level x weekday (ETS-like) ; (2) calendar regression + AR(1)-type residual carry-over
import sys, numpy as np, pandas as pd, datetime as dt
R=sys.argv[1]
d=pd.read_csv(f'{R}/Tier1/workspaces/mocry/cleveruser/tier1/20261105-v1/data/daily_model_inputs.csv',parse_dates=['date']).set_index('date')
d=d.rename(columns={'G_GWh':'G','D_GWh':'D','price_GBP2020_MWh':'p','renewable_GWh':'ren','other_GWh':'oth'})
d['S']=d.G-d.D
idx=d.index; HS=[1,2,3,7,14]
VAL=('2023-01-01','2023-12-31'); TEST=('2024-01-01','2025-12-31')
easter=[dt.date(2020,4,12),dt.date(2021,4,4),dt.date(2022,4,17),dt.date(2023,4,9),dt.date(2024,3,31),dt.date(2025,4,20),dt.date(2026,4,5)]
hol=set()
for e in easter: hol|={e-dt.timedelta(2),e+dt.timedelta(1)}
for y in range(2020,2027):
    hol|={dt.date(y,1,1),dt.date(y,12,25),dt.date(y,12,26)}
    m=[dt.date(y,5,1)+dt.timedelta(i) for i in range(31)]
    mons=[x for x in m if x.weekday()==0]; hol|={mons[0],mons[-1]}
    a=[dt.date(y,8,1)+dt.timedelta(i) for i in range(31)]; hol.add([x for x in a if x.weekday()==0][-1])
hol|={dt.date(2020,5,8),dt.date(2022,6,2),dt.date(2022,6,3),dt.date(2022,9,19),dt.date(2023,5,8)}
hol-={dt.date(2020,5,4),dt.date(2022,5,30)}
def cal(dates,withhol=True):
    dow=np.eye(7)[dates.dayofweek]; doy=dates.dayofyear.values
    F=[dow]+[f(2*np.pi*h*doy/365.25)[:,None] for h in (1,2,3) for f in (np.sin,np.cos)]
    md=dates.month*100+dates.day
    F.append(((md>=1224)|(md<=101)).astype(float)[:,None])
    if withhol: F.append(np.array([x.date() in hol for x in dates],float)[:,None])
    return np.column_stack(F)
def ev(y,f,tg,span):
    m=(tg>=span[0])&(tg<=span[1])&~np.isnan(f)&~np.isnan(y)
    return float(np.abs(y[m]-f[m]).mean())
def lvl_wd(ser,k,alpha,mult):
    y=d[ser].values; n=len(y); f=np.full(n,np.nan); dow=idx.dayofweek.values
    L=None
    for t in range(n):
        if t>=364:
            w=np.array([y[t-364:t][dow[t-364:t]==j].mean() for j in range(7)]); base=y[t-364:t].mean()
            w=(w/base) if mult else (w-base)
            x=y[t]/w[dow[t]] if mult else y[t]-w[dow[t]]
            L=x if L is None else alpha*x+(1-alpha)*L
            if t+k<n: f[t]=L*w[dow[t+k]] if mult else L+w[dow[t+k]]
    return f
def calar(ser,k,span,withhol=True,window=None,refit=28):
    y=d[ser].values; n=len(y); C=cal(idx,withhol); f=np.full(n,np.nan)
    tg=idx+pd.Timedelta(days=k); Ck=cal(tg,withhol)
    r=pd.Timestamp(span[0])
    while r<=pd.Timestamp(span[1]):
        tr=(idx<r); 
        if window: tr&=(idx>=r-pd.Timedelta(days=window))
        # level as 1 column is in dow dummies
        b=np.linalg.lstsq(C[tr],y[tr],rcond=None)[0]
        e=y-C@b
        # horizon-specific carry-over coefficient for residual and its 7-day mean
        tt=np.where(tr)[0]; tt=tt[(tt>=7)&(tt+k<=tt.max())]
        e7=pd.Series(e).rolling(7).mean().values
        Z=np.column_stack([e[tt],e7[tt]]); phi=np.linalg.lstsq(Z,e[tt+k],rcond=None)[0]
        te=(tg>=r)&(tg<r+pd.Timedelta(days=refit))
        ii=np.where(te)[0]; ii=ii[ii>=7]
        f[ii]=Ck[ii]@b+phi[0]*e[ii]+phi[1]*e7[ii]
        r+=pd.Timedelta(days=refit)
    return f
rows=[]
for ser in ['p','D','G','ren','oth','S']:
    yk={k:d[ser].shift(-k).values for k in HS}; tgk={k:(idx+pd.Timedelta(days=k)) for k in HS}
    mult=(ser=='p')
    # tune alpha on validation, mean over horizons
    va={a:np.mean([ev(yk[k],lvl_wd(ser,k,a,mult),tgk[k],VAL) for k in HS]) for a in (0.05,0.1,0.2,0.3,0.5,0.8)}
    a=min(va,key=va.get)
    for k in HS:
        row={'ser':ser,'k':k,'alpha':a}
        row['lvlwd']=ev(yk[k],lvl_wd(ser,k,a,mult),tgk[k],TEST)
        row['calar_exp']=ev(yk[k],calar(ser,k,TEST),tgk[k],TEST)
        row['calar_roll730']=ev(yk[k],calar(ser,k,TEST,window=730),tgk[k],TEST)
        row['calar_nohol']=ev(yk[k],calar(ser,k,TEST,withhol=False),tgk[k],TEST)
        rows.append(row)
r=pd.DataFrame(rows); r.to_csv('struct_results.csv',index=False)
pd.set_option('display.width',200); print(r.round(2).to_string())
