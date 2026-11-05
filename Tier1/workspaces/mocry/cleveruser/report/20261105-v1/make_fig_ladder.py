"""Redraw the offtake-capacity ladder at final printed size.

The package figure (tier1/20261105-v1/figures/fig4_offtake_ladder.png) is drawn at 1050 px
with a title inside the plot and small ticks; at the 7.5 cm printed width its labels fall
below 5 pt. This version uses the same numbers, drawn at 7.5 cm with 6.5-7 pt text, and
moves the claim into the caption.

Data: tier1/20261105-v1/results/results.json, trigger_grid rows at netback 7.799 £/kg,
2023, policy A.  offtake (kg/day) -> modules -> annual increment
    0, 1 000, 2 000 -> 0 MW         0.00 £m
    5 000 -> 20 MW   3.735 £m
   10 000 -> 20 MW   8.572 £m
   15 000 -> 40 MW  14.201 £m
   20 000 -> 60 MW  17.897 £m
   30 000 -> 80 MW  28.296 £m
   50 000 -> 120 MW 49.093 £m
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

tpd = np.array([0, 1, 2, 5, 10, 15, 20, 30, 50], dtype=float)
mw = np.array([0, 0, 0, 20, 20, 40, 60, 80, 120], dtype=float)
inc = np.array([0.0, 0.0, 0.0, 3.735, 8.572, 14.201, 17.897, 28.296, 49.093])

ACCENT = "#17456B"
BAR = "#9FB8CC"
WARM = "#B8752A"
MUTED = "#5C6672"

fig, ax = plt.subplots(figsize=(2.95, 1.70))

x = np.arange(len(tpd))
ax.bar(x, mw, width=0.62, color=BAR, edgecolor=ACCENT, linewidth=0.5, zorder=2)
ax.set_ylim(0, 135)
ax.set_xticks(x)
ax.set_xticklabels([f"{int(v)}" if v else "0" for v in tpd], fontsize=6.2)
ax.set_xlabel("hydrogen offtake cap, t/day", fontsize=6.6, color=MUTED, labelpad=2)
ax.set_ylabel("capacity, MW", fontsize=6.6, color=MUTED, labelpad=2)
ax.tick_params(axis="y", labelsize=6.2, colors=MUTED, length=2, pad=1)
ax.tick_params(axis="x", colors=MUTED, length=2, pad=1)
for spine in ("top", "right", "left", "bottom"):
    ax.spines[spine].set_color("#C3CDD8")
    ax.spines[spine].set_linewidth(0.5)
ax.grid(axis="y", color="#E4E9EE", linewidth=0.5, zorder=0)

ax2 = ax.twinx()
ax2.plot(x, inc, color=WARM, linewidth=1.0, marker="o", markersize=2.6, zorder=3)
ax2.set_ylim(-2, 58)
ax2.set_ylabel("annual increment, £m/yr", fontsize=6.6, color=WARM, labelpad=2)
ax2.tick_params(axis="y", labelsize=6.2, colors=WARM, length=2, pad=1)
for spine in ("top", "left"):
    ax2.spines[spine].set_visible(False)
ax2.spines["right"].set_color("#E0C4A8")

ax.annotate("49.1", xy=(x[-1], 120), xytext=(-2, 6), textcoords="offset points",
            fontsize=6.2, color=ACCENT, ha="center", va="bottom")
fig.tight_layout(pad=0.15)
fig.savefig("figures/fig4_ladder_redrawn.png", dpi=600, facecolor="white")
print("wrote figures/fig4_ladder_redrawn.png")
