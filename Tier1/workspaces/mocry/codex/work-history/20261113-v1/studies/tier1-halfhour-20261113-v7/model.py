"""Half-hour product investment model. GWh, GBP2020 million/year.

Twelve integer investment counts, half-hour stock and dispatch, a DAILY
hydrogen acceptance constraint. Nonconvex operating rows are added until
every original operating rule is satisfied. Bounds remain explicitly saved.
"""
from pathlib import Path
import argparse, json, math, time, tempfile, shutil
import numpy as np
import pandas as pd
import highspy
from scipy.sparse import coo_matrix

ROOT=Path(__file__).resolve().parent

def annual_costs(config):
    bs=json.loads(json.dumps(config['batteries']));hs=json.loads(json.dumps(config['electrolysers']))
    def crf(r,n):return r/(1-(1+r)**-n) if r else 1/n
    for b in bs:
        b['eta']=math.sqrt(b['rte']);b['usable']=b['E_MWh']*(b['soc_upper']-b['soc_lower'])/1000
        b['commission_GBP']=b['soc_lower']*b['E_MWh']/b['eta']*config['commission_price']
        b['annual']=(crf(config['r'],b['life'])*(b['capital_GBP']+b['commission_GBP'])+b['fom_GBP'])/1e6
        b['retention']=(1-b['self_discharge'])**(config['dt_hours']/24)
    for h in hs:
        h.update(h['comparable']);pv=h['capital_GBP']+sum(h['replacement_GBP']/(1+config['r'])**y for y in h['replacement_years'])
        h['annual']=(crf(config['r'],h['life'])*pv+h['fom_GBP'])/1e6
        h['unit_GWh']=config['dt_hours']*h['MW']/1000
    return bs,hs

class Matrix:
    def __init__(self):
        self.n=0;self.nr=0;self.lb=[];self.ub=[];self.cost=[];self.ints=[]
        self.rr=[];self.cc=[];self.val=[];self.rl=[];self.ru=[]
    def variables(self,n=1,lo=0,hi=np.inf,c=0,integer=False):
        ix=np.arange(self.n,self.n+n,dtype=np.int32);self.n+=n
        for out,v in ((self.lb,lo),(self.ub,hi),(self.cost,c)):
            out.append(np.broadcast_to(v,(n,)).copy())
        self.ints.extend(ix.tolist() if integer else [])
        return ix if n!=1 else int(ix[0])
    def rows(self,n,terms,lo=-np.inf,hi=np.inf):
        rows=np.arange(self.nr,self.nr+n,dtype=np.int32);self.nr+=n
        for idx,v in terms:
            self.rr.append(rows);self.cc.append(np.broadcast_to(idx,(n,)).astype(np.int32))
            self.val.append(np.broadcast_to(v,(n,)).astype(float))
        self.rl.append(np.broadcast_to(lo,(n,)).copy());self.ru.append(np.broadcast_to(hi,(n,)).copy())
    def sparse(self):
        return coo_matrix((np.concatenate(self.val),(np.concatenate(self.rr),np.concatenate(self.cc))),shape=(self.nr,self.n)).tocsc()

def frame_for(start,end,farm='flat',daily=False):
    f=pd.read_csv(ROOT/'inputs/halfhour.csv.gz');f['utc']=pd.to_datetime(f.utc,utc=True)
    f=f.set_index('utc').loc[start:end].copy()
    f['g']=(f.background_MW+f[f'farm_{farm}_MW'])*.0005
    f['d']=f.demand_MW*.0005
    if daily:
        f=f.groupby('date').agg(g=('g','sum'),d=('d','sum'),price=('price','mean'))
        f['date']=f.index;f.index=pd.to_datetime(f.index,utc=True)
    assert f.groupby('date').size().eq(1 if daily else 48).all()
    return f

def solve(f,config,policy,name,cap=None,seconds=600,no_battery=False,fixed=None,
          relaxation=False,threads=8,lp_solver='choose'):
    begun=time.perf_counter();outdir=ROOT/'results';outdir.mkdir(exist_ok=True)
    bs,hs=annual_costs(config);cap=config['cap_kg_day'] if cap is None else cap
    dt=config['dt_hours'];T=len(f);daycode,days=pd.factorize(f.date,sort=False)
    Y=sum(1/(366 if pd.Timestamp(d).is_leap_year else 365) for d in days)
    g,d,p=(f[k].to_numpy(float) for k in ('g','d','price'))
    ref=float(np.dot(p,np.minimum(g,d)*(p>=0 if policy=='A' else 1))/(1000*Y))
    ceiling=(float(np.dot(np.maximum(p,0),d))/1000+len(days)*cap*config['netback']/1e6)/Y
    bmax=[0 if no_battery else max(0,math.ceil((ceiling-ref)/b['annual'])) for b in bs]
    hmax=[math.ceil(cap/(h['kg_hour']*dt)) for h in hs]
    if relaxation:
        # With divisible capacity and no minimum-load rules, all comparable
        # electrolysers have identical cost/MW. The most efficient one exactly
        # dominates the others, so remove only redundant relaxation columns.
        rates=[h['annual']/h['MW'] for h in hs]
        assert max(rates)-min(rates)<1e-10
        best=min(range(len(hs)),key=lambda j:hs[j]['kWh_kg'])
        hmax=[u if j==best else 0 for j,u in enumerate(hmax)]
    if fixed:
        bmax=[int(fixed.get(b['id'],0)) for b in bs];hmax=[int(fixed.get(h['id'],0)) for h in hs]
    m=Matrix()
    nb=[m.variables(hi=u,lo=u if fixed else 0,c=b['annual'],integer=not relaxation and u>0) for b,u in zip(bs,bmax)]
    nh=[m.variables(hi=u,lo=u if fixed else 0,c=h['annual'],integer=not relaxation and u>0) for h,u in zip(hs,hmax)]
    zero=m.variables(hi=0);zeros=np.full(T,zero,dtype=np.int32)
    q=m.variables(T,hi=np.minimum(g,d),lo=np.minimum(g,d) if policy=='B' else 0,c=-p/(1000*Y))
    gen=[(q,1)];sale=[(q,1)];hbalance=[];bv=[];hv=[]
    for b,n,u in zip(bs,nb,bmax):
        if u==0:
            bv.append(dict(charge=zeros,sale=zeros,hydrogen=zeros,stock=zeros));continue
        eta=b['eta'];U=u*b['usable'];P=dt*b['P_MW']/1000
        c=m.variables(T,hi=np.minimum(g,min(U/eta,u*P)))
        r=m.variables(T,hi=np.minimum(d,min(U*eta,u*P)),c=-p/(1000*Y))
        bh=m.variables(T,hi=min(U*eta,u*P,cap*max(h['kWh_kg'] for h in hs)/1e6))
        s=m.variables(T,hi=U)
        bv.append(dict(charge=c,sale=r,hydrogen=bh,stock=s))
        gen.extend([(c,1),(bh,-1)]);sale.append((r,1));hbalance.append((bh,-1))
        m.rows(1,[(s[0],1),(c[0],-eta),(r[0],1/eta),(bh[0],1/eta)],0,0)
        m.rows(T-1,[(s[1:],1),(s[:-1],-b['retention']),(c[1:],-eta),(r[1:],1/eta),(bh[1:],1/eta)],0,0)
        m.rows(T,[(s,1),(n,-b['usable'])],hi=0)
        m.rows(T,[(c,1),(n,-P)],hi=0)
        m.rows(T,[(r,1),(bh,1),(n,-P)],hi=0)
        m.rows(1,[(s[-1],1)],0,0)
        if dt==24:
            m.rows(T,[(c,eta),(n,-b['usable'])],hi=0)
            m.rows(T,[(r,1/eta),(bh,1/eta),(n,-b['usable'])],hi=0)
    for h,n,u in zip(hs,nh,hmax):
        if u==0:
            hv.append(zeros);continue
        v=m.variables(T,hi=np.minimum(g+sum(b['usable']*u*b['eta'] for b,u in zip(bs,bmax)),u*h['unit_GWh']),
                      c=-(config['netback']-h['variable_GBP_kg'])/(h['kWh_kg']*Y))
        hv.append(v);gen.append((v,1));hbalance.append((v,1))
        m.rows(T,[(v,1),(n,-h['unit_GWh'])],hi=0)
    m.rows(T,gen,hi=g);m.rows(T,sale,hi=d);m.rows(T,hbalance,lo=0)
    # Sum hydrogen across the 48 periods, once per UTC day.
    rows=m.nr+daycode;m.nr+=len(days)
    for h,v,u in zip(hs,hv,hmax):
        if u==0:continue
        m.rr.append(rows.astype(np.int32));m.cc.append(v);m.val.append(np.full(T,1/h['kWh_kg']))
    m.rl.append(np.full(len(days),-np.inf));m.ru.append(np.full(len(days),cap/1e6))
    cost=np.concatenate(m.cost);lower=np.concatenate(m.lb);upper=np.concatenate(m.ub)
    mat=m.sparse();rl=np.concatenate(m.rl);ru=np.concatenate(m.ru)
    scales=np.ones(m.n)
    if relaxation:
        # The divisible relaxation uses capacity variables in GWh instead of
        # potentially millions of small cabinet counts. This is an exact
        # column scaling and removes tiny linking coefficients.
        for n,b in zip(nb,bs):scales[n]=b['usable']
        for n,h in zip(nh,hs):scales[n]=h['unit_GWh']
        mat.data/=np.repeat(scales,np.diff(mat.indptr))
        cost=cost/scales;lower=lower*scales;upper=upper*scales
    print(name,'BUILD',T,m.n,m.nr,mat.nnz,'seconds',time.perf_counter()-begun,flush=True)
    solver=highspy.Highs();solver.setOptionValue('output_flag',False)
    solver.setOptionValue('threads',threads);solver.setOptionValue('time_limit',seconds)
    solver.setOptionValue('mip_rel_gap',1e-9);solver.setOptionValue('mip_abs_gap',1e-7);solver.setOptionValue('random_seed',0)
    logfile=Path(tempfile.gettempdir())/('mmcs_v7_'+name+'.log')
    solver.setOptionValue('log_file',str(logfile))
    solver.setOptionValue('log_to_console',False);solver.setOptionValue('output_flag',True)
    if relaxation:solver.setOptionValue('solver',lp_solver)
    lp=highspy.HighsLp();lp.num_col_=m.n;lp.num_row_=m.nr
    # Offset removes the large unchanged electricity business from the MIP
    # gap denominator; tolerance is measured on incremental investment value.
    lp.offset_=ref
    lp.col_cost_=cost;lp.col_lower_=lower;lp.col_upper_=upper;lp.row_lower_=rl;lp.row_upper_=ru
    lp.a_matrix_.format_=highspy.MatrixFormat.kColwise;lp.a_matrix_.start_=mat.indptr
    lp.a_matrix_.index_=mat.indices;lp.a_matrix_.value_=mat.data
    solver.passModel(lp)
    if m.ints:solver.changeColsIntegrality(len(m.ints),np.array(m.ints,dtype=np.int32),np.ones(len(m.ints),dtype=np.uint8))
    del lp,mat,m
    seen_h=set();seen_b=set();seen_p=set();iterations=[]
    def row(indices,values,lo=-np.inf,hi=np.inf):
        solver.addRow(lo,hi,len(indices),np.asarray(indices,dtype=np.int32),np.asarray(values,dtype=float))
    def binary():
        i=solver.getNumCol();solver.addVar(0,1);solver.changeColIntegrality(i,highspy.HighsVarType.kInteger);return i
    for iteration in range(12):
        solver.run();info=solver.getInfo();sol=solver.getSolution();status=solver.getModelStatus()
        if not sol.value_valid:raise RuntimeError((name,str(status)))
        x=np.array(sol.col_value)
        if relaxation:x=x/scales
        fresh_h=[];fresh_b=[];fresh_p=[]
        if not relaxation:
            for j,h in enumerate(hs):
                v=x[hv[j]];unit=h['unit_GWh'];bad=np.flatnonzero((v>1e-8)&(v<h['minimum']*unit-1e-8))
                fresh_h.extend((j,int(t)) for t in bad)
            for j,v in enumerate(bv):
                bad=np.flatnonzero(np.minimum(x[v['charge']],x[v['sale']]+x[v['hydrogen']])>1e-8)
                fresh_b.extend((j,int(t)) for t in bad)
            if policy=='B':
                available=sum(np.minimum(np.r_[0,x[v['stock']][:-1]]*b['retention']*b['eta'],x[n]*dt*b['P_MW']/1000)
                              for b,v,n in zip(bs,bv,nb))
                actual=sum(x[v['sale']] for v in bv)
                fresh_p=np.flatnonzero((d>g)&(abs(actual-np.minimum(d-g,available))>1e-8)).tolist()
        bound=float(info.mip_dual_bound) if not relaxation else float(info.objective_function_value)
        # On a time-limited LP without a dual certificate, do not claim a bound.
        if relaxation and status!=highspy.HighsModelStatus.kOptimal:bound=None
        it=dict(iteration=iteration,status=str(status),profit=-float(info.objective_function_value),
                upper_profit=None if bound is None else -bound,
                h_violations=len(fresh_h),direction_violations=len(fresh_b),priority_violations=len(fresh_p),
                elapsed=time.perf_counter()-begun)
        iterations.append(it);print(name,it,flush=True)
        if relaxation or not(fresh_h or fresh_b or fresh_p):break
        assert set(fresh_h)-seen_h or set(fresh_b)-seen_b or set(fresh_p)-seen_p,'Unclosed operating violation'
        for j,t in set(fresh_h)-seen_h:
            h=hs[j];z=binary();v=hv[j][t]
            row([v,z],[1,-hmax[j]*h['unit_GWh']],hi=0)
            row([v,z],[1,-h['minimum']*h['unit_GWh']],lo=0)
        for j,t in set(fresh_b)-seen_b:
            b=bs[j];v=bv[j];z=binary();M=bmax[j]*dt*b['P_MW']/1000
            row([v['charge'][t],z],[1,-min(g[t],M)],hi=0)
            row([v['sale'][t],v['hydrogen'][t],z],[1,1,M],hi=M)
        for t in set(fresh_p)-seen_p:
            deficit=d[t]-g[t];served=binary()
            row([v['sale'][t] for v in bv]+[served],[1]*len(bv)+[-deficit],lo=0)
            if t==0:continue
            for b,v,n,u in zip(bs,bv,nb,bmax):
                if u==0:continue
                z=binary();P=dt*b['P_MW']/1000;M=max(u*P,u*b['usable']*b['eta'])
                row([v['sale'][t],n,z,served],[1,-P,M,M],lo=0)
                row([v['sale'][t],v['stock'][t-1],z,served],[1,-b['retention']*b['eta'],-M,M],lo=-M)
        seen_h.update(fresh_h);seen_b.update(fresh_b);seen_p.update(fresh_p)
    else:raise RuntimeError('Operating cuts did not converge')
    schedule=f[['date','g','d','price']].copy();schedule['direct']=x[q]
    for b,v in zip(bs,bv):
        for key,ix in v.items():schedule[b['id']+'__'+key]=x[ix]
    for h,ix in zip(hs,hv):schedule[h['id']+'__input']=x[ix]
    schedule['charge']=sum(x[v['charge']] for v in bv)
    schedule['battery_sale']=sum(x[v['sale']] for v in bv)
    schedule['battery_h2']=sum(x[v['hydrogen']] for v in bv)
    schedule['h2_input']=sum(x[v] for v in hv)
    schedule['generation_h2']=schedule.h2_input-schedule.battery_h2
    schedule['h2_kg']=sum(x[v]*1e6/h['kWh_kg'] for h,v in zip(hs,hv))
    schedule['sales']=schedule.direct+schedule.battery_sale
    schedule['unused']=g-schedule.direct-schedule.charge-schedule.generation_h2
    schedule['unserved']=d-schedule.sales
    electricity=float(np.dot(p,schedule.sales)/(1000*Y));hydrogen=float(schedule.h2_kg.sum()*config['netback']/(1e6*Y))
    fixedcost=sum(x[n]*b['annual'] for n,b in zip(nb,bs))+sum(x[n]*h['annual'] for n,h in zip(nh,hs))
    variable=sum(np.sum(x[v])*h['variable_GBP_kg']/(h['kWh_kg']*Y) for v,h in zip(hv,hs))
    investment={v['id']:float(x[n]) for v,n in list(zip(bs,nb))+list(zip(hs,nh))}
    summary=dict(name=name,policy=policy,dt_hours=dt,periods=T,days=len(days),years=Y,cap_kg_day=cap,
                 relaxation=relaxation,exact_operating_feasible=not relaxation and not(fresh_h or fresh_b or fresh_p),
                 status=str(status),annual_profit_mGBP=electricity+hydrogen-variable-fixedcost,
                 annual_increment_mGBP=electricity+hydrogen-variable-fixedcost-ref,
                 annual_reference_mGBP=ref,upper_increment_mGBP=iterations[-1]['upper_profit'],
                 annual_electricity_mGBP=electricity,annual_hydrogen_mGBP=hydrogen,annual_equipment_mGBP=float(fixedcost),
                 initial_capex_mGBP=float(sum(investment[v['id']]*v['capital_GBP']/1e6 for v in bs+hs)),
                 battery_MWh=sum(investment[b['id']]*b['E_MWh'] for b in bs),
                 electrolyser_MW=sum(investment[h['id']]*h['MW'] for h in hs),investment=investment,
                 annual_h2_tonnes=float(schedule.h2_kg.sum()/1000/Y),demand_coverage=float(schedule.sales.sum()/d.sum()) if d.sum()>0 else None,
                 annual_unused_GWh=float(schedule.unused.sum()/Y),annual_unserved_GWh=float(schedule.unserved.sum()/Y),
                 annual_battery_sales_GWh=float(schedule.battery_sale.sum()/Y),annual_battery_H2_GWh=float(schedule.battery_h2.sum()/Y),
                 runtime_seconds=time.perf_counter()-begun,variables=solver.getNumCol(),rows=solver.getNumRow(),
                 iterations=iterations,active_products={'batteries':bs,'electrolysers':hs})
    (outdir/(name+'.json')).write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
    schedule.to_csv(outdir/(name+'_schedule.csv.gz'),index_label='utc',compression='gzip',float_format='%.12g')
    if logfile.exists():shutil.copy2(logfile,outdir/(name+'.log'))
    print('FINISHED',name,summary['battery_MWh'],summary['electrolyser_MW'],summary['annual_increment_mGBP'],flush=True)
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--start',default='2020-01-01');ap.add_argument('--end',default='2025-12-31')
    ap.add_argument('--policy',choices=['A','B'],required=True);ap.add_argument('--name',required=True)
    ap.add_argument('--cap',type=float);ap.add_argument('--seconds',type=float,default=600)
    ap.add_argument('--no-battery',action='store_true');ap.add_argument('--relax',action='store_true')
    ap.add_argument('--daily',action='store_true');ap.add_argument('--farm',choices=['flat','proxy'],default='flat')
    ap.add_argument('--fixed');ap.add_argument('--threads',type=int,default=8);ap.add_argument('--lp-solver',default='choose')
    a=ap.parse_args();cfg=json.loads((ROOT/'configuration.json').read_text());cfg['dt_hours']=24 if a.daily else .5
    f=frame_for(a.start,a.end,a.farm,a.daily)
    fixed=json.loads(Path(a.fixed).read_text()) if a.fixed else None
    solve(f,cfg,a.policy,a.name,a.cap,a.seconds,a.no_battery,fixed,a.relax,a.threads,a.lp_solver)
