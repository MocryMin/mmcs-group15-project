"""Local Tier 1 study. Build schedules with Xpress and audit their economics."""
import csv
import hashlib
import json
import math
import os
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
import xpress as xp

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "inputs"
OUT = ROOT / "results"
FILES = (
    "daily_generation_total.csv", "daily_generation_by_fuel.csv", "daily_demand.csv",
    "wind_farm_generation.csv", "daily_market_index_price.csv", "date_quality.csv",
)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def prepare_inputs():
    manifest = json.loads((INPUT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert set(manifest) == set(FILES) | {"CPI.csv", "parameters.json"}
    for name, item in manifest.items():
        if hashlib.sha256((INPUT / name).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Input hash differs from the frozen release: {name}")


def load_data():
    def daily(name, date="date"):
        f = pd.read_csv(INPUT / name)
        f.index = pd.to_datetime(f.pop(date), utc=True).dt.tz_localize(None)
        assert f.index.is_unique
        return f.sort_index()

    generation = daily(FILES[0]).total_MW
    wind = daily(FILES[3]).wind_farm_MW
    demand = daily(FILES[2], "startTime").demand
    prices = daily(FILES[4])
    quality = daily(FILES[5]).strict_no_imputation
    dates = pd.date_range("2020-01-01", "2026-09-17")
    assert all(x.index.equals(dates) for x in (generation, wind, demand, prices, quality))
    assert np.allclose(prices.iloc[:, 1], 24 * prices.iloc[:, 0], atol=1e-8, rtol=0)
    fuel = pd.read_csv(INPUT / FILES[1], parse_dates=["date"])
    assert not fuel.duplicated(["date", "psrType"]).any()
    assert np.allclose(fuel.groupby("date").MW.sum().reindex(dates), generation, rtol=0, atol=1e-6)
    # A conservative reporting category, including only explicitly identified wind and solar.
    renewable = fuel.loc[fuel.psrType.isin(["Wind Offshore", "Wind Onshore", "Solar"])].groupby("date").MW.sum().reindex(dates)
    assert renewable.notna().all()
    cpi = {}
    with (INPUT / "CPI.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.reader(stream):
            try:
                month = pd.to_datetime(row[0], format="%Y %b").strftime("%Y-%m")
                cpi[month] = float(row[1])
            except (ValueError, IndexError):
                continue
    p = prices.iloc[:, 0].to_numpy() * 108.7 / np.array([cpi[t.strftime("%Y-%m")] for t in dates])
    frame = pd.DataFrame(dict(g=(generation + wind) * .024, d=demand * .024, price=p,
                              wind=wind * .024, renewable=(renewable + wind) * .024,
                              strict=quality), index=dates)
    assert np.isfinite(frame).all().all()
    assert (frame[["g", "d", "wind", "renewable"]] >= 0).all().all()
    assert (frame.renewable <= frame.g).all()
    return frame


@dataclass(frozen=True)
class Economics:
    rate: float
    eta: float
    usable: float
    battery_capex: float
    battery_fom: float
    battery_commission: float
    battery_life: int
    hydrogen_capex: float
    hydrogen_fom: float
    stack: float
    stack_years: tuple
    hydrogen_life: int
    h2_unit: float
    h2_min: float
    kg_per_gwh: float
    netback: float
    offtake: float

    def annuity(self, years):
        return self.rate / (1 - (1 + self.rate) ** (-years)) if self.rate else 1 / years

    @property
    def battery_annual(self):
        return (self.battery_capex + self.battery_commission) * self.annuity(self.battery_life) + self.battery_fom

    @property
    def hydrogen_annual(self):
        pv = self.hydrogen_capex + sum(self.stack / (1 + self.rate) ** y for y in self.stack_years)
        return pv * self.annuity(self.hydrogen_life) + self.hydrogen_fom


def economics():
    p = json.loads((INPUT / "parameters.json").read_text(encoding="utf-8"))
    assert p["battery_unit_MWh"] == 3 and p["battery_unit_MW"] == 1.5
    assert p["hydrogen_unit_MW"] == 20 and p["self_discharge"] == 0
    return Economics(p["rate"], p["eta"], p["soc_window"] * 3 / 1000,
                     3 * p["battery_cost_MWh"] / 1e6, 1.5 * p["battery_FOM_MW"] / 1e6,
                     .6 / p["eta"] * p["commission_price_GBP_MWh"] / 1e6, p["battery_life"],
                     20 * p["hydrogen_cost_MW"] / 1e6, 20 * p["hydrogen_FOM_MW"] / 1e6,
                     20 * p["hydrogen_replacement_MW"] / 1e6, tuple(p["hydrogen_replacement_years"]),
                     p["hydrogen_life"], 24 * 20 / 1000, p["hydrogen_min"],
                     1e6 / p["hydrogen_kWh_kg"], p["hydrogen_price"], p["hydrogen_limit_kg"])


def year_fraction(frame):
    return float(np.sum(1 / np.where(frame.index.is_leap_year, 366, 365)))


def direct_reference(frame, policy):
    sales = np.minimum(frame.g.to_numpy(), frame.d.to_numpy())
    return np.where(frame.price >= 0, sales, 0.) if policy == "A" else sales


def solve(frame, econ, policy, battery=True, hydrogen=True, fixed=None, chronological=False,
          netback=None, offtake=None, service_floor=None):
    """Annual pool or daily-stock MILP. Quantities GWh and objective GBP2020m/year."""
    netback = econ.netback if netback is None else netback
    offtake = econ.offtake if offtake is None else offtake
    years = year_fraction(frame)
    g, d, price = (frame[column].to_numpy() for column in ("g", "d", "price"))
    maximum_h = min(float(np.max(g)), offtake / econ.kg_per_gwh)
    h_bound = math.ceil(maximum_h / econ.h2_unit) if hydrogen else 0
    # Past the largest daily transfer, annual pooling cannot use extra capacity.
    # Chronological solves in this study fix battery capacity.
    assert not chronological or fixed is not None
    b_bound = math.ceil(max(np.max(g) * econ.eta, np.max(d) / econ.eta) / econ.usable) if battery else 0
    model = xp.problem()
    model.controls.outputlog = 0
    model.controls.threads = 4
    model.controls.maxtime = 60
    model.controls.miprelstop = 1e-9
    model.controls.mipabsstop = 1e-7
    model.controls.miprelcutoff = 0.
    n_b = model.addVariable(lb=fixed[0] if fixed else 0, ub=fixed[0] if fixed else b_bound, vartype=xp.integer)
    n_h = model.addVariable(lb=fixed[1] if fixed else 0, ub=fixed[1] if fixed else h_bound, vartype=xp.integer)
    have_b = fixed[0] > 0 if fixed else battery
    have_h = fixed[1] > 0 if fixed else hydrogen and h_bound > 0
    sales, charge, discharge, h2, on, stock = ([] for _ in range(6))
    for t in range(len(frame)):
        qmax = min(g[t], d[t])
        q = model.addVariable(lb=qmax if policy == "B" else 0, ub=qmax)
        c = model.addVariable(ub=g[t]) if have_b else 0
        r = model.addVariable(ub=d[t]) if have_b else 0
        h = model.addVariable(ub=min(g[t], maximum_h)) if have_h else 0
        z = model.addVariable(ub=h_bound, vartype=xp.integer) if have_h else 0
        sales.append(q); charge.append(c); discharge.append(r); h2.append(h); on.append(z)
        if have_b or have_h:
            model.addConstraint(q + c + h <= g[t])
        if have_h:
            model.addConstraint(z <= n_h, h <= econ.h2_unit * z, h >= econ.h2_min * econ.h2_unit * z)
        if have_b:
            model.addConstraint(q + r <= d[t])
            if chronological:
                s = model.addVariable(ub=fixed[0] * econ.usable)
                previous = stock[-1] if stock else 0
                model.addConstraint(s == previous + econ.eta * c - r / econ.eta)
                stock.append(s)
            else:
                model.addConstraint(c <= econ.usable * n_b / econ.eta, r <= econ.usable * n_b * econ.eta)
    if have_b:
        if chronological:
            assert (frame.index.to_series().diff().dropna() == pd.Timedelta(days=1)).all()
            model.addConstraint(stock[-1] == 0)
        else:
            model.addConstraint(xp.Sum(discharge) == econ.eta ** 2 * xp.Sum(charge))
    if service_floor is not None:
        model.addConstraint(xp.Sum(sales) + xp.Sum(discharge) >= service_floor)
    # Subtracting the reference constant makes the solver gap informative at UK scale.
    reference_revenue = float(np.dot(price, direct_reference(frame, policy)) / (1000 * years))
    revenue = xp.Sum((price[t] / 1000 * (sales[t] + discharge[t]) +
                      netback * econ.kg_per_gwh / 1e6 * h2[t]) / years for t in range(len(frame)))
    model.setObjective(revenue - reference_revenue - econ.battery_annual * n_b - econ.hydrogen_annual * n_h, xp.maximize)
    model.solve()
    if model.attributes.solstatus != 1:
        raise RuntimeError(f"Xpress status {model.attributes.solstatus}, policy {policy}, fixed {fixed}")
    def values(variables):
        return np.array([0. if isinstance(v, int) else model.getSolution(v) for v in variables])
    q, c, r, h, z = [values(x) for x in (sales, charge, discharge, h2, on)]
    # Remove simultaneous cycles by exchanging stored output for direct sale.
    # This preserves sales, hydrogen and stock, and weakly decreases generation used.
    cancel = np.minimum(r, c * econ.eta ** 2)
    q += cancel
    r -= cancel
    c -= cancel / econ.eta ** 2
    stock_path = values(stock) if stock else np.zeros(len(frame))
    installed = [float(model.getSolution(n)) for n in (n_b, n_h)]
    assert all(abs(n - round(n)) < 1e-6 for n in installed)
    result = measure(frame, econ, policy, int(round(installed[0])), int(round(installed[1])),
                     q, c, r, h, z, stock_path, chronological, netback, offtake)
    assert abs(result[0]["net"] - model.attributes.objval) < 1e-5, (result[0], model.attributes.objval)
    if service_floor is not None:
        assert np.sum(q + r) >= service_floor - 1e-5
    result[0].update(solver="Xpress", rows=int(model.attributes.rows), columns=int(model.attributes.cols),
                     objective=float(model.attributes.objval), service_floor_GWh=service_floor)
    return result


def measure(frame, econ, policy, nb, nh, q, c, r, h, z, stock, chronology, netback, offtake):
    years = year_fraction(frame)
    g, d, p = (frame[column].to_numpy() for column in ("g", "d", "price"))
    q0 = direct_reference(frame, policy)
    unused0, unused = g - q0, g - q - c - h
    capture = np.minimum(c + h, np.maximum(g - d, 0))
    attributed_low = np.maximum(capture - (g - frame.renewable.to_numpy()), 0)
    attributed_high = np.minimum(capture, frame.renewable.to_numpy())
    errors = [max(0., -float(np.min([q, c, r, h, z, unused, d - q - r]))),
              float(np.max(c - nb * econ.usable / econ.eta)), float(np.max(r - nb * econ.usable * econ.eta)),
              float(np.max(np.minimum(c, r))), float(np.max(abs(z - np.rint(z)))), float(np.max(z - nh)),
              float(np.max(econ.h2_min * econ.h2_unit * z - h)), float(np.max(h - econ.h2_unit * z)),
              float(np.max(h - offtake / econ.kg_per_gwh)),
              float(np.max(np.abs(c + h - ((unused0 - unused) + (q0 - q)))))]
    if policy == "B":
        errors.append(float(np.max(abs(q - np.minimum(g, d)))))
    if chronology:
        errors.extend([abs(float(stock[-1])), -float(np.min(stock)), float(np.max(stock - nb * econ.usable)),
                       float(np.max(abs(stock - np.r_[0., stock[:-1]] - econ.eta * c + r / econ.eta)))])
    else:
        errors.append(abs(float(np.sum(r - econ.eta ** 2 * c))))
    worst = max(errors)
    assert worst < 1e-5, (policy, nb, nh, errors)
    energy = lambda a: float(np.sum(a) / years)
    direct_change = float(np.dot(p, q - q0) / (1000 * years))
    discharge_value = float(np.dot(p, r) / (1000 * years))
    hydrogen_value = energy(h) * econ.kg_per_gwh * netback / 1e6
    eac = nb * econ.battery_annual + nh * econ.hydrogen_annual
    result = dict(policy=policy, nb=nb, nh=nh, battery_MW=1.5 * nb, battery_MWh=3 * nb, h2_MW=20 * nh,
                  chronology=chronology, days=len(frame), represented_years=years,
                  price_H2=netback, offtake_kg_day=offtake, direct_change=direct_change,
                  discharge_value=discharge_value, hydrogen_value=hydrogen_value, annual_cost=eac,
                  net=direct_change + discharge_value + hydrogen_value - eac,
                  capex=nb * econ.battery_capex + nh * econ.hydrogen_capex,
                  baseline_sales_GWh=energy(q0), sales_GWh=energy(q + r), demand_GWh=energy(d),
                  demand_coverage=float(np.sum(q + r) / np.sum(d)),
                  unused_GWh=energy(unused), unused_reduction_GWh=energy(unused0 - unused),
                  displacement_GWh=energy(q0 - q), capture_GWh=energy(capture),
                  renewable_capture_low_GWh=energy(attributed_low), renewable_capture_high_GWh=energy(attributed_high),
                  charge_GWh=energy(c), discharge_GWh=energy(r), h2_GWh=energy(h),
                  h2_tonnes=energy(h) * econ.kg_per_gwh / 1000,
                  h2_utilization=0. if not nh else float(np.sum(h) / (len(frame) * nh * econ.h2_unit)),
                  max_check=worst)
    schedule = pd.DataFrame(dict(g=g, demand=d, price=p, reference_sale=q0, direct=q, charge=c,
                                 discharge=r, h2_input=h, modules=z, stock=stock, unused=unused,
                                 capture=capture, renewable_low=attributed_low, renewable_high=attributed_high), index=frame.index)
    return result, schedule


def hydrogen_enumeration(frame, econ, policy, count, netback, offtake):
    """Exact daily dispatch when no battery is installed. Check interval ends and the sale kink."""
    g, d, p = (frame[column].to_numpy() for column in ("g", "d", "price"))
    q0 = direct_reference(frame, policy)
    best = np.zeros(len(frame))
    selected = np.zeros(len(frame))
    online = np.zeros(len(frame))
    feasible_energy = g - q0 if policy == "B" else g
    for z in range(1, count + 1):
        lower = z * econ.h2_min * econ.h2_unit
        upper = np.minimum(feasible_energy, min(z * econ.h2_unit, offtake / econ.kg_per_gwh))
        feasible = upper >= lower - 1e-10
        for h in (np.full(len(frame), lower), upper, np.clip(g - d, lower, upper)):
            q = q0 if policy == "B" else np.where(p >= 0, np.minimum(g - h, d), 0.)
            gain = (q - q0) * p / 1000 + h * econ.kg_per_gwh * netback / 1e6
            choose = feasible & (gain > best + 1e-12)
            best[choose], selected[choose], online[choose] = gain[choose], h[choose], z
    return float(np.sum(best) / year_fraction(frame) - count * econ.hydrogen_annual), selected, online


def simple_hydrogen(frame, econ, policy, installed):
    q = direct_reference(frame, policy)
    h = np.zeros(len(frame))
    z = np.zeros(len(frame))
    potential = np.minimum(frame.g.to_numpy() - q, econ.offtake / econ.kg_per_gwh)
    for count in range(1, installed + 1):
        use = np.minimum(potential, count * econ.h2_unit)
        choose = (use >= count * econ.h2_min * econ.h2_unit) & (use > h)
        h[choose], z[choose] = use[choose], count
    zero = np.zeros(len(frame))
    return measure(frame, econ, policy, 0, installed, q, zero, zero, h, z, zero, False, econ.netback, econ.offtake)


def battery_bound(frame, econ, policy):
    # Removing storage leaves direct sales and electrolysis feasible. Even gifting
    # charge, the deleted discharge revenue cannot exceed this per-module bound.
    eligible = (frame.g < frame.d).to_numpy() if policy == "B" else np.ones(len(frame), dtype=bool)
    limit = econ.usable * econ.eta * float(np.sum(np.maximum(frame.price, 0) * eligible)) / (1000 * year_fraction(frame))
    return dict(free_charge_revenue_ceiling=limit, annual_cost=econ.battery_annual, ruled_out=limit < econ.battery_annual)


def crossing(frame, econ, policy, offtake):
    lo, hi = 0., 60.
    if hydrogen_enumeration(frame, econ, policy, 1, hi, offtake)[0] <= 0:
        return None
    for _ in range(42):
        midpoint = (lo + hi) / 2
        if hydrogen_enumeration(frame, econ, policy, 1, midpoint, offtake)[0] > 0:
            hi = midpoint
        else:
            lo = midpoint
    return hi


def cashflow(result, econ):
    gross_operating = result["hydrogen_value"] + result["direct_change"] + result["discharge_value"]
    annual_cash = gross_operating - econ.hydrogen_fom
    flows = [-econ.hydrogen_capex] + [annual_cash - (econ.stack if year in econ.stack_years else 0.)
                                      for year in range(1, econ.hydrogen_life + 1)]
    discounted = [v / (1 + econ.rate) ** y for y, v in enumerate(flows)]
    def payback(series):
        previous = series[0]
        for y, v in enumerate(series[1:], start=1):
            if previous < 0 <= previous + v and all(s >= -1e-9 for s in np.cumsum(series)[y:]):
                return y - 1 - previous / v
            previous += v
        return None
    npv = float(sum(discounted))
    assert abs(npv * econ.annuity(econ.hydrogen_life) - result["net"]) < 1e-8
    return dict(annual_operating_cash=annual_cash, npv=npv, simple_payback=payback(flows),
                discounted_payback=payback(discounted), cash_flows=flows, discounted_flows=discounted)


def run():
    prepare_inputs()
    OUT.mkdir(exist_ok=True)
    (OUT / "schedules").mkdir(exist_ok=True)
    if os.environ.get("XPRESS_LICENSE_FILE"):
        xp.init(os.environ["XPRESS_LICENSE_FILE"])
    data, econ = load_data(), economics()
    data.to_csv(OUT / "daily_model_inputs.csv", index_label="date")
    design = data.loc["2023"]
    results = {}

    def save(name, result):
        record, schedule = result
        results[name] = record
        schedule.to_csv(OUT / "schedules" / f"{name}.csv", index_label="date")
        print(f"{name:29s} {record['battery_MW']:6.1f} MW B  {record['h2_MW']:6.1f} MW H  {record['net']:+.5f} GBP2020m/yr", flush=True)
        return record

    for policy in ("A", "B"):
        for label, allow_b, allow_h in (("zero", False, False), ("battery", True, False),
                                         ("hydrogen", False, True), ("joint", True, True)):
            save(f"{policy}_{label}", solve(design, econ, policy, allow_b, allow_h))
        for year in range(2020, 2027):
            save(f"{policy}_fixed20_{year}", solve(data.loc[str(year)], econ, policy, fixed=(0, 1)))
        save(f"{policy}_simple20_2023", simple_hydrogen(design, econ, policy, 1))
        for modules in (1, 20):
            for chronological in (False, True):
                label = "stock" if chronological else "pool"
                save(f"{policy}_battery{modules}_{label}", solve(design, econ, policy, fixed=(modules, 0), chronological=chronological))
        save(f"{policy}_strict", solve(design[design.strict == 1], econ, policy, True, True))
        for year in (2023, 2025):
            site = data.loc[str(year)].copy()
            site.d = (site.d - (site.g - site.wind)).clip(lower=0)
            site.g = site.renewable = site.wind
            save(f"{policy}_site_fixed20_{year}", solve(site, econ, policy, fixed=(0, 1)))
            save(f"{policy}_site_joint_{year}", solve(site, econ, policy))
    for policy in ("A", "B"):
        # Retain the repaired, chronological day sequence; price uses an explicit downside.
        stress = data.loc["2025"].copy()
        save(f"{policy}_fixed20_downside", solve(stress, econ, policy, fixed=(0, 1), netback=4., offtake=5000.))
        cost_stress = replace(econ, hydrogen_capex=econ.hydrogen_capex * 1.25, rate=.08)
        save(f"{policy}_fixed20_cost_stress", solve(design, cost_stress, policy, fixed=(0, 1)))
    gap = results["A_zero"]["baseline_sales_GWh"] - results["A_joint"]["sales_GWh"]
    assert gap > 0
    for retained in (.25, .5, .75, 1.):
        floor = (results["A_zero"]["baseline_sales_GWh"] - (1 - retained) * gap) * year_fraction(design)
        save(f"A_service_{int(100 * retained)}", solve(design, econ, "A", service_floor=floor))
    # Audit the annual-pool envelope with real nonzero schedules.
    for policy in ("A", "B"):
        for modules in (1, 20):
            assert results[f"{policy}_battery{modules}_pool"]["net"] >= results[f"{policy}_battery{modules}_stock"]["net"] - 1e-7
    assert results["A_joint"]["net"] >= results["B_joint"]["net"] - 1e-7
    service_values = [results[f"A_service_{p}"]["net"] for p in (25, 50, 75, 100)]
    assert all(a >= b - 1e-6 for a, b in zip([results["A_joint"]["net"]] + service_values, service_values))

    bounds = {f"{policy}_{year}": battery_bound(data.loc[str(year)], econ, policy)
              for policy in ("A", "B") for year in (2023, 2024, 2025)}
    assert all(bounds[f"{policy}_2023"]["ruled_out"] for policy in ("A", "B"))
    grid = []
    for policy in ("A", "B"):
        for tonnes in np.arange(0, 30.01, .5):
            limit = float(tonnes * 1000)
            upper = math.ceil(min(design.g.max(), limit / econ.kg_per_gwh) / econ.h2_unit)
            for price in np.arange(0, 16.01, .25):
                margins = [hydrogen_enumeration(design, econ, policy, k, float(price), limit)[0] for k in range(upper + 1)]
                best = max(range(len(margins)), key=lambda k: (round(margins[k], 10), -k))
                grid.append(dict(policy=policy, offtake_t_day=float(tonnes), price=float(price), modules=best, gain=margins[best]))
    pd.DataFrame(grid).to_csv(OUT / "contract_grid.csv", index=False)
    grid_verification = []
    for policy in ("A", "B"):
        for price, offtake in ((4., 10000.), (8., 10000.), (14., 10000.), (10., 30000.)):
            solve_result = solve(design, econ, policy, netback=price, offtake=offtake)[0]
            enum = [row for row in grid if row["policy"] == policy and row["price"] == price and row["offtake_t_day"] * 1000 == offtake][0]
            assert abs(enum["gain"] - solve_result["net"]) < 1e-5
            assert solve_result["nb"] == 0 and solve_result["nh"] == enum["modules"]
            grid_verification.append(dict(
                policy=policy, netback_GBP_kg=price, offtake_kg_day=offtake,
                enumerated_modules=enum["modules"], xpress_modules=solve_result["nh"],
                enumeration_gain_mGBP=enum["gain"], xpress_gain_mGBP=solve_result["net"],
                absolute_difference_GBP=abs(enum["gain"] - solve_result["net"]) * 1e6))
    pd.DataFrame(grid_verification).to_csv(OUT / "contract_grid_checks.csv", index=False)
    baseline = pd.read_csv(ROOT / "references/codex-v1-cases.csv").set_index("case")
    comparisons = {}
    for name, ref in baseline.iterrows():
        difference = results[name]["net"] - ref["net"]
        assert abs(difference) < 1e-5, name
        assert results[name]["nb"] == ref["nb"] and results[name]["nh"] == ref["nh"]
        comparisons[name] = difference
    surplus = np.maximum(design.g - design.d, 0)
    positive = surplus[surplus > 1e-9]
    metadata = dict(days=len(data), design_days=len(design), strict_design_days=int(design.strict.sum()),
                    hydrogen_fixed_opex=econ.hydrogen_fom, battery_fixed_opex=econ.battery_fom,
                    surplus_days=len(positive), surplus_GWh=float(positive.sum()),
                    median_surplus_day_GWh=float(positive.median()), max_surplus_day_GWh=float(positive.max()),
                    h2_daily_max_GWh=econ.h2_unit,
                    full_design_real_mean_price=float(design.price.mean()),
                    checks=dict(largest_schedule_error=max(x["max_check"] for x in results.values()),
                                xpress_schedules=sum(x.get("solver") == "Xpress" for x in results.values()),
                                simple_schedules=2, independent_grid_crosschecks=8, grid_cells=len(grid),
                                previous_v1_gain_difference_mGBP=comparisons),
                    battery_bounds=bounds,
                    hydrogen_crossings={f"{policy}_{year}": crossing(data.loc[str(year)], econ, policy, 10000.)
                                        for policy in ("A", "B") for year in (2023, 2024, 2025)},
                    cashflow_20MW={f"{policy}_{year}": cashflow(results[f"{policy}_fixed20_{year}"], econ)
                                   for policy in ("A", "B") for year in (2023, 2024, 2025)})
    write_json(OUT / "study.json", {"summary": metadata, "cases": results})
    pd.DataFrame.from_dict(results, orient="index").to_csv(OUT / "cases.csv", index_label="case")
    print("Verified results written to", OUT, flush=True)


if __name__ == "__main__":
    run()
