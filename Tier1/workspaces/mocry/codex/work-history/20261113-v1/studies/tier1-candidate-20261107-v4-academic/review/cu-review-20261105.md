# Review of the Codex four-page Tier 1 demos, 5 November 2026

Scope requested: does the report meet the course and project requirements, are the mathematics and
wording correct, and are register and layout within a reasonable range. Strategic choices and the
group's Tier 2 allocation are explicitly out of scope.

## What was reviewed

| Artefact | Commit | Pages |
|---|---|---|
| `Tier1/workspaces/mocry/codex/tier1-independent/20261105-v2/report/Tier1_Report.pdf` | `71ce76e` | 4 |
| `Tier1/workspaces/mocry/codex/technical-report-latex/20261105-v1/output/pdf/tier1-example.pdf` | `ce30692` | 4 |

Both PDFs were read in full as text and all eight pages were inspected as rendered pages. The two
documents carry the same model and near-identical numbers; findings below are grouped, and the
artefact is named where a defect appears in only one of them.

Every checkable number was recomputed by me from my own copy of the same input series
(`tier1/20261105-v1/data/daily_model_inputs.csv`) and from the author's `crosscheck.json`. Nothing
below relies on the author's own arithmetic being right.

## Independently reproduced (all confirmed)

| Claim | Recomputed |
|---|---|
| 2,452 aligned days | 2,452 |
| 2023: 29 positive-surplus days, total 549.94 GWh, median 15.09 GWh | 29, 549.944 GWh, 15.090 GWh |
| 215.1 TWh sold in the A zero-investment case | 215,102.164 GWh |
| 280 strict-quality days in 2023 | 280 |
| 13.92 GWh = a 20 MW module filling 0.48 GWh on 29 surplus days | 13.92 = 29 × 0.48 |
| 8.1% of input and 2.53% of annual surplus | 8.10%, 2.53% |
| Battery ceiling £48.7k per module | 1.7076 MWh × 28,516 £/MWh = £48.7k |
| Battery annual cost £96.4k | 768,705 × 0.096342 + 14,862 × 1.5 = £96.4k |
| Capital 1.90 + stack 0.59 = 2.49 £m/year | 1.9001 + 0.5900 = 2.4901 |
| Bridge 23.97 − 12.39 − 0.52 − 2.49 = 8.57 | 8.57 |
| Payback 2.64 simple, 2.90 discounted, NPV 131.78 | 29.21/11.06 = 2.641; 2.903; 131.7 |
| £7.29m at 25% higher cost and 8% discount | 11.06 − 3.243 − 0.533 = 7.29 |
| 175.25m for 120 MW | 6 × 29.2088 = 175.25 |

The objective, the flow balance, the storage window (1.8 MWh = 60% of 3 MWh), the efficiency split
(η = √0.90 with Σr = 0.90 Σc) and the loading limits (96/480 MWh per online module) are consistent
with each other and with the stated parameters. Units and dimensions check out throughout, including
v·h/κ in £/kg × MWh ÷ (MWh/kg).

## Requirement compliance

The Tier 1 elements the brief asks for are present: a checked and recorded data repair, a matched
no-investment counterfactual, a comparison with a simple rule, model validation, sensitivity on the
decision parameters, two figures, and a client recommendation. Four gaps, in order of what a marker
is most likely to notice:

1. **The data-repair record is one sentence.** Brief page 2 asks that data adjustments be checked
   and recorded. The demo gives four lines and a reference. The 10-page budget has room for a
   four-row table (rows kept/dropped, snapshot→full-day repair, zero-volume price removal, gap
   flags, unit and CPI conversion). This is the brief's first ask and currently the thinnest part.
2. **The brief's own reference parameters are never anchored.** TC-08 and TC-09 allow researched
   replacement, but require the departure to be explained. The demo cites good sources for
   £29.21m/module and £7.799/kg, yet never states what it replaces: the brief's €288k/MWh battery
   and £9.5/kg hydrogen benchmark. One sentence per parameter would close this, and would also
   show where the brief's £9.5/kg sits on the trigger map, where it is currently invisible.
3. **"Each historical year" is claimed, four are shown.** Section 2.5 says the module is evaluated
   on each historical year and then tabulates 2022–2025. The sample covers 2020–2026 with `1/Y`
   already normalising the partial year, so either add the missing rows or change the claim.
4. **"A separate implementation agrees on 18 matched cases" has no citation.** A reader cannot tell
   who or what that is. My package is the obvious referent; if so, name it with a path and commit,
   or drop the sentence. An unattributable cross-check reads weaker than no cross-check.

Two smaller points: the brief asks for a distinction between data-supported and assumption-driven
conclusions, which the demo leaves implicit (tagging the two or three key claims would do it); and
the validation paragraph reports counts (42 schedules, 8 trigger points) without saying how the 8
were chosen.

## Mathematics and wording

No arithmetic error was found. Five statements should be tightened:

1. **Break-even netback £4.61/kg versus my £4.6229.** The difference is 0.28% and is explained by
   the two implementations' known disagreement: £49.0/yr on the reference electrolyser case is
   £0.016/kg at 3,074 t/yr, the same order as the 0.013 gap. It is not an error, but two published
   demos should not disagree in the second decimal without a stated tolerance. Either quote
   £4.62 and note ±£0.02, or state the solver tolerance that produces 4.61.
2. **The 25% cost stress does not say what is stressed.** £7.29m is reproducible only with the
   module capital stressed and stack renewals held at base (£7.15m if both are stressed). Say which.
3. **Table 3's "Sales given up" is the allowance, not necessarily the realised sale reduction.**
   21.51 GWh is exactly the 99.99% floor complement. My run of the same constraint realises
   21.3 GWh, so the two agree; but the column would be unambiguous if labelled as the allowed
   sacrifice, with the realised figure reported separately. (My own 35.43 GWh is electrolyser input,
   not sacrificed sales, and is not published as a sales figure.)
4. **Policy B at negative prices is only half-stated.** The text says B fixes sales to min(G, D)
   "including on negative-price days", which means negative revenue; the consequence is never
   drawn. One clause would make it a finding rather than a footnote.
5. **"The 2025 contract downside reverses both investment cases" sits above the row it refers to**
   and reads, next to +13.17/+4.48, as if 2025 were already negative. Move it after the
   "2025, £4/kg and 5 t/day" row or name that row explicitly.

## Register and layout

Register is appropriate: plain declarative sentences, numbers first, no marketing. Within the range
expected in this course. Layout defects worth fixing:

- **Blank blocks at the foot of pages 3 and 4 of the Markdown-built PDF** — about 20 lines on page 3
  and about 12 on page 4. Page 3 ends after the Table 2 caption with a fifth of the text height
  empty; page 4 ends after the sources line. This is the single most visible difference from a
  hand-set document and the easiest to fix by moving one table or shortening one paragraph.
- **Caption placement is inconsistent.** Table 1 has its title above the table; Tables 2, 3 and 5
  have captions below. Pick one rule (tables above, figures below is the usual convention).
- **Hyphen-minus in table columns.** `-1.07`, `-12.39`, `-0.24` sit beside `+8.57` and `−0.52`.
  A proper minus in every negative cell.
- **Table 1 row labels are top-aligned** against multi-line descriptions in both artefacts — the same
  `p{}`-versus-`c` baseline defect I hit in my own template. Use `m{}` for every column.
- **Figure 2's panels are squat** relative to the text measure, and the 0–16 netback axis in panel B
  is half empty. A taller aspect ratio and a shared y-axis label would read better.
- On the LaTeX version, the two loading limits are set as `\underline{E}_H` and `\overline{E}_H` and
  the defining sentence keeps the bars, so constraint (1d) is correct and legible; only unusual.
  `E_H^{min}`, `E_H^{max}` would need no explanation.

## What this review changed in my own package

The author's cross-check found a real defect in my published text: the 2020 A replay was quoted as
+£16.72m in four files while `results/cases.csv` holds 16.7781. Checking the same row found a second
slip, +£3.11m for 2020 B against 3.124. Both are corrected in the same commit as this
review, the four-page PDF rebuilt, and `src/check_quoted.py` added so that the cross-year row, the 2020 quote
and the absence of the retired figure are checked from the CSV on every run. Credit for the catch.

## Bottom line

Mathematically sound and requirement-complete for a four-page Tier 1 section, with no error I could
find in the numbers. What holds it back is presentation and traceability, not modelling: the thin
data-repair record, the missing anchor to the brief's reference parameters, and the pagination.
None of these needs a new model run; all can be fixed in the page budget already available.
