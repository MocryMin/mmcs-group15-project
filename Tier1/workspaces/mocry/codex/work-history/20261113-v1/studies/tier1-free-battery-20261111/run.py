"""Free-battery comparisons using the v6 data, hydrogen assets and policy rules."""
import argparse
import json
import math
from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'tier1-multiproduct-20261110-v6'
sys.path.insert(0, str(BASE))
import legacy_model as legacy
from model import Rows, costs


def stock_bounds(generation, demand, rte, policy, capacity):
    """Maximum usable AC output still in stock at each close of day."""
    if policy == 'A':
        return np.minimum(np.cumsum(generation) * rte, capacity)
    bounds = np.zeros(len(generation))
    for day, difference in enumerate(generation - demand):
        opening = bounds[day - 1] if day else 0
        # B charges only surplus and must first serve current demand on deficit days.
        bounds[day] = min(capacity, max(0, opening + rte * max(difference, 0) + min(difference, 0)))
    return bounds


def build(frame, config, policy, rte, capacity, plants, fixed, minimum_days):
    generation, demand, price = (frame[k].to_numpy(float) for k in ('g', 'd', 'price'))
    years = legacy.year_fraction(frame)
    accept = config['cap_kg_day']
    ref = np.dot(price, legacy.direct_reference(frame, policy)) / (1000 * years)
    model = Rows()
    model.var('reference_receipts', 1, 1, c=ref)
    counts = {}
    for plant in plants:
        name = plant['id']
        limit = math.ceil(accept / (24 * plant['kg_hour']))
        lo, hi = (0, limit) if fixed is None else (fixed[name], fixed[name])
        counts[name] = model.var('installed_' + name, hi, lo, integer=True, c=plant['annual'])

    bound = stock_bounds(generation, demand, rte, policy, capacity)
    columns = {k: [] for k in ('direct', 'generation_h2', 'charge', 'battery_sale', 'battery_h2', 'stock')}
    for plant in plants:
        columns[plant['id']] = []

    for day, (g, d, p) in enumerate(zip(generation, demand, price)):
        direct_limit = min(g, d)
        mandatory = direct_limit if policy == 'B' else 0
        opening_bound = bound[day - 1] if day else 0
        power_revenue = -p / (1000 * years)
        direct = model.var(f'direct_{day}', direct_limit, mandatory, c=power_revenue)
        gen_h2 = model.var(f'gen_h2_{day}', g - mandatory)
        charge = model.var(f'charge_{day}', min(g - mandatory, capacity / rte))
        discharge_bound = min(capacity, opening_bound + rte * (g - mandatory))
        battery_sale = model.var(f'battery_sale_{day}', min(d - mandatory, discharge_bound), c=power_revenue)
        battery_h2 = model.var(f'battery_h2_{day}', discharge_bound)
        stock = model.var(f'stock_{day}', bound[day] if day < len(frame) - 1 else 0)
        previous = columns['stock'][-1] if day else None
        for key, value in zip(('direct', 'generation_h2', 'charge', 'battery_sale', 'battery_h2', 'stock'),
                              (direct, gen_h2, charge, battery_sale, battery_h2, stock)):
            columns[key].append(value)

        model.row({direct: 1, gen_h2: 1, charge: 1}, hi=g)
        model.row({direct: 1, battery_sale: 1}, hi=d)
        model.row({battery_sale: 1, battery_h2: 1}, hi=discharge_bound)
        balance = {stock: 1, charge: -rte, battery_sale: 1, battery_h2: 1}
        if previous is not None:
            balance[previous] = -1
        model.row(balance, lo=0, hi=0)

        if policy == 'B' and d > g and previous is not None:
            shortfall = d - g
            if opening_bound <= shortfall:
                model.row({battery_sale: 1, previous: -1}, lo=0, hi=0)
            else:
                mode = model.var(f'stock_covers_demand_{day}', 1, integer=True)
                model.row({battery_sale: 1, previous: -1}, hi=0)
                model.row({battery_sale: 1, mode: -shortfall}, lo=0)
                model.row({battery_sale: 1, previous: -1, mode: opening_bound}, lo=0)

        h2_balance = {gen_h2: -1, battery_h2: -1}
        acceptance = {}
        for plant in plants:
            name = plant['id']
            unit = plant['unit_GWh']
            conversion = plant['kWh_kg']
            per_kg = config['netback'] - plant['variable_GBP_kg']
            limit = min(model.hi[counts[name]] * unit, accept * conversion / 1e6)
            flow = model.var(f'{name}_{day}', limit, c=-per_kg / (conversion * years))
            columns[name].append(flow)
            model.row({flow: 1, counts[name]: -unit}, hi=0)
            h2_balance[flow] = 1
            acceptance[flow] = 1 / conversion
            if (name, day) in minimum_days:
                on = model.var(f'{name}_on_{day}', 1, integer=True)
                model.row({flow: 1, on: -limit}, hi=0)
                model.row({flow: 1, on: -unit * plant['minimum']}, lo=0)
        model.row(h2_balance, lo=0, hi=0)
        model.row(acceptance, hi=accept / 1e6)
    return model, columns, counts, float(ref)


def cancel_simultaneous(schedule, rte):
    """Replace same-day storage round trips by direct generation without moving stock."""
    cancel_sale = np.minimum(schedule.charge * rte, schedule.battery_sale)
    cancel_h2 = np.minimum(schedule.charge * rte - cancel_sale, schedule.battery_h2)
    schedule['direct'] += cancel_sale
    schedule['generation_h2'] += cancel_h2
    schedule['charge'] -= (cancel_sale + cancel_h2) / rte
    schedule['battery_sale'] -= cancel_sale
    schedule['battery_h2'] -= cancel_h2


def audit(schedule, summary, plants, config, rte, capacity):
    g, d, p, direct, gen_h2, charge, sale, h2, stock = (schedule[key].to_numpy() for key in
        ('g', 'd', 'price', 'direct', 'generation_h2', 'charge', 'battery_sale', 'battery_h2', 'stock'))
    opening = np.r_[0., stock[:-1]]
    errors = {
        'stock_balance': np.max(np.abs(stock - opening - rte * charge + sale + h2)),
        'terminal_stock': abs(stock[-1]),
        'stock_capacity': max(0, np.max(stock - capacity)),
        'max_generation_use': max(0, np.max(direct + gen_h2 + charge - g)),
        'max_sales': max(0, np.max(direct + sale - d)),
        'no_simultaneous_charge_discharge': np.max(np.minimum(charge, sale + h2)),
        'nonnegative_flows': max(0, -np.min([direct, gen_h2, charge, sale, h2, stock])),
    }
    if summary['policy'] == 'B':
        errors['B_direct'] = np.max(np.abs(direct - np.minimum(g, d)))
        errors['B_battery'] = np.max(np.abs(sale - np.minimum(np.maximum(d - g, 0), opening)))

    mass = np.zeros(len(schedule))
    energy = np.zeros(len(schedule))
    annual_cost = 0.
    annual_variable = 0.
    years = legacy.year_fraction(schedule)
    for plant in plants:
        name = plant['id']
        used = schedule[name].to_numpy()
        unit = plant['unit_GWh']
        n = summary['electrolyser_units'][name]
        online = np.where(used > 1e-7, np.ceil(used / unit - 1e-7), 0)
        errors[name + '_capacity'] = max(0, np.max(used - n * unit))
        errors[name + '_minimum'] = max(0, np.max(online * unit * plant['minimum'] - used))
        annual_cost += n * plant['annual']
        annual_variable += used.sum() * plant['variable_GBP_kg'] / (plant['kWh_kg'] * years)
        mass += used * 1e6 / plant['kWh_kg']
        energy += used
    errors['h2_sources'] = np.max(np.abs(energy - gen_h2 - h2))
    errors['h2_cap_GWh_equivalent'] = max(0, np.max(mass - config['cap_kg_day'])) * 55.9 / 1e6
    receipts = float(np.dot(p, direct + sale) / (1000 * years) + mass.sum() * config['netback'] / (1e6 * years))
    net = receipts - annual_cost - annual_variable - summary['annual_reference_receipts_mGBP']
    error = abs(net - summary['annual_incremental_profit_mGBP'])
    assert max(errors.values()) < 2e-6, errors
    assert error < 1e-6, (net, error)
    return {key: float(value) for key, value in errors.items()} | {'profit_error_mGBP': error}


def run(policy, battery_case, seconds):
    legacy.prepare_inputs()
    frame = legacy.load_data().loc['2020':'2025']
    config = json.loads((BASE / 'configuration.json').read_text(encoding='utf-8'))
    baseline = json.loads((BASE / 'results' / f'{policy}_comparable_main.json').read_text(encoding='utf-8'))
    _, plants = costs(config)
    fixed = None
    if battery_case == 'one_reference':
        rte = .9
        nominal_MWh = 3.
        capacity = nominal_MWh * .6 * math.sqrt(rte) / 1000
        fixed = {i['id']: i['count'] for i in baseline['investment'] if i['kind'] == 'electrolyser'}
        plants = [plant for plant in plants if fixed[plant['id']] > 0]
    else:
        rte = max(battery['rte'] for battery in config['batteries'])
        capacity = np.inf
        nominal_MWh = None

    minimum_days = set()
    solver_runs = []
    for iteration in range(12):
        model, columns, counts, ref = build(frame, config, policy, rte, capacity, plants, fixed, minimum_days)
        matrix = model.mat()
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Unrecognized options detected')
            answer = milp(np.asarray(model.c), integrality=np.asarray(model.integer),
                          bounds=Bounds(model.lo, model.hi),
                          constraints=LinearConstraint(matrix, model.rl, model.ru),
                          options={'time_limit': seconds, 'mip_rel_gap': 1e-9, 'mip_abs_gap': 1e-8,
                                   'threads': 6, 'random_seed': 0})
        if answer.x is None:
            raise RuntimeError(answer.message)
        schedule = pd.DataFrame({name: answer.x[indices] for name, indices in columns.items()}, index=frame.index)
        violated = set()
        for plant in plants:
            name = plant['id']
            flow = schedule[name].to_numpy()
            minimum = plant['unit_GWh'] * plant['minimum']
            violated.update((name, int(t)) for t in np.flatnonzero((flow > 1e-7) & (flow < minimum - 1e-7)))
        mip_bound = getattr(answer, 'mip_dual_bound', None)
        upper = -float(answer.fun if mip_bound is None else mip_bound)
        info = dict(iteration=iteration + 1, upper=upper, profit=-float(answer.fun),
                    status=int(answer.status), added_minimum_days=len(violated - minimum_days),
                    message=answer.message)
        solver_runs.append(info)
        print(policy, battery_case, json.dumps(info), flush=True)
        if not violated:
            break
        if not (violated - minimum_days):
            raise RuntimeError('Minimum load violation remained after adding its constraint')
        minimum_days |= violated
    else:
        raise RuntimeError('Minimum load refinement limit exceeded')

    cancel_simultaneous(schedule, rte)
    schedule[['g', 'd', 'price']] = frame[['g', 'd', 'price']]
    schedule['h2_kg'] = sum(schedule[plant['id']] * 1e6 / plant['kWh_kg'] for plant in plants)
    years = legacy.year_fraction(frame)
    profit = -float(answer.fun)
    delta = (profit - baseline['annual_incremental_profit_mGBP']) * 1e6
    installed = {name: int(round(answer.x[index])) for name, index in counts.items()}
    assert all(abs(answer.x[index] - installed[name]) < 2e-6 for name, index in counts.items())
    summary = dict(policy=policy, battery_case=battery_case, original_years=years, roundtrip_efficiency=rte,
        nominal_battery_MWh_if_fixed=nominal_MWh, maximum_usable_AC_stock_GWh=float(schedule.stock.max()),
        nominal_battery_MWh_to_reproduce_schedule=float(schedule.stock.max() * 1000 / (.6 * math.sqrt(rte))),
        annual_reference_receipts_mGBP=ref, annual_incremental_profit_mGBP=profit,
        no_battery_profit_mGBP=baseline['annual_incremental_profit_mGBP'],
        annual_additional_profit_GBP=delta,
        annual_additional_profit_upper_bound_GBP=(upper - baseline['annual_incremental_profit_mGBP']) * 1e6,
        annual_charge_MWh=float(schedule.charge.sum() * 1000 / years),
        annual_battery_sale_MWh=float(schedule.battery_sale.sum() * 1000 / years),
        annual_battery_h2_MWh=float(schedule.battery_h2.sum() * 1000 / years),
        annual_sales_GWh=float((schedule.direct + schedule.battery_sale).sum() / years),
        annual_hydrogen_tonnes=float(schedule.h2_kg.sum() / (1000 * years)),
        electrolyser_units=installed,
        electrolyser_MW=sum(plant['MW'] * installed[plant['id']] for plant in plants),
        solver_runs=solver_runs)
    summary['audit'] = audit(schedule, summary, plants, config, rte, capacity)
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    name = f'{policy}_{battery_case}'
    schedule.to_csv(out / f'{name}_schedule.csv', index_label='date')
    (out / f'{name}.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print('FINISHED', name, f'{delta:,.2f} GBP/year added', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('policy', choices=['A', 'B'])
    parser.add_argument('battery_case', choices=['one_reference', 'uncapped'])
    parser.add_argument('--seconds', type=int, default=180)
    args = parser.parse_args()
    run(args.policy, args.battery_case, args.seconds)
