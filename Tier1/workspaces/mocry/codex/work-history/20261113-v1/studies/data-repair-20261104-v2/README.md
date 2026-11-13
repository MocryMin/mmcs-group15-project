# Project data repair 20261104-v2

Prepared by Ran Min's `mocry-codex` agent on 4 November 2026. This release rebuilds the five project CSVs on a shared UTC calendar from 1 January 2020 to 17 September 2026, with **2,452 days per series**. The root files remain the archived course inputs. The datasets here are the complete repaired alternative for model comparison.

Start with `REPAIR_SUMMARY_ZH.md` for the Chinese summary, `data/` for the five CSVs, `data/cell_audit.csv` for original and replacement values, and `data/date_quality.csv` for the confidence flags. Units and schemas match the course files. Generation and demand are daily mean MW. Energy over a UTC day is daily mean MW times 24 h. Prices remain nominal historical GBP/MWh. Price correction changes the economic scale, so model comparisons must use a single stated price version.

## Issues, sources and repairs

Counts overlap. `REPAIR_AUDIT.json` lists every affected date under its issue type.

| Issue in the course inputs or upstream records | Extent | Repair and source |
|---|---:|---|
| Eight non-wind/non-solar fuel categories all recorded as zero | 107 course dates | Use complete current AGPT where available. Reconstruct the remaining affected categories from contemporaneous [Elexon FUELHH](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH), an observed fuel-outturn series with a related aggregation boundary. |
| Solar daily mean recorded as zero | 42 course dates | Use complete [AGPT](https://bmrs.elexon.co.uk/api-documentation/endpoint/generation/actual/per-type) half-hours where available, interpolate short gaps, and estimate severe gaps from [NESO embedded solar](https://www.neso.energy/data-portal/historic-demand-data), calibrated against complete AGPT days. |
| Generation query end copied as a midnight snapshot | 7 course dates | Query a complete UTC day, rebuild the affected categories and recompute their total. One of these dates, 5 January 2023, also belongs to the 107-date family. |
| Other incomplete or partially zero AGPT days | 264 dates with incomplete current AGPT coverage, including 30 absent dates; 136 current source days have simultaneous zero periods | For at most six missing half-hours, interpolate between valid same-day observations, carrying the nearest observation at an edge. For more severe gaps, use FUELHH for eight categories and calibrated NESO/FUELHH estimates for offshore wind, onshore wind and solar. |
| 2026 course extract differs from the current source | 87 dates previously enumerated | Rebuild from the full daily record. This includes the 61 dates outside the original 107-date patch. |
| Demand query end copied as a midnight record | 350 existing course dates | Requery full UTC days from [Elexon VD demand outturn](https://bmrs.elexon.co.uk/api-documentation/endpoint/demand/outturn/summary). All 349 existing Tuesdays and the final date reproduced exactly as query-end records. |
| Missing or implausibly low demand intervals | 116 days with fewer than 288 API output records; 42 days with records below 10 GW | Keep valid VD records. Fill affected slots from NESO transmission demand plus a locally calibrated VD-to-TSD offset. This reconstructs 153 days. The 636 MW value on 2 August 2022 becomes **28,744 MW** as a daily mean. |
| Price query end copied as a midnight value | 346 existing course dates | Recompute the full UTC-day price from [Elexon MID](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/MID). The old 346 endpoints and the remaining 2,076 daily values reproduce exactly under the original averaging rule. |
| Inactive price-provider records averaged as zero prices | 115,571 zero-volume provider records in the retrieved evidence | Exclude providers with no reported volume. Within a half-hour, weight active providers by volume. Take the equal-duration mean of the half-hour prices over the day. Preserve zero and negative prices when a positive traded volume is reported. |
| Missing generation, demand and price dates | 30 generation dates, 1 demand date, 30 price dates | Restore observed records when available. Missing generation uses the same reconstruction rules. Demand uses calibrated TSD. Short price gaps are interpolated; whole-day or severe price gaps use four nearby observed same-weekday daily prices. There are 35 days in this last price-estimate category. |
| Price unit duplication | Every date | Recompute the second price column as exactly 24 times GBP/MWh. Use one price series in the model. |
| Wind-farm simulation contains zero days and a trailing extra date | 10 zero days; 18 September 2026 lies beyond the joint study window | Retain simulation zeros, which can arise from a turbine model. Restrict the regular calendar to the common declared end date. Source simulation values within the window are preserved. |
| Different statistical boundaries and changing yearly conditions | All five series | Record the constructed-system boundary in the model and show yearly results. Adding the simulated farm to supplied generation is the team's stated scenario. A generation-minus-demand residual does not identify actual historical curtailment or unmet GB demand. |

## How the replacement values are produced

All source requests are made through an isolated, unauthenticated official Playwright MCP process. Five compressed evidence files retain the retrieved public records and URLs. They contain no account credentials.

`repair_data.py` performs the following deterministic calculations.

- Generation starts with AGPT half-hours. Eight-fuel reporting collapses are detected jointly, so ordinary coal, oil and pumped-storage zeros remain valid. Gas maps to CCGT plus OCGT, hydro to non-pumped hydro, and pumped storage counts positive output only. FUELHH itself is checked for simultaneous implausible collapses before use. For short gaps, linear interpolation is used between valid observations.
- A severe renewable-data gap uses a statistical estimate. Solar is scaled to AGPT by year. Onshore and offshore wind use a local two-input fit based on FUELHH wind and NESO embedded wind, using the nearest 60 complete training days in the same year. Every fifth date is held out from fitting.
- VD has a five-minute API output grid. These are interface output records; the output frequency does not certify a five-minute independent measurement. The day is recomputed on that grid. Below-10-GW records and absent records are filled using TSD and the median local VD-minus-TSD difference. For the two days with only one VD observation, nearby complete days supply the offset.
- MID zero-volume entries are inactive records. The corrected price is the daily mean of the active-provider period prices. Real negative prices remain possible. The original price file contains seven midnight-negative dates whose full-day mean is positive; the rebuilt series has two negative daily means.

The older 28,711 MW demand candidate used unadjusted TSD for the 17 bad intervals on 2 August 2022. This release adds the observed local VD-to-TSD offset before filling, resulting in 28,744 MW. Both are reconstruction estimates. The complete upstream series still contains the corrupt 636 MW block.

## Accuracy and model use

`REPAIR_AUDIT.json` contains annual renewable holdout results. Solar mean absolute error ranges from about **42 to 182 MW** across the seven annual tests. Offshore-wind errors range from **453 to 832 MW**, and onshore-wind errors from **363 to 592 MW**. The wind estimates have materially greater uncertainty than the solar estimates.

The separate `IMPUTATION_VALIDATION.json` tests the demand and price rules on complete days. Hiding the first 17 demand slots gives **8.63 MW daily-mean absolute error** over 74 control days. Hiding a complete price day gives **£19.87/MWh mean absolute error** over 77 days. These empirical errors do not bound errors on missing dates.

The five model-input CSVs are complete, while estimates remain explicit. `data/quality.csv` gives a method for every output cell. `data/date_quality.csv` identifies **436 days using estimation or interpolation**, **323 days using cross-source reconstruction**, and **1,929 days meeting the strict no-imputation flag**. These classes overlap. For evaluation, report the full repaired panel and an appropriate quality-filtered sensitivity. Preserve time gaps when filtering a chronological model.

## Reproduce and verify

From the repository root, using Python 3.9+ with timezone data available:

```text
python Tier1/public/data_quality/full_data_repair/20261104-v2/repair_data.py --course-root . --verify
python Tier1/public/data_quality/full_data_repair/20261104-v2/validate_release.py --course-root .
```

The first command rebuilds all eight output CSVs in memory and checks the published bytes. The second independently checks coverage, fuel totals, price identities, the original 107-day and 42-day defect sets, raw-file hashes and all 2,372 price days with complete active-provider coverage. `VALIDATION.json` records the result.

Source collection is separated from rebuilding. `collect_public.py` calls the official Playwright MCP through stdio and accepts a collection JavaScript file and a compressed output path. Its `--mcp-cli` and `--browser-executable` arguments select locally installed programs. Recollection may obtain revised source records. Use the archived evidence to reproduce this exact version.

`MANIFEST.json` records file hashes and release provenance. Future corrections should be published in a new recorded version. This release supersedes the 107-date candidate as the complete alternative data package.
