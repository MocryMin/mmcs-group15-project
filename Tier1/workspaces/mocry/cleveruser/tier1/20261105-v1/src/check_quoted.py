"""Guard against prose numbers drifting from the result records.

Written after an external cross-check caught +£16.72m in four published files where
results/cases.csv holds 16.7781 for the 2020 A replay. The check is deliberately narrow:
it re-reads only what is already stored, so it cannot mask a modelling error, but it does
catch transcription slips between the CSV and the text.

Run from the package root:  python -B src/check_quoted.py
"""

import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = os.path.join(ROOT, "results", "cases.csv")
DOCS = [
    "TIER1_REPORT.md",
    "SUBMISSION_SECTION_4PP.md",
    "ONE_PAGE_DECISION.md",
    os.path.join("..", "..", "report", "20261105-v1", "Tier1_4pp.tex"),
]
YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def main():
    rows = {}
    with open(CASES, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows[row["case"]] = row

    values = {}
    for policy in ("A", "B"):
        seq = []
        for year in YEARS:
            key = f"{policy}_fixed20_{year}"
            if key not in rows:
                print(f"MISSING case {key}")
                return 1
            seq.append(float(rows[key]["increment_mGBP"]))
        values[policy] = seq

    checks = []

    # 1. The cross-year row in the long report must equal the CSV rounded to 2 dp.
    expect_a = "| A, £m/year | " + " | ".join(f"{v:.2f}" for v in values["A"]) + " |"
    expect_b = "| B, £m/year | " + " | ".join(f"{v:.2f}" for v in values["B"]) + " |"
    # The report uses a typographic minus in its tables; normalise before comparing.
    report = read(os.path.join(ROOT, "TIER1_REPORT.md")).replace("\u2212", "-")
    checks.append(("report_cross_year_row_A", expect_a in report, expect_a))
    checks.append(("report_cross_year_row_B", expect_b in report, expect_b))

    # 2. No document may quote the retired 2020 figure.
    for rel in DOCS:
        text = read(os.path.join(ROOT, rel))
        checks.append((f"no_stale_16.72::{os.path.basename(rel)}", "16.72" not in text, "16.72 absent"))

    # 3. Where a document quotes the 2020 replay it must quote the CSV value.
    quotes_2020 = {
        "SUBMISSION_SECTION_4PP.md": "+£16.78m (2020)",
        "ONE_PAGE_DECISION.md": "+£16.78m (2020)",
        os.path.join("..", "..", "report", "20261105-v1", "Tier1_4pp.tex"): "£16.78m (2020)",
    }
    for rel, needle in quotes_2020.items():
        text = read(os.path.join(ROOT, rel))
        checks.append((f"quoted_2020::{os.path.basename(rel)}", needle in text, needle))

    # 4. The headline numbers repeated across documents must match the CSV/prose source.
    headline = {
        "A_fixed20_2023": f"£{values['A'][3]:.2f}m",
        "B_fixed20_2023": f"{values['B'][3]:.2f}m",
    }
    checks.append(("headline_8.57", headline["A_fixed20_2023"] == "£8.57m", headline["A_fixed20_2023"]))
    checks.append(("headline_-1.07", abs(values["B"][3] + 1.07) < 0.005, values["B"][3]))

    failed = 0
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")
        failed += 0 if ok else 1
    print(f"{len(checks) - failed}/{len(checks)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
