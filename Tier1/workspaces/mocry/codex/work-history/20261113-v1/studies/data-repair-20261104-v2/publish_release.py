"""Publish the completed, verified data repair through the repository helper."""
import contextlib
import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
REPO = HERE.parent / "group-collaboration"
sys.path.insert(0, str(REPO / "tools"))
import collab

PUBLIC = "Tier1/public/data_quality/full_data_repair/20261104-v2"
NAMES = [
    "README.md", "REPAIR_SUMMARY_ZH.md", "REPAIR_AUDIT.json", "VALIDATION.json",
    "IMPUTATION_VALIDATION.json", "repair_data.py", "validate_release.py", "evaluate_imputation.py",
    "collect_public.py", "collect_agpt.js", "collect_fuelhh.js", "collect_demand.js", "collect_mid.js",
    "collect_neso.js",
    *["evidence/" + k + ".json.gz" for k in ("agpt", "fuelhh", "demand", "mid", "neso")],
    *["data/" + k for k in ("daily_generation_by_fuel.csv", "daily_generation_total.csv",
                           "daily_demand.csv", "daily_market_index_price.csv", "wind_farm_generation.csv",
                           "cell_audit.csv", "quality.csv", "date_quality.csv")],
]
assert not collab.git_text("status", "--porcelain", cwd=REPO)
assert collab.git_text("rev-parse", "HEAD", cwd=REPO) == collab.git_text("rev-parse", "origin/main", cwd=REPO)
validation = json.loads((HERE / "VALIDATION.json").read_text(encoding="utf-8"))
assert validation["all_assertions_passed"]
base = collab.git_text("rev-parse", "HEAD", cwd=REPO)
manifest = {
    "version": "20261104-v2",
    "published_by": "mocry-codex",
    "member_name": "Ran Min",
    "authorization": "User requested repair of all exposed dataset problems with sources, methods and GitHub publication.",
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "base_commit": base,
    "course_inputs_at_repository_root": True,
    "public_path": PUBLIC,
    "content_hash_convention": "SHA-256 of exact Git-clean published bytes; manifest excludes itself.",
    "files": [],
}
for name in NAMES:
    data = collab.clean_bytes(REPO, PUBLIC + "/" + name, (HERE / name).read_bytes())
    manifest["files"].append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
(HERE / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
operations = []
for name in [*NAMES, "MANIFEST.json"]:
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture):
        collab.publish(SimpleNamespace(tier="Tier1", area="Tier1",
                        path=PUBLIC.split("/public/", 1)[1] + "/" + name,
                        source=str(HERE / name),
                        summary="Publish full data repair 20261104-v2: " + name), REPO)
    operations.append(json.loads(capture.getvalue()))
for item in manifest["files"]:
    assert hashlib.sha256((REPO / PUBLIC / item["path"]).read_bytes()).hexdigest() == item["sha256"]
paths = [op["path"] for op in operations] + ["Tier1/public/logs/mocry-codex.jsonl"]
collab.git("add", "--", *paths, cwd=REPO)
collab.git("-c", "core.whitespace=cr-at-eol", "diff", "--cached", "--check", cwd=REPO)
collab.commit(SimpleNamespace(tier="Tier1", message="Publish complete course data repair with source snapshots and quality audit"), REPO)
receipt = {
    "public_path": PUBLIC,
    "commit": collab.git_text("rev-parse", "HEAD", cwd=REPO),
    "operations": len(operations),
    "manifest_sha256": hashlib.sha256((REPO / PUBLIC / "MANIFEST.json").read_bytes()).hexdigest(),
}
(HERE / "PUBLICATION_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt))

