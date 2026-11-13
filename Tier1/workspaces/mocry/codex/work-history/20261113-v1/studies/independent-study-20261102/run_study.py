"""Tier 1 pooled-energy model and Tier 2B chronological investment/dispatch pilot.

Cost inputs below are explicit trial assumptions, not researched market estimates.
All revenues are incremental to the existing wind farm's immediate electricity sales.
"""
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
import xpress as xp
from audit_data import prepare, HERE

xp.init('C:/xpressmp/bin/xpauth.xpr')
ETA = math.sqrt(0.9)
RATE, LIFE, FX = .08, 15, .85
CRF = RATE/(1-(1+RATE)**(-LIFE))
BASE_B_COST = 2*288000*FX  # GBP per MW of installed two-hour battery
BASE_H_COST = 1000000     # trial GBP per MW, varied separately

def inputs(frame, boundary='additional', demand_scale=1.0):
    f=frame.copy()
    # Alternative interpretation: total generation already includes this wind farm.
    other=f.generation_MW-(f.wind_MW if boundary=='included' else 0)
    residual=(demand_scale*f.demand_MW-other).clip(lower=0)
    immediate=np.minimum(f.wind_MW,residual).where(f.price_MWh>0,0)
    if boundary=='pro_rata':
        share=np.minimum(1,demand_scale*f.demand_MW/(f.generation_MW+f.wind_MW))
        immediate=(f.wind_MW*share).where(f.price_MWh>0,0)
    f['surplus']=24*(f.wind_MW-immediate)
    f['headroom']=24*(residual-immediate).clip(lower=0).where(f.price_MWh>0,0)
    f['base_revenue']=24*immediate*f.price_MWh
    return f

def summarize(name,f,B,H,c,d,h,s,cost_b,cost_h,hprice,net,mode,extra):
    years=len(f.index.year.unique())
    capex=B*cost_b+H*cost_h
    annual_charge=B*cost_b*(CRF+.01)+H*cost_h*(CRF+.03)
    gross=float((d*f.price_MWh.to_numpy()+h*hprice/.0559).sum()/years)
    out={'case':name,'mode':mode,'years':list(map(int,f.index.year.unique())),
         'battery_MW':B,'battery_nameplate_MWh':2*B,'electrolyser_MW':H,
         'hydrogen_price_GBP_kg':hprice,'capex_GBP':capex,'annual_capital_and_fixed_OM_GBP':annual_charge,
         'gross_incremental_revenue_GBP_year':gross,'net_increment_GBP_year':float(net),
         'baseline_electricity_revenue_GBP_year':float(f.base_revenue.sum()/years),
         'hydrogen_kg_year':float(h.sum()/.0559/years),
         'charge_MWh_year':float(c.sum()/years),'discharge_MWh_year':float(d.sum()/years),
         'hydrogen_input_MWh_year':float(h.sum()/years),
         'unused_MWh_year':float((f.surplus.to_numpy()-h-c).sum()/years),
         'available_surplus_MWh_year':float(f.surplus.sum()/years),
         'simple_payback_years':float(capex/(gross-B*cost_b*.01-H*cost_h*.03)) if gross>B*cost_b*.01+H*cost_h*.03 else None,
         **extra}
    schedule=f.copy()
    for k,v in [('charge_MWh',c),('discharge_MWh',d),('hydrogen_input_MWh',h),('usable_SOC_MWh',s)]:schedule[k]=v
    schedule.to_csv(HERE/'outputs'/(name+'.csv'),index_label='date')
    return out

def optimize(name,frame,mode='chronological',boundary='additional',hprice=9.5,
             bcost_factor=1,hcost=BASE_H_COST,allow_b=True,allow_h=True,
             fixed=None,duty_cycle=False,demand_scale=1):
    f=inputs(frame,boundary,demand_scale);n=len(f);years=len(f.index.year.unique())
    S=f.surplus.to_numpy();D=f.headroom.to_numpy();P=f.price_MWh.to_numpy()
    bcost=BASE_B_COST*bcost_factor
    p=xp.problem(name=name);p.controls.outputlog=0;p.controls.threads=2
    p.controls.miprelstop=1e-8;p.controls.mipabsstop=.01;p.controls.maxtime=60
    # Data-derived upper bounds: no device can use more than the entire annual
    # surplus; hydrogen power above peak daily surplus cannot improve this model.
    upper=max(1.0,1.01*float(S.max())/24)
    bupper=max(1.0,1.01*max(float(S[f.index.year==y].sum()) for y in f.index.year.unique())*ETA/1.2)
    B=p.addVariable(name='battery_MW',lb=fixed[0] if fixed else 0,
                    ub=fixed[0] if fixed else (bupper if allow_b else 0))
    H=p.addVariable(name='electrolyser_MW',lb=fixed[1] if fixed else 0,
                    ub=fixed[1] if fixed else (upper if allow_h else 0))
    c={t:p.addVariable(name=f'charge_{t}',ub=float(S[t])) for t in range(n) if S[t]>1e-9 and allow_b}
    h={t:p.addVariable(name=f'electrolysis_{t}',ub=float(S[t])) for t in range(n) if S[t]>1e-9 and allow_h}
    d={t:p.addVariable(name=f'discharge_{t}',ub=float(D[t])) for t in range(n) if D[t]>1e-9 and allow_b}
    s={t:p.addVariable(name=f'usable_SOC_{t}') for t in range(n)} if mode=='chronological' and allow_b else {}
    on={t:p.addVariable(name=f'hydrogen_on_{t}',vartype=xp.binary) for t in h} if not duty_cycle else {}
    for t in range(n):
        if t in c or t in h:p.addConstraint(c.get(t,0)+h.get(t,0)<=float(S[t]))
        # One usable swing per day; power limits are looser for a two-hour battery.
        # In the chronological model surplus and discharge-headroom days are
        # disjoint, so SOC bounds already imply these daily swing limits.
        if t in c and mode=='pooled':p.addConstraint(c[t]<=1.2*B/ETA)
        if t in d and mode=='pooled':p.addConstraint(d[t]<=1.2*B*ETA)
        if t in h:
            p.addConstraint(h[t]<=24*H)
            if not duty_cycle:
                p.addConstraint(h[t]<=24*upper*on[t])
                p.addConstraint(h[t]>=4.8*H-4.8*upper*(1-on[t]))
        if t in s:
            prev=s[t-1] if t>0 and f.index[t-1].year==f.index[t].year else 0
            p.addConstraint(s[t]==prev+ETA*c.get(t,0)-d.get(t,0)/ETA)
            p.addConstraint(s[t]<=1.2*B)
    if mode=='pooled' and allow_b:
        for year in f.index.year.unique():
            ix=[t for t in range(n) if f.index[t].year==year]
            p.addConstraint(xp.Sum(d.get(t,0) for t in ix)<=.9*xp.Sum(c.get(t,0) for t in ix))
    annual_cost=bcost*(CRF+.01)*B+hcost*(CRF+.03)*H
    revenue=xp.Sum(float(P[t])*v for t,v in d.items())+hprice/.0559*xp.Sum(list(h.values()))
    p.setObjective(revenue/years-annual_cost,sense=xp.maximize)
    p.solve()
    if p.attributes.solstatus != 1:
        raise RuntimeError(f'{name}: no proven optimum; solve={p.attributes.solvestatus} sol={p.attributes.solstatus}')
    bval,hval=float(p.getSolution(B)),float(p.getSolution(H))
    arr=lambda mapping:np.array([p.getSolution(mapping[t]) if t in mapping else 0 for t in range(n)],dtype=float)
    ca,da,ha,sa=map(arr,[c,d,h,s])
    # Recompute the model's physical and financial constraints from numeric output.
    violations=[0.0,float(np.max(ca+ha-S)),float(np.max(da-D)),
                float(np.max(ca-1.2*bval/ETA)),float(np.max(da-1.2*bval*ETA)),
                float(np.max(ha-24*hval)),float(-min(ca.min(),da.min(),ha.min(),sa.min()))]
    if not duty_cycle:
        active=ha>1e-5
        if active.any():violations.append(float(np.max(4.8*hval-ha[active])))
    if mode=='chronological' and allow_b:
        previous=np.r_[0,sa[:-1]]
        previous[np.r_[True,f.index.year[1:]!=f.index.year[:-1]]]=0
        violations.extend([float(np.max(np.abs(sa-previous-ETA*ca+da/ETA))),float(np.max(sa-1.2*bval))])
    if mode=='pooled':
        for year in f.index.year.unique():
            mask=f.index.year==year;violations.append(float(da[mask].sum()-.9*ca[mask].sum()))
    net=float((P*da+ha*hprice/.0559).sum()/years-bcost*(CRF+.01)*bval-hcost*(CRF+.03)*hval)
    violations.append(abs(net-p.attributes.objval))
    assert max(violations)<1e-4,(name,max(violations))
    assert bval<bupper-.001 and hval<upper-.001,'Artificial capacity bound reached'
    extra={'solver':'Xpress9.9','solstatus':int(p.attributes.solstatus),'solvestatus':int(p.attributes.solvestatus),
           'objective_GBP':float(p.attributes.objval),'max_check_violation':max(violations),
           'rows':p.attributes.rows,'columns':p.attributes.cols,'boundary':boundary,
           'full_day_minimum_load':not duty_cycle,'battery_cost_factor':bcost_factor,
           'electrolyser_cost_GBP_MW':hcost,'demand_scale':demand_scale,
           'year_end_usable_SOC_MWh':[float(sa[np.where(f.index.year==y)[0][-1]]) for y in f.index.year.unique()]}
    if on:extra['best_bound_GBP']=float(p.attributes.bestbound)
    return summarize(name,f,bval,hval,ca,da,ha,sa,bcost,hcost,hprice,net,mode,extra)

def causal_policy(name,frame,B,H,hprice=9.5,bcost_factor=1,hcost=BASE_H_COST):
    """Current-day inputs only: use surplus for hydrogen first, then charge;
    discharge into positive-price unmet headroom. No future-price data read.
    """
    f=inputs(frame);n=len(f);c=np.zeros(n);d=c.copy();h=c.copy();soc=c.copy()
    state=0;viol=0
    for t,(_,row) in enumerate(f.iterrows()):
        if t==0 or f.index[t].year!=f.index[t-1].year:state=0
        previous=state
        if row.surplus>=4.8*H-1e-9 and H>0:h[t]=min(row.surplus,24*H)
        c[t]=max(0,min(row.surplus-h[t],(1.2*B-state)/ETA))
        state+=ETA*c[t]
        d[t]=max(0,min(row.headroom,1.2*B*ETA,state*ETA))
        state-=d[t]/ETA;soc[t]=state
        viol=max(viol,c[t]+h[t]-row.surplus,d[t]-row.headroom,state-1.2*B,-state,
                 abs(state-previous-ETA*c[t]+d[t]/ETA))
    assert viol<1e-5
    years=len(f.index.year.unique());bcost=BASE_B_COST*bcost_factor
    net=float((d*f.price_MWh.to_numpy()+h*hprice/.0559).sum()/years-B*bcost*(CRF+.01)-H*hcost*(CRF+.03))
    return summarize(name,f,B,H,c,d,h,soc,bcost,hcost,hprice,net,'causal_policy',
                     {'future_information_used':False,'max_check_violation':float(viol),
                      'year_end_usable_SOC_MWh':[float(soc[np.where(f.index.year==y)[0][-1]]) for y in f.index.year.unique()]})

def main():
    (HERE/'outputs').mkdir(exist_ok=True)
    df,audit=prepare()
    train=df.loc['2023':'2024'];test=df.loc['2025']
    assert len(train)==731 and len(test)==365
    cases=[]
    def run(name,frame=train,**kwargs):
        r=optimize(name,frame,**kwargs);cases.append(r)
        print(name,round(r['battery_MW'],3),round(r['electrolyser_MW'],3),round(r['net_increment_GBP_year'],2),flush=True)
        (HERE/'results.json').write_text(json.dumps(cases,indent=2)+'\n',encoding='utf-8')
        return r
    run('no_investment',allow_b=False,allow_h=False)
    run('tier1_pooled',mode='pooled')
    base=run('tier2_chronological')
    run('battery_only',allow_h=False)
    run('hydrogen_only',allow_b=False)
    for price in [2,3,6,12]:run(f'hydrogen_price_{price}',hprice=price)
    for cost in [500000,2000000]:run(f'hydrogen_cost_{cost}',hcost=cost)
    run('wind_included_in_total',boundary='included')
    run('curtailment_pro_rata',boundary='pro_rata')
    run('demand_plus10pct',demand_scale=1.1)
    run('demand_minus10pct',demand_scale=.9)
    run('subdaily_electrolyser_duty_cycle',duty_cycle=True)
    fixed=(base['battery_MW'],base['electrolyser_MW'])
    run('2025_fixed_design_perfect_foresight',frame=test,fixed=fixed)
    run('2025_reoptimized_hindsight',frame=test)
    cases.append(causal_policy('2025_fixed_design_causal',test,*fixed))
    # Force nonzero storage to test chronology and information even if investment optimum is zero.
    fixed=(50,base['electrolyser_MW'])
    run('diagnostic_50MW_pooled',frame=test,fixed=fixed,mode='pooled')
    run('diagnostic_50MW_chronological',frame=test,fixed=fixed)
    cases.append(causal_policy('diagnostic_50MW_causal',test,*fixed))
    # Cheap-storage diagnostic tests that the capacity decision can actually become positive.
    run('diagnostic_1pct_battery_cost',bcost_factor=.01,hprice=3)
    (HERE/'results.json').write_text(json.dumps(cases,indent=2)+'\n',encoding='utf-8')
    pd.DataFrame(cases).to_csv(HERE/'results.csv',index=False)
    (HERE/'assumptions.json').write_text(json.dumps({'cost_status':'illustrative trial assumptions, not market quotations',
        'discount_rate':RATE,'life_years':LIFE,'GBP_per_EUR':FX,'CRF':CRF,
        'battery_GBP_MW':BASE_B_COST,'electrolyser_GBP_MW':BASE_H_COST,
        'fixed_OM_fraction_battery':.01,'fixed_OM_fraction_electrolyser':.03,
        'training_years':[2023,2024],'test_year':2025,
        'boundary':'existing wind farm is additional to national background generation; all background output has priority over wind',
        'time':'daily average MW times24,one usable battery swing perday, no within-day price spread',
        'electrolyser':'either off or20%-100% for a full day; alternate subdaily duty-cycle case',
        'hydrogen':'unlimited offtake at scenario price, no compression/transport/water variable cost',
        'battery':'usableSOCabove20%floor,starts atfloor eachyear; endSOC has zero salvage, no free initialenergy',
        'cashflow':'incremental grosssales less annualized newcapex and fixedOM; excludes existingwindfarm costs'},indent=2)+'\n')
    return cases

if __name__=='__main__':main()
