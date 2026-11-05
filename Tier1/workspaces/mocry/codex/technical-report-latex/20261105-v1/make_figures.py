"""Rebuild vector figures from the verified Tier 1 v1 result records."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as PlotPath
from matplotlib.patches import Patch, PathPatch
from matplotlib.ticker import FixedLocator, StrMethodFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures"
DEFAULT_RESULTS = ROOT.parents[1] / "tier1-independent/20261105-v1/results"
INK = "#193548"
TEAL = "#27666e"
ACCENT = "#954c37"

plt.rcParams.update({
    "font.family": "serif", "font.size": 10, "axes.labelcolor": INK,
    "axes.edgecolor": "#6d7e87", "axes.titlecolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42,
})


def surplus(results):
    daily = pd.read_csv(results / "schedules/A_joint.csv")
    values = (daily["g"] - daily["demand"]).sort_values(ascending=False)
    values = values[values > 0]
    assert len(values) == 29 and abs(values.sum() - 549.9443) < .001
    fig, ax = plt.subplots(figsize=(6.35, 1.65))
    ax.plot(range(1, len(values) + 1), values, color=TEAL, lw=1.8,
            marker="o", markersize=2.2, label="Physical surplus")
    ax.axhline(.48, color=ACCENT, lw=1.1, ls="--", label="One 20 MW module")
    ax.set(yscale="log", xlim=(.6, 29.4), ylim=(.35, 110),
           xlabel="Rank of positive-surplus day", ylabel="Surplus (GWh/day)")
    ax.set_xticks([1, 5, 10, 15, 20, 25, 29])
    ax.yaxis.set_major_locator(FixedLocator([.5, 1, 5, 10, 50, 100]))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:g}"))
    ax.minorticks_off()
    ax.grid(axis="y", color="#e0e6e8", linewidth=.65)
    ax.legend(loc="upper right", frameon=False, fontsize=8, ncol=2)
    fig.savefig(OUT / "surplus-duration.pdf", bbox_inches="tight", pad_inches=.025)
    plt.close(fig)


def contract(results):
    grid = pd.read_csv(results / "contract_grid.csv")
    shades = ["#e9eef0", "#b2d8d5", "#6fa8a5", "#3c797c", "#193f54"]
    assert sorted(grid.modules.unique()) == list(range(len(shades)))
    fig, axes = plt.subplots(1, 2, figsize=(6.75, 2.33), sharey=True)
    for ax, policy, title in zip(axes, "AB", ("A. Economic dispatch", "B. Daily electricity priority")):
        data = grid[grid.policy == policy].pivot(index="price", columns="offtake_t_day", values="modules")
        # Draw each capacity as one vector path to avoid seams between grid cells.
        for count, shade in enumerate(shades):
            rows, columns = (data == count).to_numpy().nonzero()
            if not len(rows):
                continue
            cells = []
            for row, col in zip(rows, columns):
                x, y = data.columns[col], data.index[row]
                cells.append([(x - .25, y - .125), (x + .25, y - .125),
                              (x + .25, y + .125), (x - .25, y + .125)])
            path = PlotPath.make_compound_path_from_polys(np.asarray(cells))
            ax.add_patch(PathPatch(path, facecolor=shade, edgecolor="none"))
        ax.scatter(10, 7.799, marker="D", s=34, facecolor="#e7b969", edgecolor=INK, linewidth=.8)
        ax.set(xlim=(0, 30), ylim=(0, 16), xlabel="Daily offtake limit (t/day)", title=title)
        ax.set_yticks([0, 4, 8, 12, 16])
    axes[0].set_ylabel("Netback (2020 £/kg)")
    fig.legend(handles=[Patch(color=c, label=f"{20 * k} MW") for k, c in enumerate(shades)],
               ncol=len(shades), loc="lower center", frameon=False, fontsize=8)
    fig.subplots_adjust(left=.11, right=.99, bottom=.31, top=.89, wspace=.13)
    fig.savefig(OUT / "contract-trigger.pdf", bbox_inches="tight", pad_inches=.025)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    surplus(args.results)
    contract(args.results)
