import sys, numpy as np, pandas as pd
R=sys.argv[1]
d=pd.read_csv(f'{R}/Tier1/workspaces/mocry/cleveruser/tier1/20261105-v1/data/daily_model_inputs.csv',parse_dates=['date']).set_index('date')
print(d.columns.tolist()); print(d.index.min(), d.index.max(), len(d))
fuel=pd.read_csv(f'{R}/Tier1/public/data_quality/full_data_repair/20261104-v2/data/daily_generation_by_fuel.csv')
print(fuel.columns.tolist()); print(fuel.head(3))
d['S']=d.G_GWh-d.D_GWh
d['p']=d.price_GBP2020_MWh
print(d[['G_GWh','D_GWh','p','wind_farm_GWh','renewable_GWh','other_GWh','S']].describe().T.round(2))
print('strict share',d.strict_no_imputation.mean())
# yearly
y=d.groupby(d.index.year).agg(G=('G_GWh','mean'),D=('D_GWh','mean'),p=('p','mean'),psd=('p','std'),ren=('renewable_GWh','mean'),oth=('other_GWh','mean'),wf=('wind_farm_GWh','mean'),surdays=('S',lambda s:(s>0).sum()),pneg=('p',lambda s:(s<=0).sum()))
print(y.round(1))
def acf(x,lags):
    x=np.asarray(x,float);x=x-x.mean();v=(x*x).sum()
    return [round(float((x[l:]*x[:-l]).sum()/v),3) for l in lags]
L=[1,2,3,7,14,28,91,182,364,365]
for c in ['G_GWh','D_GWh','p','renewable_GWh','other_GWh','wind_farm_GWh','S']:
    print(c,'acf',dict(zip(L,acf(d[c],L))))
# weekday effect
print(d.groupby(d.index.dayofweek)[['G_GWh','D_GWh','p','renewable_GWh','other_GWh']].mean().round(1))
print(d.groupby(d.index.month)[['G_GWh','D_GWh','p','renewable_GWh','S']].mean().round(1))
print(d[['G_GWh','D_GWh','p','renewable_GWh','other_GWh','wind_farm_GWh']].corr().round(2))
# deseasonalised / diffs correlation
dd=d[['G_GWh','D_GWh','p','renewable_GWh','other_GWh','wind_farm_GWh']].diff().dropna()
print('diff corr');print(dd.corr().round(2))
# tails
for c in ['p','G_GWh','D_GWh','renewable_GWh']:
    x=d[c];z=(x-x.mean())/x.std()
    print(c,'skew %.2f kurt %.2f'%(z.pow(3).mean(),z.pow(4).mean()),'q01 %.1f q50 %.1f q99 %.1f max %.1f min %.1f'%(x.quantile(.01),x.median(),x.quantile(.99),x.max(),x.min()))
