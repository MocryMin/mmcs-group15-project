"""Verify the delivered files using only the Python standard library."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    problems = []
    for name, record in manifest["files"].items():
        path = ROOT / name
        if not path.is_file():
            problems.append(f"Missing: {name}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            problems.append(f"Changed: {name}")
    if problems:
        raise RuntimeError("\n".join(problems))
    print(f"Verified {len(manifest['files'])} delivered files against SHA-256.")


if __name__ == "__main__":
    main()
