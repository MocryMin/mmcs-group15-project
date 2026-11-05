"""Rebuild vector figures from the verified Tier 1 v1 result records."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as PlotPath
from matplotlib.patches import Patch, PathPatch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures"
if (ROOT.parents[1] / "tier1-independent").is_dir():
    DEFAULT_RESULTS = ROOT.parents[1] / "tier1-independent/20261105-v1/results"
else:
    DEFAULT_RESULTS = ROOT.parent / (
        "group-collaboration/Tier1/workspaces/mocry/codex/tier1-independent/20261105-v1/results"
    )
INK = "#193548"
TEAL = "#27666e"

plt.rcParams.update({
    "font.family": "serif", "font.size": 10, "axes.labelcolor": INK,
    "axes.edgecolor": "#6d7e87", "axes.titlecolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42,
})


def energy_balance(results):
    daily = pd.read_csv(results / "schedules/A_joint.csv")
    surplus = (daily["g"] - daily["demand"]).clip(lower=0)
    captured = daily["capture"].sum()
    h2 = daily["h2_input"].sum()
    unused = surplus.sum() - captured
    displaced = h2 - captured
    assert (surplus > 0).sum() == 29
    assert abs(unused - daily["unused"].sum()) < 1e-8
    assert abs(displaced - (daily["reference_sale"] - daily["direct"]).sum()) < 1e-8
    fig, ax = plt.subplots(figsize=(6.75, .67))
    y = [1, 0]
    ax.barh(y, [captured] * 2, height=.58, color=TEAL)
    ax.barh(y, [unused, displaced], left=captured, height=.58, color=["#e3e9eb", "#b2d8d5"])
    ax.text(captured + unused * .5, 1, f"{unused:.2f} GWh still unused", ha="center", va="center", fontsize=9)
    ax.text(h2 + 8, 0, f"{displaced:.2f} GWh diverted from sale", va="center", fontsize=9)
    ax.set(xlim=(0, 560), ylim=(-.45, 1.45))
    ax.set_yticks(y, ["Physical surplus", "Electrolyser input"])
    ax.tick_params(axis="y", length=0, pad=5, labelsize=9)
    ax.set_xticks([])
    ax.spines[["left", "bottom"]].set_visible(False)
    fig.subplots_adjust(left=.18, right=.99, bottom=.04, top=.96)
    fig.savefig(OUT / "energy-balance.pdf", bbox_inches="tight", pad_inches=.025)
    plt.close(fig)


def contract(results):
    grid = pd.read_csv(results / "contract_grid.csv")
    shades = ["#e9eef0", "#b2d8d5", "#6fa8a5", "#3c797c", "#193f54"]
    assert sorted(grid.modules.unique()) == list(range(len(shades)))
    crossings = json.loads((results / "study.json").read_text(encoding="utf-8"))["summary"]["hydrogen_crossings"]
    fig, axes = plt.subplots(1, 2, figsize=(6.75, 2.86), sharey=True)
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
        ax.scatter(10, crossings[f"{policy}_2023"], marker="o", s=37, facecolor="none",
                   edgecolor=INK, linewidth=1.15)
        ax.set(xlim=(0, 30), ylim=(0, 16), xlabel="Daily offtake limit (t/day)", title=title)
        ax.set_yticks([0, 4, 8, 12, 16])
    axes[0].set_ylabel("Netback (2020 £/kg)")
    fig.legend(handles=[Patch(color=c, label=f"{20 * k} MW") for k, c in enumerate(shades)],
               ncol=len(shades), loc="lower center", frameon=False, fontsize=8)
    fig.subplots_adjust(left=.11, right=.99, bottom=.27, top=.90, wspace=.13)
    fig.savefig(OUT / "contract-trigger.pdf", bbox_inches="tight", pad_inches=.025)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    energy_balance(args.results)
    contract(args.results)
