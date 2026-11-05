"""Redraw the energy-attribution panel at final printed size.

The package figure (tier1/20261105-v1/figures/fig2_energy_attribution.png) labels the same two
numbers three times and is drawn at 15.7 cm, so at the 7.5 cm printed width its 9 pt labels
become 4 pt. This version is drawn at 7.5 cm with 6.5 pt text and one label per segment.

A single stacked strip leaves most of the frame empty, so the two components are drawn as two
bars on a shared axis: the frame then fills like the neighbouring panel and the comparison
(large diverted flow, small avoided-waste flow) stays visible.

Package values for 2023, case A_h2:
    electrolyser input   171.84 GWh
    captured unused       13.92 GWh   (8.1 %)
    diverted from sale   157.92 GWh   (91.9 %)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

truncated, diverted = 13.92, 157.92
total = truncated + diverted

ACCENT = "#17456B"
MUTED = "#5C6672"
WARM = "#B8752A"
GREEN = "#4C8C4A"

fig, ax = plt.subplots(figsize=(2.95, 1.70))

ax.barh([1], [diverted], height=0.55, color=WARM, edgecolor="#8C5620", linewidth=0.5)
ax.barh([0], [truncated], height=0.55, color=GREEN, edgecolor="#2F5E2E", linewidth=0.5)

ax.set_yticks([1, 0])
ax.set_yticklabels(["diverted from sale", "captured unused"], fontsize=6.2, color=MUTED)
ax.set_xlim(0, total * 1.02)
ax.set_ylim(-0.6, 1.6)
ax.set_xlabel("electrolyser input, GWh (2023)", fontsize=6.6, color=MUTED, labelpad=2)
ax.tick_params(axis="x", labelsize=6.2, colors=MUTED, length=2, pad=1)
ax.tick_params(axis="y", length=0, pad=2)

ax.text(diverted / 2, 1, "157.9 GWh  (91.9 %)", ha="center", va="center",
        fontsize=6.6, color="white", weight="bold")
ax.text(truncated + 4, 0, "13.9  (8.1 %)", ha="left", va="center",
        fontsize=6.6, color="#2F5E2E", weight="bold")

for spine in ("top", "right", "left", "bottom"):
    ax.spines[spine].set_color("#C3CDD8")
    ax.spines[spine].set_linewidth(0.5)
ax.grid(axis="x", color="#E4E9EE", linewidth=0.5, zorder=0)
ax.set_axisbelow(True)

fig.tight_layout(pad=0.15)
fig.savefig("figures/fig2_attribution_redrawn.png", dpi=600, facecolor="white")
print("wrote figures/fig2_attribution_redrawn.png")
