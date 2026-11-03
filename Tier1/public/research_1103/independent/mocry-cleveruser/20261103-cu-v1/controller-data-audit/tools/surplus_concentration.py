#!/usr/bin/env python3
"""Surplus concentration diagnostics (adds to the controller audit note)."""
from __future__ import annotations

import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parents[1] / "audit" / "data_audit.json"
d = json.loads(AUDIT.read_text(encoding="utf-8"))
cs = d["combined_system"]

total = cs["total_surplus_MWh_over_window"]
top5 = cs["top5_surplus_days"]
top5_sum = sum(x["surplus_MWh"] for x in top5)

# recompute full distribution from the audit's stats is not possible; recompute from CSVs
import csv
from datetime import date

REPO = Path(__file__).resolve().parents[5]


def load_dates():
    def rows(name):
        text = (REPO / name).read_text(encoding="utf-8-sig")
        return list(csv.DictReader(text.splitlines()))

    demand = {r["startTime"][:10]: float(r["demand"]) for r in rows("daily_demand.csv")}
    total_gen = {r["date"]: float(r["total_MW"]) for r in rows("daily_generation_total.csv")}
    wind = {r["date"]: float(r["wind_farm_MW"]) for r in rows("wind_farm_generation.csv")}
    price = {r["date"]: float(r["avg_price_£_per_MWh"]) for r in rows("daily_market_index_price.csv")}
    common = sorted(set(demand) & set(total_gen) & set(wind) & set(price))
    return common, demand, total_gen, wind, price


common, demand, total_gen, wind, price = load_dates()
sur = {d_: max(0.0, (total_gen[d_] + wind[d_]) - demand[d_]) * 24.0 for d_ in common}
ranked = sorted(sur.items(), key=lambda kv: kv[1], reverse=True)
tot = sum(sur.values())
out = {
    "n_days": len(common),
    "total_surplus_MWh": round(tot, 1),
    "top1_share": round(ranked[0][1] / tot, 4),
    "top10_share": round(sum(v for _, v in ranked[:10]) / tot, 4),
    "top50_share": round(sum(v for _, v in ranked[:50]) / tot, 4),
    "days_with_surplus": sum(1 for v in sur.values() if v > 0),
    "surplus_excluding_2022-08-02_MWh": round(tot - sur["2022-08-02"], 1),
    "top10_days": [{"date": k, "surplus_MWh": round(v, 1)} for k, v in ranked[:10]],
    "second_largest_MWh": round(ranked[1][1], 1),
    "ratio_largest_to_second": round(ranked[0][1] / ranked[1][1], 2),
}
print(json.dumps(out, indent=2))
(Path(__file__).resolve().parents[1] / "audit" / "surplus_concentration.json").write_text(
    json.dumps(out, indent=2) + "\n", encoding="utf-8")
