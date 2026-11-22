# Addendum 1 — aligning the standard to the course report rubric (still before opening v5)

Recorded 2026-11-22, after `871c4e3` (standard) and **before** I opened the v5 PDF or its review notice.
Trigger: the official four-page "MMCS 25/26 Reports: Dissertation Grade Descriptors" was located at
`Tier1/workspaces/mocry/codex/work-history/20261113-v1/studies/tier1-candidate-20261107-v4.1-academic/references/mmcs_25_26_reports_descriptors.pdf`
(a course-supplied Learn document, not an agent's opinion; its PDF metadata timestamp reads Tue, 03 Nov 2026 11:51:18 +0000).

## What the rubric fixes

Seven dimensions, first six at weight 1 and Presentation at weight 2 (total 8; presentation therefore 25% of the rubric's weight sum):

| # | Dimension (verbatim heading) | Weight | Anchor language that matters here |
|:--|:--|--:|:--|
| D1 | Understanding and Depth of Academic Content | 1 | "mastered advanced theoretical concepts or mathematical models, correctly applied elaborate numerical algorithms"; errors "few and mostly minor" (A3) vs "several" errors or a misunderstood aspect (B) |
| D2 | Originality of Approach | 1 | "a few ideas to explore different research directions"; "significant contribution … outside the syllabus" (A2) |
| D3 | Amount of Work Done | 1 | "All questions raised in the project description are addressed" (A3); "should address most … adequately" (C) |
| D4 | Logic of Argument | 1 | "main steps in the mathematical, statistical, or computational reasoning … few logical gaps"; "serious gaps" (D) |
| D5 | Background and References | 1 | "adequately supported by references to relevant background and precursor items … appropriate sources" (A3); "many essential citations missing" (D) |
| D6 | Validity and Assessment of Results | 1 | "discussion of the validity of results is convincing and reliable"; "expected evidence may be missing" (C); "almost no discussion or validation" (E-H) |
| D7 | Presentation | 2 | "Figures, tables, and mathematical formulae are presented clearly … notation well-defined"; "unclear or incorrect formula" (C) |

## Consequence for scoring

1. **Final grade = rubric weights × anchor fractions.** Each dimension is graded at the descriptor anchor (A1, A2, A3, B, C, D, E-H), converted to a 0–1 fraction with the midpoints A1 0.95, A2 0.85, A3 0.78, B 0.65, C 0.55, D 0.40, E-H 0.20, then weighted 1:1:1:1:1:1:2. The report table shows dimension anchor, fraction, weight and evidence.
2. **My criteria C1–C7 remain the evidence probes underneath these dimensions**, not a parallel grade. Mapping:
   - C1 framing → D1, D4
   - C2 model integrity → D1 (correct application of the model), D4 (reasoning steps present)
   - C3 data/provenance → D5, D6
   - C4 results validity → D6, D1
   - C5 comparison & sensitivity → D4, D6, and D3 (the brief's questions include comparison and sensitivity)
   - C6 recommendation/risk → D1, D4, D6 (consulting judgement is how this project's objectives are met)
   - C7 presentation & compliance → D7
3. **Severity caps apply to the mapped dimension**, not to a private weighting: a P0 cap reduces the affected dimension(s) by at most one full anchor step, and must be justified in the finding. P1/P2 reduce within a dimension and are not double-counted.
4. **D3 is read against the brief's questions**, which include: how much battery/electrolyser; whether the added value justifies capital; comparison with a simpler strategy; sensitivity; and "what could cause the recommendation to change" (brief pp.3, 5). A report that covers only capacity-sizing and skips comparison/sensitivity loses D3 as well as D4/D6.
5. **D7 is not softened by the 10-page limit.** The teacher's limit (transcript line 236) is a compliance gate; the rubric's presentation anchor still judges legibility and notation. A 10-page report that parks its model in an appendix fails D7 *and* D3/D4 (teacher: formulation belongs in the body, line 233).
6. The 25/26 rubric predates this 2026/27 brief and `PROJECT.md` says the detailed marking grid was not part of the supplied brief. It is used as **the strongest available course evidence**, with a stated caveat, not as a confirmed 2026/27 marking scheme. No claim of official score is made.

## What does not change

Sources, gates, severity taxonomy, audit protocol, out-of-scope list and falsifiers in `STANDARD.md` remain. If a 2026/27 rubric is later published, this addendum is superseded by another recorded addendum, not silently edited.
