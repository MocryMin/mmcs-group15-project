# Controller data audit — five supplied CSVs

Author: `mocry-cleveruser` (member `mocry`), 2026-11-03. Method: deterministic script `tools/audit_data.py` reading the five root CSVs byte-for-byte; output `audit/data_audit.json`. Every number below is recomputed here, not inherited from another agent's research. Status: first-pass controller evidence for the data/finance package; not a group decision.

## 1. File shapes as delivered

| File | Columns | Data rows | Distinct dates | Date range |
|---|---|---|---|---|
| `daily_demand.csv` | `recordType,startTime,demand` | 2,451 | 2,451 | 2020-01-01 → 2026-09-17 |
| `daily_generation_by_fuel.csv` | `date,psrType,MW` | 26,642 | 2,422 | 2020-01-01 → 2026-09-17 |
| `daily_generation_total.csv` | `date,total_MW` | 2,422 | 2,422 | 2020-01-01 → 2026-09-17 |
| `daily_market_index_price.csv` | `date,avg_price_£_per_MWh,avg_price_£_per_MW_day` | 2,422 | 2,422 | 2020-01-01 → 2026-09-17 |
| `wind_farm_generation.csv` | `date,wind_farm_MW` | 2,453 | 2,453 | 2020-01-01 → 2026-09-18 |

Notes that a parser must handle:

- Demand uses an Elexon-style export: `recordType` is `VD` on every row (single value, no filtering needed), and the date is an ISO timestamp `2020-01-01T00:00:00Z`, not a bare date.
- The fuel table has 11 `psrType` values: Biomass, Fossil Gas, Fossil Hard coal, Fossil Oil, Hydro Pumped Storage, Hydro Run-of-river and poundage, Nuclear, Other, Solar, Wind Offshore, Wind Onshore. `Fossil Oil` is present with a total of 0 MW over the whole window.
- No duplicate dates in any file; no missing/blank numeric cells encountered while parsing.

## 2. Internal consistency checks

| Check | Result |
|---|---|
| Sum of fuel-level `MW` vs `total_MW`, per date | exact match on all 2,422 shared dates; max absolute difference 0.0 MW; no date unique to either file |
| `avg_price_£_per_MW_day` vs 24 × `avg_price_£_per_MWh` | exact on all 2,422 dates (max absolute difference 0.0) |
| Negative prices | 9 days; minimum −8.465 £/MWh |
| Zero price | 1 day |
| Negative or zero total generation | none |
| Negative wind-farm values | none; maximum 1,125 MW (looks like a capacity cap), mean 424.6 MW |

Consequence: the two price columns are the same information at different time units; use exactly one of them, and nothing in the files distinguishes a "daily average" from a "24-hour mean of half-hourly prices" beyond the naming.

## 3. Coverage, gaps and continuity

- All five files overlap on **2,406 dates**, 2020-01-01 → 2026-09-17.
- Those 2,406 dates form **28 continuous segments**; 46 calendar days inside the overall span are absent because the generation/price files are shorter than demand and wind.
- Longest continuous run: **2022-09-24 → 2026-09-17, 1,455 days**. Earlier years are fragmented (the 2020–2022 segments are mostly short: 188, 103, 12, 4, 1, 2 days …).
- Practical consequence for any storage model: state-of-charge continuity can only be imposed inside a segment; joining across a missing day silently invents a transition. The long 2022–2026 segment is the only one long enough for a serious chronological study; the fragmented earlier period is usable for cross-sectional (independent-day) analysis or as a stress set, but not as one continuous time series.

## 4. Combined-system view used to size the investment question

Definition used for this audit only: `G_t = total_MW + wind_farm_MW` (the independent farm added to the national total, the brief's starting-position convention) and `D_t = demand`; both treated as daily mean MW and multiplied by 24 to obtain MWh. This is a stated modelling convention, not an observed fact.

| Quantity (2,406 common days) | Value |
|---|---|
| Mean daily G / D | 26,016 MW / 28,089 MW |
| Days with G > D | 702 (29.2 %) |
| Total surplus over window | 40.63 TWh (2.7 % of G; 2.5 % of D) |
| Mean annual surplus | ≈ 6.16 TWh per year |
| Largest single-day surplus | 616,303 MWh on 2022-08-02 |
| Surplus valued at that day's wholesale price | £1.687 bn over the whole window, undiscounted and before losses |
| Total shortfall over the same window | 160.3 TWh |

Reading: in this constructed system the treated starting position is **short on most days** — surplus appears on 702 of 2,406 days and totals only 2.7 % of generation. It is also fairly dispersed rather than concentrated in a handful of events (largest day 1.5 % of the six-year surplus, top 10 days 6.1 %, top 50 days 22.3 %), so a daily model's battery/electrolyser value depends on many days while peak-day capacity is driven by the extreme tail. Two data points need explicit handling:

- **2022-08-02**: demand = 636 MW against a median of 27,472 MW and generation ≈ 26,315 MW. A single-day demand value 43× below the median produces the largest "surplus" in the dataset (616,304 MWh, 2.5× the second-largest day) — an almost certain artefact. It moves total surplus by only 1.5 %, but it dominates maximum-day and peak-size statistics. Exclude it with disclosure or keep it as a labelled stress case; it must not silently set the investment scale.
- **2021-09-09**: the highest price day (333.83 £/MWh) sits inside a fragmented early segment, so its value cannot be captured by a chronological battery strategy that needs the preceding day.

## 5. What these data cannot tell us

- Whether `MW` columns are daily means, instantaneous snapshots or 24-hour means of half-hourly values. The audit's MWh conversion assumes constant daily mean; a different convention changes every energy figure by the same factor only if applied uniformly.
- Nothing intraday: a 2-hour battery's real value depends on within-day price shape, which these series do not contain. Any daily model therefore under-states (or arbitrarily re-allocates) battery arbitrage.
- Nothing about network constraints, curtailment events or actual metered counterparties — the brief states the system is constructed.
- The producer's demand aggregation definition; only internal arithmetic consistency is verified here.

## 6. Reproduce

```
python Tier1/workspaces/mocry/cleveruser/tools/audit_data.py
```

Inputs are the five root CSVs unchanged (hashes in `audit/data_audit.json`). The script is standard library only.
