"""Two final independent checks.

1. 2025-03-11: dump FUELHH half-hours 09:30-12:30 UTC to see exactly which intervals
   are zero and whether mocry-codex's interpolated daily means are consistent with a
   linear fill between the intact 10:00 and 12:00 readings.
2. 2022-12-13: does current AGPT still report all non-wind fuels at zero while FUELHH
   shows ~22.8 GW of gas? That is the crux of "the course zeros are an upstream fault".
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

FUELHH = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH?settlementDateFrom=2025-03-11&settlementDateTo=2025-03-12&format=json"
AGPT = "https://data.elexon.co.uk/bmrs/api/v1/generation/actual/per-type?from=2022-12-13T00:00Z&to=2022-12-14T00:00Z&format=json"


def get(url):
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))["data"]


out = {}
rows = [r for r in get(FUELHH) if r["startTime"][:10] == "2025-03-11" and "09:30" <= r["startTime"][11:16] <= "12:30"]
table = {}
for r in rows:
    table.setdefault(r["startTime"][11:16], {})[r["fuelType"]] = r["generation"]
fuels = ["CCGT", "OCGT", "NUCLEAR", "BIOMASS", "NPSHYD", "PS", "OTHER", "COAL", "OIL"]
out["fuelhh_2025_03_11_window"] = [
    {"utc": t, **{f: table[t].get(f) for f in fuels}} for t in sorted(table)]

ag = get(AGPT)
zero_periods = []
nonzero = {}
for rec in ag:
    vals = {d["psrType"]: d["quantity"] for d in rec["data"]}
    nonwind = {k: v for k, v in vals.items() if k not in ("Wind Onshore", "Wind Offshore")}
    if all(v == 0 for v in nonwind.values()):
        zero_periods.append(rec["startTime"])
    for k, v in nonwind.items():
        if v:
            nonzero[k] = max(nonzero.get(k, 0.0), v)
out["agpt_2022_12_13"] = {
    "periods": len(ag),
    "periods_all_nonwind_zero": len(zero_periods),
    "max_nonzero_nonwind_by_fuel": nonzero,
    "sample_period": ag[0]["startTime"],
    "sample_vals": {d["psrType"]: d["quantity"] for d in ag[0]["data"]},
}

Path(__file__).resolve().parents[1].joinpath("audit", "final_spot_checks.json").write_text(
    json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, indent=2))
