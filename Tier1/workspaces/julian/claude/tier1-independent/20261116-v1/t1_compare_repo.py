"""Compare the independent Tier 1 with the group repository's Tier 1 (v6 daily model, Ran Min / mocry-codex).

repo_data/ holds the repository's repaired inputs (Tier1 v6 `inputs/`, rebuilt from Elexon/NESO records).
Three questions:
  A. how close is my folder-only data cleaning to their source-level repair?
  B. does my model reproduce their published numbers when given their data and assumptions?
  C. which assumption explains the gap between their answer and mine (one change at a time)?
Usage: python t1_compare_repo.py
"""
from __future__ import annotations
import csv, json
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import t1_data
import t1_model as M
from t1_run import best_n, style, OUT, BLUE, ORANGE, INK2, AXIS, MUTED

REPO = Path(__file__).resolve().parent / "repo_data"
F = t1_data.CPI[2023] / t1_data.CPI[2020]            # 2020 pounds -> 2023 pounds
# repository v6 cost basis (GBP 2020): ITM NEPTUNE V per MW, 5% real, 30 years, stack renewals in years 11 and 22
R_CAPEX, R_FOM, R_STACK, R_RATE, R_LIFE = 1_460_439.72, 25_861.65, 489_609.26, 0.05, 30
R_PV = R_CAPEX + R_STACK * ((1 + R_RATE) ** -11 + (1 + R_RATE) ** -22)
R_H2 = 7.7990270551508845                            # GBP2020/kg netback
PUBLISHED = {"B": dict(MW=739.557, gain=37.712), "A": dict(MW=3631.341, gain=1638.660),
             "B10": dict(MW=23.424, gain=2.440), "A10": dict(MW=23.424, gain=12.681)}


def repo_frame(start="2020-01-01", end="2025-12-31"):
    def daily(name, col="date"):
        f = pd.read_csv(REPO / name); f.index = pd.to_datetime(f.pop(col), utc=True).dt.tz_localize(None); return f.sort_index()
    gen = daily("daily_generation_total.csv").total_MW
    farm = daily("wind_farm_generation.csv").wind_farm_MW
    dem = daily("daily_demand.csv", "startTime").demand
    price = daily("daily_market_index_price.csv").iloc[:, 0]
    cpi = {}
    with (REPO / "CPI.csv").open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.reader(fh):
            try: cpi[pd.to_datetime(row[0], format="%Y %b").strftime("%Y-%m")] = float(row[1])
            except (ValueError, IndexError): pass
    idx = gen.index
    real2020 = price.to_numpy() * 108.7 / np.array([cpi[t.strftime("%Y-%m")] for t in idx])
    df = pd.DataFrame({"farm_MW": farm.reindex(idx), "gen_MW": gen, "demand_MW": dem.reindex(idx), "price_nominal": price,
                       "price_2020": real2020, "price": real2020 * F}, index=idx)
    return df.loc[start:end]


def repo_params(policy, money_2023=False, **kw):
    k = F if money_2023 else 1.0
    return M.Params(policy=policy, boundary="system", h2_value=R_H2 * k, el_capex=R_PV * k, el_fom=R_FOM / R_PV, el_life=R_LIFE, rate=R_RATE,
                    stack_share=0.0, module_mw=5.031, min_load_mode="none", n_max=900, **kw)


def main():
    OUT.mkdir(exist_ok=True)
    mine, theirs = t1_data.load(), repo_frame()
    out = {}
    # ---------------- A. data
    a = {}
    j = mine.join(theirs, rsuffix="_repo", how="inner")
    tue = j.demand_fixed
    a["demand_replaced_days"] = int(tue.sum())
    a["demand_replaced_MAE_MW"] = float((j.demand_MW - j.demand_MW_repo)[tue].abs().mean())
    a["demand_replaced_bias_pct"] = float(((j.demand_MW - j.demand_MW_repo)[tue] / j.demand_MW_repo[tue]).mean() * 100)
    a["demand_raw_error_on_those_days_pct"] = float(((j.demand_raw - j.demand_MW_repo)[tue & (j.demand_raw > 10000)] / j.demand_MW_repo[tue & (j.demand_raw > 10000)]).mean() * 100)
    a["demand_other_days_MAE_MW"] = float((j.demand_MW - j.demand_MW_repo)[~tue].abs().mean())
    untouched = ~j.price_fixed
    a["price_ratio_mine_to_repo_untouched_days_median"] = float((j.price_nominal / j.price_nominal_repo)[untouched].median())
    a["price_untouched_days_within_1pct"] = float((((j.price_nominal / j.price_nominal_repo)[untouched] - 1).abs() < 0.01).mean())
    a["price_replaced_days"] = int(j.price_fixed.sum())
    a["price_replaced_MAE"] = float((j.price_nominal - j.price_nominal_repo)[j.price_fixed].abs().mean())
    a["price_mean_mine"], a["price_mean_repo"] = float(j.price_nominal.mean()), float(j.price_nominal_repo.mean())
    imp = j.gen_imputed
    a["generation_imputed_days"] = int(imp.sum())
    a["generation_imputed_MAE_MW"] = float((j.gen_MW - j.gen_MW_repo)[imp].abs().mean())
    a["generation_imputed_bias_MW"] = float((j.gen_MW - j.gen_MW_repo)[imp].mean())
    a["generation_other_days_MAE_MW"] = float((j.gen_MW - j.gen_MW_repo)[~imp].abs().mean())
    a["generation_other_days_changed_over_100MW"] = int(((j.gen_MW - j.gen_MW_repo)[~imp].abs() > 100).sum())
    for name, d in (("mine", mine), ("repo", theirs)):
        p = M.Problem(d, M.Params())
        a[f"unused_share_{name}"] = float(p.S.sum() / (d.farm_MW.sum() * 24)); a[f"days_gen_above_demand_{name}"] = float((d.gen_MW > d.demand_MW).mean())
        a[f"days_fleet_plus_farm_above_demand_{name}"] = float((d.gen_MW + d.farm_MW > d.demand_MW).mean())
    same_sign = ((j.gen_MW > j.demand_MW) == (j.gen_MW_repo > j.demand_MW_repo))
    a["days_same_surplus_classification"] = float(same_sign.mean())
    out["data"] = a
    print(json.dumps(a, indent=1))

    # ---------------- B. reproduction of the repository's published v6 results (their data, their assumptions, GBP2020)
    th20 = theirs.copy(); th20["price"] = th20["price_2020"]
    rep = []
    for key, pol, cap in (("B", "surplus", None), ("A", "divert", 1_558_969.0), ("B10", "surplus", 10_000.0), ("A10", "divert", 10_000.0)):
        o, _ = best_n(M.Problem(th20, repo_params(pol, h2_cap_kg_day=cap)))
        rep.append(dict(case=key, published_MW=PUBLISHED[key]["MW"], reproduced_MW=o["electrolyser_MW"], published_gain_m=PUBLISHED[key]["gain"],
                        reproduced_gain_m=o["net_gain_m"], h2_t_per_year=o["h2_t_per_year"]))
    rep = pd.DataFrame(rep); rep.to_csv(OUT / "repo_reproduction.csv", index=False); print(rep.round(3).to_string())

    # ---------------- C. bridge, one change at a time (money in GBP2023 from step 2)
    bridge = []
    mine_cost = dict(el_capex=2_000_000, el_fom=0.03, el_life=25, rate=0.08, stack_share=0.30)
    for pol, key, cap in (("surplus", "B", None), ("divert", "A", 1_558_969.0)):
        steps = [
            ("1 Repository as published (their data, GBP2020)", th20, repo_params(pol, h2_cap_kg_day=cap)),
            ("2 Repository result, restated in 2023 pounds", theirs, repo_params(pol, money_2023=True, h2_cap_kg_day=cap)),
            ("3 + only the farm's own unused output counts", theirs, replace(repo_params(pol, money_2023=True), boundary="farm", n_max=None, h2_cap_kg_day=None)),
            ("4 + my electrolyser cost and 8% discount rate", theirs, replace(repo_params(pol, money_2023=True), boundary="farm", n_max=None, h2_cap_kg_day=None, **mine_cost)),
            ("5 + hydrogen at GBP 9.5/kg", theirs, replace(repo_params(pol, money_2023=True), boundary="farm", n_max=None, h2_cap_kg_day=None, h2_value=9.5, **mine_cost)),
            ("6 + my data cleaning", mine, replace(repo_params(pol, money_2023=True), boundary="farm", n_max=None, h2_cap_kg_day=None, h2_value=9.5, **mine_cost)),
            ("7 + 20 MW modules with 4 MW minimum load (= mine)", mine, M.Params(policy=pol)),
        ]
        for name, frame, par in steps:
            o, _ = best_n(M.Problem(frame, par))
            bridge.append(dict(policy=pol, repo_policy=key, step=name, electrolyser_MW=o["electrolyser_MW"], net_gain_m=o["net_gain_m"], capex_m=o["capex_m"],
                               h2_t_per_year=o["h2_t_per_year"], payback_years=o["payback_years"]))
        # alternative order: change the cost first, keep their boundary
        o, _ = best_n(M.Problem(theirs, replace(repo_params(pol, money_2023=True, h2_cap_kg_day=cap), **mine_cost)))
        bridge.append(dict(policy=pol, repo_policy=key, step="alt: their boundary and data, my cost and discount rate", electrolyser_MW=o["electrolyser_MW"], net_gain_m=o["net_gain_m"],
                           capex_m=o["capex_m"], h2_t_per_year=o["h2_t_per_year"], payback_years=o["payback_years"]))
    bridge = pd.DataFrame(bridge); bridge.to_csv(OUT / "repo_bridge.csv", index=False); print(bridge.round(2).to_string())

    # ---------------- D. each side's design in the other side's world
    swap = []
    for pol, key, cap, their_mw in (("surplus", "B", None, 739.557), ("divert", "A", 1_558_969.0, 3631.341)):
        my_prob = M.Problem(mine, M.Params(policy=pol)); my_opt, _ = best_n(my_prob)
        their_prob = M.Problem(theirs, repo_params(pol, money_2023=True, h2_cap_kg_day=cap)); their_opt, _ = best_n(their_prob)
        n_their_in_mine = min(int(round(their_mw / 20)), my_prob.n_max)
        swap.append(dict(policy=pol, design="mine", MW=my_opt["electrolyser_MW"], in_my_model_m=my_opt["net_gain_m"],
                         in_their_model_m=M.evaluate_exact(their_prob, my_opt["electrolyser_MW"] / 5.031)["net_gain_m"], best_in_their_model_m=their_opt["net_gain_m"]))
        swap.append(dict(policy=pol, design="repository", MW=their_mw, in_my_model_m=M.evaluate_exact(my_prob, n_their_in_mine)["net_gain_m"],
                         in_their_model_m=their_opt["net_gain_m"], best_in_their_model_m=their_opt["net_gain_m"],
                         note=f"capped at the farm size {n_their_in_mine * 20} MW in my model" if n_their_in_mine * 20 < their_mw else ""))
    swap = pd.DataFrame(swap); swap.to_csv(OUT / "repo_design_swap.csv", index=False); print(swap.round(2).to_string())
    out["note"] = "money in GBP2023 except the reproduction table (GBP2020)"
    json.dump(out, open(OUT / "repo_comparison.json", "w"), indent=2, default=float)

    plt = style()
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
    for ax, pol, c, ttl in ((axs[0], "surplus", BLUE, "Unused energy only (repo policy B)"), (axs[1], "divert", ORANGE, "Also diverting (repo policy A)")):
        b = bridge[(bridge.policy == pol) & ~bridge.step.str.startswith("alt")].iloc[1:]
        y = np.arange(len(b))[::-1]
        ax.barh(y, b.electrolyser_MW, color=c, height=0.62)
        for yy, v, g in zip(y, b.electrolyser_MW, b.net_gain_m): ax.text(v + b.electrolyser_MW.max() * 0.015, yy, f"{v:,.0f} MW   £{g:,.1f}m/yr", va="center", fontsize=8.5, color=INK2)
        ax.set_yticks(y); ax.set_yticklabels([s[2:] for s in b.step], fontsize=8.5); ax.grid(axis="x"); ax.grid(axis="y", visible=False)
        ax.set_xlim(0, b.electrolyser_MW.max() * 1.45); ax.set_title(f"{ttl}: best size (MW)")
    fig.tight_layout(); fig.savefig(OUT / "fig8_bridge_to_repository.png", dpi=160, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    main()
