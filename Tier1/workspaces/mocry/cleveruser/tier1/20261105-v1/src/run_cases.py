"""Run the Tier 1 case set and write results, plans and verification output."""
import csv, io, json, math, pathlib, sys, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import model

PKG = pathlib.Path(__file__).resolve().parents[1]
OUT = PKG / "results"
PLANS = OUT / "plans"
OUT.mkdir(exist_ok=True)
PLANS.mkdir(exist_ok=True)

ANNUITY30 = (1 - 1.05 ** -30) / 0.05


def cost_split(res):
    c = res["annual_cost"]
    return {
        "capex_m": (c["capex_battery"] + c["capex_h2"]) / 1e6,
        "capital_annual_m": (c["battery_capital"] + c["h2_capital"]) / 1e6,
        "fom_annual_m": (c["battery_fom"] + c["h2_fom"]) / 1e6,
        "stack_annual_m": c["h2_stack_annual"] / 1e6,
        "commission_m": c["battery_commission"] / 1e6,
    }


def make_case(name, frame, policy, cfg=None, fixed=None, supply_min=None, base=None, store=True):
    res = model.solve(frame, policy, cfg, fixed=fixed, supply_min=supply_min)
    if base is None:
        base = model.base_profit(frame, policy, cfg)
    inc = res["net_profit_GBP2020_year"] - base
    cs = cost_split(res)
    capex = cs["capex_m"]
    pre_stack = inc + cs["capital_annual_m"] + cs["stack_annual_m"]
    after_stack = inc + cs["capital_annual_m"]
    out = {
        "case": name, "policy": policy, "days": res["days"], "sample_years": round(res["sample_years"], 4),
        "status": res["status"],
        "n_battery_units": res["n_battery_units"], "battery_MW": round(res["battery_MW"], 1),
        "battery_MWh": round(res["battery_MWh"], 1),
        "n_h2_modules": res["n_h2_modules"], "electrolyser_MW": round(res["electrolyser_MW"], 1),
        "base_profit_mGBP": round(base, 4),
        "net_profit_mGBP": round(res["net_profit_GBP2020_year"], 4),
        "increment_mGBP": round(inc, 4),
        "electricity_revenue_mGBP": round(res["electricity_revenue"], 4),
        "hydrogen_revenue_mGBP": round(res["hydrogen_revenue"], 4),
        "annual_cost_mGBP": round(res["annual_cost"]["total"] / 1e6, 4),
        "capex_mGBP": round(capex, 4),
        "capital_annual_mGBP": round(cs["capital_annual_m"], 4),
        "fom_annual_mGBP": round(cs["fom_annual_m"], 4),
        "stack_annual_mGBP": round(cs["stack_annual_m"], 4),
        "roi": round(inc / capex, 4) if capex else None,
        "payback_pre_stack_years": round(capex / pre_stack, 3) if pre_stack > 1e-9 else None,
        "payback_after_stack_years": round(capex / after_stack, 3) if after_stack > 1e-9 else None,
        "npv30_mGBP": round(after_stack * ANNUITY30 - capex, 3) if capex else None,
        "electricity_sold_GWh": round(res["electricity_sold_GWh"], 4),
        "direct_sale_GWh": round(res["direct_sale_GWh"], 4),
        "battery_charge_GWh": round(res["charge_GWh"], 4),
        "battery_discharge_GWh": round(res["battery_discharge_GWh"], 4),
        "h2_input_GWh": round(res["h2_input_GWh"], 4),
        "hydrogen_kg": round(res["hydrogen_kg"], 1),
        "unused_GWh": round(res["unused_GWh"], 4),
        "demand_coverage": round(res["demand_coverage"], 7),
        "max_balance_violation_GWh": res["max_violation"],
        "cfg": res["cfg"],
    }
    if store:
        fn = PLANS / (name + ".csv")
        with io.open(fn, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "G", "D", "price", "q", "c", "d", "h", "u", "z", "renewable", "other"])
            for p in res["plan"]:
                w.writerow([p["date"], p["G"], p["D"], p["price"], p["q"], p["c"], p["d"], p["h"],
                            p["u"], p["z"], p["renewable"], p["other"]])
    out["_plan"] = res["plan"] if store else None
    return out


def main():
    f23 = model.load_frame(2023)
    baseA = model.base_profit(f23, "A")
    baseB = model.base_profit(f23, "B")
    cases = {}

    # 1. reference configuration set, 2023 design year
    cases["A_0"] = make_case("A_0", f23, "A", fixed=(0, 0), base=baseA)
    cases["B_0"] = make_case("B_0", f23, "B", fixed=(0, 0), base=baseB)
    cases["A_battery"] = make_case("A_battery", f23, "A", cfg=dict(model.DEFAULTS, max_h2_modules=0), base=baseA)
    cases["B_battery"] = make_case("B_battery", f23, "B", cfg=dict(model.DEFAULTS, max_h2_modules=0), base=baseB)
    cases["A_h2"] = make_case("A_h2", f23, "A", cfg=dict(model.DEFAULTS, max_battery_units=0), base=baseA)
    cases["B_h2"] = make_case("B_h2", f23, "B", cfg=dict(model.DEFAULTS, max_battery_units=0), base=baseB)
    cases["A_both"] = make_case("A_both", f23, "A", base=baseA)
    cases["B_both"] = make_case("B_both", f23, "B", base=baseB)

    # 2. rule-based comparator at the same 20 MW size
    sA = model.simple_rule(f23, model.DEFAULTS, n_h=1)
    sB = model.simple_rule(f23, model.DEFAULTS, n_h=1)
    for nm, s, b in (("A_simple20", sA, baseA), ("B_simple20", sB, baseB)):
        cost = model.annual_costs(model.DEFAULTS, 0, 1)
        cases[nm] = {
            "case": nm, "policy": "simple", "days": 365, "sample_years": 1.0, "status": "rule",
            "n_battery_units": 0, "battery_MW": 0.0, "battery_MWh": 0.0, "n_h2_modules": 1, "electrolyser_MW": 20.0,
            "base_profit_mGBP": round(b, 4), "net_profit_mGBP": round(s["net_profit_GBP2020_year"], 4),
            "increment_mGBP": round(s["net_profit_GBP2020_year"] - b, 4),
            "electricity_revenue_mGBP": round(s["electricity_revenue_mGBP"], 4),
            "hydrogen_revenue_mGBP": round(s["hydrogen_revenue_mGBP"], 4),
            "annual_cost_mGBP": round(cost["total"] / 1e6, 4), "capex_mGBP": round(cost["capex_h2"] / 1e6, 4),
            "capital_annual_mGBP": round(cost["h2_capital"] / 1e6, 4), "fom_annual_mGBP": round(cost["h2_fom"] / 1e6, 4),
            "stack_annual_mGBP": round(cost["h2_stack_annual"] / 1e6, 4),
            "roi": None, "payback_pre_stack_years": None, "payback_after_stack_years": None, "npv30_mGBP": None,
            "electricity_sold_GWh": round(s["electricity_sold_GWh"], 4), "direct_sale_GWh": round(s["electricity_sold_GWh"], 4),
            "battery_charge_GWh": 0.0, "battery_discharge_GWh": 0.0, "h2_input_GWh": round(s["hydrogen_input_GWh"], 4),
            "hydrogen_kg": round(s["hydrogen_kg"], 1), "unused_GWh": round(s["unused_GWh"], 4),
            "demand_coverage": round(s["demand_coverage"], 7), "max_balance_violation_GWh": 0.0,
            "cfg": {"rule": "sell min(G,D), then H2, then charge", "h2_limit_kg_day": 10000.0}, "plan": None,
        }
        # recompute payback for the rule case
        inc = cases[nm]["increment_mGBP"]
        pre = inc + cases[nm]["capital_annual_mGBP"] + cases[nm]["stack_annual_mGBP"]
        after = inc + cases[nm]["capital_annual_mGBP"]
        cases[nm]["payback_pre_stack_years"] = round(cases[nm]["capex_mGBP"] / pre, 3) if pre > 0 else None
        cases[nm]["payback_after_stack_years"] = round(cases[nm]["capex_mGBP"] / after, 3) if after > 0 else None
        cases[nm]["roi"] = round(inc / cases[nm]["capex_mGBP"], 4) if cases[nm]["capex_mGBP"] else None

    # 3. fixed 20 MW across years (A and B)
    robustness = []
    for yr in range(2020, 2027):
        fy = model.load_frame(yr)
        bA = model.base_profit(fy, "A")
        bB = model.base_profit(fy, "B")
        for pol, b, nm in (("A", bA, f"A_fixed20_{yr}"), ("B", bB, f"B_fixed20_{yr}")):
            r = make_case(nm, fy, pol, fixed=(0, 1), base=b, store=False)
            robustness.append(r)
    # 4. sensitivities on the 2023 design year
    sens = []
    for label, over in [
        ("H2cost_legacy_816", {"h2_cost_GBP2020_MW": 816015.4400715563}),
        ("H2cost_modern_low_1270", {"h2_cost_GBP2020_MW": 1269947.5841191008}),
        ("H2cost_modern_mid_1460", {"h2_cost_GBP2020_MW": 1460439.721736966}),
        ("H2cost_modern_high_1651", {"h2_cost_GBP2020_MW": 1650931.859354831}),
        ("rate_0", {"rate": 0.0}), ("rate_0.03", {"rate": 0.03}), ("rate_0.05", {"rate": 0.05}),
        ("rate_0.08", {"rate": 0.08}), ("rate_0.12", {"rate": 0.12}),
        ("battery_FOM_low", {"battery_FOM_GBP2020_MWyr": 7430.80852295709}),
        ("h2_price_6", {"h2_price_GBP2020_kg": 6.0}),
        ("h2_price_9.5", {"h2_price_GBP2020_kg": 9.5}),
        ("offtake_2000", {"h2_limit_kg_day": 2000.0}),
        ("offtake_50000", {"h2_limit_kg_day": 50000.0}),
    ]:
        sens.append(make_case("sens_" + label, f23, "A", cfg=dict(model.DEFAULTS, **over), base=baseA, store=False))
    # data / boundary sensitivities
    f23_strict = model.load_frame(2023, strict_only=True)
    f23_old = model.load_frame(2023, old_price=True)
    f23_nowind = model.load_frame(2023, no_wind=True)
    sens.append(make_case("data_strict_2023", f23_strict, "A", fixed=(0, 1),
                          base=model.base_profit(f23_strict, "A"), store=False))
    sens.append(make_case("data_old_price_2023", f23_old, "A", fixed=(0, 1),
                          base=model.base_profit(f23_old, "A"), store=False))
    sens.append(make_case("boundary_no_farm_2023", f23_nowind, "A", fixed=(0, 1),
                          base=model.base_profit(f23_nowind, "A"), store=False))
    sens.append(make_case("A_old_price_opt_2023", f23_old, "A", base=model.base_profit(f23_old, "A"), store=False))

    # 5. battery maximum affordable cost (2023, A and B)
    sweep = []
    for cost in [0, 25000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 125000, 150000, 200000, 256234.7766536928, 300000, 400000]:
        cfg = dict(model.DEFAULTS, battery_cost_GBP2020_MWh=float(cost), max_h2_modules=0)
        for pol, b in (("A", baseA), ("B", baseB)):
            r = make_case(f"batsweep_{pol}_{int(cost)}", f23, pol, cfg=cfg, base=b, store=False)
            sweep.append({"cost_GBP2020_MWh": cost, "policy": pol, "fom": "primary", "n_units": r["n_battery_units"],
                          "increment_mGBP": r["increment_mGBP"], "payback_after_stack": r["payback_after_stack_years"]})
    for cost in [0, 2000, 4000, 6000, 8000, 10000, 15000, 20000, 30000]:
        cfg = dict(model.DEFAULTS, battery_cost_GBP2020_MWh=float(cost),
                   battery_FOM_GBP2020_MWyr=7430.80852295709, max_h2_modules=0)
        r = make_case(f"batsweep_lowFOM_{int(cost)}", f23, "A", cfg=cfg, base=baseA, store=False)
        sweep.append({"cost_GBP2020_MWh": cost, "policy": "A", "fom": "table", "n_units": r["n_battery_units"],
                      "increment_mGBP": r["increment_mGBP"], "payback_after_stack": r["payback_after_stack_years"]})

    # 5b. battery maximum affordable cost: primary and lower FOM, battery-only model
    def battery_breakeven(fom_primary):
        fom = 14861.617045914183 if fom_primary else 7430.80852295709
        lo, hi = 0.0, 256234.7766536928
        def has(cost):
            r = model.solve(f23, "A", dict(model.DEFAULTS, battery_cost_GBP2020_MWh=cost,
                                           battery_FOM_GBP2020_MWyr=fom, max_h2_modules=0))
            return r["n_battery_units"] > 0
        if not has(0.0):
            return None
        if has(hi):
            return hi
        for _ in range(24):
            mid = (lo + hi) / 2
            if has(mid):
                lo = mid
            else:
                hi = mid
        return lo

    battery_threshold = {
        "primary_FOM_GBP2020_MWh": battery_breakeven(True),
        "table_FOM_GBP2020_MWh": battery_breakeven(False),
        "primary_FOM_value_per_MW_year": 14861.617045914183,
        "table_FOM_value_per_MW_year": 7430.80852295709,
        "note": "highest battery CAPEX at which at least one 1.5 MW / 3 MWh unit is chosen, battery-only model, 2023.",
    }

    # 5c. hydrogen thresholds by bisection
    def h2_threshold_v():
        lo, hi = 3.0, 7.0
        for _ in range(24):
            mid = (lo + hi) / 2
            r = model.solve(f23, "A", dict(model.DEFAULTS, h2_price_GBP2020_kg=mid, max_battery_units=0))
            if r["n_h2_modules"] >= 1:
                hi = mid
            else:
                lo = mid
        return hi

    def h2_threshold_L(v):
        lo, hi = 0.0, 10000.0
        for _ in range(24):
            mid = (lo + hi) / 2
            r = model.solve(f23, "A", dict(model.DEFAULTS, h2_price_GBP2020_kg=v, h2_limit_kg_day=mid,
                                           max_battery_units=0))
            if r["n_h2_modules"] >= 1:
                hi = mid
            else:
                lo = mid
        return hi

    h2_threshold = {
        "netback_GBP2020_kg_at_10000_kg_day": h2_threshold_v(),
        "offtake_kg_day_at_7.799": h2_threshold_L(7.7990270551508845),
        "offtake_kg_day_at_9.5": h2_threshold_L(9.5),
        "note": "smallest value/offtake at which one 20 MW module is installed (2023, A).",
    }

    # 6. hydrogen trigger map: netback x offtake
    grid = []
    for v in [0, 1, 2, 3, 4, 4.61, 5, 6, 7.799, 9.5, 12]:
        for L in [0, 1000, 2000, 5000, 10000, 15000, 20000, 30000, 50000]:
            cfg = dict(model.DEFAULTS, h2_price_GBP2020_kg=float(v), h2_limit_kg_day=float(L))
            r = make_case(f"grid_{v:g}_{L:g}", f23, "A", cfg=cfg, base=baseA, store=False)
            grid.append({"netback_GBP2020_kg": v, "offtake_kg_day": L, "n_modules": r["n_h2_modules"],
                         "MW": r["electrolyser_MW"], "increment_mGBP": r["increment_mGBP"],
                         "h2_input_GWh": r["h2_input_GWh"]})

    # 7. supply obligation frontier (annual electricity sales floor)
    a0_sales = cases["A_0"]["electricity_sold_GWh"]
    frontier = []
    for frac in [1.0 - 1e-6, 0.9999, 0.9995, 0.999, 0.995, 0.99, 0.98]:
        x = a0_sales * frac
        r = make_case(f"supply_{frac}", f23, "A", supply_min=x, base=baseA, store=False)
        frontier.append({"floor_GWh": round(x, 3), "fraction_of_A0_sales": frac,
                         "n_modules": r["n_h2_modules"], "MW": r["electrolyser_MW"],
                         "increment_mGBP": r["increment_mGBP"], "h2_input_GWh": r["h2_input_GWh"],
                         "sales_GWh": r["electricity_sold_GWh"]})

    # 8. energy attribution for the 20 MW case
    plan0 = cases["A_0"]["_plan"]
    plan1 = cases["A_h2"]["_plan"]
    attr = {"cases": {}}
    for nm, plan in (("A_h2", plan1), ("A_both", cases["A_both"]["_plan"])):
        cap = div = f_tot = losses = 0.0
        ren_lo = ren_hi = 0.0
        neg_days = 0
        for p0, p1 in zip(plan0, plan):
            f = p1["c"] + p1["h"]
            f_tot += f
            cap += p0["u"] - p1["u"]
            div += p0["q"] - p1["q"]
            losses += p1["c"] - p1["d"]
            s = max(0.0, p1["G"] - p1["D"])
            c_t = min(f, s)
            ren_lo += max(0.0, c_t - p1["other"])
            ren_hi += min(c_t, p1["renewable"])
            if p1["price"] <= 0:
                neg_days += 1
        attr["cases"][nm] = {
            "input_to_assets_GWh": round(f_tot, 4),
            "captured_unused_GWh": round(cap, 4),
            "diverted_from_sale_GWh": round(div, 4),
            "identity_gap_GWh": round(f_tot - cap - div, 6),
            "battery_losses_GWh": round(losses, 4),
            "captured_share_of_input": round(cap / f_tot, 4) if f_tot else None,
            "renewable_attribution_low_GWh": round(ren_lo, 4),
            "renewable_attribution_high_GWh": round(ren_hi, 4),
            "negative_price_days": neg_days,
        }
    attr["unused_definition"] = {
        "physical_surplus_2023_GWh": round(sum(max(0.0, r["G"] - r["D"]) for r in f23), 4),
        "model_unused_A0_2023_GWh": cases["A_0"]["unused_GWh"],
        "note": "u_t is the model residual; it coincides with physical surplus only when no day has a non-positive price.",
    }

    for r in cases.values():
        r.pop("_plan", None)
    for r in robustness + sens:
        r.pop("_plan", None)

    results = {
        "meta": {
            "package": "Tier1 workspace CU build 20261105-v1",
            "built_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "design_year": 2023,
            "currency": "GBP2020",
            "model": "daily energy-pool MILP, A economic allocation / B current-generation priority",
            "solver": "FICO Xpress 9.9.1 (Python), Community size limit rows+columns<=5000",
            "parameters": "public v1.1 reviewed candidate (BASELINE_CANDIDATE.json) + brief technical references",
            "data": "public full repair 20261104-v2",
            "cross_check": "reference cases reproduce Baseline 1104: A0 17,139.332; A_h2 17,147.905; B fixed20 -1.065; simple20 -1.065",
        },
        "cases": list(cases.values()),
        "robustness": robustness,
        "sensitivity": sens,
        "battery_sweep": sweep,
        "battery_threshold": battery_threshold,
        "h2_threshold": h2_threshold,
        "trigger_grid": grid,
        "supply_frontier": frontier,
        "attribution": attr,
    }
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    # flat case table
    keys = ["case", "policy", "n_battery_units", "n_h2_modules", "increment_mGBP", "net_profit_mGBP",
            "capex_mGBP", "payback_pre_stack_years", "payback_after_stack_years", "roi", "npv30_mGBP",
            "h2_input_GWh", "unused_GWh", "demand_coverage"]
    with io.open(OUT / "cases.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in list(cases.values()) + robustness + sens:
            w.writerow(r)
    print("cases", len(cases), "robust", len(robustness), "sens", len(sens), "grid", len(grid),
          "sweep", len(sweep), "frontier", len(frontier))
    print(json.dumps(attr, ensure_ascii=False, indent=1)[:1500])
    print("A0/A_h2/B20/simple:",
          cases["A_0"]["increment_mGBP"], cases["A_h2"]["increment_mGBP"],
          cases["B_0"]["increment_mGBP"], cases["A_simple20"]["increment_mGBP"])


if __name__ == "__main__":
    main()
