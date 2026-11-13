"""Daily chronological Tier 1 model with battery-to-electrolyser routing.

Daily quantities are GWh. Objective is GBP2020 million per represented year.
SciPy/HiGHS handles full studies; the same rows can be solved by Xpress.
No client trading/budget limit is inferred from a solver's licence restriction.
"""
from dataclasses import asdict, dataclass, replace
import json
import math
import os
from pathlib import Path
import time
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

import legacy_model as legacy

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Specification:
    battery_to_hydrogen: bool = True
    battery_supply_priority: bool = True
    enforce_net_daily_operation: bool = True
    battery_unit_MWh: float = 3.0
    battery_unit_MW: float = 1.5
    electrolyser_unit_MW: float = 20.0


class Rows:
    def __init__(self):
        self.names, self.lower, self.upper, self.integer, self.objective = [], [], [], [], []
        self.rows, self.cols, self.values, self.row_lower, self.row_upper = [], [], [], [], []

    def variable(self, name, upper=np.inf, lower=0., integer=False, objective=0.):
        i = len(self.names)
        self.names.append(name)
        self.lower.append(float(lower)); self.upper.append(float(upper))
        self.integer.append(int(integer)); self.objective.append(float(objective))
        return i

    def constraint(self, coefficients, lower=-np.inf, upper=np.inf):
        row = len(self.row_lower)
        for col, value in coefficients.items():
            if value:
                self.rows.append(row); self.cols.append(col); self.values.append(float(value))
        self.row_lower.append(float(lower)); self.row_upper.append(float(upper))

    def matrix(self):
        return coo_matrix((self.values, (self.rows, self.cols)),
                          shape=(len(self.row_lower), len(self.names))).tocsc()


def solve(frame, econ, policy, cap_kg_day, *, spec=Specification(), fixed=None,
          battery=True, hydrogen=True, backend='highs', seconds=240, relative_gap=1e-7):
    assert policy in ('A', 'B')
    assert (frame.index.to_series().diff().dropna() == pd.Timedelta(days=1)).all()
    assert spec.battery_unit_MWh == 2 * spec.battery_unit_MW
    assert spec.battery_unit_MWh == 3 and spec.electrolyser_unit_MW == 20, 'Costs need explicit rebasing for another grid.'
    years = legacy.year_fraction(frame)
    g, d, p = (frame[k].to_numpy(dtype=float) for k in ('g', 'd', 'price'))
    eta, usable = econ.eta, econ.usable
    hcap = float(cap_kg_day / econ.kg_per_gwh)
    h_unit, h_min = econ.h2_unit, econ.h2_min * econ.h2_unit
    baseline = legacy.direct_reference(frame, policy)
    ref = float(np.dot(p, baseline) / (1000 * years))

    # The zero-investment solution is feasible. Total nonnegative receipts cannot
    # exceed full positive-price electricity demand plus the H2 acceptance bound.
    # A positive annual equipment cost therefore gives a safe capacity upper bound.
    receipts_ceiling = float((np.dot(np.maximum(p, 0), d) / 1000 +
                              len(g) * cap_kg_day * max(econ.netback, 0) / 1e6) / years)
    b_bound = max(0, math.ceil(max(0, receipts_ceiling - ref) / econ.battery_annual)) if battery else 0
    h_bound = math.ceil(hcap / h_unit) if hydrogen else 0
    if fixed is not None:
        b_bound, h_bound = fixed
    U = b_bound * usable
    m = Rows()
    m.variable('reference_revenue_offset', lower=1, upper=1, objective=ref)
    nb = m.variable('battery_modules', b_bound, fixed[0] if fixed else 0,
                    integer=True, objective=econ.battery_annual)
    nh = m.variable('electrolyser_modules', h_bound, fixed[1] if fixed else 0,
                    integer=True, objective=econ.hydrogen_annual)
    variables = {k: [] for k in ('direct', 'charge', 'discharge_sale', 'discharge_h2',
                                 'generation_h2', 'h2_input', 'stock', 'h2_on', 'charge_mode', 'priority_mode')}
    for t in range(len(g)):
        revenue_power = -p[t] / (1000 * years)
        qmax = min(g[t], d[t])
        q = m.variable(f'direct_{t}', qmax, qmax if policy == 'B' else 0, objective=revenue_power)
        c = m.variable(f'charge_{t}', min(g[t], U / eta))
        re = m.variable(f'discharge_sale_{t}', min(d[t], U * eta), objective=revenue_power)
        rh = m.variable(f'discharge_h2_{t}', min(hcap, U * eta) if spec.battery_to_hydrogen else 0)
        hg = m.variable(f'generation_h2_{t}', min(g[t], hcap))
        h = m.variable(f'h2_input_{t}', hcap, objective=-econ.netback * econ.kg_per_gwh / (1e6 * years))
        s = m.variable(f'stock_{t}', U)
        on = m.variable(f'h2_on_{t}', 1 if h_bound else 0, integer=True)
        mode = m.variable(f'charge_mode_{t}', 1 if b_bound else 0, integer=True)
        priority = m.variable(f'priority_mode_{t}', 1 if b_bound and policy == 'B' and d[t] > g[t] and t else 0,
                              integer=True)
        for k, v in zip(variables, (q, c, re, rh, hg, h, s, on, mode, priority)):
            variables[k].append(v)
        m.constraint({q: 1, c: 1, hg: 1}, upper=g[t])
        m.constraint({q: 1, re: 1}, upper=d[t])
        m.constraint({h: 1, hg: -1, rh: -1}, lower=0, upper=0)
        balance = {s: 1, c: -eta, re: 1 / eta, rh: 1 / eta}
        if t:
            balance[variables['stock'][t - 1]] = -1
        m.constraint(balance, lower=0, upper=0)
        m.constraint({s: 1, nb: -usable}, upper=0)
        m.constraint({c: eta, nb: -usable}, upper=0)
        m.constraint({re: 1 / eta, rh: 1 / eta, nb: -usable}, upper=0)
        m.constraint({c: 1, nb: -24 * spec.battery_unit_MW / 1000}, upper=0)
        m.constraint({re: 1, rh: 1, nb: -24 * spec.battery_unit_MW / 1000}, upper=0)
        if spec.enforce_net_daily_operation:
            m.constraint({c: 1, mode: -min(g[t], U / eta)}, upper=0)
            mr = min(U * eta, d[t] + (hcap if spec.battery_to_hydrogen else 0))
            m.constraint({re: 1, rh: 1, mode: mr}, upper=mr)
        m.constraint({h: 1, nh: -h_unit}, upper=0)
        m.constraint({h: 1, on: -hcap}, upper=0)
        m.constraint({h: 1, on: -h_min}, lower=0)
        # The online-module intervals [0.2 z H, z H] overlap for z>=1.
        # Thus binary on + installed-capacity bound is exactly equivalent to
        # the former integer online-module formulation, for this 20% fraction.
        if policy == 'B' and spec.battery_supply_priority and b_bound and d[t] > g[t] + 1e-10:
            deficit = d[t] - g[t]
            # On a deficit day B leaves no current generation for charging/H2.
            # Available discharge first serves min(deficit, eta * prior stock).
            if t:
                previous = variables['stock'][t - 1]
                m.constraint({re: 1, previous: -eta}, upper=0)
                m.constraint({re: 1, priority: deficit}, lower=deficit)
                m.constraint({re: 1, previous: -eta, priority: -eta * U}, lower=-eta * U)
            else:
                m.constraint({re: 1}, lower=0, upper=0)
    m.constraint({variables['stock'][-1]: 1}, lower=0, upper=0)
    matrix = m.matrix()
    started = time.perf_counter()
    if backend == 'xpress':
        import xpress as xp
        license_path = os.environ.get('XPRESS_LICENSE_FILE')
        if license_path:
            xp.init(license_path)
        elif Path('C:/xpressmp/bin/xpauth.xpr').exists():
            xp.init('C:/xpressmp/bin/xpauth.xpr')
        problem = xp.problem()
        problem.controls.outputlog = 0
        problem.controls.threads = 8
        problem.controls.maxtime = seconds
        problem.controls.miprelstop = relative_gap
        problem.controls.miprelcutoff = 0
        xv = [problem.addVariable(lb=l, ub=u, vartype=xp.integer if i else xp.continuous)
              for l, u, i in zip(m.lower, m.upper, m.integer)]
        csr = matrix.tocsr()
        for row, (lo, hi) in enumerate(zip(m.row_lower, m.row_upper)):
            expr = xp.Sum(csr.data[j] * xv[csr.indices[j]] for j in range(csr.indptr[row], csr.indptr[row + 1]))
            if lo == hi:
                problem.addConstraint(expr == lo)
            else:
                if np.isfinite(lo): problem.addConstraint(expr >= lo)
                if np.isfinite(hi): problem.addConstraint(expr <= hi)
        problem.setObjective(xp.Sum(a * v for a, v in zip(m.objective, xv)), xp.minimize)
        problem.solve()
        if problem.attributes.solstatus != 1:
            raise RuntimeError(f'Xpress not optimal: {problem.attributes.solstatus}')
        x = np.asarray(problem.getSolution(xv))
        solver_data = dict(solver='FICO Xpress 9.9', status=0, optimal=True, gap=0.,
                           message='Xpress solstatus=1')
    else:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Unrecognized options detected')
            result = milp(np.asarray(m.objective), integrality=np.asarray(m.integer),
                          bounds=Bounds(m.lower, m.upper),
                          constraints=LinearConstraint(matrix, m.row_lower, m.row_upper),
                          options=dict(time_limit=seconds, mip_rel_gap=relative_gap,
                                       threads=8, random_seed=0))
        if result.x is None:
            raise RuntimeError(result.message)
        x = result.x
        solver_data = dict(solver='SciPy/HiGHS', status=int(result.status), optimal=result.status == 0,
                           gap=float(result.mip_gap), message=result.message,
                           minimization_dual_bound=float(result.mip_dual_bound))
    elapsed = time.perf_counter() - started
    schedule = pd.DataFrame({k: x[v] for k, v in variables.items()}, index=frame.index)
    schedule[['generation', 'demand', 'price']] = frame[['g', 'd', 'price']].to_numpy()
    schedule['unused'] = g - schedule.direct - schedule.charge - schedule.generation_h2
    schedule['sales'] = schedule.direct + schedule.discharge_sale
    schedule['unserved'] = d - schedule.sales
    schedule['h2_kg'] = schedule.h2_input * econ.kg_per_gwh
    schedule['stock_total_GWh'] = schedule.stock + .2 * spec.battery_unit_MWh / 1000 * x[nb]
    # Reconstruct a valid integer online-module count for audit/output.
    schedule['online_modules'] = np.where(schedule.h2_input > 1e-7,
                                         np.ceil(schedule.h2_input / h_unit - 1e-8), 0)
    receipts = float(np.dot(p, schedule.sales) / (1000 * years) +
                     schedule.h2_kg.sum() * econ.netback / (1e6 * years))
    cost = float(x[nb] * econ.battery_annual + x[nh] * econ.hydrogen_annual)
    summary = dict(policy=policy, days=len(frame), years=years,
                   battery_modules=int(round(x[nb])), electrolyser_modules=int(round(x[nh])),
                   battery_MWh=float(x[nb] * spec.battery_unit_MWh),
                   battery_MW=float(x[nb] * spec.battery_unit_MW),
                   electrolyser_MW=float(x[nh] * spec.electrolyser_unit_MW),
                   cap_kg_day=cap_kg_day, annual_incremental_profit_mGBP=receipts - ref - cost,
                   annual_receipts_mGBP=receipts, annual_reference_receipts_mGBP=ref,
                   annual_equipment_cost_mGBP=cost,
                   initial_capex_mGBP=float(x[nb] * econ.battery_capex + x[nh] * econ.hydrogen_capex),
                   annual_h2_tonnes=float(schedule.h2_kg.sum() / (1000 * years)),
                   annual_sales_GWh=float(schedule.sales.sum() / years),
                   annual_unserved_GWh=float(schedule.unserved.sum() / years),
                   demand_coverage=float(schedule.sales.sum() / d.sum()) if d.sum() else None,
                   annual_unused_GWh=float(schedule.unused.sum() / years),
                   annual_battery_to_h2_GWh=float(schedule.discharge_h2.sum() / years),
                   annual_battery_to_sales_GWh=float(schedule.discharge_sale.sum() / years),
                   safe_capacity_bounds=dict(battery_modules=b_bound, electrolyser_modules=h_bound),
                   variables=len(x), rows=matrix.shape[0], elapsed_s=elapsed,
                   specification=asdict(spec), economics=asdict(econ), **solver_data)
    # Generic sparse-row feasibility is independent of the schedule calculations.
    ax = matrix @ x
    violation = max(float(np.maximum(np.asarray(m.row_lower) - ax, 0).max(initial=0)),
                    float(np.maximum(ax - np.asarray(m.row_upper), 0).max(initial=0)),
                    float(np.maximum(np.asarray(m.lower) - x, 0).max(initial=0)),
                    float(np.maximum(x - np.asarray(m.upper), 0).max(initial=0)))
    integral = max((abs(x[i] - round(x[i])) for i, k in enumerate(m.integer) if k), default=0.)
    assert violation < 2e-5 and integral < 2e-5, (violation, integral)
    summary['matrix_feasibility_error_GWh'] = violation
    summary['integrality_error'] = float(integral)
    return summary, schedule


def save(case, result):
    summary, schedule = result
    directory = ROOT / 'results'
    directory.mkdir(exist_ok=True)
    schedule.to_csv(directory / f'{case}_schedule.csv', index_label='date')
    (directory / f'{case}.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(case, json.dumps({k: summary[k] for k in ('battery_MWh', 'electrolyser_MW',
          'annual_incremental_profit_mGBP', 'gap', 'elapsed_s', 'optimal')}, ensure_ascii=False), flush=True)
    return summary
