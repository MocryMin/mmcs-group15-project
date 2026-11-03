#!/usr/bin/env python3
"""One-off repair of the accidentally inserted literal line in audit_data.py."""
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "tools" / "audit_data.py"
lines = P.read_text(encoding="utf-8").splitlines(keepends=True)
fixed = []
repaired = False
for line in lines:
    if line.startswith('new="def parse_date'):
        fixed.append(
            'def parse_date(value: str) -> date:\n'
            '    value = value.strip()\n'
            '    if "T" in value:  # ISO timestamp such as 2020-01-01T00:00:00Z\n'
            '        value = value.split("T", 1)[0]\n'
            '    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%m/%d/%Y"):\n'
        )
        repaired = True
        continue
    fixed.append(line)
P.write_text("".join(fixed), encoding="utf-8")
print("repaired:", repaired, "lines:", len(fixed))
