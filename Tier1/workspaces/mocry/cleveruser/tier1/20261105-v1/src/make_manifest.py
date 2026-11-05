import hashlib, json, pathlib

PKG = pathlib.Path(__file__).resolve().parents[1]
entries = []
for p in sorted(PKG.rglob("*")):
    if not p.is_file() or "__pycache__" in p.parts or p.name == "MANIFEST.json":
        continue
    rel = p.relative_to(PKG).as_posix()
    role = ("report" if rel.endswith(".md") and rel.isupper() or rel in
            ("TIER1_REPORT.md", "SUBMISSION_SECTION_4PP.md", "ONE_PAGE_DECISION.md", "PITCH_TALKING_POINTS.md", "README.md")
            else "data" if rel.startswith("data/") else
            "code" if rel.endswith(".py") else
            "figure" if rel.startswith("figures/") else
            "result")
    entries.append({"path": rel, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size, "role": role})
(PKG / "MANIFEST.json").write_text(json.dumps({"package": "Tier1 workspace CU build 20261105-v1", "files": entries}, indent=1), encoding="utf-8")
print(len(entries), "files", sum(e["bytes"] for e in entries) // 1024, "KB")
