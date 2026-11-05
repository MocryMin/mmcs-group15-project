"""Tier 1 daily energy-pool MILP for the Group 15 project (independent CU build).

Policy A: economic allocation of each day's generation among direct sale, battery
charge, electrolyser input and unused energy.
Policy B: current generation serves current demand first (q = min(G, D)); the rest
may be stored or converted.

All money is GBP2020. Energy is GWh/day. The objective is annual-equivalent net
profit in GBP2020/year. The model is intentionally the "simplified time" Tier 1
form: one usable battery window per day with an annual energy balance, plus a
chronological cross-check variant available separately.
"""
import csv, io, json, math, pathlib

import xpress as xp

try:  # silence the licence-location warning; harmless if the file is absent
    xp.init("C:/xpressmp/bin/xpauth.xpr")
except Exception:
    pass

DEBUG_PROBLEM = False

PKG = pathlib.Path(__file__).resolve().parents[1]
DATA = PKG / "data"

DEFAULTS = {

    # battery: 2-hour reference module, 1.5 MW / 3 MWh, 20-80% usable window
    "battery_unit_MWh": 3.0,
    "battery_unit_MW": 1.5,
    "battery_cost_GBP2020_MWh": 256234.7766536928,
    "battery_FOM_GBP2020_MWyr": 14861.617045914183,
    "battery_life_years": 15,
    "battery_rte": 0.9,
    "battery_window": 0.6,
    # electrolyser: 20 MW PEM module, 20-100% of 24 h, 55.9 kWh/kg
    "h2_module_MW": 20.0,
    "h2_kWh_per_kg": 55.9,
    "h2_min_fraction": 0.2,
    "h2_cost_GBP2020_MW": 1460439.721736966,
    "h2_FOM_GBP2020_MWyr": 25861.652951699458,
    "h2_stack_GBP2020_MW": 489609.26404293376,
    "h2_stack_years": (11, 22),
    "h2_life_years": 30,
    # market and finance
    "h2_price_GBP2020_kg": 7.7990270551508845,
    "h2_limit_kg_day": 10000.0,
    "rate": 0.05,
    "commission_price_GBP2020_MWh": 78.1261430580068,
    # bounds (far above any economic size; only numerical safety)
    "max_battery_units": 200,
    "max_h2_modules": 50,
}


def crf(rate, years):
    if rate == 0:
        return 1.0 / years
    return rate / (1.0 - (1.0 + rate) ** -years)


def sample_years(frame):
    """1.0 for a complete calendar year (365/366 days), else days/365."""
    import calendar
    years = {r["date"][:4] for r in frame}
    if len(years) == 1:
        y = int(next(iter(years)))
        if len(frame) == (366 if calendar.isleap(y) else 365):
            return 1.0
    return len(frame) / 365.0


def load_frame(year=None, strict_only=False, old_price=False, no_wind=False):
    """Return a list of daily dicts (date, G, D, p, renewable, other, strict)."""
    rows = []
    with io.open(DATA / "daily_model_inputs.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            d = {
                "date": r["date"],
                "G": float(r["G_GWh"]),
                "D": float(r["D_GWh"]),
                "p": float(r["price_GBP2020_MWh"]),
                "p_nominal": float(r["price_nominal_GBP_MWh"]),
                "renewable": float(r["renewable_GWh"]),
                "other": float(r["other_GWh"]),
                "wind_farm": float(r["wind_farm_GWh"]),
                "strict": int(r["strict_no_imputation"]),
            }
            rows.append(d)
    if year is not None:
        rows = [r for r in rows if r["date"].startswith(str(year))]
    if strict_only:
        rows = [r for r in rows if r["strict"] == 1]
    if no_wind:
        for r in rows:
            r["G"] -= r["wind_farm"]
            r["renewable"] -= r["wind_farm"]
            r["wind_farm"] = 0.0
    if old_price:
        # course-original wholesale price, same deflator, on the same dates
        import subprocess
        # read the original file from the package's parent repository
        repo = PKG
        while not (repo / "PROJECT.md").exists():
            repo = repo.parent
        old = {}
        with io.open(repo / "daily_market_index_price.csv", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                old[r["date"]] = float(r["avg_price_£_per_MWh"])
        for r in rows:
            r["p"] = old[r["date"]] * 108.7 / monthly_cpi(r["date"])
    return rows


_CPI = None


def monthly_cpi(date):
    global _CPI
    if _CPI is None:
        _CPI = {}
        months = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
                  "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}
        with io.open(DATA / "daily_model_inputs.csv", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                _CPI[r["date"]] = float(r["cpi_month"])
    return _CPI[date]


def annual_costs(cfg, n_b, n_h):
    r = cfg["rate"]
    cap_b = crf(r, cfg["battery_life_years"]) * cfg["battery_cost_GBP2020_MWh"] * cfg["battery_unit_MWh"] * n_b
    fom_b = cfg["battery_FOM_GBP2020_MWyr"] * cfg["battery_unit_MW"] * n_b
    comm = cfg["commission_price_GBP2020_MWh"] * 0.2 * cfg["battery_unit_MWh"] * n_b
    cap_h = crf(r, cfg["h2_life_years"]) * cfg["h2_cost_GBP2020_MW"] * cfg["h2_module_MW"] * n_h
    fom_h = cfg["h2_FOM_GBP2020_MWyr"] * cfg["h2_module_MW"] * n_h
    stack_annual = crf(r, cfg["h2_life_years"]) * cfg["h2_stack_GBP2020_MW"] * cfg["h2_module_MW"] * n_h * sum(
        1.0 / (1.0 + r) ** y for y in cfg["h2_stack_years"])
    return {
        "battery_capital": cap_b, "battery_fom": fom_b, "battery_commission": comm,
        "h2_capital": cap_h, "h2_fom": fom_h, "h2_stack_annual": stack_annual,
        "total": cap_b + fom_b + comm + cap_h + fom_h + stack_annual,
        "capex_battery": cfg["battery_cost_GBP2020_MWh"] * cfg["battery_unit_MWh"] * n_b,
        "capex_h2": cfg["h2_cost_GBP2020_MW"] * cfg["h2_module_MW"] * n_h,
    }


def solve(frame, policy="A", cfg=None, fixed=None, supply_min=None):
    """Solve one case. frame: list of daily dicts; cfg overrides DEFAULTS."""
    cfg = {**DEFAULTS, **(cfg or {})}
    n = len(frame)
    if n == 0:
        raise ValueError("empty frame")
    yt = sample_years(frame)
    eta = math.sqrt(cfg["battery_rte"])
    c_unit = cfg["battery_window"] * cfg["battery_unit_MWh"] / (1000.0 * eta)      # GWh/day per unit
    d_unit = eta * cfg["battery_window"] * cfg["battery_unit_MWh"] / 1000.0        # GWh/day per unit
    h_max_unit = 24.0 * cfg["h2_module_MW"] / 1000.0                               # GWh/day per module
    h_min_unit = cfg["h2_min_fraction"] * h_max_unit
    h_cap_kg = cfg["h2_limit_kg_day"] * cfg["h2_kWh_per_kg"] / 1e6                 # GWh/day

    p = xp.problem()
    p.controls.outputlog = 0
    p.controls.timelimit = 120
    p.controls.threads = 4
    p.controls.miprelstop = 0.0
    p.controls.mipabsstop = 0.0

    if policy == "B":
        q = [p.addVariable(lb=min(r["G"], r["D"]), ub=min(r["G"], r["D"]), name=f"q_{i}") for i, r in enumerate(frame)]
    else:
        q = [p.addVariable(lb=0.0, ub=r["D"], name=f"q_{i}") for i, r in enumerate(frame)]
    c = [p.addVariable(lb=0.0, name=f"c_{i}") for i in range(n)]
    dd = [p.addVariable(lb=0.0, name=f"d_{i}") for i in range(n)]
    h_ub = h_max_unit * cfg["max_h2_modules"] if h_cap_kg is None else min(h_cap_kg, h_max_unit * cfg["max_h2_modules"])
    h = [p.addVariable(lb=0.0, ub=h_ub, name=f"h_{i}") for i in range(n)]
    u = [p.addVariable(lb=0.0, name=f"u_{i}") for i in range(n)]
    z = [p.addVariable(lb=0.0, ub=cfg["max_h2_modules"], vartype=xp.integer, name=f"z_{i}") for i in range(n)]
    nb = p.addVariable(lb=0.0, ub=cfg["max_battery_units"], vartype=xp.integer, name="n_b")
    nh = p.addVariable(lb=0.0, ub=cfg["max_h2_modules"], vartype=xp.integer, name="n_h")

    if fixed is not None:
        p.addConstraint(nb == fixed[0])
        p.addConstraint(nh == fixed[1])

    for i, r in enumerate(frame):
        p.addConstraint(q[i] + c[i] + h[i] + u[i] == r["G"])
        p.addConstraint(q[i] + dd[i] <= r["D"])
        p.addConstraint(c[i] - c_unit * nb <= 0)
        p.addConstraint(dd[i] - d_unit * nb <= 0)
        p.addConstraint(h[i] - h_max_unit * z[i] <= 0)
        p.addConstraint(h[i] - h_min_unit * z[i] >= 0)
        p.addConstraint(z[i] - nh <= 0)
        if policy == "B":
            pass

    p.addConstraint(xp.Sum(dd) - eta * eta * xp.Sum(c) == 0)
    if supply_min is not None:
        p.addConstraint(xp.Sum(q) + xp.Sum(dd) >= supply_min)

    obj = (xp.Sum([(r["p"] * (q[i] + dd[i]) / 1000.0) + cfg["h2_price_GBP2020_kg"] * h[i] / cfg["h2_kWh_per_kg"]
                   for i, r in enumerate(frame)]) / yt
           - (crf(cfg["rate"], cfg["battery_life_years"]) * cfg["battery_cost_GBP2020_MWh"] * cfg["battery_unit_MWh"]
              + cfg["battery_FOM_GBP2020_MWyr"] * cfg["battery_unit_MW"]
              + cfg["commission_price_GBP2020_MWh"] * 0.2 * cfg["battery_unit_MWh"]) * nb / 1e6
           - (crf(cfg["rate"], cfg["h2_life_years"]) * cfg["h2_cost_GBP2020_MW"] * cfg["h2_module_MW"]
              + cfg["h2_FOM_GBP2020_MWyr"] * cfg["h2_module_MW"]
              + crf(cfg["rate"], cfg["h2_life_years"]) * cfg["h2_stack_GBP2020_MW"] * cfg["h2_module_MW"]
              * sum(1.0 / (1.0 + cfg["rate"]) ** y for y in cfg["h2_stack_years"])) * nh / 1e6)
    p.setObjective(obj, sense=xp.maximize)
    p.solve()

    sol = p.getSolution()
    vals = sol[:6 * n + 2]
    qs, cs, ds = vals[0:n], vals[n:2 * n], vals[2 * n:3 * n]
    hs, us, zs = vals[3 * n:4 * n], vals[4 * n:5 * n], vals[5 * n:6 * n]
    n_b = int(round(vals[6 * n]))
    n_h = int(round(vals[6 * n + 1]))
    cost = annual_costs(cfg, n_b, n_h)
    rev_elec = sum(frame[i]["p"] * (qs[i] + ds[i]) / 1000.0 for i in range(n)) / yt
    rev_h2 = sum(cfg["h2_price_GBP2020_kg"] * hs[i] / cfg["h2_kWh_per_kg"] for i in range(n)) / yt
    status = str(p.attributes.solstatus)
    out = {
        "status": status,
        "policy": policy,
        "days": n,
        "sample_years": yt,
        "n_battery_units": n_b,
        "battery_MW": n_b * cfg["battery_unit_MW"],
        "battery_MWh": n_b * cfg["battery_unit_MWh"],
        "n_h2_modules": n_h,
        "electrolyser_MW": n_h * cfg["h2_module_MW"],
        "net_profit_GBP2020_year": rev_elec + rev_h2 - cost["total"] / 1e6,
        "electricity_revenue": rev_elec,
        "hydrogen_revenue": rev_h2,
        "annual_cost": cost,
        "electricity_sold_GWh": sum(qs[i] + ds[i] for i in range(n)) / yt,
        "direct_sale_GWh": sum(qs) / yt,
        "battery_discharge_GWh": sum(ds) / yt,
        "charge_GWh": sum(cs) / yt,
        "h2_input_GWh": sum(hs) / yt,
        "unused_GWh": sum(us) / yt,
        "hydrogen_kg": sum(hs) * 1e6 / cfg["h2_kWh_per_kg"] / yt,
        "demand_coverage": sum(qs[i] + ds[i] for i in range(n)) / sum(r["D"] for r in frame),
        "max_violation": max(abs(qs[i] + cs[i] + hs[i] + us[i] - frame[i]["G"]) for i in range(n)),
        "plan": [{
            "date": frame[i]["date"], "G": frame[i]["G"], "D": frame[i]["D"], "price": frame[i]["p"],
            "q": qs[i], "c": cs[i], "d": ds[i], "h": hs[i], "u": us[i], "z": int(round(zs[i])),
            "renewable": frame[i]["renewable"], "other": frame[i]["other"],
        } for i in range(n)],
        "cfg": {k: cfg[k] for k in ("rate", "battery_cost_GBP2020_MWh", "h2_cost_GBP2020_MW",
                                    "h2_price_GBP2020_kg", "h2_limit_kg_day", "battery_FOM_GBP2020_MWyr")},
    }
    if DEBUG_PROBLEM:
        out["_p"] = p
        out["_vars"] = (q, c, dd, h, u, z, nb, nh)
    return out


def base_profit(frame, policy="A", cfg=None):
    """No-investment comparator on the same frame and policy."""
    cfg = {**DEFAULTS, **(cfg or {})}
    n = len(frame)
    yt = sample_years(frame)
    if policy == "B":
        return sum(r["p"] * min(r["G"], r["D"]) for r in frame) / yt / 1000.0
    return sum(r["p"] * (min(r["G"], r["D"]) if r["p"] > 0 else 0.0) for r in frame) / yt / 1000.0


def simple_rule(frame, cfg=None, n_h=1, n_b=0):
    """Rule-based dispatch: sell min(G,D) first, then hydrogen, then charge; no
    interday optimisation and no battery discharge beyond same-day surplus."""
    cfg = {**DEFAULTS, **(cfg or {})}
    n = len(frame)
    yt = sample_years(frame)
    h_max = 24.0 * cfg["h2_module_MW"] * n_h / 1000.0
    h_cap = cfg["h2_limit_kg_day"] * cfg["h2_kWh_per_kg"] / 1e6
    rev_e = rev_h = h_tot = u_tot = 0.0
    for r in frame:
        sell = min(r["G"], r["D"])
        rem = r["G"] - sell
        hh = min(rem, h_max, h_cap)
        u = rem - hh
        rev_e += r["p"] * sell / 1000.0
        rev_h += cfg["h2_price_GBP2020_kg"] * hh / cfg["h2_kWh_per_kg"]
        h_tot += hh
        u_tot += u
    cost = annual_costs(cfg, n_b, n_h)["total"] / 1e6
    return {"policy": "simple", "net_profit_GBP2020_year": (rev_e + rev_h) / yt - cost,
            "electricity_revenue_mGBP": rev_e / yt, "hydrogen_revenue_mGBP": rev_h / yt,
            "hydrogen_input_GWh": h_tot / yt, "unused_GWh": u_tot / yt,
            "electricity_sold_GWh": sum(min(r["G"], r["D"]) for r in frame) / yt,
            "hydrogen_kg": h_tot * 1e6 / cfg["h2_kWh_per_kg"] / yt,
            "demand_coverage": sum(min(r["G"], r["D"]) for r in frame) / sum(r["D"] for r in frame)}


if __name__ == "__main__":
    f23 = load_frame(2023)
    cfg = dict(DEFAULTS)
    print("frame", len(f23), "G", round(sum(r["G"] for r in f23), 3), "D", round(sum(r["D"] for r in f23), 3))
    baseA = base_profit(f23, "A", cfg)
    baseB = base_profit(f23, "B", cfg)
    print("base A/B mGBP", round(baseA, 3), round(baseB, 3))
    a0 = solve(f23, "A", cfg, fixed=(0, 0))
    print("A0", a0["status"], a0["n_battery_units"], a0["n_h2_modules"],
          round(a0["net_profit_GBP2020_year"], 3), round(a0["unused_GWh"], 3),
          round(a0["demand_coverage"], 7))
    a1 = solve(f23, "A", cfg)
    print("A opt (same as A0?)", a1["n_h2_modules"], round(a1["net_profit_GBP2020_year"], 3))
    b0 = solve(f23, "B", cfg)
    print("B0", b0["status"], b0["n_h2_modules"], round(b0["net_profit_GBP2020_year"], 3))
    b1 = solve(f23, "B", cfg, fixed=(0, 1))
    print("B fixed20", round(b1["net_profit_GBP2020_year"], 3),
          "incr", round(b1["net_profit_GBP2020_year"] - baseB, 3))
    s = simple_rule(f23, cfg, n_h=1)
    print("simple20", round(s["net_profit_GBP2020_year"], 3),
          "incr", round(s["net_profit_GBP2020_year"] - baseB, 3))
