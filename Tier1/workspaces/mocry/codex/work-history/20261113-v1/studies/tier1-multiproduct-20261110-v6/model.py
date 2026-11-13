"""Product portfolio MILP, with a verifiable relaxation certificate.

Energy GWh, money GBP2020 million/year. Relaxed operations provide an upper
bound. If their optimum obeys all exact operations, the bound certifies the
original model too. Violated min-load states are added adaptively, never omitted
from the final feasibility audit.
"""
import json
import math
from pathlib import Path
import time
import warnings
import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix
import legacy_model as legacy

ROOT=Path(__file__).resolve().parent

class Rows:
    def __init__(self):
        self.names=[]; self.lo=[]; self.hi=[]; self.integer=[]; self.c=[]
        self.rr=[]; self.cc=[]; self.vv=[]; self.rl=[]; self.ru=[]
    def var(self,name,upper=np.inf,lower=0,integer=False,c=0):
        i=len(self.names);self.names.append(name);self.lo.append(lower);self.hi.append(upper)
        self.integer.append(int(integer));self.c.append(c);return i
    def row(self,co,lo=-np.inf,hi=np.inf):
        r=len(self.rl)
        for i,v in co.items():
            if v:self.rr.append(r);self.cc.append(i);self.vv.append(v)
        self.rl.append(lo);self.ru.append(hi)
    def mat(self):
        return coo_matrix((self.vv,(self.rr,self.cc)),shape=(len(self.rl),len(self.names))).tocsc()

def crf(r,n):return r/(1-(1+r)**-n) if r else 1/n

def costs(config, case='comparable', battery_cost='main'):
    bs=json.loads(json.dumps(config['batteries'])); hs=json.loads(json.dumps(config['electrolysers']))
    for b in bs:
        if b['id'].startswith('tesla') and battery_cost in ('tesla_current_proxy','research_favourable'):
            b['capital_GBP']=config['alternatives']['tesla2026_proxy_capital_GBP'];b['fom_GBP']=.025*b['capital_GBP']
        if battery_cost in ('literal','research_favourable') and not b['id'].startswith('tesla'):
            b['fom_GBP']=b['fom_literal_GBP']
        b['eta']=math.sqrt(b['rte']);b['usable']=b['E_MWh']*(b['soc_upper']-b['soc_lower'])/1000
        b['commission_GBP']=b['soc_lower']*b['E_MWh']/b['eta']*config['commission_price']
        b['annual']=(crf(config['r'],b['life'])*(b['capital_GBP']+b['commission_GBP'])+b['fom_GBP'])/1e6
    for h in hs:
        q=h['comparable'] if case=='comparable' else h['research'][case.replace('research_','')]
        h.update(q)
        pv=h['capital_GBP']+sum(h['replacement_GBP']/(1+config['r'])**y for y in h['replacement_years'])
        h['annual']=(crf(config['r'],h['life'])*pv+h['fom_GBP'])/1e6
        h['unit_GWh']=24*h['MW']/1000
    return bs,hs

def solve(frame,config,policy,case='comparable',battery_cost='main',cap=None,seconds=180,
          fixed_battery=None, single_h=None, integer_investment=True, name='case'):
    bs,hs=costs(config,case,battery_cost)
    if single_h:hs=[h for h in hs if h['id']==single_h]
    cap=config['cap_kg_day'] if cap is None else cap
    assert policy in ('A','B') and hs and math.isfinite(cap) and cap>=0
    assert all(0<h['minimum']<=.5 for h in hs), 'Online-module intervals must overlap.'
    assert all(24*b['P_MW']/1000>=b['usable']/b['eta'] for b in bs), 'Priority assumes full usable stock is deliverable in one day.'
    g,d,p=(frame[k].to_numpy(float) for k in ('g','d','price'));T=len(g)
    assert (frame.index.to_series().diff().dropna()==pd.Timedelta(days=1)).all()
    Y=legacy.year_fraction(frame);ref=float(np.dot(p,legacy.direct_reference(frame,policy))/(1000*Y))
    ceiling=(float(np.dot(np.maximum(p,0),d))/1000+T*cap*max(config['netback'],0)/1e6)/Y
    bmax=[max(0,math.ceil(max(0,ceiling-ref)/b['annual'])) for b in bs]
    if fixed_battery is not None:bmax=[fixed_battery.get(b['id'],0) for b in bs]
    hmax=[math.ceil(cap/(h['kg_hour']*24)) for h in hs]
    bad_h=set();need_battery_logic=False;iterations=[]
    started=time.perf_counter()
    while True:
        m=Rows();m.var('reference_constant',1,1,c=ref)
        nb=[m.var('N_'+b['id'],u,0 if fixed_battery is None else u,integer_investment,b['annual']) for b,u in zip(bs,bmax)]
        nh=[m.var('N_'+h['id'],u,0,integer_investment,h['annual']) for h,u in zip(hs,hmax)]
        q=[];hg=[];bv=[{k:[] for k in ('charge','sale','hydrogen','stock')} for b in bs];hv=[[] for h in hs]
        for t in range(T):
            qmax=min(g[t],d[t]);q.append(m.var(f'q_{t}',qmax,qmax if policy=='B' else 0,c=-p[t]/(1000*Y)))
            hg.append(m.var(f'hg_{t}',g[t]))
            gen={q[-1]:1,hg[-1]:1};sale={q[-1]:1};hbalance={hg[-1]:-1};accept={}
            priority_stock={};priority_sale={}
            for j,(b,u) in enumerate(zip(bs,bmax)):
                eta=b['eta'];U=u*b['usable'];P=24*b['P_MW']/1000
                vc=m.var(f'charge_{j}_{t}',min(g[t],U/eta));ve=m.var(f'sale_{j}_{t}',min(d[t],U*eta),c=-p[t]/(1000*Y))
                vh=m.var(f'b_hydrogen_{j}_{t}',min(U*eta,cap*max(h['kWh_kg'] for h in hs)/1e6))
                vs=m.var(f'stock_{j}_{t}',U)
                previous=bv[j]['stock'][-1] if t else None
                for k,v in zip(bv[j],(vc,ve,vh,vs)):bv[j][k].append(v)
                gen[vc]=1;sale[ve]=1;hbalance[vh]=-1
                bal={vs:1,vc:-eta,ve:1/eta,vh:1/eta}
                if previous is not None:bal[previous]=-(1-b['self_discharge'])
                m.row(bal,0,0);m.row({vs:1,nb[j]:-b['usable']},hi=0)
                m.row({vc:eta,nb[j]:-b['usable']},hi=0)
                m.row({ve:1/eta,vh:1/eta,nb[j]:-b['usable']},hi=0)
                m.row({vc:1,nb[j]:-P},hi=0);m.row({ve:1,vh:1,nb[j]:-P},hi=0)
                if need_battery_logic and u:
                    z=m.var(f'charge_mode_{j}_{t}',1,integer=True)
                    m.row({vc:1,z:-min(g[t],U/eta)},hi=0)
                    R=min(U*eta,d[t]+cap*max(h['kWh_kg'] for h in hs)/1e6)
                    m.row({ve:1,vh:1,z:R},hi=R)
                if previous is not None:priority_stock[previous]=eta*(1-b['self_discharge'])
                priority_sale[ve]=1
            for j,(h,u) in enumerate(zip(hs,hmax)):
                H=min(u*h['unit_GWh'],cap*h['kWh_kg']/1e6)
                v=m.var(f'h_{j}_{t}',H,c=-(config['netback']-h['variable_GBP_kg'])/(h['kWh_kg']*Y))
                hv[j].append(v);hbalance[v]=1;accept[v]=1/h['kWh_kg']
                m.row({v:1,nh[j]:-h['unit_GWh']},hi=0)
                if (j,t) in bad_h:
                    z=m.var(f'h_on_{j}_{t}',1,integer=True)
                    m.row({v:1,z:-H},hi=0)
                    m.row({v:1,z:-h['minimum']*h['unit_GWh']},lo=0)
            m.row(gen,hi=g[t]);m.row(sale,hi=d[t]);m.row(hbalance,0,0);m.row(accept,hi=cap/1e6)
            if policy=='B' and need_battery_logic and d[t]>g[t] and any(bmax):
                deficit=d[t]-g[t]
                m.row(priority_sale|{i:-v for i,v in priority_stock.items()},hi=0)
                z=m.var(f'priority_{t}',1,integer=True)
                # Batteries are2h assets; even all usable inventory can be
                # discharged within a day, so the priority availability is stock.
                U=sum(u*b['usable']*b['eta'] for b,u in zip(bs,bmax))
                m.row(priority_sale|{z:deficit},lo=deficit)
                m.row(priority_sale|{i:-v for i,v in priority_stock.items()}|{z:-U},lo=-U)
        for b in bv:m.row({b['stock'][-1]:1},0,0)
        A=m.mat()
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',message='Unrecognized options detected')
            result=milp(np.array(m.c),integrality=np.array(m.integer),bounds=Bounds(m.lo,m.hi),
                constraints=LinearConstraint(A,m.rl,m.ru),options=dict(time_limit=seconds,mip_rel_gap=1e-8,threads=8,random_seed=0))
        if result.x is None:raise RuntimeError(f'{name}: {result.message}')
        x=result.x
        # Exact original constraints are checked, whether present in relaxation or not.
        fresh=[]
        for j,h in enumerate(hs):
            for t,v in enumerate(hv[j]):
                if 1e-7<x[v]<h['minimum']*h['unit_GWh']-1e-7:fresh.append((j,t))
        bat_bad=False
        for b,v in zip(bs,bv):
            c,rs,rh,s=(x[v[k]] for k in v)
            bat_bad |= bool(np.max(np.minimum(c,rs+rh))>1e-7)
        if policy=='B':
            available=sum(np.r_[0,x[v['stock']][:-1]]*b['eta']*(1-b['self_discharge']) for b,v in zip(bs,bv))
            sold=sum(x[v['sale']] for v in bv)
            bat_bad |= bool(np.max(abs(np.where(d>g,np.minimum(d-g,available)-sold,0)))>1e-7)
        iterations.append(dict(status=int(result.status),objective_increment=-float(result.fun),gap=float(result.mip_gap),
            variables=len(x),rows=A.shape[0],added_min_states=len(fresh),need_battery_logic=bool(bat_bad)))
        print(name,'iteration',len(iterations),json.dumps(iterations[-1]),flush=True)
        if not fresh and not bat_bad:break
        new=set(fresh)-bad_h
        if not new and (need_battery_logic or not bat_bad):raise RuntimeError('Failed to close exact feasibility')
        bad_h.update(new);need_battery_logic |= bat_bad
        if len(iterations)>10:raise RuntimeError('Too many refinement iterations')
    out=pd.DataFrame(index=frame.index)
    out[['generation','demand','price']]=frame[['g','d','price']]
    out['direct']=x[q];out['generation_h2']=x[hg]
    for b,v,n in zip(bs,bv,nb):
        for k,iv in v.items():out[b['id']+'__'+k]=x[iv]
    for h,iv in zip(hs,hv):
        out[h['id']+'__input']=x[iv];out[h['id']+'__kg']=x[iv]*1e6/h['kWh_kg']
    out['charge']=sum(x[v['charge']] for v in bv)
    out['battery_sale']=sum(x[v['sale']] for v in bv)
    out['battery_h2']=sum(x[v['hydrogen']] for v in bv)
    out['sales']=out.direct+out.battery_sale
    out['h2_kg']=sum(x[v]*1e6/h['kWh_kg'] for h,v in zip(hs,hv))
    out['unused']=g-out.direct-out.charge-out.generation_h2
    out['unserved']=d-out.sales
    electricity=float(np.dot(p,out.sales)/(1000*Y))
    hydrogen=float(out.h2_kg.sum()*config['netback']/(1e6*Y))
    variable=float(sum(np.sum(x[v])*h['variable_GBP_kg']/(h['kWh_kg']*Y) for h,v in zip(hs,hv)))
    fixed=float(sum(x[n]*b['annual'] for b,n in zip(bs,nb))+sum(x[n]*h['annual'] for h,n in zip(hs,nh)))
    investment=[]
    for kind,prods,ns in [('battery',bs,nb),('electrolyser',hs,nh)]:
        for v,n in zip(prods,ns):
            investment.append(dict(id=v['id'],kind=kind,count=int(round(x[n])) if integer_investment else float(x[n]),
                capital_GBP=v['capital_GBP'],annual_fixed_GBP=v['annual']*1e6,
                physical_MW=v['P_MW'] if kind=='battery' else v['MW'],
                physical_MWh=v['E_MWh'] if kind=='battery' else 0))
    ax=A@x
    err=max(np.max(np.maximum(np.array(m.rl)-ax,0)),np.max(np.maximum(ax-np.array(m.ru),0)),
        np.max(np.maximum(np.array(m.lo)-x,0)),np.max(np.maximum(x-np.array(m.hi),0)))
    summary=dict(name=name,policy=policy,cost_case=case,battery_cost=battery_cost,days=T,years=Y,cap_kg_day=cap,
        annual_incremental_profit_mGBP=electricity+hydrogen-variable-fixed-ref,
        annual_operating_receipts_mGBP=electricity+hydrogen,annual_electricity_receipts_mGBP=electricity,
        annual_hydrogen_receipts_mGBP=hydrogen,annual_reference_receipts_mGBP=ref,
        annual_variable_stack_reserve_mGBP=variable,annual_equipment_fixed_cost_mGBP=fixed,
        initial_capex_mGBP=sum(v['count']*v['capital_GBP'] for v in investment)/1e6,
        battery_MWh=sum(v['count']*v['physical_MWh'] for v in investment),
        electrolyser_MW=sum(v['count']*v['physical_MW'] for v in investment if v['kind']=='electrolyser'),
        annual_h2_tonnes=float(out.h2_kg.sum()/(1000*Y)),annual_sales_GWh=float(out.sales.sum()/Y),
        annual_unserved_GWh=float(out.unserved.sum()/Y),annual_unused_GWh=float(out.unused.sum()/Y),
        demand_coverage=float(out.sales.sum()/d.sum()) if d.sum() else None,investment=investment,
        solver='SciPy/HiGHS',relaxation_certificate='Exact-feasible incumbent of a global upper-bound model',
        status=int(result.status),optimal=result.status==0,gap=float(result.mip_gap),
        upper_profit_bound_mGBP=-float(result.mip_dual_bound),matrix_error=float(err),
        objective_recalculation_error=float(abs(electricity+hydrogen-variable-fixed-ref+result.fun)),
        elapsed_s=time.perf_counter()-started,iterations=iterations,
        active_products=dict(batteries=bs,electrolysers=hs))
    assert err<2e-5 and summary['objective_recalculation_error']<1e-5
    (ROOT/'results'/f'{name}.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    out.to_csv(ROOT/'results'/f'{name}_schedule.csv',index_label='date')
    print('FINISHED',name,summary['annual_incremental_profit_mGBP'],summary['battery_MWh'],summary['electrolyser_MW'],flush=True)
    return summary,out
