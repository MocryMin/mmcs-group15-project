"""Redraw the energy-attribution panel for the report.

The package figure (tier1/20261105-v1/figures/fig2_energy_attribution.png)
labels the same two numbers three times (in-bar text, legend-style text and a
leader-line callout), which is unreadable at page size. This script draws the
same data once, with one label per segment.

Numbers are the package values for 2023, case A_h2:
    electrolyser input            171.84 GWh
    captured unused                13.92 GWh   (8.1 %)
    diverted from sale            157.92 GWh   (91.9 %)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

truncated, diverted = 13.92, 157.92
total = truncated + diverted

fig, ax = plt.subplots(figsize=(6.2, 3.0), dpi=200)

ax.barh([0], [diverted], height=0.42, color="#E8A33D", edgecolor="#B8752A",
        linewidth=0.6, label="diverted from sale")
ax.barh([0], [truncated], left=[diverted], height=0.42, color="#4C8C4A",
        edgecolor="#2F5E2E", linewidth=0.6, label="captured unused")

ax.text(diverted / 2, 0, "diverted from sale\n157.9 GWh  (91.9 %)",
        ha="center", va="center", fontsize=9, color="white", weight="bold")
ax.annotate("captured unused\n13.9 GWh  (8.1 %)",
            xy=(diverted + truncated / 2, 0.24), xytext=(118, 0.62),
            fontsize=9, color="#2F5E2E", weight="bold", ha="left", va="center",
            arrowprops=dict(arrowstyle="-", color="#2F5E2E", linewidth=0.8,
                            shrinkA=2, shrinkB=2))

ax.set_xlim(0, total * 1.02)
ax.set_ylim(-0.55, 0.95)
ax.set_yticks([])
ax.set_xlabel("electrolyser input, GWh/year (2023)", fontsize=9)
ax.tick_params(axis="x", labelsize=8)
ax.set_title("171.8 GWh of input: 8 % avoided waste, 92 % diverted sale",
             fontsize=9.5, loc="left", pad=8)
for spine in ("top", "right", "left"):
    ax.spines[spine].set_visible(False)
ax.grid(axis="x", color="#DDDDDD", linewidth=0.6)
ax.set_axisbelow(True)

fig.tight_layout()
fig.savefig("figures/fig2_attribution_redrawn.png", bbox_inches="tight",
            facecolor="white")
print("wrote figures/fig2_attribution_redrawn.png")
