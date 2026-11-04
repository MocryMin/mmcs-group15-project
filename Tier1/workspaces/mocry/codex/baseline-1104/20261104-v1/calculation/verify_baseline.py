"""Reconcile exported schedules, cash flows and optimality references."""
from pathlib import Path
import calendar
import hashlib
import json
import math

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent


def annuity(r,n):
    return 1/n if r==0 else r*(1+r)**n/((1+r)**n-1)


def one_hydrogen_portfolio(f,cfg,policy,count):
    """Independent enumeration of active modules and daily linear breakpoints."""
    kg_per_GWh=1e6/cfg["hydrogen_kWh_kg"]
    max_h=cfg["hydrogen_limit_kg"]/kg_per_GWh
    unit=cfg["hydrogen_unit_MW"]*24/1000
    gains=[]
    baseline=[]
    for row in f.itertuples():
        best=-math.inf
        for online in range(count+1):
            lo=cfg["hydrogen_min"]*unit*online
            hi=min(unit*online,max_h,row.G)
            mandatory=min(row.G,row.D) if policy=="B" else 0.
            hi=min(hi,row.G-mandatory)
            if hi<lo-1e-9: continue
            candidates=[lo,hi]
            kink=row.G-row.D
            if lo<=kink<=hi: candidates.append(kink)
            for h in candidates:
                q=mandatory if policy=="B" else (min(row.G-h,row.D) if row.price>0 else 0.)
                value=1000*row.price*q+kg_per_GWh*cfg["hydrogen_price"]*h
                best=max(best,value)
        baseq=min(row.G,row.D) if policy=="B" or row.price>0 else 0.
        baseline.append(1000*row.price*baseq); gains.append(best)
    year=sum(1/(366 if calendar.isleap(t.year) else 365) for t in f.index)
    capital=cfg["hydrogen_cost_MW"]*cfg["hydrogen_unit_MW"]
    pv=cfg["hydrogen_replacement_MW"]*cfg["hydrogen_unit_MW"]*sum((1+cfg["rate"])**-t for t in cfg["hydrogen_replacement_years"])
    annual=(capital+pv)*annuity(cfg["rate"],cfg["hydrogen_life"])+cfg["hydrogen_FOM_MW"]*cfg["hydrogen_unit_MW"]
    return (sum(gains)-sum(baseline))/year-count*annual


def main():
    results=json.loads((HERE/"results.json").read_text(encoding="utf-8"))
    manifest=json.loads((HERE/"RUN_MANIFEST.json").read_text(encoding="utf-8"))
    for name,digest in manifest["source_files"].items():
        assert hashlib.sha256((Path(__file__).resolve().parent.parent/name).read_bytes()).hexdigest()==digest,name
    errors=[]
    for r in results:
        f=pd.read_csv(HERE/"outputs"/(r["case"]+".csv"),parse_dates=["date"]).set_index("date")
        cfg=r["configuration"]; nb=r["battery_units"]; nh=r["electrolyser_units"]
        e=cfg["eta"]; U=nb*cfg["battery_unit_MWh"]*cfg["soc_window"]/1000
        checks=[0.,float(-f[["q","c","d","h","unused","deficit"]].to_numpy().min()),
                float(np.max(np.abs(f.G-f.q-f.c-f.h-f.unused))),
                float(np.max(np.abs(f.D-f.q-f.d-f.deficit))),
                float(np.max(f.c-U/e)),float(np.max(f.d-U*e)),float(np.max(np.minimum(f.c,f.d))),
                float(np.max(f.h-cfg["hydrogen_limit_kg"]*cfg["hydrogen_kWh_kg"]/1e6)),
                float(np.max(f.h-24*cfg["hydrogen_unit_MW"]*f.online/1000)),
                float(np.max(cfg["hydrogen_min"]*24*cfg["hydrogen_unit_MW"]*f.online/1000-f.h)),
                float(np.max(f.online-nh)),float(np.max(np.abs(f.online-np.rint(f.online))))]
        if r["policy"]=="B": checks.append(float(np.max(np.abs(f.q-np.minimum(f.G,f.D)))))
        for year in sorted(set(f.index.year)):
            y=f.loc[str(year)]
            if r["time_model"]=="tier1_annual_energy_pool": checks.append(abs(float(y.d.sum()-e*e*y.c.sum())))
            else:
                prev=np.r_[0,y.s.to_numpy()[:-1]]
                checks.extend([float(np.max(np.abs(y.s-(1-cfg["self_discharge"])*prev-e*y.c+y.d/e))),
                               float(np.max(y.s-U)),float(-y.s.min()),abs(float(y.s.iloc[-1]))])
        fraction=sum(1/(366 if calendar.isleap(t.year) else 365) for t in f.index)
        bc=cfg["battery_cost_MWh"]*cfg["battery_unit_MWh"]
        commissioning=.2*cfg["battery_unit_MWh"]/e*cfg["commission_price_GBP_MWh"]
        hc=cfg["hydrogen_cost_MW"]*cfg["hydrogen_unit_MW"]
        replacement=cfg["hydrogen_replacement_MW"]*cfg["hydrogen_unit_MW"]*sum((1+cfg["rate"])**-t for t in cfg["hydrogen_replacement_years"])
        annualcost=nb*((bc+commissioning)*annuity(cfg["rate"],cfg["battery_life"])+cfg["battery_FOM_MW"]*cfg["battery_unit_MW"])
        annualcost+=nh*((hc+replacement)*annuity(cfg["rate"],cfg["hydrogen_life"])+cfg["hydrogen_FOM_MW"]*cfg["hydrogen_unit_MW"])
        cash=(float(np.dot(f.price,f.q+f.d))*1000+float(f.h.sum()*1e6/cfg["hydrogen_kWh_kg"]*cfg["hydrogen_price"]))/fraction-annualcost
        checks.append(abs(cash-r["net_profit_GBP2020_year"])/1e6)
        checks.append(abs(annualcost-r["annual_equivalent_cost_GBP2020"])/1e6)
        assert max(checks)<1e-4,(r["case"],max(checks))
        errors.append(max(checks))
        # With no battery the whole MIP has a separate finite-enumeration solution.
        if nb==0:
            gain=one_hydrogen_portfolio(f,cfg,r["policy"],nh)
            if r["solver"]["optimal"]:
                assert abs(gain-r["increment_GBP2020_year"])/1e6<1e-4,(r["case"],gain)
            else:
                assert gain>=r["increment_GBP2020_year"]-100.,(r["case"],gain)
    by={r["case"]:r for r in results}
    for y in [2023]:
        assert by[f"A_both_design{y}"]["net_profit_GBP2020_year"]>=by[f"B_both_design{y}"]["net_profit_GBP2020_year"]-1
    for policy in ["A","B"]:
        for year in [2024,2025]:
            assert by[f"{policy}_fixed_{year}"]["net_profit_GBP2020_year"]>=by[f"{policy}_fixed_chronological_{year}"]["net_profit_GBP2020_year"]-1
            assert by[f"{policy}_fixed_chronological_{year}"]["net_profit_GBP2020_year"]>=by[f"{policy}_simple_{year}"]["net_profit_GBP2020_year"]-1
        assert by[f"{policy}_oracle2025"]["net_profit_GBP2020_year"]>=by[f"{policy}_fixed_2025"]["net_profit_GBP2020_year"]-1

    # A nonzero-battery fixture verifies stock constraints and the optimistic pool.
    import run_baseline as rb
    rb.init_xpress()
    cfg=rb.settings(hydrogen_limit_kg=0.,battery_cost_MWh=100.,battery_FOM_MW=1.,commission_price_GBP_MWh=0.)
    toy=pd.DataFrame(dict(G=[0.,1.],D=[1.,0.],price=[1000.,0.],strict_no_imputation=[1,1]),index=pd.date_range("2023-01-01",periods=2))
    pooled,_=rb.solve_case("future_borrowing_fixture",toy,cfg,allow_h=False)
    chronological,_=rb.solve_case("no_free_energy_fixture",toy,cfg,allow_h=False,chronology=True)
    highs,_=rb.solve_case("second_solver_fixture",toy,cfg,allow_h=False,backend="scipy")
    assert pooled["battery_units"]>0 and chronological["battery_units"]==0
    assert abs(pooled["net_profit_GBP2020_year"]-highs["net_profit_GBP2020_year"])<1.
    forward=toy.copy(); forward["G"]=[1.,0.]; forward["D"]=[0.,1.]; forward["price"]=[0.,1000.]
    physical,_=rb.solve_case("physical_transfer_fixture",forward,cfg,allow_h=False,chronology=True)
    assert physical["battery_units"]>0 and physical["discharge_GWh_year"]>0

    inputs=pd.read_csv(HERE/"model_inputs.csv",parse_dates=["date"]).set_index("date").loc["2023"]
    maincfg=by["A_both_design2023"]["configuration"]
    break_even={}
    for policy in ["A","B"]:
        break_even[policy]={}
        for count in [1,2]:
            lo,hi=0.,50.
            for _ in range(45):
                mid=(lo+hi)/2
                if one_hydrogen_portfolio(inputs,dict(maincfg,hydrogen_price=mid),policy,count)>0: hi=mid
                else: lo=mid
            break_even[policy][str(count*20)+"MW"]=(lo+hi)/2
    report=dict(cases_checked=len(results),all_assertions_passed=True,max_scaled_error=max(errors),
                independent_no_battery_enumerations=sum(r["battery_units"]==0 for r in results),
                fixture_pooled_battery_units=pooled["battery_units"],fixture_chronological_units=chronological["battery_units"],
                fixture_feasible_forward_units=physical["battery_units"],second_solver_agrees=True,
                break_even_H2_netback_GBP2020_kg_design2023=break_even)
    rb.save_json(HERE/"VERIFICATION.json",report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__": main()
