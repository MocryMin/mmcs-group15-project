# Independent content review of Tier 1 report v5

Reviewer: `mocry-cleveruser` (member `mocry`, human Ran Min). Review date: 2026-11-22.
Target: `Tier1/workspaces/mocry/codex/technical-report-latex/20261122-v5/report.pdf`
Source digest: sha256 `7b8a9fa573796be5ad80bc0844d8d8cf88efb7a68a07a9cf0b1451db46cc4e72`, 130,116 bytes, 14 PDF pages, pinned by the notice to `98b316f`.
Standard: recorded first and pushed before the PDF was opened — `review/20261122-tier1-independent-standard/STANDARD.md` (`871c4e3`) and `ADDENDUM_1_OFFICIAL_RUBRIC.md` (`40eac2e`). Scoring follows the course's seven-dimension "MMCS 25/26 Reports: Dissertation Grade Descriptors" (weights 1:1:1:1:1:1:2), with the caveat that it predates the 2026/27 brief.
Independence: I did not read `mocry-claude`'s standard, their v5 review, or their v4.1 review as evidence. Where our findings coincide, that is independent convergence, not borrowing.

## How the report was read

All 14 PDF pages were read in full through text extraction (42,719 characters), and pages 1, 5, 6, 7, 8, 13 and 14 were also inspected as rendered images (title/abstract; equations (II.1)–(II.7); Table II.3; Table II.4 + Figure II.1; Chapter III equations; Appendix B.3–B.4; Table C.1). Algebra was re-derived from the report's own printed values with `recompute_checks.py` (43 checks, `checks.json`). The published v5 directory contains only `report.pdf`, so no optimisation result could be recomputed from code; those findings are labelled **author-reported**.

Page references below give PDF page / printed page (e.g. "PDF 6 / p.4").

## Headline judgement

The report is a serious, well-instrumented piece of work: half-hour reconstruction from upstream records, an integer MILP with module counts and minimum load, annual-equivalent costing, break-even and window re-optimisation, a Xpress feasibility replay, and an explicit data-quality section. Its weakness is not arithmetic but **the distance between what is proved and what is recommended**. The battery value and the six-year joint sizing are computed on a 4.25 GW electrolysis fleet selling ~492.5 kt H₂/yr at a policy support price (≈87% of reported UK 2022 consumption), while the recommendation is 40–55 MW of electrolysis plus one 100 MW block. The report never reports the battery's value at the recommended configuration, and its own evidence shows that the implementable simple rule loses money and that the 2-hour reference menu buys no storage.

**Rubric-mapped score: 73 / 100 (band 69–77, A3-low). Non-official.** Fixing the two P0 items and the P1 item on the 2-hour/4-hour basis would plausibly move it to 77–80; fixing only wording would not.

| Dimension (weight) | Anchor | Fraction | Main reason |
|:--|:--|--:|:--|
| Understanding & Depth (1) | A3 | 0.78 | Advanced model correctly applied; errors few, mostly minor (currency factor, 827/845) |
| Originality (1) | A3 | 0.78 | Several methodological ideas; no identifiable "outside the box" element the teacher asked for |
| Amount of Work (1) | A3 | 0.78 | All core brief questions addressed; brief's £9.5 benchmark case and demand/generation scenarios absent |
| Logic of Argument (1) | C | 0.55 | Recommendation does not follow from the evidence at the recommended scale; oracle-only battery value; per-slot vs daily cap |
| Background & References (1) | A3 | 0.78 | Appropriate primary sources; internal "package" refs unresolvable; one source misnamed |
| Validity of Results (1) | B | 0.65 | Strong validation machinery, but headline validity depends on admitted-unverified eligibility and an unreported scale change |
| Presentation (2) | A3 | 0.78 | Clean, legible, numbered; one figure, wasted title page, page-limit ambiguity |

Weighted: (0.78×4 + 0.55 + 0.65 + 0.78×2) / 8 = 73.5 → **73**.

## Claim status table (headline numbers)

| Claim (locator) | Value | Status |
|:--|:--|:--|
| Calendar 2020-01-01..2026-09-17; Tier 1 2,192 days; 105,216 half-hours (PDF 3/p.1, PDF 4/p.2) | 2,452 / 2,192 / 105,216 | **Recomputed** — exact |
| Module input 90 kg/h at 55.9 kWh/kg (Table II.2) | 5.031 MW | **Recomputed** — 5.031 MW |
| 845 / 362 modules → MW (PDF 6/p.4) | 4,251.195 / 1,821.222 MW | **Recomputed** — exact |
| Broad-market capital £6.247bn / £2.698bn (PDF 6/p.4) | 6.246 / 2.697 £bn | **Recomputed** — within rounding |
| Battery annual cost £4.695m (Table II.2) | 4.694 £m | **Recomputed** — annuity + 2.5% |
| Payback 5.8 / 8.2 yr (PDF 7/p.5) | 5.85 / 8.25 | **Recomputed** — but from perfect-foresight cash |
| Break-even £156 / £117 per kWh (PDF 7/p.5) | 156.3 / 116.6 | **Recomputed** — exact |
| 4% maintenance gains £2.311m / £0.383m (PDF 7/p.5) | 2.311 / 0.384 | **Recomputed** — exact |
| Battery gains +£2.891m / +£0.964m; simple rule −£2.605m / −£0.938m (Table II.3) | consistent | **Recomputed** — table deltas exact |
| £7.80/kg → ≈£140/MWh (PDF 6/p.4) | £139.53/MWh | **Recomputed** |
| HAR1 £241/MWh = £175/MWh (2012) → £7.799/kg (2020) (PDF 12/A3) | 7.799 | **Recomputed**; strike identity verified in the DESNZ HAR1 notice |
| Battery capital $62.15m → £38.690m (PDF 12/A3–A4) | implies 0.6225, not the stated 0.635 | **Contradicted** by stated factor (P1-4) |
| Electrolyser $2,300/kW → £1.46m/MW at 0.635 (PDF 13/A4) | 1.4605 | **Recomputed** — uses 0.635 |
| Energy attribution 4,221 / 4,536 (A), 2,857 / 2,857 (B) GWh/yr (PDF 6/p.4) | table deltas 4,505 / 2,812 | **Not reconcilable** as printed (P2-1) |
| 827-module A plan (PDF 13/A4) vs 845 modules (PDF 6/p.4) | 827 vs 845 | **Internal mismatch** (P2-2) |
| Site cases 15.1/20.1 MW, 40.2/55.3 MW, gains 14.10/5.48, 4.96/1.19, 21.79/9.49 (PDF 6/p.4; Table C.1) | internally coherent when back-solved | **Author-reported**; implied opportunity cost £39–88/MWh |
| 492.5 / 50.6 kt H₂/yr; 1,559 t/day UK ceiling; 569,024 t 2022 (PDF 12/A3) | 1,559 t/day = 569,035 t/yr | **Recomputed**; EHO dataset existence verified, exact UK row not independently read |
| "Positive physical surplus in 24.75% of half-hours; 5,165 GWh/yr" | — | **Author-reported** (no data in package) |
| Xpress replay differences £4/yr (A), £73/yr (B); gap bounds £3,945/£670 per year | — | **Author-reported** (no solver logs) |

## Findings

### P0-1 — The headline battery/electrolysis scale is not the recommended scale

**Locators:** abstract (PDF 1), §5.1 and Table II.3 (PDF 6/p.4), §5.2 buyer-size paragraph (PDF 6/p.4), §5.4 (PDF 7/p.5), Table C.1 (PDF 14/A5).
**Evidence:** the "common equipment case" holds 845 modules = 4,251.195 MW electrolysis (A) and 362 = 1,821.222 MW (B); broad-market output is 492.5 kt/yr, i.e. 87% of the report's own UK 2022 consumption figure (569,024 t). Table II.3 and the abstract therefore quote battery increments (£2.891m/£0.964m) and electrolysis gains (£1,689.96m/£118.38m) at a nationally scaled, support-price-dependent fleet. §5.4 then recommends "size electrolysis to secured offtake" at 40–55 MW and "quote one battery block". The battery increment at 40–55 MW electrolysis (or at zero electrolysis) is nowhere reported; neither is the capital or payback of the 40–55 MW case.
**Why this matters:** the client is told a battery is worth £2.9m/yr, then told to buy assets at 1% of the scale that produced that number. That is a recommendation at a scale the evidence does not support (my standard's P0 definition), even though every individual table is internally correct.
**Fix (cheap, one table):** add a battery-increment column at (i) the 10 t/day site configuration and (ii) electrolysis-only zero, with the same capital/throughput conventions; move the national-scale figures to an "upper-bound screening" table and label them as such in the abstract.

### P0-2 — The battery is only positive under perfect foresight; the payback is an oracle number

**Locators:** Table II.3 (PDF 6/p.4); §5.1 simple-rule paragraph; §5.4 first paragraph; Figure II.1.
**Evidence:** with an implementable simple rule the battery loses £2.605m/yr (A) and £0.938m/yr (B); only the full-foresight replay yields +£2.891m/+£0.964m. The quoted payback (5.8/8.2 yr) divides capital by the full-foresight operating cash (7.586/5.659 £m minus maintenance). The break-even thresholds (£156/£117 per kWh) are likewise computed from that oracle cash.
**Why this matters:** an investor reading "payback 5.8 years" will not infer "only if you can dispatch with perfect knowledge of the next 30 minutes". The report does say "validate dispatch value on later data before purchase", which is the right condition, but the abstract and §5.4 headline do not carry it.
**Fix:** label the payback as an upper bound; give the implementable-rule payback (negative) or a forecast-based range from Chapter III once available; put one sentence in the abstract: "the block is justified only if dispatch value approaches the perfect-information bound or the installed quote is below £156/£117 per kWh."

### P1-1 — Main case uses a 4-hour battery although the brief specifies a 2-hour battery; the compliant menu buys none

**Locators:** Table II.2 and surrounding text (PDF 4/p.2); §5.3 (PDF 7/p.5); Appendix C.2 (PDF 14/A5); brief p.3 and p.6.
**Evidence:** brief: "For battery storage, use a standard 2-hour battery… €0.288 million per MWh… capacity to build should be a decision variable." The main storage case is a 100 MW/400 MWh four-hour Lazard block at £96.72/kWh; the two-hour product menu (Sungrow/Huawei/Megapack with DEA-scaled cost) selects zero storage in both policies. TC-08's reported permission covers researched *parameters and prices*, not the asset duration; the report itself says the two-hour menu is "the brief's two-hour reference".
**Fix:** make the 2-hour case the Tier 1 base case and the 4-hour block a labelled extension with an explicit justification (or a written course clarification). If 4 hours is retained as the headline, the abstract must say the brief's 2-hour reference yields zero storage.

### P1-2 — The main sizing is not shown to be an Xpress model, although the brief requires it

**Locators:** §4.2 "Joint sizing is checked against HiGHS bounds" (PDF 5/p.3); Appendix C.1 "Xpress Community replay … blocks of up to four days"; C.2 "bounds from capacity relaxations or decomposition" (PDF 14/A5).
**Evidence:** brief p.1: "The main modelling work should be implemented in Python using the Xpress optimiser." The body reports Xpress only for the fixed-configuration replay and the site cases; the six-year joint sizing and the archived feasible plans are described as HiGHS-derived, without saying why. No model size, solver status, runtime or MIP gap is reported for any run.
**Fix:** one short "solver evidence" table: formulation size, solver and version, status, gap, runtime, per experiment; plus a sentence explaining the HiGHS/Xpress split (e.g. Community licence limits and the 4-day decomposition). If the split is a licence constraint, say so and cite the course licence note.

### P1-3 — Two battery gains for the same block (per-slot vs daily cap), and the payback uses the favourable one

**Locators:** §4.2 "allocated as L/48 kg per interval" (PDF 5/p.3); Table II.3 £2.891m; Appendix C.1 "flexible daily cap … £2.513m/year and £0.964m/year" (PDF 14/A5).
**Evidence:** A's one-block gain is £2.891m under the L/48 per-slot cap and £2.513m under the flexible daily cap, which Appendix C calls "the specification for the joint investment and site-contract studies". The payback (5.8 yr) uses the £2.891m version. B is unaffected (its per-slot cap does not bind).
**Fix:** one configuration for the headline; report the other as a sensitivity; if the daily cap is the contract specification, the payback becomes ≈6.2 yr (recomputed: (38.69+0.006)/(7.208−0.967)).

### P1-4 — Currency conversion factor contradicts the battery capital

**Locators:** Appendix B.2 low/mid/high totals (PDF 12/A3); B.4 "conversion factor is 0.635 in 2020 pounds per 2024 dollar" (PDF 13/A4); Table II.2 £38.690m (PDF 4/p.2).
**Evidence:** $62.15m × 0.635 = £39.47m, but the block costs £38.690m; $111.32m × 0.635 = £70.69m (≈£176.7/kWh) vs stated £173.25/kWh; $160.49m × 0.635 = £101.9m vs stated capital consistent with £249.77/kWh (£99.9m). All three battery totals imply **0.6225**, while the electrolyser £1.46m/MW uses **0.635** (2,300 × 0.635). So the two equipment families are converted with different factors and the report states only one.
**Fix:** publish the factor per source and year; recompute all capital, payback and break-even numbers with the corrected factor (a ~2% shift, but it moves break-even thresholds and the payback).

### P1-5 — The brief's £9.5/kg benchmark is never run; £7.80 is correct but not connected

**Locators:** Table II.1 and §2 (PDF 4/p.2); Appendix B.1 (PDF 12/A3); brief p.3/p.6.
**Evidence:** the brief gives £9.5/kg as the core scenario (£241/MWh × 39.4 kWh/kg) and asks for lower/higher tests. The report uses £7.80/kg (HAR1 £175/MWh in 2012 prices deflated to 2020, verified as the same strike), then £5 and £10. It never reports the £9.5 case, and never shows numerically that £7.80 is the 2020-price equivalent of the brief's support value. A reader can think the report simply ignored the brief's benchmark.
**Fix:** add the £9.5/kg row to Table C.1 (cheap: the model already covers £10), and one sentence in §2: "the brief's £9.5/kg (its stated price basis) ≈ £7.80/kg at 2020 prices, the basis used throughout."

### P1-6 — Support-price revenue applied to hydrogen whose eligibility the report admits it cannot establish

**Locators:** Appendix B.3.1 (PDF 13/A4); B.1 (PDF 12/A3); brief p.3/p.6.
**Evidence:** "the system mix, including fossil generation, is insufficient to establish low-carbon hydrogen eligibility". HAR1 support is conditional on an LCHA contract and eligibility (verified in the DESNZ notice); EHO defines clean hydrogen as <3.38 kg CO₂/kg H₂. The report nevertheless values all hydrogen at the HAR1 netback, with "no additional non-electricity deduction".
**Fix:** split the netback: eligible volume at the support price, remainder at a merchant price; report the blended value and the share of output that must be eligible for the recommendation to hold. At £5/kg the site case remains positive, so this is a valuation haircut, not necessarily a reversal — but the client must see it.

### P1-7 — Traceability: the cited "accompanying package" is not in the published v5 artefact

**Locators:** references [3], [9], [10], [12], [17], [18], [19] (PDF 9/R1); §4.2 numerical checks; Appendix C.
**Evidence:** the v5 directory contains only `report.pdf` (`git ls-tree` confirms a single file). Six references point to an "accompanying package", two to "commit 53e3b50", but no path, hash or manifest is given in the PDF, and [12]/[17]/[18]/[19] are undated working archives. Solver logs, schedules and cash flows that would let a reader recompute the headline are therefore not reachable from the published artefact.
**Fix:** pin the package (path + sha256) in the review notice and in the PDF; add a one-page artefact manifest with file names and hashes.

### P1-8 — Page-limit compliance is unresolved (14 physical pages vs a 10-page limit)

**Locators:** PDF page count 14 (front i–ii; body 1–6; R1; A1–A5); transcript line 236 ("this has a 10-page limit"); `GAPS.md` Q-section.
**Evidence:** the report has 6 numbered body pages, which is within 10 on a body-only reading, but 14 physical pages. The course has no written statement on whether references/appendices count (the transcript's appendix remark at line 230 concerns the earlier six-page assignment). `PROJECT.md` records the same open point.
**Fix:** obtain a written course answer, or compress to 10 physical pages (move Table C.1 into the body if appendices are not read, per the teacher's own warning at line 233).

### P1-9 — Demand service falls under policy A and the loss is reported but not valued

**Locators:** Table II.3 "Demand served" column; §5.2 first paragraph (PDF 6/p.4).
**Evidence:** A's demand served falls from 89.66% to 80.57% (−9.1 pp) while hydrogen revenue rises; the gain is a scheme surplus, not a system benefit. The report reports the metric honestly but does not state whether the client owns a supply obligation or what unserved demand costs, and the abstract presents the gain without this trade-off.
**Fix:** one sentence in the abstract and one in §5.4: "A's gain assumes the client may divert sales and leave demand unserved; if the client has a supply obligation, the value is X." Optionally price unserved demand at the market price (already implicitly the foregone revenue).

### P2 findings (clarity/polish, not double-counted)

- **P2-1 Energy attribution numbers** (§5.2): "joint plans take up 4,221 (A) and 2,857 (B) GWh/yr… leave 4,536 and 2,857 GWh/yr less unused". Table II.3 deltas are 4,505 and 2,812; A's take-up (4,221) and less-unused (4,536) differ by 315 in the same sentence; B's 2,857 appears twice. State which plan and baseline each number refers to.
- **P2-2 827 vs 845 modules** (Appendix B.3.1 vs body): explain that 827 is the flexible-daily-cap optimum and 845 the per-slot one.
- **P2-3 References:** [14] "National Laboratory of the Rockies" should be the National Renewable Energy Laboratory (the text uses the correct name in B.2); [3]/[10] cite commit `53e3b50` for artefacts not introduced there.
- **P2-4 Title page:** no author/member names; abstract sits on the title page with ~60% white space; a contents page follows. Use the space or merge front matter.
- **P2-5 Single figure:** one bar chart in the body; the brief asks for appropriate visualisations and the sensitivity story is table-only. A second figure (surplus duration or capital/value frontier) would help.
- **P2-6 35 price days vs 30 omitted dates:** explain the overlap (incomplete vs missing).
- **P2-7 "one nominal cycle per calendar day"** uses nominal energy E while usable stock is 60% of nominal; state that this permits up to ~1.67 usable cycles/day.
- **P2-8 Chapter III equation (III.1)** is cramped at printed size; split the arg-min and the fitted-value clause.
- **P2-9 "£175/MWh benchmark"** in B.1 reads as a competing benchmark; call it "HAR1 strike expressed in 2012 prices".

## What the report does well (so the fixes are not confused with a weak submission)

- Data audit is specific and falsifiable: 107 zero-fuel dates, 42 zero-solar dates, midnight endpoints, 349 Tuesday demand endpoints, 115,571 zero-volume provider records, 1 January 2020 price change, 2 August 2022 636 MW block, plus held-out MAE checks. This is the strongest part of the report and exceeds what the past exemplars show.
- The model is honest about its own simplifications: no imports, no delivery charge, no hydrogen storage, capacity at start, zero residual, 5% real discount, L/48 vs flexible cap both reported.
- The break-even/quote discipline ("require an installed quote below £156/£117 per kWh, then validate on later data") is exactly the consulting behaviour the brief asks for.
- Startup/minimum-run sensitivity (827 modules, £14.24m/yr; 56-hour longest surplus vs 96-hour block) is a genuinely useful finding for a contract appraisal.
- The report resists claiming low-carbon eligibility and says so.

## Gap follow-up (process, not evidence for the score)

- Codex's archived disposition (`tier1-candidate-20261107-v4.1-academic/review/history-v3/FEEDBACK_DISPOSITION.md`) confirms the £49.543/yr maximum difference between the 14 independent annual cases and their exact enumeration, and retains 4.614536 £/kg against my 4.62285 (0.18%). They attribute the gap to exact enumeration with `miprelcutoff=0`, report a +£7,138/yr gain at £4.618/kg for a fixed 20 MW case, and explicitly do not adopt my earlier explanation. I have not independently reproduced either threshold in this round; the 4.62285 vs 4.614536 discrepancy and the 0.005% / +£7.47m items from my earlier cross-check remain **unresolved**, not confirmed.
- The v5 abstract/§5.1 numbers differ from the v4.1-era figures (four-hour block, 845 modules, 105,216 half-hours, 492.5 kt/yr). They are internally consistent with each other except where listed above.
- `mocry-claude` published a standard and a v5 review on 22 November. I have not used them as evidence; where findings overlap (scale, eligibility, per-slot cap), that is independent convergence.

## What would change my score

- Upward: a battery-increment table at the site scale (P0-1); an implementable-rule or forecast-based payback (P0-2); a 2-hour base case with 4-hour as extension (P1-1); corrected conversion factor (P1-4); the £9.5 row (P1-5); eligibility haircut (P1-6); a pinned package with solver table (P1-7/P1-2).
- Downward: if the 10-page limit is confirmed to count physical pages, D7 and D3 both lose and the score drops ~3 points; if the marker treats the 2-hour battery as mandatory, P1-1 escalates to P0 and the score drops ~4 more.

## Artefacts

- `recompute_checks.py`, `checks.json` — 43 arithmetic checks, 4 failures (conversion factor ×3, module count ×1), 8 informational back-solves.
- Visual inspection record: pages 1, 5, 6, 7, 8, 13, 14 rendered at 1.6× and viewed; no illegible figure/table found; layout notes in P2-4/P2-8.
