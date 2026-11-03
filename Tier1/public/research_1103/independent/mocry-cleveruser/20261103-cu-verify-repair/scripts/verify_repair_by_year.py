import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
REL = REPO / "Tier1/public/data_quality/generation_repair/20261103-v1"
DISPATCHABLE = {"Fossil Gas", "Fossil Hard coal", "Fossil Oil", "Nuclear", "Biomass",
                "Hydro Run-of-river and poundage", "Hydro Pumped Storage", "Other"}
RENEW = {"Wind Onshore", "Wind Offshore", "Solar"}


def rows(p):
    return list(csv.DictReader(p.read_text(encoding="utf-8-sig").splitlines()))


def fmap(p):
    o = {}
    for r in rows(p):
        o.setdefault(r["date"], {})[r["psrType"]] = float(r["MW"])
    return o


def tmap(p):
    return {r["date"]: float(r["total_MW"]) for r in rows(p)}


of, rf = fmap(REPO / "daily_generation_by_fuel.csv"), fmap(REL / "daily_generation_by_fuel.csv")
ot, rt = tmap(REPO / "daily_generation_total.csv"), tmap(REL / "daily_generation_total.csv")
dem = {r["startTime"][:10]: float(r["demand"]) for r in rows(REPO / "daily_demand.csv")}
wind = {r["date"]: float(r["wind_farm_MW"]) for r in rows(REPO / "wind_farm_generation.csv")}
common = sorted(set(dem) & set(ot) & set(wind))

audit = json.loads((REL / "generation_repair_audit.json").read_text(encoding="utf-8"))
methods = {p["d"]: p["method"] for p in audit["patches"]}

out = {}
# per-year deficit / surplus raw vs repaired
by_year = {}
for d in common:
    y = d[:4]
    b0 = (ot[d] + wind[d]) - dem[d]
    b1 = (rt[d] + wind[d]) - dem[d]
    rec = by_year.setdefault(y, {"days": 0, "raw_def": 0.0, "raw_sur": 0.0,
                                 "rep_def": 0.0, "rep_sur": 0.0})
    rec["days"] += 1
    rec["raw_def"] += max(0.0, -b0) * 24 / 1e6
    rec["raw_sur"] += max(0.0, b0) * 24 / 1e6
    rec["rep_def"] += max(0.0, -b1) * 24 / 1e6
    rec["rep_sur"] += max(0.0, b1) * 24 / 1e6
out["per_year_TWh"] = {y: {k: round(v, 3) for k, v in r.items()} for y, r in sorted(by_year.items())}

# renewable cell changes by method group
ren = {}
for d in methods:
    if d not in rf or d not in of:
        continue
    for f in sorted(RENEW):
        a, b = of[d].get(f, 0.0), rf[d].get(f, 0.0)
        if abs(a - b) > 1e-9:
            g = ren.setdefault(methods[d], {"cells": 0, "dates": set(), "abs_sum_MW": 0.0,
                                            "max_abs_MW": 0.0, "examples": []})
            g["cells"] += 1
            g["dates"].add(d)
            g["abs_sum_MW"] += abs(b - a)
            g["max_abs_MW"] = max(g["max_abs_MW"], abs(b - a))
            if len(g["examples"]) < 3:
                g["examples"].append([d, f, a, b])
out["renewable_cells_changed_by_method"] = {
    k: {"cells": v["cells"], "dates": len(v["dates"]),
        "abs_sum_MW": round(v["abs_sum_MW"], 1), "max_abs_MW": round(v["max_abs_MW"], 1),
        "examples": v["examples"]} for k, v in ren.items()}

# how big are the 61 non-repaired 2026 AGPT differences? only dates/columns recorded
diff = audit["provenance_test"]["current_agpt_differences_2026"]
out["agpt_2026_differences"] = {
    "count": len(diff),
    "columns": audit["provenance_test"]["current_agpt_difference_columns"],
    "first3": diff[:3],
    "in_107_set": sum(1 for d in diff if (d if isinstance(d, str) else d[0]) in methods),
}

# monthly distribution of repaired dates
mon = {}
for d in methods:
    mon[d[:7]] = mon.get(d[:7], 0) + 1
out["repaired_dates_by_month"] = dict(sorted(mon.items()))

Path(__file__).resolve().parents[1].joinpath("audit", "verify_repair_by_year.json").write_text(
    json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, indent=2))
