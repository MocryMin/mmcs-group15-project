# Tier1 independent research release — 20261103-cu-v1

Agent: `mocry-cleveruser` (member `mocry`, human owner Ran Min / GitHub `MocryMin`). Harness: Clever User (build not exposed). Model: `deepseek-v4.1-flash-1017`. Date: 2026-11-03. Status: **independent first passes plus a controller synthesis; a proposal for group review, not an adopted decision and not a replacement of Baseline 1103.**

This is the second research round in this repository. It was commissioned from a different harness on purpose: the earlier round (`Tier1/public/research_1103/controller/mocry-codex/20261103-v1.1`) was run by `mocry-codex`, and its own release states that no Clever User result was claimed. The project's research request asked for independent first passes and cross-validation, so this round repeats the same question without seeing the earlier answers.

## How independence was protected

- The four researchers each received a byte-identical input bundle: the brief (plus a page-marked text extract), five CSVs, both transcripts, `PROJECT.md`, `TEACHER_ORIGINAL_EXCERPTS.md`, `TEACHER_CLARIFICATIONS.md`, `GAPS.md`, `BASELINE_1103.md`, `RESEARCH_REQUEST.md`, `RESEARCH_RESULT_TEMPLATE.md`. Hashes: `inputs/INPUT_BUNDLE.json` in the workspace copy; the bundle is the question, not the answer.
- Each researcher was forbidden from opening `Tier1/public/research_1103/**` or another package's folder, and had to declare what it did not see in `FIRST_PASS.md`. All four declared no earlier-round or peer material.
- First passes were written, then read by the controller. Nothing was rewritten afterwards.
- **Disclosed limitation:** the controller had already read the earlier round's `README.md` and `EXECUTIVE_SUMMARY_EN.md` during repository exploration, before designing this work. The four first passes are uncontaminated by that; the controller's emphasis is not certified blind, and the comparison in `CROSS_REVIEW_NOTES.md` is explicitly non-blind.

## Contents

| Path | What it is |
|---|---|
| [SYNTHESIS.md](SYNTHESIS.md) | Controller synthesis: minimal instantiable Tier1 interface, conflicts, what could change the recommendation |
| [BASELINE_CANDIDATE_CU.json](BASELINE_CANDIDATE_CU.json) | 30 typed parameter records with units, price bases, evidence strength and status (`baseline` / `decision_required`) |
| [CROSS_REVIEW_NOTES.md](CROSS_REVIEW_NOTES.md) | Recomputed high-impact claims, one arithmetic defect found in a package, and the non-blind comparison with 20261103-v1.1 |
| `packages/R1-market/` | Electricity markets and trading: routes, prices, limits, eligibility (E-01..E-07) |
| `packages/R2-battery/` | Battery catalogue, costs, efficiency, usable window, daily convention (B-01..B-06) |
| `packages/R3-hydrogen/` | Electrolyser and hydrogen: consumption, CAPEX ladder, OPEX, stack replacement, supported value (H-01..H-07) |
| `packages/R4-finance-data/` | Data audit, FX/CPI/deflator, discounting, splits, validation gate (F-01..F-03, D-01..D-03, V-01) |
| `controller-data-audit/` | Controller's own deterministic audit of the five CSVs plus its scripts and outputs |

Each package folder contains `REPORT.md`, `parameters.json`, `sources.json` and `FIRST_PASS.md`. Vendor PDFs and XLSX files that the researchers downloaded are **not** redistributed here; the reports cite public URLs and page locators instead.

## Headline results

- **The brief's battery cost is reproducible:** €0.298 m(2020)/MWh installed for a 2-hour system from the same catalogue the brief cites (+3.5 %).
- **A "2-hour" battery has 1.2 usable hours** at rated power under the 20–80 % SOC rule — a daily-resolution model is a daily energy shifter, not an intraday arbitrage model.
- **Hydrogen's supported £9.5/kg is a contract strike price for 11 named projects**, worth £169.95 per MWh of input electricity; at £2.50/kg the route loses money before CAPEX.
- **Data:** 2,406 common dates in 28 segments, fuel rows reconcile to the total exactly, the two price columns are the same series at different time units, 9 negative-price days — and 107 dates on which every dispatchable fuel is exactly 0 MW, which must be reported as an excluded sensitivity rather than repaired.
- **Three items need a human decision, not more research:** discount rate (7 % is an assumption), electrolyser CAPEX basis (the two rounds differ by ≈1.8× on a common price basis), and a finite hydrogen offtake cap.

## Reproduce

Everything text-based here is reproducible: `controller-data-audit/tools/*.py` regenerates the audit numbers, each package ships its own scripts and source list, and `RELEASE_MANIFEST.json` records SHA-256 for every published file.

## What this release does not claim

Model results, an investment recommendation, or group agreement. No optimisation has been run in this round; no other agent is asserted to have read it. Adopting any parameter here is a recorded group decision, not an implication of publication.
