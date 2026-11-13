"""Map the incremental dispatch value of one 3 MWh battery in v6."""

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "tier1-volatility-20261111"))
from sweep import V6, check, costs, data, data_costs, make_model, max_gap_factor, solve, stress, unpack
from run_study import reference_assets

PRICE_FACTORS = (1, 2, 4, 8, 12, 16, 24, 32, 40, 50, 64, 80, 100, 127, 150, 175)
GAP_FACTORS = (1, 1.5, 2, 3, 4, 6, 8, 10, 12, 16, 20, 24)


def assets(policy):
    config, _, all_plants = data_costs()
    original = json.loads((V6 / "results" / f"{policy}_comparable_main.json").read_text(encoding="utf-8"))
    fixed = {i["id"]: i["count"] for i in original["investment"]
             if i["kind"] == "electrolyser" and i["count"]}
    plants = [h for h in all_plants if h["id"] in fixed]
    assert {h["id"] for h in plants} == set(fixed)
    with_reference = reference_assets(config, True)
    batteries, _ = costs(with_reference)
    battery = next(b for b in batteries if b["id"] == "v5-reference-battery")
    return config, battery, plants, fixed


def optimize(g, d, p, policy, config, battery, plants, fixed_h, fixed_battery, reference, bad):
    groups = [[battery]] if fixed_battery else []
    fixed_b = {battery["id"]: 1} if fixed_battery else None
    usable = battery["usable"] * battery["eta"] if fixed_battery else 0.
    available_for_h2 = g + usable if policy == "A" else (
        np.maximum(g - d, 0.) + np.maximum(usable - np.maximum(d - g, 0.), 0.)
    )
    bad = {(name, t) for name, t in bad if available_for_h2[t] >= next(
        h["minimum"] * h["unit_GWh"] for h in plants if h["id"] == name)}
    center = reference
    for _ in range(16):
        m, columns, h, b, modes = make_model(g, d, p, policy, config, groups, plants,
                                           fixed_battery, center, bad, True, fixed=fixed_b)
        for name, index in h.items():
            m.lo[index] = m.hi[index] = fixed_h[name]
            m.integer[index] = 0
        for index in b.values():
            m.integer[index] = 0
        for plant in plants:
            minimum = plant["minimum"] * plant["unit_GWh"]
            for t in np.flatnonzero(available_for_h2 < minimum - 1e-9):
                m.hi[columns[plant["id"]][t]] = 0.
        x, objective, upper, status = solve(m, 25, 1)
        flows, hc, bc, _ = unpack(x, columns, h, b, modes)
        cleaned, added, priority, value = check(flows, hc | bc, g, d, p, policy, config, groups, plants)
        if not added:
            assert priority < 2e-7
            assert abs(value - center - objective) < 2e-7
            assert upper - objective < 5e-7, (status, upper, objective)
            return value, upper + center - reference, cleaned, bad
        assert added - bad
        bad = bad | added
        if not fixed_battery:
            center = value
    raise RuntimeError("Minimum load refinement did not converge")


def one_cell(task):
    policy, gap_factor, price_factor = task
    g, d, p = stress(gap_factor, price_factor)
    config, battery, plants, fixed = assets(policy)
    zero_cost = battery | {"annual": 0.0}
    try:
        baseline, baseline_upper, _, bad = optimize(g, d, p, policy, config, battery, plants, fixed, False, 0, set())
        use, gain_upper, flows, _ = optimize(g, d, p, policy, config, zero_cost, plants, fixed, True, baseline, bad)
    except (AssertionError, RuntimeError) as error:
        raise RuntimeError(f"{task}: {error}") from error
    fixed_annual = battery["annual"] * 1e6
    assert -0.02 < (use - baseline) * 1e6 <= gain_upper * 1e6 + .02
    gap = g - d
    usable_ac_mwh = 1000 * battery["usable"] * battery["eta"]
    return {
        "policy": policy, "gap_std_multiplier": gap_factor, "price_std_multiplier": price_factor,
        "annual_additional_operating_value_GBP2020": max(0.0, (use - baseline) * 1e6),
        "annual_additional_upper_GBP2020": max(0.0, gain_upper * 1e6),
        "zero_battery_solve_gap_GBP2020": (baseline_upper - baseline) * 1e6,
        "annualised_battery_cost_GBP2020": fixed_annual,
        "annual_increment_after_battery_cost_GBP2020": (use - baseline) * 1e6 - fixed_annual,
        "annual_charge_MWh": float(flows["charge_0"].sum() * 1000 / 6),
        "annual_discharge_to_sale_MWh": float(flows["sale_0"].sum() * 1000 / 6),
        "annual_discharge_to_h2_MWh": float(flows["hydrogen_0"].sum() * 1000 / 6),
        "surplus_days": int((gap > 0).sum()), "deficit_days": int((gap < 0).sum()),
        "days_with_enough_raw_surplus_to_fill_battery": int((gap * 1000 >= usable_ac_mwh / battery["rte"]).sum()),
        "days_with_enough_raw_deficit_to_empty_battery": int((-gap * 1000 >= usable_ac_mwh).sum()),
    }


def theoretical_upper():
    g, d, prices = data()
    config, groups, all_hydrogen = data_costs()
    _, battery, _, _ = assets("A")
    max_hydrogen_value = max(1000 * config["netback"] / h["kWh_kg"] for h in all_hydrogen)
    usable = battery["usable"] * battery["eta"] * 1000
    cycles = len(prices) // 2
    electricity_top = np.sort(np.maximum(prices, 0))[-cycles:]
    all_outlets_top = np.sort(np.maximum(prices, max_hydrogen_value))[-cycles:]
    def chronological(values):
        empty, full = 0., -np.inf
        for value in values:
            empty, full = max(empty, full + usable * value), max(full, empty)
        return empty / 6

    relaxation_gaps = {}
    for policy in "AB":
        m, _, _, _, _ = make_model(g, d, prices, policy, config, groups, all_hydrogen,
                                   False, 0, set(), False)
        _, _, bound, _ = solve(m, 20, 1)
        original = json.loads((V6 / "results" / f"{policy}_comparable_main.json").read_text(encoding="utf-8"))
        exact = original["annual_operating_receipts_mGBP"] - original["annual_equipment_fixed_cost_mGBP"]
        relaxation_gaps[policy] = (bound - exact) * 1e6
        assert abs(relaxation_gaps[policy]) < .02

    return dict(
        nominal_MWh=battery["E_MWh"], power_MW=battery["P_MW"], rte=battery["rte"],
        usable_sale_MWh_per_full_cycle=usable, dates=len(prices), years=6,
        max_full_equivalent_cycles=cycles,
        theoretical_throughput_MWh_year=usable * cycles / 6,
        electricity_only_output_upper_GBP2020_year=usable * electricity_top.sum() / 6,
        electricity_or_hydrogen_output_upper_GBP2020_year=usable * all_outlets_top.sum() / 6,
        chronological_electricity_only_upper_GBP2020_year=chronological(np.maximum(prices, 0)),
        chronological_electricity_or_hydrogen_upper_GBP2020_year=chronological(np.maximum(prices, max_hydrogen_value)),
        max_h2_value_per_electric_input_GBP2020_MWh=max_hydrogen_value,
        annualised_battery_cost_GBP2020=battery["annual"] * 1e6,
        historical_no_battery_relaxation_upper_minus_v6_GBP2020_year=relaxation_gaps,
    )


def plot(table, upper):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import SymLogNorm
    from matplotlib.ticker import ScalarFormatter

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.65), sharey=True, layout="constrained")
    field = "annual_additional_operating_value_GBP2020"
    norm = SymLogNorm(linthresh=8, linscale=.7, vmin=0, vmax=table[field].max() / 1000)
    for ax, policy, title in zip(axes, "AB", ("A  Economic dispatch", "B  Supply first")):
        rows = table[table.policy == policy]
        grid = rows.pivot(index="price_std_multiplier", columns="gap_std_multiplier", values=field) / 1000
        image = ax.pcolormesh(grid.columns, grid.index, grid, cmap="viridis", norm=norm, shading="nearest")
        breakeven = upper["annualised_battery_cost_GBP2020"] / 1000
        if grid.to_numpy().min() < breakeven < grid.to_numpy().max():
            line = ax.contour(grid.columns, grid.index, grid, levels=[breakeven], colors="white", linewidths=1.4)
            ax.clabel(line, inline=True, fmt={breakeven: "Break-even"}, fontsize=9)
        ax.set(title=title, xlabel="Supply–demand gap standard deviation multiplier",
               xlim=(1, grid.columns.max()), ylim=(1, grid.index.max()), yscale="log")
        ax.set_yticks([1, 2, 4, 8, 16, 32, 64, 127, 175])
        ax.yaxis.set_major_formatter(ScalarFormatter())
        ax.tick_params(axis="both", which="major", labelsize=9)
        ax.set_xticks([1, 4, 8, 12, 16, 20, 24, 28])
    axes[0].set_ylabel("Electricity price standard deviation multiplier")
    colorbar = fig.colorbar(image, ax=axes, fraction=.045, pad=.03)
    colorbar.set_label("Additional annual operating value (£2020 thousand)")
    ticks = [0, 5, 10, 25, 50, 100, 200, 400]
    colorbar.set_ticks(ticks, labels=[str(value) for value in ticks])
    fig.savefig(ROOT / "arbitrage-surface.png", dpi=195)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.6, 3.5), layout="constrained")
    for policy, label, color in [("A", "A  Economic dispatch", "#205480"), ("B", "B  Supply first", "#9e461a")]:
        rows = table[(table.policy == policy) & (table.price_std_multiplier == 1)].sort_values("gap_std_multiplier")
        ax.plot(rows.gap_std_multiplier, rows[field] / 1000, "o-", label=label, color=color, markersize=3.5)
    ax.set(xlabel="Supply–demand gap standard deviation multiplier",
           ylabel="Additional annual operating value (£2020 thousand)", ylim=(0, None))
    ax.legend(frameon=False)
    ax.grid(axis="y", linewidth=.5, color="#dce0e4")
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(ROOT / "gap-only.png", dpi=195)
    plt.close(fig)


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--workers", type=int, default=10)
    options = args.parse_args()
    gaps = (*GAP_FACTORS, max_gap_factor())
    tasks = [(policy, gap, price) for price in PRICE_FACTORS for gap in gaps for policy in "AB"]
    rows = []
    with ProcessPoolExecutor(max_workers=options.workers) as pool:
        for row in pool.map(one_cell, tasks, chunksize=2):
            rows.append(row)
            if len(rows) % 52 == 0:
                print(f"Completed {len(rows)} of {len(tasks)} cases", flush=True)
    table = pd.DataFrame(rows)
    assert len(table) == len(tasks)
    assert table.zero_battery_solve_gap_GBP2020.abs().max() < .51
    assert (table.annual_additional_upper_GBP2020 - table.annual_additional_operating_value_GBP2020).abs().max() < .51
    table.sort_values(["policy", "gap_std_multiplier", "price_std_multiplier"]).to_csv(ROOT / "arbitrage-grid.csv", index=False)
    upper = theoretical_upper()
    (ROOT / "upper-bound.json").write_text(json.dumps(upper, indent=2) + "\n", encoding="utf-8")
    plot(table, upper)
    print(json.dumps(upper, indent=2))
    for policy in "AB":
        print(policy, "fixed historical prices")
        cols = ["gap_std_multiplier", "annual_additional_operating_value_GBP2020",
                "surplus_days", "deficit_days", "annual_discharge_to_sale_MWh"]
        print(table.loc[(table.policy == policy) & (table.price_std_multiplier == 1), cols].to_string(index=False))


if __name__ == "__main__":
    main()
