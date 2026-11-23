# v6 verification against the v5 findings and the evidence archive

Verifier: `mocry-cleveruser`. Date: 2026-11-23.
Target: `Tier1/workspaces/mocry/codex/technical-report-latex/20261123-v6/report.pdf`
sha256 `769b89e4100b33ee6de555530fd147f6b90ff8b34af2832bc59743a71a442db8`, 136,111 bytes, 15 PDF pages (body 1–6, R1, A1–A6). Pinned to `2f02e3e`.
Evidence: `tier1-site-evidence-v6.zip`, sha256 `f4c0e6e517df44dc6edbb8c7eb7453257558839ce1701e63d9bd009055b50440`, 190 files, `MANIFEST.json` with per-file sha256, report sha matches. Checksums agree with `SHA256SUMS.txt`.
Standard: `STANDARD.md` + `ADDENDUM_1_OFFICIAL_RUBRIC.md` + `ADDENDUM_2_PAGE_RULE.md` (owner: 10 pages = body only; abstract/contents/appendices excluded).
Method: read all 15 pages; rendered and viewed pages 1, 5, 6, 7, 8; ran `v6_checks.py`, which reads the ZIP directly and compares 79 printed values with CSV/JSON records. **79 checks, 0 failures.**

## Verdict

All two P0 and nine P1 findings from the v5 review are closed or materially reduced. The remaining issues are P2-level documentation/labelling points. **Revised rubric score: 78/100 (A3 across all seven descriptors; the weighted sum lands at the A3/A2 boundary because Presentation carries weight 2). Band 74–82, non-official.** Up from 73.

| Dimension (weight) | Anchor | Fraction | Basis |
|:--|:--|--:|:--|
| Understanding & Depth (1) | A3 | 0.78 | Reconstruction, two-resolution comparison, MILP + integer modules, Xpress/HiGHS split now documented |
| Originality (1) | A3 | 0.78 | Half-hour rebuild, eligibility split, two-resolution reference; no single "outside the box" artefact |
| Amount of Work (1) | A3 | 0.78 | Brief's 2 h, 4 h extension, £9.5 linkage, price/eligibility cases, window and upkeep sensitivities |
| Logic of Argument (1) | A3 | 0.78 | Recommendation now follows from site-scale evidence; residual P2 gaps below |
| Background & References (1) | A3 | 0.78 | NREL fixed, LCHS added, package pinned; two refs still generic |
| Validity of Results (1) | A3 | 0.78 | 79/79 reproduced; solver logs, bounds, replay gaps; T2B exploratory |
| Presentation (2) | A3 | 0.78 | Two-panel figure, legible tables; title page sparse, one figure |

## Disposition of the v5 findings

| v5 finding | Status | v6 evidence |
|:--|:--|:--|
| **P0-1** headline at broad-market scale, recommendation at site scale | **Closed** | Main case is the 10 t/day site (§II.1, Table II.3); one-block increment at 8/11 modules = **£5.63m / £1.64m** (site_portfolios.csv, 14.100→19.738 and 5.478→7.116); broad market moved to §5.3 and labelled an extrapolation |
| **P0-2** battery positive only under perfect foresight; payback an oracle number | **Closed** | Paybacks now split: perfect information 4.1/7.2 yr, simple rule 7.2/7.4 yr (§5.4); T2B replay shows −£20.68m (A) and +£7.75m (B) with orders committed before the slot; abstract carries the staged-decision wording |
| **P1-1** 4 h main case vs the brief's 2 h; compliant menu buys nothing | **Closed** | Table II.5 is built on the 2 h reference (brief capital, 20% electrolysis minimum, both resolutions); daily 2 h = 12.46/2.18, half-hour 2 h = 13.42/3.78; forced one block adds +1.05/−1.32 and **both negative after upkeep**; 4 h is an explicit extension |
| **P1-2** no solver evidence; main sizing not shown as Xpress | **Materially closed** | Table C.1: HiGHS daily 2 h integer optimum (13,155 cols/24,113 rows, 0.505 s, gap 0); Xpress 9.9 replay 551 blocks, 4.34 s, £4/yr from archived, gap £5.13/yr; B uses Xpress + HiGHS with a zero-stock decomposition; §4.2 states the roles. Residual P2 on the licence-driven split |
| **P1-3** per-slot vs daily cap, payback uses the favourable one | **Closed for headline** | Site model uses the daily cap (§II.4 "shares offtake across each UTC day"); the old 845-module per-slot/flexible comparison (2.89 vs 2.51) is retained in Appendix C.2 as an earlier configuration, not a headline |
| **P1-4** 0.635 vs 0.6225 conversion factor | **Closed** | Appendix B.4: electrolyser 0.635 (2020£/2024$); Lazard battery totals divided by 1.02 to a 2024 basis, then 0.634974/1.02 ≃ 0.6225 (2020£/2025$). The arithmetic now matches £38.69m / £173.25 / £249.77 |
| **P1-5** £9.5/kg benchmark absent | **Closed** | Table II.1 states £9.50 ≈ £7.80 on the 2020 basis; Table II.4 adds a £9.50 (2020£) stress row (A 8 modules £20.02m, B 12 modules £8.56m); main case remains the brief-equivalent £7.80 |
| **P1-6** support price applied without eligibility | **Closed** | Two-rate case (§5.2, Table II.4): eligible surplus at £7.80, remainder at £2.50; A average receipt £6.58/kg, gain £6.06m; minimum supported shares 22%/42%; LCHS 20 gCO₂e/MJ cited |
| **P1-7** "accompanying package" not published | **Closed** | ZIP published with MANIFEST (190 files, hashes), report sha matches, `course-sources/` includes the brief and the Q&A transcript; refs [20]/[21] point to the archive |
| **P1-8** 14 physical pages vs 10-page limit | **Closed by owner rule** | 10 pages = body only; v6 body = 6 pages (PDF 3–8). Total 15 physical pages, appendices excluded (Addendum 2) |
| **P1-9** demand service falls under A without valuation | **Closed** | Site A coverage falls only 89.66→89.61 (−0.05 pp); §5.2 states A diverts 109 GWh/yr from sales and applies only where the client can allocate between markets |
| P2-1 energy attribution | **Partly fixed** | Capture 1,918 and unused decrease 2,092 both printed; the 174 GWh difference is still unexplained (residual) |
| P2-2 827 vs 845 modules | **Fixed** | Appendix B.3.1: 827 = flexible daily cap, 845 = per-slot version |
| P2-3 NREL / commit reference | **Fixed** | [13] now National Renewable Energy Laboratory; [3] no longer cites a commit |
| P2-4 title page | **Open (cosmetic)** | Still no names, large white space |
| P2-5 one figure | **Improved** | Figure II.1 now has two panels (seasonal surplus profile; electrolysis value vs capacity) |
| P2-6 35 vs 30 price days | **Open** | Still not explained in the text |
| P2-7 nominal vs usable cycles | **Fixed** | §4.2 now states "one nominal cycle per day on average (1.67 usable cycles)" |
| P2-8 cramped equation | **Fixed** | (II.1)/(II.2)/(II.8) re-typeset; Chapter III (III.1) legible |
| P2-9 £175 "benchmark" wording | **Fixed** | "the same HAR1 strike of £175/MWh in 2012 prices" |

## Numeric verification (79/79)

Reproduced exactly from the archive: Table II.3 counts/gains/coverage (10 rows); one-block and simple-rule increments; joint battery 4,500/900 MW and capital £1.79bn/£422m; capture 1,918/647 and unused decrease 2,092/647 GWh; renewable attribution 829/278; all 12 Table II.4 rows; two-rate modules/gains; NPV 217/84 (5%) and 144/42 (8%); break-even receipts 3.69/4.70; minimum shares 22%/42%; +20% capex thresholds 3.91/5.30; 2 h reference 13.42/14.47 and 3.78/2.46, increments +1.05/−1.32; daily 2 h 12.46/2.18; Table C.2 eight rows × three columns; battery-only 5.70/1.65; Xpress 551 blocks/4.34 s/£4.0 per year/gap £5.13; T2B pooled 363.5 days, B binary_all_in £7.75m, A five-action −£20.68m.

Author-reported, not independently re-run: the optimisation itself (I read saved schedules and logs, not re-solve), the 1,559 t/day EHO row, and the T2B forecast models.

## Residual issues (P2 only)

1. **§5.2 capture vs unused decrease.** 1,918 GWh captured vs 2,092 GWh less unused (Δ 174 GWh). Either explain (e.g. charging losses / sales diversion) or print one of the two.
2. **§5.4 T2B comparison settings.** A's −£20.68m is the five-action grid (as Chapter III describes); B's £7.75m is `binary_all_in` in the pooled window, and B has higher settings (observed_quantity £9.48m). State the selected policy for each side so the A/B contrast is not read as best-vs-default.
3. **Table II.4 "£9.50/kg in 2020 pounds".** This is a real-terms stress, not the brief's £9.50 (which is ≈£7.80 on the 2020 basis). Label it "stress case" to prevent double reading.
4. **Table II.5 forced block.** The one-block 2 h rows are a fixed comparison, not an optimum; mark "(fixed one block)".
5. **2 h product metadata.** In `reference_day_A_integer.json` the `brief-2h` product's `source` string says "Lazard 2025 utility4h low component envelope … +10% allowance", while its £51.247m capital equals the brief's €288,000/MWh × 200 MWh. Align the metadata string with the actual basis.
6. **Refs [9]/[11].** Both still say "in the accompanying package"; point to the inner paths (e.g. `FinalProject/tier1-candidate-20261107-v4.1-academic/research/PARAMETER_BASIS.md`, `equipment_study_inputs.json`).
7. **Xpress/HiGHS split (compliance nuance).** Documented, but the brief says the main modelling should use Xpress; the A capacity master is a HiGHS relaxation with an Xpress fixed-interface certification. One sentence saying the investment decision is Xpress-certified (or a written course confirmation on the licence-driven split) would remove the last ambiguity.
8. **Title page.** No author names; body uses 6 of 10 allowed pages, so there is room to move Table C.1 or a figure into the body if the group prefers.

## Visual notes

Pages 1, 5, 6, 7 and 8 viewed at 1.6×. Figure II.1 is legible in both panels; Table II.3/II.4/II.5 columns are aligned and readable; equations (II.1)–(II.8) and (III.1) are unambiguous; no overflow or clipped text found. Page 1 still has a sparse title page; page 8 (body 6) ends with white space.

## What would change the score

- Upward (79–80): items 1–3 fixed; one page of body space used for a decision table/figure.
- Downward: if the A/B T2B settings turn out not to be matched at the same information set, or if the brief's 2 h reference is read as mandatory for the headline (it is now the base case, so this risk is largely removed).
