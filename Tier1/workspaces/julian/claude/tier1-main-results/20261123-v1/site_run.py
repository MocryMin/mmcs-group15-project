"""Runs every case behind the revised Tier 1 main results and writes the tables.

    python site_run.py --study-dir /path/to/tier1-halfhour-20261113-v7 --output results

The study directory is the group's frozen v7 half-hour study (inputs/halfhour.csv.gz and configuration.json).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import site_battery as sb
import site_model as sm

MAIN_ALPHA = 0.20        # minimum load of an online module (brief; Q&A of 16 November)
MAIN_RUN = 4             # days a started module must stay online (Q&A: "at least 4 or 5 days")
V5_ALPHA = 0.125         # manufacturer minimum used in report v5
CAP = 10_000.0           # kg per UTC day, the report's buyer case
PUBLISHED_C1 = [         # report v5, Table C.1: limit t/day, GBP/kg, A MW, A gain, B MW, B gain
    (4, 7.80, 15.093, 5.66, 20.124, 2.21), (10, 5.00, 35.217, 4.96, 35.217, 1.19),
    (10, 7.80, 40.248, 14.10, 55.341, 5.48), (10, 10.00, 40.248, 21.79, 60.372, 9.49)]
EARLIER = {              # earlier site-scale sensitivity in this member's folder (julian-codex, 22 November)
    ("A", 8, 1): 13.180799620, ("A", 8, 4): 13.163731026, ("A", 8, 5): 13.155458906,
    ("A", 6, 1): 13.471535660, ("A", 6, 4): 13.459603222, ("A", 6, 5): 13.453822112}


def best_flexible(site, policy, alpha, cap_kg, nmax=30):
    rows = []
    for n in range(0, nmax + 1):
        d = sm.flexible_dispatch(site, policy, alpha, n, cap_kg)
        rows.append(sm.metrics(site, policy, d, n, cap_kg, label="flexible", extra=dict(dropped_small_loads=d["dropped"])))
    return max(rows, key=lambda r: r["net_m"]), rows


def best_committed(site, rule, alpha, run, cap_kg, nmax):
    rows = []
    for n in range(0, nmax + 1):
        r, _, _ = sm.solve_case(site, rule, alpha, n, run, cap_kg)
        rows.append(r)
    return max(rows, key=lambda r: r["net_m"]), rows


def sold_after(site, policy, disp):
    """Direct sales per half-hour once the electrolyser has taken its share (flat array)."""
    paid = 0.0 if disp is None else disp["paid"]
    return np.maximum(sm.reference(site, policy)["q"] - paid, 0.0).ravel()


def national_slot_dispatch(site, policy, modules, cap_kg_day):
    """Report v5's common equipment case: half-hour switching with the daily limit split evenly over 48 slots."""
    free = sm.reference(site, policy)["free"]
    hi = min(modules * site.e, cap_kg_day / 48 * site.kwh_per_kg / 1000)
    x_free = np.minimum(free, hi)
    if policy == "A":
        cost = np.maximum(site.p, 0)
        x_paid = np.where(site.w - cost > 0, hi - x_free, 0.0)
    else:
        cost = site.p
        x_paid = np.zeros_like(x_free)
    return dict(h=x_free + x_paid, free=x_free, paid=x_paid, cost=cost)


def eligible_runs(site, alpha):
    """Continuous stretches in which generation left after demand covers one module's minimum load."""
    free = sm.reference(site, "B")["free"].ravel()
    ok = free >= alpha * site.e - 1e-9
    edges = np.flatnonzero(np.diff(np.r_[0, ok.astype(int), 0]))
    a, b = edges[::2], edges[1::2]
    length_h = (b - a) / 2
    usable = np.array([np.minimum(free[i:j], site.e).sum() for i, j in zip(a, b)])     # MWh one module could take
    rows = []
    for h in (0, 6, 12, 24, 48, 72, 96, 120):
        m = length_h >= h
        rows.append(dict(min_load_pct=100 * alpha, at_least_hours=h, stretches=int(m.sum()),
                         stretches_per_year=m.sum() / site.years_equiv, share_of_half_hours_pct=100 * (b - a)[m].sum() / len(free),
                         share_of_one_module_energy_pct=100 * usable[m].sum() / usable.sum()))
    return rows, float(length_h.max())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study-dir", required=True)
    ap.add_argument("--output", default="results")
    a = ap.parse_args()
    out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    site = sm.load(a.study_dir)
    checks = dict(inputs={k: hashlib.sha256((Path(a.study_dir) / k).read_bytes()).hexdigest()
                          for k in ("inputs/halfhour.csv.gz", "configuration.json")}, items=[])

    def check(name, ok, detail):
        checks["items"].append(dict(check=name, passed=bool(ok), detail=detail))
        print(("  PASS  " if ok else "  FAIL  ") + name + "  " + detail, flush=True)

    refA, refB = sm.reference(site, "A"), sm.reference(site, "B")
    check("no-additions figures of report v5 Table II.3", abs(refA["served_pct"] - 89.66) < 0.005 and abs(refB["served_pct"] - 91.03) < 0.005
          and abs(refA["unused_gwh"] - 8647) < 0.5 and abs(refB["unused_gwh"] - 5165) < 0.5,
          f"A {refA['served_pct']:.2f}% / {refA['unused_gwh']:.0f} GWh, B {refB['served_pct']:.2f}% / {refB['unused_gwh']:.0f} GWh")

    # ---- 1. report v5 Table C.1 reproduced, then rebuilt under the main operating rule ------------------------------
    contract = []
    for limit, price, mwA, gA, mwB, gB in PUBLISHED_C1:
        s = site.with_netback(price) if abs(price - 7.80) > 1e-9 else site
        cap = limit * 1000.0
        fa, _ = best_flexible(s, "A", V5_ALPHA, cap)
        fb, _ = best_flexible(s, "B", V5_ALPHA, cap)
        check(f"Table C.1 reproduced, {limit} t/day at GBP {price:.2f}/kg",
              abs(fa["mw"] - mwA) < 1e-6 and abs(fb["mw"] - mwB) < 1e-6 and abs(fa["net_m"] - gA) < 0.006 and abs(fb["net_m"] - gB) < 0.006,
              f"A {fa['mw']:.3f} MW {fa['net_m']:.3f} (published {mwA} / {gA}); B {fb['mw']:.3f} MW {fb['net_m']:.3f} (published {mwB} / {gB})")
        nmax = int(cap * s.kwh_per_kg / 1000 / (SLOTS_PER_DAY * MAIN_ALPHA * s.e))
        ma, _ = best_committed(s, "A", MAIN_ALPHA, MAIN_RUN, cap, min(nmax, 14))
        mb, _ = best_committed(s, "B", MAIN_ALPHA, MAIN_RUN, cap, 3)
        mr, _ = best_committed(s, "B1", MAIN_ALPHA, MAIN_RUN, cap, min(nmax, 20))
        for tag, r in (("v5 rule A", fa), ("v5 rule B", fb), ("main rule A", ma), ("main rule B", mb), ("main rule B with reserve", mr)):
            contract.append(dict(limit_t_per_day=limit, h2_gbp_per_kg=price, case=tag, **{k: r[k] for k in (
                "modules", "mw", "capital_m", "net_m", "payback_years", "h2_t_per_year", "share_from_unsold_pct",
                "served_change_pp", "days_at_95pct_cap_pct", "worst_year_m", "loss_years")}))
    pd.DataFrame(contract).to_csv(out / "contract_cases.csv", index=False)
    curve = []
    for pol in ("A", "B"):
        _, rows = best_flexible(site, pol, V5_ALPHA, CAP, nmax=20)
        curve += [dict(rule=f"{pol}, half-hour switching (report v5)", modules=r["modules"], mw=r["mw"], net_m=r["net_m"]) for r in rows]
    pd.DataFrame(curve).to_csv(out / "sizing_v5_rule.csv", index=False)

    # ---- 1b. the national-scale figures of report v5, as a test of this implementation -------------------------------
    cfg = json.loads((Path(a.study_dir) / "configuration.json").read_text())
    national = []
    for pol, n, gain, served, unused_pub, simple_pub in (("A", 845, 1689.96, 80.57, 4142, -2.605), ("B", 362, 118.38, 91.03, 2353, -0.938)):
        d = national_slot_dispatch(site, pol, n, cfg["cap_kg_day"])
        r = sm.metrics(site, pol, d, n, cfg["cap_kg_day"])
        check(f"report v5 Table II.3 reproduced, electrolysis only, {pol} {n} modules",
              abs(r["net_m"] - gain) < 0.006 and abs(r["served_pct"] - served) < 0.006 and abs(r["unused_gwh"] - unused_pub) < 0.6,
              f"{r['net_m']:.2f} / {r['served_pct']:.2f}% / {r['unused_gwh']:.0f} GWh (published {gain} / {served} / {unused_pub})")
        unused, unmet, price = sb.opportunities(site, pol, d)
        sim = sb.simulate(site, pol, unused, unmet, price)
        check(f"report v5 battery simple rule reproduced at national scale, {pol}", abs((sim["gross"] - sb.ANNUAL) / 1e6 - simple_pub) < 0.0006,
              f"{(sim['gross'] - sb.ANNUAL) / 1e6:.3f} (published {simple_pub})")
        row = dict(policy=pol, modules=n, electrolysis_only_net_m=r["net_m"], served_pct=r["served_pct"], unused_gwh=r["unused_gwh"],
                   battery_simple_rule_net_m=(sim["gross"] - sb.ANNUAL) / 1e6)
        if pol == "A":
            lp = sb.perfect_foresight_A(site, unused, unmet, price, sold=sold_after(site, pol, d))
            row["battery_foresight_gross_m_electrolysers_fixed"] = lp["gross"] / 1e6
            check("battery full foresight with electrolysers held fixed is below the published joint optimum, national A",
                  lp["gross"] / 1e6 <= 7.586 + 1e-3, f"{lp['gross'] / 1e6:.3f} <= 7.586")
        national.append(row)
    pd.DataFrame(national).to_csv(out / "national_scale_test.csv", index=False)

    # ---- 2. operating rules at the v5 sizes, and re-sizing ------------------------------------------------------------
    rules = []
    for pol, n in (("A", 8), ("B", 11)):
        for alpha, tag in ((V5_ALPHA, "v5: half-hour switching, 12.5% minimum"), (MAIN_ALPHA, "half-hour switching, 20% minimum")):
            d = sm.flexible_dispatch(site, pol, alpha, n, CAP)
            rules.append(sm.metrics(site, pol, d, n, CAP, label=tag, extra=dict(rule=pol, min_load_pct=100 * alpha, min_run_days=0)))
        for run, tag in ((1, "day-boundary starts and stops, 20% minimum"), (4, "at least 4 days online, 20% minimum"),
                         (5, "at least 5 days online, 20% minimum")):
            r, _, _ = sm.solve_case(site, pol, MAIN_ALPHA, n, run, CAP, label=tag)
            rules.append(r)
            if (pol, n, run) in EARLIER:
                check(f"earlier site sensitivity reproduced, {pol} {n} modules, run {run}", abs(r["net_m"] - EARLIER[(pol, n, run)]) < 5e-7,
                      f"{r['net_m']:.6f} against {EARLIER[(pol, n, run)]:.6f}")
    r, _, _ = sm.solve_case(site, "A", V5_ALPHA, 8, 4, CAP, label="at least 4 days online, 12.5% minimum")
    rules.append(r)
    pd.DataFrame(rules).to_csv(out / "operating_rules.csv", index=False)

    sizing = []
    best = {}
    for rule, nmax in (("A", 12), ("B", 3), ("B1", 20)):
        for run in (4, 5):
            b, rows = best_committed(site, rule, MAIN_ALPHA, run, CAP, nmax)
            best[(rule, run)] = b
            sizing += rows
            if rule == "A":
                for r in rows:
                    if ("A", r["modules"], run) in EARLIER:
                        check(f"earlier site sensitivity reproduced, A {r['modules']} modules, run {run}",
                              abs(r["net_m"] - EARLIER[("A", r["modules"], run)]) < 5e-7, f"{r['net_m']:.6f}")
    pd.DataFrame(sizing).to_csv(out / "sizing.csv", index=False)
    check("minimum-run programmes solved to optimality", all(abs(r["bound_gap_gbp_per_year"]) < 1.0 and r["path_problems"] == 0 for r in sizing + rules if "bound_gap_gbp_per_year" in r),
          f"largest gap GBP {max(abs(r['bound_gap_gbp_per_year']) for r in sizing):.3f} per year; every path passes the independent minimum-run check")
    check("supply priority cannot hold minimum load", all(r["h2_t_per_year"] < 1e-9 for r in sizing if r["rule"] == "B" and r["modules"] > 0),
          "no production at any size with a 4- or 5-day minimum run")

    # ---- 3. how continuous the surplus is --------------------------------------------------------------------------
    runs, longest = [], {}
    for alpha in (V5_ALPHA, MAIN_ALPHA):
        rr, lg = eligible_runs(site, alpha)
        runs += rr; longest[alpha] = lg
    pd.DataFrame(runs).to_csv(out / "surplus_runs.csv", index=False)
    check("longest continuous surplus for one module is 56 hours", abs(longest[MAIN_ALPHA] - 56.0) < 1e-9, f"{longest[MAIN_ALPHA]:.1f} hours")

    # ---- 4. battery block beside the site-scale plant ------------------------------------------------------------------
    batt = []
    cases = [("A", "A", best[("A", MAIN_RUN)]["modules"]), ("B", "B", 0), ("B with reserve", "B1", best[("B1", MAIN_RUN)]["modules"])]
    schedules = {}
    for tag, rule, n in cases:
        pol = "A" if rule == "A" else "B"
        disp = None
        if n:
            _, path, disp = sm.solve_case(site, rule, MAIN_ALPHA, n, MAIN_RUN, CAP)
        unused, unmet, price = sb.opportunities(site, pol, disp)
        sold = sold_after(site, pol, disp) if pol == "A" else None
        sim = sb.simulate(site, pol, unused, unmet, price)
        fore = sb.perfect_foresight_A(site, unused, unmet, price, sold=sold) if pol == "A" else sb.perfect_foresight_B(site, unused, unmet, price, grid=0.5)
        for name, run in (("simple rule", sim), ("full foresight", fore)):
            problems = sb.audit(run, unused, unmet, pol, sold)
            row = sb.summary(site, run, name, pol)
            row.update(case=tag, electrolyser_modules=n, audit_problems="; ".join(problems),
                       break_even_capital_gbp_per_kwh=(run["gross"] - sb.INITIAL_FILL_ANNUAL) / (0.09634228760924433 + 0.025) / 400_000)
            batt.append(row)
            check(f"battery schedule audit, {tag}, {name}", not problems, "all operating conditions hold" if not problems else "; ".join(problems))
        if pol == "B":
            ub = sb.perfect_foresight_A(site, unused, unmet, price)
            batt[-1]["gross_if_holding_back_allowed_m"] = ub["gross"] / 1e6
            check(f"B full foresight lies between the simple rule and the hold-back bound, {tag}", sim["gross"] - 1 <= fore["gross"] <= ub["gross"] + 1,
                  f"{sim['gross'] / 1e6:.3f} <= {fore['gross'] / 1e6:.3f} <= {ub['gross'] / 1e6:.3f}")
        else:
            check(f"A full foresight is at least the simple rule, {tag}", fore["gross"] >= sim["gross"] - 1, f"{fore['gross'] / 1e6:.3f} >= {sim['gross'] / 1e6:.3f}")
    pd.DataFrame(batt).to_csv(out / "battery.csv", index=False)

    # ---- 4b. does fixing the electrolyser plan first cost the battery anything? ---------------------------------------
    joint = []
    for y in (2022, 2023):
        one = sm.load(a.study_dir, f"{y}-01-01", f"{y}-12-31")
        j = sb.joint_check(one, best[("A", MAIN_RUN)]["modules"], CAP)
        j.update(year=y, difference_m=j["joint_battery_value_m"] - j["fixed_plan_battery_value_m"])
        joint.append(j)
        check(f"battery scheduled jointly with the electrolyser, {y}", 0 <= j["difference_m"] + 1e-6 and j["difference_m"] < 0.01 * j["joint_battery_value_m"],
              f"joint {j['joint_battery_value_m']:.3f}, electrolyser fixed first {j['fixed_plan_battery_value_m']:.3f}, difference {j['difference_m']:.3f}")
        check(f"closed-form electrolysis dispatch equals the linear programme, {y}", abs(j["electrolysis_lp_minus_greedy_gbp"]) < 1.0,
              f"difference GBP {j['electrolysis_lp_minus_greedy_gbp']:.4f}")
    pd.DataFrame(joint).to_csv(out / "joint_test.csv", index=False)

    # ---- 5. the main table --------------------------------------------------------------------------------------------
    main_rows = []
    def add(policy, plan, modules, net, served, unused, h2=np.nan, capital=np.nan, payback=np.nan, note=""):
        main_rows.append(dict(policy=policy, plan=plan, electrolyser_modules=modules, electrolyser_mw=modules * site.module_mw if modules == modules else np.nan,
                              net_gain_m=net, demand_served_pct=served, unused_gwh=unused, h2_t_per_year=h2, capital_m=capital, payback_years=payback, note=note))
    bt = {(r["case"], r["label"]): r for r in batt}
    for tag, rule, pol, ref in (("A", "A", "A", refA), ("B", "B", "B", refB), ("B with reserve", "B1", "B", refB)):
        e = best[(rule, MAIN_RUN)]
        add(tag, "No additions", 0, 0.0, ref["served_pct"], ref["unused_gwh"], 0.0, 0.0)
        add(tag, "Electrolysis only", e["modules"], e["net_m"], e["served_pct"], e["unused_gwh"], e["h2_t_per_year"], e["capital_m"], e["payback_years"])
        for name in ("simple rule", "full foresight"):
            b = bt[(tag, name)]
            add(tag, f"Electrolysis and one battery block, {name}", e["modules"], e["net_m"] + b["net_m"], e["served_pct"] + b["served_gain_pp"],
                e["unused_gwh"] - b["charged_from_unused_gwh"], e["h2_t_per_year"], e["capital_m"] + sb.CAPITAL / 1e6, np.nan,
                note=f"battery alone: net {b['net_m']:.3f}, payback {b['payback_years']:.1f} years")
    pd.DataFrame(main_rows).to_csv(out / "main_table.csv", index=False)
    checks["runtime_seconds"] = time.time() - t0
    checks["all_passed"] = all(i["passed"] for i in checks["items"])
    (out / "checks.json").write_text(json.dumps(checks, indent=2))
    print("ALL CHECKS PASSED" if checks["all_passed"] else "SOME CHECKS FAILED", f"({time.time() - t0:.0f}s)")


SLOTS_PER_DAY = sm.SLOTS

if __name__ == "__main__":
    main()
