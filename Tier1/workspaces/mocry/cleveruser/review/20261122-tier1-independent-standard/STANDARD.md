# Independent Tier 1 evaluation standard (recorded before reading report v5)

Author: `mocry-cleveruser` (member `mocry`, human Ran Min).
Recorded: 2026-11-22, local time 17:39 (Europe/London 17:39 GMT? — the machine clock; treat as GMT unless corrected).
Repository state used: public `main` at `401111c` ("Default new collaborators to a summary-only checkout"), clone `mmcs-review-20261122` (blob-filtered, sparse).
Audit target fixed at write time: `Tier1/workspaces/mocry/codex/technical-report-latex/20261122-v5/report.pdf`, blob `a69c330c03aaed7a2e027215986d9281008b8744`, 130,116 bytes, public notice commit `16f3630`/`98b316f`.
Independence statement: this standard was written before I opened the v5 PDF or the public v5 review notice. I have not read `mocry-claude`'s standard (`9d86960`), their v5 review (`489d723`), or their critique of v4.1 as inputs. Their texts remain "another agent's statement", usable only as a lead to check, never as evidence for my own findings.

Purpose: score the report's **content** against this year's course materials, not against any other agent's opinion, and produce a severity-ranked list of defects with page/equation evidence and concrete fixes.

---

## 1. Source hierarchy and how each source is used

Course materials disagree in status. I keep four provenance labels and rank them strictly, following the convention already recorded in `Tier1/public/baseline_1103/TEACHER_CLARIFICATIONS.md`:

| Rank | Source | Status | Use |
|:--|:--|:--|:--|
| 1 | `Project_Brief.pdf` (6 pages) | **Written** brief | Binding requirements, parameters, client questions |
| 2 | `Project_Launch_Transcript_Timed.txt` | **Transcript** (automatic transcription, not audio-checked; see `PROJECT.md`) | Teacher's stated expectations where the brief is silent (page limit, what earns credit) — treated as strong but not verbatim-audited |
| 3 | `TEACHER_CLARIFICATIONS.md` TC-08 | **Reported discussion** (owner's report of a teacher conversation; no recording) | Only where the report departs from written defaults; a departure needs a source, not this note alone |
| 4 | `TEACHER_CLARIFICATIONS.md`, `GAPS.md`, `BASELINE_1103.md` | **Our interpretation / team decisions** | Never binding on the author; a team convention cannot be scored as a course requirement |
| 5 | `261026_MMCS_Project_Overview.pptx`, `mmcs_presentation_25_26_descriptors.pdf` | Course launch slides and the 25/26 **presentation** grade descriptors | Pitch expectations; "no formulae/code" applies to the presentation only. Descriptors inform the readability criterion, not the report's march |
| 6 | `Tier1/public/reference/past_project_reports/20261103-v1/` (6 reports, 93 pages) | Prior years' exemplars, different topics | Evidence of accepted practice (solver evidence, staged validation, switching-point tables); **not** a page allowance or template for 2026/27 (its own README says so) |

Where the brief is silent (report front matter, references, appendices counting), the standard records the silence rather than inventing a rule. `GAPS.md` Q-section already states that the detailed marking grid, cover/reference counting and appendix rules are unresolved and must not be silently converted into a teacher rule. The one page statement available is the teacher's "this has a 10-page limit" (transcript line 236).

## 2. Hard constraints and gates

These are scored once, in C7, and flagged separately as compliance risks. A gate failure is not automatically a zero.

- **G1 Length.** The technical report is limited to **10 pages**. The transcript does not say whether cover, contents and references count (line 236; the six-page/appendix discussion at lines 230–233 concerns the earlier Assignment 2). Conservative reading: **10 physical pages is safe; more than 10 needs a written course rule**, and an unsourced narrowing ("references don't count") is a P0 compliance risk, not a fact.
- **G2 Where the model must live.** The teacher calls the technical report "the bible of your solution" and warns against parking "your integer programming formulation in the appendix" (transcript lines 233, 107). Therefore the formulations, domains, integrality, parameter values and solver evidence that carry the recommendation must be in the body, not only in an appendix or in code. Careful: this is a *content-location* rule; the appendix itself is not asserted to be ungraded for this project.
- **G3 Code is not graded, but numbers must be reproducible.** "We will never look at the code" (transcript lines 113–116). Consequence for an auditor: the submission must ship the artefacts (code, inputs, results) from which the headline numbers can be recomputed; a number that exists only in prose is "author-reported", not verified.
- **G4 Data honesty.** The supplied system is constructed and UK-scale, the wind-farm series is a simulation under dated weather (brief p.2; transcript lines 248, 254; TC-01/TC-02). Claims about actual Scottish curtailment, network deliverability or a specific site are out of scope unless separately evidenced.
- **G5 Honest valuation.** £9.5/kg is "a UK policy supported hydrogen value … rather than a guaranteed commercial selling price" (brief p.3 and p.6), traceable as £241/MWh × 39.4 kWh/kg ≈ £9.5/kg (brief p.6). A report that presents it as a market price, or that prices policy support without checking eligibility, loses credibility.
- **G6 Senior-investor readability.** "Your recommendations should be understandable to a senior investor as well as technically defensible" (brief p.2). A decision statement (what, how much, why better, what would change it) must be extractable without reading the algebra.

## 3. Criteria and weights

Total 100. Content carries 80; presentation and compliance 20. Within each criterion the score is a fraction of the weight, judged from evidence, not from how impressive the machinery looks.

### C1 — Problem framing and the client decision (12)

*Earns credit:* the Tier 1 decision is posed as an investment question (how much battery and/or electrolyser, and whether the added value justifies the capital — brief p.3); the inherited infrastructure is stated; the objective is justified as the client's interest, not merely convenient (brief p.4: "explain why your chosen objective … represents the client's interests"); the reader can see what a "no new investment" world means (brief p.5; transcript line 137: baseline = "what happens now … without any change").

*Loses credit:* objective switching without explanation; conflating Tier 1 with generation investment (that is Tier 2A, brief p.3); framing that quietly assumes a market or contract that is not in the materials; a decision question that only the model can answer, not the client.

*Evidence required:* decision statement in the opening pages; explicit comparator; explicit objective with units.

### C2 — Model formulation and implementation integrity (20)

*Earns credit:* a complete, dimensionally consistent formulation in the body: decision variables with domains and integrality, energy/capacity conversion for the 2-hour battery and the 20–100% electrolyser, SOC 20–80%, 90% round trip, 55.9 kWh/kg, per-period balance, capacity limits that actually bind the offtake route, and a stated treatment of "simplified time" appropriate to Tier 1 (brief p.3); a solver run with status, model size and gap evidence (transcript lines 104, 143; exemplars' solver-evidence practice); a feasible solution ("you need to have something that runs … and produces results", line 104).

*Loses credit (severity examples):* printed equations whose units do not balance (a capacity in MWh constrained by a tonnes-per-day quantity without the kWh/kg factor); a variable documented as "days in the year" when the code uses sampled years; missing domains/integrality; a headline "optimal" capacity that the code never bounds; solver claims without status; a model that cannot be re-run from the artefacts.

*Rule:* equations are judged as printed, not as the code probably meant. A printed-formula defect is still a defect even if the code is right; but its severity depends on whether the printed form misleads a reader about the recommendation (then P0) or is a typesetting slip with the correct values in the text (then P1).

### C3 — Data treatment, assumptions and provenance (16)

*Earns credit:* the five supplied series are described and reconciled (total vs fuel rows not double-counted, brief p.2; PROJECT.md); the daily MW→MWh convention is stated; missing/duplicate days and the sample window are disclosed with the resulting denominator (years or days); every replaced or added parameter (costs, efficiencies, prices, 1.5 MW/3 MWh, 10 t/day, 55.9 L/10⁶) carries a source, a price year, a currency and a scope (CAPEX boundary), and a departure from the brief's default is labelled as a departure (TC-08/TC-09: permission to research parameters is not a blanket permission for every parameter); assumptions are separated from data-supported conclusions (brief p.5).

*Loses credit:* a parameter whose source is "the brief" when it is the team's scenario; a price year mixed with today's £; unstated denominator behind a percentage; silent addition of a new market outlet or offtake contract; "reported in Section 7" style references that do not exist.

*Evidence required:* parameter register with source column; a sample-window statement; checkable arithmetic for every derived unit.

### C4 — Results validity and traceability (16)

*Earns credit:* every headline number (capacity, energy captured, tonnes, revenue, cost, NPV, payback, share of surplus) is recomputable from the submitted code and inputs; internal identities hold (energy balance, cash-flow annualisation, capacity ↔ cost, £/kg ↔ £/MWh ↔ kWh/kg); results are presented at the scale the recommendation actually uses; sensitivity numbers move in the direction the physics implies.

*Loses credit:* a headline computed at one scale while the recommendation uses another (e.g., national-scale module counts in the table, a 10 t/day offtake in the text); percentages whose numerator and denominator come from different years; payback/NPV quoted with inconsistent discounting or currency year; "zero battery" claimed without the matching comparator.

*Rule:* I recompute from the author's own artefacts where possible, and mark anything I cannot recompute as **author-reported**. If a headline number cannot be recomputed, C4 is capped at 70% of its weight.

### C5 — Comparison, sensitivity and what would change the recommendation (16)

*Earns credit:* the optimised solution is compared with simple alternatives (brief p.5: "Compare the optimised solution with simple alternatives"), at minimum a no-investment baseline and a plain operating rule; the assumptions with the greatest influence are identified, with numbers, through sensitivity (brief p.5; transcript lines 122, 128); switching points/thresholds are reported (hydrogen value, electrolyser cost, offtake scale, surplus hours) rather than discussed qualitatively; the report says "what could cause the recommendation to change" (brief p.5) — including the assumption set, not only a tornado chart.

*Loses credit:* a sensitivity section that varies only the parameter the model is least sensitive to; one-at-a-time sensitivity with no combined-stress case; comparisons against a straw man; a "robust" claim with no stress test.

### C6 — Recommendation, risk and sustainability judgement (12)

*Earns credit:* a single, unambiguous recommendation (invest/do not invest, how much, which asset mix, why better than the simpler strategy — brief p.5); payback/ROI framing ("show me how long I need to wait until I get to the break-even point", transcript lines 95–98); risk and resilience discussed ("risk profiling is also a very important element", line 134; sustainability includes resilience, brief p.4); at least one non-mainstream, defensible suggestion (line 149), provided it is evidenced and not a distraction; limitations stated honestly.

*Loses credit:* a menu of options with no decision; a recommendation whose feasibility depends on an unreported assumption; ROI without capital cost; an "outside the box" idea that replaces analysis.

### C7 — Presentation, compliance and readability (8)

*Earns credit:* within the 10-page gate; body contains the model; figures legible at printed size with units and sources; tables not padded with zeros; language plain enough for a senior investor (brief p.2); the report reads as an audit trail of the pitch (transcript line 107).

*Loses credit:* appendix-dependent core results; >10 pages without a written rule; mislabelled axes; references that do not resolve; figures that cannot be read in print.

## 4. Severity taxonomy and deduction rules

- **P0 — invalidates or misleads.** A defect that makes a stated conclusion unsupported or wrong for the client: a unit/identity error that changes a headline number; a recommendation at a scale the evidence does not support; an eligibility/valuation claim contradicted by its own appendix; >10 pages without a written rule; an unrecomputable headline. Effect: the primary criterion is capped at **50%** of its weight until fixed; the defect must be fixed before submission.
- **P1 — material weakness.** A required element is missing or too thin: no no-investment comparator, no sensitivity to a decision parameter, no solver evidence, missing domains/integrality in print, a parameter without a source, a citation that does not resolve. Effect: up to **40%** of that criterion's weight lost.
- **P2 — clarity and polish.** Legibility, notation, dead space, redundant tables. Effect: up to **20%**, and not double-counted with C7.

No double penalty: each defect is scored in exactly one primary criterion and cross-referenced elsewhere. Style preferences I hold personally (colour, density, layout taste) are not P1/P2 unless they cost the reader content.

## 5. Audit protocol (what "independent" means here)

1. Read the report once, end to end, in the body order the client would read it; note claims on first pass without scoring.
2. Extract every headline number into a claim table: page, claim, value, unit, source it names, and status (`recomputed` / `author-reported` / `contradicted`).
3. Recompute the Tier 1 identities from the submission's own code and inputs (energy balance, capacity↔cost, hydrogen↔electricity, cash-flow annualisation, payback, NPV, surplus share, sample window). I may reuse my own model only as an independent second implementation, never as the author's evidence; agreement between two of my own fixtures is not external truth.
4. Check the 3–5 parameters that carry the recommendation against primary sources named by the report (price basis, equipment cost, efficiency, offtake scale, policy eligibility). Where the report's own appendices contradict its body, the contradiction is the finding.
5. Judge each criterion against §3, record deductions with severity, then sum. Report the score as a band (±4) and state which findings, if fixed, would move it.
6. Record explicitly which findings are mine, and which claims I could not verify; never import another agent's conclusion as evidence.

## 6. Score anchors

| Band | Meaning in this project |
|:--|:--|
| A1 85–100 | All essential points, in detail, level right for a senior investor; every headline recomputable; switching points and stress tests present; a defensible outside-the-box element; audit trail complete |
| A2 78–84 | As A1 with minor slips; one required element thin but present; no misleading claim |
| A3 70–77 | Clear account; all essential points covered; some redundant material; one material but non-fatal weakness (e.g., sensitivity limited, one parameter unsourced) |
| B 60–69 | Adequate account; several essential points thin or at too high a level; analysis mostly accurate; a required comparison or the decision statement is weak |
| C 50–59 | Partial account; most essential points present but under-explained; irrelevant material or a P0 defect that undermines a headline conclusion |
| D <50 | Essential points missing or the content obscured; the client cannot act on the report |

Final score = Σ (criterion fraction × weight), after caps. The score is advisory and non-official (`GAPS.md` Q: no marking grid supplied).

## 7. Out of scope

Tier 2A vs 2B route choice; group process/division of labour; aesthetics I happen to prefer; defects in earlier versions already fixed (a fixed defect is not re-scored, but a regression is); the pitch deck (scored by the descriptors, not by this standard).

## 8. Falsifiers — what would change my judgement

- A written course rule that references/cover do not count toward the 10 pages, or a different limit.
- Evidence that the 10 t/day offtake or the module grid is a supplied course input (then C3/C4 treatment flips from "unsourced scenario" to "given").
- A primary source that supports the hydrogen eligibility at the carbon intensity the report assumes (then the valuation objection falls).
- A recomputation showing the headline numbers reproduce exactly at the recommended scale (then C4 rises).

## 9. Checklist used against the report (30 questions)

Framing: 1 decision question stated? 2 inherited infrastructure? 3 objective justified? 4 no-invest comparator defined? 5 route separation (Tier 1 only)?

Model: 6 domains/integrality? 7 battery energy↔power? 8 SOC 20–80? 9 round trip 90%? 10 electrolyser 20–100% and shutdown? 11 55.9 kWh/kg used with units? 12 period balance? 13 capacity limits bind offtake? 14 time simplification declared? 15 solver status/size/gap? 16 reproducible run?

Data/assumptions: 17 five series reconciled? 18 MW→MWh convention? 19 sample window and denominator? 20 missing days disclosed? 21 parameter register with sources/price year/currency? 22 departures labelled? 23 data vs assumption separated?

Results: 24 headline numbers recomputable? 25 scale consistent with recommendation? 26 energy/cash identities hold? 27 percentages share a denominator? 28 surplus share correct?

Comparison: 29 simple alternative comparison? 30 sensitivity with numbers? 31 switching points? 32 what flips the decision?

Recommendation: 33 single recommendation? 34 payback/NPV consistent? 35 risk/resilience? 36 outside-the-box evidenced? 37 limitations stated?

Compliance: 38 ≤10 pages or written rule? 39 model in body? 40 figures legible and sourced? 41 references resolve? 42 senior-investor readable?

(Forty-two questions; the numbering is a checklist, not a score.)

## 10. Receipt

- Standard file committed before opening v5: see the commit that adds this file; its message records the pre-read state.
- Target blob at write time: `a69c330c03aaed7a2e027215986d9281008b8744`; report page count, hashes and claim table are recorded in the later review directory.
- Any change to weights or gates after the audit starts must be recorded as an addendum with a reason, not retrofitted silently.
