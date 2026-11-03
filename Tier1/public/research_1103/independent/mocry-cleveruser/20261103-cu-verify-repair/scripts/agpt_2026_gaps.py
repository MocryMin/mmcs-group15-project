"""Rank the 61 non-repaired 2026 dates by |course total - current AGPT total|."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
REL = REPO / "Tier1/public/data_quality/generation_repair/20261103-v1"
audit = json.loads((REL / "generation_repair_audit.json").read_text(encoding="utf-8"))
diff = audit["provenance_test"]["current_agpt_differences_2026"]
rows = []
for r in diff:
    d, course, agpt, inrep = r[0], float(r[1]), float(r[2]), r[3]
    rows.append({"date": d, "course_total_MW": course, "current_agpt_total_MW": agpt,
                 "delta_MW": round(agpt - course, 1), "in_repair": inrep})
rows.sort(key=lambda r: -abs(r["delta_MW"]))
print(json.dumps(rows[:12], indent=1))
big = [r for r in rows if abs(r["delta_MW"]) > 1000]
print("\n|delta|>1000 MW:", len(big), "in_repair:", sum(1 for r in big if str(r["in_repair"]).lower() == "true"))
Path(__file__).resolve().parents[1].joinpath("audit", "agpt_2026_gaps.json").write_text(
    json.dumps(rows, indent=1) + "\n", encoding="utf-8")
