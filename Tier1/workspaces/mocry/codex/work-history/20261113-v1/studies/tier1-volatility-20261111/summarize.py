"""Export and check the sensitivity sweep, and plot the price-only entry points."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sweep import data, data_costs, max_gap_factor, stress


ROOT = Path(__file__).resolve().parent


def make_plot(table, price_brackets):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.0), layout="constrained")
    for ax, policy, color, limits in zip(axes, "AB", ("#1c5784", "#ad4d1c"),
                                         ((39.93, 40.01), (126.83, 127.01))):
        rows = table[(table.policy == policy) & (table.path == "price")
                     & table.factor.between(*limits)]
        ax.scatter(rows.factor, rows.battery_MWh, c=color, s=19, zorder=3)
        a, b = price_brackets[policy]
        ax.axvspan(a, b, alpha=.16, color=color)
        ax.axvline(b, color=color, alpha=.55, lw=.8)
        ax.set(xlabel="Multiplier on historical price standard deviation",
               ylabel="Optimal nominal battery capacity (MWh)",
               title=("A  Economic dispatch" if policy == "A" else "B  Supply first"),
               xlim=limits)
        ticks = [39.94, 39.96, 39.98, 40.00] if policy == "A" else [126.85, 126.90, 126.95, 127.00]
        ax.set_xticks(ticks, [f"{tick:.2f}" for tick in ticks])
        ax.set_ylim(-30, 950)
        ax.grid(axis="y", linewidth=.5, color="#dce0e4")
        ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(ROOT / "price-entry.png", dpi=190)
    plt.close(fig)


def main():
    cases = [json.loads(path.read_text(encoding="utf-8")) for path in (ROOT/"cases").glob("*.json")]
    table = pd.DataFrame(cases)
    table = table[~table.forced & table.stock_limit_GWh.isna()] if "stock_limit_GWh" in table else table[~table.forced]
    table = table.sort_values(["path", "policy", "factor"]).reset_index(drop=True)
    assert table.objective_lower_GBP.notna().all()
    assert (table.objective_upper_GBP >= table.objective_lower_GBP - .005).all()
    assert table.decision.isin(["zero_within_50p", "positive"]).all()
    config, batteries, _ = data_costs()
    capacities = {b["id"]: b["E_MWh"] for group in batteries for b in group}
    for row in table.itertuples():
        assert abs(sum(capacities[name] * count for name, count in row.counts.items()) - row.battery_MWh) < 1e-7
        if row.decision == "zero_within_50p":
            assert row.battery_MWh == 0 and row.objective_upper_GBP < .5
        else:
            assert row.battery_MWh > 0 and row.objective_lower_GBP > row.zero_upper_minus_feasible_GBP + .5
        g, d, p = stress(row.factor if row.path in ("gap", "both") else 1,
                         row.factor if row.path in ("price", "both") else 1)
        assert np.min(g) >= 0 and np.min(d) >= 0
        assert np.isclose(p.min(), row.price_min) and np.isclose(p.max(), row.price_max)
    limit = max_gap_factor()
    brackets = {}
    for policy in "AB":
        for path in ("gap", "both"):
            subset = table[(table.policy == policy) & (table.path == path)]
            assert subset.decision.eq("zero_within_50p").all()
            assert set(range(1, 29)).issubset(set(subset.factor))
            assert (subset.factor - limit).abs().min() < 1e-10
        sub = table[(table.policy == policy) & (table.path == "price")]
        positive = sub[sub.decision == "positive"].iloc[0]
        zero = sub[(sub.factor < positive.factor) & (sub.decision == "zero_within_50p")].iloc[-1]
        brackets[policy] = (zero.factor, positive.factor)
        print(policy, brackets[policy], "first positive tested MWh", positive.battery_MWh,
              "gain GBP/year", positive.objective_lower_GBP)
    table["gap_multiplier"] = np.where(table.path.isin(["gap", "both"]), table.factor, 1)
    table["price_multiplier"] = np.where(table.path.isin(["price", "both"]), table.factor, 1)
    g, d, p = data()
    table["gap_std_GWh"] = table.gap_multiplier * (g-d).std()
    table["price_std_GBP_MWh"] = table.price_multiplier * p.std()
    table["counts"] = table.counts.map(json.dumps)
    table.to_csv(ROOT / "sensitivity.csv", index=False)
    make_plot(table, brackets)
    print("Verified", len(table), "optimal decision cases. Price mean/std", p.mean(), p.std(),
          "Gap mean/std", (g-d).mean(), (g-d).std(), "Gap factor ceiling", limit)


if __name__ == "__main__":
    main()
