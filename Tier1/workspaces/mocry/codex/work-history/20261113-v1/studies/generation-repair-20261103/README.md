# Tier 1 generation data audit and 107-day repair

Release 20261103-v1, prepared by `mocry-codex` on 3 November 2026. This is a proposed comparison input for Tier 1. The group can use the original inputs alongside this candidate.

## What the source replay establishes

- The course fuel table contains 107 dates on which all eight categories other than wind and solar are zero. The NESO historical mix and Elexon FUELHH show positive daily gas and nuclear generation on every one of those dates. The course total inherits the zeros because it sums the 11 fuel categories.
- Replaying Elexon AGPT using UTC midnight boundaries, with each full query spanning 366 elapsed days and the next starting 367 days after the previous start, reproduces all 2,422 course date keys and all 11 values on 2,335 dates. All 2,162 rows dated 2020–2025 match. All seven original query-end values reproduce as midnight snapshots. The 87 differences span 31 May–25 August 2026. The original extraction timestamp and 2026 data revision remain unknown.
- Current AGPT reproduces the simultaneous zeros on 81 dates in 2022–2025. At 12:00–12:30 UTC on 1 January 2023, the published AGPT document records zero nuclear generation, while the Elexon B1610 settlement records show 318.400 and 247.816 MWh for the two Torness units. On the remaining 26 dates in 2026, current AGPT has positive daily gas and nuclear generation. The exact fault behind the zeros has not been identified.
- The Met Office documents the December 2022 cold spell during the longest zero run. NESO recorded substantial gas and nuclear generation during it. The closure of Britain's last coal-fired power station explains later hard-coal zeros on their own.

Sources are linked in the [107-date provenance trace](generation_source_trace.json), including the official AGPT, FUELHH, B1610, NESO and weather evidence. The [repair audit](generation_repair_audit.json) contains the seven replay queries and the underlying comparison results.

## Repair method

| Dates | Count | Replacement |
|---|---:|---|
| 2022–2025 | 81 | Rebuild the eight affected categories from Elexon FUELHH half-hour outturn and retain the course wind and solar values. For 5 January 2023, replace the three renewable midnight values with full-day AGPT averages. |
| 2026, full AGPT coverage | 23 | Use the current AGPT daily values for all 11 categories after checking that all 48 half-hours are present and their rounded means reproduce those daily values. |
| 2026, incomplete AGPT coverage | 3 | Use 48 FUELHH intervals for the eight affected categories and retain course wind and solar. AGPT contains 45, 38 and 35 intervals on 13, 19 and 26 July, respectively. |

For FUELHH, use UTC days, sum CCGT and OCGT for gas, and count only positive pumped-storage output in each half-hour. Use the corresponding biomass, coal, oil, non-pumped hydro, nuclear and other categories. Exclude interconnectors. Round the daily means to integer MW and then sum the 11 fuel values. On 11 March 2025, three FUELHH intervals required linear interpolation between 10:00 and 12:00 UTC. The audit includes the underlying readings and contemporaneous NESO gas and nuclear cross-check.

On 58 complete control dates from the affected era, the mean absolute difference between the FUELHH-based daily eight-category sum and the course sum was 50.4 MW, or 0.29% on a mean absolute relative basis. The 95th percentile of the absolute difference was 141 MW. These are observed cross-source differences on control dates.

## Files and reproducibility

- [Repaired fuel table](daily_generation_by_fuel.csv) and [repaired total table](daily_generation_total.csv) preserve the course schemas and all 2,422 date keys. Values change on exactly 107 dates.
- [Repair audit](generation_repair_audit.json) records the original and replacement values, interval coverage, validation dates, query links and checksums. [Source trace](generation_source_trace.json) records the independent evidence for flagging the dates.
- Run `python Tier1/public/data_quality/generation_repair/20261103-v1/verify_repair.py` from the repository root. The script reconstructs the CSVs in memory from the pinned course files and the published patch, checks the totals and verifies the shipped bytes. The audit lists the original public queries for anyone checking the upstream values.

Across 2,406 common course dates, with supply defined as course generation plus the separate wind farm, the cumulative daily deficit changes from 160.30 to 116.96 TWh and surplus from 40.63 to 41.89 TWh. These are project supply–demand comparisons using daily mean MW times 24 hours.

The repair covers the 107 simultaneous-zero dates. The audit records at least 19 other dates with partial-interval zeros, six other midnight snapshots, 61 other 2026 AGPT differences and the 31 dates absent from the course file. Demand, market prices, the independent wind-farm series and model configuration are outside this release.
