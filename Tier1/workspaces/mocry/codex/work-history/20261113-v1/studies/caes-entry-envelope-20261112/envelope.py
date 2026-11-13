"""Investment entry boundary for one 50 MW / 1.5 GWh electric CAES project."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "tier1-volatility-20261111"))
from sweep import V6, YEARS, check, data, data_costs, make_model, max_gap_factor, repair_a_minimum, solve, stress, unpack

GAP_POINTS = (1., 1.025, 1.05, 1.1, 1.25, 1.5, 2., 3., 4., 6., 8., 12., 16., 24.)
PRICE_GRID = (1., 2., 4., 6., 8., 12., 16., 24., 32., 48., 64., 96., 128.)
RTE = .62
CAPACITY = 1.5
POWER = (1.2, 1.2)
STORAGE = dict(id="caes", usable=CAPACITY, rte=RTE, eta=1., annual=0.)


def economics():
    base = json.loads((V6 / "inputs/parameters.json").read_text(encoding="utf-8"))
    pnnl = json.loads((ROOT.parent / "nonbattery-storage-research-20261111/REFERENCE_COSTS.json").read_text(encoding="utf-8"))
    row = next(x["scenarios"]["point"] for x in pnnl["profiles"] if x["technology"] == "CAES")
    cost = base["battery_cost_MWh"] * CAPACITY * 1000 / 3
    ratio = row["fixed_OM_USD_reported_per_year"] / row["installed_capital_USD_reported"]
    rate, life = .05, row["calendar_life_years"]
    annuity = cost * rate / (1 - (1+rate)**-life)
    return dict(
        storage_output_capacity_GWh=CAPACITY, charge_MW=POWER[0]*1000/24, discharge_MW=POWER[1]*1000/24,
        roundtrip_efficiency=RTE, installation_cost_GBP2020=cost,
        reference_battery_installed_GBP2020_MWh=base["battery_cost_MWh"], installation_ratio=1/3,
        fixed_om_share_per_year=ratio, fixed_om_GBP2020_year=cost*ratio, life_years=life,
        real_discount_rate=rate, annuity_GBP2020_year=annuity, annual_total_GBP2020=annuity+cost*ratio)


def verify_storage(flows, g, d, policy, plants):
    c, y, h, s = (flows[f"{key}_0"] for key in ("charge", "sale", "hydrogen", "stock"))
    opening = np.r_[0., s[:-1]]
    direct = flows["direct"]
    hgen = sum(flows[x["id"]] for x in plants) - h
    errors = [
        np.max(np.abs(s - opening - RTE*c + y + h)), abs(s[-1]), max(0., s.max()-CAPACITY),
        max(0., c.max()-POWER[0]), max(0., (y+h).max()-POWER[1]), np.minimum(c,y+h).max(),
        max(0., -hgen.min()), max(0., (direct+hgen+c-g).max()), max(0., (direct+y-d).max()),
    ]
    if policy == "B":
        errors.extend((np.abs(direct-np.minimum(g,d)).max(),
                       np.abs(y-np.minimum(np.minimum(np.maximum(d-g,0),POWER[1]),opening)).max()))
    assert max(errors) < 2e-7, (policy, errors)


def solve_side(g, d, p, policy, config, plants, storage, seconds, seed=None):
    groups = [[STORAGE]] if storage else []
    fixed = {"caes": 1} if storage else None
    prices = p if policy == "B" else np.maximum(p, 0)
    center = float(np.dot(prices, np.minimum(g, d)) / (1000 * YEARS)) if seed is None else seed["value"]
    bad = set()
    best, upper = -np.inf, np.inf
    selected = None
    for _ in range(10):
        m, cols, h, b, modes = make_model(
            g, d, p, policy, config, groups, plants, storage, center, bad, policy == "B",
            fixed=fixed, size_limit=CAPACITY if storage else np.inf,
            power_limits=POWER if storage else (np.inf, np.inf))
        start = None
        if seed is not None:
            start = [(0, 1.)]
            start.extend((idx, seed["counts"].get(name, 0)) for name, idx in h.items())
            start.extend((idx, 1) for idx in b.values())
            for name, indices in cols.items():
                start.extend(zip(indices, seed["flows"].get(name, np.zeros(len(g)))))
            if "stock_0" not in seed["flows"]:
                start.extend((i, 0) for i in modes.values())
        x, _, hi, status = solve(m, seconds, 1, start)
        upper = min(upper, hi+center)
        flows, hc, bc, _ = unpack(x, cols, h, b, modes)
        flows, violated, _, value = check(flows, hc | bc, g, d, p, "A", config, groups, plants)
        if storage:
            verify_storage(flows, g, d, policy, plants)
        if violated:
            if storage:
                flows = repair_a_minimum(flows, violated, groups, plants, g, d)
                verify_storage(flows, g, d, policy, plants)
            else:
                for name, t in violated:
                    flows[name][t] = 0.
            flows, residual, _, value = check(flows, hc | bc, g, d, p, "A", config, groups, plants)
            assert not residual
        if value > best:
            best, selected = value, dict(flows=flows, counts=hc)
        assert best <= upper + .00001, (policy, best, upper, status)
        if upper-best < .00004:
            break
        if not violated:
            break
        bad.update(violated)
    assert selected is not None
    assert upper-best < .0002, (policy, storage, best, upper, status)
    return selected | {"value": best, "upper": max(upper,best)}


def solve_point(g, d, p, gap, price, policy, config, plants, annual_cost, seconds, support=None):
    baseline = solve_side(g, d, p, policy, config, plants, False, seconds)
    with_storage = solve_side(g, d, p, policy, config, plants, True, seconds, baseline)
    lower = with_storage["value"] - baseline["upper"]
    upper = with_storage["upper"] - baseline["value"]
    raw_price = data()[2]
    slope = np.dot(raw_price-raw_price.mean(), baseline["flows"]["direct"]) / (1000 * YEARS)
    if support is not None and policy == "A":
        hydrogen_power = sum(baseline["flows"][h["id"]] for h in plants)
        hydrogen_revenue = sum(baseline["flows"][h["id"]] / h["kWh_kg"] for h in plants)
        support[price] = (
            baseline["counts"],
            np.maximum(0, np.minimum(d, g-hydrogen_power)) / (1000 * YEARS),
            hydrogen_revenue * config["netback"] / YEARS,
            sum(baseline["counts"].get(h["id"], 0) * h["annual"] for h in plants),
        )
    return dict(policy=policy, gap_std_multiplier=gap, price_std_multiplier=price,
                gross_lower_GBP_year=lower*1e6, gross_upper_GBP_year=upper*1e6,
                net_lower_GBP_year=lower*1e6-annual_cost, net_upper_GBP_year=upper*1e6-annual_cost,
                zero_profit_lower_GBP_year=baseline["value"]*1e6, zero_profit_slope_GBP_year=slope*1e6,
                storage_profit_upper_GBP_year=with_storage["upper"]*1e6,
                electrolyser_MW=sum(with_storage["counts"].get(h["id"],0)*h["MW"] for h in plants),
                no_storage_electrolyser_MW=sum(baseline["counts"].get(h["id"],0)*h["MW"] for h in plants),
                annual_charge_MWh=float(with_storage["flows"]["charge_0"].sum()*1000/YEARS),
                annual_sale_MWh=float(with_storage["flows"]["sale_0"].sum()*1000/YEARS),
                annual_to_h2_MWh=float(with_storage["flows"]["hydrogen_0"].sum()*1000/YEARS))


def interval_upper(left, right, annual_cost):
    # Convexity gives a chord upper bound on the optimum with storage.
    # A feasible no-storage plan at either endpoint gives a lower line.
    a, b = left["price_std_multiplier"], right["price_std_multiplier"]
    a0, b0 = (v["zero_profit_lower_GBP_year"] for v in (left, right))
    sa, sb = (v["zero_profit_slope_GBP_year"] for v in (left, right))
    candidates = [a, b]
    if abs(sa-sb) > 1e-8:
        intersection = (b0-a0+sa*a-sb*b)/(sa-sb)
        if a < intersection < b:
            candidates.append(intersection)
    au, bu = (v["storage_profit_upper_GBP_year"] for v in (left, right))
    return max(au+(bu-au)*(k-a)/(b-a)-max(a0+sa*(k-a), b0+sb*(k-b))-annual_cost for k in candidates)


def daily_interval_upper(left, right, annual_cost, support, price_mean, price_deviation, common_sale):
    a, b = left["price_std_multiplier"], right["price_std_multiplier"]
    # These units can always be allocated to a sale at positive prices or
    # curtailed at negative prices, whatever the H2 and storage plan.
    a_value, b_value = (
        point["storage_profit_upper_GBP_year"] / 1e6
        - np.dot(common_sale, np.maximum(price_mean + k * price_deviation, 0))
        for k, point in ((a, left), (b, right))
    )
    slope = (b_value - a_value) / (b - a)
    plans = [support[a], support[b]]
    if plans[0][0] == plans[1][0]:
        groups = [plans]
    else:
        groups = [[plan] for plan in plans]
    upper = math.inf
    for group in groups:
        _, _, _, investment = group[0]
        q = np.stack([plan[1] - common_sale for plan in group])
        h = np.stack([plan[2] for plan in group])
        lo, hi = a, b
        # For a common installed fleet, any daily mix of these H2 plans is feasible.
        # Subtract their best daily profit from the chord. Its concave upper bound
        # comes from the supporting line at a midpoint of this derivative search.
        for _ in range(35):
            k = (lo + hi) / 2
            price = price_mean + k * price_deviation
            net = h + np.maximum(price, 0) * q
            best = net.argmax(axis=0)
            best_q = q[best, np.arange(price.size)]
            level = a_value + slope * (k-a) - net.max(axis=0).sum() + investment
            gradient = slope - np.dot(price_deviation, best_q * (price > 0))
            tangent_upper = level + max(gradient*(lo-k), gradient*(hi-k))
            upper = min(upper, (tangent_upper + 1e-8)*1e6 - annual_cost)
            if upper < -.05:
                return upper
            if gradient > 0:
                lo = k
            else:
                hi = k
    return upper


def boundary(task):
    policy, gap, seconds, tolerance = task
    config, _, plants = data_costs()
    annual_cost = economics()["annual_total_GBP2020"]
    cached = {}
    support = {}
    raw_price = data()[2]
    price_mean = raw_price.mean()
    price_deviation = raw_price - price_mean
    g, d, _ = stress(gap, 1.)
    h2_limit = config["cap_kg_day"] * max(h["kWh_kg"] for h in plants) / 1e6
    common_sale = np.maximum(0, np.minimum(d-POWER[1], g-POWER[0]-h2_limit)) / (1000 * YEARS)

    def at(price):
        if price not in cached:
            g, d, p = stress(gap, price)
            cached[price] = solve_point(g, d, p, gap, price, policy, config, plants, annual_cost, seconds, support)
        return cached[price]

    def first(left, right):
        if interval_upper(left, right, annual_cost) < -.05:
            return None
        if policy == "A":
            upper = daily_interval_upper(left, right, annual_cost, support, price_mean, price_deviation, common_sale)
            if upper < -.05:
                return None
        a, b = left["price_std_multiplier"], right["price_std_multiplier"]
        if b-a <= tolerance and right["net_lower_GBP_year"] > 0:
            return a, b, True
        if b-a <= tolerance/8:
            return a, b, right["net_lower_GBP_year"] > 0
        middle = at((a+b)/2)
        return first(left,middle) or first(middle,right)

    left = at(1.)
    interval = (1., 1., True) if left["net_lower_GBP_year"] > 0 else None
    for price in PRICE_GRID[1:]:
        if interval:
            break
        right = at(price)
        interval = first(left, right)
        left = right
    result = dict(policy=policy, gap_std_multiplier=gap, historical_price_net_GBP_year=cached[1.]["net_lower_GBP_year"],
                  historical_price_gross_GBP_year=cached[1.]["gross_lower_GBP_year"],
                  gap_sd_GWh_day=gap * (data()[0]-data()[1]).std(),
                  samples=len(cached))
    if interval is not None:
        low, high, certified = interval
        result.update(price_entry_lower=low, price_entry_upper=high, entry_certified=certified,
                      net_at_lower_GBP_year=cached[low]["net_lower_GBP_year"],
                      net_at_upper_GBP_year=cached[high]["net_lower_GBP_year"],
                      price_entry_sd_lower_GBP_MWh=low*data()[2].std(),
                      price_entry_sd_upper_GBP_MWh=high*data()[2].std())
    else:
        result["entry_certified"] = False
    path = ROOT / "cases" / f"{policy}_{gap:.10g}.json"
    path.write_text(json.dumps(dict(boundary=result, points=list(cached.values())), indent=2)+"\n",encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--seconds", type=float, default=45)
    parser.add_argument("--tol", type=float, default=.125)
    parser.add_argument("--gaps", type=float, nargs="+", default=[*GAP_POINTS,max_gap_factor()])
    parser.add_argument("--policy", default="AB")
    options = parser.parse_args()
    (ROOT / "cases").mkdir(exist_ok=True)
    jobs = [(p, g, options.seconds, options.tol) for p in options.policy for g in options.gaps
            if not (ROOT / "cases" / f"{p}_{g:.10g}.json").exists()]
    print(json.dumps(economics(), indent=2), flush=True)
    with ProcessPoolExecutor(max_workers=options.workers) as pool:
        futures = {pool.submit(boundary, task): task for task in jobs}
        for future in as_completed(futures):
            print(json.dumps(future.result()), flush=True)


if __name__ == "__main__":
    main()
