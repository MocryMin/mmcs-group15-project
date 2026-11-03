"""Characterise the 2026 dates inside the repair: how much do the 11 cells and the
total move, and is the largest renewable cell change consistent with the total delta?"""
from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
REL = REPO / "Tier1/public/data_quality/generation_repair/20261103-v1"


def rows(p):
    return list(csv.DictReader(p.read_text(encoding="utf-8-sig").splitlines()))


of, rf = {}, {}
for r in rows(REPO / "daily_generation_by_fuel.csv"):
    of.setdefault(r["date"], {})[r["psrType"]] = float(r["MW"])
for r in rows(REL / "daily_generation_by_fuel.csv"):
    rf.setdefault(r["date"], {})[r["psrType"]] = float(r["MW"])
ot = {r["date"]: float(r["total_MW"]) for r in rows(REPO / "daily_generation_total.csv")}
rt = {r["date"]: float(r["total_MW"]) for r in rows(REL / "daily_generation_total.csv")}

audit = json.loads((REL / "generation_repair_audit.json").read_text(encoding="utf-8"))
methods = {p["d"]: p["method"] for p in audit["patches"]}
d2026 = [d for d, m in methods.items() if m == "AGPT_48_half_hours"]

out = {"agpt_48_half_hours_dates": {}, "worst_cells": []}
for d in sorted(d2026):
    tot = round(rt[d] - ot[d], 1)
    diffs = {f: round(rf[d][f] - of[d].get(f, 0.0), 1) for f in rf[d]
             if abs(rf[d][f] - of[d].get(f, 0.0)) > 1}
    ren = {f: v for f, v in diffs.items() if f in ("Wind Onshore", "Wind Offshore", "Solar")}
    out["agpt_48_half_hours_dates"][d] = {
        "total_delta_MW": tot, "sum_of_cell_deltas": round(sum(diffs.values()), 1),
        "renewable_cells": ren, "all_cell_deltas": diffs}
    for f, v in ren.items():
        out["worst_cells"].append({"date": d, "fuel": f, "delta_MW": v, "total_delta_MW": tot})
out["worst_cells"].sort(key=lambda r: -abs(r["delta_MW"]))

# same for the 61 non-repaired 2026 AGPT differences: what is the recorded gap
diff = audit["provenance_test"]["current_agpt_differences_2026"]
outside = [r for r in diff if str(r[3]).lower() in ("false", "False")]
gaps = [abs(float(r[1]) - float(r[2])) for r in outside if r[1] is not None and r[2] is not None]
gaps.sort()
out["non_repaired_2026_differences"] = {
    "count": len(outside),
    "abs_gap_MW_min": gaps[0] if gaps else None,
    "abs_gap_MW_median": gaps[len(gaps) // 2] if gaps else None,
    "abs_gap_MW_max": gaps[-1] if gaps else None,
    "dates_first_last": [outside[0][0], outside[-1][0]] if outside else None,
}
Path(__file__).resolve().parents[1].joinpath("audit", "repair_2026_detail.json").write_text(
    json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "agpt_48_half_hours_dates"}, indent=2))
for d, rec in sorted(out["agpt_48_half_hours_dates"].items())[:30]:
    print(d, "totalΔ", rec["total_delta_MW"], "sumΔcells", rec["sum_of_cell_deltas"], rec["renewable_cells"])
