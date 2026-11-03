"""Independent upstream re-query of FUELHH for a sample of the 107 repaired dates.

Rebuilds the daily mean MW for the eight dispatchable categories from the published
Elexon FUELHH endpoint and compares with mocry-codex's shipped repaired values.
Network access is live in this shell; no value is taken from their audit except the
fuel-type mapping rule and the sample dates.
"""
from __future__ import annotations

import csv
import json
import statistics
import urllib.request
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
REL = REPO / "Tier1/public/data_quality/generation_repair/20261103-v1"
API = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH"
MAP = {"Biomass": ["BIOMASS"], "Fossil Gas": ["CCGT", "OCGT"], "Fossil Hard coal": ["COAL"],
       "Fossil Oil": ["OIL"], "Hydro Pumped Storage": ["PS"], "Hydro Run-of-river and poundage": ["NPSHYD"],
       "Nuclear": ["NUCLEAR"], "Other": ["OTHER"]}


def fetch(d: str):
    url = f"{API}?settlementDateFrom={d}&settlementDateTo={d}&format=json"
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))["data"]


def repaired(d: str):
    text = (REL / "daily_generation_by_fuel.csv").read_text(encoding="utf-8-sig")
    return {r["psrType"]: float(r["MW"]) for r in csv.DictReader(text.splitlines()) if r["date"] == d}


patches = [p["d"] for p in json.loads((REL / "generation_repair_audit.json").read_text(encoding="utf-8"))["patches"]]
sample = [patches[0]] + [patches[i] for i in range(15, len(patches), 15)][:5] + ["2023-01-01", "2025-03-11"]
sample = list(dict.fromkeys(sample))

report = {"sample": sample, "dates": {}}
for d in sample:
    rows = [r for r in fetch(d) if r.get("settlementDate") == d]
    per = {}
    for r in rows:
        per.setdefault(r["fuelType"], []).append(float(r["generation"]))
    spans = sorted({r["settlementPeriod"] for r in rows})
    rec = {"intervals": len(spans), "fuels_present": len(per), "compare": {}}
    for target, srcs in MAP.items():
        if not all(s in per for s in srcs):
            rec["compare"][target] = {"my_MW": None, "note": "missing " + ",".join(s for s in srcs if s not in per)}
            continue
        if target == "Hydro Pumped Storage":
            vals = [max(0.0, v) for v in per["PS"]]
        elif len(srcs) == 2:
            vals = [a + b for a, b in zip(per["CCGT"], per["OCGT"])]
        else:
            vals = per[srcs[0]]
        my = round(statistics.fmean(vals), 0)
        theirs = repaired(d).get(target)
        rec["compare"][target] = {"my_MW": my, "theirs_MW": theirs,
                                  "delta_MW": None if theirs is None else round(my - theirs, 1),
                                  "n_intervals": len(vals)}
    if d == "2025-03-11":
        rec["raw_zero_intervals"] = {
            "CCGT": sum(1 for v in per.get("CCGT", []) if v == 0),
            "NUCLEAR": sum(1 for v in per.get("NUCLEAR", []) if v == 0),
            "OCGT": sum(1 for v in per.get("OCGT", []) if v == 0),
        }
        rec["ccgt_by_sp"] = {sp: per["CCGT"][i] for i, sp in enumerate(spans)}
    report["dates"][d] = rec

worst = 0.0
for d, rec in report["dates"].items():
    for t, c in rec["compare"].items():
        if c.get("delta_MW") is not None:
            worst = max(worst, abs(c["delta_MW"]))
report["max_abs_delta_MW"] = worst

out = Path(__file__).resolve().parents[1] / "audit" / "upstream_recheck_fuelhh.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
