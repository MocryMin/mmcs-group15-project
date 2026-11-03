# First-pass declaration — R4 (miscellaneous data, finance, implementation)

## Identity

- Assigned package: **R4** of `inputs/RESEARCH_REQUEST.md` — gap IDs F-01..F-03, D-01..D-03, V-01 (X-01 not attempted).
- Researcher identity as configured and exposed by the harness: model **deepseek-v4.1-flash-1017**; role researcher; harness **Clever User worker (CU Builder)**, worker name `res-r4-finance-b`, worker id `76e9c24180ee4c8e93f201db478b739d`. Harness build/version: **not exposed** to this worker; no model or harness version was inferred.
- Workspace: `D:\projects\CU projects\course check\MMCS Project\mmcs-group15-project`; output folder `Tier1/workspaces/mocry/cleveruser/firstpass/R4-finance-data/`.
- UTC timestamps: started **2026-11-03T21:05Z**, finished **2026-11-03T21:50Z** (machine clock checked at 2026-11-03T21:42:13Z). The machine clock and the project timeline both read 2026-11-03; the public web content read matches that date, and no mismatch was edited away.

## Independence statement

This first pass was produced **without reading the earlier research round or any peer first pass**. Specifically:

- I did **not** read, list or grep anything under `Tier1/public/research_1103/`.
- I did **not** read or list any other folder under `Tier1/workspaces/mocry/cleveruser/firstpass/`.
- I did **not** read `Tier1/workspaces/mocry/` files created by `mocry-codex` other than the byte-identical input copies in `inputs/`, which the brief explicitly allows.
- I did not browse the repository "for context"; everything project-specific came from `inputs/`.
- No peer or earlier-round value, parameter or conclusion is knowingly reproduced below. If any number here coincides with an earlier round's number, that is coincidence within the same primary data.

I have seen the following peer-adjacent material and no more: the contents of `inputs/` (`PROJECT.md`, `brief_extracted_text.md`, `TEACHER_ORIGINAL_EXCERPTS.md`, `TEACHER_CLARIFICATIONS.md`, `GAPS.md`, `BASELINE_1103.md`, `RESEARCH_REQUEST.md`, `RESEARCH_RESULT_TEMPLATE.md`, `SOURCE_MANIFEST.json`, `INPUT_BUNDLE.json`, the two transcript files, and the five CSVs). `SOURCE_MANIFEST.json` records hashes and row counts published by the input packager; I used them only as a checksum cross-check after computing my own audit, and every headline number in the report is my own computation from the files.

## Work actually done

1. Independent audit of the five CSVs from the raw files (`audit_inputs.py` → `audit_results.json`, `audit_summary.txt`): hashes, byte and row counts, duplicate dates, per-file coverage, pairwise date differences, common-date intersection, continuous segments and gaps, fuel-vs-total reconciliation, price-column identity, negative/extreme/missing-value screening, implied daily energy and annual context.
2. Derived checks (`derived_checks.py` → `derived_checks.json`): anomaly lists, surplus/deficit energy, discount/annuity/capital-recovery factors, FX and CPI conversions.
3. Data-quality screens S1–S5 with run lengths and an exclusion scenario (`data_quality.py` → `data_quality.json`).
4. Official macro/finance evidence fetched programmatically (`fetch_finance.py` → `finance_evidence.json`): ONS CPI index D7BT and rate D7G7, ECB EUR/GBP daily reference rates.
5. HM Treasury Green Book (2026 edition) and Green Book Discount Rate Review 2026 Terms of Reference read as HTML documents; the discounting passages were located by full-text search and quoted verbatim.

No optimiser was run in this package, so no solver result, gap, runtime or profit figure is claimed. The validation items in REPORT.md §2.7 are requirements.

## Sources tried and not obtained

| target | what happened | effect on the result |
|---|---|---|
| `api.ons.gov.uk/timeseries/d7g7/dataset/mm23/data` | HTTP 403 without a User-Agent, HTTP 404 with one | used the working `www.ons.gov.uk/.../timeseries/<cdid>/mm23/data` JSON endpoint instead; same ONS series, so no loss |
| ONS CDID `Z8VK` (candidate price index) | HTTP 404 | discarded as a wrong identifier, not used |
| ECB Data Portal without a CA bundle | `SSL: CERTIFICATE_VERIFY_FAILED` from the local interpreter | re-fetched with the installed `certifi` bundle; succeeded, no data loss |
| Bank of England IADB CSV endpoint (`SeriesCodes=XUDLER`) | returned an HTML wrapper page, not CSV | abandoned; ECB reference rates used for FX instead |
| Green Book 2020 HTML URL | redirected to the publication landing page (2,523 characters, no chapter text) | used the 2026 edition HTML instead |
| Green Book **supplementary guidance on discounting** (official discount-factor table) | not fetched within the time box | discount factors were computed from DF(t)=1/(1+r)^t in `derived_checks.json`; NOT verified against the official table |
| ONS **GDP deflator** series | not fetched | CPI used as deflator, substitution disclosed in the report |
| Bank of England Bank Rate / risk-free nominal series | not fetched | no nominal-rate cross-check; real-rate framework does not depend on it |
| Green Book Discount Rate Review 2026 findings PDF | identified in search results, not read | the 3.00 % vs 3.5 % conflict between two GOV.UK pages is reported unresolved |

## Files produced in this folder

`REPORT.md`, `parameters.json`, `sources.json`, `FIRST_PASS.md`,
`audit_inputs.py`, `audit_results.json`, `audit_summary.txt`,
`derived_checks.py`, `derived_checks.json`, `data_quality.py`, `data_quality.json`,
`fetch_finance.py`, `finance_evidence.json`,
`probe_sources.py`, `probe_sources2.py`, `check_dates.py`, `inspect_low_days.py`, `print_audit_highlights.py`.

All scripts are read-only with respect to `inputs/`; nothing was rewritten, no file was committed, pushed, or copied into `Tier1/public/**`.
