"""
Tier 2B study: the Tier 1 portfolio operated day by day, 2020-2025.

    python t2b_run.py --check                 consistency checks (about 20 seconds)
    python t2b_run.py                         every stage, then figures (about 45 minutes)
    python t2b_run.py --stage sizing rolling  selected stages; results are cached as CSV in results/
    python t2b_run.py --stage figs            redraw the figures from the cached results
    python t2b_run.py --solver xpress ...     same models through FICO Xpress (branch not yet executed)

Stages: sizing, time, minrun, battery, windows, rolling, sensitivity, figs.
"""
from __future__ import annotations
import argparse, json, sys, time
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd

from t1_model import Params, Problem, evaluate_exact, dispatch
from t2b_model import Ops, RULES, module_energy, realise, summarise, solve_chrono, chrono_problem, brute_force, rolling_operation
from t2b_forecast import load_frame, make_forecasts, to_energy, expected_energy, skill_table, calibration_table

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
L0 = 5                                   # central minimum run in days
EVAL = ("2022-01-01", "2025-12-31")      # rolling operation is scored on these four years
SOLVER = "highs"


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def save(df: pd.DataFrame, name: str):
    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / name, index=False, float_format="%.6g")
    log("wrote", name, len(df), "rows")


def solve(prob, ops, N, **kw):
    kw.setdefault("time_limit", 120); kw.setdefault("gap", 2e-4)
    r = chrono_problem(prob, ops, n_modules=N, solver=SOLVER, **kw)
    if r["n"] is None: raise RuntimeError(f"{ops} N={N}: {r['status']}")
    return r


def net_gain(prob, ops, N):
    if N == 0: return 0.0, None
    r = solve(prob, ops, N)
    return float(r["cash"].sum()) / prob.years / 1e6 - prob.par.el_annual * N * prob.par.module_mw / 1e6, r


def best_size(prob, ops, step=8):
    """Largest net gain over whole modules: coarse scan, then steps of 2, then steps of 1."""
    seen = {0: 0.0}

    def f(N):
        N = int(min(max(N, 0), prob.n_max))
        if N not in seen: seen[N] = net_gain(prob, ops, N)[0]
        return seen[N]

    falls, N = 0, step
    while N <= prob.n_max and falls < 2:
        falls = falls + 1 if f(N) < max(v for k, v in seen.items() if k < N) else 0
        N += step
    for width, inc in ((step - 2, 2), (1, 1)):
        b = max(seen, key=seen.get)
        for N in range(b - width, b + width + 1, inc): f(N)
    b = max(seen, key=seen.get)
    return b, seen[b], seen


def idle_spell(n):
    best = cur = 0
    for v in n:
        cur = cur + 1 if v == 0 else 0
        best = max(best, cur)
    return best


def by_year(prob, cash, N, bat=0.0):
    yrs = prob.dates.year.to_numpy()
    cost = (prob.par.el_annual * N * prob.par.module_mw + prob.par.bat_annual * bat) / 1e6
    return {int(y): float(cash[yrs == y].sum()) / 1e6 - cost for y in np.unique(yrs)}


# ---------------------------------------------------------------------------------------------------------
def stage_sizing(df, par, prob):
    """Best plant size for each rule with free daily switching and with the central minimum run."""
    curves, optima = [], []
    grids = dict(strict=range(0, 7), topup=range(0, 29, 2), divert=range(0, 57, 4))
    for rule in RULES:
        for L in (1, L0):
            ops = Ops(min_run=L, rule=rule)
            for N in grids[rule]:
                g, _ = net_gain(prob, ops, N)
                curves.append(dict(rule=rule, min_run=L, modules=N, electrolyser_MW=N * par.module_mw, net_gain_m=g))
            if rule == "strict":
                cand = {N: net_gain(prob, ops, N)[0] for N in range(0, 7)}
                b = max(cand, key=cand.get)
            else:
                b, _, _ = best_size(prob, ops)
            if b == 0:
                optima.append(dict(label=f"{rule}, minimum run {L} d", rule=rule, min_run=L, modules=0, electrolyser_MW=0.0,
                                   net_gain_m=0.0, best_nonzero_net_gain_m=net_gain(prob, ops, 1)[0]))
            else:
                r = solve(prob, ops, b, gap=1e-4)
                optima.append(summarise(prob, r["n"], ops, b, label=f"{rule}, minimum run {L} d"))
            log("sizing", rule, L, "->", b, "modules", round(optima[-1]["net_gain_m"], 3))
    for pol, N in (("surplus", 2), ("divert", 30)):                       # Tier 1 references
        e = evaluate_exact(Problem(df, replace(par, policy=pol)), N)
        optima.append(dict(label=f"Tier 1 plan ({pol}), free switching, own output only", rule="tier1-" + pol, min_run=1,
                           modules=N, electrolyser_MW=N * par.module_mw, net_gain_m=float(e["net_gain_m"]),
                           h2_t_per_year=float(e["h2_t_per_year"])))
    save(pd.DataFrame(curves), "sizing_curve.csv"); save(pd.DataFrame(optima), "sizing_optimum.csv")


def optimum(rule, L=L0):
    o = pd.read_csv(OUT / "sizing_optimum.csv")
    return int(o[(o.rule == rule) & (o.min_run == L)].modules.iloc[0])


def designs(par):
    """(key, description, rule, minimum run, modules)"""
    Nt, Nd = optimum("topup"), optimum("divert")
    return [("A", "Tier 1 surplus plan as assumed: unsold energy only, free daily switching", "strict", 1, 2),
            ("B", "Same 40 MW, unsold energy only, 5-day minimum run", "strict", L0, 2),
            ("C", "Same 40 MW, minimum load may be topped up, 5-day minimum run", "topup", L0, 2),
            ("D", f"Top-up rule at its own best size ({Nt * 20} MW), 5-day minimum run", "topup", L0, Nt),
            ("F", "Tier 1 diversion plan size (600 MW), diversion allowed, 5-day minimum run", "divert", L0, 30),
            ("G", f"Diversion rule at its own best size ({Nd * 20} MW), 5-day minimum run", "divert", L0, Nd)]


def stage_time(df, par, prob):
    """The Tier 1 plans and their chronological counterparts replayed through 2020-2025."""
    rows, yearly, daily, monthly = [], [], [], []
    for key, desc, rule, L, N in designs(par):
        ops = Ops(min_run=L, rule=rule)
        r = solve(prob, ops, N, gap=1e-4)
        s = summarise(prob, r["n"], ops, N, label=desc, extra=dict(design=key))
        s["longest_idle_days"] = idle_spell(r["n"])
        yr = by_year(prob, r["cash"], N)
        s["worst_year_net_gain_m"], s["years_negative"] = min(yr.values()), int(sum(v < 0 for v in yr.values()))
        capex = par.el_capex * N * par.module_mw
        fom = par.el_fom * capex / 365.25
        cum = np.cumsum(r["cash"] - fom) - capex
        hit = np.flatnonzero(cum >= 0)
        s["payback_date"] = str(prob.dates[hit[0]].date()) if len(hit) else "not within 2020-2025"
        rows.append(s)
        yearly += [dict(design=key, year=y, net_gain_m=v) for y, v in yr.items()]
        d = pd.DataFrame(dict(design=key, date=prob.dates, unsold_MWh=prob.S, saleable_MWh=prob.Q0, price=prob.p,
                              modules_on=r["n"], load_MWh=r["load"], from_unsold_MWh=r["xs"], diverted_MWh=r["xd"],
                              imported_MWh=r["xg"], cash=r["cash"], cumulative_cash_m=cum / 1e6))
        daily.append(d)
        g = d.set_index("date").resample("MS").agg(dict(load_MWh="sum", from_unsold_MWh="sum", diverted_MWh="sum",
                                                         imported_MWh="sum", cash="sum", modules_on="mean"))
        g["design"] = key
        monthly.append(g.reset_index())
        log("time", key, round(s["net_gain_m"], 3), s["payback_date"])
    save(pd.DataFrame(rows), "through_time.csv"); save(pd.DataFrame(yearly), "through_time_by_year.csv")
    save(pd.concat(monthly), "through_time_monthly.csv")
    pd.concat(daily).to_csv(OUT / "daily_operation.csv.gz", index=False, float_format="%.5g")


def stage_minrun(df, par, prob):
    """How the length of the minimum run changes the result, plant size held fixed."""
    Nt, Nd = optimum("topup"), optimum("divert")
    rows = []
    for rule, N in (("strict", 2), ("topup", 2), ("topup", Nt), ("divert", Nd)):
        for L in (1, 2, 3, 5, 7, 10, 14, 28):
            ops = Ops(min_run=L, rule=rule)
            r = solve(prob, ops, N)
            rows.append(summarise(prob, r["n"], ops, N, label=f"{rule} {N * 20} MW"))
        if rule != "strict":
            ops = Ops(min_run=prob.T, rule=rule)
            rows.append(summarise(prob, np.full(prob.T, N), ops, N, label=f"{rule} {N * 20} MW", extra=dict(never_off=True)))
        log("minrun", rule, N)
    save(pd.DataFrame(rows), "min_run.csv")


def stage_battery(df, par, prob):
    """Does a battery whose state of charge carries from day to day earn its cost once days are linked?"""
    rows = []
    Nd = optimum("divert")
    for rule, N in (("strict", 2), ("topup", 2), ("divert", Nd)):
        ops = Ops(min_run=L0, rule=rule)
        base = solve(prob, ops, N, gap=1e-4)
        base_cash = float(base["cash"].sum()) / prob.years

        def row(case, r, B):
            gross = float(r["cash"].sum()) / prob.years - base_cash
            return dict(rule=rule, modules=N, case=case, battery_MWh=B, operating_cash_m=float(r["cash"].sum()) / prob.years / 1e6,
                        gross_value_per_MWh_year=gross / B if B > 1e-6 else np.nan, annual_cost_per_MWh=par.bat_annual,
                        break_even_capex_per_MWh=gross / B / (par.crf_bat + par.bat_fom) if B > 1e-6 else np.nan,
                        net_gain_change_m=(gross - par.bat_annual * B) / 1e6, solver_status=str(r["status"])[:40], mip_gap=r["mip_gap"])

        # size chosen by the model while the electrolyser keeps its no-battery commitment plan
        r = solve(prob, ops, N, b_max=5000.0, fix_n=base["n"], time_limit=240)
        rows.append(row("battery size chosen by the model, electrolyser plan unchanged", r, r["battery"]))
        if rule == "strict":                                       # here the battery could also enable longer runs
            r = solve(prob, ops, N, b_max=5000.0, time_limit=240)
            rows.append(row("battery size chosen by the model, electrolyser plan re-optimised", r, r["battery"]))
        for B in (100.0, 500.0, 2000.0):
            r = solve(prob, ops, N, bat_mwh=B, time_limit=300)
            rows.append(row(f"battery forced to {B:.0f} MWh, electrolyser plan re-optimised", r, B))
            log("battery", rule, B, round(rows[-1]["gross_value_per_MWh_year"]), rows[-1]["solver_status"])
    save(pd.DataFrame(rows), "battery.csv")


def stage_windows(df, par, prob):
    """Seasonal pattern and the hardest stretches of the record, for the two chronological plans."""
    d = pd.read_csv(OUT / "daily_operation.csv.gz", parse_dates=["date"])
    m, cap = module_energy(par)
    seas = []
    for key in ("D", "G"):
        x = d[d.design == key].set_index("date")
        g = x.groupby(x.index.month).agg(unsold_GWh_per_day=("unsold_MWh", lambda v: v.mean() / 1e3), price=("price", "mean"),
                                         h2_t_per_day=("load_MWh", lambda v: v.mean() / par.kwh_per_kg),
                                         cash_k_per_day=("cash", lambda v: v.mean() / 1e3),
                                         share_from_unsold=("from_unsold_MWh", "sum"), load=("load_MWh", "sum"),
                                         modules_on=("modules_on", "mean"))
        g["share_from_unsold"] = g["share_from_unsold"] / g["load"].clip(lower=1e-9)
        g = g.drop(columns="load").reset_index().rename(columns={"date": "month"})
        g.insert(0, "design", key); seas.append(g)
    save(pd.concat(seas), "seasonal.csv")

    def longest(mask):
        best, cur, end = 0, 0, 0
        for i, v in enumerate(mask):
            cur = cur + 1 if v else 0
            if cur > best: best, end = cur, i
        return end - best + 1, end

    dem, farm = df["demand_MW"].to_numpy(), df["farm_MW"].to_numpy()
    roll = lambda a, k=28: pd.Series(a).rolling(k).mean().to_numpy()
    wins = {"Longest stretch with too little unsold energy for one module": longest(prob.S < m),
            "Longest stretch with unsold energy every day": longest(prob.S > 0),
            "Longest stretch with price above the hydrogen break-even": longest(prob.p > par.margin),
            "Calmest 28 days (lowest farm output)": (int(np.nanargmin(roll(farm))) - 27, int(np.nanargmin(roll(farm)))),
            "Highest-demand 28 days": (int(np.nanargmax(roll(dem))) - 27, int(np.nanargmax(roll(dem)))),
            "Highest-price 28 days": (int(np.nanargmax(roll(prob.p))) - 27, int(np.nanargmax(roll(prob.p))))}
    rows = []
    for name, (a, b) in wins.items():
        for key in ("D", "G"):
            x = d[d.design == key].reset_index(drop=True)
            w, N = x.iloc[a:b + 1], x.modules_on.max()
            rows.append(dict(window=name, start=str(prob.dates[a].date()), end=str(prob.dates[b].date()), days=b - a + 1,
                             design=key, mean_price=float(w.price.mean()), unsold_GWh_per_day=float(w.unsold_MWh.mean()) / 1e3,
                             modules_on_share=float(w.modules_on.mean() / N), h2_t_per_day=float(w.load_MWh.mean()) / par.kwh_per_kg,
                             h2_t_per_day_whole_record=float(x.load_MWh.mean()) / par.kwh_per_kg,
                             cash_k_per_day=float(w.cash.mean()) / 1e3, cash_k_per_day_whole_record=float(x.cash.mean()) / 1e3,
                             imported_GWh=float(w.imported_MWh.sum()) / 1e3))
    save(pd.DataFrame(rows), "stress_windows.csv")


def stage_rolling(df, par, prob):
    """Commitment decided one day ahead on forecasts that are refreshed daily, scored on 2022-2025."""
    H = 7
    FC = {m: make_forecasts(df, H, m) for m in ("perfect", "persist", "ar", "neso")}
    save(skill_table(df, FC, *EVAL), "forecast_skill.csv"); save(calibration_table(df), "calibration.csv")
    i0, i1 = df.index.get_loc(pd.Timestamp(EVAL[0])), df.index.get_loc(pd.Timestamp(EVAL[1]))
    sub = lambda a: a[i0:i1 + 1]
    years = (i1 - i0 + 1) / 365.25
    yr = df.index.year.to_numpy()[i0:i1 + 1]
    rows, yearly = [], []
    for rule in ("topup", "divert"):
        N = optimum(rule)
        for h2 in (9.5, 7.5, 6.0):
            ph = replace(par, h2_value=h2); pr = Problem(df, ph)
            ops = Ops(min_run=L0, rule=rule)
            fce = {}
            for m, F in FC.items():
                S, Q0 = to_energy(F["farm_MW"], F["gap_MW"], F["price"])
                fce[m] = dict(S=S, Q0=Q0, p=F["price"])
            Se, Qe = expected_energy(df, FC["neso"])
            fce["neso_expected"] = dict(S=Se, Q0=Qe, p=FC["neso"]["price"])
            paths = {"Never switch off": rolling_operation(pr, ops, N, method="always", first=i0, last=i1),
                     "Price rule on yesterday's price": rolling_operation(pr, ops, N, fce["persist"], H, i0, i1, "price"),
                     "Rolling plan, persistence forecast": rolling_operation(pr, ops, N, fce["persist"], H, i0, i1, solver=SOLVER),
                     "Rolling plan, regression forecast": rolling_operation(pr, ops, N, fce["ar"], H, i0, i1, solver=SOLVER),
                     "Rolling plan, regression + NESO day-ahead": rolling_operation(pr, ops, N, fce["neso"], H, i0, i1, solver=SOLVER),
                     "Rolling plan, same forecast, expected unsold energy": rolling_operation(pr, ops, N, fce["neso_expected"], H, i0, i1, solver=SOLVER),
                     "Rolling plan, perfect 7-day forecast": rolling_operation(pr, ops, N, fce["perfect"], H, i0, i1, solver=SOLVER)}
            g = solve_chrono(sub(pr.S), sub(pr.Q0), sub(pr.R), sub(pr.p), years, ph, ops, n_modules=N, gap=1e-4, solver=SOLVER)
            paths["Full foresight (upper bound)"] = np.concatenate([np.zeros(i0), g["n"]])
            best = None
            for name, n in paths.items():
                rr = realise(sub(pr.S), sub(pr.Q0), sub(pr.p), sub(n), ph, ops, pr.cap_mwh)
                cash = float(rr["cash"].sum()) / years / 1e6
                if name.startswith("Full"): best = cash
                rows.append(dict(rule=rule, modules=N, h2_value=h2, method=name, operating_cash_m=cash,
                                 days_on_share=float(np.mean(sub(n) > 0)), starts_per_year=float(rr["starts"].sum()) / years,
                                 imported_GWh=float(rr["xg"].sum()) / years / 1e3))
                yearly += [dict(rule=rule, h2_value=h2, method=name, year=int(y), operating_cash_m=float(rr["cash"][yr == y].sum()) / 1e6)
                           for y in np.unique(yr)]
            for r_ in rows[-len(paths):]:
                r_["shortfall_vs_full_foresight_m"] = best - r_["operating_cash_m"]
                r_["share_of_full_foresight"] = r_["operating_cash_m"] / best if best > 0 else np.nan
            log("rolling", rule, h2, "done")
    save(pd.DataFrame(rows), "rolling.csv"); save(pd.DataFrame(yearly), "rolling_by_year.csv")


def scenarios(df, par):
    """(name, group, data frame, parameters, operating assumptions)"""
    base = Ops(min_run=L0)
    out = [("Central case", "central", df, par, base)]
    for v in (5.0, 6.0, 7.0, 8.0, 11.0, 12.0):
        out.append((f"Hydrogen value {v:g}/kg", "hydrogen value", df, replace(par, h2_value=v), base))
    for v in (1.5e6, 2.5e6):
        out.append((f"Electrolyser cost {v / 1e6:g}m/MW", "electrolyser cost", df, replace(par, el_capex=v), base))
    for v in (0.05, 0.10):
        out.append((f"Discount rate {v:.0%}", "discount rate", df, replace(par, rate=v), base))
    for f in (0.9, 1.1):
        d = df.copy(); d["demand_MW"] *= f
        out.append((f"Demand {f - 1:+.0%}", "demand", d, par, base))
    for f in (0.8, 1.2):
        d = df.copy(); d["gen_MW"] += (f - 1) * d["res_MW"]; d["farm_MW"] = (d["farm_MW"] * f).clip(upper=1125.0)
        out.append((f"Wind and solar {f - 1:+.0%}", "renewable output", d, par, base))
    for f in (0.75, 1.25):
        d = df.copy(); d["price"] *= f
        out.append((f"Electricity price {f - 1:+.0%}", "electricity price", d, par, base))
    for v in (20.0, 40.0):
        out.append((f"Grid import charge +{v:g}/MWh", "import charge", df, par, replace(base, import_adder=v)))
    for v in (10_000.0, 50_000.0):
        out.append((f"Start cost {v / 1e3:g}k per module start", "start cost", df, par, replace(base, start_cost=v)))
    for v in (3, 14):
        out.append((f"Minimum run {v} days", "minimum run", df, par, replace(base, min_run=v)))
    for v in (10.0, 25.0, 50.0):
        out.append((f"Hydrogen offtake limit {v:g} t/day", "offtake", df, replace(par, h2_cap_kg_day=v * 1000), base))
    out.append(("2023-2025 only", "years", df.loc["2023-01-01":], par, base))
    out.append(("2020-2022 only", "years", df.loc[:"2022-12-31"], par, base))
    return out


def stage_sensitivity(df, par, prob):
    """Re-size the plant under each alternative assumption: which ones change the strategy?"""
    rows = []
    for name, group, d, p, base in scenarios(df, par):
        pr = Problem(d, p)
        for rule in ("topup", "divert"):
            ops = replace(base, rule=rule)
            b, g, _ = best_size(pr, ops)
            if b:
                r = solve(pr, ops, b)
                s = summarise(pr, r["n"], ops, b, label=name, extra=dict(group=group))
            else:
                s = dict(label=name, group=group, rule=rule, modules=0, electrolyser_MW=0.0, net_gain_m=0.0)
            rows.append(s)
            log("sensitivity", name, rule, "->", b, round(s["net_gain_m"], 2))
        strict = net_gain(pr, replace(base, rule="strict"), 1)[0]
        rows.append(dict(label=name, group=group, rule="strict", modules=1 if strict > 0 else 0,
                         electrolyser_MW=20.0 if strict > 0 else 0.0, net_gain_m=max(strict, 0.0), one_module_net_gain_m=strict))
        save(pd.DataFrame(rows), "sensitivity.csv")


# ---------------------------------------------------------------------------------------------------------
def check(df, par, prob):
    ok = True

    def test(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  {'PASS' if cond else 'FAIL'}  {name}  {detail}")

    for N in (1, 2, 4):
        r = solve(prob, Ops(min_run=1, rule="strict"), N, gap=1e-7)
        mine = float(r["cash"].sum()) / prob.years / 1e6 - par.el_annual * N * par.module_mw / 1e6
        t1 = float(evaluate_exact(prob, N)["net_gain_m"])
        test(f"strict rule with free switching equals the Tier 1 dispatch, {N} module(s)", abs(mine - t1) < 1e-4, f"{mine:.4f} vs {t1:.4f}")
    rng, bad, cases = np.random.default_rng(7), 0, 0
    for rule in RULES:
        for L in (1, 3, 5):
            for N in (1, 2):
                a = int(rng.integers(0, prob.T - 9)); sl = slice(a, a + 9)
                ops = Ops(min_run=L, rule=rule, start_cost=float(rng.choice([0, 20000])), import_adder=float(rng.choice([0, 30])))
                _, bv = brute_force(prob.S[sl], prob.Q0[sl], prob.p[sl], par, ops, N)
                m = solve_chrono(prob.S[sl], prob.Q0[sl], prob.R[sl], prob.p[sl], 1.0, par, ops, n_modules=N, gap=1e-9, solver=SOLVER)
                cases += 1; bad += abs(float(m["cash"].sum()) - bv) > 1e-4 * max(1.0, abs(bv))
    test("programme equals exhaustive search on 9-day windows", bad == 0, f"{cases} cases, {bad} differences")
    ops = Ops(min_run=L0, rule="topup"); r = solve(prob, ops, 2, gap=1e-7)
    cf = realise(prob.S, prob.Q0, prob.p, r["n"], par, ops)["cash"].sum()
    test("closed-form operation of the optimal commitment reproduces the programme's cash", abs(cf - r["cash"].sum()) < 1.0, f"difference {cf - r['cash'].sum():.3f}")
    i0, i1 = 800, 1000
    F = make_forecasts(df, 28, "perfect"); S, Q0 = to_energy(F["farm_MW"], F["gap_MW"], F["price"])
    n = rolling_operation(prob, ops, 2, dict(S=S, Q0=Q0, p=F["price"]), 28, i0, i1, solver=SOLVER)
    sub = lambda a: a[i0:i1 + 1]
    roll = realise(sub(prob.S), sub(prob.Q0), sub(prob.p), sub(n), par, ops)["cash"].sum()
    g = solve_chrono(sub(prob.S), sub(prob.Q0), sub(prob.R), sub(prob.p), 1.0, par, ops, n_modules=2, gap=1e-7, solver=SOLVER)["cash"].sum()
    test("rolling plan with a perfect 28-day forecast matches full foresight", roll > 0.995 * g and roll <= g + 1.0, f"{roll / g:.4f} of the optimum")
    a = solve(prob, Ops(min_run=1, rule="topup"), 2, gap=1e-7)["cash"].sum(); b = solve(prob, Ops(min_run=5, rule="topup"), 2, gap=1e-7)["cash"].sum()
    c = solve(prob, Ops(min_run=14, rule="topup"), 2, gap=1e-7)["cash"].sum()
    test("a longer minimum run never raises the optimum", a >= b - 1 and b >= c - 1, f"{a / 6e6:.3f} >= {b / 6e6:.3f} >= {c / 6e6:.3f} (m per year)")
    s1 = solve(prob, Ops(min_run=5, rule="strict"), 2, gap=1e-7)["cash"].sum(); d1 = solve(prob, Ops(min_run=5, rule="divert"), 2, gap=1e-7)["cash"].sum()
    test("looser rules never lower the optimum (strict <= top-up <= divert)", s1 <= b + 1 and b <= d1 + 1)
    r = solve(prob, Ops(min_run=5, rule="topup"), 2, bat_mwh=100.0, gap=1e-6)
    test("battery state of charge stays inside its usable window", r["soc"].min() > -1e-6 and r["soc"].max() <= 60.0 + 1e-6, f"{r['soc'].min():.2f} to {r['soc'].max():.2f} MWh of 60")
    print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    return ok


def main():
    global SOLVER
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true"); ap.add_argument("--solver", default="highs", choices=["highs", "xpress"])
    ap.add_argument("--stage", nargs="*", default=None)
    a = ap.parse_args()
    SOLVER = a.solver
    df = load_frame(ROOT); par = Params(); prob = Problem(df, par)
    if a.check:
        sys.exit(0 if check(df, par, prob) else 1)
    stages = dict(sizing=stage_sizing, time=stage_time, minrun=stage_minrun, battery=stage_battery, windows=stage_windows,
                  rolling=stage_rolling, sensitivity=stage_sensitivity)
    todo = a.stage if a.stage else list(stages) + ["figs"]
    for s in todo:
        t0 = time.time()
        if s == "figs":
            import t2b_figures; t2b_figures.main()
        else:
            stages[s](df, par, prob)
        log(f"stage {s} finished in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
