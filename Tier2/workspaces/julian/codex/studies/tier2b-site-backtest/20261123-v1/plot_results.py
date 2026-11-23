"""Plot the pre-test design's held-out results from the exported summary."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot(summary, output):
    results = pd.read_csv(summary).query("design == 'pre_test'")
    methods = [
        ("pace", "Daily pacing", "#9CADB8"),
        ("greedy", "Greedy", "#306C8C"),
        ("rolling", "Rolling schedule", "#087B67"),
        ("perfect", "Perfect foresight", "#915C31"),
    ]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.spines.left": False})
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.55), sharey=True)
    fig.subplots_adjust(left=0.087, right=0.973, bottom=0.18, top=0.737, wspace=0.11)
    fig.text(0.087, 0.955, "Tier 2B | Site-scale offtake replay", fontsize=21,
             va="top", color="#142530", weight="bold")
    fig.text(0.087, 0.866, "2023–2025 half-hourly test  ·  10 t/day equivalent acceptance cap  ·  Zero storage",
             color="#425768", fontsize=10.5)
    categories = np.arange(2)
    for ax, policy, heading in zip(
        axes, ("A", "B"), ("A  Economic dispatch", "B  Supply priority")
    ):
        cases = results[results.policy == policy].set_index(["window_days", "rule"])
        count = cases.modules.iloc[0]
        ax.set_title(f"{heading}  |  {count} modules", loc="left", weight="bold", color="#142530", pad=9)
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#DBE4E9", linewidth=0.8)
        ax.spines["bottom"].set_color("#B8C7CE")
        ax.tick_params(axis="both", length=0, pad=6, labelcolor="#425768")
        ax.set_xticks(categories, ["Daily cap", "Weekly cap"])
        ax.set_yticks(np.arange(0, 17, 4))
        ax.set_xlim(-0.49, 1.49)
        ax.set_ylim(0, 16)
        width = 0.19
        for i, (method, name, color) in enumerate(methods):
            values = [cases.at[(days, method), "annual_net_gain_gbp"] / 1e6 for days in (1, 7)]
            bars = ax.bar(categories + (i - 1.5) * width, values, width * 0.87, color=color, label=name)
            ax.bar_label(bars, labels=[f"{v:.2f}" for v in values], padding=3, fontsize=8.2, color="#142530")
    axes[0].set_ylabel("Annual net gain (£m, 2020 prices)", color="#425768")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower left", bbox_to_anchor=(0.078, 0.024), ncol=4,
               frameon=False, labelcolor="#425768")
    fig.savefig(output / "site-backtest.png", dpi=200, facecolor="white")
    fig.savefig(output / "site-backtest.pdf", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    path = parser.parse_args().results
    plot(path / "summary.csv", path)
