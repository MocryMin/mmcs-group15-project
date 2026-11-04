"""Baseline 1104: researched Tier1 investment cases and chronological checks.

Internal units are GWh, GW and million constant-2020 GBP. Xpress is the
course implementation. The optional full-panel reference uses scipy/HiGHS
when its size exceeds the locally installed Xpress Community licence.
"""
from pathlib import Path
import argparse
import calendar
import csv
import hashlib
import json
import math
import os
import time

import numpy as np
import pandas as pd
import xpress as xp

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
REPO = PROJECT / "group-collaboration"
RELEASE = REPO / "Tier1/public/data_quality/full_data_repair/20261104-v2"
RESEARCH = REPO / "Tier1/public/research_1103/controller/mocry-codex/20261103-v1.1"


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def crf(rate, years):
    return 1 / years if rate == 0 else rate / (1 - (1 + rate) ** -years)


def load_inputs():
    g = pd.read_csv(RELEASE / "data/daily_generation_total.csv", parse_dates=["date"]).set_index("date")
    d = pd.read_csv(RELEASE / "data/daily_demand.csv")
    d["date"] = pd.to_datetime(d.startTime, utc=True).dt.tz_localize(None)
    d = d.set_index("date")[["demand"]]
    w = pd.read_csv(RELEASE / "data/wind_farm_generation.csv", parse_dates=["date"]).set_index("date")
    p = pd.read_csv(RELEASE / "data/daily_market_index_price.csv", parse_dates=["date"]).set_index("date")
    z = pd.read_csv(RELEASE / "data/date_quality.csv", parse_dates=["date"]).set_index("date")
    f = g.join(d).join(w).join(p.iloc[:, :1]).join(z)
    assert len(f) == 2452 and f.notna().all().all()
    cpi_path = PROJECT / "research-1103-controlled/control/browser_captures/R4/ONS-CPI-CSV.csv"
    months = {}
    with cpi_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.reader(stream):
            try:
                stamp = pd.to_datetime(row[0], format="%Y %b")
                months[stamp.strftime("%Y-%m")] = float(row[1])
            except (ValueError, IndexError):
                continue
    f["CPI"] = [months[t.strftime("%Y-%m")] for t in f.index]
    f["price"] = f.iloc[:, 3] * 108.7 / f.CPI
    f["G"] = 24 * (f.total_MW + f.wind_farm_MW) / 1000
    f["D"] = 24 * f.demand / 1000
    assert np.isfinite(f[["G", "D", "price"]].to_numpy()).all()
    return f, cpi_path


def annual_fraction(f):
    return sum(1 / (366 if calendar.isleap(t.year) else 365) for t in f.index)


def settings(**changes):
    ref = json.loads((RESEARCH / "BASELINE_CANDIDATE.json").read_text(encoding="utf-8"))
    b, h = ref["battery"], ref["hydrogen"]
    out = dict(
        rate=.05, battery_unit_MWh=3., battery_unit_MW=1.5,
        battery_cost_MWh=b["CAPEX_GBP2020_MWh"],
        battery_FOM_MW=b["FOM_primary_GBP2020_MWyr"], battery_life=15,
        eta=math.sqrt(.9), soc_window=.6,
        hydrogen_unit_MW=20., hydrogen_kWh_kg=55.9, hydrogen_min=.2,
        hydrogen_cost_MW=h["modern_CAPEX"]["CAPEX_GBP2020_per_kW_assumed_electrical"]["analyst_midpoint"] * 1000,
        hydrogen_FOM_MW=h["FOM_absolute_proxy_GBP2020_kWe_yr"] * 1000,
        hydrogen_replacement_MW=h["replacement_absolute_proxy_GBP2020_kWe"] * 1000,
        hydrogen_replacement_years=[11, 22], hydrogen_life=30,
        hydrogen_price=h["supported_H2_reporting_case"]["GBP2020_per_kg"],
        hydrogen_limit_kg=10000., self_discharge=0.,
        commission_price_GBP_MWh=None,
    )
    out.update(changes)
    return out


def capital_costs(cfg, f):
    r = cfg["rate"]
    bc = cfg["battery_cost_MWh"] * cfg["battery_unit_MWh"]
    # The lower SOC buffer cannot produce free initial sales. Its one-off
    # commissioning cost uses the design-panel mean positive electricity value.
    commission_price = cfg["commission_price_GBP_MWh"]
    if commission_price is None:
        commission_price = max(0., float(f.price.mean()))
    commission = .2 * cfg["battery_unit_MWh"] / cfg["eta"] * commission_price
    hc = cfg["hydrogen_cost_MW"] * cfg["hydrogen_unit_MW"]
    replacement_pv = cfg["hydrogen_replacement_MW"] * cfg["hydrogen_unit_MW"] * sum(
        (1 + r) ** -y for y in cfg["hydrogen_replacement_years"])
    bannual = (bc + commission) * crf(r, cfg["battery_life"]) + cfg["battery_FOM_MW"] * cfg["battery_unit_MW"]
    hannual = (hc + replacement_pv) * crf(r, cfg["hydrogen_life"]) + cfg["hydrogen_FOM_MW"] * cfg["hydrogen_unit_MW"]
    return dict(battery_CAPEX_unit=bc, hydrogen_CAPEX_unit=hc,
                battery_annual_unit=bannual, hydrogen_annual_unit=hannual,
                commissioning_unit=commission, commissioning_price=commission_price,
                hydrogen_replacement_PV_unit=replacement_pv)


class LinearModel:
    def __init__(self):
        self.names, self.lower, self.upper, self.integer, self.objective = [], [], [], [], []
        self.rows, self.row_lower, self.row_upper = [], [], []

    def var(self, name, lower=0., upper=math.inf, integer=False, objective=0.):
        index = len(self.names)
        self.names.append(name); self.lower.append(lower); self.upper.append(upper)
        self.integer.append(int(integer)); self.objective.append(objective)
        return index

    def row(self, coefficients, lower=-math.inf, upper=math.inf):
        self.rows.append(coefficients); self.row_lower.append(lower); self.row_upper.append(upper)

    def solve(self, backend="xpress", time_limit=90):
        started = time.monotonic()
        if backend == "xpress":
            p = xp.problem(); p.controls.outputlog = 0; p.controls.threads = 4
            p.controls.maxtime = time_limit; p.controls.miprelstop = 1e-7; p.controls.mipabsstop = 1e-5
            v = [p.addVariable(name=name, lb=self.lower[i], ub=self.upper[i],
                               vartype=xp.integer if self.integer[i] else xp.continuous)
                 for i, name in enumerate(self.names)]
            for a, lo, hi in zip(self.rows, self.row_lower, self.row_upper):
                expr = xp.Sum(coef * v[i] for i, coef in a.items())
                if lo == hi: p.addConstraint(expr == lo)
                else:
                    if math.isfinite(lo): p.addConstraint(expr >= lo)
                    if math.isfinite(hi): p.addConstraint(expr <= hi)
            p.setObjective(xp.Sum(c * v[i] for i, c in enumerate(self.objective) if c), xp.maximize)
            p.solve()
            if p.attributes.solstatus != 1:
                raise RuntimeError(f"No optimal solution: {p.attributes.solvestatus}/{p.attributes.solstatus}")
            value = np.array(p.getSolution(v), dtype=float)
            record = dict(backend="Xpress 9.9", optimal=True, objective_mGBP=float(p.attributes.objval),
                          best_bound_mGBP=float(p.attributes.bestbound), rows=int(p.attributes.rows),
                          columns=int(p.attributes.cols))
        else:
            from scipy.optimize import milp, Bounds, LinearConstraint
            from scipy.sparse import coo_matrix
            rr, cc, vv = [], [], []
            for j, a in enumerate(self.rows):
                for i, coef in a.items(): rr.append(j); cc.append(i); vv.append(coef)
            matrix = coo_matrix((vv, (rr, cc)), shape=(len(self.rows), len(self.names))).tocsc()
            r = milp(-np.array(self.objective), integrality=np.array(self.integer),
                     bounds=Bounds(self.lower, self.upper),
                     constraints=LinearConstraint(matrix, self.row_lower, self.row_upper),
                     options={"time_limit":time_limit, "mip_rel_gap":1e-7})
            if not r.success: raise RuntimeError(r.message)
            value = r.x
            record = dict(backend="SciPy/HiGHS reference", optimal=True, objective_mGBP=float(-r.fun),
                          best_bound_mGBP=float(-r.mip_dual_bound), rows=len(self.rows), columns=len(self.names))
        row_values = np.array([sum(c * value[i] for i, c in a.items()) for a in self.rows])
        violation = max(0., float(np.max(np.array(self.lower)-value)), float(np.max(value-np.array(self.upper))),
                        float(np.max(np.array(self.row_lower)-row_values)), float(np.max(row_values-np.array(self.row_upper))))
        int_error = max([abs(value[i] - round(value[i])) for i, flag in enumerate(self.integer) if flag] or [0.])
        assert violation < 1e-5 and int_error < 1e-4, (violation, int_error)
        record.update(seconds=time.monotonic()-started, max_linear_violation=violation, max_integer_error=int_error)
        return value, record


def formulate(f, cfg, policy, chronology, allow_b=True, allow_h=True, fixed=None):
    m = LinearModel(); years = annual_fraction(f); costs = capital_costs(cfg, f)
    u = cfg["soc_window"] * cfg["battery_unit_MWh"] / 1000
    eta = cfg["eta"]; hunit = 24 * cfg["hydrogen_unit_MW"] / 1000
    # Pool: no gain beyond enough energy capacity for the largest daily transfer.
    # Chronology: enough capacity to hold all supplied energy is a finite bound.
    bmax = math.ceil((max(eta*f.G.max(), f.D.max()/eta) if not chronology else eta*f.G.sum()) / u) + 1
    hmax = math.ceil(min(f.G.max(), cfg["hydrogen_limit_kg"]*cfg["hydrogen_kWh_kg"]/1e6) / hunit)
    nb = m.var("battery_units", fixed[0] if fixed else 0, fixed[0] if fixed else (bmax if allow_b else 0), True, -costs["battery_annual_unit"]/1e6)
    nh = m.var("electrolyser_units", fixed[1] if fixed else 0, fixed[1] if fixed else (hmax if allow_h else 0), True, -costs["hydrogen_annual_unit"]/1e6)
    flows = {k: [] for k in ("q", "c", "d", "h", "online", "s")}
    for t, row in enumerate(f.itertuples()):
        mandatory = min(row.G, row.D) if policy == "B" else 0.
        q = m.var(f"sale_{t}", mandatory, min(row.G, row.D), objective=row.price/1000/years)
        c = m.var(f"charge_{t}", upper=row.G if allow_b else 0.)
        d = m.var(f"discharge_{t}", upper=row.D if allow_b else 0., objective=row.price/1000/years)
        h = m.var(f"electrolysis_{t}", upper=min(row.G, cfg["hydrogen_limit_kg"]*cfg["hydrogen_kWh_kg"]/1e6) if allow_h else 0., objective=cfg["hydrogen_price"]/cfg["hydrogen_kWh_kg"]/years)
        online = m.var(f"active_modules_{t}", upper=hmax if allow_h else 0., integer=True)
        for key, index in zip(("q", "c", "d", "h", "online"), (q, c, d, h, online)): flows[key].append(index)
        m.row({q:1, c:1, h:1}, upper=row.G)
        m.row({q:1, d:1}, upper=row.D)
        if not chronology:
            m.row({c:1, nb:-u/eta}, upper=0)
            m.row({d:1, nb:-u*eta}, upper=0)
        # In chronology these bounds follow from bounded stock and one-way
        # operation. The equivalent no-cycle schedule is recovered below.
        m.row({online:1, nh:-1}, upper=0)
        m.row({h:1, online:-hunit}, upper=0)
        m.row({h:1, online:-cfg["hydrogen_min"]*hunit}, lower=0)
        if chronology:
            s = m.var(f"usable_stock_{t}")
            flows["s"].append(s)
            eq = {s:1, c:-eta, d:1/eta}
            if t and f.index[t-1].year == f.index[t].year:
                assert (f.index[t]-f.index[t-1]).days == 1, "Unmodelled calendar gap"
                eq[flows["s"][t-1]] = -(1-cfg["self_discharge"])
            m.row(eq, lower=0, upper=0)
            m.row({s:1, nb:-u}, upper=0)
            if t == len(f)-1 or f.index[t+1].year != f.index[t].year: m.row({s:1}, upper=0)
    if not chronology:
        for year in sorted(set(f.index.year)):
            eq = {flows["d"][t]:1 for t in range(len(f)) if f.index[t].year == year}
            eq.update({flows["c"][t]:-eta**2 for t in range(len(f)) if f.index[t].year == year})
            m.row(eq, lower=0, upper=0)
    return m, (nb, nh), flows, costs


def summarize(name, f, cfg, policy, chronology, nb, nh, schedule, record, costs):
    years = annual_fraction(f); eta = cfg["eta"]
    q,c,d,h = [schedule[k].to_numpy(copy=True) for k in ("q", "c", "d", "h")]
    # A has an equally profitable schedule without simultaneous charge/discharge.
    # Eliminate a cycle, leave its conversion loss unused, and preserve sales and
    # the internal stock increment exactly. B already has disjoint surplus/deficit.
    overlap = np.minimum(d, eta**2*c)
    if policy == "A": q += overlap; d -= overlap; c -= overlap/eta**2
    schedule["q"],schedule["c"],schedule["d"] = q,c,d
    schedule["unused"] = f.G.to_numpy()-q-c-h
    schedule["deficit"] = f.D.to_numpy()-q-d
    er = float(np.dot(f.price, q+d)*1000/years)
    hr = float(h.sum()*1e6/cfg["hydrogen_kWh_kg"]*cfg["hydrogen_price"]/years)
    cost = nb*costs["battery_annual_unit"]+nh*costs["hydrogen_annual_unit"]
    net = er+hr-cost
    objective_error = abs(net/1e6-record["objective_mGBP"])
    violations = [0., -schedule[["q","c","d","h","unused","deficit"]].to_numpy().min(),
                  float(np.max(c-nb*cfg["soc_window"]*cfg["battery_unit_MWh"]/1000/eta)),
                  float(np.max(d-nb*cfg["soc_window"]*cfg["battery_unit_MWh"]/1000*eta)),
                  float(np.max(np.minimum(c,d))), objective_error]
    if policy == "B": violations.append(float(np.max(np.abs(q-np.minimum(f.G,f.D)))))
    assert max(violations) < 1e-4, (name, max(violations))
    out = dict(case=name, policy=policy, time_model="chronological_check" if chronology else "tier1_annual_energy_pool",
               years=sorted(set(map(int,f.index.year))), observations=len(f), annual_fraction=years,
               battery_units=int(round(nb)), battery_MW=nb*cfg["battery_unit_MW"], battery_MWh=nb*cfg["battery_unit_MWh"],
               electrolyser_units=int(round(nh)), electrolyser_MW=nh*cfg["hydrogen_unit_MW"],
               CAPEX_GBP2020=nb*costs["battery_CAPEX_unit"]+nh*costs["hydrogen_CAPEX_unit"],
               commissioning_GBP2020=nb*costs["commissioning_unit"],
               annual_equivalent_cost_GBP2020=cost, electricity_revenue_GBP2020_year=er,
               hydrogen_revenue_GBP2020_year=hr, net_profit_GBP2020_year=net,
               electricity_GWh_year=float((q+d).sum()/years), hydrogen_kg_year=float(h.sum()*1e6/cfg["hydrogen_kWh_kg"]/years),
               charge_GWh_year=float(c.sum()/years), discharge_GWh_year=float(d.sum()/years),
               unused_GWh_year=float(schedule.unused.sum()/years), deficit_GWh_year=float(schedule.deficit.sum()/years),
               demand_coverage=float((q+d).sum()/f.D.sum()),
               battery_equivalent_full_window_cycles_year=float(d.sum()/years/(nb*cfg["soc_window"]*cfg["battery_unit_MWh"]/1000*eta)) if nb else 0.,
               max_numeric_violation=float(max(violations)), solver=record, configuration=cfg)
    return out, schedule


def solve_case(name, f, cfg, policy="A", chronology=False, allow_b=True, allow_h=True, fixed=None, backend="xpress"):
    m, idx, flows, costs = formulate(f,cfg,policy,chronology,allow_b,allow_h,fixed)
    value, record = m.solve(backend)
    schedule = f[["G","D","price","strict_no_imputation"]].copy()
    for k, indexes in flows.items():
        if indexes: schedule[k] = value[indexes]
    return summarize(name,f,cfg,policy,chronology,value[idx[0]],value[idx[1]],schedule,record,costs)


def simple_rule(name, f, cfg, policy, capacity):
    nb,nh = capacity; eta=cfg["eta"]; U=nb*cfg["soc_window"]*cfg["battery_unit_MWh"]/1000
    hunit=24*cfg["hydrogen_unit_MW"]/1000
    schedule=f[["G","D","price","strict_no_imputation"]].copy()
    a={k:np.zeros(len(f)) for k in ["q","c","d","h","online","s"]}
    stock=0.
    for t, row in enumerate(f.itertuples()):
        if t==0 or f.index[t-1].year!=f.index[t].year: stock=0.
        q=min(row.G,row.D) if policy=="B" or row.price>0 else 0.
        available=min(row.G-q, cfg["hydrogen_limit_kg"]*cfg["hydrogen_kWh_kg"]/1e6)
        h,z=0.,0
        if cfg["hydrogen_price"]>0:
            for on in range(1,nh+1):
                candidate=min(available,hunit*on)
                if candidate>=cfg["hydrogen_min"]*hunit*on and candidate>h: h,z=candidate,on
        c=max(0.,min(row.G-q-h,(U-stock)/eta,U/eta))
        stock+=eta*c
        d=max(0.,min(row.D-q,stock*eta,U*eta)) if row.price>0 else 0.
        stock-=d/eta
        for k,v in zip(["q","c","d","h","online","s"],[q,c,d,h,z,stock]): a[k][t]=v
    # Remove unused final charges from each year without changing delivered output.
    for year in set(f.index.year):
        ids=np.where(f.index.year==year)[0]
        for t in ids[::-1]:
            suffix=ids[ids>=t]
            reduction=max(0.,min(a["c"][t],float(np.min(a["s"][suffix]))/eta))
            a["c"][t]-=reduction; a["s"][suffix]-=eta*reduction
        assert abs(a["s"][ids[-1]])<1e-6
    for k,v in a.items(): schedule[k]=v
    costs=capital_costs(cfg,f); years=annual_fraction(f)
    net=(float(np.dot(f.price,a["q"]+a["d"]))*1000+float(a["h"].sum()*1e6/cfg["hydrogen_kWh_kg"]*cfg["hydrogen_price"]))/years-nb*costs["battery_annual_unit"]-nh*costs["hydrogen_annual_unit"]
    record=dict(backend="simple current-day rule",optimal=False,objective_mGBP=net/1e6)
    return summarize(name,f,cfg,policy,True,nb,nh,schedule,record,costs)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--quick",action="store_true"); args=parser.parse_args()
    xp.init(os.environ.get("XPRESS_LICENSE_FILE","C:/xpressmp/bin/xpauth.xpr"))
    (HERE/"outputs").mkdir(exist_ok=True)
    f,cpi_path=load_inputs(); base=settings()
    base["commission_price_GBP_MWh"]=max(0.,float(f.loc["2023"].price.mean()))
    save_json(HERE/"parameters.json",base)
    f.to_csv(HERE/"model_inputs.csv",index_label="date")
    results=[]
    def run(name, frame=None, cfg=None, **kw):
        result,schedule=solve_case(name,f.loc["2023"] if frame is None else frame,base if cfg is None else cfg,**kw)
        results.append(result); schedule.to_csv(HERE/"outputs"/(name+".csv"),index_label="date")
        save_json(HERE/"results.json",results)
        print(name,result["battery_MW"],result["electrolyser_MW"],round(result["net_profit_GBP2020_year"]/1e6,5),flush=True)
        return result
    for policy in ["A","B"]:
        for label,ab,ah in [("0",False,False),("battery",True,False),("hydrogen",False,True),("both",True,True)]:
            run(f"{policy}_{label}_design2023",policy=policy,allow_b=ab,allow_h=ah)
        chosen=next(r for r in results if r["case"]==f"{policy}_both_design2023")
        cap=(chosen["battery_units"],chosen["electrolyser_units"])
        for year in [2024,2025]:
            run(f"{policy}_fixed_{year}",frame=f.loc[str(year)],policy=policy,fixed=cap)
            run(f"{policy}_fixed_chronological_{year}",frame=f.loc[str(year)],policy=policy,fixed=cap,chronology=True)
            r,s=simple_rule(f"{policy}_simple_{year}",f.loc[str(year)],base,policy,cap)
            results.append(r); s.to_csv(HERE/"outputs"/(r["case"]+".csv"),index_label="date")
        run(f"{policy}_chronological_design2023",policy=policy,chronology=True)
        run(f"{policy}_oracle2025",frame=f.loc["2025"],policy=policy)
        for year in [2020,2021,2022,2026]:
            run(f"{policy}_fixed_stress_{year}",frame=f.loc[str(year)],policy=policy,fixed=cap)
        for year in [2023,2025]:
            forced=run(f"{policy}_fixed20MW_{year}",frame=f.loc[str(year)],policy=policy,fixed=(0,1))
            r,s=simple_rule(f"{policy}_simple20MW_{year}",f.loc[str(year)],base,policy,(0,1))
            results.append(r); s.to_csv(HERE/"outputs"/(r["case"]+".csv"),index_label="date")
    if not args.quick:
        for policy in ["A","B"]:
            for price in [0.,2.,3.,6.]: run(f"{policy}_H2price_{price:g}",cfg=dict(base,hydrogen_price=price),policy=policy)
            for limit in [0.,2000.,50000.]: run(f"{policy}_H2limit_{limit:g}",cfg=dict(base,hydrogen_limit_kg=limit),policy=policy)
            for rate in [0.,.03,.08,.12]: run(f"{policy}_rate_{rate:g}",cfg=dict(base,rate=rate),policy=policy)
            lowFOM=settings()["battery_FOM_MW"]/2
            run(f"{policy}_battery_lowFOM",cfg=dict(base,battery_FOM_MW=lowFOM),policy=policy)
            for label,cost in [("legacy",816015.4400715563),("modern_low",1269947.5841191008),("modern_high",1650931.859354831)]:
                run(f"{policy}_H2cost_{label}",cfg=dict(base,hydrogen_cost_MW=cost),policy=policy)
            nofarm=f.loc["2023"].copy(); nofarm["G"]-=24*nofarm.wind_farm_MW/1000
            run(f"{policy}_no_independent_wind",frame=nofarm,policy=policy)
            clean=f.loc["2023"].query("strict_no_imputation == 1")
            run(f"{policy}_strict_quality_refit",frame=clean,policy=policy)
        # Full-sample hindsight reference, evaluated also on the test year.
        # This reference exceeds the local Community model-size allowance.
        for policy in ["A","B"]:
            oracle=run(f"{policy}_all_years_oracle",frame=f,policy=policy,backend="scipy")
            run(f"{policy}_all_years_capacity_on2025",frame=f.loc["2025"],policy=policy,fixed=(oracle["battery_units"],oracle["electrolyser_units"]))
        # Isolate the newly corrected price effect on a matched 2023 calendar.
        old=pd.read_csv(REPO/"daily_market_index_price.csv",parse_dates=["date"]).set_index("date")
        matched=f.loc["2023"].index.intersection(old.index)
        oldf=f.loc[matched].copy(); oldf["price"]=old.loc[matched].iloc[:,0]*108.7/oldf.CPI
        for policy in ["A","B"]:
            run(f"{policy}_old_price_matched",frame=oldf,policy=policy)
            run(f"{policy}_new_price_matched",frame=f.loc[matched],policy=policy)
    # Compare every addition against the same policy and sample with no equipment.
    for result in results:
        rframe=pd.read_csv(HERE/"outputs"/(result["case"]+".csv"),parse_dates=["date"]).set_index("date")
        direct=np.minimum(rframe.G,rframe.D)
        if result["policy"]=="A": direct=direct.where(rframe.price>0,0.)
        base_profit=float(np.dot(direct,rframe.price)*1000/annual_fraction(rframe))
        result["no_investment_profit_GBP2020_year"]=base_profit
        result["increment_GBP2020_year"]=result["net_profit_GBP2020_year"]-base_profit
        operating_increment=result["increment_GBP2020_year"]+result["annual_equivalent_cost_GBP2020"]
        used=result["configuration"]
        recurringFOM=result["battery_units"]*used["battery_FOM_MW"]*used["battery_unit_MW"]+result["electrolyser_units"]*used["hydrogen_FOM_MW"]*used["hydrogen_unit_MW"]
        cash=operating_increment-recurringFOM
        result["simple_payback_years_before_stack_replacement"]=(result["CAPEX_GBP2020"]+result["commissioning_GBP2020"])/cash if cash>0 and result["CAPEX_GBP2020"] else None
    save_json(HERE/"results.json",results)
    summary=pd.DataFrame([{k:v for k,v in r.items() if k not in ["configuration","solver","years"]} for r in results])
    summary.to_csv(HERE/"results.csv",index=False)
    files=[RESEARCH/"BASELINE_CANDIDATE.json",cpi_path]+list((RELEASE/"data").glob("*.csv"))
    save_json(HERE/"RUN_MANIFEST.json",dict(version="Baseline 1104",date="2026-11-04",source_release_commit="0a821eaf61a2b552682e185c137d98c5a9bffc93",
        design_year=2023,validation_year=2024,test_year=2025,perfect_information=True,
        portfolio_fixed_out_of_design=True,unseen_blind_test_claim=False,
        hydrogen_value_status="policy-supported value scenario treated as a site netback assumption, not a secured subsidy or contract",
        primary_time_model="annual pooled-energy relaxation; chronological feasibility checked separately",
        self_discharge_primary=0.,source_files={str(p.relative_to(PROJECT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        cases=len(results),publication="local proposal for review",solver_core="Xpress9.9",full_sample_reference="SciPy/HiGHS"))
    print("Completed",len(results),"cases",flush=True)


if __name__=="__main__": main()
