"""Minimize nameplate storage subject to keeping the free-storage profit."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize._highspy import _core as highs

from run import BASE, ROOT, audit, build, cancel_simultaneous, costs, legacy, stock_bounds


def strengthen_priority(model, columns, frame):
    """Use the actual opening-stock bound in the priority disjunction."""
    previous_mode = None
    previous_day = None
    for mode, name in enumerate(model.names):
        if not name.startswith('stock_covers_demand_'):
            continue
        day = int(name.rsplit('_', 1)[1])
        previous = columns['stock'][day - 1]
        remaining_bound = model.hi[previous] - (frame.d.iloc[day] - frame.g.iloc[day])
        model.row({columns['battery_sale'][day]: 1, previous: -1, mode: remaining_bound}, lo=0)
        model.row({columns['stock'][day]: 1, columns['battery_h2'][day]: 1, mode: -remaining_bound}, hi=0)
        if previous_day == day - 1:
            model.row({mode: 1, previous_mode: -1}, hi=0)
        previous_mode, previous_day = mode, day


def solve_with_start(model, start, seconds, absolute_gap, *, relative_gap=1e-9, threads=4):
    # SciPy's bundled HiGHS binding permits a feasible MIP start. scipy.milp
    # does not currently expose that argument.
    matrix = model.mat()
    lp = highs.HighsLp()
    lp.num_col_, lp.num_row_ = matrix.shape[1], matrix.shape[0]
    lp.col_cost_, lp.col_lower_, lp.col_upper_ = model.c, model.lo, model.hi
    lp.row_lower_, lp.row_upper_ = model.rl, model.ru
    lp.a_matrix_.num_col_, lp.a_matrix_.num_row_ = lp.num_col_, lp.num_row_
    lp.a_matrix_.format_ = highs.MatrixFormat.kColwise
    lp.a_matrix_.start_ = matrix.indptr
    lp.a_matrix_.index_ = matrix.indices
    lp.a_matrix_.value_ = matrix.data
    lp.integrality_ = [highs.HighsVarType(i) for i in model.integer]

    solver = highs._Highs()
    options = {'output_flag': False, 'time_limit': float(seconds), 'threads': threads,
               'mip_abs_gap': absolute_gap, 'mip_rel_gap': relative_gap,
               'mip_feasibility_tolerance': 1e-8, 'random_seed': 0}
    for key, value in options.items():
        assert solver.setOptionValue(key, value) == highs.HighsStatus.kOk, key
    assert solver.passModel(lp) == highs.HighsStatus.kOk
    idx = np.arange(lp.num_col_, dtype=np.int32)
    assert solver.setSolution(len(idx), idx, start) == highs.HighsStatus.kOk
    solver.run()
    result = solver.getSolution()
    info = solver.getInfo()
    if not result.value_valid:
        raise RuntimeError(f'No feasible solution: {solver.getModelStatus()}')
    return np.asarray(result.col_value), dict(status=str(solver.getModelStatus()),
        objective=float(info.objective_function_value), lower_bound=float(info.mip_dual_bound),
        relative_gap=float(info.mip_gap), nodes=int(info.mip_node_count))


def warm_start(model, columns, counts, schedule, investments):
    vector = np.zeros(len(model.names))
    vector[0] = 1
    for name, indices in columns.items():
        vector[indices] = schedule[name]
    for name, index in counts.items():
        vector[index] = investments[name]
    for index, name in enumerate(model.names):
        if name.startswith('stock_covers_demand_'):
            day = int(name.rsplit('_', 1)[1])
            vector[index] = int(schedule.stock.iloc[day - 1] >= schedule.d.iloc[day] - schedule.g.iloc[day] - 1e-9)
        elif '_on_' in name:
            plant, day = name.rsplit('_on_', 1)
            vector[index] = int(schedule[plant].iloc[int(day)] > 1e-7)
        elif name == 'peak_stock':
            vector[index] = schedule.stock.max()
    return vector


def compute(policy, objective, seconds, allowed_loss_GBP, seed):
    legacy.prepare_inputs()
    frame = legacy.load_data().loc['2020':'2025']
    config = json.loads((BASE / 'configuration.json').read_text(encoding='utf-8'))
    batteries, plants = costs(config)
    rte = max(b['rte'] for b in batteries)
    deliverable_fraction = .6 * math.sqrt(rte)
    results = ROOT / 'results'
    seed_summary = json.loads((results / f'{seed}.json').read_text(encoding='utf-8'))
    schedule = pd.read_csv(results / f'{seed}_schedule.csv', index_col='date', parse_dates=True)
    investments = seed_summary['electrolyser_units']
    no_battery_profit = seed_summary['no_battery_profit_mGBP']
    target = seed_summary['annual_incremental_profit_mGBP'] - allowed_loss_GBP / 1e6
    exact_upper = float(stock_bounds(frame.g.to_numpy(), frame.d.to_numpy(), rte, policy, np.inf).max())
    capacity = float(schedule.stock.max()) + 1e-7 if objective == 'min_capacity' else exact_upper + 1e-7

    minimum_days = set()
    iterations = []
    for _ in range(6):
        model, columns, counts, ref = build(frame, config, policy, rte, capacity, plants, None, minimum_days)
        if policy == 'B':
            strengthen_priority(model, columns, frame)
        profit_costs = dict(enumerate(model.c))
        peak = None
        if objective == 'min_capacity':
            model.row(profit_costs, hi=-target)
            peak = model.var('peak_stock', capacity)
            for stock in columns['stock']:
                model.row({stock: 1, peak: -1}, hi=0)
            model.c = [0.] * len(model.c)
            model.c[peak] = 1
        start = warm_start(model, columns, counts, schedule, investments)
        values, info = solve_with_start(model, start, seconds, .0005 if peak is not None else 1e-7)
        output = pd.DataFrame({k: values[indices] for k, indices in columns.items()}, index=frame.index)
        new_days = set()
        for plant in plants:
            k = plant['id']
            active = output[k].to_numpy()
            minimum = plant['unit_GWh'] * plant['minimum']
            new_days.update((k, int(t)) for t in np.flatnonzero((active > 1e-7) & (active < minimum - 1e-7)))
        info['violated_minimum_days'] = len(new_days)
        iterations.append(info)
        print(policy, objective, json.dumps(info), flush=True)
        if not new_days:
            break
        if new_days <= minimum_days:
            raise RuntimeError('Exact minimum load constraints remain violated')
        minimum_days |= new_days
    else:
        raise RuntimeError('Minimum-load refinement did not finish')

    cancel_simultaneous(output, rte)
    output[['g', 'd', 'price']] = frame[['g', 'd', 'price']]
    output['h2_kg'] = sum(output[p['id']] * 1e6 / p['kWh_kg'] for p in plants)
    profit = -sum(values[k] * v for k, v in profit_costs.items())
    chosen = {name: int(round(values[index])) for name, index in counts.items()}
    assert all(abs(values[index] - chosen[name]) < 1e-6 for name, index in counts.items())
    stock = float(output.stock.max())
    result = dict(policy=policy, objective=objective, seed=seed, allowed_annual_profit_loss_GBP=allowed_loss_GBP,
        roundtrip_efficiency=rte, annual_reference_receipts_mGBP=ref,
        no_battery_profit_mGBP=no_battery_profit, annual_incremental_profit_mGBP=profit,
        annual_additional_profit_GBP=(profit - no_battery_profit) * 1e6,
        target_annual_incremental_profit_mGBP=target if peak is not None else None,
        max_stock_GWh=stock, nominal_capacity_TWh=stock / deliverable_fraction / 1000,
        electrolyser_units=chosen,
        electrolyser_MW=sum(p['MW'] * chosen[p['id']] for p in plants), solver_runs=iterations)
    result['audit'] = audit(output, result, plants, config, rte, capacity)
    if peak is not None:
        assert profit >= target - 1e-7
        result['minimum_nominal_capacity_lower_bound_TWh'] = max(0, info['lower_bound']) / deliverable_fraction / 1000
    else:
        result['maximum_profit_upper_bound_mGBP'] = -info['lower_bound']
        result['maximum_additional_profit_upper_bound_GBP'] = (-info['lower_bound'] - no_battery_profit) * 1e6
        result['capacity_sufficient_for_any_B_schedule_TWh'] = exact_upper / deliverable_fraction / 1000 if policy == 'B' else None
    case = f'{policy}_{objective}'
    (results / f'{case}.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    output.to_csv(results / f'{case}_schedule.csv', index_label='date')
    print('FINISHED', case, result['nominal_capacity_TWh'], result['annual_additional_profit_GBP'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('policy', choices=['A', 'B'])
    parser.add_argument('objective', choices=['min_capacity', 'max_profit'])
    parser.add_argument('--seconds', type=int, default=150)
    parser.add_argument('--allowed-loss', type=float, default=1.)
    parser.add_argument('--seed')
    args = parser.parse_args()
    compute(args.policy, args.objective, args.seconds, args.allowed_loss, args.seed or f'{args.policy}_uncapped')
