# Tier 1 independent study, report revision

5 November 2026 · Ran Min / mocry-codex · Personal workspace study

[Four-page technical report](report/Tier1_Report.pdf) · [Editable text](report/Tier1_Report.md) · [Comparison with Clever User](COMPARISON.md) · [Cross-check results](crosscheck.json)

The [v1 archive](../20261105-v1/README.md) contains the calculation, inputs and schedules for the reference model. This revision adds a direct test of the second electrolyser module at the 10 t/day limit, a 50 t/day expansion case, and an annual sales-floor test at 99.99% and 100%. The core model and selected reference capacities are unchanged.

The [CU v1 archive](../../../cleveruser/tier1/20261105-v1/README.md) and the Codex v1 archive are the comparison sources. From this directory, run `python -B compare.py` and then `python -B build_report.py` with the dependencies in the v1 README. The comparison script checks all 2,452 common input rows and 18 matched cases. It also independently solves the new cases in FICO Xpress. The report was rendered and checked at four A4 pages.
