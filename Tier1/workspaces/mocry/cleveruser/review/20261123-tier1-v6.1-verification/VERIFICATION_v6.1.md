# v6.1 verification of the Tier 1 report candidate

Verifier: `mocry-cleveruser`. Date: 2026-11-23.
Target: `Tier1/workspaces/mocry/codex/technical-report-latex/20261123-v6.1/report.pdf`
sha256 `f218a0e00b4e9f23f9aa866f50ef7668967a5b49ba8c3e478b633c13d3564f83`, 138,363 bytes, 15 PDF pages (cover/abstract i, contents ii, body 1–6, R1, A1–A6). Published at `589b9d5`.
Sources: `report-source.zip` sha256 `618cb5699567356c5cf4e18db9e28cd1f28b654525caedf8068c58d142a250a3` (10 LaTeX files); both digests agree with `SHA256SUMS.txt`.
Evidence: baseline values still come from the pinned v6 archive `tier1-site-evidence-v6.zip` (sha256 `f4c0e6e5…b50440`, 190 files, `MANIFEST.json` intact). The new operating-limits numbers come from Julian's study at commit `c3902fe`, `Tier1/workspaces/julian/claude/tier1-main-results/20261123-v1` (`results/*.csv`, `results/checks.json`, `REVISION.md`).
Standard: `STANDARD.md` + `ADDENDUM_1_OFFICIAL_RUBRIC.md` + `ADDENDUM_2_PAGE_RULE.md` (owner rule: 10 pages = body only; abstract, contents and appendices excluded).
Method: read all 15 pages; rendered and viewed PDF pages 1, 3, 4, 6, 7, 8, 13 and 14 at 1.6×; ran `v6.1_checks.py`, which reads both archives directly, pulls Julian's results from git (`c3902fe`), and compares 128 printed values with CSV/JSON records. **128 checks, 0 failures.**

## Verdict

v6.1 keeps every v6 headline number and adds a verified operating-limits sensitivity that ties equipment limits to the investment recommendation. Of the eight P2 items left by the v6 verification, five are closed, two partly closed, one unchanged. No new arithmetic error was found. What remains is documentation-level, plus one editorial question about which operating rule should carry the headline. **Revised score: 79/100 (descriptor fractions 0.78–0.80; no descriptor reaches A1). Band 76–82. Non-official.**

## Disposition of the eight v6 P2 items

| v6 P2 | Status | v6.1 evidence |
|:--|:--|:--|
| 1. §5.2 capture 1,918 GWh vs unused decrease 2,092 GWh (Δ 174 GWh) | **Closed by removal** | §5.2 now prints only the capture (1,918 A / 647 B) and the renewable attribution (829 / 278). The inconsistent pair is gone. Cost: the reader can no longer see that A's joint portfolio also removes 2,092 GWh from unused generation, 174 GWh more than it captures. Optional transparency note, not an error. |
| 2. T2B settings unlabelled (A five-action, B `binary_all_in`; B also has higher settings) | **Closed** | §5.4: "A's five-action forecast controller nets −£20.68m and B's binary full-group controller nets £7.75m"; §III.2 defines the full-group order as "up to 450 MWh". Pooled rows reproduce at 363.5 days. |
| 3. £9.50/kg in 2020 pounds read as the brief's benchmark | **Closed** | Table II.4 row is now "10 t/day at £9.50/kg (real-price stress)". |
| 4. Table II.5 fixed one-block rows unlabelled | **Closed** | Rows read "Reconstructed half-hour, fixed zero blocks" and "fixed one block"; caption states "under the brief's capital cost"; §5.3 confirms five modules are held. |
| 5. `reference_day_A_integer.json` brief-2h `source` string vs its £51.247m capital | **Open in the pinned archive** | Archive frozen at v6, so the mismatch remains inside the ZIP. The report now states the brief's capital basis in the Table II.5 caption, which removes the reader-facing ambiguity but not the metadata inconsistency. |
| 6. Refs [9]/[11] point at "the accompanying package" | **Partly closed** | [9] now names "R1–R4 research and research/PARAMETER_BASIS.md", but still says "in the accompanying package" and never names `tier1-site-evidence-v6.zip`; [11] is unchanged ("10 November working archive"). |
| 7. Xpress/HiGHS split vs the brief's "main modelling in Xpress" | **Materially closed** | §4.2 states the split and "For A at 45 blocks and six electrolysers, the Xpress replay agrees with the saved dispatch value within £4/year"; C.1 states that HiGHS's linked-horizon capacity relaxation yields supporting planes that constrain competing integer capacities, that the Xpress fixed-interface replay preserves block boundaries, and that both portfolios beat the best upper bound for any other tested or screened capacity combination. Residual: the two £4 statements differ in direction ("agrees with the saved dispatch value within £4" in §4.2 vs "improves the saved feasible A plan by about £4" in C.1), and no single sentence says the capacity choice itself is Xpress-certified. |
| 8. Title page (no names, white space) | **Open** | Cover still reads only title, course, "Group 15", "November 2026". Body uses 6 of 10 allowed pages. |
| (v6 P2-6: 35 vs 30 price days) | **Also fixed here** | Appendix A.3: "The 35 missing or severely incomplete price days include the 30 dates omitted in the source price file and five further dates requiring a complete estimate." |

## New content: operating limits and the investment recommendation

| Printed claim (page / table) | Recomputed | Source | Result |
|:--|:--|:--|:--|
| 40.2 MW (A) and 55.3 MW (B) (§5.1, §5.4, abstract) | 8 × 5.031 = 40.248; 11 × 5.031 = 55.341 | Table II.3 counts, Table II.2 module rating | pass |
| Capital £58.8m / £80.8m (§5.4) | 58.7798 / 80.8222 | `main_table.csv`, `operating_rules.csv` | pass |
| "a 20% minimum load leaves the half-hour result effectively unchanged" (§5.3) | A 14.100113 vs 14.100135; B 5.478233 vs 5.478280 | `operating_rules.csv` rows 1–2 | pass |
| Table B.1 row 1: 14.10 / 5.48 | same two rows, 2 dp | `operating_rules.csv` | pass |
| Table B.1 row 2 (midnight, 20%): 13.18 / −8.14 | 13.1808 / −8.13993 | same | pass |
| Table B.1 row 3 (≥4 days): 13.16 / −8.32 | 13.163731 / −8.321908 | same | pass |
| Table B.1 row 4 (≥5 days): 13.16 / −8.32 | 13.155459 / −8.321908 | same | pass |
| Table B.1 row 5 (four days, resized): 13.46 / 0.00 | A 6 modules, 30.186 MW, 13.4596; B 0 modules | `main_table.csv` | pass |
| "A drops from eight to six modules (30.2 MW)" (§5.3) | 6 × 5.031 = 30.186 | as above | pass |
| "B selects zero … longest surplus spell above one module's minimum is 56 hours, short of the 96 needed" | 56.0 h; no 72 h or 96 h stretch in `surplus_runs.csv`; "no production at any size with a 4- or 5-day minimum run" | `checks.json` items "longest continuous surplus … 56.0 hours", "supply priority cannot hold minimum load" | pass |
| "minimum-run programmes solved to optimality" (B.3.1) | "largest gap GBP 0.000 per year; every path passes the independent minimum-run check" | `checks.json` | pass |
| Reserve variant: ten modules, £8.11m/yr, 61 GWh/yr forgone sales | 10 modules / 50.31 MW / 8.1137; 61.2 GWh taken ahead of sales; served −0.0243 pp | `main_table.csv` "B with reserve", Julian REVISION table | pass |
| NPV £217m / £84m at 5% (§5.4) | 216.75 / 84.21 | `electrolyser_finance.csv` | pass |
| NPV £144m / £42m at 8% (C.2) | 144.30 / 41.82 | same | pass |
| Break-even receipts £3.69 / £4.70 (§5.4) | 3.6901 / 4.7030 | same | pass |
| "22.5% of output receives the support price" (§5.4) | (3.6901 − 2.50)/(7.7990 − 2.50) = 22.46% | same + HAR1 netback | pass |
| "direct surplus supplies 41.7% of electrolysis input" (§5.4) | 0.41734 | `site_portfolios.csv`, A Electrolysis | pass |
| Simple paybacks 3.1 / 6.5 years (§5.4) | 58.7798/(20.1524 − 1.0403) = 3.076; 80.8222/(13.8001 − 1.4315) = 6.534 | `operating_rules.csv`, definition matches B.4 | pass |
| Battery paybacks 4.1 / 7.2 and 7.2 / 7.4 (§5.4) | 38.6898/(5.63 + 3.727) = 4.14; /(1.64 + 3.727) = 7.21; /(1.63 + 3.727) = 7.22; /(1.50 + 3.727) = 7.40 | Table C.2, Table II.2 annual charge | pass |

Everything else printed in v6 is unchanged and still reproduces: Table II.3 (10 rows), one-block and simple-rule increments, joint 4,500/900 MW and £1.79bn/£422m, capture 1,918/647 and attribution 829/278, Table II.4 (12 rows) plus the two-rate rows, the two-hour reference 13.42/14.47 and 3.78/2.46 with +1.05/−1.32, daily 2 h 12.46/2.18, HiGHS 13,155 columns/24,113 rows, Table C.2 (8 rows × 3 columns), battery-only 5.70/1.65, Xpress 551 blocks/4.3 s/£4 per year/gap 5.1, T2B pooled 363.5 days with A −£20.68m and B £7.75m.

Author-reported, not independently re-run: the optimisation itself (saved schedules and logs were read, not re-solved), Julian's surplus-spell computation (taken from its `checks.json`), the EHO 1,559 t/day row, and the T2B forecast models.

## Residual issues

1. **Which operating rule carries the headline (editorial, P2-high).** The base case allows half-hour starts and stops down to 12.5% load, while the course Q&A (transcript lines 86 and 125, cited as [15]) says an electrolyser is "not gonna … turn it on for an hour, turn it off for an hour" and that "if it's on, it would have to be on for a long time". The report discloses the four-day variant and recommends conditionally ("appraise the smaller A plant and defer the surplus-only B investment"), which keeps it honest, but §5.3 calls the test "a classroom example" while it is the rule Julian's own study treats as the main case — and under it B falls from £5.48m to zero. The group should state explicitly which regime is the Tier 1 base and why, because Julian's published headline (30.2 MW / none) and this report's (40.2 / 55.3 MW) now read as opposite front-page answers.
2. **Q&A third operating mode not appraised (P2).** Lines 92 and 128 of the same transcript describe units kept online at the 20% minimum and varying load rather than switching off. Only the "reserve minimum-load power ahead of sales" variant in B approximates it; A has no continuously-on case. One sentence on why it is or is not covered would close the gap.
3. **Reserve variant changes policy B's definition (P3).** §5.3/B.3.1 call it "a variant" and report a −0.024 pp coverage change, but the report does not say that it lets online modules take minimum-load power ahead of electricity sales, i.e. it relaxes B's service rule. Julian's note states this and says the choice is the group's.
4. **£4/year stated in two directions (P3).** §4.2: the Xpress replay "agrees with the saved dispatch value within £4/year". C.1: "It improves the saved feasible A plan by about £4/year". Pick one formulation.
5. **Refs [9]/[11] (P3).** Name `tier1-site-evidence-v6.zip` and the inner paths instead of "the accompanying package" / "10 November working archive".
6. **Pinned-archive metadata (P2, evidence-level).** The `brief-2h` `source` string in `reference_day_A_integer.json` still contradicts its £51.247m capital. Fixing it needs a superseding archive; the report cannot fix a frozen ZIP.
7. **B's minimum supported share dropped (P3).** v6 printed 42%; the evidence gives 41.6%. v6.1 omits the B figure rather than correcting it, so §5.4 now gives the A share only. Reprint 41.6% if space allows.
8. **Title page (P2, unchanged).** No author names; body page 1 is half empty and body 6 ends with white space, with 4 of 10 body pages unused.

## Visual notes

PDF pages 1, 3, 4, 6, 7, 8, 13 and 14 viewed at 1.6×. Table II.3, II.4, II.5, B.1, C.1 and C.2 are aligned and readable; no overflow, clipping or orphaned captions. New Table B.1 sits in Appendix B.3.1 with its caption above and the HiGHS sentence below. The abstract page carries the headline and the two conditionality sentences; the cover itself is unchanged and sparse.

## Score

| Descriptor (weight) | Anchor | Fraction | Basis |
|:--|:--|--:|:--|
| Understanding & Depth (1) | A3+ | 0.79 | Limits now tied to investment; regime choice left open |
| Originality (1) | A3 | 0.78 | No new own-model artefact; the sensitivity is Julian's |
| Amount of Work (1) | A3+ | 0.80 | Five-case limit grid, resizing, reserve variant, B.3.1 |
| Logic of Argument (1) | A3+ | 0.79 | Conditional recommendation; headline regime unresolved |
| Background & References (1) | A3+ | 0.79 | [22] added, [15] cites transcript lines; [9]/[11] vague |
| Validity of Results (1) | A3+ | 0.80 | 128/128 reproduced; residual archive metadata |
| Presentation (2) | A3+ | 0.79 | Labels fixed; cover and page fill unchanged |

Weighted: (0.79 + 0.78 + 0.80 + 0.79 + 0.79 + 0.80 + 2 × 0.79) / 8 = **79** (v6: 78).

## What would change the score

- Upward (80–81): decide and state the base operating rule (item 1), close items 3–5 and 7, and use one of the four spare body pages for a decision table or the operating-limit graph.
- Downward: if the group adopts Julian's main rule as the Tier 1 base, the abstract, §5.1 and §5.4 headline numbers (40.2/55.3 MW, £14.10m/£5.48m) must be rewritten to 30.2 MW / none; leaving both versions standing in group outputs is the main reputational risk, not a numeric error.
- No numeric regression was found: all 79 v6 checks still hold, and the 49 new checks on the operating-limits content pass.
