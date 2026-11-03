#!/usr/bin/env python3
"""Print a compact digest of data_audit.json for the controller's own note."""
import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parents[1] / "audit" / "data_audit.json"
d = json.loads(AUDIT.read_text(encoding="utf-8"))

print("== files ==")
for name, f in d["files"].items():
    print(f"{name:<34} rows={f['data_rows']:>6} bytes={f['bytes']:>8} header={f['header']}")

print("\n== per-file coverage ==")
print({k: v for k, v in d["coverage"]["per_file_dates"].items()})
print("common:", d["coverage"]["common_dates"], d["coverage"]["common_date_min"], "->", d["coverage"]["common_date_max"])
print("missing between min/max:", d["coverage"]["missing_dates_between_min_and_max"])
print("segments:", [(s["start"], s["end"], s["days"]) for s in d["coverage"]["segments"]])

print("\n== demand ==", json.dumps(d["demand"], ensure_ascii=False)[:600])
print("\n== generation_total ==", json.dumps(d["generation_total"], ensure_ascii=False)[:600])
print("\n== by fuel ==", d["generation_by_fuel"]["technology_count"], d["generation_by_fuel"]["technologies"])
print("tech totals:", d["generation_by_fuel"]["technology_totals_MW_summed_over_days"])
print("reconciliation:", d["fuel_vs_total_reconciliation"])

print("\n== prices ==", json.dumps(d["prices"], ensure_ascii=False)[:1500])
print("\n== wind ==", json.dumps(d["wind_farm"], ensure_ascii=False)[:700])
print("\n== combined ==", json.dumps({k: v for k, v in d["combined_system"].items()
                                     if not k.startswith("top5") and not k.startswith("three_")},
                                    ensure_ascii=False, indent=1)[:2500])
print("\ntop5 surplus:", d["combined_system"]["top5_surplus_days"])
print("lowest demand:", d["combined_system"]["three_lowest_demand_days"])
print("highest price:", d["combined_system"]["three_highest_price_days"])
