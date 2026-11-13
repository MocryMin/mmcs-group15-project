"""Check the joint investment grid and export the table and figure."""

import json
from itertools import combinations

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm, Normalize
from matplotlib.ticker import FuncFormatter, LogLocator
import numpy as np
import pandas as pd

from run import CASES, GAP_GRID, PRICE_GRID, ROOT
from sweep import data_costs


def table():
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in CASES.glob("*.json")]
    frame = pd.DataFrame(rows).sort_values(["policy", "gap_std_multiplier", "price_std_multiplier"])
    assert not frame.duplicated(["policy", "gap_std_multiplier", "price_std_multiplier"]).any()
    expected = {(p, g, k) for p in "AB" for g in GAP_GRID for k in PRICE_GRID}
    assert expected.issubset(set(zip(frame.policy, frame.gap_std_multiplier, frame.price_std_multiplier)))
    _, battery_groups, electrolysers = data_costs()
    batteries = {p["id"]: p for group in battery_groups for p in group}
    plants = {p["id"]: p for p in electrolysers}
    for r in frame.itertuples():
        assert abs(r.battery_MWh - sum(batteries[n]["E_MWh"] * c for n, c in r.counts.items())) < 1e-7
        assert abs(r.battery_MW - sum(batteries[n]["P_MW"] * c for n, c in r.counts.items())) < 1e-7
        assert abs(r.battery_annual_cost_GBP - sum(batteries[n]["annual"] * 1e6 * c for n, c in r.counts.items())) < .01
        assert abs(r.electrolyser_MW - sum(plants[n]["MW"] * c for n, c in r.electrolyser_counts.items())) < 1e-7
        assert abs(r.no_battery_electrolyser_MW - sum(plants[n]["MW"] * c for n, c in r.no_battery_electrolyser_counts.items())) < 1e-7
    frame["net_gain_lower_GBP_year"] = (frame.objective_lower_GBP - frame.zero_upper_minus_feasible_GBP.clip(lower=0)).clip(lower=0)
    frame["net_gain_upper_GBP_year"] = frame.objective_upper_GBP.clip(lower=0)
    zero = frame.decision.eq("zero_within_50p")
    assert (frame.loc[zero, "battery_MWh"] == 0).all() and (frame.loc[zero, "net_gain_upper_GBP_year"] < .5).all()
    frame.loc[zero, "net_gain_lower_GBP_year"] = 0
    assert (frame.net_gain_upper_GBP_year >= frame.net_gain_lower_GBP_year - .02).all()
    frame["net_gain_upper_GBP_year"] = np.maximum(frame.net_gain_upper_GBP_year, frame.net_gain_lower_GBP_year)
    frame["net_gain_gap_GBP_year"] = frame.net_gain_upper_GBP_year - frame.net_gain_lower_GBP_year
    frame["chosen_portfolio_value_before_battery_cost_lower_GBP_year"] = (
        frame.net_gain_lower_GBP_year + frame.battery_annual_cost_GBP)
    frame["chosen_portfolio_annual_profit_GBP"] = frame.no_battery_annual_profit_GBP + frame.objective_lower_GBP.clip(lower=0)
    frame.loc[zero, "chosen_portfolio_annual_profit_GBP"] = frame.loc[zero, "no_battery_annual_profit_GBP"]
    frame["zero_battery_annual_profit_upper_GBP"] = frame.no_battery_annual_profit_GBP + frame.zero_upper_minus_feasible_GBP.clip(lower=0)
    for name in ("counts", "electrolyser_counts", "no_battery_electrolyser_counts"):
        frame[name] = frame[name].map(json.dumps)
    for (policy, _), group in frame.groupby(["policy", "gap_std_multiplier"]):
        price = group.price_std_multiplier.to_numpy()
        base = group.no_battery_annual_profit_GBP.to_numpy()
        bounds = [(base, group.zero_battery_annual_profit_upper_GBP.to_numpy()),
                  (group.chosen_portfolio_annual_profit_GBP.to_numpy(),
                   base + group.net_gain_upper_GBP_year.to_numpy())]
        if policy == "B":
            bounds.append((group.net_gain_lower_GBP_year.to_numpy(), group.net_gain_upper_GBP_year.to_numpy()))
        for lo, hi in bounds:
            # With fixed energy inputs, the best value is a maximum of
            # affine functions of price volatility.
            for a, m, b in combinations(range(len(group)), 3):
                share = (price[m] - price[a]) / (price[b] - price[a])
                assert lo[m] <= (1-share) * hi[a] + share * hi[b] + .10
    return frame


def draw(frame):
    figure, axes = plt.subplots(2, 3, figsize=(13.7, 6.7), layout="constrained", sharex=True, sharey=True)
    design = frame[frame.gap_std_multiplier.isin(GAP_GRID) & frame.price_std_multiplier.isin(PRICE_GRID)].copy()
    metrics = [
        ("net_gain_lower_GBP_year", 1e6, "Annual net gain (£2020 million)", "viridis", True),
        ("battery_MWh", 1e3, "Battery nameplate (GWh)", "cividis", True),
        ("electrolyser_MW", 1e3, "Electrolyser nameplate (GW)", "Blues", False),
    ]
    for col, (field, scale, title, colour, logarithmic) in enumerate(metrics):
        values = design[field].to_numpy() / scale
        positive = values[values > 0]
        norm = LogNorm(vmin=max(1e-5, positive.min()), vmax=positive.max()) if logarithmic else Normalize(0, values.max())
        cmap = plt.get_cmap(colour).copy()
        cmap.set_bad("#e9edf0")
        for row, policy in enumerate("AB"):
            selection = design[design.policy == policy]
            grid = selection.pivot(index="price_std_multiplier", columns="gap_std_multiplier", values=field) / scale
            data = grid.to_numpy()
            data = np.ma.masked_less_equal(data, 0) if logarithmic else data
            ax = axes[row, col]
            colour_image = ax.imshow(data, aspect="auto", origin="lower", norm=norm, cmap=cmap)
            if row == 0:
                ax.set_title(title, fontsize=11)
            ax.set_xticks(range(len(GAP_GRID)), [f"{g:g}" for g in GAP_GRID])
            ax.set_yticks(range(len(PRICE_GRID)), [f"{p:g}" for p in PRICE_GRID])
            ax.set_xticks(np.arange(-.5, len(GAP_GRID), 1), minor=True)
            ax.set_yticks(np.arange(-.5, len(PRICE_GRID), 1), minor=True)
            ax.grid(which="minor", color="white", linewidth=.45, alpha=.45)
            ax.tick_params(which="minor", length=0)
            ax.tick_params(which="major", length=0, labelsize=8)
            if col == 0:
                ax.set_ylabel(("A   Economic dispatch" if policy == "A" else "B   Supply first")
                              + "\nPrice SD multiplier")
            if row == 1:
                ax.set_xlabel("Supply–demand gap SD multiplier")
            if col <= 1:
                for case in selection.itertuples():
                    if case.net_gain_gap_GBP_year > max(10., case.net_gain_lower_GBP_year * 1e-6):
                        ax.plot(GAP_GRID.index(case.gap_std_multiplier), PRICE_GRID.index(case.price_std_multiplier),
                                "x", color="#c94637", ms=5, mew=1.1)
        cb = figure.colorbar(colour_image, ax=axes[:, col], shrink=.95, pad=.02)
        if logarithmic:
            cb.locator = LogLocator(numticks=6)
            cb.formatter = FuncFormatter(lambda x, _: f"{x:g}")
            cb.update_ticks()
        cb.ax.tick_params(labelsize=8)
    figure.savefig(ROOT / "portfolio-grid.png", dpi=190)
    plt.close(figure)


def main():
    frame = table()
    frame.to_csv(ROOT / "portfolio-grid.csv", index=False)
    draw(frame)
    wide = frame.loc[frame.net_gain_gap_GBP_year > np.maximum(10., frame.net_gain_lower_GBP_year * 1e-6)]
    print("Cases", len(frame), "certified positive", frame.decision.eq("positive").sum(),
          "certified zero", frame.decision.eq("zero_within_50p").sum(),
          "wide bounds", len(wide))
    cols = ["policy", "gap_std_multiplier", "price_std_multiplier", "battery_MWh",
            "electrolyser_MW", "net_gain_lower_GBP_year", "net_gain_upper_GBP_year"]
    print(wide[cols].to_string(index=False))


if __name__ == "__main__":
    main()
