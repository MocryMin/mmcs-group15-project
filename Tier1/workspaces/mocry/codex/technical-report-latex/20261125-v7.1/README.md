# Project report candidate v7.1

25 November 2026 · Group 15

[Report PDF](report.pdf) · [LaTeX source](report-source.zip) · [Xpress and Tier 1 evidence](tier1-v7.1-review-evidence.zip) · [Checksums](SHA256SUMS.txt)

The report uses the brief's 20% minimum load for the six-module appraisal and its price sweep. The 12.5% product floor remains a separate sensitivity. The £2.50/kg low-price case comes from the project launch example. For the six-module case, the same Xpress dispatch now reconciles physical surplus, generation left unsold at negative prices, and generation diverted from sales. The support sensitivity compares the estimated renewable-surplus share with the share needed to break even. The solver table shows separate upper bounds for the selected and the competing capacities. The four-hour Tier 2B table now includes the existing 11-block replay.

Available summaries include the [four-day price sweep](four-day-price-sweep.csv), [electricity input split](electricity-input-split.csv) and [11-block replay](eleven-block-replay.csv). The evidence ZIP carries the earlier Xpress schedules and logs, the additional calculations, the equipment configuration and a file-level manifest. The underlying half-hour panel is identified by hash and by its path in the earlier input archive. Extract report-source.zip and compile report.tex with Tectonic.
