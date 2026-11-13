# Ran Min Tier 1 research and iteration history

Publication snapshot: 13 November 2026. This is Ran Min's working research archive, including earlier assumptions, unsuccessful approaches, solver attempts, data, numerical checks and report revisions. It is available for group review; publication does not adopt any model as the group's final submission.

## Current reading order

1. [Half-hour v7 results and reproducibility](studies/tier1-halfhour-20261113-v7/README.md). This is the newest numerical model: all 105,216 half-hours of 2020–2025, four battery products and eight electrolyser products, explicit storage and power limits, battery-to-hydrogen flow, and demand-priority battery discharge under policy B. The daily hydrogen limit remains a daily total.
2. [Latest technical report v4.5](studies/project-report-20261113-v4.5/report/report.pdf). It uses the daily v6 results and the later sensitivity work; it has not yet been updated with half-hour v7. Its Tier 2 chapter remains the older draft, not the completed forecasting experiments archived in Tier 2.
3. [Daily multiproduct v6](studies/tier1-multiproduct-20261110-v6/README.md) and [strengthened daily v5](studies/tier1-strengthened-20261110-v5/README.md) explain the transition from the earlier 10 t/day hydrogen case to explicit stock-flow, researched equipment choices and a broad national-market scenario.
4. [Equipment catalogue v3.1](studies/equipment-research-20261110-v3.1/README.md) and [Tesla and Lazard economics](studies/tesla-lazard-economics-20261110/README.md) separate manufacturer specifications, third-party cost estimates and modelling conventions.
5. [Tier 2B research archive](../../../../../../Tier2/workspaces/mocry/codex/work-history/20261113-v1/README.md) contains the forecasting, feature-engineering, scope checks and maintained GUI application.

## Latest numerical finding

| Policy | Half-hour battery capacity | Electrolyser AC input | Annual incremental profit | Gap to global profit upper bound |
|:--|--:|--:|--:|--:|
| A economic allocation | 0 MWh | 4,251.195 MW | £1,807.615 million | at most £231.49 per year |
| B demand priority | 0 MWh | 1,821.222 MW | £118.378 million | at most £47.59 per year |

These are feasible integer portfolios under the frozen v6 economics: constant hydrogen netback £7.799027/kg (2020 GBP), no grid imports, no hydrogen inventory, no supply-shortfall penalty, and a 1,558.969 t/day broad UK market scenario. That cap is not a client contract. Positive integer battery investment is excluded by the stored numerical upper-bound certificates; the particular electrolyser mix is near-optimal, not claimed uniquely optimal.

Upstream half-hour shapes are anchored to the repaired daily totals. Missing observations remain labelled. The separate simulated wind farm has no observed half-hour profile: flat power within each day is the primary assumption, with a wind-shape-transfer sensitivity. Both give zero battery investment. B's 2023 and 2024 annual increments remain negative despite its positive six-year average. The full-scale computation uses CPU HiGHS; the report's course requirement to use Python/Xpress still needs to be respected in the final submission implementation.

## How the work developed

| Stage | Question and retained evidence |
|:--|:--|
| Initial model and data repair | Independent 2 November study, 3 November controlled research, fuel/demand/solar anomaly tracing, 4 November repair audit, baseline 1104 and price interpretation checks. |
| First candidate reports | Independent Tier 1 study, LaTeX templates, candidate v3, academic v4 and v4.1; revised report v4.2–v4.5 incorporates evidence-linked advice and moves detailed repair/research to appendices. |
| Assumption review and v5 | Audits added restrictions, revises hydrogen market capacity, introduces explicit daily stock flow, battery-to-electrolyser delivery and B battery-priority rules. |
| Equipment research and v6 | Multiple batteries/electrolysers, physical interfaces, cost completeness, Tesla quotations, Lazard/NREL cost boundaries, CU cross-check and integer multiproduct portfolios. |
| Alternatives to batteries | Hydrogen storage and reconversion, pumped storage, conventional/advanced compressed air and other non-battery storage screening. Technology-specific cost boundaries are retained. |
| Economic and volatility experiments | Free-battery capacity/value curve, per-unit arbitrage, demand-gap/price-volatility perturbations, joint optimal portfolios, real high-volatility historical windows and a compressed-air entry envelope. |
| Half-hour v7 | Full chronological half-hour constraints and prices, fixed-day H2 cap, farm-profile sensitivity, physical audits, behavioural tests and independent dual-certificate checks. |

The compressed-air envelope uses an illustrative 50 MW/1.5 GWh cavern-storage scenario with the stated one-third battery installation-cost assumption. It is not a quotation for Hydrostor Goderich. Price-volatility multipliers in the experiments scale deviations from the mean (standard deviation); variance scales by their square. Read each experiment's own transformation, economic basis and equipment universe before comparing thresholds.

## Archive use and preservation

The directory table below covers every included study. Code, data, logs, figures, trial results and checks stay together in their original study folders. Statements such as "not uploaded" inside old reports describe their original completion date; this snapshot publishes those frozen records without rewriting their history. Earlier assumptions are not silently replaced by v7.

[CONTENT_MANIFEST.json](CONTENT_MANIFEST.json) records source-relative paths, sizes, SHA-256 hashes and every scoped exclusion. [release_manifests](release_manifests/) resolves every retained entry from the original distribution ZIPs to exact file bytes. Changed/deleted earlier release entries live in [release_history](release_history/); identical entries point to an existing copy. ZIP containers are not duplicated, and ZIP byte-for-byte recreation is not claimed.

Installed environments, caches, credentials and Git metadata are excluded. Lazard's original report, complete extracted pages and page images remain local because of its redistribution restriction; our economic analysis, parameters, URL and original hash are retained. The previously local-only chat handoffs are not published. Existing public course materials and past-report examples remain at their original repository locations.

Use [verify_archive.py](verify_archive.py) to check the published payload and release-entry hashes. [restore_workspace.py](restore_workspace.py) can reconstruct the original course-relative study layout in a new empty directory. Historical scripts can still contain machine-specific paths; the manifests preserve them as evidence, rather than claiming every old entry point is portable without configuration. Newer frozen input packages include their own execution instructions and dependencies. No experiments were retrained for this publication.

## Complete study directory

| Study | Reading entry | Archived files |
|:--|:--|--:|
| baseline-1104 | [Open report](studies/baseline-1104/README.md) | 95 |
| baseline-1104-publication | [Open folder](studies/baseline-1104-publication/) | 184 |
| battery-cost-clarification-20261108 | [Open report](studies/battery-cost-clarification-20261108/README.md) | 2 |
| battery-research-20261110-v2 | [Open folder](studies/battery-research-20261110-v2/) | 10 |
| caes-entry-envelope-20261112 | [Open report](studies/caes-entry-envelope-20261112/REPORT_ZH.md) | 37 |
| data-repair-20261104-v2 | [Open report](studies/data-repair-20261104-v2/README.md) | 34 |
| equipment-cu-crosscheck-20261110 | [Open report](studies/equipment-cu-crosscheck-20261110/REVIEW_ZH.md) | 19 |
| equipment-research-20261110-v3 | [Open report](studies/equipment-research-20261110-v3/README.md) | 164 |
| equipment-research-20261110-v3.1 | [Open report](studies/equipment-research-20261110-v3.1/README.md) | 188 |
| gb-price-stress-20261112 | [Open report](studies/gb-price-stress-20261112/REPORT_ZH.md) | 19 |
| gb-price-window-replay-20261112 | [Open report](studies/gb-price-window-replay-20261112/REPORT_ZH.md) | 52 |
| generation-repair-20261103 | [Open report](studies/generation-repair-20261103/README.md) | 5 |
| hydrogen-market-research-20261110 | [Open report](studies/hydrogen-market-research-20261110/REPORT_ZH.md) | 12 |
| hydrogen-reconversion-screen-20261111 | [Open report](studies/hydrogen-reconversion-screen-20261111/REPORT_ZH.md) | 4 |
| hydrogen-storage-research-20261111 | [Open report](studies/hydrogen-storage-research-20261111/REPORT_ZH.md) | 15 |
| independent-study-20261102 | [Open report](studies/independent-study-20261102/README.md) | 41 |
| market-obligations-research-20261108 | [Open report](studies/market-obligations-research-20261108/README.md) | 1 |
| nonbattery-storage-research-20261111 | [Open report](studies/nonbattery-storage-research-20261111/REPORT_ZH.md) | 23 |
| price-check-20261104 | [Open folder](studies/price-check-20261104/) | 2 |
| project-report-20261113-v4.2 | [Open report](studies/project-report-20261113-v4.2/README.md) | 22 |
| project-report-20261113-v4.3 | [Open report](studies/project-report-20261113-v4.3/README.md) | 38 |
| project-report-20261113-v4.4 | [Open report](studies/project-report-20261113-v4.4/README.md) | 31 |
| project-report-20261113-v4.5 | [Open report](studies/project-report-20261113-v4.5/README.md) | 27 |
| publication-1103-research-v1 | [Open folder](studies/publication-1103-research-v1/) | 90 |
| research-1103-controlled | [Open folder](studies/research-1103-controlled/) | 116 |
| solar-demand-audit-20261104 | [Open folder](studies/solar-demand-audit-20261104/) | 4 |
| technical-report-latex-20261105 | [Open report](studies/technical-report-latex-20261105/README.md) | 12 |
| technical-report-latex-20261105-v2 | [Open report](studies/technical-report-latex-20261105-v2/README.md) | 14 |
| tesla-lazard-economics-20261110 | [Open report](studies/tesla-lazard-economics-20261110/README.md) | 37 |
| tier1-assumption-audit-20261110 | [Open report](studies/tier1-assumption-audit-20261110/REVIEW_ZH.md) | 1 |
| tier1-candidate-20261107-v3 | [Open report](studies/tier1-candidate-20261107-v3/README.md) | 198 |
| tier1-candidate-20261107-v4-academic | [Open report](studies/tier1-candidate-20261107-v4-academic/README.md) | 205 |
| tier1-candidate-20261107-v4.1-academic | [Open report](studies/tier1-candidate-20261107-v4.1-academic/README.md) | 206 |
| tier1-free-battery-20261111 | [Open report](studies/tier1-free-battery-20261111/README.md) | 69 |
| tier1-halfhour-20261113-v7 | [Open report](studies/tier1-halfhour-20261113-v7/README.md) | 112 |
| tier1-independent-20261105 | [Open report](studies/tier1-independent-20261105/README.md) | 72 |
| tier1-joint-portfolio-20261111 | [Open report](studies/tier1-joint-portfolio-20261111/REPORT_ZH.md) | 206 |
| tier1-multiproduct-20261110-v6 | [Open report](studies/tier1-multiproduct-20261110-v6/README.md) | 74 |
| tier1-strengthened-20261110-v5 | [Open report](studies/tier1-strengthened-20261110-v5/README.md) | 102 |
| tier1-unit-arbitrage-20261111 | [Open report](studies/tier1-unit-arbitrage-20261111/REPORT_ZH.md) | 6 |
| tier1-volatility-20261111 | [Open report](studies/tier1-volatility-20261111/REPORT_ZH.md) | 198 |
| verification | [Open folder](studies/verification/) | 4 |

Recorded payload: 2,790 files; 612.86 MB before Git deduplication. See the manifest for auxiliary provenance and release-history entries.
