"""Figures for the Tier 2B study, drawn from the cached CSV files in results/."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

from t1_model import Params
from t2b_model import module_energy

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
BLUE, ORANGE, AQUA, YELLOW, VIOLET, RED, GREEN = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#6250d6", "#e34948", "#008300"
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
RULE_NAME = dict(strict="Unsold energy only", topup="Unsold energy, minimum load topped up", divert="Diversion allowed")
RULE_COL = dict(strict=VIOLET, topup=BLUE, divert=ORANGE)


def style():
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
    return plt


def done(fig, name):
    fig.savefig(OUT / name, dpi=160, bbox_inches="tight")
    print("wrote", name)


def main():
    plt = style()
    par = Params()
    m, cap = module_energy(par)
    tt = pd.read_csv(OUT / "through_time.csv")
    daily = pd.read_csv(OUT / "daily_operation.csv.gz", parse_dates=["date"])

    # 1 cumulative cash through time -------------------------------------------------------------------
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.3))
    groups = ((axs[0], ("A", "B", "C"), "The 40 MW plant from Tier 1 under three operating assumptions"),
              (axs[1], ("D", "G"), "Plants re-sized for a 5-day minimum run"))
    names = dict(A="Unsold energy only, free daily switching (Tier 1 assumption)", B="Unsold energy only, 5-day minimum run",
                 C="Minimum load topped up, 5-day minimum run")
    cols = dict(A=MUTED, B=VIOLET, C=BLUE, D=BLUE, G=ORANGE)
    for ax, keys, title in groups:
        for k in keys:
            x = daily[daily.design == k]
            row = tt[tt.design == k].iloc[0]
            lab = names.get(k, f"{RULE_NAME[row.rule]}, {row.electrolyser_MW:.0f} MW")
            ax.plot(x.date, x.cumulative_cash_m, color=cols[k], label=lab, ls="--" if k == "A" else "-")
        ax.axhline(0, color=INK2, lw=0.9)
        ax.set_title(title); ax.set_ylabel("Cumulative cash since investment, GBP m (2023 prices)")
        ax.legend(loc="upper left", fontsize=8.5)
    fig.suptitle("Cash position day by day, 2020-2025: investment paid at the start, operating cash and fixed costs added daily",
                 x=0.01, ha="left", fontsize=10, color=INK2)
    fig.tight_layout(); done(fig, "fig1_cash_through_time.png"); plt.close(fig)

    # 2 minimum run ---------------------------------------------------------------------------------------
    mr = pd.read_csv(OUT / "min_run.csv")
    if "never_off" not in mr: mr["never_off"] = np.nan
    fig, axs = plt.subplots(1, 4, figsize=(13, 3.6))
    for ax, lab in zip(axs, mr.label.drop_duplicates()):
        x = mr[(mr.label == lab) & mr.never_off.isna()].sort_values("min_run")
        rule = x.rule.iloc[0]
        pos = np.arange(len(x))
        ax.plot(pos, x.net_gain_m, color=RULE_COL[rule], marker="o", ms=5)
        never = mr[(mr.label == lab) & mr.never_off.notna()]
        ticks, labs = list(pos), [str(v) for v in x.min_run]
        if len(never):
            ax.plot([len(x)], never.net_gain_m, color=RULE_COL[rule], marker="s", ms=6, ls="none")
            ticks.append(len(x)); labs.append("never\noff")
        ax.set_xticks(ticks); ax.set_xticklabels(labs)
        ax.axhline(0, color=INK2, lw=0.9)
        ax.set_title(f"{RULE_NAME[rule]}\n{x.electrolyser_MW.iloc[0]:.0f} MW", fontsize=9.5)
        ax.set_xlabel("Minimum run, days")
    axs[0].set_ylabel("Net gain, GBP m per year")
    fig.suptitle("Effect of the minimum run on annual net gain (plant size held fixed; each panel has its own scale)",
                 x=0.01, ha="left", fontsize=10, color=INK2)
    fig.tight_layout(); done(fig, "fig2_minimum_run.png"); plt.close(fig)

    # 3 sizing curves -------------------------------------------------------------------------------------
    sc = pd.read_csv(OUT / "sizing_curve.csv")
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.9))
    for ax, rule in zip(axs, ("strict", "topup", "divert")):
        for L, ls, lab in ((1, "--", "Free daily switching"), (5, "-", "5-day minimum run")):
            x = sc[(sc.rule == rule) & (sc.min_run == L)]
            ax.plot(x.electrolyser_MW, x.net_gain_m, color=RULE_COL[rule] if L == 5 else MUTED, ls=ls, marker="o", ms=3.5, label=lab)
        ax.axhline(0, color=INK2, lw=0.9)
        ax.set_title(RULE_NAME[rule], fontsize=10); ax.set_xlabel("Electrolyser capacity, MW"); ax.legend(fontsize=8.5)
    axs[0].set_ylabel("Net gain, GBP m per year")
    fig.suptitle("Annual net gain against plant size, with and without the minimum run (each panel has its own scale)",
                 x=0.01, ha="left", fontsize=10, color=INK2)
    fig.tight_layout(); done(fig, "fig3_sizing.png"); plt.close(fig)

    # 4 seasonal pattern ----------------------------------------------------------------------------------
    se = pd.read_csv(OUT / "seasonal.csv")
    mon = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
    fig, axs = plt.subplots(2, 2, figsize=(11.5, 6.4))
    d0 = se[se.design == "D"]
    axs[0, 0].bar(d0.month, d0.unsold_GWh_per_day, color=MUTED, width=0.68)
    axs[0, 0].set_title("Wind-farm energy with no buyer"); axs[0, 0].set_ylabel("GWh per day")
    axs[0, 1].bar(d0.month, d0.price, color=MUTED, width=0.68); axs[0, 1].axhline(par.margin, color=RED, lw=1.2)
    axs[0, 1].text(12.4, par.margin, " hydrogen\n break-even", color=INK2, fontsize=8.5, va="center")
    axs[0, 1].set_title("Electricity price"); axs[0, 1].set_ylabel("GBP per MWh (2023 prices)")
    for key, c, off in (("D", BLUE, -0.2), ("G", ORANGE, 0.2)):
        x = se[se.design == key]; row = tt[tt.design == key].iloc[0]
        util = x.h2_t_per_day * par.kwh_per_kg / (cap * row.modules)
        lab = f"{RULE_NAME[row.rule]}, {row.electrolyser_MW:.0f} MW"
        axs[1, 0].bar(x.month + off, util * 100, color=c, width=0.38, label=lab)
        axs[1, 1].bar(x.month + off, x.share_from_unsold * 100, color=c, width=0.38, label=lab)
    axs[1, 0].set_title("Share of electrolyser capacity in use"); axs[1, 0].set_ylabel("%")
    axs[1, 1].set_title("Share of hydrogen made from energy with no buyer"); axs[1, 1].set_ylabel("%")
    for ax in axs.flat:
        ax.set_xticks(range(1, 13)); ax.set_xticklabels(mon)
    fig.suptitle("Average by calendar month, 2020-2025", x=0.01, ha="left", fontsize=10, color=INK2)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    h, l = axs[1, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, fontsize=9)
    done(fig, "fig4_seasonal.png"); plt.close(fig)

    # 5 one hard stretch, day by day ---------------------------------------------------------------------
    sw = pd.read_csv(OUT / "stress_windows.csv")
    w = sw[(sw.window.str.startswith("Longest stretch with price above")) & (sw.design == "D")].iloc[0]
    a, b = pd.Timestamp(w.start) - pd.Timedelta(days=21), pd.Timestamp(w.end) + pd.Timedelta(days=21)
    x = daily[(daily.design == "D") & (daily.date >= a) & (daily.date <= b)]
    N = int(tt[tt.design == "D"].modules.iloc[0])
    fig, axs = plt.subplots(4, 1, figsize=(11, 8.2), sharex=True)
    axs[0].plot(x.date, x.price, color=INK2); axs[0].axhline(par.margin, color=RED, lw=1.2)
    axs[0].set_title("Electricity price (line at the hydrogen break-even of GBP %.0f/MWh)" % par.margin); axs[0].set_ylabel("GBP/MWh")
    axs[1].fill_between(x.date, x.unsold_MWh / 1e3, color=MUTED, alpha=0.45, lw=0)
    axs[1].set_title("Wind-farm energy with no buyer"); axs[1].set_ylabel("GWh per day")
    axs[2].step(x.date, x.modules_on, where="mid", color=BLUE)
    axs[2].set_title(f"Modules running (of {N})"); axs[2].set_ylabel("modules"); axs[2].set_ylim(-0.5, N + 0.8)
    axs[3].stackplot(x.date, x.from_unsold_MWh / 1e3, x.diverted_MWh / 1e3, x.imported_MWh / 1e3, colors=[BLUE, AQUA, YELLOW],
                     labels=["energy with no buyer", "own saleable output", "grid import"], lw=0)
    axs[3].set_title("Electricity taken by the electrolyser, by source"); axs[3].set_ylabel("GWh per day")
    axs[3].set_ylim(0, float((x.load_MWh / 1e3).max()) * 1.28)
    axs[3].legend(fontsize=8.5, ncol=3, loc="upper left")
    for ax in axs:
        ax.axvspan(pd.Timestamp(w.start), pd.Timestamp(w.end), color=RED, alpha=0.06, lw=0)
    fig.suptitle(f"A hard stretch: {w.days} consecutive days with the price above the hydrogen break-even "
                 f"({w.start} to {w.end}, shaded), top-up plant of {N * 20} MW", x=0.01, ha="left", fontsize=10, color=INK2)
    fig.tight_layout(); done(fig, "fig5_stress_window.png"); plt.close(fig)

    # 6 forecasts -----------------------------------------------------------------------------------------
    sk = pd.read_csv(OUT / "forecast_skill.csv"); cal = pd.read_csv(OUT / "calibration.csv")
    fig, axs = plt.subplots(2, 2, figsize=(11.5, 6.6))
    tn = dict(farm_MW=("Wind-farm output", "MW"), gap_MW=("National demand minus generation", "MW"), price=("Electricity price", "GBP/MWh"))
    mn = dict(persist=("Tomorrow equals today", MUTED), ar=("Regression on recent days and calendar", BLUE),
              neso=("Regression + NESO day-ahead forecast", ORANGE))
    for ax, t in zip(axs.flat[:3], tn):
        for k, (lab, c) in mn.items():
            x = sk[(sk.target == t) & (sk.method == k)]
            ax.plot(x.horizon_days, x.mae, color=c, marker="o", ms=4, label=lab)
        ax.set_title(f"{tn[t][0]}: mean absolute error"); ax.set_ylabel(tn[t][1]); ax.set_xlabel("Days ahead"); ax.set_ylim(bottom=0)
    axs[0, 0].legend(fontsize=8.5, loc="lower right")
    ax = axs[1, 1]
    for col, lab, c in (("mae_as_published", "NESO forecast as published", MUTED), ("mae_persistence", "Tomorrow equals today", INK2),
                        ("mae_fixed_scale", "Scaled once, on 2021", AQUA), ("mae_recalibrated_yearly", "Re-calibrated every year", ORANGE)):
        ax.plot(cal.year.astype(str), cal[col], color=c, marker="o", ms=4, label=lab)
    ax.set_title("National demand one day ahead: error before and after calibration"); ax.set_ylabel("MW")
    ax.set_ylim(0, float(cal["mae_as_published"].max()) * 1.45)
    ax.legend(fontsize=8.5, ncol=2, loc="upper center")
    fig.suptitle("Forecast errors on 2022-2025; every forecast uses only information available on the day it is made",
                 x=0.01, ha="left", fontsize=10, color=INK2)
    fig.tight_layout(); done(fig, "fig6_forecasts.png"); plt.close(fig)

    # 7 rolling operation ---------------------------------------------------------------------------------
    ro = pd.read_csv(OUT / "rolling.csv")
    ro = ro[~ro.method.str.startswith("Full")]
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.2), sharey=True)
    order = list(ro.method.drop_duplicates())[::-1]
    for ax, rule in zip(axs, ("topup", "divert")):
        for h2, c, mk in ((9.5, BLUE, "o"), (7.5, AQUA, "s"), (6.0, ORANGE, "D")):
            x = ro[(ro.rule == rule) & (ro.h2_value == h2)].set_index("method").loc[order]
            ax.plot(x.share_of_full_foresight * 100, range(len(order)), color=c, marker=mk, ms=7, ls="none",
                    label=f"hydrogen at GBP {h2:g}/kg")
        ax.set_yticks(range(len(order))); ax.set_yticklabels(order)
        ax.axvline(100, color=INK2, lw=0.9); ax.grid(axis="x"); ax.grid(axis="y", visible=False)
        ax.set_xlabel("Operating cash as % of full foresight, 2022-2025")
        ax.set_title(f"{RULE_NAME[rule]}, {int(ro[ro.rule == rule].modules.iloc[0]) * 20} MW", fontsize=10)
    fig.suptitle("What can be earned without knowing the future: commitment decided one day ahead, re-planned every day",
                 x=0.01, ha="left", fontsize=10, color=INK2)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=9)
    done(fig, "fig7_rolling_operation.png"); plt.close(fig)

    # 8 sensitivity ---------------------------------------------------------------------------------------
    sn = pd.read_csv(OUT / "sensitivity.csv")
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 8.2), sharey=True)
    labels = list(sn.label.drop_duplicates())[::-1]
    for ax, rule in zip(axs, ("topup", "divert")):
        x = sn[sn.rule == rule].set_index("label").loc[labels]
        cols = [INK2 if g == "central" else RULE_COL[rule] for g in x.group]
        ax.barh(range(len(labels)), x.electrolyser_MW, color=cols, height=0.64)
        for i, (mw, g) in enumerate(zip(x.electrolyser_MW, x.net_gain_m)):
            ax.text(mw + x.electrolyser_MW.max() * 0.012, i, f"{g:,.1f}m" if mw else "no plant", va="center", fontsize=8, color=INK2)
        ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=8.5)
        ax.grid(axis="x"); ax.grid(axis="y", visible=False); ax.set_xlim(0, x.electrolyser_MW.max() * 1.16)
        ax.set_xlabel("Best electrolyser capacity, MW"); ax.set_title(RULE_NAME[rule], fontsize=10)
    fig.suptitle("Best plant size when one assumption changes (5-day minimum run unless stated); labels show annual net gain, GBP",
                 x=0.01, ha="left", fontsize=10, color=INK2)
    fig.tight_layout(); done(fig, "fig8_sensitivity.png"); plt.close(fig)


if __name__ == "__main__":
    main()
