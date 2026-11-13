"""Dantzig-Wolfe storage columns: exact continuous-capacity upper bound.

Every column is a feasible six-year trajectory of ONE battery. Electrolyser
capacity is divisible for the bound; equal annual cost/MW means the most
efficient product dominates all other divisible products. Integer investment,
minimum-load, mode and B-priority rules are audited separately for candidates.
"""
import argparse, json, time, math
from pathlib import Path
import numpy as np
import pandas as pd
import highspy
from model import ROOT, Matrix, annual_costs, frame_for

def highslp(m,solver='ipm',seconds=600,crossover='off'):
    A=m.sparse();lp=highspy.HighsLp();lp.num_col_=m.n;lp.num_row_=m.nr
    lp.col_cost_=np.concatenate(m.cost);lp.col_lower_=np.concatenate(m.lb);lp.col_upper_=np.concatenate(m.ub)
    lp.row_lower_=np.concatenate(m.rl);lp.row_upper_=np.concatenate(m.ru)
    lp.a_matrix_.format_=highspy.MatrixFormat.kColwise;lp.a_matrix_.start_=A.indptr;lp.a_matrix_.index_=A.indices;lp.a_matrix_.value_=A.data
    h=highspy.Highs();h.setOptionValue('output_flag',False);h.setOptionValue('threads',4)
    h.setOptionValue('solver',solver);h.setOptionValue('run_crossover',crossover);h.setOptionValue('time_limit',seconds)
    h.setOptionValue('ipm_optimality_tolerance',1e-9);h.passModel(lp)
    return h

class Pricing:
    def __init__(self,b,T,dt,Y):
        self.b=b;self.T=T;self.Y=Y;m=Matrix();eta=b['eta'];P=dt*b['P_MW'];W=b['usable']*1000
        self.c=m.variables(T,hi=P);self.d=m.variables(T,hi=P);self.s=m.variables(T,hi=W)
        m.rows(1,[(self.s[0],1),(self.c[0],-eta),(self.d[0],1/eta)],0,0)
        m.rows(T-1,[(self.s[1:],1),(self.s[:-1],-b['retention']),(self.c[1:],-eta),(self.d[1:],1/eta)],0,0)
        m.rows(1,[(self.s[-1],1)],0,0)
        self.h=highslp(m)
    def solve(self,charge_cost,discharge_value,charge_allowed=None):
        # Master dual units are million GBP/year/GWh; price LP uses GBP/MWh.
        costs=np.r_[charge_cost*1000*self.Y,-discharge_value*1000*self.Y]
        ix=np.r_[self.c,self.d]
        self.h.changeColsCost(len(ix),ix,costs)
        if charge_allowed is not None:
            self.h.changeColsBounds(self.T,self.c,np.zeros(self.T),np.where(charge_allowed,.5*self.b['P_MW'],0))
        self.h.run();status=self.h.getModelStatus()
        assert status==highspy.HighsModelStatus.kOptimal,str(status)
        solution=self.h.getSolution();x=np.array(solution.col_value)
        op_cost=self.h.getObjectiveValue()/(1e6*self.Y)
        info=self.h.getInfo()
        # Independently form a valid dual lower bound. All pricing rows are
        # equalities with RHS zero, and every variable has a finite box bound.
        # Any row multiplier gives min_{box}(c-A'pi)'x as a lower bound.
        pi=np.array(solution.row_dual);eta=self.b['eta'];P=.5*self.b['P_MW'];W=self.b['usable']*1000
        red_c=charge_cost*1000*self.Y+eta*pi[:self.T]
        red_d=-discharge_value*1000*self.Y-pi[:self.T]/eta
        red_s=-pi[:self.T].copy();red_s[:-1]+=self.b['retention']*pi[1:self.T];red_s[-1]-=pi[-1]
        cbound=np.full(self.T,P) if charge_allowed is None else np.where(charge_allowed,P,0)
        dual_lower=float(np.dot(cbound,np.minimum(red_c,0))+P*np.minimum(red_d,0).sum()+W*np.minimum(red_s,0).sum())/(1e6*self.Y)
        return dict(charge=x[self.c]/1000,discharge=x[self.d]/1000,stock=x[self.s]/1000,
                    reduced_cost=self.b['annual']+op_cost,reduced_cost_lower=self.b['annual']+dual_lower,
                    pricing_dual_gap_GBP=(op_cost-dual_lower)*1e6,pricing_row_dual=pi,operating_cost=op_cost,
                    primal_error=float(info.max_primal_infeasibility),dual_error=float(info.max_dual_infeasibility))

def run(policy,name,start='2020-01-01',end='2025-12-31',cap=None,farm='flat',maxiter=35):
    begin=time.perf_counter();config=json.loads((ROOT/'configuration.json').read_text());bs,hs=annual_costs(config)
    cap=config['cap_kg_day'] if cap is None else cap
    f=frame_for(start,end,farm);T=len(f);codes,days=pd.factorize(f.date,sort=False)
    Y=sum(1/(366 if pd.Timestamp(d).is_leap_year else 365) for d in days)
    g,d,p=(f[k].to_numpy(float) for k in ('g','d','price'))
    ref=np.dot(p,np.minimum(g,d)*(p>=0 if policy=='A' else 1))/(1000*Y)
    best=min(range(len(hs)),key=lambda j:hs[j]['kWh_kg']);hprod=hs[best]
    assert np.ptp([h['annual']/h['MW'] for h in hs])<1e-10
    m=Matrix();n=m.variables(c=hprod['annual']);q=m.variables(T,c=-p/(1000*Y),
                   lo=np.minimum(g,d) if policy=='B' else 0,hi=np.minimum(g,d) if policy=='B' else np.inf)
    v=m.variables(T,c=-(config['netback']-hprod['variable_GBP_kg'])/(hprod['kWh_kg']*Y))
    rg=m.nr;m.rows(T,[(q,1),(v,1)],hi=g)
    rs=m.nr;m.rows(T,[(q,1)],hi=d)
    rh=m.nr;m.rows(T,[(v,1)],lo=0)
    m.rows(T,[(v,1),(n,-hprod['unit_GWh'])],hi=0)
    m.rr.append((m.nr+codes).astype(np.int32));m.cc.append(v);m.val.append(np.full(T,1/hprod['kWh_kg']))
    m.nr+=len(days);m.rl.append(np.full(len(days),-np.inf));m.ru.append(np.full(len(days),cap/1e6))
    master=highslp(m,solver='ipm',crossover='on');del m
    pricing=[Pricing(b,T,.5,Y) for b in bs]
    cols=[];trace=[];last_solutions=[]
    ceiling=(np.dot(np.maximum(p,0),d)/1000+len(days)*cap*config['netback']/1e6)/Y
    bmax=np.array([max(0,(ceiling-ref)/b['annual']) for b in bs])
    out=ROOT/'results';out.mkdir(exist_ok=True)
    for iteration in range(maxiter):
        master.run();assert master.getModelStatus()==highspy.HighsModelStatus.kOptimal,str(master.getModelStatus())
        solution=master.getSolution();dual=np.array(solution.row_dual)
        charge_cost=-dual[rg:rg+T]
        sale_value=p/(1000*Y)+dual[rs:rs+T]
        if policy=='B':sale_value=np.where(d>g,sale_value,-1e10)
        h2_value=-dual[rg:rg+T]-dual[rh:rh+T]
        value=np.maximum(sale_value,h2_value);solutions=[]
        for j,pricer in enumerate(pricing):
            plan=pricer.solve(charge_cost,value,g>d if policy=='B' else None);plan['sale']=np.where(sale_value>=h2_value,plan['discharge'],0)
            plan['hydrogen']=plan['discharge']-plan['sale'];plan['type']=j
            solutions.append(plan)
        reduced=np.array([x['reduced_cost_lower'] for x in solutions]);profit=-master.getObjectiveValue()-ref
        correction=float(np.dot(bmax,np.maximum(-reduced,0)))
        trace.append(dict(iteration=iteration,restricted_profit=float(profit),upper_profit=float(profit+correction),
                          reduced_costs=reduced.tolist(),seconds=time.perf_counter()-begin))
        print(name,trace[-1],flush=True)
        (out/(name+'_progress.json')).write_text(json.dumps(trace,indent=2))
        last_solutions=solutions
        if correction<.01 or reduced.min()>-1e-9:break
        for j,plan in enumerate(solutions):
            if plan['reduced_cost']>=-1e-9:continue
            i=master.getNumCol();coef=np.r_[plan['charge']-plan['hydrogen'],plan['sale'],-plan['hydrogen']]
            indices=np.r_[rg+np.arange(T),rs+np.arange(T),rh+np.arange(T)]
            mask=abs(coef)>1e-13
            obj=bs[j]['annual']-np.dot(p,plan['sale'])/(1000*Y)
            master.addCol(float(obj),0,highspy.kHighsInf,int(mask.sum()),indices[mask].astype(np.int32),coef[mask])
            cols.append((i,plan))
        master.setOptionValue('solver','simplex')
    # Save the solved restricted-master solution, not unoptimised columns.
    x=np.array(solution.col_value);flow={b['id']:{k:np.zeros(T) for k in ('charge','sale','hydrogen','stock')} for b in bs}
    counts={p['id']:0. for p in bs+hs};counts[hprod['id']]=float(x[n])
    for ix,plan in cols:
        if ix>=len(x):continue
        weight=x[ix];bid=bs[plan['type']]['id'];counts[bid]+=float(weight)
        for k in flow[bid]:flow[bid][k]+=weight*plan[k]
    s=f[['date','g','d','price']].copy();s['direct']=x[q]
    for b in bs:
        for k,a in flow[b['id']].items():s[b['id']+'__'+k]=a
    for h in hs:s[h['id']+'__input']=x[v] if h['id']==hprod['id'] else 0.
    s['charge']=sum(flow[b['id']]['charge'] for b in bs);s['battery_sale']=sum(flow[b['id']]['sale'] for b in bs)
    s['battery_h2']=sum(flow[b['id']]['hydrogen'] for b in bs);s['h2_input']=x[v]
    s['generation_h2']=s.h2_input-s.battery_h2;s['h2_kg']=s.h2_input*1e6/hprod['kWh_kg']
    s['sales']=s.direct+s.battery_sale;s['unused']=g-s.direct-s.charge-s.generation_h2;s['unserved']=d-s.sales
    meta=dict(name=name,policy=policy,cap_kg_day=cap,years=Y,dt_hours=.5,periods=T,days=len(days),
              relaxation=True,annual_increment_mGBP=float(profit),upper_increment_mGBP=float(profit+correction),
              annual_reference_mGBP=float(ref),investment=counts,active_products={'batteries':bs,'electrolysers':hs},
              battery_MWh=sum(counts[b['id']]*b['E_MWh'] for b in bs),
              electrolyser_MW=counts[hprod['id']]*hprod['MW'],trace=trace,runtime_seconds=time.perf_counter()-begin,
              farm_profile=farm,
              pricing_audit=[{k:plan[k] for k in ('type','reduced_cost','reduced_cost_lower','pricing_dual_gap_GBP','operating_cost','primal_error','dual_error')} for plan in last_solutions],
              master_primal_error=float(master.getInfo().max_primal_infeasibility),
              master_dual_error=float(master.getInfo().max_dual_infeasibility),
              method='Dantzig-Wolfe battery trajectories; continuous investment/min-load/B-priority relaxation',
              stopping_bound_correction_mGBP=correction)
    (out/(name+'.json')).write_text(json.dumps(meta,indent=2));s.to_csv(out/(name+'_schedule.csv.gz'),index_label='utc',compression='gzip',float_format='%.12g')
    certificate={'master_row_dual':dual,'charge_opportunity':charge_cost,'sale_value':sale_value,'hydrogen_value':h2_value}
    for j,plan in enumerate(last_solutions):
        for key in ('charge','sale','hydrogen','stock'):certificate[f'b{j}_{key}']=plan[key]
        certificate[f'b{j}_row_dual']=plan['pricing_row_dual']
    np.savez_compressed(out/(name+'_certificate.npz'),**certificate)
    print('FINISHED',name,meta['battery_MWh'],meta['electrolyser_MW'],meta['annual_increment_mGBP'],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--policy',required=True);ap.add_argument('--name',required=True)
    ap.add_argument('--start',default='2020-01-01');ap.add_argument('--end',default='2025-12-31');ap.add_argument('--cap',type=float)
    ap.add_argument('--farm',default='flat');ap.add_argument('--maxiter',type=int,default=35)
    a=ap.parse_args();run(a.policy,a.name,a.start,a.end,a.cap,a.farm,a.maxiter)
