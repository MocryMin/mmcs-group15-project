# -*- coding: utf-8 -*-
"""Quantify the second defect family (solar/PS zeroed days) and the 30 missing dates
against live AGPT; also profile demand seasonality."""
import csv
import json
import os
import statistics
import urllib.request
from collections import defaultdict

BASE = "https://data.elexon.co.uk/bmrs/api/v1"
REPO = os.path.abspath(".")
AUD = os.path.join(REPO, "Tier1", "workspaces", "mocry", "cleveruser", "audit")

gen = defaultdict(dict)
for r in csv.DictReader(open(os.path.join(REPO, "daily_generation_by_fuel.csv"), encoding="utf-8", newline="")):
    gen[r["date"]][r["psrType"]] = float(r["MW"])
tot = {r["date"]: float(r["total_MW"])
       for r in csv.DictReader(open(os.path.join(REPO, "daily_generation_total.csv"), encoding="utf-8", newline=""))}
dem = {r["startTime"][:10]: float(r["demand"])
       for r in csv.DictReader(open(os.path.join(REPO, "daily_demand.csv"), encoding="utf-8", newline=""))}
wf = {r["date"]: float(r["wind_farm_MW"])
      for r in csv.DictReader(open(os.path.join(REPO, "wind_farm_generation.csv"), encoding="utf-8", newline=""))}

a1 = json.load(open(os.path.join(AUD, "all_data_audit.json"), encoding="utf-8"))
a2 = json.load(open(os.path.join(AUD, "all_data_audit2.json"), encoding="utf-8"))
solar_zero = a2["solar_zero_dates"]
missing = a1["series"]["generation_by_fuel"]["missing_calendar_days"]


def agpt_day(day):
    url = "%s/datasets/AGPT?PublishDateTimeFrom=%sT00:00Z&PublishDateTimeTo=%sT23:59Z&format=json" % (BASE, day, day)
    req = urllib.request.Request(url, headers={"User-Agent": "cu-audit/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        rows = json.loads(r.read().decode("utf-8")).get("data", [])
    acc = defaultdict(list)
    for r in rows:
        if r.get("quantity") is None:
            continue
        if r["startTime"][:10] != day:
            continue
        acc[r["psrType"]].append(float(r["quantity"]))
    return {k: sum(v) / len(v) for k, v in acc.items()}, len(rows)


out = {"solar_zero_days": [], "missing_days": []}
for day in solar_zero:
    try:
        m, n = agpt_day(day)
    except Exception as e:  # noqa
        out["solar_zero_days"].append({"date": day, "error": repr(e)[:200]})
        continue
    rec = {
        "date": day, "agpt_rows": n,
        "course_total": tot.get(day), "agpt_total": round(sum(m.values()), 1),
        "course_solar": gen.get(day, {}).get("Solar"), "agpt_solar": round(m.get("Solar", 0.0), 1),
        "course_ps": gen.get(day, {}).get("Hydro Pumped Storage"),
        "agpt_ps": round(m.get("Hydro Pumped Storage", 0.0), 1),
        "course_gas": gen.get(day, {}).get("Fossil Gas"), "agpt_gas": round(m.get("Fossil Gas", 0.0), 1),
        "course_demand": dem.get(day),
    }
    rec["total_gap_MW"] = round((rec["agpt_total"] or 0) - (rec["course_total"] or 0), 1)
    out["solar_zero_days"].append(rec)
    print("solarzero", day, "course", rec["course_total"], "agpt", rec["agpt_total"],
          "gap", rec["total_gap_MW"], "solar", rec["course_solar"], "/", rec["agpt_solar"])

for day in missing:
    try:
        m, n = agpt_day(day)
        out["missing_days"].append({"date": day, "agpt_rows": n, "agpt_total": round(sum(m.values()), 1),
                                    "course_demand": dem.get(day), "course_windfarm": wf.get(day)})
        print("missing ", day, "agpt_total", round(sum(m.values()), 1), "rows", n)
    except Exception as e:  # noqa
        out["missing_days"].append({"date": day, "error": repr(e)[:200]})

# ---- summaries
zs = [r for r in out["solar_zero_days"] if "total_gap_MW" in r]
gaps = [r["total_gap_MW"] for r in zs]
out["solar_zero_summary"] = {
    "n": len(zs),
    "n_upstream_higher": sum(1 for g in gaps if g > 100),
    "n_upstream_lower": sum(1 for g in gaps if g < -100),
    "mean_gap_MW": round(statistics.fmean(gaps), 1) if gaps else None,
    "median_gap_MW": round(statistics.median(gaps), 1) if gaps else None,
    "max_gap_MW": max(gaps) if gaps else None,
    "min_gap_MW": min(gaps) if gaps else None,
    "sum_gap_TWh": round(sum(gaps) * 24 / 1e6, 3) if gaps else None,
    "n_solar_zero_upstream_too": sum(1 for r in zs if (r.get("agpt_solar") or 0) == 0),
}
ms = [r for r in out["missing_days"] if "agpt_total" in r]
out["missing_summary"] = {"n": len(ms), "n_with_upstream_data": sum(1 for r in ms if (r.get("agpt_total") or 0) > 0),
                          "mean_agpt_total": round(statistics.fmean([r["agpt_total"] for r in ms]), 1) if ms else None}

# ---- demand seasonality and annual levels
mon = defaultdict(list)
for d, v in dem.items():
    mon[d[:7]].append(v)
out["demand_monthly"] = {k: {"mean": round(statistics.fmean(v), 1), "max": max(v), "min": min(v), "n": len(v)}
                         for k, v in sorted(mon.items())}
ann = defaultdict(list)
for d, v in dem.items():
    ann[d[:4]].append(v)
out["demand_annual_TWh"] = {y: round(sum(v) * 24 / 1e6, 1) for y, v in sorted(ann.items())}
out["demand_monthly_max_top"] = sorted(((max(v), k) for k, v in mon.items()), reverse=True)[:8]

# wind farm zero days
out["windfarm_zero_days"] = [d for d, v in wf.items() if v == 0]

json.dump(out, open(os.path.join(AUD, "agpt_defect_family.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("\nSUMMARY solar-zero family:", json.dumps(out["solar_zero_summary"], ensure_ascii=False))
print("SUMMARY missing days:", json.dumps(out["missing_summary"], ensure_ascii=False))
print("demand annual TWh:", out["demand_annual_TWh"])
print("monthly max top:", out["demand_monthly_max_top"])
print("windform zeros:", out["windfarm_zero_days"])
print("monthly:", json.dumps(out["demand_monthly"], ensure_ascii=False))
