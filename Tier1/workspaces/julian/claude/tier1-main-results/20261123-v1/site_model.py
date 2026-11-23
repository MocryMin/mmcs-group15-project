"""Site-scale electrolysis under supplier-realistic operating rules, on the group's half-hour Tier 1 conventions.

Conventions are those of the v7 half-hour study and report v5: 2020-2025, 105,216 half-hours, generation = supplied
total + flat wind farm, sales limited to demand, no grid imports, no hydrogen storage, 2020 pounds, 5% real,
hydrogen at the v7 net receipt, ITM NEPTUNE V modules, a daily hydrogen acceptance limit.

Energy is in MWh per half-hour, money in pounds. Written independently of the earlier scripts so that their numbers
can be checked against it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

SLOTS = 48


@dataclass(frozen=True)
class Site:
    G: np.ndarray            # generation, MWh per half-hour, shape (days, 48)
    D: np.ndarray            # demand, MWh per half-hour
    p: np.ndarray            # price, GBP/MWh
    dates: np.ndarray        # one date string per day
    year: np.ndarray         # calendar year per day
    years_equiv: float       # number of years (sum of day fractions)
    w: float                 # hydrogen receipt per MWh of electrolyser input
    e: float                 # module input energy per half-hour at full load, MWh
    kwh_per_kg: float
    kg_per_hour: float
    module_mw: float
    capital: float           # per module
    fixed_om: float          # per module per year
    annual: float            # annual-equivalent cost per module (capital, stack renewals, fixed O&M)
    netback: float           # GBP/kg

    @property
    def nd(self) -> int:
        return self.G.shape[0]

    def with_netback(self, netback: float) -> "Site":
        return Site(**{**self.__dict__, "netback": netback, "w": netback / self.kwh_per_kg * 1000})


def load(study_dir: str | Path, start="2020-01-01", end="2025-12-31", farm="flat") -> Site:
    study_dir = Path(study_dir)
    cfg = json.loads((study_dir / "configuration.json").read_text())
    f = pd.read_csv(study_dir / "inputs/halfhour.csv.gz")
    f["utc"] = pd.to_datetime(f.utc, utc=True)
    f = f.set_index("utc").loc[start:end]
    assert len(f) % SLOTS == 0 and f.groupby("date").size().eq(SLOTS).all()
    nd = len(f) // SLOTS
    G = ((f.background_MW + f[f"farm_{farm}_MW"]) * 0.5).to_numpy().reshape(nd, SLOTS)
    D = (f.demand_MW * 0.5).to_numpy().reshape(nd, SLOTS)
    p = f.price.to_numpy().reshape(nd, SLOTS)
    dates = f.date.to_numpy().reshape(nd, SLOTS)[:, 0]
    ts = pd.to_datetime(dates)
    years_equiv = float(sum(1 / (366 if t.is_leap_year else 365) for t in ts))
    h = next(x for x in cfg["electrolysers"] if x["id"] == "itm-neptune-v")
    c = h["comparable"]
    r = cfg["r"]
    crf = r / (1 - (1 + r) ** -h["life"])
    pv = c["capital_GBP"] + sum(c["replacement_GBP"] / (1 + r) ** y for y in c["replacement_years"])
    return Site(G=G, D=D, p=p, dates=dates, year=ts.year.to_numpy(), years_equiv=years_equiv,
                w=cfg["netback"] / h["kWh_kg"] * 1000, e=h["MW"] * 0.5, kwh_per_kg=h["kWh_kg"], kg_per_hour=h["kg_hour"],
                module_mw=h["MW"], capital=c["capital_GBP"], fixed_om=c["fom_GBP"], annual=crf * pv + c["fom_GBP"],
                netback=cfg["netback"])


# ----------------------------------------------------------------------------------------------------------------------
# Energy available to the electrolyser under each policy
# ----------------------------------------------------------------------------------------------------------------------
def reference(site: Site, policy: str) -> dict:
    """Direct sales with no additions. A sells up to demand at non-negative prices; B always serves demand first."""
    q = np.minimum(site.G, site.D)
    if policy == "A":
        q = q * (site.p >= 0)
    return dict(q=q, free=site.G - q, served_pct=100 * q.sum() / site.D.sum(),
                unused_gwh=(site.G - q).sum() / 1000 / site.years_equiv, receipts=(site.p * q).sum() / site.years_equiv)


def _fill(free_inc, paid_inc, paid_profit, room):
    """Fill `room` MWh per day with free increments first, then paid increments in order of profit. Returns MWh used."""
    free_tot = free_inc.sum(1)
    use_free = np.minimum(free_tot, room)
    share = np.divide(use_free, free_tot, out=np.zeros_like(use_free), where=free_tot > 0)
    x_free = free_inc * share[:, None]
    left = room - use_free
    order = np.argsort(-paid_profit, axis=1, kind="stable")
    inc = np.take_along_axis(np.where(paid_profit > 0, paid_inc, 0.0), order, axis=1)
    cum = np.cumsum(inc, axis=1)
    take = np.clip(left[:, None] - (cum - inc), 0, inc)
    x_paid = np.zeros_like(take)
    np.put_along_axis(x_paid, order, take, axis=1)
    return x_free, x_paid


def day_dispatch(site: Site, rule: str, alpha: float, n, cap_kg: float):
    """Best half-hour loads when `n` modules (scalar or one value per day) are online for the whole UTC day.

    rule 'A'  economic dispatch: energy without a buyer is free, saleable energy costs its price.
    rule 'B'  supply priority: only energy left after demand; every half-hour must cover minimum load.
    rule 'B1' supply priority with a minimum-load reserve: energy left after demand, plus saleable energy only to
              bring the online modules up to minimum load.
    Returns dict(h, free, paid, value, feasible), arrays per day or per half-hour.
    """
    n = np.broadcast_to(np.asarray(n, float), (site.nd,))
    lo = (alpha * n * site.e)[:, None] * np.ones((1, SLOTS))
    hi = (n * site.e)[:, None] * np.ones((1, SLOTS))
    cap_mwh = cap_kg * site.kwh_per_kg / 1000
    room = cap_mwh - lo.sum(1)
    feasible = room >= -1e-9
    if rule == "A":
        free = reference(site, "A")["free"]
        cost = np.maximum(site.p, 0)
        base_free = np.minimum(free, lo)
        base_paid = lo - base_free
        top = np.minimum(np.maximum(free, lo), hi)
        x_free, x_paid = _fill(top - lo, hi - top, site.w - cost, np.maximum(room, 0))
    elif rule in ("B", "B1"):
        free = reference(site, "B")["free"]
        cost = site.p
        base_free = np.minimum(free, lo)
        base_paid = lo - base_free
        if rule == "B":
            feasible = feasible & (base_paid.max(1) <= 1e-9)
        top = np.minimum(np.maximum(free, lo), hi)
        x_free, x_paid = _fill(top - lo, np.zeros_like(lo), np.zeros_like(lo), np.maximum(room, 0))
    else:
        raise ValueError(rule)
    f_use = base_free + x_free
    p_use = base_paid + x_paid
    h = f_use + p_use
    value = site.w * h.sum(1) - (cost * p_use).sum(1)
    value = np.where(feasible, value, -np.inf)
    value = np.where(n == 0, 0.0, value)
    return dict(h=h, free=f_use, paid=p_use, value=value, feasible=feasible | (n == 0), cost=cost)


def flexible_dispatch(site: Site, policy: str, alpha: float, modules: int, cap_kg: float):
    """Half-hour switching as in report v5: any number of the installed modules may be online in each half-hour."""
    cap_mwh = cap_kg * site.kwh_per_kg / 1000
    hi = np.full((site.nd, SLOTS), modules * site.e)
    room = np.full(site.nd, cap_mwh)
    if policy == "A":
        free = reference(site, "A")["free"]
        cost = np.maximum(site.p, 0)
        top = np.minimum(free, hi)
        x_free, x_paid = _fill(top, hi - top, site.w - cost, room)
    else:
        free = reference(site, "B")["free"]
        cost = site.p
        top = np.minimum(free, hi)
        x_free, x_paid = _fill(top, np.zeros_like(top), np.zeros_like(top), room)
    h = x_free + x_paid
    # A load below one module's minimum cannot be run: drop it (a lower bound; the count is reported).
    small = (h > 1e-9) & (h < alpha * site.e - 1e-9)
    dropped = int(small.sum())
    x_free = np.where(small, 0, x_free)
    x_paid = np.where(small, 0, x_paid)
    h = x_free + x_paid
    value = site.w * h.sum(1) - (cost * x_paid).sum(1)
    return dict(h=h, free=x_free, paid=x_paid, value=value, cost=cost, dropped=dropped)


# ----------------------------------------------------------------------------------------------------------------------
# Commitment with a minimum run
# ----------------------------------------------------------------------------------------------------------------------
def value_table(site: Site, rule: str, alpha: float, modules: int, cap_kg: float) -> np.ndarray:
    """V[d, k]: best operating value of day d with k modules online all day (minus infinity if not possible)."""
    return np.column_stack([day_dispatch(site, rule, alpha, k, cap_kg)["value"] for k in range(modules + 1)])


def commit(V: np.ndarray, min_days: int, time_limit=600.0, gap=1e-9):
    """Number of modules online each day maximising total value, each start followed by at least `min_days` days.

    All modules are off before the first day, and no module may start so late that its minimum run would end after
    the last day. Returns (path, info).
    """
    nd, K = V.shape
    ok = np.isfinite(V)
    if min_days <= 1:
        path = np.argmax(np.where(ok, V, -np.inf), axis=1)
        return path, dict(status="closed form", objective=float(V[np.arange(nd), path].sum()), gap=0.0)
    nx = nd * K
    xi = lambda d, k: d * K + k
    vi = lambda d: nx + d
    nvar = nx + nd
    c = np.zeros(nvar)
    c[:nx] = -np.where(ok, V, 0.0).ravel()
    lb = np.zeros(nvar)
    ub = np.ones(nvar)
    ub[:nx] = ok.ravel().astype(float)
    ub[nx:] = K - 1
    ub[nx + max(nd - min_days + 1, 0):] = 0          # a start must be able to finish its run
    rows, cols, vals, lo, hi = [], [], [], [], []
    r = 0
    kk = np.arange(K)
    for d in range(nd):                               # exactly one level per day
        rows += [r] * K; cols += [xi(d, k) for k in kk]; vals += [1.0] * K; lo.append(1); hi.append(1); r += 1
    for d in range(nd):                               # starts >= increase in modules online
        rows += [r] * K; cols += [xi(d, k) for k in kk]; vals += list(kk.astype(float))
        if d > 0:
            rows += [r] * K; cols += [xi(d - 1, k) for k in kk]; vals += list(-kk.astype(float))
        rows.append(r); cols.append(vi(d)); vals.append(-1.0); lo.append(-np.inf); hi.append(0); r += 1
    for d in range(nd):                               # modules started in the last min_days days are still on
        a = max(0, d - min_days + 1)
        for t in range(a, d + 1):
            rows.append(r); cols.append(vi(t)); vals.append(1.0)
        rows += [r] * K; cols += [xi(d, k) for k in kk]; vals += list(-kk.astype(float)); lo.append(-np.inf); hi.append(0); r += 1
    A = coo_matrix((vals, (rows, cols)), shape=(r, nvar)).tocsr()
    integrality = np.zeros(nvar); integrality[:nx] = 1
    res = milp(c, constraints=LinearConstraint(A, lo, hi), bounds=Bounds(lb, ub), integrality=integrality,
               options=dict(time_limit=time_limit, mip_rel_gap=gap, disp=False))
    if res.x is None:
        raise RuntimeError(res.message)
    path = np.rint(res.x[:nx].reshape(nd, K)).argmax(1)
    obj = float(V[np.arange(nd), path].sum())
    bound = -float(res.mip_dual_bound) if getattr(res, "mip_dual_bound", None) is not None else np.nan
    return path, dict(status=res.message, objective=obj, bound=bound, gap=(bound - obj) if np.isfinite(bound) else np.nan)


def check_path(path: np.ndarray, min_days: int, feasible: np.ndarray) -> list[str]:
    """Independent check of a commitment path: first-in-first-out stopping and the minimum run of every start."""
    out = []
    if not feasible[np.arange(len(path)), path].all():
        out.append("a day uses a module count that is not feasible")
    ages: list[int] = []                               # days online of each running module, oldest first
    for d, n in enumerate(path):
        ages = [a + 1 for a in ages]
        while len(ages) > n:
            if ages[0] - 1 < min_days:
                out.append(f"day {d}: a module stops after {ages[0] - 1} days")
            ages.pop(0)
        while len(ages) < n:
            ages.append(1)
            if d + min_days > len(path):
                out.append(f"day {d}: a start cannot finish its run")
    return out


# ----------------------------------------------------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------------------------------------------------
def metrics(site: Site, policy: str, disp: dict, modules: int, cap_kg: float, path=None, label="", extra=None) -> dict:
    ref = reference(site, policy)
    Y = site.years_equiv
    h, free, paid = disp["h"], disp["free"], disp["paid"]
    kg_day = h.sum(1) * 1000 / site.kwh_per_kg
    value = site.w * h.sum(1) - (disp["cost"] * paid).sum(1)
    gross = value.sum() / Y
    equip = modules * site.annual
    by_year = {}
    for y in np.unique(site.year):
        m = site.year == y
        by_year[int(y)] = value[m].sum() - equip
    sales = ref["q"] - paid
    cap = modules * site.capital
    op = gross - modules * site.fixed_om
    row = dict(label=label, policy=policy, modules=modules, mw=modules * site.module_mw, h2_price=site.netback,
               capital_m=cap / 1e6, equipment_m=equip / 1e6, gross_m=gross / 1e6, net_m=(gross - equip) / 1e6,
               payback_years=(cap / op) if op > 0 and modules else np.nan,
               h2_t_per_year=kg_day.sum() / 1000 / Y, input_gwh=h.sum() / 1000 / Y,
               from_unsold_gwh=free.sum() / 1000 / Y, diverted_gwh=paid.sum() / 1000 / Y,
               share_from_unsold_pct=100 * free.sum() / h.sum() if h.sum() > 0 else np.nan,
               served_pct=100 * sales.sum() / site.D.sum(), served_change_pp=100 * sales.sum() / site.D.sum() - ref["served_pct"],
               unused_gwh=ref["unused_gwh"] - free.sum() / 1000 / Y,
               days_at_95pct_cap_pct=100 * (kg_day >= 0.95 * cap_kg).mean(), zero_days=int((kg_day < 1e-6).sum()),
               worst_year_m=min(by_year.values()) / 1e6, best_year_m=max(by_year.values()) / 1e6,
               loss_years=sum(v < 0 for v in by_year.values()))
    if path is not None:
        starts = np.maximum(np.diff(np.r_[0, path]), 0).sum()
        row.update(module_starts=int(starts), mean_online=float(path.mean()), days_any_online_pct=100 * float((path > 0).mean()))
    row.update({f"net_{y}_m": v / 1e6 for y, v in by_year.items()})
    if extra:
        row.update(extra)
    return row


def solve_case(site: Site, rule: str, alpha: float, modules: int, min_days: int, cap_kg: float, label=""):
    """Day-boundary commitment with a minimum run for a fixed number of installed modules."""
    policy = "A" if rule == "A" else "B"
    V = value_table(site, rule, alpha, modules, cap_kg)
    path, info = commit(V, min_days)
    problems = check_path(path, min_days, np.isfinite(V))
    disp = day_dispatch(site, rule, alpha, path, cap_kg)
    assert np.allclose(disp["value"].sum(), info["objective"], rtol=1e-9, atol=1e-3)
    lo = alpha * path[:, None] * site.e
    assert (disp["h"] >= lo - 1e-7).all() and (disp["h"] <= path[:, None] * site.e + 1e-7).all()
    assert (disp["h"].sum(1) * 1000 / site.kwh_per_kg <= cap_kg + 1e-4).all()
    row = metrics(site, policy, disp, modules, cap_kg, path, label,
                  dict(rule=rule, min_load_pct=100 * alpha, min_run_days=min_days, solver=info["status"],
                       bound_gap_gbp_per_year=(info.get("gap", 0.0) or 0.0) / site.years_equiv, path_problems=len(problems)))
    return row, path, disp
