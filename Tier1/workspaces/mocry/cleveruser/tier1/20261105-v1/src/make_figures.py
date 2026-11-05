"""Build the report figures from results.json and the daily input table."""
import csv, io, json, math, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PKG = pathlib.Path(__file__).resolve().parents[1]
FIG = PKG / "figures"
FIG.mkdir(exist_ok=True)
R = json.loads((PKG / "results/results.json").read_text(encoding="utf-8"))

# daily inputs
rows = []
with io.open(PKG / "data/daily_model_inputs.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        rows.append({k: (float(v) if k not in ("date",) else v) for k, v in r.items()})
y23 = [r for r in rows if r["date"].startswith("2023")]

plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
                     "figure.dpi": 150, "savefig.dpi": 150, "axes.grid": True,
                     "grid.alpha": 0.3, "axes.spines.top": False, "axes.spines.right": False})

# 1 current position
fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
x = np.arange(len(y23))
ax[0].plot(x, [r["G_GWh"] for r in y23], lw=0.7, color="#1f77b4", label="generation (incl. farm)")
ax[0].plot(x, [r["D_GWh"] for r in y23], lw=0.7, color="#d62728", label="demand")
ax[0].set_title("2023 daily energy: generation vs demand")
ax[0].set_xlabel("day of year")
ax[0].set_ylabel("GWh/day")
ax[0].legend(frameon=False, fontsize=8)
surplus = sorted((max(0.0, r["G_GWh"] - r["D_GWh"]) for r in y23), reverse=True)
surplus = [s for s in surplus if s > 0]
ax[1].plot(np.arange(1, len(surplus) + 1), surplus, marker="o", ms=2, lw=1, color="#2ca02c")
ax[1].axhline(0.48, color="k", ls="--", lw=0.8)
ax[1].annotate("one 20 MW module: 0.48 GWh/day", xy=(len(surplus) * 0.45, 0.48),
               xytext=(len(surplus) * 0.35, 6), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
ax[1].set_title("Surplus exceedance: 29 days, 549.9 GWh")
ax[1].set_xlabel("surplus days (ranked)")
ax[1].set_ylabel("GWh/day")
fig.tight_layout()
fig.savefig(FIG / "fig1_current_position.png")
plt.close(fig)

# 2 energy attribution
attr = R["attribution"]["cases"]["A_h2"]
fig, ax = plt.subplots(figsize=(6.2, 3.0))
parts = [attr["captured_unused_GWh"], attr["diverted_from_sale_GWh"]]
bottom = 0
colors = ["#2ca02c", "#ff7f0e"]
labels = [f"captured unused\n{parts[0]:.1f} GWh ({parts[0]/sum(parts)*100:.1f}%)",
          f"diverted from sale\n{parts[1]:.1f} GWh ({parts[1]/sum(parts)*100:.1f}%)"]
for v, c, lab in zip(parts, colors, labels):
    ax.bar(["20 MW electrolyser input"], [v], bottom=bottom, color=c, label=lab, width=0.5)
    if v > 20:
        ax.text(0, bottom + v / 2, lab, ha="center", va="center", fontsize=8, color="white")
    bottom += v
ax.annotate(labels[0], xy=(0.27, parts[0] / 2), xytext=(0.42, 40), fontsize=8,
            arrowprops=dict(arrowstyle="->", lw=0.7))
ax.set_ylabel("GWh/year")
ax.set_title("Where the electrolyser's 171.8 GWh comes from (2023)")
ax.set_ylim(0, 200)
ax.legend(frameon=False, fontsize=8, loc="upper right")
fig.tight_layout()
fig.savefig(FIG / "fig2_energy_attribution.png")
plt.close(fig)

# 3 scenario comparison
cases = {c["case"]: c for c in R["cases"]}
labels = ["no\ninvestment", "battery\nonly", "H2 only", "both", "rule-based\n20 MW"]
A = [cases["A_0"]["increment_mGBP"], cases["A_battery"]["increment_mGBP"], cases["A_h2"]["increment_mGBP"],
     cases["A_both"]["increment_mGBP"], cases["A_simple20"]["increment_mGBP"]]
B = [cases["B_0"]["increment_mGBP"], cases["B_battery"]["increment_mGBP"], cases["B_h2"]["increment_mGBP"],
     cases["B_both"]["increment_mGBP"], cases["B_simple20"]["increment_mGBP"]]
fig, ax = plt.subplots(figsize=(7.2, 3.2))
w = 0.38
xx = np.arange(len(labels))
ax.bar(xx - w / 2, A, w, label="A: economic allocation", color="#1f77b4")
ax.bar(xx + w / 2, B, w, label="B: current generation first", color="#ff7f0e")
for i, (a, b) in enumerate(zip(A, B)):
    ax.text(i - w / 2, a + (0.15 if a >= 0 else -0.45), f"{a:+.2f}", ha="center", fontsize=7)
    ax.text(i + w / 2, b + (0.15 if b >= 0 else -0.45), f"{b:+.2f}", ha="center", fontsize=7)
ax.axhline(0, color="k", lw=0.6)
ax.set_xticks(xx)
ax.set_xticklabels(labels)
ax.set_ylabel("annual increment, £m GBP2020")
ax.set_title("2023 design year: incremental value by configuration")
ax.legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "fig3_scenarios.png")
plt.close(fig)

# 4 offtake ladder
grid = R["trigger_grid"]
Ls = sorted({g["offtake_kg_day"] for g in grid})
mw = [next(g["MW"] for g in grid if g["netback_GBP2020_kg"] == 7.799 and g["offtake_kg_day"] == L) for L in Ls]
inc = [next(g["increment_mGBP"] for g in grid if g["netback_GBP2020_kg"] == 7.799 and g["offtake_kg_day"] == L) for L in Ls]
fig, ax = plt.subplots(figsize=(7.0, 3.2))
ax.bar([str(int(L / 1000)) for L in Ls], mw, color="#9467bd", width=0.6, label="capacity (left)")
ax.set_xlabel("hydrogen offtake cap, t/day")
ax.set_ylabel("electrolyser capacity, MW")
ax2 = ax.twinx()
ax2.plot([str(int(L / 1000)) for L in Ls], inc, color="#2ca02c", marker="o", lw=1.2, label="annual increment (right)")
ax2.set_ylabel("increment, £m/year")
ax2.spines["right"].set_visible(True)
ax.set_title("Capacity is set by the hydrogen buyer, not by the electricity surplus (7.80 £/kg)")
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="upper left")
fig.tight_layout()
fig.savefig(FIG / "fig4_offtake_ladder.png")
plt.close(fig)

# 5 trigger heatmap
vs = sorted({g["netback_GBP2020_kg"] for g in grid})
M = np.array([[next(g["MW"] for g in grid if g["netback_GBP2020_kg"] == v and g["offtake_kg_day"] == L) for L in Ls]
              for v in vs])
fig, ax = plt.subplots(figsize=(7.4, 3.6))
im = ax.imshow(M, aspect="auto", cmap="viridis", origin="lower")
ax.set_xticks(range(len(Ls)))
ax.set_xticklabels([str(int(L / 1000)) for L in Ls])
ax.set_yticks(range(len(vs)))
ax.set_yticklabels([f"{v:g}" for v in vs])
ax.set_xlabel("hydrogen offtake cap, t/day")
ax.set_ylabel("hydrogen netback, £/kg GBP2020")
ax.set_title("Optimal electrolyser capacity (MW), 2023 design year, policy A")
for i in range(len(vs)):
    for j in range(len(Ls)):
        ax.text(j, i, f"{int(M[i, j])}", ha="center", va="center",
                color="white" if M[i, j] < 60 else "black", fontsize=7)
ax.grid(False)
cb = fig.colorbar(im, ax=ax, shrink=0.85)
cb.set_label("MW")
fig.tight_layout()
fig.savefig(FIG / "fig5_trigger_map.png")
plt.close(fig)

# 6 battery value vs capex
tab = [r for r in R["battery_sweep"] if r["fom"] == "table" and r["policy"] == "A"]
fig, ax = plt.subplots(figsize=(6.4, 3.1))
ax.plot([r["cost_GBP2020_MWh"] / 1000 for r in tab], [r["n_units"] for r in tab], marker="o", lw=1.2,
        color="#1f77b4", label="units chosen (table FOM)")
ax.set_xlabel("battery CAPEX, £k/MWh")
ax.set_ylabel("1.5 MW / 3 MWh units chosen")
ax.axvline(256.2, color="#d62728", ls="--", lw=1)
ax.text(250, max(r["n_units"] for r in tab) * 0.55, "brief: €288k/MWh\n(£256k/MWh)", ha="right", fontsize=8, color="#d62728")
ax.axvline(6.99, color="k", ls=":", lw=1)
ax.text(9, max(r["n_units"] for r in tab) * 0.9, "break-even\n£7.0k/MWh", fontsize=8)
ax.set_title("Battery: no unit is economic at any non-negative capex with the primary FOM")
ax.legend(frameon=False, fontsize=8, loc="center right")
fig.tight_layout()
fig.savefig(FIG / "fig6_battery_value.png")
plt.close(fig)

# 7 robustness
rob = {c["case"]: c for c in R["robustness"]}
years = list(range(2020, 2027))
A = [rob[f"A_fixed20_{y}"]["increment_mGBP"] for y in years]
B = [rob[f"B_fixed20_{y}"]["increment_mGBP"] for y in years]
fig, ax = plt.subplots(1, 2, figsize=(9, 3.2), gridspec_kw={"width_ratios": [1.1, 1.0]})
xx = np.arange(len(years))
ax[0].bar(xx - 0.2, A, 0.4, label="A", color="#1f77b4")
ax[0].bar(xx + 0.2, B, 0.4, label="B", color="#ff7f0e")
ax[0].axhline(0, color="k", lw=0.6)
ax[0].set_xticks(xx)
ax[0].set_xticklabels([str(y) for y in years])
ax[0].set_ylabel("increment, £m/year")
ax[0].set_title("Fixed 20 MW replayed on each year")
ax[0].legend(frameon=False, fontsize=8)
sens = {c["case"]: c for c in R["sensitivity"]}
items = [("CAPEX legacy", sens["sens_H2cost_legacy_816"]["increment_mGBP"]),
         ("CAPEX modern high", sens["sens_H2cost_modern_high_1651"]["increment_mGBP"]),
         ("rate 0%", sens["sens_rate_0"]["increment_mGBP"]),
         ("rate 12%", sens["sens_rate_0.12"]["increment_mGBP"]),
         ("strict sample", sens["data_strict_2023"]["increment_mGBP"]),
         ("no farm", sens["boundary_no_farm_2023"]["increment_mGBP"]),
         ("old price", sens["data_old_price_2023"]["increment_mGBP"])]
base = cases["A_h2"]["increment_mGBP"]
ax[1].barh([k for k, _ in items], [v - base for _, v in items], color="#8c564b")
ax[1].axvline(0, color="k", lw=0.6)
ax[1].set_xlabel("change vs reference, £m/year")
ax[1].set_title("Single-factor sensitivity (reference +8.57)")
ax[1].invert_yaxis()
fig.tight_layout()
fig.savefig(FIG / "fig7_robustness.png")
plt.close(fig)

# 8 cash-flow bridge
ref = cases["A_h2"]
steps = [("hydrogen\nrevenue", ref["hydrogen_revenue_mGBP"]),
         ("electricity\nrevenue change", -(cases["A_0"]["electricity_revenue_mGBP"] - ref["electricity_revenue_mGBP"])),
         ("FOM", -ref["fom_annual_mGBP"]),
         ("stack\nreplacement", -ref["stack_annual_mGBP"]),
         ("capital\ncharge", -ref["capital_annual_mGBP"])]
fig, ax = plt.subplots(figsize=(7.0, 3.2))
cum = 0
for i, (lab, val) in enumerate(steps):
    ax.bar(i, val, bottom=cum, color="#2ca02c" if val >= 0 else "#d62728", width=0.6)
    ax.text(i, cum + val + (0.4 if val >= 0 else -0.4), f"{val:+.2f}", ha="center", fontsize=7)
    cum += val
ax.bar(len(steps), cum, color="#1f77b4", width=0.6)
ax.text(len(steps), cum + 0.4, f"{cum:+.2f}", ha="center", fontsize=8, weight="bold")
ax.set_xticks(range(len(steps) + 1))
ax.set_xticklabels([s[0] for s in steps] + ["net annual\nincrement"])
ax.axhline(0, color="k", lw=0.6)
ax.set_ylabel("£m/year (GBP2020)")
ax.set_title("Value bridge for the 20 MW electrolyser, 2023")
fig.tight_layout()
fig.savefig(FIG / "fig8_bridge.png")
plt.close(fig)

print("figures written:", sorted(p.name for p in FIG.glob("*.png")))
