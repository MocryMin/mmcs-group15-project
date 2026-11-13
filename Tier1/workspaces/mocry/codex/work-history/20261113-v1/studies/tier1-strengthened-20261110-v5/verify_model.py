"""Behavioural tests and independent reconciliation of saved daily schedules."""
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pandas as pd

import legacy_model as legacy
import model

ROOT = Path(__file__).resolve().parent


def check(frame, econ, summary, s):
    g, d, p = (frame[k].to_numpy() for k in ('g', 'd', 'price'))
    nb, nh = summary['battery_modules'], summary['electrolyser_modules']
    previous = np.r_[0., s.stock.to_numpy()[:-1]]
    errors = {
        'generation_balance': np.max(np.abs(s.direct + s.charge + s.generation_h2 + s.unused - g)),
        'h2_sources': np.max(np.abs(s.h2_input - s.generation_h2 - s.discharge_h2)),
        'daily_stock_balance': np.max(np.abs(s.stock - previous - econ.eta * s.charge +
                                            (s.discharge_sale + s.discharge_h2) / econ.eta)),
        'minimum_stock': max(0., -float(s.stock.min())),
        'maximum_stock': max(0., float(s.stock.max() - nb * econ.usable)),
        'final_stock': abs(float(s.stock.iloc[-1])),
        'sales_ceiling': max(0., float((s.sales - d).max())),
        'hydrogen_acceptance': max(0., float((s.h2_kg - summary['cap_kg_day']).max())) / econ.kg_per_gwh,
        'electrolyser_capacity': max(0., float((s.h2_input - nh * econ.h2_unit).max())),
        'no_same_day_opposite_flows': float(np.minimum(s.charge, s.discharge_sale + s.discharge_h2).max()),
        'nonnegative_flows': max(0., -float(s[['direct', 'charge', 'discharge_sale', 'discharge_h2',
                                               'generation_h2', 'h2_input', 'unused']].min().min())),
    }
    online = s.online_modules.to_numpy()
    errors['online_minimum'] = max(0., float(np.max(online * econ.h2_min * econ.h2_unit - s.h2_input)))
    errors['online_capacity'] = max(0., float(np.max(s.h2_input - online * econ.h2_unit)))
    errors['installed_modules'] = max(0., float(np.max(online - nh)))
    if summary['policy'] == 'B':
        errors['current_generation_priority'] = float(np.max(abs(s.direct - np.minimum(g, d))))
        if summary['specification']['battery_supply_priority']:
            expected = np.minimum(np.maximum(d - g, 0), econ.eta * previous)
            errors['battery_priority'] = float(np.max(abs(s.discharge_sale - expected)))
            errors['no_h2_discharge_with_unmet_demand'] = float(np.max(
                np.where(s.unserved > 2e-5, s.discharge_h2, 0)))
    ref = np.dot(p, legacy.direct_reference(frame, summary['policy'])) / (1000 * legacy.year_fraction(frame))
    revenue = (np.dot(p, s.sales) / 1000 + s.h2_kg.sum() * econ.netback / 1e6) / legacy.year_fraction(frame)
    cost = nb * econ.battery_annual + nh * econ.hydrogen_annual
    money_error = abs(revenue - ref - cost - summary['annual_incremental_profit_mGBP'])
    assert max(errors.values()) < 3e-5, errors
    assert money_error < 1e-5, money_error
    return dict(errors_GWh=errors, profit_error_mGBP=money_error)


def frame(g, d, p):
    return pd.DataFrame(dict(g=g, d=d, price=p), index=pd.date_range('2023-01-01', periods=len(g)))


def tests():
    econ = legacy.economics()
    cases = {}
    data = frame([.22, 0.], [0., 0.], [0., 0.])
    cap = .1 * econ.kg_per_gwh
    for backend in ('highs', 'xpress'):
        name = 'stored_energy_to_hydrogen_' + backend
        summary, s = model.solve(data, econ, 'A', cap, fixed=(100, 1), backend=backend)
        assert s.discharge_h2.iloc[1] > .09999 and s.h2_input.iloc[1] > .09999
        cases[name] = dict(summary=summary, audit=check(data, econ, summary, s))
    assert abs(cases['stored_energy_to_hydrogen_highs']['summary']['annual_incremental_profit_mGBP'] -
               cases['stored_energy_to_hydrogen_xpress']['summary']['annual_incremental_profit_mGBP']) < 1e-7
    spec = replace(model.Specification(), battery_to_hydrogen=False)
    summary, s = model.solve(data, econ, 'A', cap, fixed=(100, 1), spec=spec)
    assert abs(s.h2_input.iloc[1]) < 1e-8
    cases['route_disabled_control'] = dict(summary=summary, audit=check(data, econ, summary, s))
    reverse = frame([0., .22], [0., 0.], [0., 0.])
    summary, s = model.solve(reverse, econ, 'A', cap, fixed=(100, 1))
    assert abs(s.h2_input.iloc[0]) < 1e-8 and abs(s.stock.iloc[0]) < 1e-8
    cases['no_borrowing_from_future'] = dict(summary=summary, audit=check(reverse, econ, summary, s))
    data = frame([.32, 0.], [0., .05], [0., 0.])
    summary, s = model.solve(data, econ, 'B', cap, fixed=(100, 1))
    assert abs(s.discharge_sale.iloc[1] - .05) < 1e-8
    assert s.discharge_h2.iloc[1] > .09999 and abs(s.unserved.iloc[1]) < 1e-8
    cases['B_hydrogen_after_demand_filled'] = dict(summary=summary, audit=check(data, econ, summary, s))
    data = frame([.35, 0.], [0., .3], [0., 100.])
    summary, s = model.solve(data, econ, 'B', cap, fixed=(100, 1))
    assert s.unserved.iloc[1] > .1 and abs(s.discharge_h2.iloc[1]) < 1e-8
    cases['B_no_hydrogen_before_demand_filled'] = dict(summary=summary, audit=check(data, econ, summary, s))
    data = frame([.35, 0., 0.], [0., .05, .1], [0., -10., 300.])
    for policy in ('A', 'B'):
        summary, s = model.solve(data, econ, policy, 0., fixed=(100, 0))
        if policy == 'B':
            assert abs(s.discharge_sale.iloc[1] - .05) < 1e-8
        else:
            assert abs(s.discharge_sale.iloc[1]) < 1e-8
        cases['negative_price_supply_priority_' + policy] = dict(summary=summary, audit=check(data, econ, summary, s))
    summary, s = model.solve(data, econ, 'B', 0., battery=False, hydrogen=False)
    cases['zero_investment_feasible_B'] = dict(summary=summary, audit=check(data, econ, summary, s))
    # Same fixed reference asset as v4.1: battery=0 removes all new route/state effects.
    annual = legacy.load_data().loc['2023']
    for policy in ('A', 'B'):
        summary, s = model.solve(annual, econ, policy, 10000, fixed=(0, 1))
        old = legacy.solve(annual, econ, policy, fixed=(0, 1))[0]
        assert abs(summary['annual_incremental_profit_mGBP'] - old['net']) < 1e-6
        cases['legacy_fixed20_match_' + policy] = dict(summary=summary, audit=check(annual, econ, summary, s),
                                                     old_net=old['net'])
    (ROOT / 'results' / 'behavioural_checks.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PASS',len(cases),'behavioural and solver checks', flush=True)


if __name__ == '__main__':
    tests()
