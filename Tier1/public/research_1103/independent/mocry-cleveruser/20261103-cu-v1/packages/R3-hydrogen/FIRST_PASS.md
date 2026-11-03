# FIRST_PASS declaration — R3 (electrolysers, hydrogen storage and market)

## Identity

- **Worker / agent id**: `res-r3-hydrogen` (`task:cu-independent-r3-hydrogen`).
- **Model as configured**: `deepseek-v4.1-flash-1017`.
- **Harness**: Clever User worker (research role). **Harness build/version: not exposed to me** — recorded as unknown rather than guessed.
- **Platform**: Windows, `cmd.exe`, product interpreter at `C:\研究生\Projects\clever user\.venv\Scripts\pythonw.exe`.
- **Workspace**: `mmcs-group15-project`, output under `Tier1/workspaces/mocry/cleveruser/firstpass/R3-hydrogen/`.

## Timing (harness clock, UTC)

- Session start: **2026-11-03T19:41Z** (first search attempt).
- First successful primary-source read (gov.uk HAR1 page): **2026-11-03T19:52Z**.
- Last evidence read (transport & storage annex Table A2): **2026-11-03T21:36Z**.
- Deliverables written: **2026-11-03T21:40Z** (report) to **21:47Z** (this file).
- Clock note: the harness clock reports 2026-11-03 and the public content observed is consistent with that date. Timestamps are approximate to the minute; several documents were fetched in single batch calls. Where a page displayed its own timestamp (a Google rate-limit page showed `2026-11-03T19:47:12Z`), it agreed with the local clock.

## Package

**R3 only** — H-01 … H-07, informing M-05 / M-09 / M-10. Findings that touch R1 (market interface), R2 (batteries) or R4 (finance/data conventions) are flagged in `REPORT.md` and left to those packages; I have not attempted to close their gaps.

## Independence statement

I did **not** read, list, grep or open:

- anything under `Tier1/public/research_1103/**` (the earlier research round, its syntheses, parameter candidates, review decisions or cross-reviews);
- any other folder under `Tier1/workspaces/mocry/cleveruser/firstpass/**` (other researchers' first passes);
- any `Tier1/workspaces/mocry/` file created by `mocry-codex` other than the byte-identical input copies.

The only project context used was the input bundle provided with the task: `inputs/PROJECT.md`, `inputs/brief_extracted_text.md`, `inputs/TEACHER_ORIGINAL_EXCERPTS.md`, `inputs/TEACHER_CLARIFICATIONS.md`, `inputs/GAPS.md`, `inputs/BASELINE_1103.md`, `inputs/RESEARCH_REQUEST.md`, `inputs/RESEARCH_RESULT_TEMPLATE.md`, plus `RESEARCH_BRIEF.md`.

Consequently I cannot state whether my values agree with the earlier round, and `REPORT.md` section 5 (cross-validation) is deliberately empty rather than filled from memory or inference.

## What was actually done

- Evidence was gathered **only from primary sources**: three ITM Power manufacturer data sheets, one GOV.UK/DESNZ publication page, and two DESNZ technical reports (one PDF plus its spreadsheet annex). One course transcript segment was used, explicitly labelled as weak evidence.
- Public PDFs/XLSX were downloaded into `_work/` solely to extract page-located text and spreadsheet cells. **These third-party files must not be redistributed from this repository**; `sources.json` cites URL plus page/table/cell instead.
- Tooling note for reproducibility: the shared document pipeline (`document_open` on XLSX) failed the 2 MB BEIS annex with a `memory_limit_exceeded` error; the same file parsed cleanly with `openpyxl` in read-only mode. The PDFs extracted normally, and `document_read find`/page reads were used for page-accurate locators.

## Sources tried and failed to obtain

| Target | Reason |
|---|---|
| IEA Global Hydrogen Review 2024 body figures | Report content behind a free-account/download gate; only the landing page and table of contents were reachable. Not cited. |
| IRENA green hydrogen cost-reduction study | Requested early; result not reviewed before the cost question was answered from UK government sources. Treated as unread. |
| HAR2 strike price / project list | URL identified via the gov.uk search API but never opened; no HAR2 claim is made. |
| Firm merchant hydrogen offtake price or volume | No public number found. Government publications do not disclose commercial offtake terms for a hypothetical producer. |
| ITM NEPTUNE 5 MW data sheet | Product page exists; data sheet not read, so the 5 MW module is excluded from the recommended equipment set. |
| General keyword web search (Bing / Brave / Google / DuckDuckGo HTML / Mojeek) | **Systematic sandbox limitation**: HTTP 429 rate limits, CAPTCHA challenges (DuckDuckGo duck challenge, Mojeek ALTCHA, Google `/sorry/`), or empty pages with `readiness_timeout`. The `web_search`/`web_search_batch` tools returned zero usable results for all five queries attempted. Evidence therefore came from the `gov.uk` search API and direct publisher navigation. **Absence of a source in this report is not evidence that it does not exist**; a keyword-searching agent should expect to find more, particularly IEA/IRENA cost data and any commercial hydrogen price index. |

## Honest limitations of this pass

1. **No merchant hydrogen price exists in this report.** The core £9.50/kg is a contracted policy strike price for 11 named HAR1 projects. Any scheme without an LCHA has an assumed revenue line, not an evidenced one. I have said so in the report rather than manufacturing a number.
2. **The central electrolyser CAPEX (£1.5 m/MW_e) is interpolated**, not observed: the BEIS 2020 figure uprated by an assumed ×1.25 for inflation. The two endpoints (£0.85 m list equipment, £3.30 m committed FOAK capital) are sourced.
3. **Two structurally different CAPEX concepts are both in play** (equipment list price vs whole-project committed capital) and the correct choice depends on what the model means by "investment". I have kept them separate and flagged the conflict rather than picking one silently.
4. **Degradation is not evidenced.** The data sheets give beginning-of-life consumption; I use the BEIS stack-replacement schedule as a proxy instead of inventing an annual degradation rate.
5. **Water, reconversion equipment and hydrogen compression beyond plant-gate pressure were not costed.** Each is named as a gap with a bounded fallback rather than a fabricated value.
6. No cross-review of any kind has been performed, and no peer result informed any value here.
