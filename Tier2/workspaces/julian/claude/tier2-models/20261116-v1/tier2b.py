"""Tier 2B - a strategy through time under limited information (MMCS Group 15).

Starting point (Tier 1): the client buys electrolysers and no battery, and sells hydrogen under a
DAILY offtake limit.  With no storage each day is solved on its own, so chronology and forecasts
have no value.  A steel hydrogen tank does not change that (see `tank_screen`): it never pays.

What does couple the days is the SHAPE OF THE OFFTAKE CONTRACT.  If the buyer accepts the same
volume as a total over a settlement window of W days (W = 1 is the Tier 1 contract), production can
move to the cheapest days of each window.  The operator then faces the lecturer's question every
morning: use today's electricity now, or keep quota for a cheaper day that may or may not come?

Model (GBP2020; electricity in GWh/day; hydrogen in tonnes):
    f_t  surplus ("free") electricity used        0 <= f_t <= free_t
    b_t  electricity diverted from market sales    cost p_t per MWh (policy A only)
    f_t + b_t <= 0.024 E                           electrolyser rating, E in MW
    sum over each window of (f_t + b_t)/0.0559 <= W * C     hydrogen quota, C = daily-equivalent cap
    maximise  netback * hydrogen - sum p_t b_t - annualised electrolyser cost
Design: E is chosen once with perfect foresight on 2020-2022 and then frozen.
Operation: 2023-2025 is replayed day by day with policies that only see the past.

Usage:  python tier2b.py            full study, writes results_2b/
        python tier2b.py --check    consistency checks
        python tier2b.py --solver xpress
"""
from __future__ import annotations
import argparse, json
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import common as C

OUT = C.ROOT / "results_2b"
GWH_PER_T = C.H2_KWH_PER_KG / 1000          # 0.0559 GWh of electricity per tonne of hydrogen
CAP_T = C.H2_CAP_KG_DAY / 1000              # 10 t/day
TRAIN_END, TEST_START = "2022-12-31", "2023-01-01"


def inputs(df, policy):
    """Free electricity (GWh/day) and the price of diverted electricity (GBP/MWh) for each policy."""
    p = df.price.to_numpy()
    free = (df.g - df.d).clip(lower=0).to_numpy()
    if policy == "A":                         # at negative prices the reference case sells nothing: all output is free
        free = np.where(p < 0, df.g.to_numpy(), free)
    return free, np.maximum(p, 0.0)


def blocks(T, W):
    return np.arange(T) // W


# ------------------------------------------------------------------ optimisation (design and perfect foresight)
def optimise(df, policy, W, E=None, cap_t=CAP_T, netback=C.H2_NETBACK, el_annual=C.EL_ANNUAL_PER_MW, solver="highs"):
    """LP over the whole frame.  E=None lets the model size the electrolyser.  Returns dict (GBP m/yr)."""
    free, p = inputs(df, policy)
    T, yrs = len(df), C.years_in(df)
    value = netback / GWH_PER_T                # GBP k per GWh turned into hydrogen (= GBP per MWh)
    lp = C.LP()
    e = lp.var(1, c=-el_annual * yrs / 1e3) if E is None else None
    f = lp.var(T, ub=free, c=value)
    b = lp.var(T, ub=np.inf if policy == "A" else 0.0, c=value - p)
    if e is not None:
        lp.rows(np.column_stack([f, b, np.full(T, e[0])]), np.column_stack([np.ones(T), np.ones(T), np.full(T, -0.024)]), hi=0.0)
    else:
        lp.rows(np.column_stack([f, b]), np.ones((T, 2)), hi=0.024 * E)
    blk = blocks(T, W)
    for k in np.unique(blk):
        idx = np.flatnonzero(blk == k)
        lp.row(list(f[idx]) + list(b[idx]), [1.0] * (2 * len(idx)), hi=len(idx) * cap_t * GWH_PER_T)
    sol, obj = lp.solve(solver)
    Ev = float(sol[e[0]]) if e is not None else float(E)
    fv, bv = sol[f], sol[b]
    return summarise(df, policy, Ev, fv, bv, netback, el_annual)


def summarise(df, policy, E, f, b, netback=C.H2_NETBACK, el_annual=C.EL_ANNUAL_PER_MW):
    _, p = inputs(df, policy)
    yrs = C.years_in(df)
    h2 = (f + b) / GWH_PER_T
    margin = (netback * h2.sum() - np.sum(p * b)) / 1e3 / yrs          # GBP m/yr before equipment cost
    return dict(policy=policy, E_MW=E, h2_t_per_year=h2.sum() / yrs, free_GWh_per_year=f.sum() / yrs, bought_GWh_per_year=b.sum() / yrs,
                avg_price_paid=float(np.sum(p * b) / max(b.sum(), 1e-12)), operating_margin_m=margin,
                net_gain_m=margin - el_annual * E / 1e6, utilisation=float((f + b).sum() / (0.024 * E * len(df))) if E > 0 else 0.0,
                f=f, b=b)


# ------------------------------------------------------------------ operation with limited information
def knapsack(free, p, K, quota_gwh, value):
    """Exact solution of one window when its inputs are taken as given: fill the cheapest electricity first.
    free, p: arrays for the days of the window; K = 0.024 E; returns (f, b)."""
    n = len(free)
    f_max = np.minimum(free, K); b_max = K - f_max
    cost = np.concatenate([np.zeros(n), p]); amount = np.concatenate([f_max, b_max])
    order = np.argsort(cost, kind="stable")
    take = np.zeros(2 * n); left = quota_gwh
    for i in order:
        if cost[i] >= value or left <= 1e-12:
            break
        take[i] = min(amount[i], left); left -= take[i]
    return take[:n], take[n:]


class Forecaster:
    """Direct multi-step ridge forecasts of price and net balance (g - d), re-estimated at the start of
    each year on all earlier data.  Features: the last 7 days of both series, their 28-day means, and the
    target day's weekday and season.  Only information available on the morning of the decision is used."""
    def __init__(self, df, horizons, policy):
        self.df, self.H = df, horizons
        self.p = df.price.to_numpy(); self.n = (df.g - df.d).to_numpy(); self.g = df.g.to_numpy()
        self.dow = df.index.dayofweek.to_numpy(); self.doy = df.index.dayofyear.to_numpy()
        self.models = {}; self.policy = policy

    def _x(self, t, h):
        lag = lambda s: s[t - 6:t + 1]
        tgt = t + h
        dow = np.eye(7)[self.dow[tgt]] if tgt < len(self.p) else np.eye(7)[(self.dow[t] + h) % 7]
        doy = self.doy[tgt] if tgt < len(self.p) else (self.doy[t] + h)
        return np.concatenate([lag(self.p), lag(self.n), [self.p[t - 27:t + 1].mean(), self.n[t - 27:t + 1].mean()],
                               dow, [np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)]])

    def _fit(self, year):
        end = int(np.searchsorted(self.df.index.year, year))            # first index of `year`
        for h in range(1, self.H + 1):
            ts = np.arange(27, end - h)
            X = np.array([self._x(t, h) for t in ts])
            for name, y in (("p", self.p), ("n", self.n)):
                self.models[(year, h, name)] = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(X, y[ts + h])

    def predict(self, t, n_ahead):
        """Forecasts for days t+1 .. t+n_ahead made on day t.  Returns (free_hat, price_hat)."""
        year = self.df.index.year[t]
        if (year, 1, "p") not in self.models:
            self._fit(year)
        ph, nh = np.empty(n_ahead), np.empty(n_ahead)
        for h in range(1, n_ahead + 1):
            x = self._x(t, h)[None]
            ph[h - 1] = self.models[(year, h, "p")].predict(x)[0]; nh[h - 1] = self.models[(year, h, "n")].predict(x)[0]
        return np.maximum(nh, 0.0), np.maximum(ph, 0.0)

    def naive(self, t, n_ahead):
        """No model: next days look like the last four weeks on average."""
        free_hist = np.maximum(self.n[t - 27:t + 1], 0.0)
        return np.full(n_ahead, free_hist.mean()), np.full(n_ahead, max(self.p[t - 27:t + 1].mean(), 0.0))


def simulate(df_all, policy, W, E, rule, start=TEST_START, cap_t=CAP_T, netback=C.H2_NETBACK, fc=None, quantile_window=56):
    """Replay the test period one day at a time.  `rule` in {'pace','greedy','threshold','mpc_naive','mpc_ridge','perfect'}."""
    free_all, p_all = inputs(df_all, policy)
    if policy == "B":
        p_all = np.full(len(p_all), np.inf)                    # supply first: never divert sales
    t0 = int(np.searchsorted(df_all.index, pd.Timestamp(start)))
    T = len(df_all) - t0
    blk = blocks(T, W)
    K, value = 0.024 * E, netback / GWH_PER_T
    f = np.zeros(T); b = np.zeros(T)
    for k in np.unique(blk):
        days = np.flatnonzero(blk == k); left = len(days) * cap_t * GWH_PER_T
        if rule == "perfect":
            f[days], b[days] = knapsack(free_all[t0 + days], p_all[t0 + days], K, left, value); continue
        for j, i in enumerate(days):
            t = t0 + i; n_left = len(days) - j
            fr, pr = min(free_all[t], K), p_all[t]
            if rule == "pace":                                 # ignore the flexibility: one day's quota per day
                budget = min(left, cap_t * GWH_PER_T)
                ft = min(fr, budget); bt = min(K - ft, budget - ft) if pr < value else 0.0
            elif rule == "greedy":                             # produce whenever it pays until the quota is gone
                ft = min(fr, left); bt = min(K - ft, left - ft) if pr < value else 0.0
            elif rule == "threshold":                          # buy only if today is among the cheapest share of days needed
                ft = min(fr, left)
                need = (left - ft) / max(n_left * K, 1e-12)    # share of remaining capacity the quota still requires
                hist = p_all[t - quantile_window:t]
                theta = np.quantile(hist, min(1.0, need)) if need > 0 else -1.0
                if n_left == 1:
                    theta = np.inf
                bt = min(K - ft, left - ft) if (pr < value and pr <= theta) else 0.0
            else:                                              # rolling plan: today is known, the rest is forecast
                if n_left > 1:
                    fh, ph = (fc.naive if rule == "mpc_naive" else fc.predict)(t, n_left - 1)
                    if policy == "B": ph = np.full(n_left - 1, np.inf)
                else:
                    fh, ph = np.empty(0), np.empty(0)
                fplan, bplan = knapsack(np.concatenate([[free_all[t]], fh]), np.concatenate([[pr], ph]), K, left, value)
                ft, bt = fplan[0], bplan[0]
            f[i], b[i] = ft, bt; left -= ft + bt
    b = np.where(np.isfinite(b), b, 0.0)
    return summarise(df_all.iloc[t0:], policy, E, f, b, netback)


# ------------------------------------------------------------------ studies
def tank_screen(df, solver="highs"):
    """Would a hydrogen buffer tank create useful coupling?  Co-optimise electrolyser and tank size."""
    rows = []
    for policy in "AB":
        free, p = inputs(df, policy); T, yrs = len(df), C.years_in(df)
        for label, scale in (("DEA steel tank (researched cost)", 1.0), ("tank at 25% of cost", 0.25), ("tank at 5% of cost (cavern-like)", 0.05), ("free storage", 0.0)):
            lp = C.LP()
            e = lp.var(1, c=-C.EL_ANNUAL_PER_MW * yrs / 1e3); s = lp.var(1, c=-C.TANK_ANNUAL_PER_KG * scale * yrs)   # s in tonnes
            prod = lp.var(T, c=C.H2_NETBACK); inj = lp.var(T, c=-C.H2_NETBACK); w = lp.var(T, c=C.H2_NETBACK); inv = lp.var(T)
            f = lp.var(T, ub=free); b = lp.var(T, ub=np.inf if policy == "A" else 0.0, c=-p)
            one = np.ones(T)
            lp.rows(np.column_stack([prod, inj, f, b]), np.column_stack([one * GWH_PER_T, one * C.TANK_COMPRESSION_KWH_PER_KG / 1000, -one, -one]), lo=0, hi=0)
            lp.rows(np.column_stack([prod, np.full(T, e[0])]), np.column_stack([one * GWH_PER_T, -0.024 * one]), hi=0)
            lp.rows(np.column_stack([inj, prod]), np.column_stack([one, -one]), hi=0)
            lp.rows(np.column_stack([prod, inj, w]), np.column_stack([one, -one, one]), lo=0, hi=CAP_T)
            lp.row([inv[0], inj[0], w[0]], [1, -1, 1], lo=0, hi=0)
            lp.rows(np.column_stack([inv[1:], inv[:-1], inj[1:], w[1:]]), np.column_stack([one[1:], -one[1:], -one[1:], one[1:]]), lo=0, hi=0)
            lp.rows(np.column_stack([inv, np.full(T, s[0])]), np.column_stack([one, -one]), hi=0)
            sol, obj = lp.solve(solver)
            rows.append(dict(policy=policy, storage_cost_case=label, E_MW=sol[e[0]], tank_t=sol[s[0]], net_gain_m=obj / yrs / 1e3))
    return pd.DataFrame(rows)


def chronology(df, solver="highs"):
    """Follow the Tier 1 design (daily contract) through 2020-2025: cash by month, payback date, idle spells."""
    rows, monthly, out = [], {}, {}
    for policy in "AB":
        r = optimise(df, policy, 1, solver=solver); E = r["E_MW"]
        _, p = inputs(df, policy)
        h2 = (r["f"] + r["b"]) / GWH_PER_T
        cash = C.H2_NETBACK * h2 * 1000 - p * r["b"] * 1000 - C.EL_FOM_PER_MW * E / 365.25          # GBP per day
        capex = C.EL_CAPEX_PER_MW * E
        cum = np.cumsum(cash) - capex
        paid = np.flatnonzero(cum >= 0)
        monthly[policy] = pd.Series(cash, index=df.index).resample("MS").sum() / 1e6
        out[policy] = pd.Series(cum / 1e6, index=df.index)
        idle = h2 < 0.05 * CAP_T
        grp = (idle != np.roll(idle, 1)).cumsum(); grp[0] = 0
        spells = pd.Series(idle).groupby(grp).agg(["first", "size"]).query("first")["size"]
        yearly = pd.Series(cash, index=df.index).groupby(df.index.year).sum() / 1e6 - C.crf(C.RATE, C.EL_LIFE) * C.EL_PV_PER_MW * E / 1e6
        rows.append(dict(policy=policy, E_MW=E, capex_m=capex / 1e6, operating_cash_m_per_year=cash.sum() / C.years_in(df) / 1e6,
                         payback_date=str(df.index[paid[0]].date()) if len(paid) else "not within 2020-2025",
                         simple_payback_years=capex / (cash.sum() / C.years_in(df)), share_of_days_producing=float((~idle).mean()),
                         longest_idle_spell_days=int(spells.max()) if len(spells) else 0, idle_spells_over_7_days=int((spells > 7).sum()),
                         **{f"net_gain_{y}_m": float(v) for y, v in yearly.items()}))
    return pd.DataFrame(rows), pd.DataFrame(monthly), pd.DataFrame(out)


def forecast_skill(df, fc, max_h=7):
    t0 = int(np.searchsorted(df.index, pd.Timestamp(TEST_START)))
    rows = []
    err = {(m, v, h): [] for m in ("ridge", "naive") for v in ("price", "balance") for h in range(1, max_h + 1)}
    for t in range(t0, len(df) - max_h):
        for m, fn in (("ridge", fc.predict), ("naive", fc.naive)):
            _, ph = fn(t, max_h)
            for h in range(1, max_h + 1):
                err[(m, "price", h)].append(abs(ph[h - 1] - max(fc.p[t + h], 0)))
        year = df.index.year[t]
        for h in range(1, max_h + 1):
            nh = fc.models[(year, h, "n")].predict(fc._x(t, h)[None])[0]
            err[("ridge", "balance", h)].append(abs(nh - fc.n[t + h])); err[("naive", "balance", h)].append(abs(fc.n[t - 27:t + 1].mean() - fc.n[t + h]))
    for (m, v, h), e in err.items():
        rows.append(dict(method=m, variable=v, horizon_days=h, MAE=float(np.mean(e))))
    return pd.DataFrame(rows)


def study(solver="highs"):
    OUT.mkdir(exist_ok=True)
    df = C.load_panel(); train = df.loc[:TRAIN_END]; test = df.loc[TEST_START:]
    drop = lambda r: {k: v for k, v in r.items() if k not in ("f", "b")}

    chrono, monthly, cum = chronology(df, solver); chrono.to_csv(OUT / "chronology_tier1_design.csv", index=False)
    monthly.to_csv(OUT / "monthly_operating_cash.csv"); print(chrono.round(2).T.to_string())
    tank = tank_screen(df, solver); tank.to_csv(OUT / "tank_screen.csv", index=False); print(tank.round(3).to_string())

    # 1. value of contract flexibility with perfect foresight over the whole history
    win = []
    for policy in "AB":
        for W in (1, 2, 3, 7, 14, 28, 91, 365):
            r = drop(optimise(df, policy, W, solver=solver)); r["window_days"] = W; win.append(r)
    win = pd.DataFrame(win); win.to_csv(OUT / "contract_window_value.csv", index=False)
    print(win[["policy", "window_days", "E_MW", "h2_t_per_year", "free_GWh_per_year", "bought_GWh_per_year", "avg_price_paid", "net_gain_m", "utilisation"]].round(2).to_string())

    # 2. design on 2020-2022, operate 2023-2025 with limited information
    rules = ["pace", "greedy", "threshold", "mpc_naive", "mpc_ridge", "perfect"]
    ops, keep = [], {}
    for policy in "AB":
        e1 = optimise(train, policy, 1, solver=solver)["E_MW"]
        base = drop(simulate(df, policy, 1, e1, "perfect")); base.update(window_days=1, rule="Tier 1 daily contract", design="2020-22"); ops.append(base)
        for W in (7, 28):
            e = optimise(train, policy, W, solver=solver)["E_MW"]
            fc = Forecaster(df, W - 1, policy)
            for rule in rules:
                r = simulate(df, policy, W, e, rule, fc=fc); keep[(policy, W, rule)] = r
                r2 = drop(r); r2.update(window_days=W, rule=rule, design="2020-22"); ops.append(r2)
            hind = drop(optimise(test, policy, W, solver=solver)); hind.update(window_days=W, rule="perfect + hindsight design", design="2023-25"); ops.append(hind)
    ops = pd.DataFrame(ops)
    for pol in "AB":
        base = ops[(ops.policy == pol) & (ops.window_days == 1)].net_gain_m.iloc[0]
        ops.loc[ops.policy == pol, "gain_vs_daily_contract_m"] = ops.loc[ops.policy == pol, "net_gain_m"] - base
    ops.to_csv(OUT / "operating_policies.csv", index=False)
    print(ops[["policy", "window_days", "rule", "E_MW", "h2_t_per_year", "bought_GWh_per_year", "avg_price_paid", "net_gain_m", "gain_vs_daily_contract_m"]].round(3).to_string())

    fc7 = Forecaster(df, 7, "A"); skill = forecast_skill(df, fc7); skill.to_csv(OUT / "forecast_skill.csv", index=False)
    print(skill.pivot_table(index="horizon_days", columns=["variable", "method"], values="MAE").round(2).to_string())

    # 3. what changes the answer (policy A, 7-day window, rolling plan with ridge forecasts)
    sens = []
    def case(name, **kw):
        nb = kw.get("netback", C.H2_NETBACK); cap = kw.get("cap_t", CAP_T); ela = kw.get("el_annual", C.EL_ANNUAL_PER_MW)
        dfx = kw.get("frame", df); tr = dfx.loc[:TRAIN_END]
        e1 = optimise(tr, "A", 1, cap_t=cap, netback=nb, el_annual=ela, solver=solver)["E_MW"]
        e7 = optimise(tr, "A", 7, cap_t=cap, netback=nb, el_annual=ela, solver=solver)["E_MW"]
        fc = Forecaster(dfx, 6, "A")
        out = dict(case=name, E_daily_MW=e1, E_weekly_MW=e7)
        for label, W, e, rule in (("daily_contract", 1, e1, "perfect"), ("weekly_greedy", 7, e7, "greedy"), ("weekly_mpc_ridge", 7, e7, "mpc_ridge"), ("weekly_perfect", 7, e7, "perfect")):
            r = simulate(dfx, "A", W, e, rule, cap_t=cap, netback=nb, fc=fc)
            out[label + "_m"] = r["operating_margin_m"] - ela * e / 1e6
        sens.append(out)
    case("central")
    case("hydrogen netback GBP 6/kg", netback=6.0); case("hydrogen netback GBP 10/kg", netback=10.0)
    case("electrolyser cost -30%", el_annual=C.EL_ANNUAL_PER_MW * 0.7); case("electrolyser cost +30%", el_annual=C.EL_ANNUAL_PER_MW * 1.3)
    case("offtake 100 t/day", cap_t=100.0)
    for s in (0.5, 1.5):
        d2 = df.copy(); d2["price"] = d2.price * s; case(f"electricity price x{s}", frame=d2)
    d2 = df.copy(); m = d2.price.rolling(28, min_periods=1).mean(); d2["price"] = (m + 2 * (d2.price - m)); case("price volatility x2 around 28-day mean", frame=d2)
    sens = pd.DataFrame(sens); sens.to_csv(OUT / "sensitivity.csv", index=False); print(sens.round(3).to_string())
    figures(df, win, ops, skill, sens, keep, tank, monthly, cum)


def figures(df, win, ops, skill, sens, keep, tank, monthly, cum):
    plt = C.style()
    # Fig 0: the Tier 1 design through time
    fig, axs = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    for pol, c in zip('AB', (C.BLUE, C.ORANGE)):
        axs[0].plot(monthly.index, monthly[pol], color=c, label=f'Policy {pol}'); axs[1].plot(cum.index, cum[pol], color=c, label=f'Policy {pol}')
    axs[0].set_title('Monthly operating cash from the Tier 1 electrolyser (GBP2020 m)'); axs[0].axhline(0, color=C.AXIS, lw=1); axs[0].legend()
    axs[1].set_title('Cumulative cash after the initial investment (GBP2020 m)'); axs[1].axhline(0, color=C.INK2, lw=1, ls='--')
    fig.savefig(OUT / 'fig2b_0_tier1_through_time.png', dpi=160, bbox_inches='tight'); plt.close(fig)
    # Fig 1: value of the contract window
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    for pol, c in zip("AB", (C.BLUE, C.ORANGE)):
        s = win[win.policy == pol]
        axs[0].plot(s.window_days, s.net_gain_m, color=c, marker="o", ms=5, label=f"Policy {pol}")
        axs[1].plot(s.window_days, s.E_MW, color=c, marker="o", ms=5, label=f"Policy {pol}")
    for ax in axs:
        ax.set_xscale("log"); ax.set_xticks([1, 2, 3, 7, 14, 28, 91, 365]); ax.set_xticklabels(["1", "2", "3", "7", "14", "28", "91", "365"]); ax.minorticks_off()
        ax.set_xlabel("offtake settlement window (days)"); ax.set_ylim(0)
    axs[0].set_title("Annualised net gain with perfect foresight (GBP m/yr)"); axs[1].set_title("Electrolyser capacity chosen (MW)"); axs[0].legend()
    fig.savefig(OUT / "fig2b_1_contract_window.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # Fig 2: operating rules, test period
    names = {"Tier 1 daily contract": "Daily contract (Tier 1)", "pace": "Weekly, paced", "greedy": "Weekly, greedy", "threshold": "Weekly, price threshold",
             "mpc_naive": "Weekly, rolling plan (naive)", "mpc_ridge": "Weekly, rolling plan (ridge)", "perfect": "Weekly, perfect foresight"}
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
    for ax, pol in zip(axs, "AB"):
        s = ops[(ops.policy == pol) & ((ops.window_days == 7) | (ops.window_days == 1)) & ops.rule.isin(names)]
        s = s.set_index("rule").loc[[r for r in names if r in s.rule.values]]
        y = np.arange(len(s))[::-1]
        colors = [C.MUTED if r == "Tier 1 daily contract" else (C.INK2 if r == "perfect" else C.BLUE) for r in s.index]
        ax.barh(y, s.net_gain_m, color=colors, height=0.62)
        for yy, v in zip(y, s.net_gain_m):
            ax.text(max(v, 0) + s.net_gain_m.max() * 0.01, yy, f"{v:.2f}", va="center", fontsize=9, color=C.INK2)
        ax.set_yticks(y); ax.set_yticklabels([names[r] for r in s.index]); ax.grid(axis="x"); ax.grid(axis="y", visible=False)
        ax.set_xlim(0, s.net_gain_m.max() * 1.12); ax.set_title(f"Policy {pol}: net gain 2023-2025 (GBP m/yr)")
    fig.tight_layout(); fig.savefig(OUT / "fig2b_2_operating_rules.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # Fig 3: forecast skill
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, v, ttl in zip(axs, ("price", "balance"), ("Price forecast error (MAE, GBP/MWh)", "Supply-demand balance error (MAE, GWh/day)")):
        for m, c in (("naive", C.MUTED), ("ridge", C.BLUE)):
            s = skill[(skill.variable == v) & (skill.method == m)]
            ax.plot(s.horizon_days, s.MAE, color=c, marker="o", ms=4, label={"naive": "28-day average", "ridge": "Ridge regression"}[m])
        ax.set_title(ttl); ax.set_xlabel("days ahead"); ax.set_ylim(0)
    axs[0].legend()
    fig.savefig(OUT / "fig2b_3_forecast_skill.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # Fig 4: a stress window - what each rule does (policy A, weekly)
    test = df.loc[TEST_START:]
    roll = test.price.rolling(28).std(); end = roll.idxmax(); sl = slice(test.index.get_loc(end) - 41, test.index.get_loc(end) + 1)
    idx = test.index[sl]
    fig, axs = plt.subplots(3, 1, figsize=(10, 6.6), sharex=True, gridspec_kw=dict(height_ratios=[1.1, 1, 1]))
    axs[0].plot(idx, test.price.iloc[sl], color=C.ORANGE); axs[0].axhline(C.H2_NETBACK / GWH_PER_T, color=C.INK2, lw=1, ls="--")
    axs[0].text(idx[0], C.H2_NETBACK / GWH_PER_T + 4, "hydrogen break-even", fontsize=9, color=C.INK2); axs[0].set_title("Electricity price (GBP2020/MWh), most volatile six weeks of 2023-2025")
    for ax, rule, ttl in ((axs[1], "perfect", "Hydrogen produced, perfect foresight (t/day)"), (axs[2], "mpc_ridge", "Hydrogen produced, rolling plan with ridge forecasts (t/day)")):
        r = keep[("A", 7, rule)]
        ax.bar(idx, (r["f"][sl] + r["b"][sl]) / GWH_PER_T, color=C.BLUE, width=0.8); ax.set_title(ttl)
        ax.axhline(CAP_T, color=C.AXIS, lw=1, ls="--")
    fig.autofmt_xdate(); fig.savefig(OUT / "fig2b_4_stress_window.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    # Fig 5: sensitivity - does a weekly contract beat the daily one?
    fig, ax = plt.subplots(figsize=(10, 4.4))
    y = np.arange(len(sens))[::-1]; h = 0.36
    for off, col, lab, c in ((h / 2, "weekly_mpc_ridge_m", "Weekly contract, rolling plan (what an operator can achieve)", C.BLUE),
                             (-h / 2, "weekly_perfect_m", "Weekly contract, perfect foresight (upper bound)", C.INK2)):
        ax.barh(y + off, sens[col] - sens.daily_contract_m, height=h * 0.9, color=c, label=lab)
    ax.set_yticks(y); ax.set_yticklabels(sens.case); ax.grid(axis="x"); ax.grid(axis="y", visible=False); ax.axvline(0, color=C.INK2, lw=1)
    ax.set_title("Policy A: gain from a weekly contract over the daily contract, 2023-2025 (GBP m/yr)")
    fig.legend(*ax.get_legend_handles_labels(), loc="lower center", bbox_to_anchor=(0.5, -0.1), ncol=1, fontsize=9)
    fig.savefig(OUT / "fig2b_5_sensitivity.png", dpi=160, bbox_inches="tight"); plt.close(fig)


def check(solver="highs"):
    df = C.load_panel()
    for pol, target in (("A", 12.681), ("B", 2.440)):
        r = optimise(df, pol, 1, solver=solver)
        print(f"W=1 reproduces Tier 1, policy {pol}: E {r['E_MW']:.2f} MW, net gain {r['net_gain_m']:.3f} (v6 with integer modules: {target})")
    for pol in "AB":                       # the per-window greedy fill must equal the LP for a fixed design
        lp = optimise(df, pol, 7, E=40.0, solver=solver); sim = simulate(df, pol, 7, 40.0, "perfect", start="2020-01-01")
        print(f"policy {pol}: LP {lp['net_gain_m']:.6f} vs window fill {sim['net_gain_m']:.6f}")
        g = simulate(df, pol, 7, 40.0, "greedy", start="2020-01-01"); m = simulate(df, pol, 7, 40.0, "pace", start="2020-01-01")
        assert m["net_gain_m"] <= lp["net_gain_m"] + 1e-6 and g["net_gain_m"] <= lp["net_gain_m"] + 1e-6
    print("causal rules never beat perfect foresight: ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); ap.add_argument("--solver", default="highs")
    a = ap.parse_args()
    check(a.solver) if a.check else study(a.solver)
