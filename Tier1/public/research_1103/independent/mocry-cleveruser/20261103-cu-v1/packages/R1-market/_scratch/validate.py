"""Validate R1 deliverables: JSON parses, claim count, source_ref resolution, key arithmetic."""
import json
import os

BASE = os.path.join("Tier1", "workspaces", "mocry", "cleveruser", "firstpass", "R1-market")

with open(os.path.join(BASE, "parameters.json"), encoding="utf-8") as fh:
    params = json.load(fh)
with open(os.path.join(BASE, "sources.json"), encoding="utf-8") as fh:
    sources = json.load(fh)

claims = params["claims"]
print("claims:", len(claims))
ids = [c["id"] for c in claims]
assert len(ids) == len(set(ids)), "duplicate claim ids"
print("unique claim ids: True")

src_ids = {s["id"] for s in sources["sources"]}
print("sources:", len(src_ids))
missing = sorted({r for c in claims for r in c["source_ref"] if r not in src_ids})
print("unresolved source_ref:", missing)

gaps = sorted({c["gap_id"] for c in claims})
print("gap ids covered:", gaps)

# required fields present on every claim
req = ["id", "gap_id", "meaning", "value_type", "value", "unit", "currency", "price_year",
       "scope", "source_ref", "evidence_strength", "recommended_baseline", "sensitivity_range"]
for c in claims:
    for k in req:
        assert k in c, (c["id"], k)
print("all required claim fields present: True")

# arithmetic checks
c = {x["id"]: x for x in claims}
assert abs(c["R1-C11"]["value"] - 28113.0 * 24) < 1e-6, "C11 demand energy"
assert abs(c["R1-C12"]["value"] - 25583.0 * 24) < 1e-6, "C12 generation energy"
assert abs(c["R1-C19"]["value"] - 1 / 0.90) < 1e-4, "C19 threshold"
assert abs(c["R1-C20"]["value"] + (48.17 - 0.90 * 48.17)) < 0.01, "C20 loss per MWh"
assert abs(c["R1-C21"]["value"] - 100 * 424.6 / 28113.0) < 0.01, "C21 share"
assert abs(c["R1-C22"]["value"] - 100 * 1125.0 / 28113.0) < 0.01, "C22 share"
assert abs(c["R1-C23"]["value"] - 100 * 1125.0 / 20779.0) < 0.01, "C23 share"
assert abs(c["R1-C34"]["value"] - 9.5 / 55.9 * 1000) < 0.05, "C34 H2 equivalent"
assert abs(c["R1-C35"]["value"] - 424.6 * 24 * 48.17 * 365) < 1.0, "C35 revenue anchor"
print("arithmetic assertions: all pass")
print("C34 recompute:", round(9.5 / 55.9 * 1000, 2), "GBP/MWh")
print("C35 recompute:", round(424.6 * 24 * 48.17 * 365, 0), "GBP/yr")

# report cross-reference: every claim id appears in the report or its JSON is the record
with open(os.path.join(BASE, "REPORT.md"), encoding="utf-8") as fh:
    report = fh.read()
print("report chars:", len(report))
for token in ("E-01", "E-02", "E-03", "E-04", "E-05", "E-06", "E-07"):
    assert token in report, token
print("all E- ids present in report: True")
assert "27 typed claims" not in report
print("stale claim count removed: True")
print("OK")
