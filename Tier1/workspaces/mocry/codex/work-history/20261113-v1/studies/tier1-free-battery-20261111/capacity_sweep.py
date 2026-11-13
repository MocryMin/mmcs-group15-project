"""Compute the historical free-battery capacity/value frontier for policies A and B."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import math
from pathlib import Path
import time

import numpy as np
import pandas as pd

from capacity_requirement import solve_with_start, strengthen_priority, warm_start
from run import BASE, ROOT, audit, build, cancel_simultaneous, costs, legacy

OUT = ROOT / 'capacity_sweep'
CAPACITIES = [0, 3, 100, 300, 1500, 10000, 45000, 100000, 300000,
              1000000, 3000000, 6000000, 30000000, 100000000, 200000000, 272000000]
PLATEAU_FROM = {'A': 272000000, 'B': 6000000}
REPLACEMENTS = {'itm-alpha50': ('itm-neptune-v', 10),
                'nel-mc2000': ('nel-mc1000', 2), 'nel-mc4000': ('nel-mc1000', 4)}
RTE = .92
SOC_WINDOW = .6


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def case_file(policy, capacity, schedule=False):
    name = f'{policy}_{capacity}_MWh'
    return OUT / (f'{name}_schedule.csv' if schedule else f'{name}.json')


def original_seed(policy, plants):
    case = f'{policy}_comparable_main'
    source = BASE / 'results'
    original = read_json(source / f'{case}.json')
    raw = pd.read_csv(source / f'{case}_schedule.csv', index_col='date', parse_dates=True)
    columns = ['direct', 'generation_h2', 'charge', 'battery_sale', 'battery_h2', 'price', 'h2_kg']
    seed = raw[columns].copy()
    seed['stock'] = 0.
    seed[['g', 'd']] = raw[['generation', 'demand']]
    counts = {p['id']: p['count'] for p in original['investment'] if p['kind'] == 'electrolyser'}
    for plant in plants:
        name = plant['id']
        seed[name] = raw[name + '__input']
    for large, (small, ratio) in REPLACEMENTS.items():
        seed[small] += raw[large + '__input']
        counts[small] += ratio * counts[large]
    return original, seed, {p['id']: counts[p['id']] for p in plants}


def latest_seed(policy, capacity, baseline, schedule, counts):
    for smaller in sorted((v for v in CAPACITIES if 0 < v < capacity), reverse=True):
        if case_file(policy, smaller).is_file() and case_file(policy, smaller, schedule=True).is_file():
            run = read_json(case_file(policy, smaller))
            if run['annual_gain_GBP'] > 0:
                path = case_file(policy, smaller, schedule=True)
                return (pd.read_csv(path, index_col='date', parse_dates=True), run['electrolyser_units'],
                        run['annual_gain_GBP'])
    return schedule, counts, 0.


def solve_case(policy, nominal_capacity, seconds, threads, refine=False):
    config = read_json(BASE / 'configuration.json')
    _, all_plants = costs(config)
    plant_lookup = {p['id']: p for p in all_plants}
    for large, (small, ratio) in REPLACEMENTS.items():
        a, b = plant_lookup[large], plant_lookup[small]
        assert math.isclose(a['unit_GWh'], b['unit_GWh'] * ratio)
        assert math.isclose(a['annual'], b['annual'] * ratio)
        assert math.isclose(a['kWh_kg'], b['kWh_kg']) and a['minimum'] >= b['minimum']
    plants = [p for p in all_plants if p['id'] not in REPLACEMENTS]
    baseline, base_schedule, base_counts = original_seed(policy, plants)
    seed, counts, feasible_gain = latest_seed(policy, nominal_capacity, baseline, base_schedule, base_counts)
    frame = legacy.load_data().loc['2020':'2025']
    assert seed.index.equals(frame.index)
    best_schedule, best_counts = seed, counts
    best_upper = math.inf
    physical_capacity = nominal_capacity * SOC_WINDOW * math.sqrt(RTE) / 1000
    min_days = set()
    history = []
    if refine and case_file(policy, nominal_capacity).is_file():
        previous = read_json(case_file(policy, nominal_capacity))
        best_upper = previous['annual_gain_upper_GBP']
        history = previous['solver_history']
        if previous['annual_gain_GBP'] >= feasible_gain:
            best_schedule = pd.read_csv(case_file(policy, nominal_capacity, schedule=True),
                                        index_col='date', parse_dates=True)
            best_counts = previous['electrolyser_units']
            feasible_gain = previous['annual_gain_GBP']
    started = time.monotonic()

    for _ in range(4):
        model, columns, installed, ref = build(frame, config, policy, RTE, physical_capacity, plants, None, min_days)
        if policy == 'B':
            strengthen_priority(model, columns, frame)
        model.c[0] += baseline['annual_incremental_profit_mGBP']
        initial = warm_start(model, columns, installed, best_schedule, best_counts)
        values, info = solve_with_start(model, initial, seconds, .000005,
                                        relative_gap=1e-5, threads=threads)
        schedule = pd.DataFrame({k: values[indices] for k, indices in columns.items()}, index=frame.index)
        invalid = set()
        for plant in plants:
            name = plant['id']
            use = schedule[name].to_numpy()
            minimum = plant['unit_GWh'] * plant['minimum']
            invalid.update((name, int(t)) for t in np.flatnonzero((use > 1e-7) & (use < minimum - 1e-7)))
        info['invalid_minimum_load_days'] = len(invalid)
        history.append(info)
        best_upper = min(best_upper, -info['lower_bound'] * 1e6)
        if invalid:
            assert invalid - min_days
            min_days |= invalid
            continue

        counts = {name: int(round(values[index])) for name, index in installed.items()}
        assert all(abs(values[index] - counts[name]) < 1e-6 for name, index in installed.items())
        cancel_simultaneous(schedule, RTE)
        schedule[['g', 'd', 'price']] = frame[['g', 'd', 'price']]
        schedule['h2_kg'] = sum(schedule[p['id']] * 1e6 / p['kWh_kg'] for p in plants)
        gain = -info['objective'] * 1e6
        if gain >= feasible_gain - 1e-5:
            feasible_gain, best_schedule, best_counts = gain, schedule, counts
        break

    assert math.isfinite(best_upper) and best_upper >= feasible_gain - 1.
    years = legacy.year_fraction(best_schedule)
    result = dict(policy=policy, nominal_capacity_MWh=nominal_capacity,
        annual_gain_GBP=feasible_gain, annual_gain_upper_GBP=max(best_upper, feasible_gain),
        annual_incremental_profit_mGBP=baseline['annual_incremental_profit_mGBP'] + feasible_gain / 1e6,
        no_battery_profit_mGBP=baseline['annual_incremental_profit_mGBP'],
        annual_reference_receipts_mGBP=baseline['annual_reference_receipts_mGBP'],
        roundtrip_efficiency=RTE, available_stock_window_fraction=SOC_WINDOW,
        electrolyser_units=best_counts,
        electrolyser_MW=sum(p['MW'] * best_counts[p['id']] for p in plants),
        annual_charge_MWh=float(best_schedule.charge.sum() * 1000 / years),
        annual_battery_sales_MWh=float(best_schedule.battery_sale.sum() * 1000 / years),
        annual_battery_to_H2_MWh=float(best_schedule.battery_h2.sum() * 1000 / years),
        max_stock_GWh=float(best_schedule.stock.max()),
        elapsed_seconds=time.monotonic()-started, solver_history=history)
    result['audit'] = audit(best_schedule, result, plants, config, RTE, physical_capacity)
    best_schedule.to_csv(case_file(policy, nominal_capacity, schedule=True), index_label='date')
    case_file(policy, nominal_capacity).write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return result


def run_batch(seconds, threads, workers, only, selected_policy, refine):
    OUT.mkdir(exist_ok=True)
    legacy.prepare_inputs()
    jobs = [(policy, capacity) for capacity in CAPACITIES if capacity > 0
            for policy in ('A', 'B') if capacity < PLATEAU_FROM[policy] and (not only or capacity in only)
            and (selected_policy is None or policy == selected_policy)]
    if not refine:
        jobs = [(p, c) for p, c in jobs if not case_file(p, c).is_file()]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(solve_case, p, c, seconds, threads, refine): (p, c) for p, c in jobs}
        for future in as_completed(futures):
            policy, capacity = futures[future]
            try:
                answer = future.result()
                print(policy, capacity, f'{answer["annual_gain_GBP"]:,.2f}',
                      f'{answer["annual_gain_upper_GBP"]:,.2f}',
                      f'{answer["elapsed_seconds"]:.1f}s', flush=True)
            except Exception as exc:
                print(policy, capacity, 'ERROR', repr(exc), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=int, default=65)
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--only', type=int, nargs='+')
    parser.add_argument('--policy', choices=['A', 'B'])
    parser.add_argument('--refine', action='store_true')
    args = parser.parse_args()
    run_batch(args.seconds, args.threads, args.workers, args.only, args.policy, args.refine)
