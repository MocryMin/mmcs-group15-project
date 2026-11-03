#!/usr/bin/env python3
"""Print section headings and line counts for each first-pass report."""
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "firstpass"
for path in sorted(BASE.rglob("REPORT.md")):
    text = path.read_text(encoding="utf-8").splitlines()
    print(f"\n=== {path.parent.name} ({len(text)} lines) ===")
    for i, line in enumerate(text, start=1):
        if line.startswith("## "):
            print(f"  {i:>4}  {line}")
