"""Independent Tier 1 - run the four methods, integrate them, test sensitivities, draw figures.

Usage:  python t1_run.py            full study -> results/
        python t1_run.py --check    fast consistency checks
        python t1_run.py --solver xpress   (MILPs through Xpress; untested where this was written)
"""
from __future__ import annotations
import argparse, json, time
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import t1_data
import t1_model as M

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
POLICIES = ("surplus", "divert")
BLUE, ORANGE, AQUA, YELLOW, VIOLET, RED, GREEN = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#6250d6", "#e34948", "#008300"
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"


def style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "font.size": 10,
        "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.edgecolor": AXIS,
        "axes.labelcolor": INK2, "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK2, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
        "ytick.major.size": 0, "lines.linewidth": 2, "legend.frameon": False})
    return plt


def flat(r):
    return {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in r.items() if k != "by_year"}


def best_n(prob):
    """Exact optimum over whole modules when no battery is built."""
    rows = [M.evaluate_exact(prob, n) for n in range(prob.n_max + 1)]
    return max(rows, key=lambda r: r["net_gain_m"]), rows


def study(solver="highs"):
    OUT.mkdir(exist_ok=True)
    t0 = time.time()
    df = t1_data.load()
    base = M.Params()
    summary = {"parameters": {k: getattr(base, k) for k in base.__dataclass_fields__},
               "derived": dict(margin_GBP_per_MWh=base.margin, h2_value_per_MWh=base.h2_value * 1000 / base.kwh_per_kg, stack_cost_per_MWh=base.stack_cost,
                               electrolyser_annual_cost_per_MW=base.el_annual, battery_annual_cost_per_MWh=base.bat_annual,
                               breakeven_full_load_hours=base.el_annual / base.margin)}
    p0 = M.Problem(df, base)
    farm = df.farm_MW.to_numpy() * 24
    summary["baseline"] = dict(
        years=p0.years, farm_output_GWh_per_year=farm.sum() / p0.years / 1e3, unused_GWh_per_year=p0.S.sum() / p0.years / 1e3,
        unused_share=float(p0.S.sum() / farm.sum()), days_with_unused_energy=float((p0.S > 0).mean()),
        days_fully_unsold=float((p0.Q0 <= 0).mean()), national_generation_above_demand_days=float((df.gen_MW > df.demand_MW).mean()),
        revenue_if_all_output_sold_m=float((farm * df.price).sum() / p0.years / 1e6), revenue_actually_saleable_m=p0.base_revenue / 1e6,
        mean_price=float(df.price.mean()), unused_share_by_year={int(y): float(p0.S[df.index.year == y].sum() / farm[df.index.year == y].sum()) for y in sorted(set(df.index.year))})
    print(json.dumps(summary["baseline"], indent=1))

    # ---------------- the four methods
    methods, curves, by_n = [], {}, []
    designs = {}
    for pol in POLICIES:
        prob = M.Problem(df, replace(base, policy=pol))
        r1, curve = M.m1_duration_curve(prob); curve["policy"] = pol; curves[pol] = curve
        r2 = M.m2_rep_weeks(prob, k=52, solver=solver)
        r2x = M.evaluate_exact(prob, r2["modules"]) if r2["battery_MWh"] < 1e-6 else M.m3_chronological(prob, fix_n=r2["modules"], fix_b=r2["battery_MWh"], solver=solver)
        r2.update(net_gain_m=r2x["net_gain_m"], capex_m=r2x["capex_m"], h2_t_per_year=r2x["h2_t_per_year"], payback_years=r2x["payback_years"], worst_year_m=r2x["worst_year_m"])
        r3 = M.m3_chronological(prob, solver=solver, time_limit=400)
        r4, _ = M.m4_sim_search(prob)
        for r in (r1, r2, r3, r4):
            methods.append(flat(r)); print(pol, r["label"], r["modules"], round(r["battery_MWh"], 2), round(r["net_gain_m"], 3))
        designs[pol] = dict(M1=r1["modules"], M2=r2["modules"], M3=r3["modules"], M4=r4["modules"])
        opt, rows = best_n(prob)
        for r in rows:
            by_n.append(dict(policy=pol, modules=r["modules"], electrolyser_MW=r["electrolyser_MW"], net_gain_m=r["net_gain_m"], cash_gain_m=r["cash_gain_m"],
                             capex_m=r["capex_m"], h2_t_per_year=r["h2_t_per_year"], utilisation=r["utilisation"], worst_year_m=r["worst_year_m"],
                             unused_captured_share=r["unused_captured_share"], payback_years=r["payback_years"]))
    methods = pd.DataFrame(methods); methods.to_csv(OUT / "method_results.csv", index=False)
    by_n = pd.DataFrame(by_n); by_n.to_csv(OUT / "profit_by_modules.csv", index=False)
    pd.concat(curves.values()).to_csv(OUT / "marginal_value_curve.csv", index=False)
    print("methods done", round(time.time() - t0), "s")

    # ---------------- M2 convergence: how many representative weeks are enough
    conv = []
    for pol in POLICIES:
        prob = M.Problem(df, replace(base, policy=pol))
        opt, _ = best_n(prob)
        for k in (8, 12, 26, 52, 104):
            for seed in range(4):
                r = M.m2_rep_weeks(prob, k=k, seed=seed, solver=solver)
                ex = M.evaluate_exact(prob, r["modules"])
                conv.append(dict(policy=pol, weeks=k, seed=seed, modules=r["modules"], battery_MWh=r["battery_MWh"], own_model_net_gain_m=r["net_gain_m_own_model"],
                                 true_net_gain_m=ex["net_gain_m"], loss_vs_optimum_m=opt["net_gain_m"] - ex["net_gain_m"]))
    conv = pd.DataFrame(conv); conv.to_csv(OUT / "m2_convergence.csv", index=False)
    print("convergence done", round(time.time() - t0), "s")

    # ---------------- battery: forced sizes, perfect foresight vs rules
    bat = []
    for pol in POLICIES:
        par = replace(base, policy=pol, min_load_mode="none")
        prob = M.Problem(df, par)
        opt, _ = best_n(prob)
        for b in (25.0, 100.0, 400.0):
            pf = M.m3_chronological(prob, fix_b=b, solver=solver, time_limit=200)
            sim = M.simulate(prob, opt["modules"], b)
            bat.append(dict(policy=pol, battery_MWh=b, modules_perfect_foresight=pf["modules"], net_gain_perfect_foresight_m=pf["net_gain_m"],
                            net_gain_rules_m=sim["net_gain_m"], net_gain_without_battery_m=opt["net_gain_m"],
                            gross_value_per_MWh_perfect_foresight=(pf["net_gain_m"] - opt["net_gain_m"]) * 1e6 / b + par.bat_annual,
                            gross_value_per_MWh_rules=(sim["net_gain_m"] - opt["net_gain_m"]) * 1e6 / b + par.bat_annual,
                            annual_cost_per_MWh=par.bat_annual))
    bat = pd.DataFrame(bat)
    bat["breakeven_capex_per_MWh"] = bat.gross_value_per_MWh_perfect_foresight / (base.crf_bat + base.bat_fom)
    bat.to_csv(OUT / "battery_value.csv", index=False)
    print("battery done", round(time.time() - t0), "s")

    # ---------------- integration: cross-evaluation by year, split sample
    cross, split, yearly = [], [], []
    years = sorted(set(df.index.year))
    recommended = {}
    for pol in POLICIES:
        par = replace(base, policy=pol); prob = M.Problem(df, par)
        opt, rows = best_n(prob)
        year_best = {}
        for y in years:
            sub = prob.subset(df.index.year == y)
            ob, _ = best_n(sub); year_best[y] = ob
            yearly.append(dict(policy=pol, year=y, best_modules=ob["modules"], best_net_gain_m=ob["net_gain_m"],
                               unused_share=float(sub.S.sum() / (df.farm_MW[df.index.year == y].sum() * 24)), mean_price=float(sub.p.mean())))
        cands = {f"{k} design": v for k, v in designs[pol].items()}
        cands.update({"Do nothing": 0, "One 20 MW reference unit": 1, "Sized to the farm (1,140 MW)": prob.n_max})
        for name, n in cands.items():
            r = rows[n]
            regrets = [year_best[y]["net_gain_m"] - M.evaluate_exact(prob.subset(df.index.year == y), n)["net_gain_m"] for y in years]
            row = dict(policy=pol, design=name, modules=n, net_gain_m=r["net_gain_m"], worst_year_m=r["worst_year_m"], capex_m=r["capex_m"],
                       payback_years=r["payback_years"], max_regret_m=max(regrets), mean_regret_m=float(np.mean(regrets)))
            row.update({f"y{y}": M.evaluate_exact(prob.subset(df.index.year == y), n)["net_gain_m"] for y in years})
            cross.append(row)
        # min-max regret over whole modules
        reg = []
        for n in range(prob.n_max + 1):
            reg.append(max(year_best[y]["net_gain_m"] - M.evaluate_exact(prob.subset(df.index.year == y), n)["net_gain_m"] for y in years))
        recommended[pol] = dict(expected_value_modules=opt["modules"], minmax_regret_modules=int(np.argmin(reg)), minmax_regret_m=float(min(reg)))
        for a, b in ((("2020", "2022"), ("2023", "2025")), (("2023", "2025"), ("2020", "2022"))):
            tr = prob.subset((df.index >= a[0]) & (df.index <= a[1] + "-12-31")); te = prob.subset((df.index >= b[0]) & (df.index <= b[1] + "-12-31"))
            n_tr = best_n(tr)[0]["modules"]; te_opt = best_n(te)[0]
            split.append(dict(policy=pol, designed_on=f"{a[0]}-{a[1]}", tested_on=f"{b[0]}-{b[1]}", modules=n_tr, net_gain_on_test_m=M.evaluate_exact(te, n_tr)["net_gain_m"],
                              test_period_optimum_modules=te_opt["modules"], test_period_optimum_m=te_opt["net_gain_m"]))
    cross = pd.DataFrame(cross); cross.to_csv(OUT / "cross_evaluation.csv", index=False)
    pd.DataFrame(split).to_csv(OUT / "split_sample.csv", index=False)
    yearly = pd.DataFrame(yearly); yearly.to_csv(OUT / "by_year_optimum.csv", index=False)
    summary["integration"] = dict(designs_by_method=designs, recommended=recommended)

    # ---------------- sensitivities
    sens = []
    def case(name, group, par_changes=None, frame=None, **prob_kw):
        for pol in POLICIES:
            par = replace(base, policy=pol, **(par_changes or {}))
            prob = M.Problem(df if frame is None else frame, par, **prob_kw)
            o, _ = best_n(prob)
            ref = M.evaluate_exact(prob, designs[pol]["M3"]) if designs[pol]["M3"] <= prob.n_max else None
            sens.append(dict(group=group, case=name, policy=pol, modules=o["modules"], electrolyser_MW=o["electrolyser_MW"], net_gain_m=o["net_gain_m"],
                             payback_years=o["payback_years"], h2_t_per_year=o["h2_t_per_year"], worst_year_m=o["worst_year_m"],
                             central_design_net_gain_m=ref["net_gain_m"] if ref else np.nan))
    case("Central", "central")
    for v in (5.0, 7.0, 8.0, 11.0, 12.0): case(f"Hydrogen value GBP {v:g}/kg", "hydrogen", dict(h2_value=v))
    for c in (1.5e6, 2.5e6): case(f"Electrolyser capex GBP {c / 1e6:g}m/MW", "cost", dict(el_capex=c))
    for r in (0.05, 0.10): case(f"Discount rate {r:.0%}", "cost", dict(rate=r))
    for f in (0.02, 0.05): case(f"Fixed O&M {f:.0%} of capex", "cost", dict(el_fom=f))
    case("Stack 48% of capex (Andoni et al.)", "cost", dict(stack_share=0.48)); case("Stack 16% of capex (TNO low)", "cost", dict(stack_share=0.16))
    case("Plant life 30 years", "cost", dict(el_life=30))
    case("Minimum load 20% of whole plant", "technical", dict(min_load_mode="plant")); case("No minimum load", "technical", dict(min_load_mode="none"))
    case("Whole fleet is the client's pool (system boundary)", "boundary", dict(boundary="system", n_max=600))
    d2 = df.copy(); raw = d2.demand_raw.where(d2.demand_raw > 10000).interpolate("time").bfill(); d2["demand_MW"] = raw
    case("Data: weekly-window fault NOT fixed in demand", "data", frame=d2)
    d3 = df[~df.gen_imputed]
    case("Data: days with imputed generation dropped", "data", frame=d3)
    case("Data: prices as supplied (no x2 correction)", "data", price_col="price_as_supplied_real")
    case("Data: nominal prices (no CPI adjustment)", "data", price_col="price_nominal")
    for s in (0.75, 1.25):
        d4 = df.copy(); d4["price"] = d4.price * s; case(f"Electricity price x{s}", "market", frame=d4)
    for name, mask in (("Only 2023-2025", df.index.year >= 2023), ("Only 2025 (latest system)", df.index.year == 2025), ("Excluding 2021-2022 (energy crisis)", ~df.index.year.isin([2021, 2022]))):
        case(f"History: {name}", "history", frame=df[mask])
    for cap in (5, 10, 25, 50, 100): case(f"Hydrogen offtake limit {cap} t/day", "offtake", dict(h2_cap_kg_day=cap * 1000.0))
    sens = pd.DataFrame(sens); sens.to_csv(OUT / "sensitivity.csv", index=False)

    dmap = []
    for pol in POLICIES:
        for v in (4, 5, 6, 7, 8, 9.5, 11, 12.5, 14):
            for c in (1.0e6, 1.25e6, 1.5e6, 1.75e6, 2.0e6, 2.25e6, 2.5e6):
                o, _ = best_n(M.Problem(df, replace(base, policy=pol, h2_value=float(v), el_capex=c)))
                dmap.append(dict(policy=pol, h2_value=v, el_capex_m=c / 1e6, modules=o["modules"], electrolyser_MW=o["electrolyser_MW"], net_gain_m=o["net_gain_m"]))
    dmap = pd.DataFrame(dmap); dmap.to_csv(OUT / "decision_map.csv", index=False)
    json.dump(summary, open(OUT / "summary.json", "w"), indent=2, default=float)
    figures(df, base, summary, methods, by_n, curves, conv, bat, cross, yearly, sens, dmap, designs)
    print("all done", round(time.time() - t0), "s")


def figures(df, base, summary, methods, by_n, curves, conv, bat, cross, yearly, sens, dmap, designs):
    plt = style()
    p0 = M.Problem(df, base)
    # 1. the unused energy
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4))
    s_mw = np.sort(p0.S / 24)[::-1]; x = np.arange(len(s_mw)) / len(s_mw) * 100
    axs[0].fill_between(x, s_mw, color=BLUE, alpha=0.18, lw=0); axs[0].plot(x, s_mw, color=BLUE)
    be = base.el_annual / base.margin / 8766 * 100
    axs[0].axvline(be, color=INK2, lw=1, ls="--"); axs[0].text(be + 0.6, 1020, f"an electrolyser must run\n{be:.0f}% of the time to pay back", fontsize=9, color=INK2, va="top")
    axs[0].set_xlim(0, 40); axs[0].set_ylim(0, 1150); axs[0].set_xlabel("% of days"); axs[0].set_title("Farm output with no buyer, sorted (MW)")
    ys = summary["baseline"]["unused_share_by_year"]
    axs[1].bar([str(y) for y in ys], [v * 100 for v in ys.values()], color=BLUE, width=0.62)
    for i, v in enumerate(ys.values()): axs[1].text(i, v * 100 + 1, f"{v:.0%}", ha="center", fontsize=9, color=INK2)
    axs[1].set_title("Share of the farm's output with no buyer, by year (%)"); axs[1].set_ylim(0, 55)
    fig.savefig(OUT / "fig1_unused_energy.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # 2. marginal value of capacity (M1)
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    for pol, c, lab in (("surplus", BLUE, "Unused energy only"), ("divert", ORANGE, "Also diverting saleable output")):
        cv = curves[pol]; ax.plot(cv.MW, cv.marginal_value / 1e3, color=c, label=lab)
    ax.axhline(base.el_annual / 1e3, color=INK2, lw=1, ls="--"); ax.text(1120, base.el_annual / 1e3 + 15, "annual cost of one MW", ha="right", fontsize=9, color=INK2)
    ax.set_xlabel("electrolyser capacity already installed (MW)"); ax.set_title("Value of one more MW of electrolyser (GBP thousand per year)"); ax.set_ylim(0); ax.set_xlim(0, 1140); ax.legend()
    fig.savefig(OUT / "fig2_marginal_value.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # 3. net gain by size, with the four methods' picks
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4))
    for ax, pol, c, ttl in ((axs[0], "surplus", BLUE, "Unused energy only"), (axs[1], "divert", ORANGE, "Also diverting saleable output")):
        b = by_n[by_n.policy == pol]
        ax.plot(b.electrolyser_MW, b.net_gain_m, color=c)
        ax.axhline(0, color=AXIS, lw=1)
        for k, mk in zip(("M1", "M2", "M3", "M4"), ("o", "s", "D", "^")):
            n = designs[pol][k]; ax.plot(n * base.module_mw, b.net_gain_m.iloc[n], mk, color=INK, ms=7, mfc="none", mew=1.5, label=k)
        ax.set_title(f"{ttl}: annualised net gain (GBP m/yr)"); ax.set_xlabel("electrolyser capacity (MW)")
        if pol == "surplus": ax.set_xlim(0, 400); ax.set_ylim(-25, 5)
    axs[0].legend(title="method picks", ncol=4, fontsize=9, loc="lower left")
    fig.savefig(OUT / "fig3_net_gain_by_size.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # 4. decision map
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.4))
    for ax, pol, ttl in ((axs[0], "surplus", "Unused energy only"), (axs[1], "divert", "Also diverting saleable output")):
        pv = dmap[dmap.policy == pol].pivot(index="h2_value", columns="el_capex_m", values="electrolyser_MW").sort_index(ascending=False)
        im = ax.imshow(pv.values, cmap="Blues", aspect="auto", vmin=0, vmax=1140)
        ax.set_xticks(range(pv.shape[1])); ax.set_xticklabels([f"{c:g}" for c in pv.columns]); ax.set_yticks(range(pv.shape[0])); ax.set_yticklabels([f"{v:g}" for v in pv.index])
        for i in range(pv.shape[0]):
            for j in range(pv.shape[1]):
                v = pv.values[i, j]; ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8.5, color="white" if v > 600 else INK)
        ax.set_xlabel("electrolyser capex (GBP m per MW)"); ax.set_ylabel("hydrogen value (GBP/kg)"); ax.set_title(f"{ttl}: best size (MW)"); ax.grid(False)
    fig.savefig(OUT / "fig4_decision_map.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # 5. by year
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4))
    for ax, pol, c in ((axs[0], "surplus", BLUE), (axs[1], "divert", ORANGE)):
        row = cross[(cross.policy == pol) & (cross.design == "M3 design")].iloc[0]
        ys = [k for k in row.index if k.startswith("y2")]
        vals = [row[k] for k in ys]
        ax.bar([k[1:] for k in ys], vals, color=[c if v >= 0 else RED for v in vals], width=0.62); ax.axhline(0, color=AXIS, lw=1)
        for i, v in enumerate(vals): ax.text(i, v + (abs(max(vals, key=abs)) * 0.03 if v >= 0 else -abs(max(vals, key=abs)) * 0.08), f"{v:.1f}", ha="center", fontsize=9, color=INK2)
        ax.set_title(f"{'Unused energy only' if pol == 'surplus' else 'Also diverting'}: {int(row.modules) * 20} MW, net gain by year (GBP m)")
    fig.savefig(OUT / "fig5_by_year.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # 6. representative weeks convergence
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.8))
    for ax, pol, c in ((axs[0], "surplus", BLUE), (axs[1], "divert", ORANGE)):
        cv = conv[conv.policy == pol]
        ax.scatter(cv.weeks.astype(str), cv.modules * 20, color=c, s=36, alpha=0.75)
        ax.axhline(designs[pol]["M3"] * 20, color=INK2, lw=1, ls="--")
        ax.set_xlabel("representative weeks used (4 random starts each)"); ax.set_title(f"{'Unused energy only' if pol == 'surplus' else 'Also diverting'}: size chosen by the simplified model (MW)")
    fig.savefig(OUT / "fig6_rep_weeks_convergence.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # 7. sensitivity, surplus policy
    s = sens[(sens.policy == "surplus") & ~sens.group.isin(["offtake"])].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9.5, 8))
    y = np.arange(len(s))[::-1]
    ax.barh(y, s.electrolyser_MW, color=[INK2 if g == "central" else BLUE for g in s.group], height=0.62)
    for yy, v, g in zip(y, s.electrolyser_MW, s.net_gain_m): ax.text(v + 8, yy, f"{v:.0f} MW   £{g:.1f}m/yr", va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(y); ax.set_yticklabels(s.case, fontsize=9); ax.grid(axis="x"); ax.grid(axis="y", visible=False); ax.set_xlim(0, s.electrolyser_MW.max() * 1.35 + 40)
    ax.set_title("Unused energy only: best electrolyser size under changed assumptions (MW)")
    fig.savefig(OUT / "fig7_sensitivity_surplus.png", dpi=160, bbox_inches="tight"); plt.close(fig)


def check(solver="highs"):
    df = t1_data.load("2024-01-01", "2025-12-31")
    for pol in POLICIES:
        par = M.Params(policy=pol); prob = M.Problem(df, par)
        o, _ = best_n(prob); r1, _ = M.m1_duration_curve(prob); r4, _ = M.m4_sim_search(prob)
        r3 = M.m3_chronological(prob, solver=solver, time_limit=200)
        print(f"{pol:8s} modules  exact {o['modules']}  M1 {r1['modules']}  M3 {r3['modules']}  M4 {r4['modules']}   net gain exact {o['net_gain_m']:.4f}  M3 {r3['net_gain_m']:.4f}")
        assert abs(o["net_gain_m"] - r3["net_gain_m"]) < 1e-3 * max(1, abs(o["net_gain_m"]))
        fixed = M.m3_chronological(prob, fix_n=3, fix_b=0.0, solver=solver)
        assert abs(fixed["net_gain_m"] - M.evaluate_exact(prob, 3)["net_gain_m"]) < 1e-6, "closed form and MILP disagree for a fixed design"
        par2 = M.Params(policy=pol, min_load_mode="none"); pr2 = M.Problem(df, par2)
        pf = M.m3_chronological(pr2, fix_n=o["modules"], fix_b=100.0, solver=solver); sim = M.simulate(pr2, o["modules"], 100.0)
        print(f"         100 MWh battery: perfect foresight {pf['net_gain_m']:.4f} >= rules {sim['net_gain_m']:.4f}")
        assert pf["net_gain_m"] >= sim["net_gain_m"] - 1e-6
    # hand example: one day with 600 MWh unused, one 20 MW module -> 480 MWh -> 8,587 kg -> margin 480 x 157.9
    par = M.Params(); one = pd.DataFrame({"farm_MW": [25.0], "gen_MW": [100.0], "demand_MW": [100.0], "price": [80.0]}, index=pd.to_datetime(["2023-06-01"]))
    r = M.evaluate_exact(M.Problem(one, par), 1)
    print(f"hand example: hydrogen {r['h2_t_per_year'] / 365:.3f} t in the day (expected {480 / 55.9:.3f}), margin GBP {480 * par.margin:,.0f}")
    assert abs(r["h2_t_per_year"] / 365 - 480 / 55.9) < 1e-9
    print("all checks passed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); ap.add_argument("--solver", default="highs")
    a = ap.parse_args()
    check(a.solver) if a.check else study(a.solver)
