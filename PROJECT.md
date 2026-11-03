# MMCS final project — investment and flexibility

Course: Methodology, Modelling and Consulting Skills, academic year 2026/27. This repository is the Group 15 collaboration space.

## Client and question

Act as technical consultants to a hypothetical Scottish renewable-energy investment consortium. Assess the supplied starting infrastructure, recommend battery/electrolyser investment and explain how to operate the assets, what value is added, when investment pays back and which assumptions change the recommendation.

The supplied generation, demand and prices form a constructed system. They are not observations of actual Scottish network curtailment. Model choices need an explicit rationale and validation; there is no single prescribed objective function.

Read the original [Project_Brief.pdf](Project_Brief.pdf). Its six pages cover client context/data, mandatory Tier1, the two Tier2 routes, client expectations and reference technology parameters.

The complete recording transcript is shared as [Project_Launch_Transcript.txt](Project_Launch_Transcript.txt), copied from the original TXT export. [Project_Launch_Transcript_Timed.txt](Project_Launch_Transcript_Timed.txt) is the complete timestamped rendering made from the companion VTT. Both represent the same recording, not independent evidence. The transcript has not been checked against audio; names, numbers and wording may contain automatic-transcription errors. The class date is associated with 26 October 2026 from context, not independently established from the export metadata. Selected exact segments and our interpretation are linked from the Tier1 package.

## Work and outputs

- Implement the main optimisation in Python using Xpress.
- Complete Tier1: assess additional battery and/or electrolyser capacity given the existing generation.
- Select one extension: Tier2A (generation investment/portfolio) or Tier2B (strategy and operation through time). The extension route is not yet adopted in this repository.
- Produce a technical report. The project-launch explanation sets a ten-page limit; treatment of covers/references/appendices needs confirmation.
- Prepare a business pitch for investors. The launch explanation explicitly excludes mathematical formulations and code snippets from the pitch. One or multiple speakers are allowed.
- Compare against simpler/no-investment alternatives, validate results and explain sensitivity and business consequences.

Recorded course schedule: report 27 November 2026 at 10:00 Europe/London (GMT); presentation 30 November 2026, group slot not yet recorded here. These dates were last checked against the course on 30 October, not newly rechecked for this repository upload. A separate detailed marking grid and final code-upload instructions are not included in the supplied brief.

## Original inputs at the repository root

| File | Content | Role |
|---|---|---|
| [daily_generation_by_fuel.csv](daily_generation_by_fuel.csv) | Daily `MW` by fuel/technology | Generation composition and reconciliation |
| [daily_generation_total.csv](daily_generation_total.csv) | Daily `total_MW` | Aggregate of the fuel-level series; do not add the fuel rows again |
| [daily_demand.csv](daily_demand.csv) | Dated `demand` series | Constructed-system demand; lecturer describes UK scale |
| [wind_farm_generation.csv](wind_farm_generation.csv) | Daily `wind_farm_MW` | Specified simulated baseline wind-farm profile |
| [daily_market_index_price.csv](daily_market_index_price.csv) | Daily prices in GBP/MWh and GBP/MW-day | Wholesale-value inputs; not automatically a full import/export tariff |

The archived versions run from 2020 into September 2026, not to the date of this repository update. The independent farm is a historical-weather simulation, not a supplied forecast of future calendar years. The exact inventory, coverage, file sizes and SHA-256 hashes are in [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json). Originals are copied byte for byte; no data cleaning has been applied to them.

All supplied series are daily; the fuel table has several technology rows per day, not intraday readings. Confirm the interpretation of the power fields before converting them to daily MWh. Keep raw files unchanged; date intersections, exclusions and transformed inputs belong in separately published processing artifacts with an adjustment log.

## Current Tier1 proposal

Start at [Tier1/public/baseline_1103/INDEX.md](Tier1/public/baseline_1103/INDEX.md).

Baseline 1103 treats total generation plus the specified independent wind profile as a fixed starting combination. This addition is a modelling connection convention, not a claim that the teacher explicitly identified a particular facility inside/outside the national total. It compares A (free economic allocation) with B (current-generation supply priority), maximises scheme net profit/net benefit and reports the improvement against each regime's matching no-investment comparator.

Teacher wording, reported discussions, our interpretations and our own assumptions are labelled separately. Research is requested on electricity markets, batteries, electrolysers/hydrogen and miscellaneous data/financial/implementation issues. Any member may challenge the proposal or submit independent research through the agent protocol. Requested external-agent research has not been dispatched by this publication.
