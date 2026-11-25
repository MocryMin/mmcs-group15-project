# Tier 2B report preview

MMCS 2026/27 · Group 15 · 25 November 2026

The PDF contains five pages, numbered 6–10 to follow the introduction and Tier 1 v7.1. The standalone entry point is `tier2b-report-preview.tex`. The chapter body is `tier2.tex`. The source archive provides all figures and generated LaTeX tables required for compilation.

The chapter uses the 20% load floor for A with six modules, starts at midnight and a four-day minimum run. B uses no electrolysers. The capacity sweep retains the fitted controllers and uses one frozen zero-battery comparator per policy and window. The new simpler B rule is tested at one block. The corresponding larger counts still use the fitted classifier.

## Evidence

- `evidence/six-fold-capacity-replay.csv` has all 552 fixed-capacity rows from the 20% commitment study.
- `evidence/replays.csv` contains audited six-window operating results for the zero-battery plant, forecast controllers, simple strategies, and the rolling truth diagnostics.
- `evidence/plant-oracle.csv` contains the six complete-window zero-storage plant optima from Python Xpress 9.9.0. This uses full retrospective knowledge for commitment and allocation. The battery diagnostics give their fixed controllers the true 12-hour paths (A) or current gap sign (B).
- `evidence/daily-operation.csv`, `stress-weeks.csv` and `break-even.csv` give the data for the season chart, seven-day extremes and first-block purchase thresholds.
- `evidence/forecast-value.csv` contains test-window forecast errors or classification accuracy paired with the net value of the one-block replay.
- `evidence/xpress-dispatch-audit.csv` is the archived Xpress audit for the rolling controller. The full-supply school Xpress licence is loaded in the process for the separately computed plant oracle.

## Local reproduction

Compile the provided snapshot with `tectonic tier2b-report-preview.tex`. The original data for recomputation remain in the adjacent FinalProject study directories. Use the existing Python environment with NumPy, pandas, SciPy, Numba, matplotlib and Xpress installed.

1. Run `build_evidence.py` to replay the comparisons under the archived 20% setup.
2. Run `build_evidence.py oracle` to recompute the six Xpress oracle rows.
3. Copy the 20% study's `six-fold-capacity-replay.csv` into `evidence/`, then run `make_exhibits.py` and compile.

When inserting the chapter into the group report, copy `tier2.tex` into `sections/` and copy the new figures and evidence TeX files under the corresponding project paths. The current v7.1 Tier 1 closing paragraph and Appendix C both cite parts of the earlier 12.5% replay. Label those as separate 12.5% comparisons or reconcile the figures explicitly when revising the combined report.
