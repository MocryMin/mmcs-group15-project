"""Shared data, cost and solver helpers for the Tier 2A / Tier 2B models (MMCS Group 15).

Conventions follow the group's Tier 1 v6 study so that results are comparable:
  * repaired daily panel (data/), study window 2020-2025 (2,192 days);
  * G_t = national generation + the client's simulated wind farm, D_t = national demand
    (the daily limit on electricity sales), both converted from mean MW to GWh/day;
  * prices deflated to 2020 pounds with monthly CPI (2020 average = 108.7);
  * 5% real discount rate, annualised (annuity) equipment costs, money in GBP2020.
Policies:  A = economic dispatch (electricity goes wherever it earns most);
           B = supply first (current generation serves demand before anything else).
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RATE = 0.05                       # real discount rate (Tier 1 v6)
H2_NETBACK = 7.7990270551508845   # GBP2020 per kg delivered (Tier 1 v6 research value)
H2_KWH_PER_KG = 55.9              # project brief
H2_CAP_KG_DAY = 10_000.0          # illustrative client-scale offtake limit used in the Tier 1 report
CPI_2020 = 108.7
CPI_ANNUAL = {2020: 108.7, 2021: 111.6, 2022: 121.7, 2023: 130.5, 2024: 133.9, 2025: 138.4}


def crf(rate: float, years: float) -> float:
    return rate / (1 - (1 + rate) ** -years)


# Electrolyser: Tier 1 v6 'comparable' cost basis per MW of AC input (ITM NEPTUNE V figures).
EL_CAPEX_PER_MW = 1_460_439.72
EL_FOM_PER_MW = 25_861.65
EL_STACK_PER_MW = 489_609.26      # stack renewals in years 11 and 22
EL_LIFE = 30
EL_PV_PER_MW = EL_CAPEX_PER_MW + EL_STACK_PER_MW * ((1 + RATE) ** -11 + (1 + RATE) ** -22)
EL_ANNUAL_PER_MW = crf(RATE, EL_LIFE) * EL_PV_PER_MW + EL_FOM_PER_MW

# Battery: Tesla Megapack 2XL 2h figures from Tier 1 v6, per MWh of nameplate energy.
BAT_CAPEX_PER_MWH = 1_239_439.63 / 3.8544
BAT_FOM_PER_MWH = 30_985.99 / 3.8544
BAT_LIFE = 15
BAT_RTE = 0.92
BAT_USABLE = 0.60                 # 20%-80% state-of-charge window
BAT_ANNUAL_PER_MWH = crf(RATE, BAT_LIFE) * BAT_CAPEX_PER_MWH + BAT_FOM_PER_MWH

# Hydrogen buffer store: DEA 200 bar Type I steel tank system (group research 2026-11-11), per usable kg.
TANK_USABLE_KG = 387.94
TANK_CAPEX_PER_KG = 900_603 / TANK_USABLE_KG
TANK_FOM_PER_KG = 7_805 / TANK_USABLE_KG
TANK_LIFE = 25
TANK_ANNUAL_PER_KG = crf(RATE, TANK_LIFE) * TANK_CAPEX_PER_KG + TANK_FOM_PER_KG
TANK_COMPRESSION_KWH_PER_KG = 1.5


def load_panel(start="2020-01-01", end="2025-12-31") -> pd.DataFrame:
    """Daily panel: g, d (GWh/day), price (GBP2020/MWh), farm and fuel series (mean MW)."""
    def daily(name, col="date"):
        f = pd.read_csv(DATA / name)
        f.index = pd.to_datetime(f.pop(col), utc=True).dt.tz_localize(None)
        return f.sort_index()
    gen = daily("daily_generation_total.csv").total_MW
    farm = daily("wind_farm_generation.csv").wind_farm_MW
    dem = daily("daily_demand.csv", "startTime").demand
    price = daily("daily_market_index_price.csv").iloc[:, 0]
    fuel = pd.read_csv(DATA / "daily_generation_by_fuel.csv", parse_dates=["date"]).pivot(index="date", columns="psrType", values="MW")
    cpi = {}
    with (DATA / "CPI.csv").open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.reader(fh):
            try:
                cpi[pd.to_datetime(row[0], format="%Y %b").strftime("%Y-%m")] = float(row[1])
            except (ValueError, IndexError):
                pass
    idx = gen.index
    real = price.to_numpy() * CPI_2020 / np.array([cpi[t.strftime("%Y-%m")] for t in idx])
    df = pd.DataFrame({"g": (gen + farm.reindex(idx)) * 0.024, "d": dem.reindex(idx) * 0.024, "price": real,
                       "farm_MW": farm.reindex(idx), "onshore_MW": fuel["Wind Onshore"].reindex(idx),
                       "solar_MW": fuel["Solar"].reindex(idx)}, index=idx)
    df = df.loc[start:end]
    assert np.isfinite(df).all().all()
    return df


def years_in(df: pd.DataFrame) -> float:
    return float(np.sum(1 / np.where(df.index.is_leap_year, 366, 365)))


class LP:
    """Tiny sparse LP builder (maximisation). Solved with HiGHS via SciPy by default.

    solver='xpress' builds the identical model through the FICO Xpress Python API. That branch could
    not be executed in the environment where this file was written (no Xpress licence there), so run
    `python tier2a.py --solver xpress --check` once on a licensed machine before relying on it.
    """
    def __init__(self):
        self.c, self.lb, self.ub = [], [], []
        self.r, self.k, self.v, self.lo, self.hi = [], [], [], [], []
        self.nrow = 0

    def var(self, n=1, lb=0.0, ub=np.inf, c=0.0):
        start = len(self.c)
        for arr, val in ((self.c, c), (self.lb, lb), (self.ub, ub)):
            arr.extend(np.broadcast_to(np.asarray(val, float), (n,)).tolist())
        return np.arange(start, start + n)

    def row(self, cols, vals, lo=-np.inf, hi=np.inf):
        self.r.extend([self.nrow] * len(cols)); self.k.extend(cols); self.v.extend(vals)
        self.lo.append(lo); self.hi.append(hi); self.nrow += 1

    def rows(self, cols2d, vals2d, lo=-np.inf, hi=np.inf):
        """Add len(cols2d) rows at once; cols2d/vals2d are (nrows, nterms) arrays."""
        cols2d, vals2d = np.asarray(cols2d), np.asarray(vals2d, float)
        n, m = cols2d.shape
        self.r.extend(np.repeat(np.arange(self.nrow, self.nrow + n), m).tolist())
        self.k.extend(cols2d.ravel().tolist()); self.v.extend(vals2d.ravel().tolist())
        self.lo.extend(np.broadcast_to(np.asarray(lo, float), (n,)).tolist())
        self.hi.extend(np.broadcast_to(np.asarray(hi, float), (n,)).tolist()); self.nrow += n

    def solve(self, solver="highs"):
        c = np.asarray(self.c)
        A = coo_matrix((self.v, (self.r, self.k)), shape=(self.nrow, len(c))).tocsr()
        lo, hi = np.asarray(self.lo), np.asarray(self.hi)
        if solver == "xpress":
            return self._solve_xpress(c, A, lo, hi)
        eq = lo == hi
        ub_rows, lb_rows = np.isfinite(hi) & ~eq, np.isfinite(lo) & ~eq
        from scipy.sparse import vstack
        A_ub = vstack([A[ub_rows], -A[lb_rows]]) if (ub_rows.any() or lb_rows.any()) else None
        b_ub = np.concatenate([hi[ub_rows], -lo[lb_rows]]) if A_ub is not None else None
        res = linprog(-c, A_ub=A_ub, b_ub=b_ub, A_eq=A[eq] if eq.any() else None, b_eq=hi[eq] if eq.any() else None,
                      bounds=list(zip(self.lb, [None if not np.isfinite(u) else u for u in self.ub])), method="highs")
        if res.status != 0:
            raise RuntimeError(f"LP not solved: {res.message}")
        return res.x, -res.fun

    def _solve_xpress(self, c, A, lo, hi):
        import xpress as xp
        m = xp.problem()
        x = [m.addVariable(lb=float(l), ub=float(u) if np.isfinite(u) else xp.infinity) for l, u in zip(self.lb, self.ub)]
        A = A.tocsr()
        for i in range(A.shape[0]):
            s, e = A.indptr[i], A.indptr[i + 1]
            expr = xp.Sum(float(A.data[j]) * x[A.indices[j]] for j in range(s, e))
            if lo[i] == hi[i]:
                m.addConstraint(expr == float(hi[i]))
            else:
                if np.isfinite(hi[i]): m.addConstraint(expr <= float(hi[i]))
                if np.isfinite(lo[i]): m.addConstraint(expr >= float(lo[i]))
        m.setObjective(xp.Sum(float(c[j]) * x[j] for j in np.flatnonzero(c)), sense=xp.maximize)
        m.setControl("outputlog", 0)
        (m.optimize if hasattr(m, "optimize") else m.solve)()
        sol = np.asarray(m.getSolution(x), float)
        return sol, float(c @ sol)


# ---------------------------------------------------------------- chart style (shared)
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"


def style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "text.color": INK,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
        "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
        "axes.axisbelow": True, "ytick.major.size": 0, "lines.linewidth": 2, "legend.frameon": False})
    return plt
