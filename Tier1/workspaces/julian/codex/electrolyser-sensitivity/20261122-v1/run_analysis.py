"""Site-scale electrolyser operating sensitivity with 30-minute power dispatch."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from highspy import Highs, HighsModelStatus, HighsVarType
from scipy.sparse import csr_matrix, eye, hstack, vstack

sys.dont_write_bytecode = True
SLOTS = 48
DT_HOURS = 0.5
DAILY_CAP_KG = 10_000.0
TOL = 1e-7
SCENARIOS = [
    ("v5_flexible", 0.125, 0),
    ("brief_flexible", 0.20, 0),
    ("brief_daily_commitment", 0.20, 1),
    ("brief_minimum_4d", 0.20, 4),
    ("brief_minimum_5d", 0.20, 5),
]


@dataclass
class Inputs:
    dates: pd.DatetimeIndex
    generation: np.ndarray
    demand: np.ndarray
    price: np.ndarray
    price_forgone: np.ndarray
    free_in_A: np.ndarray
    surplus: np.ndarray
    nominal_mw: float
    rated_kg_hour: float
    mwh_per_kg: float
    ref_price: float
    capex: float
    annual_cost: float
    annual_om: float
    crf: float

    @property
    def unit_slot_mwh(self):
        return self.nominal_mw * DT_HOURS

    @property
    def cap_mwh(self):
        return DAILY_CAP_KG * self.mwh_per_kg


def load_inputs(study: Path):
    sys.path.insert(0, str(study))
    from model import annual_costs, frame_for

    config = json.loads((study / "configuration.json").read_text())
    f = frame_for("2020-01-01", "2025-12-31")
    assert len(f) == 105216
    assert np.all(np.diff(f.index.asi8) == (f.index[1].value - f.index[0].value))
    g = f.g.to_numpy().reshape(-1, SLOTS) * 1000
    d = f.d.to_numpy().reshape(-1, SLOTS) * 1000
    p = f.price.to_numpy().reshape(-1, SLOTS)
    _, electrolysers = annual_costs(config)
    h = next(h for h in electrolysers if h["id"] == "itm-neptune-v")
    rate = config["r"]
    return Inputs(
        pd.DatetimeIndex(f.date.iloc[::SLOTS]), g, d, p, p.clip(min=0),
        np.where(p >= 0, (g-d).clip(min=0), g), (g-d).clip(min=0),
        h["MW"], h["kg_hour"], h["kWh_kg"] / 1000, config["netback"],
        h["capital_GBP"], h["annual"] * 1e6, h["fom_GBP"],
        rate / (1 - (1+rate)**(-h["life"])),
    )


def value_dispatch(free, price, upper, lower, cap, hydrogen_per_mwh):
    """Optimal half-hour energy allocation for continuous slot bands and daily caps."""
    free_capacity = (np.minimum(upper, free)-lower).clip(min=0)
    paid_capacity = (upper-np.maximum(lower, free)).clip(min=0)
    paid_value = hydrogen_per_mwh - price
    paid_order = np.argsort(-paid_value, axis=1, kind="stable")
    paid_capacity = np.take_along_axis(paid_capacity, paid_order, axis=1)
    limits = np.concatenate((free_capacity, np.where(np.take_along_axis(paid_value, paid_order, axis=1)>0, paid_capacity, 0)), axis=1)
    prefix = np.cumsum(limits, axis=1) - limits
    quota = cap - lower.sum(axis=1)[:, None]
    assigned = np.minimum((quota-prefix).clip(min=0), limits)
    paid_assigned = np.zeros_like(lower)
    np.put_along_axis(paid_assigned, paid_order, assigned[:, SLOTS:], axis=1)
    load = lower + assigned[:, :SLOTS] + paid_assigned
    net = (hydrogen_per_mwh * load - price * (load-free).clip(min=0)).sum(axis=1)
    return load, net


def exact_flexible_day(free, price, upper, minimum, cap, hydrogen_per_mwh, seed):
    """Repair a day whose unconstrained solution leaves a sub-minimum active slot."""
    available = (upper > 0).astype(float)
    e = eye(SLOTS, format="csr")
    z = csr_matrix((SLOTS, SLOTS))
    sum_load = csr_matrix(([1.0]*SLOTS, ([0]*SLOTS, range(SLOTS))), shape=(1, SLOTS*3))
    # Variables are load, electricity taken from sales, and nonzero slot indicator.
    matrix = vstack((
        hstack((e, -e, z)),
        hstack((e, z, -e.multiply(upper[:, None]))),
        hstack((-e, z, minimum*e)),
        sum_load,
    )).tocsr()
    ub = np.r_[free, np.zeros(2*SLOTS), cap]
    highs = Highs()
    highs.silent()
    highs.setOptionValue("threads", 1)
    highs.setOptionValue("mip_rel_gap", 1e-10)
    highs.setOptionValue("mip_abs_gap", 1e-6)
    highs.addCols(3*SLOTS, np.r_[np.full(SLOTS, -hydrogen_per_mwh), price, np.zeros(SLOTS)],
                  np.zeros(3*SLOTS), np.r_[upper, upper, available],
                  0, np.array([], dtype=np.int32), np.array([], dtype=np.int32), np.array([]))
    highs.addRows(matrix.shape[0], np.full(len(ub), -np.inf), ub, matrix.nnz,
                  matrix.indptr.astype(np.int32), matrix.indices.astype(np.int32), matrix.data)
    for index in range(SLOTS*2, SLOTS*3):
        highs.changeColIntegrality(index, HighsVarType.kInteger)
    x = seed.copy()
    x[(x>0)&(x<minimum)] = 0
    highs.setSolution(3*SLOTS, np.arange(3*SLOTS, dtype=np.int32),
                      np.r_[x, (x-free).clip(min=0), (x>TOL).astype(float)])
    highs.run()
    if highs.getModelStatus() != HighsModelStatus.kOptimal:
        raise RuntimeError(f"Daily repair was not certified optimal: {highs.getModelStatus()}")
    load = np.asarray(highs.getSolution().col_value[:SLOTS])
    load[np.abs(load)<TOL] = 0
    net = np.sum(hydrogen_per_mwh * load - price * (load-free).clip(min=0))
    return load, net


def solve_flexible(data, policy, count, minimum_fraction, price_h2):
    free = data.free_in_A if policy == "A" else data.surplus
    paid_price = data.price_forgone if policy == "A" else np.zeros_like(free)
    available = data.generation if policy == "A" else data.surplus
    unit = data.unit_slot_mwh
    minimum = unit * minimum_fraction
    upper = np.minimum(count*unit, available)
    upper[upper<minimum] = 0
    hydrogen_per_mwh = price_h2 / data.mwh_per_kg
    loads, val = value_dispatch(free, paid_price, upper, np.zeros_like(upper), data.cap_mwh, hydrogen_per_mwh)

    repairs = np.flatnonzero(np.any((loads>TOL) & (loads<minimum-TOL), axis=1))
    for day in repairs:
        loads[day], val[day] = exact_flexible_day(
            free[day], paid_price[day], upper[day], minimum, data.cap_mwh, hydrogen_per_mwh, loads[day]
        )
    online = np.maximum(0, np.ceil((loads-TOL)/unit)).astype(int)
    return loads, online, val, len(repairs)


def states_and_transitions(count, min_days):
    # Age buckets are starts from today back to min_days-2 days ago plus mature units.
    states = [state for state in itertools.product(range(count+1), repeat=min_days) if sum(state)<=count]
    index = {state: i for i, state in enumerate(states)}
    sources, destinations = [], []
    for i, state in enumerate(states):
        immature = sum(state[1:])
        for keep_mature in range(state[0]+1):
            for start in range(count-immature-keep_mature+1):
                nxt = (keep_mature+state[-1], start, *state[1:-1])
                sources.append(i)
                destinations.append(index[nxt])
    return np.array(states), np.array(sources, dtype=np.int32), np.array(destinations, dtype=np.int32)


def choose_counts(day_value, count, min_days):
    """Solve the full chronology exactly, with module commitment changing at UTC midnight."""
    if min_days == 1:
        best = np.argmax(day_value[:, :count+1], axis=1)
        return best, day_value[np.arange(len(best)), best].sum()

    states, src, dst = states_and_transitions(count, min_days)
    counts = states.sum(axis=1)
    from_edge = np.arange(len(src), dtype=np.int32)
    values = np.full(len(states), -np.inf)
    values[0] = 0
    history = np.full((len(day_value), len(states)), -1, dtype=np.int32)
    for day, value in enumerate(day_value):
        trial = values[src]
        best = np.full(len(states), -np.inf)
        np.maximum.at(best, dst, trial)
        tied = (trial == best[dst]) & np.isfinite(trial)
        preferred = np.full(len(states), len(src), dtype=np.int32)
        np.minimum.at(preferred, dst[tied], from_edge[tied])
        valid = preferred < len(src)
        history[day, valid] = src[preferred[valid]]
        values = best + value[counts]
    mature_final = np.flatnonzero(states[:, 1:].sum(axis=1)==0)
    node = mature_final[np.argmax(values[mature_final])]
    optimum = values[node]
    online = np.empty(len(day_value), dtype=int)
    for day in range(len(day_value)-1, -1, -1):
        online[day] = counts[node]
        node = history[day,node]
        assert node>=0
    assert node==0
    return online, optimum


def longest_true(values):
    endpoints = np.flatnonzero(np.diff(np.r_[False, values, False]))
    return int(np.max(endpoints[1::2]-endpoints[::2], initial=0))


def daily_choices(data, policy, max_units, minimum_fraction, price_h2):
    minimum = data.unit_slot_mwh * minimum_fraction
    free = data.free_in_A if policy == "A" else data.surplus
    price = data.price_forgone if policy == "A" else np.zeros_like(free)
    available = data.generation if policy == "A" else data.surplus
    hval = price_h2 / data.mwh_per_kg
    choices, all_loads = [], []
    for count in range(max_units+1):
        lower = np.full_like(data.price, count*minimum)
        upper = np.minimum(available, count*data.unit_slot_mwh)
        feasible = np.all(upper >= lower-TOL, axis=1) & (lower.sum(axis=1) <= data.cap_mwh+TOL)
        load = np.zeros_like(lower)
        val = np.full(len(lower), -np.inf)
        load[feasible], val[feasible] = value_dispatch(
            free[feasible], price[feasible], upper[feasible], lower[feasible], data.cap_mwh, hval
        )
        choices.append(val)
        all_loads.append(load)
    return np.column_stack(choices), np.asarray(all_loads)


def solve_minimum_run(data, policy, max_units, minimum_fraction, min_days, price_h2, choices=None):
    minimum = data.unit_slot_mwh * minimum_fraction
    longest = None
    if policy == "B":
        longest = longest_true((data.surplus>=minimum).ravel())
        if longest < min_days*SLOTS:
            return np.zeros_like(data.surplus), np.zeros_like(data.surplus, dtype=int), np.zeros(len(data.dates)), longest

    day_value, all_loads = choices if choices is not None else daily_choices(
        data, policy, max_units, minimum_fraction, price_h2
    )
    online_day, optimum = choose_counts(day_value, max_units, min_days)
    seq = np.arange(len(online_day))
    load = all_loads[online_day,seq]
    val = day_value[seq,online_day]
    assert abs(val.sum()-optimum)<0.1
    return load, np.repeat(online_day[:,None], SLOTS, axis=1), val, longest


def audit(data, policy, count, minimum_fraction, min_days, price_h2, loads, online, gross):
    assert loads.min() >= -TOL
    assert np.max(loads.sum(axis=1)) <= data.cap_mwh+TOL
    assert np.max(online) <= count and np.min(online)>=0
    assert np.max(loads-online*data.unit_slot_mwh) < TOL
    assert np.max(online*data.unit_slot_mwh*minimum_fraction-loads) < TOL
    original = np.minimum(data.generation, data.demand)
    if policy=="A":
        actual = np.where(data.price>=0, np.minimum(data.generation-loads,data.demand), 0)
        reference = np.where(data.price>=0, original, 0)
    else:
        assert np.max(loads-data.surplus)<TOL
        actual = reference = original
    assert np.all(actual+loads<=data.generation+TOL)
    cash = (data.price*(actual-reference) + price_h2*loads/data.mwh_per_kg).sum(axis=1)
    assert np.max(np.abs(gross-cash)) < 0.001
    # Reconstruct real modules. A stop only removes a unit that has served its required time.
    if min_days:
        current = online.ravel()
        changes = np.diff(np.r_[0, current, 0])
        uncommitted = count
        mature = 0
        ready_after = np.zeros(len(current)+1, dtype=int)
        for t in range(len(current)+1):
            mature += ready_after[t]
            diff = changes[t]
            if diff>0:
                assert t+SLOTS*min_days <= len(current)
                assert diff<=uncommitted
                uncommitted -= diff
                ready_after[t+SLOTS*min_days] += diff
            elif diff<0:
                assert mature>=-diff
                mature += diff
                uncommitted -= diff
        assert uncommitted==count
    return actual


def metrics(data, policy, count, name, minimum_fraction, min_days, h2_price, choices=None):
    if min_days:
        loads, online, gross, record = solve_minimum_run(data, policy, count, minimum_fraction, min_days, h2_price, choices)
        repairs = 0
    else:
        loads, online, gross, repairs = solve_flexible(data, policy, count, minimum_fraction, h2_price)
        record = None
    sales = audit(data, policy, count, minimum_fraction, min_days, h2_price, loads, online, gross)
    daily_kg = loads.sum(axis=1)/data.mwh_per_kg
    years = data.dates.year.to_numpy()
    annual_cost = count*data.annual_cost
    investment = count*data.capex
    operating_cash = gross.sum()/len(np.unique(years))-count*data.annual_om
    annual_net = gross.sum()/len(np.unique(years))-annual_cost
    cap95 = daily_kg>=0.95*DAILY_CAP_KG-TOL
    zero = daily_kg<TOL
    labels = dict(policy=policy, scenario=name, modules=count, mw=count*data.nominal_mw,
                  minimum_load_pct=100*minimum_fraction, minimum_on_days=min_days, h2_gbp2020_per_kg=h2_price)
    annual = []
    for year in np.unique(years):
        mask = years==year
        annual.append(dict(labels, year=year, gross_increment_gbp2020=gross[mask].sum(),
                           net_increment_gbp2020=gross[mask].sum()-annual_cost,
                           annual_h2_tonnes=daily_kg[mask].sum()/1000,
                           days_at_least_95pct_of_cap=int(cap95[mask].sum()),
                           days_with_zero_h2=int(zero[mask].sum()),
                           demand_served_pct=100*sales[mask].sum()/data.demand[mask].sum()))
    row = dict(labels, capital_gbp2020=investment, equipment_annual_gbp2020=annual_cost,
               mean_annual_gross_increment_gbp2020=gross.sum()/len(annual),
               mean_annual_net_increment_gbp2020=annual_net,
               npv_repeated_mean_gbp2020=annual_net/data.crf,
               simple_payback_years=investment/operating_cash if operating_cash>TOL and count else None,
               mean_h2_tonnes_per_year=daily_kg.sum()/1000/len(annual),
               days_at_least_95pct_of_cap_pct=100*np.mean(cap95),
               zero_production_days=int(zero.sum()), longest_zero_production_days=longest_true(zero),
               loss_years=sum(x["net_increment_gbp2020"]<-TOL for x in annual),
               worst_annual_net_gbp2020=min(x["net_increment_gbp2020"] for x in annual),
               demand_served_pct=100*sales.sum()/data.demand.sum(),
               module_starts=int(np.maximum(np.diff(np.r_[0,online.ravel()]),0).sum()),
               longest_eligible_B_hours=None if record is None else DT_HOURS*record,
               exact_daily_mip_repairs=repairs)
    return row, annual


def run(data, out):
    results, annual, sizing, size_bounds = [], [], [], []
    for policy, installed in (("A",8),("B",11)):
        for price in (data.ref_price, 5, 9.5):
            for name, min_load, min_days in SCENARIOS:
                row, rows = metrics(data, policy, installed, name, min_load, min_days, price)
                results.append(row)
                annual.extend(rows)
                print(policy, f"{price:.3f}",name, f"{row['mean_annual_net_increment_gbp2020']/1e6:.4f}",
                      row["exact_daily_mip_repairs"], flush=True)
    # With daily commitments, additional installed modules may remain idle. An
    # installed count above the daily physically-operable maximum is dominated.
    daily_max = int(DAILY_CAP_KG // (data.rated_kg_hour*24*0.20))
    choices = daily_choices(data, "A", daily_max, 0.20, data.ref_price)
    for name,min_load,min_days in SCENARIOS:
        fixed = next(r for r in results if r["policy"]=="A" and r["scenario"]==name and r["h2_gbp2020_per_kg"]==data.ref_price)
        if not min_days:
            for n in (0,4,5,6,7,8,9,10):
                if n==8:
                    sizing.append(fixed)
                    continue
                row,_ = metrics(data, "A",n,name,min_load,min_days,data.ref_price)
                sizing.append(row)
            continue

        sizing.append(fixed)
        # Dropping the interday minimum-run restriction gives an upper bound on
        # all tested designs; it is exact for the one-day commitment scenario.
        upper = np.maximum.accumulate(choices[0], axis=1).sum(axis=0)/6 - np.arange(daily_max+1)*data.annual_cost
        incumbent = fixed["mean_annual_net_increment_gbp2020"]
        best_n = 8
        kept = {8:incumbent, 0:0.0}
        for n in np.argsort(-upper):
            if n in kept or upper[n] < incumbent-TOL:
                continue
            row,_ = metrics(data, "A",int(n),name,min_load,min_days,data.ref_price,choices)
            sizing.append(row)
            candidate = row["mean_annual_net_increment_gbp2020"]
            kept[n] = candidate
            if candidate > incumbent:
                incumbent, best_n = candidate, int(n)
        for n, bound in enumerate(upper):
            size_bounds.append(dict(scenario=name, modules=n, mw=n*data.nominal_mw,
                                    upper_net_gbp2020=bound, exact_net_gbp2020=kept.get(n),
                                    best_modules=best_n, best_net_gbp2020=incumbent))
        assert max((u for n,u in enumerate(upper) if n not in kept), default=-np.inf) <= incumbent+TOL
        print(f"Sizing {name}: best {best_n} modules, £{incumbent/1e6:.4f}m/year",flush=True)

    pd.DataFrame(results).to_csv(out/"site_sensitivity.csv",index=False)
    pd.DataFrame(annual).to_csv(out/"site_annual_results.csv",index=False)
    pd.DataFrame(sizing).to_csv(out/"A_sizing_results.csv",index=False)
    pd.DataFrame(size_bounds).to_csv(out/"A_sizing_bounds.csv",index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-dir", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    study = args.study_dir.resolve()
    data = load_inputs(study)
    run(data, args.output)
    source_names = ("inputs/halfhour.csv.gz", "configuration.json", "model.py")
    metadata = {
        "source_sha256": {p:hashlib.sha256((study/p).read_bytes()).hexdigest() for p in source_names},
        "half_hour_periods": len(data.dates)*SLOTS,
        "daily_offtake_cap_kg": DAILY_CAP_KG,
        "fixed_modules": {"A": 8, "B": 11},
        "neptune_v_capex_gbp2020_per_unit": data.capex,
        "neptune_v_annual_cost_gbp2020_per_unit": data.annual_cost,
        "neptune_v_fixed_om_gbp2020_per_unit": data.annual_om,
        "min_run_schedule": "Each module starts/stops at UTC midnight; energy dispatch remains half-hourly. Across years the same sequence is used.",
        "solver": f"Day-commitment dynamic programming and HiGHS {Highs().version()} for independent days",
        "simple_payback": "Initial capital divided by average annual operating contribution less fixed O&M (undiscounted, before future stack replacements).",
        "npv": "Constant-equivalent 30-year NPV at 5% real, using the six-year mean, with fixed O&M and discounted stack replacements.",
        "boundary_conditions": "Start with all modules off; finish all commenced minimum runs within the historical horizon. No power imports, battery, or hydrogen storage."
    }
    (args.output/"assumptions.json").write_text(json.dumps(metadata, indent=2)+"\n")
