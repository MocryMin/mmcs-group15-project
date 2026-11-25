# Addendum 1 — the chapter score on the course report rubric (written before opening the preview)

Recorded 2026-11-25, with `STANDARD.md` in the same commit and **before** I opened
`tier2b-report-preview.pdf`. Same trigger and provenance as the Tier 1 addendum: the MMCS 25/26 report grade
descriptors are a course-supplied document (path
`Tier1/workspaces/mocry/codex/work-history/20261113-v1/studies/tier1-candidate-20261107-v4.1-academic/references/mmcs_25_26_reports_descriptors.pdf`,
PDF metadata 2026-11-03 11:51:18 +0000), already transcribed verbatim into
`Tier1/.../review/20261122-tier1-independent-standard/ADDENDUM_1_OFFICIAL_RUBRIC.md`. I reuse those transcribed
headings and anchor phrases rather than re-quoting from memory.

## Weights and anchors

| # | Dimension (verbatim heading) | Weight | Anchor language that matters for a Tier 2B chapter |
|:--|:--|--:|:--|
| D1 | Understanding and Depth of Academic Content | 1 | "mastered advanced theoretical concepts or mathematical models, correctly applied elaborate numerical algorithms"; errors "few and mostly minor" (A3) vs "several" (B) |
| D2 | Originality of Approach | 1 | "a few ideas to explore different research directions"; "significant contribution … outside the syllabus" (A2) |
| D3 | Amount of Work Done | 1 | "All questions raised in the project description are addressed" (A3); "most … adequately" (C) |
| D4 | Logic of Argument | 1 | "main steps in the mathematical, statistical, or computational reasoning … few logical gaps"; "serious gaps" (D) |
| D5 | Background and References | 1 | "adequately supported by references to relevant background and precursor items … appropriate sources" (A3); "many essential citations missing" (D) |
| D6 | Validity and Assessment of Results | 1 | "discussion of the validity of results is convincing and reliable"; "expected evidence may be missing" (C) |
| D7 | Presentation | 2 | "Figures, tables, and mathematical formulae are presented clearly … notation well-defined"; "unclear or incorrect formula" (C) |

Fractions: A1 0.95, A2 0.85, A3 0.78, B 0.65, C 0.55, D 0.40, E–H 0.20. In-band fractions are allowed when a
dimension sits between anchors.

Chapter score = 100 × (D1 + D2 + D3 + D4 + D5 + D6 + 2·D7) / 8, with D7 at weight 2 (25% of the weight sum).
A band of ±4 is reported around it.

## How the seven dimensions read for a five-page chapter

- **D1.** Correctness and depth of the *temporal* machinery: SOC recursion, rolling re-solve, forecast
  construction, and the economics that converts forecasts into decisions. An arithmetic slip inside a printed
  formula is a D1/D7 defect; a look-ahead that invalidates a policy is a D1/D6 defect.
- **D2.** Not novelty for its own sake. Credit for an idea the brief did not ask for and that survives checking
  (e.g. a forecast-error-aware operating rule, a properly constructed like-for-like comparator); no credit for
  architecture variety that is not used in the decision.
- **D3.** Scored against Section A's list, scaled to a five-page budget. A missing A-item is a deduction; a
  deliberately omitted nice-to-have is not (STANDARD §9). Because the chapter is half the report, D3 is judged
  on the chapter's own coverage and recorded as partial — the report-level total is a later judgement.
- **D4.** The chain: Tier 1 position → feasible operation → comparator → recommendation → conditions for change.
  A gap anywhere in that chain is a D4 deduction, even if every number is right.
- **D5.** Chapter-local: are the forecast source, the cost bases and the market assumptions referenced? D5 is
  where "we used a model" without a source, or a public data set without an identity, costs credit.
- **D6.** The heart of Tier 2B: validity of the information set, honesty about realised vs expected, stress and
  worst-window evidence, break-evens, and stated limits.
- **D7.** Five-page craft: page economy, table comparability, figure legibility, notation defined once,
  printed pages that match their intended positions in the combined report.

## Mapping from the chapter criteria to the dimensions

| STANDARD criterion | Primary dimension(s) |
|:--|:--|
| C1 Framing/continuity/decision statement | D1, D4 |
| C2 Chronological model integrity | D1, D6 |
| C3 Information set, forecasting, calibration | D1, D6, D5 (sources) |
| C4 Comparator and economic attribution | D4, D6 |
| C5 Performance through time, stress, sensitivity | D3, D6 |
| C6 Recommendation, thresholds, what would change | D1, D4, D6 |
| C7 Reproducibility and presentation | D7, D3 |

## Rules

1. The scored grade comes from the seven dimensions, not from the criterion weights. The criterion weights in
   `STANDARD.md` §5 organise the evidence; they are not a second grade.
2. A P0 finding caps the mapped dimension at one full anchor step below where it would otherwise sit, and the
   cap must be justified in the finding. P1/P2 reduce within a dimension and are never double-counted.
3. Reproducibility marks (`recomputed` / `author-reported`) enter D6 and D1: an unrecomputable headline that
   carries the recommendation is a P0; an unrecomputable supporting number is P1.
4. The 25/26 rubric predates the 2026/27 brief and no 2026/27 marking grid has been published. It is the
   strongest available course evidence, used with that caveat. No claim of an official grade is made, and the
   chapter score is not a report grade.
5. If the course publishes a 2026/27 grid, this addendum is superseded by a further recorded addendum, not
   silently edited.
