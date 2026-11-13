"""Reconstruct the original daily model from exported schedules, not sparse rows."""
import json
from itertools import product
from pathlib import Path
import numpy as np
import pandas as pd
import legacy_model as legacy

ROOT=Path(__file__).resolve().parent

def zero_battery_daily_check(summary,s,config,ns,hs):
    """Enumerate active product types; allocate remaining electricity by value.

    All H2 shares the same per-kg net value in each cost case, so the most
    efficient active H2 type has both the best power value and the least power
    use per kg of shared offtake. This independent calculation needs no MILP.
    """
    g,d,p=(s[k].to_numpy() for k in ('generation','demand','price'))
    plants=[h for h in hs if ns[h['id']]>0]
    prices=[config['netback']-h['variable_GBP_kg'] for h in plants]
    assert not prices or (min(prices)>0 and max(prices)-min(prices)<1e-10)
    q=np.minimum(g,d) if summary['policy']=='B' else np.zeros_like(g)
    free_sales=np.minimum(g,d) if summary['policy']=='A' else np.zeros_like(g)
    best=np.full(len(s),-np.inf)
    for mask in product((False,True),repeat=len(plants)):
        remaining=g-q
        remaining_mass=summary['cap_kg_day']
        revenue=q*p/1000
        options=[]
        for h,enabled,value in zip(plants,mask,prices):
            if not enabled:continue
            minimum=h['minimum']*h['unit_GWh'];conv=1e6/h['kWh_kg']
            remaining=remaining-minimum;remaining_mass-=minimum*conv
            revenue=revenue+minimum*value/h['kWh_kg']
            options.append((value/h['kWh_kg'],ns[h['id']]*h['unit_GWh']-minimum,conv))
        feasible=(remaining>=-1e-8)&(remaining_mass>=-1e-5)
        remaining=np.maximum(remaining,0);remaining_mass=np.full(len(s),max(remaining_mass,0))
        # Compare per-day sales and hydrogen bids for the same remaining GWh.
        sold=np.zeros(len(s),dtype=bool)
        for val,quantity,conv in sorted(options,reverse=True):
            sell_here=(~sold)&(p/1000>val)
            f=np.where(sell_here,np.minimum(free_sales,remaining),0)
            revenue+=f*p/1000;remaining-=f;sold|=sell_here
            h=np.minimum(np.minimum(remaining,quantity),remaining_mass/conv)
            remaining-=h;remaining_mass-=h*conv;revenue+=h*val
        f=np.where((~sold)&(p>0),np.minimum(free_sales,remaining),0)
        revenue+=f*p/1000
        best=np.maximum(best,np.where(feasible,revenue,-np.inf))
    observed=s.sales.to_numpy()*p/1000
    for h in plants:observed=observed+s[h['id']+'__kg'].to_numpy()*(config['netback']-h['variable_GBP_kg'])/1e6
    error=float(np.max(np.abs(best-observed)))
    assert error<2e-5,(summary['name'],error)
    return error

def check(summary,s):
    bs=summary['active_products']['batteries'];hs=summary['active_products']['electrolysers']
    ns={v['id']:v['count'] for v in summary['investment']}
    errors={}
    def record(k,a):errors[k]=float(np.max(np.abs(a)))
    def upper(k,a):errors[k]=max(0,float(np.max(a)))
    charge=0;sale=0;bh=0;stock=0;hinput=0;hydrogen=0;available=0;fixed=0;variable=0;capex=0
    Y=legacy.year_fraction(s)
    for b in bs:
        n=ns[b['id']];col=lambda k:s[b['id']+'__'+k].to_numpy()
        c,r,h,z=(col(k) for k in ('charge','sale','hydrogen','stock'));prior=np.r_[0,z[:-1]]
        record(b['id']+'_balance',z-prior*(1-b['self_discharge'])-b['eta']*c+(r+h)/b['eta'])
        upper(b['id']+'_capacity',z-n*b['usable']);record(b['id']+'_terminal',[z[-1]])
        upper(b['id']+'_negative',-np.r_[c,r,h,z]);record(b['id']+'_net_direction',np.minimum(c,r+h))
        upper(b['id']+'_daily_charge',c*b['eta']-n*b['usable'])
        upper(b['id']+'_daily_discharge',(r+h)/b['eta']-n*b['usable'])
        upper(b['id']+'_charge_power',c-n*24*b['P_MW']/1000)
        upper(b['id']+'_discharge_power',r+h-n*24*b['P_MW']/1000)
        charge+=c;sale+=r;bh+=h;available+=prior*(1-b['self_discharge'])*b['eta']
        fixed+=n*b['annual'];capex+=n*b['capital_GBP']/1e6
    for h in hs:
        n=ns[h['id']];v=s[h['id']+'__input'].to_numpy();unit=h['unit_GWh']
        online=np.where(v>1e-7,np.ceil(v/unit-1e-7),0)
        upper(h['id']+'_count',online-n);upper(h['id']+'_min',h['minimum']*unit*online-v)
        upper(h['id']+'_max',v-unit*online);upper(h['id']+'_negative',-v)
        hinput+=v;hydrogen+=v*1e6/h['kWh_kg'];fixed+=n*h['annual']
        variable+=float(np.sum(v)*h['variable_GBP_kg']/(h['kWh_kg']*Y));capex+=n*h['capital_GBP']/1e6
    record('generation',s.direct+charge+s.generation_h2+s.unused-s.generation)
    record('electrolysis_sources',hinput-s.generation_h2-bh)
    record('sales',s.sales-s.direct-sale);record('H2_output',s.h2_kg-hydrogen)
    upper('sale_limit',s.sales-s.demand);upper('acceptance_GWh_equivalent',(hydrogen-summary['cap_kg_day'])*55.9/1e6)
    upper('unused_nonnegative',-s.unused)
    if summary['policy']=='B':
        record('B_direct',s.direct-np.minimum(s.generation,s.demand))
        record('B_battery_priority',sale-np.minimum(np.maximum(s.demand-s.generation,0),available))
        record('B_no_H2_before_service',np.where(s.unserved>1e-6,bh,0))
    config=json.loads((ROOT/'configuration.json').read_text(encoding='utf-8'))
    ref=float(np.dot(s.price, np.minimum(s.generation,s.demand)*((s.price>=0) if summary['policy']=='A' else 1))/(1000*Y))
    receipts=float(np.dot(s.price,s.sales)/(1000*Y)+np.sum(hydrogen)*config['netback']/(1e6*Y))
    money=abs(receipts-fixed-variable-ref-summary['annual_incremental_profit_mGBP'])
    assert max(errors.values())<2e-5,(summary['name'],errors)
    assert money<1e-5,(summary['name'],money)
    assert abs(capex-summary['initial_capex_mGBP'])<1e-5
    daily_error=None
    if all(ns[b['id']]==0 for b in bs):daily_error=zero_battery_daily_check(summary,s,config,ns,hs)
    return dict(maximum_error_GWh=max(errors.values()),errors=errors,profit_error_mGBP=money,
        independent_daily_dispatch_error_mGBP=daily_error,
        integer_online_counts_reconstructed=True,passed=True)

def run():
    checks={}
    for f in sorted((ROOT/'results').glob('*_schedule.csv')):
        summary=json.loads(f.with_name(f.name.replace('_schedule.csv','.json')).read_text(encoding='utf-8'))
        s=pd.read_csv(f,index_col='date',parse_dates=True)
        checks[summary['name']]=check(summary,s)
    (ROOT/'results/independent_audits.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    print('PASS',len(checks),'independent schedule audits')

if __name__=='__main__':run()
