"""Independent Tier 1 - problem definition and four solution methods.

Client position (from the brief and the course's own get_data.py analysis):
  the national fleet G_t serves national demand D_t; the client's 1,125 MW wind farm W_t is added on top.
  The farm can sell   q0_t = min(W_t, max(D_t - G_t, 0))   at the market price p_t;
  the rest            s_t  = W_t - q0_t                     is "otherwise unused renewable energy".
Tier 1 question: how much electrolyser (20 MW modules) and 2-hour battery is worth adding?

Policies
  'surplus'  only the unused energy s_t may feed the electrolyser or the battery (the brief's Tier 1 wording)
  'divert'   saleable energy may also be turned into hydrogen or stored when that is worth more than selling it
Boundary
  'farm'     as above (central case)          'system'  the whole fleet G_t + W_t is the client's pool (the group repo's reading)

Methods (all maximise annualised net benefit = hydrogen and electricity margin minus annuity and fixed costs)
  M1  duration_curve   analytical, no dates: marginal value of capacity from the surplus duration curve
  M2  rep_weeks        MILP on K representative weeks (simplified time, storage cycles inside a week)
  M3  chronological    MILP on every day in order with perfect foresight (upper bound)
  M4  sim_search       rule-based day-by-day simulation without foresight + exhaustive search over designs
Units: energy MWh per day (= 24 x daily mean MW), money GBP in 2023 prices.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import coo_matrix


@dataclass(frozen=True)
class Params:
    # hydrogen
    h2_value: float = 9.5              # GBP/kg, brief benchmark (HAR1 strike price, 2023 prices)
    kwh_per_kg: float = 55.9           # brief
    h2_cap_kg_day: float | None = None # optional offtake limit
    # electrolyser (PEM), per MW of electrical input
    el_capex: float = 2_000_000        # IEA Global Hydrogen Review 2025 (via ACER): PEM EUR 2,365/kW installed in 2024
    el_fom: float = 0.03               # IEA GHR 2024 assumptions annex: annual OPEX 3% of CAPEX
    el_life: int = 25                  # NESO levelised cost of green hydrogen: 25-year plant life
    stack_share: float = 0.30          # stack replacement as share of CAPEX (TNO stack cost range 16-45%; Andoni et al. 48%)
    stack_hours: float = 50_000        # IEA GHR 2024 assumptions annex
    module_mw: float = 20.0            # brief: ITM POSEIDON 20 MW reference unit
    min_load: float = 0.20             # brief: 20%-100%
    min_load_mode: str = "module"      # 'module' (4 MW floor), 'plant' (20% of the whole plant), 'none'
    # battery, per MWh of energy capacity
    bat_capex: float = 288_000 * 0.85  # brief: EUR 0.288m/MWh, converted at 0.85 GBP/EUR (assumption)
    bat_fom: float = 0.01              # assumption
    bat_life: int = 20                 # assumption (generous to the battery)
    bat_rte: float = 0.90              # brief
    bat_usable: float = 0.60           # brief: 20%-80% window
    bat_hours: float = 2.0             # brief: 2-hour battery
    # finance and case definition
    rate: float = 0.08                 # real discount rate (NESO LCOH work spans 6-15%)
    policy: str = "surplus"
    boundary: str = "farm"
    n_max: int | None = None

    @property
    def crf_el(self): return self.rate / (1 - (1 + self.rate) ** -self.el_life)
    @property
    def crf_bat(self): return self.rate / (1 - (1 + self.rate) ** -self.bat_life)
    @property
    def el_annual(self): return (self.crf_el + self.el_fom) * self.el_capex            # GBP per MW-year
    @property
    def bat_annual(self): return (self.crf_bat + self.bat_fom) * self.bat_capex        # GBP per MWh-year
    @property
    def stack_cost(self): return self.stack_share * self.el_capex / self.stack_hours   # GBP per MWh of electricity used
    @property
    def margin(self): return self.h2_value * 1000 / self.kwh_per_kg - self.stack_cost  # GBP per MWh turned into hydrogen


class Problem:
    """Daily arrays derived from the cleaned data for one boundary/policy/parameter set."""
    def __init__(self, df: pd.DataFrame, par: Params, price_col="price", gen_col="gen_MW", demand_col="demand_MW"):
        self.par, self.dates = par, df.index
        W, G, D = df["farm_MW"].to_numpy(float), df[gen_col].to_numpy(float), df[demand_col].to_numpy(float)
        p = df[price_col].to_numpy(float)
        if par.boundary == "farm":
            own, head = W, np.maximum(D - G, 0.0)
        else:
            own, head = G + W, D
        q0 = np.where(p >= 0, np.minimum(own, head), 0.0)      # nothing is sold at a negative price
        self.own = 24 * own                                     # MWh/day available to the client
        self.Q0 = 24 * q0                                       # baseline sales
        self.S = self.own - self.Q0                             # unused energy
        self.R = 24 * head - self.Q0                            # room for extra sales (battery discharge)
        self.p = p
        self.T = len(p)
        self.years = float(np.sum(1 / np.where(df.index.is_leap_year, 366, 365)))
        self.own_peak_mw = float(own.max())
        nmax = par.n_max if par.n_max is not None else int(np.ceil(own.max() / par.module_mw))
        self.n_max = nmax
        self.cap_mwh = np.inf if par.h2_cap_kg_day is None else par.h2_cap_kg_day * par.kwh_per_kg / 1000
        self.base_revenue = float(np.sum(self.Q0 * p)) / self.years

    def subset(self, mask):
        new = object.__new__(Problem); new.__dict__.update(self.__dict__)
        for k in ("own", "Q0", "S", "R", "p"):
            setattr(new, k, getattr(self, k)[mask])
        new.dates = self.dates[mask]; new.T = int(np.sum(mask))
        new.years = float(np.sum(1 / np.where(new.dates.is_leap_year, 366, 365)))
        new.base_revenue = float(np.sum(new.Q0 * new.p)) / new.years
        return new


# ------------------------------------------------------------------ exact operation without a battery
def dispatch(prob: Problem, n_modules: float):
    """Best daily operation of an n-module electrolyser with no battery (each day is independent)."""
    par = prob.par
    A = min(24 * par.module_mw * n_modules, prob.cap_mwh)
    m = par.margin
    a_s = np.minimum(prob.S, A)
    a_d = np.zeros(prob.T)
    if par.policy == "divert":
        a_d = np.where(prob.p < m, np.minimum(prob.Q0, A - a_s), 0.0)
    if par.min_load_mode != "none" and n_modules > 0:
        floor = 24 * par.min_load * (par.module_mw if par.min_load_mode == "module" else par.module_mw * n_modules)
        tot = a_s + a_d
        low = (tot > 0) & (tot < floor - 1e-9)
        if low.any():
            if par.policy == "divert":       # topping up to the floor from saleable energy may still pay
                top = np.minimum(floor - a_s, prob.Q0)
                ok = low & (a_s + top >= floor - 1e-9) & (floor <= A + 1e-9) & (m * floor - prob.p * top > 0)
                a_d = np.where(ok, top, np.where(low, 0.0, a_d))
                a_s = np.where(low & ~ok, 0.0, a_s)
            else:
                a_s = np.where(low, 0.0, a_s)
    return a_s, a_d


def metrics(prob: Problem, n_modules, bat_mwh, a_s, a_d, d_sell=None, d_h2=None, c_d=None, label=""):
    par = prob.par
    z = np.zeros(prob.T)
    d_sell = z if d_sell is None else d_sell; d_h2 = z if d_h2 is None else d_h2; c_d = z if c_d is None else c_d
    E = par.module_mw * n_modules
    elec_h2 = a_s + a_d + d_h2
    daily = par.margin * elec_h2 + prob.p * (d_sell - a_d - c_d)                        # GBP/day operating margin gain
    op = daily.sum() / prob.years
    fixed_om = par.el_fom * par.el_capex * E + par.bat_fom * par.bat_capex * bat_mwh
    capex = par.el_capex * E + par.bat_capex * bat_mwh
    cash = op - fixed_om                                                                 # before capital recovery
    net = op - par.el_annual * E - par.bat_annual * bat_mwh
    by_year = pd.Series(daily, index=prob.dates).groupby(prob.dates.year).sum() - (par.el_annual * E + par.bat_annual * bat_mwh)
    return dict(label=label, policy=par.policy, boundary=par.boundary, modules=n_modules, electrolyser_MW=E, battery_MWh=bat_mwh,
                capex_m=capex / 1e6, net_gain_m=net / 1e6, cash_gain_m=cash / 1e6,
                payback_years=capex / cash if cash > 1e-9 and capex > 0 else np.nan,
                h2_t_per_year=elec_h2.sum() / par.kwh_per_kg / prob.years,
                unused_captured_share=float((a_s.sum() + (0 if bat_mwh == 0 else 0)) / max(prob.S.sum(), 1e-9)),
                diverted_GWh_per_year=float(a_d.sum() / prob.years / 1000),
                utilisation=float(elec_h2.sum() / (24 * E * prob.T)) if E > 0 else 0.0,
                worst_year_m=float(by_year.min() / 1e6), best_year_m=float(by_year.max() / 1e6),
                by_year={int(k): float(v / 1e6) for k, v in by_year.items()})


def evaluate_exact(prob: Problem, n_modules, label=""):
    a_s, a_d = dispatch(prob, n_modules)
    return metrics(prob, n_modules, 0.0, a_s, a_d, label=label)


# ------------------------------------------------------------------ M1: duration curve (analytical)
def m1_duration_curve(prob: Problem):
    """Marginal value of the E-th MW from the duration curve; no chronology is used."""
    par = prob.par; m = par.margin
    s_mw, own_mw = prob.S / 24, prob.own / 24
    grid = np.arange(0, int(np.ceil(prob.own_peak_mw)) + 1)                 # MW levels
    hours = np.array([(s_mw > e).sum() for e in grid]) * 24 / prob.years     # hours/yr the E-th MW runs on unused energy
    mv = m * hours
    if par.policy == "divert":
        gain = np.maximum(m - prob.p, 0.0)
        mv = mv + np.array([24 * gain[(s_mw <= e) & (own_mw > e)].sum() for e in grid]) / prob.years
    if np.isfinite(prob.cap_mwh):
        mv = np.where(grid * 24 >= prob.cap_mwh, 0.0, mv)
    above = np.flatnonzero(mv >= par.el_annual)
    e_star = float(grid[above[-1]] + 1) if len(above) else 0.0
    cands = sorted({int(np.floor(e_star / par.module_mw)), int(np.ceil(e_star / par.module_mw))})
    best = max((evaluate_exact(prob, n) for n in cands), key=lambda r: r["net_gain_m"])
    # battery screen (surplus policy): one fill per run of days with unused energy left over, one release before the next run
    a_s, a_d = dispatch(prob, best["modules"])
    A = min(24 * par.module_mw * best["modules"], prob.cap_mwh)
    left = prob.S - a_s > 1e-6
    spare = (A - a_s - a_d) > 1e-6
    unit = np.maximum(np.where(spare, m, 0.0), np.where(prob.R > 1e-6, prob.p, 0.0))      # best use of a released MWh that day
    eta_d = np.sqrt(par.bat_rte)
    runs, value, t = 0, 0.0, 0
    while t < prob.T:
        if left[t]:
            while t < prob.T and left[t]: t += 1
            g0 = t
            while t < prob.T and not left[t]: t += 1
            if t > g0:
                runs += 1; value += par.bat_usable * eta_d * unit[g0:t].max()
        else:
            t += 1
    arb = par.bat_usable * eta_d * np.maximum(np.diff(prob.p), 0).sum() / prob.years if par.policy == "divert" else 0.0
    best.update(label="M1 duration curve", continuous_optimum_MW=e_star,
                marginal_value_first_MW=float(mv[0]), annual_cost_per_MW=par.el_annual,
                breakeven_hours=par.el_annual / m, first_MW_hours=float(hours[0]),
                battery_cycles_per_year=runs / prob.years, battery_value_bound_per_MWh=value / prob.years + arb,
                battery_annual_cost_per_MWh=par.bat_annual)
    curve = pd.DataFrame({"MW": grid, "marginal_value": mv, "hours_on_unused_energy": hours})
    return best, curve


# ------------------------------------------------------------------ MILP used by M2, M3 and exact evaluation
def solve_milp(prob: Problem, blocks, weights, fix_n=None, fix_b=None, cyclic=False, b_max=20000.0,
               time_limit=180, gap=1e-5, solver="highs"):
    """blocks: list of index arrays (days in chronological order); weights: one weight per block.
    Returns dict with design and flows for the days in `blocks` (concatenated)."""
    par = prob.par; m = par.margin
    eta = np.sqrt(par.bat_rte)
    days = np.concatenate(blocks); T = len(days)
    wt = np.concatenate([np.full(len(b), w, float) for b, w in zip(blocks, weights)]) / prob.years
    S, Q0, R, p = prob.S[days], prob.Q0[days], prob.R[days], prob.p[days]
    use_bin = par.min_load_mode != "none"
    # variable layout
    iN, iB = 0, 1
    off = 2
    a_s, a_d, c_s, c_d, d_s, d_h, soc = (off + k * T + np.arange(T) for k in range(7))
    u = off + 7 * T + np.arange(T) if use_bin else None
    nv = off + (8 if use_bin else 7) * T
    c = np.zeros(nv)
    c[iN] = -par.el_annual * par.module_mw; c[iB] = -par.bat_annual
    c[a_s] = wt * m; c[a_d] = wt * (m - p); c[d_h] = wt * m; c[d_s] = wt * p; c[c_d] = -wt * p
    lb = np.zeros(nv); ub = np.full(nv, np.inf)
    ub[iN] = prob.n_max; ub[iB] = b_max
    if fix_n is not None: lb[iN] = ub[iN] = fix_n
    if fix_b is not None: lb[iB] = ub[iB] = fix_b
    if par.policy != "divert":
        ub[a_d] = 0.0; ub[c_d] = 0.0
    integrality = np.zeros(nv); integrality[iN] = 1
    if use_bin:
        integrality[u] = 1; ub[u] = 1
    rows, cols, vals, lo, hi = [], [], [], [], []
    nr = 0
    def add(col_lists, val_lists, lo_, hi_):
        nonlocal nr
        n = len(col_lists[0])
        for cc, vv in zip(col_lists, val_lists):
            rows.extend(range(nr, nr + n)); cols.extend(np.broadcast_to(cc, (n,)).tolist()); vals.extend(np.broadcast_to(vv, (n,)).astype(float).tolist())
        lo.extend(np.broadcast_to(lo_, (n,)).astype(float).tolist()); hi.extend(np.broadcast_to(hi_, (n,)).astype(float).tolist()); nr += n
    one = np.ones(T)
    add([a_s, c_s], [one, one], -np.inf, S)                                   # unused energy
    add([a_d, c_d], [one, one], -np.inf, Q0)                                  # saleable energy
    add([d_s, a_d, c_d], [one, -one, -one], -np.inf, R)                       # sales cannot exceed what the system absorbs
    add([a_s, a_d, d_h, np.full(T, iN)], [one, one, one, np.full(T, -24 * par.module_mw)], -np.inf, 0.0)   # electrolyser rating
    if np.isfinite(prob.cap_mwh):
        add([a_s, a_d, d_h], [one, one, one], -np.inf, prob.cap_mwh)
    pw = 24 / par.bat_hours
    add([c_s, c_d, np.full(T, iB)], [one, one, np.full(T, -pw)], -np.inf, 0.0)
    add([d_s, d_h, np.full(T, iB)], [one, one, np.full(T, -pw)], -np.inf, 0.0)
    add([soc, np.full(T, iB)], [one, np.full(T, -par.bat_usable)], -np.inf, 0.0)
    # state of charge
    start = 0
    for b in blocks:
        n = len(b); idx = start + np.arange(n)
        prev = np.roll(idx, 1)
        for j in range(n):
            cc = [soc[idx[j]], c_s[idx[j]], c_d[idx[j]], d_s[idx[j]], d_h[idx[j]]]; vv = [1, -eta, -eta, 1 / eta, 1 / eta]
            if j > 0 or cyclic:
                cc.append(soc[prev[j]]); vv.append(-1)
            rows.extend([nr] * len(cc)); cols.extend(cc); vals.extend(vv); lo.append(0.0); hi.append(0.0); nr += 1
        start += n
    if use_bin:
        big = 24 * par.module_mw * prob.n_max
        add([a_s, a_d, d_h, u], [one, one, one, np.full(T, -big)], -np.inf, 0.0)
        if par.min_load_mode == "module":
            add([a_s, a_d, d_h, u], [one, one, one, np.full(T, -24 * par.min_load * par.module_mw)], 0.0, np.inf)
        else:                                                                   # a >= 0.2*24*20*N - big*(1-u)
            add([a_s, a_d, d_h, np.full(T, iN), u], [one, one, one, np.full(T, -24 * par.min_load * par.module_mw), np.full(T, -big)], -big, np.inf)
    A = coo_matrix((vals, (rows, cols)), shape=(nr, nv)).tocsr()
    lo, hi = np.array(lo), np.array(hi)
    if solver == "xpress":
        x, status = _solve_xpress(c, A, lo, hi, lb, ub, integrality, time_limit, gap)
        gap_out = np.nan
    else:
        res = milp(-c, constraints=LinearConstraint(A, lo, hi), integrality=integrality, bounds=Bounds(lb, ub),
                   options={"time_limit": time_limit, "mip_rel_gap": gap, "disp": False})
        if res.x is None:
            raise RuntimeError(f"MILP failed: {res.message}")
        x, status, gap_out = res.x, res.message, getattr(res, "mip_gap", np.nan)
    return dict(modules=int(round(x[iN])), battery_MWh=float(x[iB]), objective_m=float(c @ x) / 1e6, days=days, status=status, mip_gap=gap_out,
                a_s=x[a_s], a_d=x[a_d], c_s=x[c_s], c_d=x[c_d], d_sell=x[d_s], d_h2=x[d_h], soc=x[soc])


def _solve_xpress(c, A, lo, hi, lb, ub, integrality, time_limit, gap):
    """Same matrices through the FICO Xpress Python API.  NOT executed where this file was written (no licence
    there): check it once against the HiGHS numbers with `python t1_run.py --check --solver xpress`."""
    import xpress as xp
    mdl = xp.problem()
    x = [mdl.addVariable(lb=float(l), ub=float(h) if np.isfinite(h) else xp.infinity,
                         vartype=xp.integer if i else xp.continuous) for l, h, i in zip(lb, ub, integrality)]
    A = A.tocsr()
    for r in range(A.shape[0]):
        s, e = A.indptr[r], A.indptr[r + 1]
        expr = xp.Sum(float(A.data[j]) * x[A.indices[j]] for j in range(s, e))
        if lo[r] == hi[r]: mdl.addConstraint(expr == float(hi[r]))
        else:
            if np.isfinite(hi[r]): mdl.addConstraint(expr <= float(hi[r]))
            if np.isfinite(lo[r]): mdl.addConstraint(expr >= float(lo[r]))
    mdl.setObjective(xp.Sum(float(c[j]) * x[j] for j in np.flatnonzero(c)), sense=xp.maximize)
    mdl.setControl("outputlog", 0); mdl.setControl("maxtime", int(time_limit)); mdl.setControl("miprelstop", gap)
    (mdl.optimize if hasattr(mdl, "optimize") else mdl.solve)()
    return np.asarray(mdl.getSolution(x), float), "xpress"


def _from_solution(prob, sol, label):
    full = {k: np.zeros(prob.T) for k in ("a_s", "a_d", "c_d", "d_sell", "d_h2")}
    for k in full: full[k][sol["days"]] = sol[k]
    r = metrics(prob, sol["modules"], sol["battery_MWh"], full["a_s"], full["a_d"], full["d_sell"], full["d_h2"], full["c_d"], label)
    r["status"] = sol["status"]; r["mip_gap"] = sol["mip_gap"]
    return r


# ------------------------------------------------------------------ M3: chronological, perfect foresight
def m3_chronological(prob: Problem, fix_n=None, fix_b=None, label="M3 chronological MILP", **kw):
    sol = solve_milp(prob, [np.arange(prob.T)], [1.0], fix_n=fix_n, fix_b=fix_b, **kw)
    return _from_solution(prob, sol, label)


# ------------------------------------------------------------------ M2: representative weeks
def m2_rep_weeks(prob: Problem, k=52, seed=0, label=None, **kw):
    """Simplified time: cluster the 7-day blocks of the history on a few summary features, keep the real week
    nearest to each cluster centre, weight it by cluster size, and rescale energy so that the represented
    totals match the history.  Storage may cycle inside a week but not across weeks."""
    from sklearn.cluster import KMeans
    par = prob.par
    nw = prob.T // 7
    idx = np.arange(nw * 7).reshape(nw, 7)
    S, Q0, p = prob.S[idx], prob.Q0[idx], prob.p[idx]
    feats = np.column_stack([S.sum(1), S.max(1), (S > 0).sum(1), Q0.sum(1), (np.maximum(par.margin - p, 0) * Q0).sum(1), p.mean(1), p.std(1)])
    z = (feats - feats.mean(0)) / (feats.std(0) + 1e-9)
    if k >= nw:
        chosen, weights = list(range(nw)), np.ones(nw)
    else:
        km = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(z)
        chosen, weights = [], []
        for j in range(k):
            members = np.flatnonzero(km.labels_ == j)
            dist = ((z[members] - km.cluster_centers_[j]) ** 2).sum(1)
            chosen.append(int(members[dist.argmin()])); weights.append(len(members))
    weights = np.array(weights, float)
    scaled = object.__new__(Problem); scaled.__dict__.update(prob.__dict__)
    fs = S.sum() / max((S[chosen].sum(1) * weights).sum(), 1e-9)
    fq = Q0.sum() / max((Q0[chosen].sum(1) * weights).sum(), 1e-9)
    scaled.S, scaled.Q0 = prob.S * fs, prob.Q0 * fq
    sol = solve_milp(scaled, [idx[w] for w in chosen], weights * prob.T / (nw * 7), cyclic=True, **kw)
    return dict(label=label or f"M2 representative weeks (K={len(chosen)})", policy=par.policy, boundary=par.boundary,
                modules=sol["modules"], electrolyser_MW=sol["modules"] * par.module_mw, battery_MWh=sol["battery_MWh"],
                net_gain_m_own_model=sol["objective_m"], weeks=len(chosen), energy_scale_unused=float(fs), energy_scale_saleable=float(fq),
                status=sol["status"], mip_gap=sol["mip_gap"])


# ------------------------------------------------------------------ M4: rule-based simulation + search
def simulate(prob: Problem, n_modules, bat_mwh, label="", lo_q=0.25, hi_q=0.75, window=28):
    """Day-by-day operation with no knowledge of the future."""
    par = prob.par; m = par.margin
    if bat_mwh <= 0:
        return evaluate_exact(prob, n_modules, label)
    T = prob.T; eta = np.sqrt(par.bat_rte)
    A = min(24 * par.module_mw * n_modules, prob.cap_mwh)
    floor = 0.0
    if par.min_load_mode != "none" and n_modules > 0:
        floor = 24 * par.min_load * (par.module_mw if par.min_load_mode == "module" else par.module_mw * n_modules)
    cap, pw = par.bat_usable * bat_mwh, 24 / par.bat_hours * bat_mwh
    divert = par.policy == "divert"
    S, Q0, R, p = prob.S, prob.Q0, prob.R, prob.p
    ps = pd.Series(p)
    lo_thr = ps.rolling(window, min_periods=7).quantile(lo_q).shift(1).fillna(-np.inf).to_numpy()   # yesterday's view of "cheap"
    hi_thr = ps.rolling(window, min_periods=7).quantile(hi_q).shift(1).fillna(np.inf).to_numpy()
    a_s = np.zeros(T); a_d = np.zeros(T); c_dv = np.zeros(T); d_sell = np.zeros(T); d_h2 = np.zeros(T)
    soc = 0.0
    for t in range(T):
        as_ = min(S[t], A)
        ad_ = min(Q0[t], A - as_) if (divert and p[t] < m) else 0.0
        dh_ = ds_ = cd_ = 0.0
        if S[t] <= 1e-9 and soc > 1e-9:                       # no unused energy today: release what was stored
            avail = min(soc * eta, pw)
            if m >= p[t]:
                dh_ = min(avail, A - as_ - ad_); avail -= dh_
            if p[t] > 0 and (not divert or p[t] >= hi_thr[t] or m < p[t]):
                ds_ = min(avail, R[t] + ad_)
        if floor > 0 and 0 < as_ + ad_ + dh_ < floor - 1e-9:  # below minimum load: stay off
            as_ = ad_ = dh_ = 0.0
        soc -= (dh_ + ds_) / eta
        cs_ = min(S[t] - as_, pw, (cap - soc) / eta)          # store unused energy the electrolyser could not take
        soc += cs_ * eta
        if divert and S[t] <= 1e-9 and p[t] <= lo_thr[t] and dh_ + ds_ == 0:   # cheap day: store saleable energy
            cd_ = min(Q0[t] - ad_, pw - cs_, (cap - soc) / eta); soc += cd_ * eta
        a_s[t], a_d[t], c_dv[t], d_sell[t], d_h2[t] = as_, ad_, cd_, ds_, dh_
    return metrics(prob, n_modules, bat_mwh, a_s, a_d, d_sell, d_h2, c_dv, label)


def m4_sim_search(prob: Problem, bat_grid=(0, 25, 50, 100, 200, 400, 800), label="M4 simulation + search"):
    best, table = None, []
    for b in bat_grid:
        ns = range(0, prob.n_max + 1) if b == 0 else None
        if b == 0:
            cand = [simulate(prob, n, 0.0) for n in ns]
        else:                                                  # search around the no-battery optimum
            n0 = best["modules"] if best else 0
            cand = [simulate(prob, n, float(b)) for n in sorted({0, max(n0 - 2, 0), max(n0 - 1, 0), n0, n0 + 1, n0 + 2})]
        table += [(r["modules"], r["battery_MWh"], r["net_gain_m"]) for r in cand]
        top = max(cand, key=lambda r: r["net_gain_m"])
        if best is None or top["net_gain_m"] > best["net_gain_m"] + 1e-9:
            best = top
    best = dict(best); best["label"] = label
    return best, pd.DataFrame(table, columns=["modules", "battery_MWh", "net_gain_m"])


def with_params(prob_df, par: Params, **changes):
    return Problem(prob_df, replace(par, **changes))
