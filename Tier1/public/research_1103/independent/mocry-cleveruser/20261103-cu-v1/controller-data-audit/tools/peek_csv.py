#!/usr/bin/env python3
"""Peek at raw CSV structure, including any non-date rows ("VD")."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
FILES = ["daily_demand.csv", "daily_generation_by_fuel.csv", "daily_generation_total.csv",
         "daily_market_index_price.csv", "wind_farm_generation.csv"]
for name in FILES:
    p = REPO / name
    lines = p.read_text(encoding="utf-8-sig").splitlines()
    print("=" * 70)
    print(name, "lines:", len(lines), "first 3:", lines[:3])
    odd = [(i, l) for i, l in enumerate(lines) if l and not l[0].isdigit()]
    print("rows not starting with a digit:", len(odd))
    for i, l in odd[:6]:
        print(f"   line {i}: {l!r}")
    print("last 2:", lines[-2:])
