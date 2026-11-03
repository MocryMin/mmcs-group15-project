"""Quantify the 2026 gap the repair leaves, and test one big non-repaired date upstream."""
from __future__ import annotations

import csv
import json
import statistics
import urllib.request
from datetime import date as _date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
REL = REPO / "Tier1/public/data_quality/generation_repair/20261103-v1"
AUD = Path(__file__).resolve().parents[1] / "audit"


def rows(p):
    return list(csv.DictReader(p.read_text(encoding="utf-8-sig").splitlines()))


dem = {r["startTime"][:10]: float(r["demand"]) for r in rows(REPO / "daily_demand.csv")}
wind = {r["date"]: float(r["wind_farm_MW"]) for r in rows(REPO / "wind_farm_generation.csv")}
rt = {r["date"]: float(r["total_MW"]) for r in rows(REL / "daily_generation_total.csv")}
audit = json.loads((REL / "generation_repair_audit.json").read_text(encoding="utf-8"))
gaps = json.loads((AUD / "agpt_2026_gaps.json").read_text(encoding="utf-8"))
outside = [g for g in gaps if str(g["in_repair"]).lower() == "false"]

# effect of accepting current AGPT totals on the 61 non-repaired 2026 dates
def year_bal(total):
    d2026 = [d for d in total if d.startswith("2026") and d in dem and d in wind]
    s = sum(max(0.0, (total[d] + wind[d]) - dem[d]) * 24 / 1e6 for d in d2026)
    df = sum(max(0.0, dem[d] - (total[d] + wind[d])) * 24 / 1e6 for d in d2026)
    return round(s, 3), round(df, 3), len(d2026)


base_s, base_d, n26 = year_bal(rt)
alt = dict(rt)
for g in outside:
    if g["date"] in alt:
        alt[g["date"]] = g["current_agpt_total_MW"]
alt_s, alt_d, _ = year_bal(alt)
big8 = [g for g in outside if abs(g["delta_MW"]) > 1000]
alt8 = dict(rt)
for g in big8:
    if g["date"] in alt8:
        alt8[g["date"]] = g["current_agpt_total_MW"]
a8_s, a8_d, _ = year_bal(alt8)

out = {
    "2026_days": n26,
    "repaired_2026": {"surplus_TWh": base_s, "deficit_TWh": base_d},
    "if_all_61_AGPT_totals_adopted": {"surplus_TWh": alt_s, "deficit_TWh": alt_d,
                                      "n_dates": len([g for g in outside if g["date"] in alt])},
    "if_only_the_8_over_1GW_adopted": {"surplus_TWh": a8_s, "deficit_TWh": a8_d, "n_dates": len(big8),
                                       "dates": [g["date"] for g in big8]},
}

# upstream check of one non-repaired date with a ~15 GW gap
API = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH"
MAP = {"Biomass": ["BIOMASS"], "Fossil Gas": ["CCGT", "OCGT"], "Fossil Hard coal": ["COAL"],
       "Fossil Oil": ["OIL"], "Hydro Pumped Storage": ["PS"], "Hydro Run-of-river and poundage": ["NPSHYD"],
       "Nuclear": ["NUCLEAR"], "Other": ["OTHER"]}
of = {}
for r in rows(REPO / "daily_generation_by_fuel.csv"):
    of.setdefault(r["date"], {})[r["psrType"]] = float(r["MW"])


def fuelhh_day(d):
    y, m, dd = map(int, d.split("-"))
    lo = (_date(y, m, dd) - timedelta(days=1)).isoformat()
    hi = (_date(y, m, dd) + timedelta(days=1)).isoformat()
    with urllib.request.urlopen(f"{API}?settlementDateFrom={lo}&settlementDateTo={hi}&format=json", timeout=90) as r:
        raw = json.loads(r.read().decode("utf-8"))["data"]
    utc = [x for x in raw if x["startTime"][:10] == d]
    per = {}
    for x in utc:
        per.setdefault(x["fuelType"], []).append(float(x["generation"]))
    disp = 0.0
    detail = {}
    for target, srcs in MAP.items():
        if target == "Hydro Pumped Storage":
            vals = [max(0.0, v) for v in per.get("PS", [])]
        elif len(srcs) == 2:
            vals = [a + b for a, b in zip(per["CCGT"], per["OCGT"])]
        else:
            vals = per.get(srcs[0], [])
        m = round(statistics.fmean(vals), 0) if vals else None
        detail[target] = m
        if m:
            disp += m
    ren = sum(of.get(d, {}).get(f, 0.0) for f in ("Wind Onshore", "Wind Offshore", "Solar"))
    return {"intervals": len({x["startTime"] for x in utc}), "dispatchable_mean_sum_MW": round(disp, 0),
            "course_wind_solar_MW": round(ren, 0), "implied_total_MW": round(disp + ren, 0),
            "course_total_MW": round(rt.get(d, float("nan")), 0), "per_fuel": detail}


for d in [g["date"] for g in big8][:3]:
    out[f"fuelhh_check_{d}"] = fuelhh_day(d)

(AUD / "repair_2026_gap_effect.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, indent=2))
