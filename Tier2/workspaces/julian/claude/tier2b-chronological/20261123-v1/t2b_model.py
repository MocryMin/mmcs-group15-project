"""
Tier 2B - operating the Tier 1 portfolio through time (daily chronology).

What is new relative to the Tier 1 model in t1_model.py
-------------------------------------------------------
* Days are linked.  A started electrolyser module must stay on for `min_run` days and must take at least its
  minimum load on every day it is on (course Q&A of 16 November: an electrolyser is not switched on and off
  daily; "at least 4 or 5 days").  A battery, if one is built, carries its state of charge from day to day.
* Three rules for the electricity an electrolyser may take:
    'strict'  only energy that has no buyer (the literal Tier 1 rule);
    'topup'   energy with no buyer, plus just enough other electricity to hold minimum load on a committed day;
    'divert'  also saleable output of the wind farm whenever that pays (grid imports only to hold minimum load).
* Operation without foresight: a rolling optimisation that commits modules one day ahead on forecasts that are
  updated every day, and then takes whatever the day actually brings (see t2b_forecast.py and t2b_run.py).

Units: MWh per day for energy, GBP (2023 prices) for money.  One module is 20 MW, so 480 MWh/day at full load
and 96 MWh/day at minimum load.

Solver: HiGHS through scipy.optimize.milp.  `solver="xpress"` sends the same matrices to FICO Xpress through
t1_model._solve_xpress; that branch has not been executed where this file was written.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from itertools import product
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import coo_matrix

from t1_model import Params, Problem, _solve_xpress

RULES = ("strict", "topup", "divert")


@dataclass(frozen=True)
class Ops:
    min_run: int = 5            # days a started module must stay on; 1 = free daily switching (Tier 1)
    rule: str = "topup"
    start_cost: float = 0.0     # GBP per module start (assumption, tested in the sensitivity runs)
    import_adder: float = 0.0   # GBP/MWh on top of the market price for grid imports (assumption, tested)


def module_energy(par: Params):
    cap = par.module_mw * 24.0
    return par.min_load * cap, cap           # minimum and full daily energy of one module


# ---------------------------------------------------------------------------------------------------------
# Closed-form operation of a given commitment path (no battery)
# ---------------------------------------------------------------------------------------------------------
def realise(S, Q0, p, n, par: Params, ops: Ops, cap_mwh=np.inf):
    """Best use of each day's energy when the number of running modules n[t] is already fixed.
    Returns a dict of daily arrays.  Under 'strict' a committed module that finds too little unsold energy still
    has to hold minimum load; that forced purchase is counted in `forced`."""
    S, Q0, p, n = (np.asarray(a, float) for a in (S, Q0, p, n))
    m, cap = module_energy(par)
    lo, hi = m * n, np.minimum(cap * n, cap_mwh)
    hi = np.maximum(hi, lo)                                   # an offtake limit never undercuts minimum load
    margin, buy = par.margin, np.maximum(p, 0.0) + ops.import_adder
    xs = np.minimum(S, hi)
    xd = np.zeros_like(S)
    if ops.rule == "divert":
        xd = np.where(p < margin, np.minimum(Q0, hi - xs), 0.0)
    short = np.maximum(lo - xs - xd, 0.0)                     # still below minimum load
    more_d = np.minimum(Q0 - xd, short)                       # own saleable output first, then the grid
    xg = short - more_d
    xd = xd + more_d
    load = xs + xd + xg
    starts = np.maximum(np.diff(np.concatenate([[0.0], n])), 0.0)
    cash = margin * load - p * xd - buy * xg - ops.start_cost * starts
    forced = short if ops.rule == "strict" else np.zeros_like(S)
    return dict(load=load, xs=xs, xd=xd, xg=xg, cash=cash, starts=starts, forced=forced)


def summarise(prob: Problem, n, ops: Ops, n_modules, bat_mwh=0.0, cash=None, label="", extra=None):
    """Annualised metrics for a commitment path, operated in closed form unless daily cash is supplied."""
    par = prob.par
    r = realise(prob.S, prob.Q0, prob.p, n, par, ops, prob.cap_mwh)
    cash = r["cash"] if cash is None else cash
    m, cap = module_energy(par)
    mw = n_modules * par.module_mw
    yrs = prob.years
    out = dict(label=label, rule=ops.rule, min_run=ops.min_run, modules=int(round(n_modules)), electrolyser_MW=mw,
               battery_MWh=bat_mwh,
               operating_cash_m=float(cash.sum()) / yrs / 1e6,
               annual_cost_m=(par.el_annual * mw + par.bat_annual * bat_mwh) / 1e6,
               h2_t_per_year=float(r["load"].sum()) / par.kwh_per_kg / yrs,
               utilisation=float(r["load"].sum()) / (cap * n_modules * prob.T) if n_modules else 0.0,
               unused_energy_used_share=float(r["xs"].sum()) / max(float(prob.S.sum()), 1e-9),
               h2_share_from_unused=float(r["xs"].sum()) / max(float(r["load"].sum()), 1e-9),
               diverted_GWh=float(r["xd"].sum()) / yrs / 1e3, imported_GWh=float(r["xg"].sum()) / yrs / 1e3,
               days_on_share=float(np.mean(np.asarray(n) > 0)), starts_per_year=float(r["starts"].sum()) / yrs,
               forced_GWh=float(r["forced"].sum()) / yrs / 1e3)
    out["net_gain_m"] = out["operating_cash_m"] - out["annual_cost_m"]
    capex = (par.el_capex * mw + par.bat_capex * bat_mwh) / 1e6
    out["capex_m"] = capex
    fom = (par.el_fom * par.el_capex * mw + par.bat_fom * par.bat_capex * bat_mwh) / 1e6
    free = out["operating_cash_m"] - fom
    out["payback_years"] = capex / free if free > 1e-9 else np.inf
    if extra: out.update(extra)
    return out


# ---------------------------------------------------------------------------------------------------------
# Chronological mixed-integer programme
# ---------------------------------------------------------------------------------------------------------
def solve_chrono(S, Q0, R, p, years, par: Params, ops: Ops, n_modules=None, n_max=None, bat_mwh=0.0, b_max=0.0,
                 n_prev=0, carry=None, soc0=0.0, cap_mwh=np.inf, fix_n=None, capex_in_obj=True,
                 time_limit=300, gap=1e-4, solver="highs"):
    """Maximise annualised net gain over consecutive days.

    n_modules  fixed plant size; None lets the model choose it (integer, up to n_max)
    bat_mwh    fixed battery size; set b_max > 0 to let the model choose it
    n_prev     modules running on the day before the horizon; carry[t] = modules that started before the
               horizon and are still inside their minimum run on day t (rolling use)
    fix_n      optional commitment path to impose (used for cross-checks)
    Returns dict(n, load, xs, xd, xg, cash, modules, battery, objective, status)."""
    S, Q0, R, p = (np.asarray(a, float) for a in (S, Q0, R, p))
    T = len(p)
    m, cap = module_energy(par)
    size_free, bat_free = n_modules is None, b_max > 0
    N_ub = int(n_max if size_free else n_modules)
    use_bat = bat_free or bat_mwh > 0
    L = max(int(ops.min_run), 1)
    margin, buy = par.margin, np.maximum(p, 0.0) + ops.import_adder
    eta, P = np.sqrt(par.bat_rte), 24.0 / par.bat_hours

    names = ["n", "v", "z", "xs", "xd", "xg"] + (["cs", "cd", "ds", "dh", "soc"] if use_bat else [])
    ix = {k: np.arange(i * T, (i + 1) * T) for i, k in enumerate(names)}
    nv = len(names) * T
    iN = iB = None
    if size_free: iN, nv = nv, nv + 1
    if bat_free: iB, nv = nv, nv + 1

    lb, ub = np.zeros(nv), np.full(nv, np.inf)
    integ = np.zeros(nv)
    ub[ix["n"]] = N_ub; integ[ix["n"]] = 1
    ub[ix["z"]] = 1; integ[ix["z"]] = 1
    ub[ix["xs"]] = S; ub[ix["xd"]] = Q0
    if ops.rule == "strict": ub[ix["xd"]] = 0; ub[ix["xg"]] = 0; ub[ix["z"]] = 0
    if size_free: ub[iN] = N_ub; integ[iN] = 1
    if bat_free: ub[iB] = b_max
    if use_bat and ops.rule != "divert": ub[ix["cd"]] = 0
    if fix_n is not None: lb[ix["n"]] = ub[ix["n"]] = np.asarray(fix_n, float)

    rows, cols, vals, lo, hi = [], [], [], [], []
    r = [0]

    def add(entries, lo_, hi_):
        """entries: list of (columns array, coefficient) for T (or fewer) parallel rows"""
        k = len(entries[0][0])
        rr = np.arange(r[0], r[0] + k)
        for c_, a_ in entries:
            rows.append(rr); cols.append(np.asarray(c_)); vals.append(np.broadcast_to(np.asarray(a_, float), (k,)))
        lo.append(np.broadcast_to(np.asarray(lo_, float), (k,))); hi.append(np.broadcast_to(np.asarray(hi_, float), (k,)))
        r[0] += k

    load = [(ix["xs"], 1.0), (ix["xd"], 1.0), (ix["xg"], 1.0)] + ([(ix["dh"], 1.0)] if use_bat else [])
    add(load + [(ix["n"], -m)], 0.0, np.inf)                                  # at least minimum load
    add(load + [(ix["n"], -cap)], -np.inf, 0.0)                               # at most full load
    if np.isfinite(cap_mwh): add(load, -np.inf, max(cap_mwh, 0.0))           # offtake limit
    if size_free: add([(ix["n"], 1.0), (np.full(T, iN), -1.0)], -np.inf, 0.0)
    # other electricity only to hold minimum load: allowed on days with z = 1, and then load equals minimum load
    U = m * N_ub
    non_surplus = [(ix["xg"], 1.0)] + ([(ix["xd"], 1.0)] if ops.rule == "topup" else [])
    add(non_surplus + [(ix["z"], -U)], -np.inf, 0.0)
    add(load + [(ix["n"], -m), (ix["z"], (cap - m) * N_ub)], -np.inf, (cap - m) * N_ub)
    # starts and minimum run
    add([(ix["v"][1:], 1.0), (ix["n"][1:], -1.0), (ix["n"][:-1], 1.0)], 0.0, np.inf)
    rows.append(np.array([r[0], r[0]])); cols.append(np.array([ix["v"][0], ix["n"][0]])); vals.append(np.array([1.0, -1.0]))
    lo.append(np.array([-float(n_prev)])); hi.append(np.array([np.inf])); r[0] += 1
    carry = np.zeros(T) if carry is None else np.asarray(carry, float)
    if L > 1 or carry.any():
        for t in range(T):
            a = max(0, t - L + 1)
            k = t - a + 1
            rows.append(np.full(k + 1, r[0])); cols.append(np.concatenate([ix["v"][a:t + 1], [ix["n"][t]]]))
            vals.append(np.concatenate([np.ones(k), [-1.0]])); lo.append(np.array([-np.inf])); hi.append(np.array([-carry[t]]))
            r[0] += 1
    if use_bat:
        add([(ix["xs"], 1.0), (ix["cs"], 1.0)], -np.inf, S)
        add([(ix["xd"], 1.0), (ix["cd"], 1.0)], -np.inf, Q0)
        add([(ix["ds"], 1.0), (ix["xd"], -1.0), (ix["cd"], -1.0)], -np.inf, R)   # room for extra sales
        bcol = [(np.full(T, iB), 1.0)] if bat_free else []
        fixB = 0.0 if bat_free else bat_mwh
        add([(ix["cs"], 1.0), (ix["cd"], 1.0)] + [(c_, -P) for c_, _ in bcol], -np.inf, P * fixB)
        add([(ix["ds"], 1.0), (ix["dh"], 1.0)] + [(c_, -P) for c_, _ in bcol], -np.inf, P * fixB)
        add([(ix["soc"], 1.0)] + [(c_, -par.bat_usable) for c_, _ in bcol], -np.inf, par.bat_usable * fixB)
        add([(ix["soc"][1:], 1.0), (ix["soc"][:-1], -1.0), (ix["cs"][1:], -eta), (ix["cd"][1:], -eta),
             (ix["ds"][1:], 1 / eta), (ix["dh"][1:], 1 / eta)], 0.0, 0.0)
        rows.append(np.full(5, r[0])); cols.append(np.array([ix["soc"][0], ix["cs"][0], ix["cd"][0], ix["ds"][0], ix["dh"][0]]))
        vals.append(np.array([1.0, -eta, -eta, 1 / eta, 1 / eta])); lo.append(np.array([soc0])); hi.append(np.array([soc0])); r[0] += 1

    c = np.zeros(nv)
    w = 1.0 / years
    c[ix["xs"]] = margin * w
    c[ix["xd"]] = (margin - p) * w
    c[ix["xg"]] = (margin - buy) * w
    c[ix["v"]] = -ops.start_cost * w
    if use_bat:
        c[ix["dh"]] = margin * w; c[ix["cd"]] = -p * w; c[ix["ds"]] = p * w
    if size_free and capex_in_obj: c[iN] = -par.el_annual * par.module_mw
    if bat_free and capex_in_obj: c[iB] = -par.bat_annual

    A = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(r[0], nv)).tocsr()
    lo, hi = np.concatenate(lo), np.concatenate(hi)
    mip_gap = np.nan
    if solver == "xpress":
        x, status = _solve_xpress(c, A, lo, hi, lb, ub, integ, time_limit, gap)
    else:
        res = milp(-c, constraints=LinearConstraint(A, lo, hi), bounds=Bounds(lb, ub), integrality=integ,
                   options=dict(time_limit=time_limit, mip_rel_gap=gap, disp=False))
        if res.x is None:
            return dict(status=f"no solution ({res.message})", n=None)
        x, status = res.x, ("optimal" if res.status == 0 else res.message)
        mip_gap = float(getattr(res, "mip_gap", np.nan))
    n = np.round(x[ix["n"]])
    xs, xd, xg = x[ix["xs"]], x[ix["xd"]], x[ix["xg"]]
    dh = x[ix["dh"]] if use_bat else np.zeros(T)
    cash = margin * (xs + xd + xg + dh) - p * xd - buy * xg - ops.start_cost * np.maximum(x[ix["v"]], 0)
    if use_bat: cash = cash + p * x[ix["ds"]] - p * x[ix["cd"]]
    return dict(status=status, n=n, load=xs + xd + xg + dh, xs=xs, xd=xd, xg=xg, cash=cash,
                modules=int(round(x[iN])) if size_free else int(n_modules),
                battery=float(x[iB]) if bat_free else float(bat_mwh),
                soc=x[ix["soc"]] if use_bat else None, objective=float(c @ x), mip_gap=mip_gap)


def chrono_problem(prob: Problem, ops: Ops, **kw):
    """solve_chrono on a Problem (whole record, starting cold)."""
    kw.setdefault("n_max", prob.n_max)
    return solve_chrono(prob.S, prob.Q0, prob.R, prob.p, prob.years, prob.par, ops, cap_mwh=prob.cap_mwh, **kw)


# ---------------------------------------------------------------------------------------------------------
# Exhaustive search on a short window - an independent check of the programme above
# ---------------------------------------------------------------------------------------------------------
def brute_force(S, Q0, p, par: Params, ops: Ops, n_modules, cap_mwh=np.inf):
    """Enumerate every commitment path on a short window (testing only)."""
    T, L = len(p), max(int(ops.min_run), 1)
    m, _ = module_energy(par)
    best, best_n = -np.inf, None
    for path in product(range(n_modules + 1), repeat=T):
        n = np.array(path, float)
        v = np.maximum(np.diff(np.concatenate([[0.0], n])), 0.0)
        if any(v[max(0, t - L + 1):t + 1].sum() > n[t] + 1e-9 for t in range(T)): continue
        if ops.rule == "strict" and np.any(m * n > np.asarray(S) + 1e-9): continue
        cash = realise(S, Q0, p, n, par, ops, cap_mwh)["cash"].sum()
        if cash > best + 1e-9: best, best_n = cash, n
    return best_n, best


# ---------------------------------------------------------------------------------------------------------
# Operation without foresight: commit one day ahead on forecasts, then take what the day brings
# ---------------------------------------------------------------------------------------------------------
def rolling_operation(prob: Problem, ops: Ops, n_modules, fc=None, H=7, first=1, last=None, method="mpc",
                      solver="highs"):
    """Commitment path n[t] for t in [first, last] decided at the end of day t-1.

    fc      {'S','Q0','p'}: arrays (T, H); row o holds the forecasts made at the end of day o for days o+1..o+H
    method  'mpc'     solve the chronological programme over the next H days on the latest forecasts, keep day 1
            'price'   run every module when tomorrow's forecast price is below the hydrogen break-even price
            'always'  never switch off
    The plant starts cold on day `first`.  Minimum-run obligations from earlier starts are always respected."""
    par, T, L = prob.par, prob.T, max(int(ops.min_run), 1)
    last = T - 1 if last is None else last
    n, starts, n_prev = np.zeros(T), np.zeros(T), 0
    for t in range(first, last + 1):
        o = t - 1
        carry = np.array([starts[max(first, t + j - L + 1):t].sum() for j in range(H)])
        if method == "always":
            nt = n_modules
        elif method == "price":
            nt = max(n_modules if fc["p"][o, 0] < par.margin else 0, int(carry[0]))
        else:
            r = solve_chrono(fc["S"][o], fc["Q0"][o], np.zeros(H), fc["p"][o], 1.0, par, ops, n_modules=n_modules,
                             n_prev=n_prev, carry=carry, cap_mwh=prob.cap_mwh, gap=1e-6, time_limit=30, solver=solver)
            nt = int(r["n"][0]) if r["n"] is not None else max(n_prev, int(carry[0]))
        n[t], starts[t], n_prev = nt, max(nt - n_prev, 0), nt
    return n
