# Full audit of the five disclosed project datasets

Release `20261104-cu-full-data-audit`, prepared by `mocry-cleveruser` on 4 November 2026.
Independent of the Tier 1 model; read-only on all course inputs. Supersedes the balance
figures in `20261103-cu-verify-repair` (see §15).

## 1. Scope and method

Every dataset the project discloses at repository root is audited here: the five CSVs,
`SOURCE_MANIFEST.json`, `Project_Brief.pdf` and the two transcripts. The Tier 1/Tier 2
working folders are *derived* material and are not audited as disclosure.

Checks performed, all reproducible from `scripts/`:

1. Byte-level inventory: size, SHA-256, encoding, BOM, line endings, row/column counts,
   empty cells, duplicate keys, date formats.
2. Per-series integrity: calendar coverage within 2020-01-01…2026-09-17, zero and negative
   values, non-integer values, distribution, extremes.
3. Cross-file identities: fuel sum vs total, price-per-MW-day vs price-per-MWh, wind-farm
   vs fuel-table wind, and the generation-versus-demand balance.
4. Reconciliation of every declared value in `SOURCE_MANIFEST.json` against the files.
5. Re-derivation of the supply–demand statistic on four definitions and two data versions,
   on two date panels.
6. Upstream spot checks against live Elexon BMRS `AGPT` and `FUELHH` (about 260 queries):
   fidelity of ordinary days, the two zero-value defect families, the 30 absent dates, and
   a 60-date random sample used to test what the balance residual actually measures.

## 2. What is sound

| Check | Result |
|---|---|
| `SOURCE_MANIFEST.json` bytes, SHA-256, row counts, column names, first/last dates | **all 7 files match exactly** (see `results/manifest_check.csv`) |
| Encoding | UTF-8, no BOM, CRLF throughout, trailing newline present |
| Empty cells / ragged rows | 0 / 0 |
| Duplicate `(date, fuel)` or duplicate date keys | 0 in all five files |
| Malformed dates, non-midnight timestamps, duplicate demand records | 0 |
| Negative generation or negative demand | 0 |
| Σ(11 fuel categories) = `total_MW` | exact on **2,422 / 2,422** dates (max deviation 0) |
| `avg_price_£_per_MW_day` = 24 × `avg_price_£_per_MWh` | exact on **2,421 / 2,421** non-zero-price dates |
| Coal phase-out behaviour | last non-zero hard-coal day 2024-09-30, none after — consistent with the GB phase-out |
| Negative-price days vs defect days | 9 negative and 1 zero-price day, **none** falls on a defect date |

The manifest is therefore an accurate description of the files, and the two internal
identities hold exactly. Everything below concerns coverage, value defects, and semantic
definitions — not corruption of the shipped bytes.

## 3. F1 — Coverage is unequal and date-aligned only by accident (severity: medium)

Window 2020-01-01…2026-09-17 is 2,452 calendar days.

| File | Dates | Missing | Notes |
|---|---:|---:|---|
| `daily_generation_by_fuel.csv` | 2,422 | 30 | 9 in Nov 2020; 5 in Feb 2021; 6 in Jan 2022; 6 in Apr 2022; 2 in Sep 2022; 1 each Jun 2021 and Jun 2022 |
| `daily_generation_total.csv` | 2,422 | 30 | identical date set to the fuel table |
| `daily_market_index_price.csv` | 2,422 | 30 | **different set**: 16 generation dates have no price, and 16 price dates have no generation |
| `daily_demand.csv` | 2,451 | 1 | only 2020-07-07 is absent; the other 30 absent generation dates **do** have demand |
| `wind_farm_generation.csv` | 2,453 | 0 | covers all 30 generation gaps plus 2026-09-18 |

Consequences any merge must disclose:

* generation ∩ demand = 2,421 dates; adding price cuts the panel to **2,406** (98.1 %).
* The 16 price-only dates are 2021-06-14, six in Jan 2022, six in Apr 2022, 2022-06-22,
  2022-09-17 and 2022-09-23 (`results/defect_dates.csv`, classes
  `no_generation_rows_price_present` / `no_price_row`).
* Wind-farm-only dates are not usable currency: they have demand and wind but no generation
  or price, so they cannot enter a balance.

**Action:** state the panel in the report ("2,406 days with price; 2,421 without"), never
quote a "daily" statistic without it. An inner join on all five files silently deletes
46 days of a 2,452-day window and, more importantly, 100 % of the 2022-01/2022-04 gaps.

## 4. F2 — 107 dates with seven categories forced to zero (severity: high; already repaired)

Exactly 107 dates carry identical zeros for Biomass, Fossil Gas, Fossil Hard coal, Hydro
Pumped Storage, Hydro Run-of-river, Nuclear and Other, while Wind Onshore/Offshore and Solar
retain values. The total inherits the understatement because it is the sum of the categories.

Verified here:

* the zero-day sets of the five always-on categories are **identical** and equal, date for
  date, to the `changed_dates` list of the `20261103-v1` repair — the repair covers exactly
  this family and nothing else;
* live `FUELHH` and `AGPT` show positive gas and nuclear generation on every such date
  checked (nine dates re-pulled in the `20261103-cu-verify-repair` check, two `AGPT`
  documents read directly);
* the worst case is 2022-12-12: course total 1,664 MW against 35,123 MW domestic generation
  in live `FUELHH` (37,849 MW including imports).

The repair is arithmetically clean: 107 changed dates, Σ(categories) = total on all 2,422
dates, and I reproduced its published headline exactly (§8).

## 5. F3 — A second, unrepaired zero-value family (severity: high)

**42 dates have `Solar` = 0.0 MW as a daily mean.** An exact national zero cannot occur at
daily resolution — the file's own distribution runs to 5,673 MW with a 5th percentile of
153 MW — and on six of these dates the same date reports 188–2,477 MW of solar upstream
(table below). 41 of these dates lie outside the 107-date repair set
(`results/defect_dates.csv`, class `solar_zero`). Nine further dates have
`Hydro Pumped Storage` = 0 with solar present.

Upstream check: `AGPT` returns no rows for 33 of the 42 dates through the publish-window
endpoint (so neither confirmation nor refutation is possible), but on the nine comparable
dates:

| Date | Course total | Live AGPT | Course − AGPT | Course solar | AGPT solar |
|---|---:|---:|---:|---:|---:|
| 2021-01-01 | 25,644 | 28,794.5 | −3,150.5 | 0 | 188 |
| 2022-01-03 | 24,713 | 27,592.4 | −2,879.4 | 0 | 249 |
| 2024-01-07 | 22,472 | 28,330.6 | −5,858.6 | 0 | 543 |
| 2025-01-08 | 28,845 | 35,505.7 | −6,660.7 | 0 | 266 |
| 2026-01-10 | 25,373 | 32,579.4 | −7,206.4 | 0 | 1,088 |
| 2026-09-17 | 25,490 | 25,868.1 | −378.1 | 0 | 2,477 |
| 2021-03-10 | 22,768 | 22,766.4 | +1.6 | 0 | 0 |
| 2022-06-23 | 24,551 | 24,550.9 | −0.1 | 0 | 0 |
| 2023-01-05 | 11,096 | 11,075.4 | +20.6 | 0 | 212 |

Two readings are supported and they are not exclusive: on six dates the course file is
materially below what the same upstream source now reports (0.4–7.2 GW), and on two dates
the upstream source also reports zero solar (an inherited upstream gap). On 2024-01-07 the
understatement is not confined to solar: gas is 7,938 MW against 13,434 MW in `FUELHH`,
i.e. the day behaves like a partially harvested day rather than a single missing category.

**Action:** extend the repair to this family with the same method (rebuild from `FUELHH`/
`AGPT`, retain course wind), or at minimum exclude the 41 dates from any statistic that
depends on total generation and disclose the exclusion. The current repair README already
flags "at least 19 other dates with partial-interval zeros"; this audit fixes the count at
41 non-overlapping dates and gives the per-date file.

## 6. F4 — One impossible demand value (severity: medium)

`daily_demand.csv`, 2022-08-02, demand = **636 MW**, against 22,000–30,000 MW on every
neighbouring day (monthly August 2022 range 22,437–30,110 MW). No metering convention
produces a 636 MW national daily mean across the GB transmission boundary.

Effect measured on the 2,421-date panel:

* the day's balance becomes **+24,768 MW**, the largest apparent surplus in the whole
  sample; replacing the value with the mean of 2022-08-01 and 2022-08-03 (27,331 MW) turns
  it into −1,927 MW;
* total apparent surplus falls from 32.915 to 32.321 TWh, i.e. **1.8 % of the cumulative
  surplus statistic rests on this one value**;
* any "best day to run the plant" statement drawn from the balance picks this day first.

**Action:** replace with a documented imputation or exclude the date; record the choice.

## 7. F5–F7 — The price file carries less information than it appears to

**F5 (medium).** `avg_price_£_per_MW_day` is exactly 24 × `avg_price_£_per_MWh` on every
non-zero date. The second column is derived, not independent, and the implied hours are 24
on all 2,421 dates — no 23- or 25-hour signature on the DST-change days. A model that
consumes both columns as separate inputs is double-counting the same series, and a
"£/MW-day" revenue stream is a 24-hour convention rather than a metered quantity.

**F6 (medium).** The price set differs from the generation set by 16 dates in each direction
(§3). Statistically this changes little, but a model calibrated on price and validated on
generation — or the reverse — is silently fitting different samples.

**F7 (low, informational).** Price extremes are mild and plausible: 9 negative daily means
(2020-05-22, 2020-06-28, 2021-05-04, 2023-04-11, 2023-12-26, 2024-01-02, 2025-06-03,
2025-08-05, 2025-09-16), one zero day (2021-04-27), maximum 333.83 £/MWh (2021-09-09), and
**no daily mean above 1,000 £/MWh anywhere**. Annual means: 16.1 (2020), 54.7 (2021), 95.2
(2022), 45.4 (2023), 35.0 (2024), 39.6 (2025), 50.4 (2026 to September). For a
daily-mean-index project the price series cannot by itself represent scarcity events, which
are intra-day; that belongs in the report's limitations, not in the calibration.

## 8. F8 — The supply–demand balance is a convention, not a physical quantity (severity: high)

This is the most consequential finding. The balance is defined as daily mean
(generation − demand) × 24 h, summed over days.

**8.1 The published numbers are reproducible.** With supply defined as national generation
*plus* the simulated wind farm, the `20261103-v1` README states 160.30 → 116.96 TWh deficit
and 40.63 → 41.89 TWh surplus. I reproduce 160.301 → 116.958 and 40.626 → 41.886 TWh on the
same 2,406 dates. The arithmetic is correct.

**8.2 The definition moves the headline by more than any model decision.** Four definitions,
two data versions, two panels (`results/balance_definitions.csv`):

| Panel | Supply definition | Version | Deficit TWh | Surplus TWh | Mean gap MW |
|---|---|---|---:|---:|---:|
| 2,406 | national generation | course | 176.81 | 32.82 | −2,494 |
| 2,406 | national generation | repaired | 133.21 | 33.82 | −1,721 |
| 2,406 | generation + wind farm | course | 160.30 | 40.63 | −2,073 |
| 2,406 | generation + wind farm | repaired | 116.96 | 41.89 | −1,300 |
| 2,421 | national generation | course | 178.88 | 32.92 | −2,512 |
| 2,421 | national generation | repaired | 135.28 | 33.92 | −1,745 |
| 2,421 | generation + wind farm | course | 162.16 | 40.74 | −2,090 |
| 2,421 | generation + wind farm | repaired | 118.82 | 42.00 | −1,322 |

The farm convention alone moves the deficit by 16.5 TWh and the surplus by 7.8 TWh. That is
24.3 TWh — exactly the farm's own energy over the same 2,406 dates (mean 421.08 MW ×
57,744 h). A 0.42 GW asset cannot create 24 TWh of system surplus; the statistic is
dominated by which series are put on which side of the minus sign.

**8.3 The residual is not explained by trade.** On a 60-date random sample of clean days
(neither defect family, no missing dates), the gap averages **−2,237 MW** (s.d. 3,565;
73 % of days negative). Live `FUELHH` net interconnector imports on the same dates average
**+2,854 MW** (s.d. 2,005). If generation and demand shared one boundary and differed only by
trade, the gap would be −(net imports). It is not:

* correlation(gap, net imports) = **−0.374**; least-squares slope **−0.665**; **R² = 0.14**
  (`results/sample_regression.json`);
* the residual after adding back net imports has mean +617 MW but s.d. 3,373 MW, and
  correlates **+0.335 with solar** and **+0.294 with national wind**.

That pattern — a large dispersion plus a positive dependence on solar and wind — is the
signature of two series that count embedded renewable output differently, not of a physical
energy balance. Worked examples: 2024-06-01 has imports of 4,781 MW yet a gap of −8,940 MW;
2026-08-11 has imports of 4,979 MW and a gap of **+524 MW**.

**8.4 What follows.**

1. `generation − demand` must not be described as "surplus electricity available for
   electrolysis" or "unmet demand". Call it what it is: the residual of two series whose
   boundaries have not been reconciled, and say so in the report.
2. If a physical surplus is needed, define it explicitly and defend the definition —
   national balance with trade and embedded generation reconciled; or price-based scarcity
   (daily mean ≤ 0, or below a stated marginal cost); or curtailment. Each gives a different
   answer, and the current metric cannot arbitrate between them.
3. Report both conventions (with and without the wind farm) at least once, with the 24 TWh
   difference stated. It is a one-line sentence that protects the whole recommendation.
4. The annual shape survives anything: deficit 178.88 TWh and surplus 32.92 TWh over 2,421
   days, with 24.5 % of days positive (25.6 % after repair). What does *not* survive is any
   claim that a particular year or day was "the tightest", because it depends on the defect
   families and on this convention.

## 9. F9 — The wind-farm series is one simulated asset (severity: medium)

`Project.md` describes it as a "specified simulated baseline wind-farm profile" and an
"historical-weather simulation", so it is a client asset, not a national series. The data
confirm the scale: mean 422 MW, maximum 1,125 MW, minimum 0, twelve significant decimals
(derived, not metered), correlation 0.69 with national wind, and a ratio to national wind
varying 3–17 % by month — not a fixed share, not a national proxy.

Two consequences: (i) adding it to national generation is a counterfactual for a *new* asset
and must be labelled as such — which `baseline_1103` already does, and this audit supports
keeping that label; (ii) 10 dates report exactly 0 MW for a whole day (2020-06-16,
2020-09-19, 2021-07-30, 2021-09-08, 2022-09-19, 2023-09-08, 2023-11-16, 2024-09-23,
2025-10-13/14), which is implausible for a wind farm and should be treated as missing, not
calm. The last value in the file (2026-09-18) has no counterpart anywhere else.

## 10. F10 — The sample contains a structural break; 2026 is a different system

Mean output by category (MW) on the dates present:

| Category | 2020 | 2023 | 2026 (to 17 Sep) |
|---|---:|---:|---:|
| Fossil Gas | 10,752 | 9,382 | 7,028 |
| Nuclear | 5,381 | 4,076 | 3,420 |
| Wind Offshore | 3,080 | 2,971 | 5,463 |
| Wind Onshore | 2,976 | 2,953 | 4,007 |
| Solar | 1,286 | 1,322 | 2,778 |
| Fossil Hard coal | 499 | 300 | 0 |

Solar doubles and offshore wind rises by 84 % inside the sample; nuclear and gas fall by a
third. A single average capacity factor, a single price level, or a single "typical year"
calibrated on 2020–2026 averages is therefore not defensible, and the 2026 slice is nine
months, not a year. Note also that `Fossil Oil` is 0 on all 2,422 dates — a dead column,
harmless in a sum, degenerate if used as a decision category.

## 11. F11 — Fidelity to the public upstream is good but not exact

On 50 random clean dates from 2022 onward, the course total differs from live `AGPT` by
**−1.20 % on average** (mean absolute 1.31 %, range −9.21 % to +1.73 %). That is the
signature of a settlement-day or midnight-snapshot extraction rather than a different
source, and matches the `20261103-v1` replay claim (2,335 of 2,422 dates reproduce exactly).
Two caveats: one sampled date (2026-06-27) is 9.2 % low unexplained, and course wind minus
`FUELHH` wind is −214 MW on average with s.d. 2,582 MW, so `FUELHH` is not a valid ground
truth for the wind categories.

The 30 absent dates are recoverable in principle: live `FUELHH` returns complete days for
2022-01-27 (33,733 MW) and 2020-11-01 (25,638 MW), while `AGPT` returns nothing for those
dates through the publish-window endpoint. Extending the repair to them is a
data-availability decision, not a modelling one.

## 12. F12 — Annual decomposition after the repair (2,421-date panel)

| Year | Days | Net TWh (course → repaired) | Deficit TWh | Surplus TWh |
|---|---:|---|---:|---:|
| 2020 | 356 | −5.99 → −5.99 | 12.33 | 6.34 |
| 2021 | 359 | −10.87 → −10.87 | 16.05 | 5.18 |
| 2022 | 350 | −25.41 → −7.53 | 32.06 → 14.40 | 6.65 → 6.87 |
| 2023 | 365 | −35.48 → −27.66 | 37.74 → 30.04 | 2.26 → 2.38 |
| 2024 | 366 | −42.73 → −37.77 | 44.99 → 40.16 | 2.26 → 2.39 |
| 2025 | 365 | −12.51 → −7.27 | 18.51 → 13.50 | 6.01 → 6.23 |
| 2026 | 260 | −12.98 → −4.27 | 17.20 → 8.81 | 4.22 → 4.53 |

Deficit-type statements are highly repair-sensitive (−43.6 TWh overall: −55 % in 2022,
−20 % in 2023, −11 % in 2024, −27 % in 2025, −49 % in 2026); surplus-type statements move by
only +3 %. Combined with F8, the defensible
reading is: *surplus*-adjacent conclusions are robust to the data repair, *deficit/tightness*
conclusions are not, and neither is a physical quantity until the boundary is reconciled.

## 13. Actions for Tier 1 / Tier 2 and the ten-page report

Priority order, all cheap:

1. **Never present generation − demand as available surplus** without naming the boundary
   (F8). One sentence plus one sensitivity row protects everything downstream.
2. **Repair or exclude the 41 solar-zero dates** (F3). On the six verifiable dates the
   understatement is 0.4–7.2 GW per day, which is one to two orders of magnitude larger than
   the plant.
3. **Fix 2022-08-02** (F4); it is the first day any surplus ranking will surface.
4. **Quote the panel** in every table (2,406 or 2,421 days) (F1).
5. **Do not treat the two price columns as independent inputs**, and do not interpret
   £/MW-day as a metered revenue (F5).
6. **State the 2020–2026 break** and avoid a single blended capacity factor or price level
   (F10); if the model spans years, show per-year results.
7. **Label the wind farm as a counterfactual addition** and disclose the 24 TWh convention
   effect when using it (F9, F8.2).
8. Keep the repair as the primary generation input, but cite that it covers 107 of at least
   178 affected dates (107 seven-category-zero + 41 further zero-solar + 30 absent, disjoint
   families).

## 14. Limits — what this audit does not establish

* The exact provenance of the generation extract is not proven. The published `AGPT` replay
  in `20261103-v1` (2,335/2,422 exact dates) plus my −1.2 % mean fidelity is consistent with
  a compliant extraction, but the original query timestamps and the 2026 revision remain
  unknown, and I did not obtain the 2020–2022 `AGPT` history (the API returns no rows for
  those publish windows).
* The demand series' definition is inferred, not read from a source document. The tests in
  F8.3 exclude a series that includes solar at the same boundary as the generation table;
  they do not identify the exact Elexon/NESO dataset. Historical half-hourly demand and
  interconnector data were not retrievable from the open endpoints used here
  (`INDO`/`ITSDO` retain only the current period; the demand endpoint returns only initial
  outturns).
* The 33 solar-zero dates for which `AGPT` returns no rows could be either inherited
  upstream gaps or course-side losses; the publish-window endpoint does not settle it.
* No intraday data is disclosed, so every statement here is about daily means. Nothing in
  this audit validates an hourly dispatch, and daily-mean aggregation is itself an
  optimistic assumption for storage and electrolysis value (the launch recording makes the
  same point).

## 15. Files and versioning

```
README.md                              this report
results/coverage.csv                   per-file coverage and gaps
results/identities.csv                 identity checks and outcomes
results/manifest_check.csv             declared vs actual, all seven files
results/balance_definitions.csv        balance on four definitions x two versions x two panels
results/balance_panel_by_year.csv      annual decomposition on the 2,421-date panel
results/gap_by_year.csv                annual decomposition on the 2,406-date panel
results/defect_dates.csv               216 date-level rows across 10 defect classes
results/upstream_sample.csv            60-date random sample with AGPT fidelity and FUELHH trade
results/all_data_audit.json            full inventory, series statistics, identity results
results/all_data_audit2.json           zero-day structure, wind-farm comparison, price profile
results/agpt_defect_family.json        per-date AGPT comparison for the solar-zero family
results/sample_regression.json         boundary test summary and sample rows
results/trade_boundary_test.json       ten extreme days with interconnector detail
results/upstream_zero_fill.json        upstream values for four zero-solar days and two absent days
results/balance_panel.json             panel definitions, price coverage, outlier effect
scripts/*.py                           nine scripts; standard library only
```

Reproduction: run each script from the repository root with the project interpreter, e.g.
`python -X utf8 results/../scripts/audit_all_project_data.py . audit.json`. The upstream
scripts need outbound HTTPS to `data.elexon.co.uk`; results depend on the state of the
upstream revisions and are dated accordingly.

**Versioning.** This note supersedes the balance paragraph of
`20261103-cu-verify-repair/README.md` and of `20261103-v1/README.md` only in interpretation:
their arithmetic (160.30 → 116.96 TWh, 40.63 → 41.89 TWh) is reproduced exactly here, but
the note now records that (a) the statistic includes a 0.42 GW client asset on the national
side, a convention worth 24 TWh, and (b) the residual itself is not a physical surplus.
Nothing in the 107-date repair is withdrawn; its scope limit (107 dates, no demand or price
work) is confirmed.
