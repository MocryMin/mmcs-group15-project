"""One 100 MW / 400 MWh battery block beside a site-scale electrolyser, on the group's half-hour conventions.

The block is the one fixed in the group's Tier 2B handoff: 240 MWh usable, 50 MWh per half-hour on the AC side in
either direction, 90% round trip split evenly, opening and closing stock zero, and an annual budget of internal
discharge equal to 400 MWh per calendar day.

The battery charges only from generation that is left unused once direct sales and the electrolyser have taken
theirs, and sells only into demand that direct sales leave unserved. With a 30-55 MW electrolyser these two
quantities are thousands of MWh per half-hour whenever they are positive, so the battery and the electrolyser do not
compete and the electrolyser schedule is held fixed.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, eye, hstack, vstack

from site_model import Site, flexible_dispatch, reference

P_STEP = 50.0          # MWh per half-hour, AC side
USABLE = 240.0         # MWh of internal stock above the 20% floor
ETA = 0.9 ** 0.5
BUDGET_PER_DAY = 400.0 # MWh of internal discharge per calendar day, pooled over each year
CAPITAL = 38_689_824.68284418
FIXED_OM = 967_245.6170711045
ANNUAL = 4_695_346.554053117
INITIAL_FILL_ANNUAL = 634.7198361980263


def opportunities(site: Site, policy: str, disp: dict | None):
    """Unused generation and unserved demand per half-hour once the electrolyser schedule is in place (flat arrays)."""
    ref = reference(site, policy)
    free_used = 0.0 if disp is None else disp["free"]
    paid = 0.0 if disp is None else disp["paid"]
    unused = np.maximum(ref["free"] - free_used, 0.0).ravel()
    unmet = np.maximum(site.D - (ref["q"] - paid), 0.0).ravel()
    return unused, unmet, site.p.ravel()


def year_index(site: Site) -> np.ndarray:
    return np.repeat(site.year, site.G.shape[1])


def simulate(site: Site, policy: str, unused, unmet, price, charge_target=None, sell_floor=0.0):
    """Rule-based operation, half-hour by half-hour, using only the current half-hour's values.

    Discharge into unserved demand as fast as power, stock and the unserved amount allow: under A only when the
    price is above `sell_floor`, under B always. Otherwise charge from unused generation. The yearly discharge
    budget is respected by never holding more stock than the budget left, and nothing is charged on the last day.
    `charge_target`, if given, caps the stock that charging may reach in each half-hour (used to replay a plan).
    """
    T = len(price)
    yr = year_index(site)
    budget = {int(y): BUDGET_PER_DAY * int((site.year == y).sum()) for y in np.unique(site.year)}
    s = 0.0
    c = np.zeros(T); r = np.zeros(T); stock = np.zeros(T)
    last_day_start = T - 48
    for t in range(T):
        y = int(yr[t])
        can_sell = unmet[t] > 0 and (policy == "B" or price[t] > sell_floor)
        if can_sell and s > 0:
            out = min(P_STEP, ETA * s, unmet[t], ETA * budget[y])
            r[t] = out; s -= out / ETA; budget[y] -= out / ETA
        elif unused[t] > 0 and t < last_day_start and not (policy == "B" and unmet[t] > 0):
            top = USABLE if charge_target is None else min(USABLE, charge_target[t])
            top = min(top, budget[y])
            room = max(top - s, 0.0)
            inp = min(P_STEP, unused[t], room / ETA)
            c[t] = inp; s += inp * ETA
        stock[t] = s
    return dict(c=c, r=r, s=stock, gross=float((price * r).sum()) / site.years_equiv, end_stock=s)


def perfect_foresight_A(site: Site, unused, unmet, price, sold=None):
    """Linear programme for the battery alone with the whole record known.

    Charging from unused generation is free. If `sold` is given (policy A), the battery may also charge from
    generation that would otherwise be sold, at the price forgone; this is the arbitrage that economic dispatch
    allows in the report's model, where direct sales are a free variable. Without `sold` the battery charges from
    unused generation only, which is all that supply priority permits; in that form the result is an upper bound
    for policy B, because it lets stored energy be held back during a shortfall.
    """
    T = len(price)
    yr = year_index(site)
    years = np.unique(site.year)
    paid = sold is not None
    cf_max = np.minimum(P_STEP, unused)
    cp_max = np.minimum(P_STEP, sold) if paid else np.zeros(T)
    rmax = np.minimum(P_STEP, unmet)
    # variables: cf (T), cp (T), r (T), s (T)
    I = eye(T, format="csr")
    Z = coo_matrix((T, T)).tocsr()
    sub = coo_matrix((np.ones(T - 1), (np.arange(1, T), np.arange(T - 1))), shape=(T, T)).tocsr()
    A_eq = hstack([-ETA * I, -ETA * I, I / ETA, I - sub], format="csr")     # s_t - s_{t-1} - eta (cf+cp) + r/eta = 0
    b_eq = np.zeros(T)
    rows = [hstack([I, I, Z, Z], format="csr")]                               # cf + cp <= power step
    b_ub = [np.full(T, P_STEP)]
    for y in years:
        m = (yr == y).astype(float)
        rows.append(hstack([coo_matrix((1, 2 * T)), coo_matrix(m[None, :] / ETA), coo_matrix((1, T))]).tocsr())
        b_ub.append(np.array([BUDGET_PER_DAY * int((site.year == y).sum())], float))
    A_ub = vstack(rows, format="csr")
    b_ub = np.concatenate(b_ub)
    cost = np.r_[np.zeros(T), np.maximum(price, 0.0), -price, np.zeros(T)]
    smax = np.full(T, USABLE); smax[-1] = 0.0
    bounds = np.c_[np.zeros(4 * T), np.r_[cf_max, cp_max, rmax, smax]]
    res = linprog(cost, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    if res.status != 0:
        raise RuntimeError(res.message)
    cf, cp, r, s = res.x[:T], res.x[T:2 * T], res.x[2 * T:3 * T], res.x[3 * T:]
    gross = float((price * r).sum() - (np.maximum(price, 0.0) * cp).sum()) / site.years_equiv
    budgets = np.array([BUDGET_PER_DAY * int((site.year == y).sum()) for y in years], float)
    used = np.array([r[yr == y].sum() / ETA for y in years])
    return dict(c=cf + cp, c_free=cf, c_paid=cp, r=r, s=s, gross=gross, status=res.message, budget_used=used / budgets)


def perfect_foresight_B(site: Site, unused, unmet, price, grid=1.0):
    """Best charging plan under supply priority with the whole record known.

    Under B stored energy must go to the next shortfall at once, so the only decision is how full to be when each
    shortfall begins. The record is cut into stretches of shortfall separated by stretches without one; a dynamic
    programme over a stock grid chooses the stock at the start of every shortfall stretch. The plan is then
    replayed with the exact rule-based simulator, and that replay is what is reported.
    """
    T = len(price)
    short = unmet > 0
    # stretches: maximal runs of equal `short`
    edges = np.flatnonzero(np.diff(short.astype(int)) != 0) + 1
    starts = np.r_[0, edges]; ends = np.r_[edges, T]
    levels = np.arange(0.0, USABLE + 1e-9, grid)
    nL = len(levels)
    stretches = [(a, b, bool(short[a])) for a, b in zip(starts, ends)]
    # backward pass
    F = np.zeros(nL)                                   # value-to-go as a function of stock at the stretch start
    F[levels > 1e-9] = -1e18                           # stock must be zero at the end of the record
    policy_tables = [None] * len(stretches)
    last_day_start = T - 48
    for k in range(len(stretches) - 1, -1, -1):
        a, b, is_short = stretches[k]
        if is_short:
            s = levels.copy(); rev = np.zeros(nL)
            for t in range(a, b):
                out = np.minimum(np.minimum(P_STEP, ETA * s), unmet[t])
                rev += price[t] * out; s = s - out / ETA
                if not (s > 1e-9).any():
                    break
            # leftover stock s is generally off-grid: interpolate the value-to-go (linear)
            F = rev + np.interp(s, levels, np.where(F < -1e17, -1e18, F))
            policy_tables[k] = None
        else:
            # how much stock can be added in this stretch
            room_in = np.minimum(P_STEP, unused[a:min(b, last_day_start)]).sum() * ETA if a < last_day_start else 0.0
            reach = np.minimum(levels + room_in, USABLE)
            # best target level >= current level and <= reach
            best = np.full(nL, -1e18); arg = np.arange(nL)
            # suffix maximum of F over targets, limited by reach: evaluate with a running maximum
            run_max = np.maximum.accumulate(F[::-1])[::-1]              # max over targets >= i (unbounded above)
            idx_reach = np.minimum(np.floor(reach / grid + 1e-9).astype(int), nL - 1)
            # prefix structure: max over i..idx_reach[i]; do it directly (nL is small)
            for i in range(nL):
                j = i + int(np.argmax(F[i:idx_reach[i] + 1]))
                best[i] = F[j]; arg[i] = j
            policy_tables[k] = arg
            F = best
    # forward pass: targets per half-hour
    target = np.full(T, 0.0)
    s_idx = 0
    s_val = 0.0
    for k, (a, b, is_short) in enumerate(stretches):
        if is_short:
            s = s_val
            for t in range(a, b):
                out = min(P_STEP, ETA * s, unmet[t]); s -= out / ETA
            s_val = s
        else:
            i = min(int(np.floor(s_val / grid + 1e-9)), nL - 1)
            j = policy_tables[k][i]
            tgt = max(levels[j], s_val) if j > i else s_val
            target[a:b] = tgt
            room_in = np.minimum(P_STEP, unused[a:min(b, last_day_start)]).sum() * ETA if a < last_day_start else 0.0
            s_val = min(tgt, s_val + room_in)
    sim = simulate(site, "B", unused, unmet, price, charge_target=target)
    sim["dp_value"] = float(F[0]) / site.years_equiv
    sim["stretches"] = len(stretches)
    return sim


def summary(site: Site, run: dict, label: str, policy: str) -> dict:
    yr = year_index(site)
    price = site.p.ravel()
    gross = run["gross"]
    cp = run.get("c_paid", np.zeros_like(price))
    cash = price * run["r"] - np.maximum(price, 0.0) * cp
    by_year = {int(y): float(cash[yr == y].sum()) - ANNUAL for y in np.unique(site.year)}
    disc = {int(y): float(run["r"][yr == y].sum() / ETA) / (BUDGET_PER_DAY * int((site.year == y).sum())) for y in np.unique(site.year)}
    row = dict(label=label, policy=policy, gross_m=gross / 1e6, annual_cost_m=ANNUAL / 1e6, net_m=(gross - ANNUAL) / 1e6,
               payback_years=(CAPITAL + INITIAL_FILL_ANNUAL / 0.09634228760924432) / (gross - FIXED_OM) if gross > FIXED_OM else np.nan,
               sold_gwh=float(run["r"].sum()) / 1000 / site.years_equiv, charged_gwh=float(run["c"].sum()) / 1000 / site.years_equiv,
               charged_from_unused_gwh=float((run["c"] - cp).sum()) / 1000 / site.years_equiv,
               charged_from_saleable_gwh=float(cp.sum()) / 1000 / site.years_equiv,
               served_gain_pp=100 * float(run["r"].sum() - cp.sum()) / site.D.sum(), max_budget_use_pct=100 * max(disc.values()),
               worst_year_m=min(by_year.values()) / 1e6, best_year_m=max(by_year.values()) / 1e6,
               loss_years=sum(v < 0 for v in by_year.values()), end_stock=float(run["s"][-1]))
    row.update({f"net_{y}_m": v / 1e6 for y, v in by_year.items()})
    return row


def audit(run: dict, unused, unmet, policy: str, sold=None) -> list[str]:
    """Independent check of a battery schedule against every operating condition."""
    c, r, s = run["c"], run["r"], run["s"]
    out = []
    tol = 1e-6
    s_prev = np.r_[0.0, s[:-1]]
    if np.abs(s - (s_prev + ETA * c - r / ETA)).max() > 1e-5: out.append("stock balance")
    if s.min() < -tol or s.max() > USABLE + tol: out.append("stock bounds")
    if abs(s[-1]) > 1e-5: out.append("closing stock")
    cp = run.get("c_paid", np.zeros_like(c))
    if (c > P_STEP + tol).any() or (c - cp > np.minimum(P_STEP, unused) + tol).any(): out.append("charge limit")
    if cp.max() > tol and (policy == "B" or sold is None or (cp > np.minimum(P_STEP, sold) + tol).any()): out.append("charging from saleable generation")
    if (r > np.minimum(P_STEP, unmet) + tol).any(): out.append("discharge limit")
    if (np.minimum(c, r) > 1e-5).any(): out.append("charging and discharging together")
    if policy == "B":
        due = np.minimum(np.minimum(unmet, P_STEP), ETA * s_prev)
        if np.abs(r - due).max() > 1e-5: out.append("B: stored energy held back during a shortfall")
    return out


def joint_check(site: Site, modules: int, cap_kg: float) -> dict:
    """Battery value when battery and electrolyser are scheduled together, against this study's method.

    Policy A, half-hour switching without a minimum load, so that both sides are linear programmes. `site` should
    cover one calendar year. Returns the battery's gross value from the joint programme and from the method used in
    the study (electrolyser plan fixed first, battery scheduled on what is left).
    """
    G, D, p = site.G.ravel(), site.D.ravel(), site.p.ravel()
    T, nd = len(p), site.nd
    cap_mwh = cap_kg * site.kwh_per_kg / 1000
    hi = modules * site.e
    I = eye(T, format="csr"); Z = coo_matrix((T, T)).tocsr()
    sub = coo_matrix((np.ones(T - 1), (np.arange(1, T), np.arange(T - 1))), shape=(T, T)).tocsr()
    day = np.repeat(np.arange(nd), T // nd)
    Dm = coo_matrix((np.ones(T), (day, np.arange(T))), shape=(nd, T)).tocsr(); Zd = coo_matrix((nd, T)).tocsr()
    one = coo_matrix(np.ones((1, T)) / ETA); z1 = coo_matrix((1, T))
    # variables: direct sales q, generation to electrolysis h, charge c, discharge to sales r, to electrolysis u, stock s
    A_ub = vstack([hstack([I, I, I, Z, Z, Z]), hstack([I, Z, Z, I, Z, Z]), hstack([Z, I, Z, Z, I, Z]), hstack([Z, Z, Z, I, I, Z]),
                   hstack([Zd, Dm, Zd, Zd, Dm, Zd]), hstack([z1, z1, z1, one, one, z1])], format="csr")
    b_ub = np.r_[G, D, np.full(T, hi), np.full(T, P_STEP), np.full(nd, cap_mwh), BUDGET_PER_DAY * nd]
    A_eq = hstack([Z, Z, -ETA * I, I / ETA, I / ETA, I - sub], format="csr")
    cost = np.r_[-p, -np.full(T, site.w), np.zeros(T), -p, -np.full(T, site.w), np.zeros(T)]
    smax = np.full(T, USABLE); smax[-1] = 0.0
    ub = np.r_[np.minimum(G, D), np.full(T, hi), np.full(T, P_STEP), np.full(T, P_STEP), np.full(T, P_STEP), smax]
    both = linprog(cost, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=np.zeros(T), bounds=np.c_[np.zeros(6 * T), ub], method="highs")
    ub0 = ub.copy(); ub0[2 * T:] = 0.0
    alone = linprog(cost, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=np.zeros(T), bounds=np.c_[np.zeros(6 * T), ub0], method="highs")
    if both.status != 0 or alone.status != 0:
        raise RuntimeError("joint check did not solve")
    disp = flexible_dispatch(site, "A", 0.0, modules, cap_kg)
    greedy = reference(site, "A")["receipts"] * site.years_equiv + disp["value"].sum()
    unused, unmet, price = opportunities(site, "A", disp)
    sold = np.maximum(reference(site, "A")["q"] - disp["paid"], 0.0).ravel()
    fixed = perfect_foresight_A(site, unused, unmet, price, sold=sold)
    return dict(joint_battery_value_m=(-both.fun + alone.fun) / 1e6, fixed_plan_battery_value_m=fixed["gross"] * site.years_equiv / 1e6,
                electrolysis_lp_minus_greedy_gbp=-alone.fun - greedy)
