import sys, numpy as np, pandas as pd
R=sys.argv[1]
d=pd.read_csv(f'{R}/Tier1/workspaces/mocry/cleveruser/tier1/20261105-v1/data/daily_model_inputs.csv',parse_dates=['date']).set_index('date')
d['S']=d.G_GWh-d.D_GWh; d['p']=d.price_GBP2020_MWh
thr=7.799/55.9*1000
print('netback-equivalent price £/MWh %.1f'%thr)
g=d.groupby(d.index.year)
print(pd.DataFrame({'S_mean':g.S.mean(),'S_sd':g.S.std(),'sur_days':g.S.apply(lambda s:(s>0).sum()),'p_gt_thr':g.p.apply(lambda s:(s>thr).sum()),'p_mean':g.p.mean(),'p_sd':g.p.std(),'p_cv':g.p.std()/g.p.mean()}).round(2))
s=(d.S>0).astype(int).values
p11=((s[1:]==1)&(s[:-1]==1)).sum()/(s[:-1]==1).sum(); p01=((s[1:]==1)&(s[:-1]==0)).sum()/(s[:-1]==0).sum()
print('P(sur|sur)=%.3f P(sur|not)=%.3f base=%.3f'%(p11,p01,s.mean()))
# spells
runs=[];c=0
for v in s:
    if v: c+=1
    elif c: runs.append(c);c=0
if c: runs.append(c)
runs=np.array(runs);print('surplus spells n=%d mean=%.2f median=%d max=%d share of days in spells>=3: %.2f'%(len(runs),runs.mean(),np.median(runs),runs.max(),runs[runs>=3].sum()/runs.sum()))
# weekly price pattern relative: ratio weekday/weekend by year
d['we']=d.index.dayofweek>=5
print(d.groupby([d.index.year,'we']).p.mean().unstack().assign(ratio=lambda x:x[False]/x[True]).round(2))
# adjacent-day price ratio distribution: how often max/min over next 7 days exceeds 1/0.9
p=d.p.values
r=[]
for i in range(len(p)-7):
    w=p[i:i+7]
    if w.min()>0: r.append(w.max()/w.min())
r=np.array(r);print('7-day max/min price ratio: median %.2f, share>1.111: %.2f, share>1.5: %.2f'%(np.median(r),(r>1/0.9).mean(),(r>1.5).mean()))
# log-return stats / unit root flavour: variance ratio
lp=np.arcsinh(d.p/ d.p.median())
for k in (1,7,28,91):
    print('h',k,'sd of k-day change in asinh price %.3f'%(lp.diff(k).std()))
# share of variance explained by annual+weekly deterministic terms (OLS) per series, by year fixed effects
import numpy.linalg as la
t=np.arange(len(d)); doy=d.index.dayofyear.values
def r2(y,X):
    b=la.lstsq(X,y,rcond=None)[0];res=y-X@b;return 1-res.var()/y.var()
dow=np.eye(7)[d.index.dayofweek]
four=np.column_stack([f(2*np.pi*h*doy/365.25) for h in (1,2,3) for f in (np.sin,np.cos)])
yr=pd.get_dummies(d.index.year).values.astype(float)
for c in ['D_GWh','G_GWh','renewable_GWh','other_GWh','p','S','wind_farm_GWh']:
    y=d[c].values
    print(c,'R2 calendar(dow+annual) %.2f | +year effects %.2f | year only %.2f'%(r2(y,np.column_stack([dow,four])),r2(y,np.column_stack([dow[:,1:],four,yr])),r2(y,yr)))
