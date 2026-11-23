"""Build the Tier 2B stress figure from the frozen half-hour inputs and weekly results."""

import argparse
from datetime import timedelta
from hashlib import sha256
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import StrMethodFormatter
import numpy as np
import pandas as pd


def weekly_metrics(results, halfhour):
    audit = json.loads((results / "audit.json").read_text())
    if sha256(halfhour.read_bytes()).hexdigest() != audit["input_sha256"]["inputs/halfhour.csv.gz"]:
        raise ValueError("The half-hour input is not the frozen backtest series.")
    weekly = pd.read_csv(results / "contract_windows.csv")
    weekly = weekly.query("design == 'pre_test' and window_days == 7 and days == 7").copy()
    weekly["start_date"] = pd.to_datetime(weekly["start_date"], utc=True)
    columns = ["end_date", "cap_kg", "hydrogen_kg", "operating_gain_gbp", "modules"]
    a = weekly.query("policy == 'A' and rule == 'rolling'").set_index("start_date")[columns]
    b = weekly.query("policy == 'B' and rule == 'greedy'").set_index("start_date")[columns]
    oracle = weekly.query("policy == 'B' and rule == 'perfect'").set_index("start_date")
    assert a.index.equals(b.index) and b.index.equals(oracle.index) and len(a) == 156
    assert a["cap_kg"].eq(70_000).all() and a["cap_kg"].equals(b["cap_kg"])
    assert a["end_date"].equals(b["end_date"]) and (a["hydrogen_kg"] <= a["cap_kg"] + 1e-6).all()
    assert np.allclose(b["hydrogen_kg"], oracle["hydrogen_kg"], rtol=0, atol=1e-6)
    panel = pd.read_csv(halfhour, usecols=["utc", "background_MW", "farm_flat_MW", "demand_MW", "price"])
    panel["utc"] = pd.to_datetime(panel["utc"], utc=True)
    panel = panel.set_index("utc").sort_index()
    panel["surplus_MWh"] = 0.5 * (panel.background_MW + panel.farm_flat_MW - panel.demand_MW).clip(lower=0)
    records = []
    for start, a_week in a.sort_index().iterrows():
        end = start + timedelta(days=7)
        slots = panel.loc[start:end - timedelta(minutes=30)]
        expected = pd.date_range(start, end, freq="30min", inclusive="left")
        assert slots.index.equals(expected) and slots["price"].notna().all()
        b_week = b.loc[start]
        year_fraction = sum(1 / (366 if day.is_leap_year else 365) for day in pd.date_range(start, periods=7))
        unit_cost = audit["equipment"]["annual_gbp"]
        net_a = a_week.operating_gain_gbp - a_week.modules * unit_cost * year_fraction
        net_b = b_week.operating_gain_gbp - b_week.modules * unit_cost * year_fraction
        records.append({
            "week_start_utc": start, "week_end_utc": a_week.end_date, "weekly_acceptance_cap_t": a_week.cap_kg / 1000,
            "mean_power_price_gbp2020_per_mwh": slots.price.mean(), "physical_surplus_gwh": slots.surplus_MWh.sum() / 1000,
            "a_rolling_delivery_t": a_week.hydrogen_kg / 1000, "b_greedy_delivery_t": b_week.hydrogen_kg / 1000,
            "b_perfect_foresight_delivery_t": oracle.loc[start, "hydrogen_kg"] / 1000,
            "a_rolling_net_gain_gbp2020": net_a, "b_greedy_net_gain_gbp2020": net_b,
        })
    return pd.DataFrame(records)


def plot_stress(metrics, out):
    zero = metrics.index[metrics.physical_surplus_gwh.eq(0)][0]
    peak = metrics.mean_power_price_gbp2020_per_mwh.idxmax()
    assert peak == zero - 1
    shown = metrics.iloc[zero - 3:zero + 4].copy()
    assert len(shown) == 7

    ink = "#162831"
    muted = "#4C6270"
    a_color = "#077A77"
    b_color = "#BB5F36"
    price_band = "#F8EFDC"
    surplus_band = "#E6EDF5"
    grid = "#DEE7EB"
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "axes.labelcolor": muted, "xtick.color": muted,
        "ytick.color": muted, "text.color": ink, "axes.spines.top": False,
        "axes.spines.right": False, "axes.spines.left": False, "axes.spines.bottom": False,
        "pdf.fonttype": 42,
    })
    fig = plt.figure(figsize=(11.4, 7.8), facecolor="white")
    gs = fig.add_gridspec(3, 1, height_ratios=[0.67, 2.1, 2.45], hspace=0.24,
                          left=0.13, right=0.976, top=0.779, bottom=0.139)
    market = fig.add_subplot(gs[0])
    delivery = fig.add_subplot(gs[1], sharex=market)
    net = fig.add_subplot(gs[2], sharex=market)

    fig.text(0.13, 0.96, "Hydrogen delivery under stress", fontsize=27, weight="bold", va="top")
    fig.text(0.13, 0.895, "Tier 2B site-scale replay  |  January–February 2023  |  Zero battery and zero hydrogen storage",
             fontsize=11, color=muted, va="top")
    fig.legend(handles=[Patch(color=a_color, label="A · Economic dispatch, rolling"),
                        Patch(color=b_color, label="B · Supply priority, greedy"),
                        Line2D([], [], color="#8796A2", lw=1.15, ls=(0, (5, 3)), label="70 t acceptance cap")],
               loc="upper left", bbox_to_anchor=(0.123, 0.864), ncol=3, frameon=False,
               fontsize=10, handlelength=1.8, columnspacing=1.54)

    x = np.arange(len(shown))
    for ax in (market, delivery, net):
        ax.set_xlim(-0.56, len(shown) - 0.44)
        ax.tick_params(axis="both", length=0, pad=7, labelsize=9.5)
        ax.set_axisbelow(True)
        for case, shade in ((peak, price_band), (zero, surplus_band)):
            pos = case - shown.index[0]
            ax.axvspan(pos - 0.48, pos + 0.48, color=shade, ec="none", zorder=0)

    market.set_ylim(0, 1)
    market.set_yticks([])
    market.tick_params(labelbottom=False)
    for row, y, title in (
        ("mean_power_price_gbp2020_per_mwh", 0.63, "Mean price (£/MWh)"),
        ("physical_surplus_gwh", 0.17, "Surplus (GWh)"),
    ):
        market.text(-0.65, y, title, ha="right", va="center", fontsize=9, color=muted)
        for j, value in enumerate(shown[row]):
            marked = (row.startswith("mean") and j + shown.index[0] == peak) or (
                row.startswith("physical") and j + shown.index[0] == zero
            )
            market.text(j, y, f"{value:.1f}", ha="center", va="center", fontsize=10,
                        weight="bold" if marked else "normal", color=ink if marked else muted)
    for code, label in ((peak, "Highest mean price"), (zero, "First zero surplus")):
        market.text(code - shown.index[0], 1.04, label, ha="center", va="bottom",
                    fontsize=8.15, weight="bold", clip_on=False)

    delivery.set_ylabel("Hydrogen delivered (t)", fontsize=10)
    delivery.set_ylim(0, 80)
    delivery.set_yticks([0, 20, 40, 60])
    delivery.tick_params(labelbottom=False)
    delivery.axhline(70, color="#8796A2", lw=1.15, ls=(0, (5, 3)), zorder=2)
    net.set_ylabel("Weekly net gain (£k)", fontsize=10)
    net.set_ylim(-210, 182)
    net.set_yticks([-200, -100, 0, 100])
    net.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    net.axhline(0, color="#8796A2", lw=1.0, zorder=2)
    net.set_xticks(x, shown.week_start_utc.dt.strftime("%d %b"))
    net.set_xlabel("Week starting (UTC), 2023", fontsize=10, labelpad=7)

    for ax in (delivery, net):
        ax.grid(axis="y", color=grid, linewidth=0.8, zorder=1)
    for code, name, color, offset in (
        ("a", "rolling", a_color, -0.19), ("b", "greedy", b_color, 0.19)
    ):
        values = shown[f"{code}_{name}_delivery_t"].to_numpy()
        gains = shown[f"{code}_{name}_net_gain_gbp2020"].to_numpy() / 1000
        delivery.bar(x + offset, values, color=color, width=0.35, zorder=3)
        net.bar(x + offset, gains, color=color, width=0.35, zorder=3)
        for j, (mass, gain) in enumerate(zip(values, gains)):
            delivery.annotate(f"{mass:.1f}" if mass else "0", (j + offset, mass),
                              xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8.2, color=color)
            net.annotate(f"{gain:+.0f}".replace("-", "−"), (j + offset, gain), xytext=(0, 3 if gain >= 0 else -3),
                         textcoords="offset points", ha="center", va="bottom" if gain >= 0 else "top",
                         fontsize=8.2, color=color)

    fig.text(0.13, 0.041, "Net gain is relative to each policy’s electricity-only baseline, after prorated equipment costs.",
             fontsize=9, color=muted)
    fig.text(0.13, 0.019, "Prices and net gains use 2020 pounds. Hydrogen deliveries are scored without a shortfall penalty.",
             fontsize=9, color=muted)
    fig.savefig(out / "delivery-stress-en.png", facecolor="white", dpi=200)
    fig.savefig(out / "delivery-stress-en.pdf", facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-results", type=Path, required=True)
    parser.add_argument("--halfhour", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    metrics = weekly_metrics(args.replay_results, args.halfhour)
    metrics.to_csv(args.output / "weekly_stress_metrics.csv", index=False, date_format="%Y-%m-%d",
                   float_format="%.9f")
    plot_stress(metrics, args.output)


if __name__ == "__main__":
    main()
