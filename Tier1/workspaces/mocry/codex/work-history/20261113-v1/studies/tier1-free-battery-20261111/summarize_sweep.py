"""Combine solved intervals, including the already certified capacity plateaus."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from capacity_sweep import CAPACITIES, OUT, PLATEAU_FROM, ROOT, case_file, read_json


def bounds_by_policy(policy):
    root = ROOT / 'results'
    if policy == 'A':
        uncapped = read_json(root / 'A_uncapped.json')
        plateau = (uncapped['annual_additional_profit_GBP'], uncapped['annual_additional_profit_upper_bound_GBP'])
        plateau_MW = uncapped['electrolyser_MW']
    else:
        best = read_json(root / 'B_max_profit.json')
        old = read_json(root / 'B_uncapped.json')
        plateau = (best['annual_additional_profit_GBP'], min(old['annual_additional_profit_upper_bound_GBP'],
                                                           best['maximum_additional_profit_upper_bound_GBP']))
        plateau_MW = best['electrolyser_MW']
    records = []
    for capacity in CAPACITIES:
        if capacity == 0:
            lo, hi, mw, source = 0., 0., None, 'v6 no battery'
        elif capacity >= PLATEAU_FROM[policy]:
            lo, hi = plateau
            mw, source = plateau_MW, 'certified plateau'
        else:
            case = read_json(case_file(policy, capacity))
            lo, hi = case['annual_gain_GBP'], case['annual_gain_upper_GBP']
            mw, source = case['electrolyser_MW'], case_file(policy, capacity).name
        records.append(dict(nominal_MWh=capacity, lower=lo, upper=hi, achieved_electrolyser_MW=mw, source=source))

    # A larger free store can reproduce any smaller store's feasible plan.
    best = records[0]
    for row in records:
        if row['lower'] < best['lower']:
            row['lower'], row['achieved_electrolyser_MW'], row['source'] = (
                best['lower'], best['achieved_electrolyser_MW'], best['source'])
        best = row
    upper = np.inf
    for row in reversed(records):
        upper = min(upper, row['upper'])
        assert row['lower'] <= upper + .1, (policy, row, upper)
        row['upper'] = max(upper, row['lower'])
    return records


def figure(table):
    plot = table[table.nominal_MWh > 0]
    fig, axes = plt.subplots(2, 1, figsize=(10, 7.4), sharex=True, layout='constrained')
    for label, name, color in [('A', 'A  Economic dispatch', '#244d79'), ('B', 'B  Supply first', '#b55717')]:
        x = plot.nominal_MWh.to_numpy()
        lower = plot[f'{label}_lower_GBP_year'].to_numpy()
        upper = plot[f'{label}_upper_GBP_year'].to_numpy()
        axes[0].plot(x, lower / 1e6, 'o-', label=name, color=color, markersize=4, linewidth=1.7)
        axes[0].fill_between(x, lower / 1e6, upper / 1e6, color=color, alpha=.22)
        axes[1].plot(x, lower / x, 'o-', color=color, markersize=4, linewidth=1.7)
        axes[1].fill_between(x, lower / x, upper / x, color=color, alpha=.22)
    axes[0].legend(frameon=False)
    axes[0].set_ylabel('Additional profit (£m per year)')
    axes[1].set_ylabel('Additional profit per MWh installed (£/year)')
    axes[1].set_xlabel('Nominal free battery capacity')
    for axis in axes:
        axis.set_xscale('log')
        axis.set_yscale('log')
        axis.grid(visible=True, which='major', color='#dce0e3', linewidth=.6)
        axis.spines[['top', 'right']].set_visible(False)
    axes[1].set_xticks([3, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000],
                       ['3 MWh', '100 MWh', '1 GWh', '10 GWh', '100 GWh', '1 TWh', '10 TWh', '100 TWh'])
    fig.suptitle('Value of free storage in the 2020–2025 MMCS historical dispatch', fontsize=13)
    fig.savefig(OUT / 'capacity_value.png', dpi=190)
    plt.close(fig)


def summarize():
    a, b = bounds_by_policy('A'), bounds_by_policy('B')
    rows = []
    for ar, br in zip(a, b):
        assert ar['nominal_MWh'] == br['nominal_MWh']
        record = dict(nominal_MWh=ar['nominal_MWh'])
        for policy, item in [('A', ar), ('B', br)]:
            record.update({f'{policy}_lower_GBP_year': item['lower'], f'{policy}_upper_GBP_year': item['upper'],
                           f'{policy}_electrolyser_MW': item['achieved_electrolyser_MW'], f'{policy}_source': item['source']})
        rows.append(record)
    table = pd.DataFrame(rows)
    table.to_csv(OUT / 'capacity_value.csv', index=False, float_format='%.8f')
    figure(table)
    print(table.iloc[:, [0, 1, 2, 5, 6]].to_string(index=False))


if __name__ == '__main__':
    summarize()
