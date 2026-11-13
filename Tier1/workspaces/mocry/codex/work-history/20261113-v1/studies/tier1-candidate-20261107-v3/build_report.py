"""Generate the report's numbers, tables and vector charts from the result archive."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as PlotPath
from matplotlib.patches import PathPatch, Patch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "report"
GENERATED = REPORT / "generated"
FIGURES = REPORT / "figures"


def number(value, digits=2):
    if abs(value) < .5 * 10 ** (-digits):
        value = 0.
    if value < 0:
        return r"\negval{" + f"{-value:.{digits}f}" + "}"
    return f"{value:.{digits}f}"


def table(filename, caption, label, headers, widths, rows):
    lines = [
        r"\begin{table}[H]", r"\centering\small",
        r"\caption{" + caption + "}", r"\label{" + label + "}",
        r"\begin{tabularx}{\linewidth}{@{}" + widths + "@{}}", r"\toprule",
        " & ".join(headers) + r" \\", r"\midrule",
    ]
    lines.extend(" & ".join(row) + r" \\" for row in rows)
    lines.extend([r"\bottomrule", r"\end{tabularx}", r"\end{table}"])
    (GENERATED / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def figures(years, result_dir, crossings):
    plt.rcParams.update({
        "font.family": "serif", "font.size": 9.5, "text.color": "#193548",
        "axes.labelcolor": "#193548", "axes.edgecolor": "#718490",
        "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42, "axes.titleweight": "regular",
    })
    fig, ax = plt.subplots(figsize=(6.4, 1.6))
    complete = years[years.full_year]
    shades = ["#a5c6ca" if y != 2023 else "#176976" for y in complete.year]
    ax.bar(complete.year, complete.surplus_GWh / 1000, color=shades, width=.64)
    for row in complete.itertuples():
        ax.text(row.year, row.surplus_GWh / 1000 + .08, f"{row.surplus_days} days",
                ha="center", fontsize=8.2)
    ax.set(xlabel="Complete calendar year", ylabel="Surplus (TWh)", ylim=(0, 5.3))
    ax.set_xticks(complete.year)
    ax.set_yticks([0, 2, 4])
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="both", length=0)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#e3e9ec", lw=.6)
    fig.subplots_adjust(left=.10, right=.99, bottom=.29, top=.98)
    fig.savefig(FIGURES / "annual_surplus.pdf", bbox_inches="tight", pad_inches=.025)
    plt.close(fig)

    grid = pd.read_csv(result_dir / "contract_grid.csv")
    palette = ["#e9eef0", "#b2d8d5", "#6fa8a5", "#3c797c", "#193f54"]
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.35), sharey=True)
    for ax, policy, title in zip(axes, "AB", ["A. Economic allocation", "B. Daily sales priority"]):
        data = grid[grid.policy == policy].pivot(index="price", columns="offtake_t_day", values="modules")
        for count, color in enumerate(palette):
            rows, cols = (data == count).to_numpy().nonzero()
            if not len(rows):
                continue
            cells = []
            for row, col in zip(rows, cols):
                x, y = data.columns[col], data.index[row]
                cells.append([(x - .25, y - .125), (x + .25, y - .125),
                              (x + .25, y + .125), (x - .25, y + .125)])
            path = PlotPath.make_compound_path_from_polys(np.asarray(cells))
            ax.add_patch(PathPatch(path, facecolor=color, edgecolor="none"))
        ax.scatter(10, 7.7990270551508845, marker="D", s=27,
                   facecolor="#e7b969", edgecolor="#193548", linewidth=.8)
        ax.scatter(10, crossings[f"{policy}_2023"], marker="o", s=31,
                   facecolor="none", edgecolor="#193548", linewidth=1.0)
        ax.set(xlim=(0, 30), ylim=(0, 16), xlabel="Offtake cap (t/day)", title=title)
        ax.set_yticks([0, 4, 8, 12, 16])
    axes[0].set_ylabel("Netback (2020 £/kg)")
    fig.legend(handles=[Patch(color=color, label=f"{20*k} MW") for k, color in enumerate(palette)],
               ncol=5, loc="lower center", frameon=False, fontsize=8)
    fig.subplots_adjust(left=.105, right=.99, bottom=.29, top=.90, wspace=.13)
    fig.savefig(FIGURES / "contract_trigger.pdf", bbox_inches="tight", pad_inches=.025)
    plt.close(fig)


def run():
    GENERATED.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    result_dir = ROOT / "results"
    primary = json.loads((result_dir / "study.json").read_text(encoding="utf-8"))
    extension = json.loads((result_dir / "extension.json").read_text(encoding="utf-8"))
    cases, summary = primary["cases"], primary["summary"]
    extra = extension["cases"]
    a = cases["A_joint"]
    cash = summary["cashflow_20MW"]["A_2023"]
    yearly = pd.read_csv(result_dir / "annual_replay.csv")
    whole = yearly[yearly.full_year]
    solved = sum(row.get("solver") == "Xpress" for row in [*cases.values(), *extra.values()])
    values = {
        "Capital": f'{a["capex"]:.1f}',
        "MeanA": f'{whole.A_gain.mean():.2f}',
        "MeanB": f'{whole.B_gain.mean():.2f}',
        "Netback": f'{a["price_H2"]:.2f}',
        "RefGain": f'{a["net"]:.2f}',
        "Capture": f'{a["capture_GWh"]:.2f}',
        "Hinput": f'{a["h2_GWh"]:.1f}',
        "Displaced": f'{a["displacement_GWh"]:.1f}',
        "Surplus": f'{summary["surplus_GWh"]:.1f}',
        "Unused": f'{a["unused_GWh"]:.1f}',
        "CaptureShare": f'{100*a["capture_GWh"]/a["h2_GWh"]:.1f}',
        "SurplusShare": f'{100*a["capture_GWh"]/summary["surplus_GWh"]:.2f}',
        "PhysicalCap": f'{extension["physical_cap_GWh"]:.2f}',
        "BreakA": f'{summary["hydrogen_crossings"]["A_2023"]:.2f}',
        "BreakB": f'{summary["hydrogen_crossings"]["B_2023"]:.2f}',
        "OfftakeBreak": f'{extension["offtake_break_even_kg_day"]/1000:.2f}',
        "FortyGain": f'{extra["A_fixed40_2023"]["net"]:.2f}',
        "ExpansionGain": f'{extra["A_offtake50_2023"]["net"]:.2f}',
        "ExpansionCapital": f'{extra["A_offtake50_2023"]["capex"]:.1f}',
        "SimpleLoss": f'{abs(cases["A_simple20_2023"]["net"]):.2f}',
        "RuleAdvantage": f'{a["net"]-cases["A_simple20_2023"]["net"]:.2f}',
        "CostStress": f'{cases["A_fixed20_cost_stress"]["net"]:.2f}',
        "BatteryBound": f'{extension["battery_bounds"]["A"]["free_charge_revenue_ceiling"]*1000:.1f}',
        "BatteryCost": f'{summary["battery_bounds"]["A_2023"]["annual_cost"]*1000:.1f}',
        "PoolValue": f'{1000*(cases["A_battery1_pool"]["direct_change"]+cases["A_battery1_pool"]["discharge_value"]):.1f}',
        "StockValue": f'{1000*(cases["A_battery1_stock"]["direct_change"]+cases["A_battery1_stock"]["discharge_value"]):.1f}',
        "CheckCount": str(solved),
        "Payback": f'{cash["simple_payback"]:.2f}',
        "DiscountedPayback": f'{cash["discounted_payback"]:.2f}',
        "NPV": f'{cash["npv"]:.1f}',
    }
    macros = [r"\newcommand{" + chr(92) + key + "}{" + value + "}" for key, value in values.items()]
    (GENERATED / "numbers.tex").write_text("\n".join(macros) + "\n", encoding="utf-8")
    (result_dir / "report_values.json").write_text(json.dumps(values, indent=2) + "\n", encoding="utf-8")

    rows = []
    for title, label in [("No investment", "zero"), ("Battery only", "battery"),
                         ("Hydrogen only", "hydrogen"), ("Joint choice", "joint"),
                         ("Fixed 20 MW", "fixed20_2023")]:
        row = [title]
        for policy in "AB":
            item = cases[f"{policy}_{label}"]
            row.extend([f'{item["battery_MW"]:g} / {item["h2_MW"]:g}', number(item["net"])])
        rows.append(row)
    table("portfolios.tex", "2023 capacity (battery / electrolyser MW) and gain "
          r"(\gbp m/year) under the same-policy comparator.", "tab:portfolios",
          ["Scenario", "A capacity", "A gain", "B capacity", "B gain"], "Y r r r r", rows)

    floor_rows = []
    for label, item in [("A without floor", a), ("Restore half the sales loss", cases["A_service_50"]),
                        (r"Retain 99.99\% of sales", extra["A_floor_0.9999"]),
                        ("Retain all sales", extra["A_floor_1.0000"])]:
        floor_rows.append([label, number(item["displacement_GWh"], 1),
                           f'{item["h2_MW"]:g}', number(item["net"])])
    table("sales_floors.tex", "Realised sales lost and investment under annual floors, 2023 A.",
          "tab:floors", ["Annual rule", "Lost sales (GWh)", "H$_2$ (MW)", r"Gain (\gbp m/year)"],
          "Y r r r", floor_rows)

    annual_rows = [[str(int(row.year)), number(row.surplus_GWh, 0),
                    number(row.A_gain), number(row.B_gain)] for row in whole.itertuples()]
    annual_rows.append(["2020--25 mean", number(whole.surplus_GWh.mean(), 0),
                        number(whole.A_gain.mean()), number(whole.B_gain.mean())])
    table("annual_replay.tex", "Fixed 20 MW on all complete years. Gains are "
          r"\gbp m/year under each policy; dispatch uses realised daily inputs.", "tab:years",
          ["Year", "Surplus (GWh)", "A gain", "B gain"], "Y r r r", annual_rows)

    bridge = [
        ["Hydrogen netback receipts", number(a["hydrogen_value"])],
        ["Forgone electricity receipts", number(a["direct_change"])],
        ["Fixed operating cost", number(-summary["hydrogen_fixed_opex"])],
        ["Capital and stack equivalent annual cost", number(-(a["annual_cost"]-summary["hydrogen_fixed_opex"]))],
        ["Equivalent annual gain", number(a["net"])],
    ]
    table("cash_bridge.tex", "2023 A cash and annual-value bridge for one module.",
          "tab:cash", ["Component", r"\gbp m/year"], "Y r", bridge)
    figures(yearly, result_dir, summary["hydrogen_crossings"])
    print("Generated report numbers, tables and vector figures.", flush=True)


if __name__ == "__main__":
    run()
