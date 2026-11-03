"""One-off normalisation: resolve source_ref aliases and register own-computation pseudo-sources."""
import json
import os

BASE = os.path.join("Tier1", "workspaces", "mocry", "cleveruser", "firstpass", "R1-market")

ALIAS = {
    "BASELINE-1103-BL07": "BASELINE-1103",
    "BASELINE-1103-BL09": "BASELINE-1103",
    "BASELINE-1103-BL11": "BASELINE-1103",
    "LCCC": "LCCC-BMRP",
}

p = os.path.join(BASE, "parameters.json")
with open(p, encoding="utf-8") as fh:
    params = json.load(fh)

changed = 0
for c in params["claims"]:
    refs = []
    for r in c["source_ref"]:
        r2 = ALIAS.get(r, r)
        if r2 != r:
            changed += 1
        if r2 not in refs:
            refs.append(r2)
    c["source_ref"] = refs

with open(p, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(params, fh, ensure_ascii=False, indent=2)
    fh.write("\n")
print("alias replacements:", changed)

s = os.path.join(BASE, "sources.json")
with open(s, encoding="utf-8") as fh:
    sources = json.load(fh)

have = {x["id"] for x in sources["sources"]}
pseudo = [
    {
        "id": "OWN-COMPUTE",
        "publisher": "This pass (reproducible local computation)",
        "title": "_scratch/analyze_inputs.py applied to the byte-identical input copies",
        "url": None,
        "local_path": "Tier1/workspaces/mocry/cleveruser/firstpass/R1-market/_scratch/analyze_inputs.py",
        "doc_type": "own computation from supplied inputs",
        "access_utc": "2026-11-03",
        "locator": "script output (row counts, coverage, intersection, price statistics, unit identity, scale shares)",
        "quotes": [],
        "supports": "All figures in REPORT.md marked 'own computation' and the derived claims R1-C02..C06, C09..C12, C16, C19..C23, C31, C32, C34, C35.",
        "evidence_strength": "high for arithmetic on the supplied files; it inherits every limitation of those files",
    },
    {
        "id": "OWN-INFERENCE",
        "publisher": "This pass",
        "title": "Reasoning step, not a sourced fact",
        "url": None,
        "doc_type": "own inference",
        "access_utc": "2026-11-03",
        "locator": "n/a",
        "quotes": [],
        "supports": "Used where the conclusion follows from market structure plus the source set (e.g. net metering forbidding simultaneous import and export at one connection) rather than from a single quoted sentence. Flagged so the reader can separate evidence from reasoning.",
        "evidence_strength": "medium",
    },
]
for entry in pseudo:
    if entry["id"] not in have:
        sources["sources"].append(entry)

with open(s, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(sources, fh, ensure_ascii=False, indent=2)
    fh.write("\n")
print("sources now:", len(sources["sources"]))
