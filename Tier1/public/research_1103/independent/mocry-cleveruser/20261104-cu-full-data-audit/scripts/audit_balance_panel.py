# -*- coding: utf-8 -*-
"""Balance on the full generation-intersect-demand panel (price not required)."""
import csv
import json
import os
import statistics
from collections import defaultdict

REPO = os.path.abspath(".")
tot = {r["date"]: float(r["total_MW"]) for r in csv.DictReader(open("daily_generation_total.csv", encoding="utf-8", newline=""))}
dem = {r["startTime"][:10]: float(r["demand"]) for r in csv.DictReader(open("daily_demand.csv", encoding="utf-8", newline=""))}
price = {r["date"]: float(r["avg_price_£_per_MWh"]) for r in csv.DictReader(open("daily_market_index_price.csv", encoding="utf-8", newline=""))}
wf = {r["date"]: float(r["wind_farm_MW"]) for r in csv.DictReader(open("wind_farm_generation.csv", encoding="utf-8", newline=""))}
rep = os.path.join(REPO, "Tier1", "public", "data_quality", "generation_repair", "20261103-v1")
rtot = {r["date"]: float(r["total_MW"]) for r in csv.DictReader(open(os.path.join(rep, "daily_generation_total.csv"), encoding="utf-8", newline=""))}

gd = sorted(set(tot) & set(dem))
gd_price = sorted(set(tot) & set(dem) & set(price))
out = {"n_gen_intersect_demand": len(gd), "n_gen_demand_price": len(gd_price)}


def bal(days, total, add_wind=False):
    b = [(d, total[d] + (wf.get(d, 0.0) if add_wind else 0.0) - dem[d]) for d in days if d in total]
    return {"days": len(b),
            "deficit_TWh": round(sum(-x for _, x in b if x < 0) * 24 / 1e6, 3),
            "surplus_TWh": round(sum(x for _, x in b if x > 0) * 24 / 1e6, 3),
            "net_TWh": round(sum(x for _, x in b) * 24 / 1e6, 3),
            "mean_gap_MW": round(statistics.fmean([x for _, x in b]), 1)}


out["gen_intersect_demand"] = {
    "orig_gen_only": bal(gd, tot),
    "rep_gen_only": bal(gd, rtot),
    "orig_gen_plus_windfarm": bal(gd, tot, True),
    "rep_gen_plus_windfarm": bal(gd, rtot, True),
    "orig_with_price_subset": bal(gd_price, tot),
    "rep_with_price_subset": bal(gd_price, rtot),
}

# annual on gen-intersect-demand
ann = {}
for y in sorted({d[:4] for d in gd}):
    days = [d for d in gd if d[:4] == y]
    b = [(d, tot[d] - dem[d]) for d in days]
    br = [(d, rtot[d] - dem[d]) for d in days if d in rtot]
    ann[y] = {"days": len(days),
              "net_orig": round(sum(x for _, x in b) * 24 / 1e6, 3),
              "net_rep": round(sum(x for _, x in br) * 24 / 1e6, 3),
              "deficit_orig": round(sum(-x for _, x in b if x < 0) * 24 / 1e6, 3),
              "deficit_rep": round(sum(-x for _, x in br if x < 0) * 24 / 1e6, 3),
              "surplus_orig": round(sum(x for _, x in b if x > 0) * 24 / 1e6, 3),
              "surplus_rep": round(sum(x for _, x in br if x > 0) * 24 / 1e6, 3)}
out["by_year"] = ann

# price coverage classes
p_only = sorted(set(price) - set(tot))
no_price = sorted(set(tot) - set(price))
missing_gen = sorted(set(price) | set(tot))  # placeholder
out["price_coverage"] = {"price_dates": len(price), "gen_dates": len(tot),
                         "price_only_n": len(p_only), "gen_only_n": len(no_price),
                         "intersection": len(set(price) & set(tot)),
                         "price_only_dates": p_only, "gen_without_price_dates": no_price}

# effect of the corrupt demand value
d2 = dict(dem)
d2["2022-08-02"] = statistics.fmean([dem["2022-08-01"], dem["2022-08-03"]])
b = [(d, tot[d] - dem[d]) for d in gd]
b2 = [(d, tot[d] - d2[d]) for d in gd]
out["demand_outlier_effect"] = {
    "neighbour_mean_MW": round(d2["2022-08-02"], 1),
    "surplus_with_636_TWh": round(sum(x for _, x in b if x > 0) * 24 / 1e6, 3),
    "surplus_with_neighbours_TWh": round(sum(x for _, x in b2 if x > 0) * 24 / 1e6, 3),
    "gap_with_636_MW": round(tot["2022-08-02"] - 636, 1),
    "gap_with_neighbours_MW": round(tot["2022-08-02"] - d2["2022-08-02"], 1),
}
json.dump(out, open(os.path.join(REPO, "Tier1", "workspaces", "mocry", "cleveruser", "audit",
                                 "balance_panel.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(out, ensure_ascii=False, indent=1))
