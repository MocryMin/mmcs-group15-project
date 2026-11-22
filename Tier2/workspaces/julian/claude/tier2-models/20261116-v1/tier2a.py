"""Tier 2A - generation investment (MMCS Group 15).

Question: on top of the existing system and the Tier 1 flexibility options, which new generation
(offshore wind, onshore wind, solar) should the client fund, how much, and where do returns diminish?

Decision variables (chosen once for the whole 2020-2025 history):
    x_k   new capacity of technology k [MW]         E   electrolyser [MW AC input]
    B     battery energy [MWh, 2-hour product]      daily operation of sales, hydrogen and battery
Objective: maximise annualised net benefit in GBP2020 (revenue minus annuity and fixed costs),
subject to a capital budget.  Zero new capacity reproduces the Tier 1 case.

Usage:  python tier2a.py                 full study, writes results_2a/
        python tier2a.py --check         quick reproduction check against Tier 1 v6
        python tier2a.py --solver xpress (same model through the Xpress API; see common.LP)
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
import common as C

OUT = C.ROOT / "results_2a"
DEFLATE_2023 = C.CPI_ANNUAL[2020] / C.CPI_ANNUAL[2023]      # 2023 real prices -> GBP2020

# Arup for DESNZ, "Renewable Energy Generation Cost and Technical Assumptions 2024" (2023 real prices):
# total capex GBP/kW, total opex kGBP/MW/yr (O&M + insurance + connection/use-of-system), net load factor, life.
TECH = {
    "offshore": {"low": (3321, 73.8, 0.460, 35), "medium": (3976, 138.5, 0.505, 35), "high": (4439, 207.2, 0.561, 35)},
    "onshore":  {"low": (1241, 17.4, 0.330, 25), "medium": (1588, 40.1, 0.381, 35), "high": (2205, 72.4, 0.413, 40)},
    "solar":    {"low": (526, 6.5, 0.115, 35),   "medium": (659, 9.3, 0.122, 38),   "high": (788, 12.3, 0.145, 40)},
}
NAMES = list(TECH)
LABEL = {"offshore": "Offshore wind", "onshore": "Onshore wind", "solar": "Solar PV"}


def tech_costs(case="medium", rate=C.RATE, capex_scale=1.0):
    """Per-MW capex and annual cost in GBP2020.  Note: in the Arup 'high' case the higher load factor
    comes with the higher cost; the load factor is applied separately through `profiles`."""
    out = {}
    for k, cases in TECH.items():
        capex_kw, opex_k, lf, life = cases[case]
        capex = capex_kw * 1000 * DEFLATE_2023 * capex_scale
        out[k] = dict(capex=capex, annual=C.crf(rate, life) * capex + opex_k * 1000 * DEFLATE_2023, lf=lf, life=life)
    return out


def _rescale(shape, target):
    """Scale a non-negative daily shape to a target mean capacity factor, clipping at 1."""
    cf = shape / shape.mean() * target
    for _ in range(50):
        cf = np.minimum(cf, 1.0)
        if abs(cf.mean() - target) < 1e-9:
            break
        cf = cf * target / cf.mean()
    return np.minimum(cf, 1.0)


def profiles(df, costs):
    """Daily capacity factors per technology, built from the supplied history.
    offshore: the client's simulated farm (ERA5-driven); onshore, solar: national daily series with the
    capacity trend removed year by year.  Each is scaled to the sourced net load factor."""
    yr = df.index.year
    on = (df.onshore_MW / df.onshore_MW.groupby(yr).transform("mean")).to_numpy()
    so = (df.solar_MW / df.solar_MW.groupby(yr).transform("mean")).to_numpy()
    off = (df.farm_MW / 1125.0).to_numpy()
    return {"offshore": _rescale(off, costs["offshore"]["lf"]), "onshore": _rescale(on, costs["onshore"]["lf"]),
            "solar": _rescale(so, costs["solar"]["lf"])}


def solve(df, policy="A", budget=None, costs=None, cf=None, cap_kg=C.H2_CAP_KG_DAY, netback=C.H2_NETBACK,
          fix_x=None, fix_e=None, battery=True, price=None, solver="highs", rate=C.RATE):
    """One investment + operation optimisation.  Returns a result dict (money in GBP2020 m/yr)."""
    costs = costs or tech_costs()
    cf = cf or profiles(df, costs)
    T, yrs = len(df), C.years_in(df)
    g, d = df.g.to_numpy(), df.d.to_numpy()
    p = df.price.to_numpy() if price is None else np.asarray(price, float)
    kg_per_gwh = 1e6 / C.H2_KWH_PER_KG
    el_annual = C.crf(rate, C.EL_LIFE) * C.EL_PV_PER_MW + C.EL_FOM_PER_MW
    bat_annual = C.crf(rate, C.BAT_LIFE) * C.BAT_CAPEX_PER_MWH + C.BAT_FOM_PER_MWH
    gen = np.column_stack([0.024 * cf[k] for k in NAMES])          # GWh per MW-day

    def build(surplus_set):
        lp = C.LP()
        x = lp.var(3, c=[-costs[k]["annual"] / 1e6 for k in NAMES])
        e = lp.var(1, c=-el_annual / 1e6)
        b = lp.var(1, c=-bat_annual / 1e6, ub=np.inf if (battery and policy == "A") else 0.0)
        if fix_x is not None:
            for i, v in enumerate(fix_x):
                lp.lb[x[i]] = lp.ub[x[i]] = float(v)
        if fix_e is not None:
            lp.lb[e[0]] = lp.ub[e[0]] = float(fix_e)
        q = lp.var(T, ub=d, c=p * 1000 / yrs / 1e6)                         # direct sales, GWh
        a = lp.var(T, ub=cap_kg / kg_per_gwh, c=netback * kg_per_gwh / yrs / 1e6)   # electricity to hydrogen, GWh
        tt = np.arange(T)
        # a_t <= 0.024 E
        lp.rows(np.column_stack([a, np.full(T, e[0])]), np.column_stack([np.ones(T), np.full(T, -0.024)]), hi=0.0)
        if policy == "A":
            ch = lp.var(T); dis = lp.var(T, c=p * 1000 / yrs / 1e6); soc = lp.var(T)
            eta = np.sqrt(C.BAT_RTE)
            # q + a + ch - sum_k gen_k x_k <= g
            lp.rows(np.column_stack([q, a, ch, np.tile(x, (T, 1))]), np.column_stack([np.ones((T, 3)), -gen]), hi=g)
            lp.rows(np.column_stack([q, dis]), np.ones((T, 2)), hi=d)
            # soc_t - soc_{t-1} - eta ch + dis/eta = 0   (soc_{-1} = 0, soc_{T-1} = 0)
            lp.row([soc[0], ch[0], dis[0]], [1, -eta, 1 / eta], lo=0, hi=0)
            lp.rows(np.column_stack([soc[1:], soc[:-1], ch[1:], dis[1:]]),
                    np.column_stack([np.ones(T - 1), -np.ones(T - 1), np.full(T - 1, -eta), np.full(T - 1, 1 / eta)]), lo=0, hi=0)
            lp.ub[soc[-1]] = 0.0
            lp.rows(np.column_stack([soc, np.full(T, b[0])]), np.column_stack([np.ones(T), np.full(T, -C.BAT_USABLE / 1000)]), hi=0.0)
        else:
            s = np.zeros(T, bool); s[surplus_set] = True
            # sales cannot exceed generation: q - gen x <= g
            lp.rows(np.column_stack([q, np.tile(x, (T, 1))]), np.column_stack([np.ones(T), -gen]), hi=g)
            for t in np.flatnonzero(~s):
                lp.ub[a[t]] = 0.0                                             # hydrogen only from surplus
            ts = np.flatnonzero(s)
            if len(ts):                                                     # a_t <= G_t(x) - d_t on surplus days
                lp.rows(np.column_stack([a[ts], np.tile(x, (len(ts), 1))]), np.column_stack([np.ones(len(ts)), -gen[ts]]), hi=g[ts] - d[ts])
        if budget is not None:
            lp.row(list(x) + [e[0], b[0]], [costs[k]["capex"] for k in NAMES] + [C.EL_CAPEX_PER_MW, C.BAT_CAPEX_PER_MWH], hi=budget)
        sol, obj = lp.solve(solver)
        return sol[x], float(sol[e[0]]), float(sol[b[0]]), obj

    if policy == "A":
        xv, ev, bv, _ = build(None)
    else:                                   # B: fixed point on the set of surplus days
        sset = np.flatnonzero(g > d)
        for _ in range(12):
            xv, ev, bv, _ = build(sset)
            new = np.flatnonzero(g + gen @ xv > d + 1e-9)
            if set(new) <= set(sset):
                break
            sset = np.union1d(sset, new)
    return evaluate(df, policy, xv, ev, bv, costs, cf, cap_kg, netback, p, solver, rate)


def reference_revenue(g, d, p, policy):
    sales = np.minimum(g, d)
    return float(np.sum(np.where(p >= 0, sales, 0.0) * p if policy == "A" else sales * p) * 1000)


def evaluate(df, policy, xv, ev, bv, costs, cf, cap_kg, netback, p, solver="highs", rate=C.RATE):
    """Exact operation for a fixed design: closed form for B, LP for A (battery)."""
    T, yrs = len(df), C.years_in(df)
    g0, d = df.g.to_numpy(), df.d.to_numpy()
    gen = np.column_stack([0.024 * cf[k] for k in NAMES])
    g = g0 + gen @ xv
    kg_per_gwh = 1e6 / C.H2_KWH_PER_KG
    amax = min(0.024 * ev, cap_kg / kg_per_gwh)
    if policy == "B":
        q = np.minimum(g, d); a = np.minimum(np.maximum(g - d, 0), amax); dis = np.zeros(T)
    elif bv < 1e-6:                          # no battery: each day is independent
        h2_value = netback * kg_per_gwh / 1000            # GBP per MWh of electricity turned into hydrogen
        a = np.where(p < h2_value, np.minimum(g, amax), np.minimum(np.maximum(g - d, 0), amax))
        q = np.where(p >= 0, np.minimum(g - a, d), 0.0); dis = np.zeros(T)
    else:
        lp = C.LP(); eta = np.sqrt(C.BAT_RTE)
        q = lp.var(T, ub=d, c=p); a = lp.var(T, ub=amax, c=netback * kg_per_gwh / 1000)
        ch = lp.var(T); dis = lp.var(T, c=p); soc = lp.var(T, ub=C.BAT_USABLE * bv / 1000)
        lp.rows(np.column_stack([q, a, ch]), np.ones((T, 3)), hi=g)
        lp.rows(np.column_stack([q, dis]), np.ones((T, 2)), hi=d)
        lp.row([soc[0], ch[0], dis[0]], [1, -eta, 1 / eta], lo=0, hi=0)
        lp.rows(np.column_stack([soc[1:], soc[:-1], ch[1:], dis[1:]]),
                np.column_stack([np.ones(T - 1), -np.ones(T - 1), np.full(T - 1, -eta), np.full(T - 1, 1 / eta)]), lo=0, hi=0)
        lp.ub[soc[-1]] = 0.0
        sol, _ = lp.solve(solver); q, a, dis = sol[q], sol[a], sol[dis]
    el_annual = C.crf(rate, C.EL_LIFE) * C.EL_PV_PER_MW + C.EL_FOM_PER_MW
    bat_annual = C.crf(rate, C.BAT_LIFE) * C.BAT_CAPEX_PER_MWH + C.BAT_FOM_PER_MWH
    revenue = (np.sum(p * (q + dis)) * 1000 + netback * kg_per_gwh * a.sum()) / yrs
    ref = reference_revenue(g0, d, p, policy) / yrs
    annual_cost = sum(costs[k]["annual"] * xv[i] for i, k in enumerate(NAMES)) + el_annual * ev + bat_annual * bv
    capex = sum(costs[k]["capex"] * xv[i] for i, k in enumerate(NAMES)) + C.EL_CAPEX_PER_MW * ev + C.BAT_CAPEX_PER_MWH * bv
    fixed_opex = annual_cost - (sum(C.crf(rate, costs[k]["life"]) * costs[k]["capex"] * xv[i] for i, k in enumerate(NAMES))
                                + C.crf(rate, C.EL_LIFE) * C.EL_PV_PER_MW * ev + C.crf(rate, C.BAT_LIFE) * C.BAT_CAPEX_PER_MWH * bv)
    cash = revenue - ref - fixed_opex                 # annual operating cash gain before capital recovery
    new_gen = (gen @ xv).sum() / yrs
    return dict(policy=policy, offshore_MW=xv[0], onshore_MW=xv[1], solar_MW=xv[2], electrolyser_MW=ev, battery_MWh=bv,
                capex_m=capex / 1e6, net_gain_m=(revenue - ref - annual_cost) / 1e6, cash_gain_m=cash / 1e6,
                payback_years=capex / cash if cash > 0 and capex > 0 else np.nan,
                h2_t_per_year=a.sum() * kg_per_gwh / 1000 / yrs, new_generation_GWh_per_year=new_gen,
                demand_coverage=float((q + dis).sum() / d.sum()), unused_GWh_per_year=float((g - q - a).clip(min=0).sum() / yrs) if bv < 1e-6 else np.nan,
                surplus_days_share=float((g > d).mean()))


def study(solver="highs"):
    OUT.mkdir(exist_ok=True)
    df = C.load_panel()
    costs = tech_costs(); cf = profiles(df, costs)
    info = {k: dict(capex_GBP2020_per_MW=round(v["capex"]), annual_cost_GBP2020_per_MW=round(v["annual"]), load_factor=v["lf"],
                    achieved_mean_cf=float(cf[k].mean()), lcoe_GBP2020_per_MWh=v["annual"] / (cf[k].mean() * 8766),
                    capture_price_all_days=float((cf[k] * df.price).sum() / cf[k].sum()),
                    realised_revenue_per_MWh_generated=float((cf[k] * df.price * (df.g <= df.d)).sum() / cf[k].sum()),
                    corr_with_existing_generation=float(np.corrcoef(cf[k], df.g)[0, 1])) for k, v in costs.items()}
    info["electrolyser_annual_GBP_per_MW"] = C.EL_ANNUAL_PER_MW; info["mean_real_price"] = float(df.price.mean())
    json.dump(info, open(OUT / "technology_inputs.json", "w"), indent=2)
    print(json.dumps(info, indent=1))

    rows = []
    budgets = [100e6, 250e6, 500e6, 1e9, 2e9, 4e9, 8e9, 16e9, None]
    for pol in "AB":
        r = solve(df, pol, None, costs, cf, fix_x=np.zeros(3), solver=solver); r["budget_m"] = 0.0; r["case"] = "Tier 1 (no new generation)"; rows.append(r)
        for bud in budgets:
            r = solve(df, pol, bud, costs, cf, solver=solver); r["budget_m"] = np.nan if bud is None else bud / 1e6; rows.append(r)
            print(pol, bud, {k: round(v, 2) for k, v in r.items() if isinstance(v, float)})
    pd.DataFrame(rows).to_csv(OUT / "budget_sweep.csv", index=False)

    # marginal benefit of each technology alone (electrolyser fixed at the Tier 1 optimum)
    t1 = {pol: solve(df, pol, None, costs, cf, fix_x=np.zeros(3), solver=solver) for pol in "AB"}
    grid = [0, 100, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000, 10000, 15000]
    curve = []
    for pol in "AB":
        for i, k in enumerate(NAMES):
            for mw in grid:
                xv = np.zeros(3); xv[i] = mw
                r = evaluate(df, pol, xv, t1[pol]["electrolyser_MW"], 0.0, costs, cf, C.H2_CAP_KG_DAY, C.H2_NETBACK, df.price.to_numpy())
                curve.append(dict(policy=pol, tech=k, MW=mw, net_gain_m=r["net_gain_m"], capex_m=r["capex_m"],
                                  unused_GWh_per_year=r["unused_GWh_per_year"], demand_coverage=r["demand_coverage"], surplus_days_share=r["surplus_days_share"]))
    curve = pd.DataFrame(curve); curve.to_csv(OUT / "marginal_curves.csv", index=False)

    # sensitivity at the GBP 500m budget
    sens = []
    def add(name, **kw):
        for pol in "AB":
            kw2 = dict(costs=costs, cf=cf); kw2.update(kw)
            r = solve(df, pol, 500e6, solver=solver, **kw2); r["case"] = name; sens.append(r)
    add("central")
    for case in ("low", "high"):
        cc = tech_costs(case); add(f"Arup {case} cost and load-factor case", costs=cc, cf=profiles(df, cc))
    for s in (0.5, 0.75, 1.25):
        add(f"electricity price x{s}", price=df.price.to_numpy() * s)
    calm = df[~df.index.year.isin([2021, 2022])]
    for pol in "AB":
        r = solve(calm, pol, 500e6, costs, profiles(calm, costs), solver=solver); r["case"] = "excluding 2021-2022"; sens.append(r)
    add("generation capex +30%", costs=tech_costs(capex_scale=1.3))
    add("discount rate 8%", costs=tech_costs(rate=0.08), rate=0.08)
    add("hydrogen offtake 100 t/day", cap_kg=100_000.0)
    add("hydrogen netback GBP 4/kg", netback=4.0)
    pd.DataFrame(sens).to_csv(OUT / "sensitivity.csv", index=False)
    figures(pd.DataFrame(rows), curve, pd.DataFrame(sens), info)
    return pd.DataFrame(rows), curve, pd.DataFrame(sens)


def figures(sweep, curve, sens, info):
    plt = C.style()
    col = {"offshore": C.BLUE, "onshore": C.AQUA, "solar": C.YELLOW, "electrolyser": C.VIOLET}
    # Fig 1: optimal portfolio by budget (capex split), policy A and B
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, pol in zip(axs, "AB"):
        s = sweep[(sweep.policy == pol) & sweep.budget_m.notna() & (sweep.budget_m > 0)]
        lab = [f"{b/1000:g}" for b in s.budget_m]
        bottom = np.zeros(len(s))
        for k in NAMES:
            v = (s[f"{k}_MW"] * info[k]["capex_GBP2020_per_MW"] / 1e9).to_numpy()
            ax.bar(lab, v, bottom=bottom, color=col[k], width=0.62, edgecolor=C.SURFACE, linewidth=2, label=LABEL[k]); bottom += v
        v = (s.electrolyser_MW * C.EL_CAPEX_PER_MW / 1e9).to_numpy()
        ax.bar(lab, v, bottom=bottom, color=col["electrolyser"], width=0.62, edgecolor=C.SURFACE, linewidth=2, label="Electrolyser")
        ax.set_title(f"Policy {pol}: capital allocated (GBP bn)"); ax.set_xlabel("capital budget (GBP bn)")
    fig.legend(*axs[0].get_legend_handles_labels(), ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.08), fontsize=9)
    fig.savefig(OUT / "fig2a_1_portfolio_by_budget.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # Fig 2: net gain and marginal return on budget
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    for pol, c in zip("AB", (C.BLUE, C.ORANGE)):
        s = sweep[(sweep.policy == pol)].assign(capex_m=lambda f: f.capex_m.round(0)).drop_duplicates("capex_m").sort_values("capex_m")
        axs[0].plot(s.capex_m / 1000, s.net_gain_m, color=c, marker="o", ms=5, label=f"Policy {pol}")
        dm = np.diff(s.net_gain_m) / np.diff(s.capex_m)
        axs[1].step(s.capex_m.to_numpy()[1:] / 1000, dm * 100, where="pre", color=c, label=f"Policy {pol}")
    axs[0].set_title("Annualised net gain vs capital spent (GBP m/yr)"); axs[0].set_xlabel("capital spent (GBP bn)")
    axs[1].set_title("Marginal net gain per extra GBP of capital (% per year)"); axs[1].set_xlabel("capital spent (GBP bn)")
    axs[1].axhline(0, color=C.AXIS, lw=1); axs[0].legend(); axs[1].set_xscale("log"); axs[0].set_xscale("log")
    fig.savefig(OUT / "fig2a_2_diminishing_returns.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # Fig 3: single-technology curves
    fig, axs = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, pol in zip(axs, "AB"):
        for k in NAMES:
            s = curve[(curve.policy == pol) & (curve.tech == k)]
            ax.plot(s.MW / 1000, s.net_gain_m - s.net_gain_m.iloc[0], color=col[k], marker="o", ms=4, label=LABEL[k])
        ax.axhline(0, color=C.AXIS, lw=1); ax.set_xlabel("new capacity of one technology (GW)"); ax.set_ylim(-300, 220); ax.set_xlim(0, 10.3)
        ax.set_title(f"Policy {pol}: net gain over Tier 1 (GBP m/yr)")
    axs[0].legend()
    fig.savefig(OUT / "fig2a_3_single_technology_curves.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # Fig 4: sensitivity of the GBP 500m portfolio
    s = sens[sens.policy == "A"].reset_index(drop=True)
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True, gridspec_kw=dict(width_ratios=[1.3, 1]))
    y = np.arange(len(s))[::-1]; left = np.zeros(len(s))
    for k in NAMES:
        axs[0].barh(y, s[f"{k}_MW"], left=left, color=col[k], height=0.6, edgecolor=C.SURFACE, linewidth=2, label=LABEL[k]); left += s[f"{k}_MW"].to_numpy()
    axs[0].set_yticks(y); axs[0].set_yticklabels(s.case); axs[0].set_title("Policy A, GBP 500m budget: new generation chosen (MW)")
    fig.legend(*axs[0].get_legend_handles_labels(), ncol=3, loc="lower center", bbox_to_anchor=(0.4, -0.07), fontsize=9); axs[0].grid(axis="x"); axs[0].grid(axis="y", visible=False)
    axs[1].barh(y, s.net_gain_m, color=C.BLUE, height=0.6); axs[1].set_title("Annualised net gain (GBP m/yr)")
    for yy, v in zip(y, s.net_gain_m):
        axs[1].text(v + 1, yy, f"{v:.0f}", va="center", fontsize=9, color=C.INK2)
    axs[1].grid(axis="x"); axs[1].grid(axis="y", visible=False)
    fig.savefig(OUT / "fig2a_4_sensitivity.png", dpi=160, bbox_inches="tight"); plt.close(fig)


def check(solver="highs"):
    df = C.load_panel()
    for pol, target in (("A", 12.681), ("B", 2.440)):
        r = solve(df, pol, None, fix_x=np.zeros(3), solver=solver)
        print(f"Tier 1 reproduction, policy {pol}: electrolyser {r['electrolyser_MW']:.2f} MW (v6: 23.42), battery {r['battery_MWh']:.2f} MWh (v6: 0), "
              f"net gain {r['net_gain_m']:.3f} (v6: {target})")
    # LP optimum equals exact evaluation
    r = solve(df, "A", 500e6, solver=solver); print("A @500m", {k: round(v, 3) for k, v in r.items() if isinstance(v, float)})


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); ap.add_argument("--solver", default="highs")
    a = ap.parse_args()
    check(a.solver) if a.check else study(a.solver)
