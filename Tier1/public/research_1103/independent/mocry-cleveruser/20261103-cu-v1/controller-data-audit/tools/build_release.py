#!/usr/bin/env python3
"""Assemble the public release tree for the independent first pass.

Copies text deliverables (md/json/py) from the firstpass folders plus the controller
audit into `release/20261103-cu-v1/`, skipping binaries and oversized files, and writes
RELEASE_MANIFEST.json with sizes and SHA-256 hashes of the release copy.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]           # .../cleveruser
RELEASE = BASE / "release" / "20261103-cu-v1"
PACKAGES = ["R1-market", "R2-battery", "R3-hydrogen", "R4-finance-data"]
TEXT_SUFFIXES = {".md", ".json", ".py", ".txt", ".csv"}
MAX_BYTES = 512 * 1024


def main() -> int:
    if RELEASE.exists():
        shutil.rmtree(RELEASE)
    RELEASE.mkdir(parents=True)

    copied = []
    skipped = []

    def add(src: Path, rel: str) -> None:
        if not src.is_file():
            return
        if src.suffix.lower() not in TEXT_SUFFIXES:
            skipped.append({"source": str(src.relative_to(BASE)), "reason": "binary/unsupported type"})
            return
        size = src.stat().st_size
        if size > MAX_BYTES:
            skipped.append({"source": str(src.relative_to(BASE)), "reason": f"larger than {MAX_BYTES} bytes"})
            return
        dst = RELEASE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        copied.append({
            "release_path": rel,
            "source": str(src.relative_to(BASE)).replace("\\", "/"),
            "bytes": size,
            "sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
        })

    for pkg in PACKAGES:
        root = BASE / "firstpass" / pkg
        if not root.is_dir():
            skipped.append({"source": f"firstpass/{pkg}", "reason": "package folder missing"})
            continue
        for src in sorted(root.rglob("*")):
            if not src.is_file():
                continue
            rel_inner = src.relative_to(root).as_posix()
            # Vendor documents and scratch binaries stay local; scripts and text go public.
            add(src, f"packages/{pkg}/{rel_inner}")

    audit = BASE / "audit"
    for src in sorted(audit.rglob("*")):
        if src.is_file():
            add(src, f"controller-data-audit/{src.name}")

    for src in sorted((BASE / "tools").glob("*.py")):
        add(src, f"controller-data-audit/tools/{src.name}")

    synth = BASE / "synthesis"
    if synth.is_dir():
        for src in sorted(synth.iterdir()):
            if src.is_file():
                add(src, src.name)

    manifest = {
        "release": "20261103-cu-v1",
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "builder": "mocry-cleveruser",
        "purpose": "Independent (unleaky) Tier1 research first passes produced by Clever User harness workers, plus a controller data audit.",
        "copied": copied,
        "skipped": skipped,
    }
    (RELEASE / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"copied {len(copied)} files, skipped {len(skipped)}")
    for c in copied:
        print(f"  {c['bytes']:>8}  {c['release_path']}")
    for s in skipped:
        print(f"  SKIP {s['source']}: {s['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
