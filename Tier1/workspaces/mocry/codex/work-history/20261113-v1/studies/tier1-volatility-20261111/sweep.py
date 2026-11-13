"""Mean-preserving volatility stresses of the full v6 product model."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.optimize._highspy import _core as highs

ROOT = Path(__file__).resolve().parent
V6 = ROOT.parent / "tier1-multiproduct-20261110-v6"
sys.path.insert(0, str(V6))
from model import Rows, costs

PLANTS = {"itm-alpha50": ("itm-neptune-v", 10),
          "nel-mc2000": ("nel-mc1000", 2), "nel-mc4000": ("nel-mc1000", 4)}
YEARS = 6


def data():
    path = V6 / "results/A_comparable_main_schedule.csv"
    frame = pd.read_csv(path, index_col="date", parse_dates=True)
    assert len(frame) == 2192
    assert frame.index.equals(pd.date_range("2020-01-01", "2025-12-31"))
    return frame[["generation", "demand", "price"]].to_numpy().T


def stress(gap_factor, price_factor):
    g, d, p = data()
    gap = g - d
    mean = gap.mean()
    changed = mean + gap_factor * (gap - mean)
    positive = np.maximum(changed, 0)
    common = np.minimum(g, d)
    weight = (g.mean() - positive.mean()) / common.mean()
    if weight < -1e-10:
        raise ValueError("Infeasible spread under both original energy means")
    gp = max(weight, 0) * common + positive
    dp = max(weight, 0) * common + np.maximum(-changed, 0)
    pp = p.mean() + price_factor * (p - p.mean())
    assert np.allclose([gp.mean(), dp.mean(), pp.mean()], [g.mean(), d.mean(), p.mean()])
    assert np.allclose(gp - dp, changed)
    return gp, dp, pp


def max_gap_factor():
    g, d, _ = data()
    gap = g - d
    mean = gap.mean()
    return brentq(lambda k: np.maximum(mean + k * (gap - mean), 0).mean() - g.mean(), 1, 100)


def data_costs():
    config = json.loads((V6 / "configuration.json").read_text(encoding="utf-8"))
    batteries, plants = costs(config)
    all_plants = {h["id"]: h for h in plants}
    for big, (small, count) in PLANTS.items():
        large, base = all_plants[big], all_plants[small]
        assert math.isclose(large["unit_GWh"], count * base["unit_GWh"])
        assert math.isclose(large["annual"], count * base["annual"])
        assert large["kWh_kg"] == base["kWh_kg"] and large["minimum"] >= base["minimum"]
    groups = [[b for b in batteries if b["rte"] == rte] for rte in sorted({b["rte"] for b in batteries})]
    for b in batteries:
        assert b["self_discharge"] == 0 and b["soc_upper"] - b["soc_lower"] > 0
        assert b["P_MW"] * 24 / 1000 >= b["usable"] / b["eta"]
    return config, groups, [h for h in plants if h["id"] not in PLANTS]


def stock_limits(g, d, policy, rte, size_limit, power_limits=(np.inf, np.inf)):
    charge_limit, discharge_limit = power_limits
    if policy == "A":
        return np.minimum(size_limit, np.cumsum(np.minimum(g, charge_limit)) * rte)
    stock = np.zeros(len(g))
    for t, delta in enumerate(g - d):
        old = stock[t - 1] if t else 0
        stock[t] = min(size_limit, max(0, old + rte * min(max(delta, 0), charge_limit)
                                      - min(max(-delta, 0), discharge_limit)))
    return stock


def make_model(g, d, p, policy, config, groups, plants, battery, reference, bad, exact_priority,
               fixed=None, forced=False, gross_upper=None, size_limit=np.inf, investment_limit=np.inf,
               power_limits=(np.inf, np.inf)):
    m = Rows()
    m.var("reference", 1, 1, c=reference)
    acceptance = config["cap_kg_day"]
    electrolysers = {
        h["id"]: m.var("N_" + h["id"], math.ceil(acceptance / (24 * h["kg_hour"])),
                       integer=True, c=h["annual"]) for h in plants
    }
    batteries = {}
    energies = []
    if not battery:
        groups = []
    if any(math.isfinite(power) for power in power_limits):
        assert len(groups) == 1
    for group in groups:
        units = {}
        for b in group:
            unit = b["usable"] * b["eta"]
            upper = math.ceil(size_limit / unit) if math.isfinite(size_limit) else math.ceil(g.sum() / unit)
            upper = min(upper, math.ceil(gross_upper / b["annual"])) if gross_upper is not None else upper
            lo = 0
            if fixed is not None:
                upper = lo = fixed.get(b["id"], 0)
            index = m.var("N_" + b["id"], upper, lo, integer=True, c=b["annual"])
            units[index] = unit
            batteries[b["id"]] = index
        energies.append(units)
    if forced:
        m.row({idx: 1 for idx in batteries.values()}, lo=1)
    if math.isfinite(investment_limit):
        m.row({index: energy for units in energies for index, energy in units.items()}, hi=investment_limit)
    cap = [
        min(size_limit, sum(m.hi[index] * energy for index, energy in units.items()))
        for units in energies
    ]
    if groups:
        total = stock_limits(g, d, policy, max(b[0]["rte"] for b in groups),
                             min(sum(cap), size_limit), power_limits)
    else:
        total = np.zeros(len(g))
    maximum_h2_energy = acceptance * max(h["kWh_kg"] for h in plants) / 1e6
    columns = {"direct": []}
    columns.update({h["id"]: [] for h in plants})
    for j in range(len(groups)):
        columns.update({f"{kind}_{j}": [] for kind in ("charge", "sale", "hydrogen", "stock")})
    modes = {}
    cumulative_deficit, block_opening = 0., {}
    for t, (supply, demand, price) in enumerate(zip(g, d, p)):
        direct_limit = min(supply, demand)
        mandate = direct_limit if policy == "B" else 0
        q = m.var(f"q_{t}", direct_limit, mandate, c=-price / (1000 * YEARS))
        columns["direct"].append(q)
        gen_h2 = m.var(f"gen_h2_{t}", min(supply - mandate, maximum_h2_energy))
        gen = {q: 1, gen_h2: 1}
        sales = {q: 1}
        h2 = {gen_h2: -1}
        intake = {}
        prev_stock, sale_stock, left_stock = {}, {}, {}
        opening = total[t - 1] if t else 0
        for j, (group, usable, units) in enumerate(zip(groups, cap, energies)):
            rte = group[0]["rte"]
            charge = m.var(f"charge_{j}_{t}", min(supply - mandate, usable / rte, power_limits[0]))
            available = min(usable, opening + rte * (supply - mandate), power_limits[1])
            release = m.var(f"sale_{j}_{t}", min(demand - mandate, available), c=-price / (1000 * YEARS))
            to_h2 = m.var(f"hydrogen_{j}_{t}", min(maximum_h2_energy, available))
            stock = m.var(f"stock_{j}_{t}", min(usable, total[t]) if t < len(g) - 1 else 0)
            previous = columns[f"stock_{j}"][-1] if t else None
            for key, index in zip(("charge", "sale", "hydrogen", "stock"), (charge, release, to_h2, stock)):
                columns[f"{key}_{j}"].append(index)
            gen[charge], sales[release], h2[to_h2] = 1, 1, -1
            sale_stock[release] = 1
            left_stock.update({stock: 1, to_h2: 1})
            balance = {stock: 1, charge: -rte, release: 1, to_h2: 1}
            if previous is not None:
                balance[previous] = -1
                prev_stock[previous] = 1
            m.row(balance, 0, 0)
            expansion = {index: -energy for index, energy in units.items()}
            m.row({stock: 1} | expansion, hi=0)
            m.row({charge: rte} | expansion, hi=0)
            m.row({release: 1, to_h2: 1} | expansion, hi=0)
            if math.isfinite(power_limits[1]):
                m.row({release: 1, to_h2: 1}, hi=power_limits[1])
        if groups and policy == "B" and demand > supply and t:
            deficit = min(demand - supply, power_limits[1])
            if cumulative_deficit == 0:
                block_opening = prev_stock
            cumulative_deficit += deficit
            if exact_priority and opening <= deficit + 1e-9:
                m.row(left_stock, hi=0)
            elif exact_priority:
                z = m.var(f"covers_{t}", 1, integer=True)
                modes[t] = z
                m.row(sale_stock | {z: -deficit}, lo=0)
                m.row(left_stock | {z: -(opening - deficit)}, hi=0)
                # There is no charging within a run of deficit days. Covering
                # today's deficit also requires covering every earlier one.
                m.row(left_stock | {z: cumulative_deficit} |
                      {i: -v for i, v in block_opening.items()}, hi=0)
                if t - 1 in modes:
                    m.row({z: 1, modes[t - 1]: -1}, hi=0)
            else:
                fraction = min(1., deficit / opening) if opening > 0 else 1.
                m.row(sale_stock | {i: -v * fraction for i, v in prev_stock.items()}, lo=0)
        else:
            cumulative_deficit = 0.
        for h in plants:
            name = h["id"]
            e = h["kWh_kg"]
            installed = electrolysers[name]
            upper = min(acceptance * e / 1e6, m.hi[installed] * h["unit_GWh"])
            idx = m.var(f"{name}_{t}", upper, c=-config["netback"] / (e * YEARS))
            columns[name].append(idx)
            h2[idx], intake[idx] = 1, 1 / e
            m.row({idx: 1, installed: -h["unit_GWh"]}, hi=0)
            if (name, t) in bad:
                on = m.var(f"on_{name}_{t}", 1, integer=True)
                m.row({idx: 1, on: -upper}, hi=0)
                m.row({idx: 1, on: -h["minimum"] * h["unit_GWh"]}, lo=0)
        m.row(gen, hi=supply)
        m.row(sales, hi=demand)
        m.row(h2, 0, 0)
        m.row(intake, hi=acceptance / 1e6)
    return m, columns, electrolysers, batteries, modes


def solve(m, seconds, threads, initial=None):
    matrix = m.mat()
    lp = highs.HighsLp()
    lp.num_col_, lp.num_row_ = matrix.shape[1], matrix.shape[0]
    lp.col_cost_, lp.col_lower_, lp.col_upper_ = m.c, m.lo, m.hi
    lp.row_lower_, lp.row_upper_ = m.rl, m.ru
    lp.integrality_ = [highs.HighsVarType(i) for i in m.integer]
    lp.a_matrix_.num_col_, lp.a_matrix_.num_row_ = lp.num_col_, lp.num_row_
    lp.a_matrix_.format_ = highs.MatrixFormat.kColwise
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = matrix.indptr, matrix.indices, matrix.data
    optimizer = highs._Highs()
    for key, value in dict(output_flag=False, time_limit=float(seconds), threads=threads,
                           mip_abs_gap=0.0000004, mip_rel_gap=1e-10,
                           mip_feasibility_tolerance=1e-8, random_seed=0).items():
        assert optimizer.setOptionValue(key, value) == highs.HighsStatus.kOk
    assert optimizer.passModel(lp) == highs.HighsStatus.kOk
    if initial:
        idx, values = zip(*initial)
        assert optimizer.setSolution(len(idx), np.asarray(idx, dtype=np.int32), np.asarray(values)) == highs.HighsStatus.kOk
    optimizer.run()
    sol, info = optimizer.getSolution(), optimizer.getInfo()
    if not sol.value_valid:
        raise RuntimeError(str(optimizer.getModelStatus()))
    x = np.asarray(sol.col_value)
    lower = info.mip_dual_bound
    if not any(m.integer):
        lower = info.objective_function_value
    assert math.isfinite(lower)
    ax = matrix @ x
    error = max(np.max(np.maximum(np.asarray(m.rl) - ax, 0)),
                np.max(np.maximum(ax - np.asarray(m.ru), 0)))
    assert error < 2e-5, error
    return x, -float(info.objective_function_value), -float(lower), str(optimizer.getModelStatus())


def unpack(x, columns, h, b, modes):
    return ({name: x[idx] for name, idx in columns.items()},
            {name: int(round(x[idx])) for name, idx in h.items()},
            {name: int(round(x[idx])) for name, idx in b.items()},
            {day: int(round(x[idx])) for day, idx in modes.items()})


def check(flows, counts, g, d, p, policy, config, groups, plants):
    out = {name: vals.copy() for name, vals in flows.items()}
    charge = np.zeros(len(g))
    discharge = np.zeros(len(g))
    power_to_h2 = np.zeros(len(g))
    opening = np.zeros(len(g))
    for j, group in enumerate(groups):
        rte = group[0]["rte"]
        charged, sold, h2, stock = (out[f"{name}_{j}"] for name in ("charge", "sale", "hydrogen", "stock"))
        cancel = np.minimum(rte * charged, sold)
        cancel_h2 = np.minimum(rte * charged - cancel, h2)
        out["direct"] += cancel
        charged -= (cancel + cancel_h2) / rte
        sold -= cancel
        h2 -= cancel_h2
        assert np.max(np.minimum(charged, sold + h2)) < 1e-7
        charge += charged
        discharge += sold
        power_to_h2 += h2
        opening[1:] += stock[:-1]
    bad = {(h["id"], int(t)) for h in plants
           for t in np.flatnonzero((out[h["id"]] > 1e-7) & (out[h["id"]] < h["unit_GWh"] * h["minimum"] - 1e-7))}
    priority_error = 0.0
    if policy == "B":
        priority_error = float(np.max(np.abs(discharge - np.minimum(np.maximum(d-g, 0), opening))))
    quantity_h2 = sum(out[h["id"]] / h["kWh_kg"] for h in plants)
    revenues = float(np.dot(p, out["direct"] + discharge) / (1000 * YEARS)
                     + quantity_h2.sum() * config["netback"] / YEARS)
    annual_cost = sum(counts.get(h["id"], 0) * h["annual"] for h in plants)
    annual_cost += sum(counts.get(b["id"], 0) * b["annual"] for group in groups for b in group)
    return out, bad, priority_error, revenues - annual_cost


def repair_a_minimum(flows, bad, groups, plants, g, d):
    """Drop sub-minimum loads and undo the earlier charges that would supply them."""
    hydrogen = sum(flows[h["id"]] for h in plants)
    from_battery = sum(flows[f"hydrogen_{j}"] for j in range(len(groups)))
    dropped = np.zeros(len(g))
    for name, t in bad:
        dropped[t] += flows[name][t]
        flows[name][t] = 0
    excess = np.maximum(0, dropped - (hydrogen - from_battery))
    for j, group in enumerate(groups):
        rte = group[0]["rte"]
        charge, sale, feed, stock = [flows[f"{name}_{j}"] for name in ("charge", "sale", "hydrogen", "stock")]
        withdrawn = np.minimum(excess, feed)
        feed -= withdrawn
        excess -= withdrawn
        undo = 0.
        for t in range(len(g) - 1, -1, -1):
            stock[t] -= undo
            undo += withdrawn[t]
            undo_charge = min(undo, rte * charge[t])
            charge[t] -= undo_charge / rte
            undo -= undo_charge
        assert undo < 1e-7 and stock.min() > -1e-7
        assert np.max(np.abs(stock - np.r_[0., stock[:-1]] - rte * charge + sale + feed)) < 1e-7
    assert excess.max() < 1e-7
    charge = sum(flows[f"charge_{j}"] for j in range(len(groups)))
    sale = sum(flows[f"sale_{j}"] for j in range(len(groups)))
    feed = sum(flows[f"hydrogen_{j}"] for j in range(len(groups)))
    from_generation = sum(flows[h["id"]] for h in plants) - feed
    assert from_generation.min() > -1e-7
    assert np.max(flows["direct"] + from_generation + charge - g) < 1e-7
    assert np.max(flows["direct"] + sale - d) < 1e-7
    return flows


def capacity_bound(g, d, p, config, groups, plants, reference, gross, incumbent, threads):
    # The discounted relaxation bounds all competitive full-cost portfolios:
    # at least half of the cheapest annual cost per usable GWh must be added back.
    discounted = [[b | {"annual": .5 * b["annual"]} for b in group] for group in groups]
    model, _, _, _, _ = make_model(g, d, p, "B", config, discounted, plants, True,
                                   reference, set(), False, gross_upper=gross)
    model.integer = [0] * len(model.integer)
    try:
        _, _, upper, status = solve(model, 30, threads)
    except RuntimeError:
        return np.inf
    if not status.endswith("kOptimal"):
        return np.inf
    cheapest = min(b["annual"] / (b["usable"] * b["eta"]) for group in groups for b in group)
    return max(0., upper - incumbent) / (.5 * cheapest) + .02


def scenario(policy, path, factor, seconds, threads, forced=False, limit=np.inf,
             *, gap_factor=None, case_directory=None, incumbent_profit=None):
    started = time.monotonic()
    kg = gap_factor if gap_factor is not None else factor if path in ("gap", "both") else 1
    kp = factor if gap_factor is not None or path in ("price", "both") else 1
    g, d, p = stress(kg, kp)
    config, groups, plants = data_costs()
    cap = config["cap_kg_day"]
    name = f"{policy}_{path}_{factor:.8g}" + ("_forced" if forced else "")
    if gap_factor is not None:
        name += f"_gap{kg:.10g}"
    bad = set()
    latest = None
    for _ in range(5):
        model, cols, h, b, modes = make_model(g, d, p, policy, config, groups, plants, False, 0, bad, False)
        x, lo, zero_upper, status = solve(model, seconds, threads)
        flow, h0, _, _ = unpack(x, cols, h, b, modes)
        flow, added, _, baseline = check(flow, h0, g, d, p, policy, config, [], plants)
        if not added:
            assert abs(baseline - lo) < 0.00002
            break
        bad.update(added)
    else:
        raise RuntimeError("Zero-battery minimum load refinement did not converge")

    # Universal annual receipts upper bound, net of the feasible no-battery plan.
    gross = max(0., float(np.dot(np.maximum(p, 0), d)) / (1000 * YEARS)
                + len(g) * cap * config["netback"] / (1e6 * YEARS) - baseline)
    upper = math.inf
    best = -math.inf if forced else 0.
    best_counts = {}
    best_h = h0
    exact = False
    cap_on_investment = np.inf
    for attempt in range(6):
        m, cols, h, b, modes = make_model(g, d, p, policy, config, groups, plants, True, baseline,
                                         bad, exact, forced=forced, gross_upper=gross,
                                         size_limit=min(limit, cap_on_investment), investment_limit=cap_on_investment)
        start = []
        if not forced:
            seed_flows, seed_h, seed_b, seed_modes = latest if latest is not None else (flow, h0, {}, {})
            start = [(0, 1)] + [(i, seed_h[name]) for name, i in h.items()]
            start += [(i, seed_b.get(name, 0)) for name, i in b.items()]
            start += [(int(i), float(v)) for name, ii in cols.items() if name in seed_flows
                      for i, v in zip(ii, seed_flows[name])]
            start += [(i, seed_modes.get(t, 0)) for t, i in modes.items()]
        x, lo, hi, status = solve(m, seconds, threads, start)
        upper = min(upper, hi)
        flows, hc, bc, mc = unpack(x, cols, h, b, modes)
        clean, added, prio, profit = check(flows, hc | bc, g, d, p, policy, config, groups, plants)
        if not added and prio < 1e-7 and profit - baseline > best - 1e-8:
            best, best_counts = profit - baseline, bc
            best_h = hc
            latest = (flows, hc, bc, mc)
        elif gap_factor is not None and policy == "A" and added:
            repaired = repair_a_minimum(clean, added, groups, plants, g, d)
            repaired, violations, _, repaired_profit = check(repaired, hc | bc, g, d, p, policy, config, groups, plants)
            assert not violations
            if repaired_profit - baseline > best:
                best, best_counts, best_h = repaired_profit - baseline, bc, hc
                latest = (repaired, hc, bc, mc)
            if upper - best < max(0.0000005, abs(best) * 1e-8):
                break
        if upper < -0.0000005 or (not added and prio < 1e-7):
            break
        bad.update(added)
        if not exact and prio >= 1e-7 and incumbent_profit is not None:
            floor = max(best, incumbent_profit / 1e6 - baseline - 1e-7)
            cap_on_investment = capacity_bound(g, d, p, config, groups, plants, baseline, gross, floor, threads)
        exact |= prio >= 1e-7

    capacity = sum(best_counts.get(b["id"], 0)*b["E_MWh"] for group in groups for b in group)
    output = dict(policy=policy, path=path, factor=factor, forced=forced,
                  objective_lower_GBP=best*1e6 if math.isfinite(best) else None,
                  objective_upper_GBP=upper*1e6, zero_upper_minus_feasible_GBP=(zero_upper-baseline)*1e6,
                  battery_MWh=capacity, counts=best_counts, attempts=attempt+1, status=status,
                  exact_priority_added=exact, price_min=float(p.min()), price_max=float(p.max()),
                  elapsed_seconds=time.monotonic()-started)
    if gap_factor is not None:
        output.update(
            gap_std_multiplier=kg, price_std_multiplier=kp,
            no_battery_annual_profit_GBP=baseline*1e6,
            electrolyser_counts=best_h, no_battery_electrolyser_counts=h0,
            electrolyser_MW=sum(best_h.get(h["id"], 0)*h["MW"] for h in plants),
            no_battery_electrolyser_MW=sum(h0.get(h["id"], 0)*h["MW"] for h in plants),
            battery_MW=sum(best_counts.get(b["id"], 0)*b["P_MW"] for group in groups for b in group),
            battery_annual_cost_GBP=sum(best_counts.get(b["id"], 0)*b["annual"]*1e6 for group in groups for b in group))
        if math.isfinite(cap_on_investment):
            output["competitive_usable_AC_capacity_upper_GWh"] = cap_on_investment
    if not forced and best > 0 and best > zero_upper-baseline + 0.0000005:
        output["decision"] = "positive"
    elif forced and upper < -0.0000005:
        output["decision"] = "zero"
    elif not forced and upper < 0.0000005 and capacity == 0:
        output["decision"] = "zero_within_50p"
    else:
        output["decision"] = "unresolved"
    if math.isfinite(limit):
        output["stock_limit_GWh"] = limit
        name += f"_limit{limit:.8g}"
    directory = ROOT / "cases" if case_directory is None else case_directory
    (directory / (name + ".json")).write_text(json.dumps(output, indent=2)+"\n", encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default="AB")
    parser.add_argument("--path", default="gap,price,both")
    parser.add_argument("--factors", nargs="+", type=float, required=True)
    parser.add_argument("--seconds", type=float, default=45)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=float, default=np.inf)
    args = parser.parse_args()
    (ROOT / "cases").mkdir(exist_ok=True)
    largest = max_gap_factor()
    print("Maximum physically feasible gap factor", largest, flush=True)
    jobs = [(p, path, k) for p in args.policy for path in args.path.split(",")
            for k in args.factors if path == "price" or k <= largest + 1e-8]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        work = {pool.submit(scenario, *job, args.seconds, args.threads, args.force, args.limit): job for job in jobs}
        for future in as_completed(work):
            try:
                row = future.result()
                print(work[future], row["decision"], row["battery_MWh"],
                      row["objective_lower_GBP"], row["objective_upper_GBP"],
                      f'{row["elapsed_seconds"]:.1f}s', flush=True)
            except Exception as exc:
                print(work[future], "ERROR", str(exc), flush=True)


if __name__ == "__main__":
    main()
