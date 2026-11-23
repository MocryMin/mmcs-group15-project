"""Figure for the revised Tier 1 main results, drawn from the CSV files written by site_run.py.

    python site_figures.py results
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ORANGE, VIOLET, BLUE = "#eb6834", "#6250d6", "#2a78d6"
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
MAIN_RUN = 4


def main(out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "font.size": 10,
        "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.edgecolor": AXIS,
        "axes.labelcolor": INK2, "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK2, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
        "ytick.major.size": 0, "lines.linewidth": 2, "legend.frameon": False})
    size = pd.read_csv(out / "sizing.csv")
    size = size[size.min_run_days == MAIN_RUN]
    old = pd.read_csv(out / "sizing_v5_rule.csv")
    runs = pd.read_csv(out / "surplus_runs.csv")
    runs = runs[runs.min_load_pct == 20]

    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw=dict(width_ratios=[1.45, 1]))
    ax = axs[0]
    series = [("A", "A: economic dispatch", ORANGE), ("B1", "B with a minimum-load reserve", BLUE), ("B", "B: supply priority", VIOLET)]
    for rule, name, col in series:
        d = size[size.rule == rule].sort_values("mw")
        ax.plot(d.mw, d.net_m, color=col, label=name, marker="o", ms=3.5)
        if rule != "B":
            b = d.loc[d.net_m.idxmax()]
            ax.plot([b.mw], [b.net_m], "o", ms=9, color=col, mec=SURFACE, mew=2, zorder=5)
            below = rule == "A"
            ax.annotate(f"{b.mw:.0f} MW, GBP {b.net_m:.1f}m", (b.mw, b.net_m), xytext=(0, -11 if below else 9), textcoords="offset points",
                        color=INK, fontsize=9, ha="center", va="top" if below else "bottom")
    for pol, col in (("A", ORANGE), ("B", VIOLET)):
        d = old[old.rule.str.startswith(pol)].sort_values("mw")
        d = d[d.mw <= 62]
        ax.plot(d.mw, d.net_m, color=col, ls=(0, (4, 3)), lw=1.4, alpha=0.9)
        b = d.loc[d.net_m.idxmax()]
        ax.plot([b.mw], [b.net_m], "o", ms=6, mfc=SURFACE, mec=col, mew=1.5, zorder=4)
    ax.annotate("no production at any size", (15.1, -2.27), xytext=(8, -4), textcoords="offset points", color=INK2, fontsize=9, va="top")
    ax.axhline(0, color=INK2, lw=0.9)
    ax.set_xlim(0, 62); ax.set_ylim(-4, 16)
    ax.set_xlabel("Installed electrolyser capacity, MW"); ax.set_ylabel("Net gain, GBP m per year (2020 prices)")
    ax.set_title("Net gain by plant size: 20% minimum load, at least 4 days online")
    from matplotlib.lines import Line2D
    h, l = ax.get_legend_handles_labels()
    h.append(Line2D([0], [0], color=MUTED, ls=(0, (4, 3)), lw=1.4)); l.append("dashed: same policy with half-hour switching (report v5)")
    ax.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=8.5)

    ax = axs[1]
    d = runs[runs.at_least_hours.isin([0, 6, 12, 24, 48, 72, 96])]
    x = range(len(d))
    bars = ax.bar(x, d.share_of_one_module_energy_pct, color=VIOLET, width=0.62)
    for xi, v in zip(x, d.share_of_one_module_energy_pct):
        ax.text(xi, v + 1.5, f"{v:.0f}%" if v >= 10 or v == 0 else f"{v:.1f}%", ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_xticks(list(x)); ax.set_xticklabels(["any"] + [f"{int(h)} h" for h in d.at_least_hours.iloc[1:]])
    ax.set_ylim(0, 112); ax.set_ylabel("% of the surplus energy one module could take")
    ax.set_xlabel("Surplus lasting at least this long without a break")
    ax.set_title("How long surplus lasts under supply priority")
    ax.annotate("a 4-day run\nneeds 96 h", (6, 10), xytext=(6, 34), ha="center", fontsize=9, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.9))
    fig.suptitle("10 t/day buyer, hydrogen at GBP 7.80/kg, 2020-2025 at half-hour resolution", x=0.01, ha="left", fontsize=10, color=INK2)
    fig.tight_layout()
    fig.savefig(out / "fig_size_and_surplus.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("wrote fig_size_and_surplus.png")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "results"))
