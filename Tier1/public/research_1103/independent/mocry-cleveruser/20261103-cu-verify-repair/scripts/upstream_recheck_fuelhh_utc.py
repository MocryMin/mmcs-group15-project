"""Upstream FUELHH re-check, v2: select half-hours by UTC day (timeFrom), not settlement date.

v1 (upstream_recheck_fuelhh.py) filtered on settlementDate, which is the local
(GMT/BST) settlement day. That matches their repair on winter dates and is shifted
by one hour on BST dates; winter dates matched exactly, which is itself evidence.
This version rebuilds each date from the UTC-day intervals.
"""
from __future__ import annotations

import csv
import json
import statistics
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
REL = REPO / "Tier1/public/data_quality/generation_repair/20261103-v1"
API = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH"
MAP = {"Biomass": ["BIOMASS"], "Fossil Gas": ["CCGT", "OCGT"], "Fossil Hard coal": ["COAL"],
       "Fossil Oil": ["OIL"], "Hydro Pumped Storage": ["PS"], "Hydro Run-of-river and poundage": ["NPSHYD"],
       "Nuclear": ["NUCLEAR"], "Other": ["OTHER"]}


def fetch(d: str):
    """Fetch three settlement days so a UTC day is fully covered under BST."""
    from datetime import date as _date, timedelta
    y, m, dd = map(int, d.split("-"))
    lo = (_date(y, m, dd) - timedelta(days=1)).isoformat()
    hi = (_date(y, m, dd) + timedelta(days=1)).isoformat()
    url = f"{API}?settlementDateFrom={lo}&settlementDateTo={hi}&format=json"
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))["data"]


def repaired_rows(d: str):
    text = (REL / "daily_generation_by_fuel.csv").read_text(encoding="utf-8-sig")
    return {r["psrType"]: float(r["MW"]) for r in csv.DictReader(text.splitlines()) if r["date"] == d}


patches = [p["d"] for p in json.loads((REL / "generation_repair_audit.json").read_text(encoding="utf-8"))["patches"]]
sample = list(dict.fromkeys([patches[0]] + [patches[i] for i in range(15, len(patches), 15)][:5]
                            + ["2023-01-01", "2025-03-11", "2026-07-13"]))

out_dates = {}
fields = None
for d in sample:
    raw = fetch(d)
    if fields is None:
        fields = sorted(raw[0].keys())
    # intervals whose UTC start falls on d
    utc = [r for r in raw if r["startTime"][:10] == d]
    per = {}
    for r in utc:
        per.setdefault(r["fuelType"], []).append(float(r["generation"]))
    theirs = repaired_rows(d)
    rec = {"utc_intervals": len({r["startTime"] for r in utc}), "cmp": {}}
    worst = 0.0
    for target, srcs in MAP.items():
        if target == "Hydro Pumped Storage":
            vals = [max(0.0, v) for v in per.get("PS", [])] or None
        elif len(srcs) == 2:
            vals = ([a + b for a, b in zip(per["CCGT"], per["OCGT"])]
                    if "CCGT" in per and "OCGT" in per else None)
        else:
            vals = per.get(srcs[0])
        if not vals:
            rec["cmp"][target] = "absent"
            continue
        my = round(statistics.fmean(vals), 0)
        t = theirs.get(target)
        dl = None if t is None else round(my - t, 1)
        rec["cmp"][target] = {"me": my, "them": t, "d": dl, "n": len(vals)}
        if dl is not None:
            worst = max(worst, abs(dl))
    rec["max_abs_delta_MW"] = worst
    if d == "2025-03-11":
        rec["zero_intervals"] = {"CCGT": sum(1 for v in per.get("CCGT", []) if v == 0),
                                 "NUCLEAR": sum(1 for v in per.get("NUCLEAR", []) if v == 0),
                                 "OCGT": sum(1 for v in per.get("OCGT", []) if v == 0)}
    out_dates[d] = rec

report = {"fuelhh_fields": fields, "sample": sample, "dates": out_dates,
          "max_abs_delta_overall_MW": max(r["max_abs_delta_MW"] for r in out_dates.values())}
Path(__file__).resolve().parents[1].joinpath("audit", "upstream_recheck_fuelhh_utc.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8")

print("fields:", fields)
for d, rec in out_dates.items():
    parts = [f"{t[:4]} me={c['me']} them={c['them']} d={c['d']} n={c['n']}"
             for t, c in rec["cmp"].items() if isinstance(c, dict)]
    print(f"\n{d} utc_intervals={rec['utc_intervals']} worst={rec['max_abs_delta_MW']}")
    print("   " + " | ".join(parts))
    if "zero_intervals" in rec:
        print("   zeros:", rec["zero_intervals"])
print("\noverall max abs delta MW:", report["max_abs_delta_overall_MW"])
