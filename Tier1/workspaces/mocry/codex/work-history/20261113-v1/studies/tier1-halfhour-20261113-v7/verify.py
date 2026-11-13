"""Independent feasibility and cash audit of the exported half-hour schedules."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent

def verify(name):
    meta=json.loads((ROOT/'results'/f'{name}.json').read_text())
    if meta['relaxation']:return {'name':name,'relaxation':True,'passed':None}
    df=pd.read_csv(ROOT/'results'/f'{name}_schedule.csv.gz')
    config=json.loads((ROOT/'configuration.json').read_text())
    ns=meta['investment'];bs=meta['active_products']['batteries'];hs=meta['active_products']['electrolysers']
    dt=meta['dt_hours'];errs={};available=0;ecost=0;hydrogen=0;hinput=0;c=0;r=0;u=0
    def eq(k,x):errs[k]=float(np.max(np.abs(np.asarray(x))))
    def le(k,x):errs[k]=float(max(0,np.max(np.asarray(x))))
    for b in bs:
        n=ns[b['id']];eta=np.sqrt(b['rte']);W=b['E_MWh']*(b['soc_upper']-b['soc_lower'])/1000
        ret=(1-b['self_discharge'])**(dt/24);P=n*dt*b['P_MW']/1000
        vals={k:df[b['id']+'__'+k].to_numpy(dtype=float) for k in ('charge','sale','hydrogen','stock')}
        ch,sa,hy,s=(vals[k] for k in vals);prior=np.r_[0,s[:-1]]
        eq(b['id']+'_stock_balance_GWh',s-ret*prior-eta*ch+(sa+hy)/eta)
        le(b['id']+'_capacity_GWh',s-n*W);le(b['id']+'_charge_power_GWh',ch-P)
        le(b['id']+'_discharge_power_GWh',sa+hy-P);eq(b['id']+'_terminal_GWh',[s[-1]])
        eq(b['id']+'_simultaneous_GWh',np.minimum(ch,sa+hy));le(b['id']+'_nonnegative_GWh',-np.concatenate(list(vals.values())))
        if dt==24:
            le(b['id']+'_daily_window_GWh',np.r_[eta*ch-n*W,(sa+hy)/eta-n*W])
        available+=np.minimum(ret*prior*eta,P);c+=ch;r+=sa;u+=hy
        ecost+=n*b['annual'];eq(b['id']+'_integer',[n-round(n)])
    for h in hs:
        n=ns[h['id']];v=df[h['id']+'__input'].to_numpy(dtype=float);unit=dt*h['MW']/1000
        online=np.ceil(np.maximum(0,v-1e-9)/unit)
        le(h['id']+'_online_count',online-round(n));le(h['id']+'_maximum_GWh',v-online*unit)
        le(h['id']+'_minimum_GWh',online*unit*h['minimum']-v)
        le(h['id']+'_nonnegative_GWh',-v);eq(h['id']+'_integer',[n-round(n)])
        hinput+=v;hydrogen+=v*1e6/h['kWh_kg'];ecost+=n*h['annual']
    eq('generation_balance_GWh',df.direct+c+hinput-u+df.unused-df.g)
    eq('electrolysis_balance_GWh',df.generation_h2+u-hinput)
    eq('hydrogen_kg',hydrogen-df.h2_kg);eq('sales_GWh',df.direct+r-df.sales)
    le('sale_cap_GWh',df.sales-df.d);le('direct_supply_nonnegative_GWh',-df.generation_h2)
    le('curtailment_nonnegative_GWh',-df.unused)
    kg_daily=pd.Series(hydrogen).groupby(df.date).sum()
    le('daily_hydrogen_cap_kg',kg_daily-meta['cap_kg_day'])
    if meta['policy']=='B':
        eq('B_direct_GWh',df.direct-np.minimum(df.g,df.d))
        eq('B_power_limited_priority_GWh',r-np.minimum(np.maximum(df.d-df.g,0),available))
        eq('B_no_hydrogen_before_service_GWh',np.where(df.d-df.sales>1e-7,u,0))
    receipts=(np.dot(df.price,df.sales)/1000+hydrogen.sum()*config['netback']/1e6)/meta['years']
    variable=sum(df[h['id']+'__input'].sum()*h['variable_GBP_kg']/(h['kWh_kg']*meta['years']) for h in hs)
    eq('annual_cash_mGBP',[receipts-variable-ecost-meta['annual_profit_mGBP']])
    tol=lambda k: 0.05 if k.endswith('_kg') else (1e-4 if k.endswith('mGBP') else 2e-7)
    failed={k:v for k,v in errs.items() if v>tol(k)}
    result={'name':name,'passed':not failed,'failed':failed,'errors':errs}
    (ROOT/'results'/f'{name}_audit.json').write_text(json.dumps(result,indent=2))
    print(name,'PASS' if not failed else failed,flush=True)
    assert not failed
    return result

if __name__=='__main__':
    import sys
    if len(sys.argv)>1:
        for n in sys.argv[1:]:verify(n)
    else:
        for f in sorted((ROOT/'results').glob('*_schedule.csv.gz')):verify(f.name.replace('_schedule.csv.gz',''))
