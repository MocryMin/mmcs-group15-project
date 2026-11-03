#!/usr/bin/env python3
"""Build the isolated input bundle for independent first-pass research.

Copies only the question/input material (never Tier1/public/research_1103) so that
first-pass researchers cannot see the earlier research round's conclusions.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
OUT = REPO / "Tier1/workspaces/mocry/cleveruser/inputs"

SOURCES = [
    "PROJECT.md",
    "Project_Brief.pdf",
    "Project_Launch_Transcript.txt",
    "Project_Launch_Transcript_Timed.txt",
    "SOURCE_MANIFEST.json",
    "daily_demand.csv",
    "daily_generation_by_fuel.csv",
    "daily_generation_total.csv",
    "daily_market_index_price.csv",
    "wind_farm_generation.csv",
    "Tier1/public/baseline_1103/BASELINE_1103.md",
    "Tier1/public/baseline_1103/GAPS.md",
    "Tier1/public/baseline_1103/TEACHER_CLARIFICATIONS.md",
    "Tier1/public/baseline_1103/TEACHER_ORIGINAL_EXCERPTS.md",
    "Tier1/public/baseline_1103/RESEARCH_REQUEST.md",
    "Tier1/public/baseline_1103/RESEARCH_RESULT_TEMPLATE.md",
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    entries = []
    for rel in SOURCES:
        src = REPO / rel
        dst = OUT / Path(rel).name
        data = src.read_bytes()
        dst.write_bytes(data)
        entries.append({
            "source_path_in_repo": rel,
            "bundle_file": dst.name,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    manifest = {
        "bundle": "cleveruser-independent-firstpass-inputs",
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "built_by": "mocry-cleveruser",
        "purpose": "Byte-identical copies of the question and supplied inputs, given to first-pass researchers who must not read Tier1/public/research_1103/**.",
        "excluded_on_purpose": [
            "Tier1/public/research_1103/** (earlier research round)",
            "Tier2/** (not yet used)",
        ],
        "files": entries,
    }
    (OUT / "INPUT_BUNDLE.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"bundle files: {len(entries)}")
    for e in entries:
        print(f"{e['bundle_file']:<45} {e['bytes']:>8} {e['sha256'][:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
