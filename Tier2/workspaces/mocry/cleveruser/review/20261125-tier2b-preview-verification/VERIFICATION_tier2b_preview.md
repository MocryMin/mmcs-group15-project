# Tier 2B preview — independent verification (chapter score 79, band 75–83)

Reviewer: `mocry-cleveruser` (member `mocry`, human Ran Min).
Date: 2026-11-25. Repository state: local `main` = `84471f6` + my standard commit `3abab26`.
Standard used: `Tier2/workspaces/mocry/cleveruser/standard/20261125-tier2b-independent-standard/`
(`STANDARD.md`, `ADDENDUM_1_OFFICIAL_RUBRIC.md`, `ADDENDUM_2_PAGE_RULE.md`), committed and pushed **before**
this PDF was opened.

Target (pinned, hashes verified against the published `SHA256SUMS.txt`):
`Tier2/workspaces/mocry/codex/technical-report/20261125-preview/tier2b-report-preview.pdf`,
sha256 `5d03f59e…430a125b`, 118,822 B, 5 pages, printed 6–10; evidence zip sha256 `abf99335…7e21486c`.

Independence: I did not read `mocry-claude`'s `20261125-tier2b-outline` or `20261125-tier2b-preview` reviews,
and I did not use the author's request as a source of requirements. The request told me the chapter occupies
five printed pages; everything else below comes from the brief, the Q&A transcript, the rubric and the artefacts.

---

## 1. What was verified, and how

`checks_tier2b_preview.py` (same directory) reads the published PDF and the published zip directly and
recomputes 216 printed quantities from the author's own evidence tables. **All 216 pass** at the printed
rounding (tolerances 0.006 £m, 0.05 GWh, 0.0005 pp, 0.51 units on £k and £/MWh):

| Group | Passed | What it covers |
|:--|--:|:--|
| III.1 | 84/84 | all eleven Table III.1 rows: net, battery cost, gross = net + plant + battery cost, served %, unused, RE, H₂ |
| III.2 | 44/44 | six windows × six columns of Table III.2, and the six-window means |
| III.3 | 24/24 | Table III.3 stress weeks (RE, load, price, A £k, B £k) |
| III.4 | 7/7 | four break-even capitals, the £97/kWh base coherence, the £4.28/kg hydrogen break-even |
| III.5 | 36/36 | Table III.5 price/gen/load MAE, sign accuracy, net value, the £0.20m gap, 6/6 window ranking |
| selection | 12/12 | reference-window argmax (A 7 → £0.69m, B 22 → £12.51m), six-window argmax (11/11), all-positive-counts-negative without 2021/22, £8.70m worst window, £6.19m/−1.55m split |
| mechanics | 6/6 | 90% round trip in the trace, ≤1 cycle/block-day, daily-sum = table-sum, 2,191 days |
| artifact | 2/2 | published sha256 values |

I also read all five printed pages end to end, rendered and looked at them, and read the LaTeX source and
`build_evidence.py`. Nothing in the chapter's numbers is unsupported by its own tables; the defects below are
about what the numbers mean, what is not said, and what cannot be regenerated.

## 2. Score

Rubric mapping per `ADDENDUM_1`; fractions A1 0.95, A2 0.85, A3 0.78, B 0.65, C 0.55, D 0.40.

| Dimension | Anchor | Fraction | Why |
|:--|:--|--:|:--|
| D1 Understanding and depth | A3 | 0.78 | Real chronology, SOC recursion, DP, classifier, truth diagnostics, break-evens. Held back by the oracle contradiction (P0-1) and the unexplained 4× forecast gap (P1-1) |
| D2 Originality | A2 | 0.85 | Rolling DP against a rule and a classifier, capacity selection separated from replay, shock-year break-even; ideas the brief did not prescribe |
| D3 Amount of work | A3+ | 0.82 | Nearly every Tier 2B requirement is touched in five pages; sustainability's renewable leg and data-vs-assumption labelling stay thin |
| D4 Logic of argument | A3 | 0.80 | Clear chain from Tier 1 portfolio to recommendation; broken where Table III.1 compares 11 A-blocks with 9 B-blocks and where the oracle gap is asserted |
| D5 Background and references | C | 0.55 | The chapter contains **no citation at all**: not the £7.80/kg receipt, not the cost basis, not the published day-ahead prices, not the model families. Report-level D5 will be higher; chapter-level it is the weakest dimension and the cheapest to fix |
| D6 Validity of results | A2− | 0.82 | Unusually honest: the simple B rule beats the classifier in 6/6 windows and the chapter says so; truth diagnostics bound the value of information. Reduced by the training-window regime (P1-3) and terminal-stock treatment (P2-5) |
| D7 Presentation (×2) | A2 | 0.85 | Clean tables, legible figures, printed pages that match their intended positions. A third of printed p.7 is blank on a zero-slack 5-page budget; two figures have contrast problems |

Score = 100 × (0.78 + 0.85 + 0.82 + 0.80 + 0.55 + 0.82 + 2×0.85) / 8 = **79** (band 75–83).
Diagnostic criterion scores: C1 8/10, C2 16/18, C3 14/18, C4 13/16, C5 12/14, C6 13/14, C7 7/10.

This is a chapter score, not a report grade. With the P0 resolved and P1-1/P1-2 fixed, the same evidence would
sit at 84–86; D5 alone accounts for ~3.7 points of the gap.

## 3. Findings, most consequential first

### P0-1 The plant oracle cannot be reconciled with the Tier 1 half

Locators: chapter printed p.6 (§1, "first we replay zero storage"), p.7 §2.1 and Table III.1 row `A: plant
oracle` (gross 55.94, net 51.40), evidence `plant-oracle.csv` (six rows, `oracle_gap ≈ 1e-8`, Xpress status
optimal). Tier 1 v7.1: printed p.4 Table II.3 row "20% four-day, zero battery 0/6 → **13.46**", printed p.5
Table II.6 ("Assumed hydrogen price … 7.80 … Electrolyser modules 6 … Net gain 13.46"), and A4 Table B.1 row
"Four days, 20%, six modules (A) and zero (B) **13.46**".

Both are the same object: six modules, 20% floor, four-day runs, 10 t/day, half-hour data, full information,
net gain over same-policy direct sales. They differ by a factor of 3.8. My recomputation confirms 51.40 is
what the shipped table says, so this is not a typesetting error; either the oracle model relaxes a constraint
that binds in Tier 1 (the daily offtake quota, the minimum-load reservation, the four-day path condition) or
Tier 1's 13.46 comes from a different model than its captions say.

Why it matters: the chapter's central sentence — "Full foresight raises the mean to £51.40m" — and the
implied loss from forecasting (£39.45m/window, 77% of achievable value) both rest on it. If Tier 1's 13.46 is
right, forecast operation (11.95) is close to full information (13.46), and the story in §2.1 inverts. If the
oracle is right, Tier 1's NPV (£206.91m), payback (2.56 y) and "is the added value sufficient" answer
understate the plant by roughly £38m per window.

Needed: one of (a) rebuild the oracle with the same constraints and show 51.40, or (b) state which model each
number comes from and which one the client should use, and delete the other from the comparative sentence.

### P1-1 The value lost to forecasting is measured but not explained

Printed p.7 §2.1 gives 11.95 (forecast) against 51.40 (full foresight) and no mechanism, no decomposition, and
no statement of how much of Tier 1's case survives realistic operation. The only truth diagnostic in the
chapter is for the battery (18% / 69% of battery net gain). For a chapter whose question is "what does
prediction change", the missing decomposition is the main analytical gap: split the loss into commitment error
(4-day schedule from a 12 h model plus weekday means) and dispatch error (half-hour orders). Two runs suffice:
oracle commitment with forecast dispatch, and forecast commitment with realised dispatch.

### P1-2 Table III.1 compares A at 11 blocks with B at 9

Table III.1 shows `B: classifier 9` (net 6.57) while §3 says eleven blocks maximise the six-window mean "in
either policy" and Table III.2 reports B at 11 (6.83). Nine is Tier 1's full-information B optimum, not the
chapter's selection. As printed, the main table's scale comparison is A-11 versus B-9 and a reader cannot see
the recommended B capacity. Add the B 11-block row (or drop the 9-block row and label the Tier 1 reference).

### P1-3 Five of six windows' forecasts are fitted with later data, and the consequence is not stated

Printed p.7: "Each forecast fit has a separate test window and validation block. Earlier fits can use later
years. The 2025/26 forecast fit uses only earlier data." The disclosure is honest and the 2025/26-only fit is
named, but the reader is not told that the six-window mean is therefore an upper bound on real-time
performance, nor given the causal-window values side by side (A plant 15.36 net; one block +0.17; B +1.27).
One sentence fixes it; the conclusion survives on the causal window alone, which is worth saying.

### P1-4 The evidence package documents a reproduction path that is not in the repository

`README.md` sends the reader to "the adjacent FinalProject study directories". Those do not exist: at
`origin/main` there is no `tier2b-commitment-20-20261124`, `tier2b-six-fold-20261123`,
`tier2b-b-battery-only-20261124`, `tier1-xpress-full-20261124`, `tier2b-b-site-ordinal-20261122` or
`panels.npz`. `build_evidence.py` imports from all of them (`replay`, `site_model`, `halfhour`, `commitment`,
`data`, `continuous`, `solver_adapter`, `run`, `site_replay`). The archive `20261122-post-v2/volumes/*.zip.part*`
may contain them; I did not open it, so I cannot say the code is lost — only that the printed instructions
cannot be followed from the repository as published. The tables can still be checked (I checked them), but they
cannot be regenerated.

### P1-5 The audit claim is partly unsupported

Printed p.10: "checked against 192 sampled Xpress solutions and 48 enumerations." The 192 samples are present
(`xpress-dispatch-audit.csv`, 192 rows, blocks {1, 7, 12, 45} × 6 years × 8 slots). Within them: 9 rows where
the DP and Xpress orders differ, and 2 rows whose `status` is not 6 with an unexplained `xpress_gap` of 180.7
and 295.1 against ~1e-5 elsewhere. The 48 enumerations are not in the package. State the acceptance criterion
and either drop or explain the two non-optimal rows; drop "48 enumerations" or ship it.

### P1-6 The combined report will carry two Table III.1s and two one-block totals

v7.1's Section III (printed p.6) already prints a Table III.1 of six-window incremental gains at **12.5%**
(total 4.65 in A, 7.58 in B), and v7.1's closing paragraph (printed p.5) cites it: "One block gains £4.65m in A
and £7.58m in B over six forecast windows (Table III.1)". This chapter's Table III.1 is a different table at
**20%** (one block 4.63 and 7.57; 11 blocks 22.84 vs 22.99; 45 blocks −133.46 vs −134.08; B identical because
B has no electrolyser). The stub page also states "the 12.5% minimum load" where the chapter uses 20%.
Two tables with one number, two totals differing by £0.02–0.15m, and a cross-reference that will point at the
wrong object. Fix when merging: delete the stub, renumber, and label the 12.5% replay explicitly wherever it
survives (v7.1 Appendix C) as a floor sensitivity.

### P2 findings

1. `Unused (GWh)` is not comparable across policies: A's unused includes generation it declines to sell at
   non-positive prices, B always serves demand first. A 7,962 vs B 5,725 does not mean A wastes more (p.7
   §2.2). Split the two components or add a clause.
2. Renewable use needs its ratio: the six-module plant captures 28.7 GWh of a 2,911 GWh annual renewable
   surplus (~1%), and its 3.4 kt/yr of hydrogen (≈190 GWh of input) is mostly not surplus electricity. The
   "good use of renewable energy" leg of sustainability should say so (p.7 Table III.1, p.9).
3. `£97/kWh base cost` in Table III.4 is not derived on the page. It is Tier 1's £38.69m per 400 MWh block
   (=£96.7/kWh), not the brief's indicative €288,000/MWh (=£256/kWh). One clause, plus the note that at the
   brief's cost the deferral is stronger.
4. Table III.5's `Gen. (MWh) 1,453 / 929` does not say whether the error is per half-hour or summed over the
   24-slot path (price is £/MWh per slot). Define both.
5. The DP gives zero credit to closing stock and B drains the last 48 slots; final stock is 0 in every row.
   Disclosed, but the downward bias on storage value is not discussed. A closing-stock-floor variant would
   bound it.
6. Page economy: printed p.7 ends with roughly a third of the page empty while p.10 carries Table III.5 and
   the whole recommendation. On a 5+5 = 10-page report with no slack, that is a real cost. Also Fig III.3's
   "Other five windows" bars are too light, and Fig III.2's 2025/26 line is hard to separate from the
   all-window mean.
7. The chapter has no citations (D5). Four footnotes would carry it: brief parameter table, Lazard cost basis,
   day-ahead price source, forecast-model references already in the report list.
8. The DP recursion is described but not printed. At five pages this is defensible; two lines would make the
   method checkable.

## 4. What is genuinely strong

- Every printed number reproduces from the shipped tables (216/216). That is rare and it is the reason this
  review can be specific.
- Comparators are same-window and same-equipment: zero-battery replay per policy and window, a reactive rule,
  a previous-slot rule, and truth diagnostics. The chapter reports the result that hurts (the classifier loses
  to a one-line rule in 6/6 windows) and explains why (slot-weighted accuracy versus value-weighted errors).
- The recommendation is conditional and quantified: break-even capital £113/£123/kWh across six windows,
  £90/£92 without 2021/22, hydrogen break-even £4.28/kg, and an explicit statement that the seven- and
  22-block peaks come from a single window.
- The 2021/22 dependence is treated as the finding rather than buried: "evidence of a historical hedge … its
  future value depends on how often similar conditions occur and on the customer's downside tolerance"
  (p.8) is exactly the consulting judgement the brief asks for.
- Stress weeks are real historical episodes with observed conditions used for evaluation, and the mechanism
  (economic dispatch displacing valuable sales versus supply priority absorbing surplus) is given.

## 5. What would change the score

| Fix | Effect |
|:--|:--|
| Resolve P0-1 (rebuild or rescope the oracle) | D1 to A2, D4 up: 82–84 |
| Add the forecast-loss decomposition (P1-1) | D1/D4 up: +1–2 |
| Align B's block count in Table III.1 (P1-2) | D4 up: +1 |
| State the sampling regime and the 2025/26-only result (P1-3) | D6 up: +0.5–1 |
| Ship the five study directories and `panels.npz`, or state the archive steps (P1-4) | D6/D3 up: +1 |
| Four citations (P2-7) | D5 from C to A3: +2.5–3.5 on its own |
| Rebalance p.7/p.10 and fix figure contrast (P2-6) | D7 up: +1 |

Ceiling: with everything above, 87–89. I do not see a route to the mid-90s on five pages: the forecast
discussion (Table III.5) reports accuracy and value but never tests calibration, and the uncertainty of the
capacity choice is stated as sensitivity to one window rather than as a distribution over windows.

## 6. Limits of this review

- I verified the evidence tables, not the models. The DP, the rolling loop, the ridge/transformer fits and the
  classifier are not in the package; where the chapter makes claims about them (fold-specific refits,
  validation-based checkpoint selection, no look-ahead in the feature set) I record them as
  **author-reported**. What I could check about information sets is consistent: features are lagged by at least
  one slot and the truth paths appear only in labelled diagnostics.
- I did not open `20261122-post-v2/volumes/*.zip.part*`, so P1-4 is a statement about the published tree and
  instructions, not about whether the code exists somewhere.
- The 25/26 grade descriptors are the strongest rubric evidence available; no 2026/27 grid is published. The
  score is a review instrument, not an official grade.
- Page compliance holds only if this chapter replaces v7.1's Section III stub: Tier 1 printed pp.1–5 plus this
  chapter pp.6–10 is exactly 10 body pages. Appending it instead would breach the limit.

## 7. Cross-tier checklist for the combined report

1. Delete v7.1's Section III stub (printed p.6) and renumber this chapter's tables into the report sequence.
2. Label every surviving 12.5% figure (v7.1 Table III.1, Appendix C, closing paragraph) as a floor
   sensitivity, and change "£4.65m / £7.58m … (Table III.1)" to the 20% numbers with the right table.
3. Reconcile 13.46 / 11.95 / 51.40 for the six-module plant (P0-1) and state which the client should use.
4. Keep the 20% floor in both halves (the abstract already recommends "the brief's 20% minimum load").
5. Re-check the total: 10 body pages, no appendix dependence for the recommendation.
