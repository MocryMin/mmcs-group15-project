"""Refresh MANIFEST.json hashes/bytes for the files it lists, and add any new tracked file.

Only rewrites hashes and sizes; it does not invent entries for files that are absent, and it
fails loudly if a listed path has disappeared. Additions must be requested on the command line
as `path:role`; each is inserted after the existing entries of the same directory.
"""

import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def digest(path):
    with open(path, "rb") as fh:
        blob = fh.read()
    return hashlib.sha256(blob).hexdigest(), len(blob)


def insert_after_dir(entries, entry):
    """Insert after the last entry that sits in the same directory."""
    directory = entry["path"].rsplit("/", 1)[0] if "/" in entry["path"] else ""
    last = None
    for i, old in enumerate(entries):
        old_dir = old["path"].rsplit("/", 1)[0] if "/" in old["path"] else ""
        if old_dir == directory:
            last = i
    if last is None:
        entries.append(entry)
    else:
        entries.insert(last + 1, entry)


def main(additions):
    path = os.path.join(ROOT, "MANIFEST.json")
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    entries = manifest["files"]

    missing = []
    for entry in entries:
        full = os.path.join(ROOT, entry["path"].replace("/", os.sep))
        if not os.path.exists(full):
            missing.append(entry["path"])
            continue
        entry["sha256"], entry["bytes"] = digest(full)
    if missing:
        print("MISSING listed files:", missing)
        return 1

    known = {e["path"] for e in entries}
    for spec in additions:
        rel, role = spec.split(":", 1)
        full = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(full):
            print("MISSING addition:", rel)
            return 1
        sha, size = digest(full)
        if rel in known:
            for entry in entries:
                if entry["path"] == rel:
                    entry["sha256"], entry["bytes"], entry["role"] = sha, size, role
        else:
            insert_after_dir(entries, {"path": rel, "sha256": sha, "bytes": size, "role": role})
            known.add(rel)

    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    bad = []
    for entry in entries:
        full = os.path.join(ROOT, entry["path"].replace("/", os.sep))
        sha, size = digest(full)
        if sha != entry["sha256"] or size != entry["bytes"]:
            bad.append(entry["path"])
    print(f"{len(entries)} entries refreshed, {len(bad)} mismatched")
    for name in bad:
        print("  mismatch:", name)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
