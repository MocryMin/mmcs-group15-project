# Independent Tier 2B evaluation standard (recorded before reading the Tier 2B preview)

Author: `mocry-cleveruser` (member `mocry`, human Ran Min).
Recorded: 2026-11-25, before opening any Tier 2B preview artefact.
Repository state at write time: `mmcs-review-20261122`, local `main` = `84471f6c8fd24ab65515c2e642f602d20c3dca7f`
(fast-forwarded from my `a01836f`; remote also contains `mocry-claude`'s Tier 2B outline and preview reviews).
Working copy is sparse; the Tier 2 codex workspace was materialised only to read the *request messages*.

**Audit target pinned at write time** (hashes computed by reading the file bytes, not by reading the content):

| Artefact | sha256 | Bytes | Git blob |
|:--|:--|--:|:--|
| `Tier2/workspaces/mocry/codex/technical-report/20261125-preview/tier2b-report-preview.pdf` | `5d03f59e8bf29ba4627f95eca49dd8c329fe8bfd56ee3cb7e7c8381a430a125b` | 118,822 | `a874b4727cb528c5d9debe1967b97764820f1c7a` |
| `…/tier2b-report-preview-source-and-evidence.zip` | `abf99335961b6301ce0643528958cd498615e120e7093568f151919c7e21486c` | 267,936 | `342110bd2194a1b1faf7709e19c0ca7336fe8031` |
| `…/SHA256SUMS.txt` | `380aaa66a4bdc633ae8a558a4f19e31d6dd45964aeef01403442577594b88272` | 204 | `b28fd98f0121599f0b8f351fd62925ea877d65b1` |
| `…/README.md` | `1721bf1fd7547d0d1d0b823ef24d3f5bdb27ff3b1dd30cf66c6d11f759fb1c53` | 2,757 | `4c715495dc1f92c26bebb7e4d5d7b358d7227002` |

**Independence statement.** Before this file was written I had *not* opened the preview PDF, the evidence zip,
the preview README, `mocry-claude`'s `20261125-tier2b-outline/REVIEW.md` or `20261125-tier2b-preview/REVIEW.md`,
or any Tier 2 result table. What I had read:
1. the whole 2026/27 `Project_Brief.pdf` (6 pages, extracted text plus the Tier 2B pages);
2. the whole course Q&A transcript (167 lines);
3. my own Tier 1 standard and its two addenda;
4. the two codex request messages (`03d22096…` outlines request, `537a9b2f…` preview request).

Point 4 needs to be stated plainly: those messages name the *planned* architecture (operating policies A and B,
a classifier, a capacity sweep, forecast metrics, "printed pages 6–10"), and the preview request lists the
specific quantities the author wants traced. Those are the author's plan and the author's self-chosen checks —
they are **not** course requirements and they set none of the criteria below. They did tell me two facts I use:
the chapter is five printed body pages inside a ten-page report, and the report as a whole must reconcile with
the Tier 1 v7.1 candidate. Everything in Sections A–C is derived from the brief, the transcript and the rubric.

Purpose: score the Tier 2B chapter against this year's course materials, produce a severity-ranked defect list
with printed-page/table/file locators, and state which findings could change the chapter's recommendation.

---

## 1. Why a Tier 2B standard is not the Tier 1 standard with more words

Tier 1 is a one-shot annual optimisation over a stylised day; perfect foresight is *legitimate* there and the
brief says so ("a simplified treatment of time", brief p.3). Tier 2B changes what "correct" means:

1. **The information set becomes part of the model.** A dispatch decision that uses the next day's realised
   wind is not "stronger", it is invalid. Look-ahead is the Tier 2B equivalent of a unit error in Tier 1.
2. **Chronology creates state.** A battery's state of charge crosses period boundaries; energy stored yesterday
   is a constraint today (brief p.4). Results therefore have to come from a simulated path, not from an
   independent-period optimisation.
3. **Averages stop being evidence.** The brief says an investment that looks attractive on annual averages may
   perform poorly in low-renewable, high-demand or prolonged-surplus periods (p.4). So a single annual number is
   not a result; the distribution over time, and the worst windows, are.
4. **The chapter is half a report.** Five body pages of ten. Page economy is a first-class criterion, and the
   chapter must pick up the Tier 1 position without re-arguing it.
5. **Supplementary course guidance becomes material.** The Q&A session told Tier 2B teams to start from
   published forecast data, re-solve the model every day with an updated forecast, and watch calibration and
   the drift between expected and actual (transcript lines 50 and 53). That is guidance, not a written rule —
   but it is the only course statement about how Tier 2B should be done, so it is scored as strong evidence.

## 2. Source hierarchy

| Rank | Source | Status | Use here | Limit |
|:--|:--|:--|:--|:--|
| 1 | `Project_Brief.pdf` (2026/27, 6 pp.) | Written brief | Binding requirements, parameters, client questions | Silent on page split between tiers, on forecast method, and on the marking grid |
| 2 | Course Q&A transcript, 2026-11-25 (167 lines) | Automatic transcription, not audio-checked | Teacher's Tier 2B method guidance (lines 50, 53); page-limit confirmation (line 167); hydrogen-price caveat (line 71) | Wording is machine-transcribed; I quote it as reported speech, not as a course document |
| 3 | MMCS 25/26 report grade descriptors | Course document, previous year | Seven dimensions, weights and anchor language (see `ADDENDUM_1`) | 25/26 vintage; no 2026/27 marking grid has been published |
| 4 | Owner clarifications (Ran Min) | Human owner decision | 10 body pages; abstract/contents/references/appendix excluded (`ADDENDUM_2`) | Now also corroborated by rank 2, line 160 |
| 5 | `PROJECT.md`, `Tier2/public/models/*`, codex's requests, other agents' reviews | Team documents and agent statements | Leads to check; scope of the request | Never evidence for a course requirement, never evidence that a claim is true |

Also rank 1 but easy to miss: the brief's own parameter table (p.6) is the *default* parameter set — 2-hour
battery, 90% round-trip, 20–80% usable, €0.288m/MWh, PEM 20–100%, 55.9 kWh/kg, £9.5/kg hydrogen. A report may
depart from these, but a departure has to be labelled and sourced; being different is not by itself a defect,
and being different silently is.

**Recorded discrepancy, so I do not mis-flag it later.** The Q&A speaker says "we said that you could sell
hydrogen for a constant price of 7.50 per kilogram" (line 71) while the brief's appendix says £9.5/kg and warns
that it is a policy-supported value, not a market price. The written brief governs the base case; the spoken
£7.50 is best read as evidence that the hydrogen price is *the* assumption to sensitise. I will not treat
either number as an error in a report that states its own choice and tests alternatives. The Q&A line is also
the course's own instruction to vary hydrogen value, which is already A11 below.

## 3. Section A — what the course actually requires of Tier 2B (checkable list)

Each item is a yes/no against the printed chapter plus the evidence package. "Evidenced" means a reader can
check it from the page or from a named file; a sentence that asserts a property without a mechanism is not
evidence. Locators: `p.N` = printed brief page; `T50` = Q&A transcript line 50.

| # | Requirement | Locator | Satisfied by | Not satisfied by |
|:--|:--|:--|:--|:--|
| A1 | The chronology of the supplied data is explicitly preserved; one day's decisions constrain later days | brief p.4 | A stated simulation over consecutive periods with carried state; period index tied to real dates | A per-period model relabelled "dynamic"; a full-window LP described as a strategy |
| A2 | Battery state of charge carries from one period to the next | p.4 | SOC recursion with initial/terminal condition and usable band | SOC that resets daily without saying so, or that is bounded only inside a period |
| A3 | The portfolio's performance is determined **day by day over time**, with the operating rule identified | p.4 | A path of decisions and outcomes; the rule written as a rule | One annual aggregate; "the optimiser decides" with no decision rule |
| A4 | Seasonal behaviour, prolonged high/low renewable periods, and unusually high demand or prices are investigated | p.4 | Named windows or quantiles with results in them | "We checked seasonality" with no numbers |
| A5 | Timing dependence of value: renewable value depends on availability relative to demand | p.4 | Value decomposed by period type (surplus/scarcity), not only annual totals | Annual-average-only valuation |
| A6 | The stress claim: an investment attractive on averages may fail in difficult periods | p.4 | The same asset/value compared in best and worst windows | A robustness sentence without a window comparison |
| A7 | Sustainability read on three axes: return on investment, good use of renewable energy, resilience | p.4 | All three addressed with numbers or explicit evidence | Only ROI; or "sustainability" as a paragraph of adjectives |
| A8 | Alternative demand, renewable, battery-cost, hydrogen-value and budget levels are tested; the assumptions that materially change the strategy are identified | p.4 | At least the decision-relevant subset, with thresholds | A single sensitivity chosen because it is cheap |
| A9 | The objective (or combination) is justified as the client's interest | p.4 | An argument linking objective to investor and system outcomes | "We maximised profit because profit matters" |
| A10 | Results make sense and are shown with appropriate visualisations | p.5 | Checks and figures that carry the argument | Decorative charts; figures whose message is unstated |
| A11 | The optimised solution is compared with simple alternatives | p.5 | Same-window, same-equipment comparators: no investment, and a plain operating rule | A straw man; a comparator in a different window |
| A12 | Sensitivity identifies the assumptions with the greatest influence | p.5 | Ordered influence with magnitudes or thresholds | One-at-a-time sweep with no ranking |
| A13 | Data-supported conclusions are separated from modelling assumptions | p.5 | Explicit labelling at the claim level, in the text or a table column | A general disclaimer in the introduction |
| A14 | The recommendation states what to invest in, how much, and why it beats a simpler strategy | p.5 | A decision paragraph with quantities | A menu of options |
| A15 | "What could cause the recommendation to change" is answered | p.2, p.5 | Thresholds, conditions, and the mechanism | "Results may change if assumptions change" |
| A16 | The chapter takes the inherited position as given and improves on it | p.2 | Continuity with the Tier 1 portfolio and its numbers | A Tier 2B that silently re-invests or re-sizes the Tier 1 assets without saying so |
| A17 | Depth, justification and interpretation beat feature count | p.3 | Fewer things, fully argued | A feature list |
| A18 | Senior-investor readability plus technical defensibility; main modelling work in Python/Xpress | p.1, p.2 | Plain decision language; solver/model provenance | Jargon-gated prose; a result with no model behind it |
| A19 | Start from forecasts available at the decision time | T50 | Forecast source/issue time stated; or an own model with a stated information set | "We use the actual values" |
| A20 | Re-solve the model every day (or period) with the updated forecast | T50, T53 | A rolling loop whose cadence is stated and whose outputs are the reported results | One solve at the start |
| A21 | Calibration of the predictive model is considered | T53 | Calibration evidence or an explicit statement of what is calibrated and how | Accuracy table only |
| A22 | Over time, the gap between expected and actual should shrink / be monitored | T53 | A time series of expected vs realised, and its trend | A single pooled error number |

A19–A22 are rank-2 evidence: a chapter that documents an equivalent discipline by another route (e.g., a
published day-ahead forecast with its own error statistics, and a rolling re-solve) satisfies the intent. They
are not a requirement to build a machine-learning model; the Q&A explicitly refuses to prescribe an approach.

## 4. Section B — the vague words, and the anchors I will actually apply

The brief asks for "a robust modelling methodology, clear assumptions, appropriate use of data and public
information, technical validation and a consulting style interpretation" (p.1). Those words decide marks and
carry no operational content. My anchors:

**B1 — "Consulting style" / professionalism.** Earns credit: decision first, quantity second, mechanism third,
caveat fourth; every comparator named by window, equipment and information set; units on every number; no
superlative without a number behind it; the recommendation survives being read alone. Loses credit: results
before the question; "significant" without magnitude; a comparator introduced after the conclusion; a
recommendation that requires the appendix. Anchor: a senior investor who reads only the recommendation and the
main table should be able to state what to buy, how much, what it earns, and what would change it.

**B2 — Analytical depth.** Earns credit: the mechanism is explained (where the money comes from: arbitrage
between periods, avoided unused generation, capture-price timing), the decomposition adds up, and the report
says why one policy beats another rather than that it does. Loses credit: more configurations instead of more
explanation; ablations that report only accuracy; a "driver" claimed without a counterfactual.

**B3 — Reproducibility.** Earns credit: shipped code, pinned inputs, seeds, window definitions, runtime, and a
README mapping each headline number to the file that produces it. Loses credit: a headline that exists only in
prose; a config referenced but absent; a run whose window cannot be reconstructed from the text.

**B4 — Expression and page economy.** Earns credit: each of the five pages has one job; figures legible at
print size; notation defined once; tables that a reader can compare down a column. Loses credit: a page that
repeats the previous page; a figure whose message is only in the caption; an appendix carrying a decision.

**B5 — Defensibility / robustness.** Earns credit: the recommendation is stated with the conditions under
which it holds, and at least one condition is quantified as a break-even. Loses credit: "robust" as an
adjective; a sensitivity that cannot move the decision.

**B6 — Honesty about what was known.** Earns credit: the report distinguishes, for each result, what was known
when the decision was made, what was assumed, and what was learned afterwards. Loses credit: any presentation
in which hindsight and foresight are merged, even if the numbers are individually correct. This is the Tier 2B
professionalism test, and it is the one I will apply most strictly.

**B7 — Proportion.** A five-page chapter is allowed to leave things out. Leaving out a requirement from
Section A is a deduction; leaving out a *nice-to-have* is not, provided the omission is not needed for the
claims that are made.

## 5. Section C — Tier 2B-specific probes

Each probe states the question, what an acceptable answer looks like, and the failure signature. `[M]` marks
probes I expect to check mechanically from the evidence package.

**C1 — Decision-time information set.** For each reported policy, what exactly was known at the moment of the
decision, and when was it known? Acceptable: a timeline (forecast issue → decision → execution → settlement)
and a feature list that respects it. Failure: a "forecast" that contains the target period's realised values,
or normalisation/scaling fitted on the full sample, or a stated horizon that the code does not honour `[M]`.

**C2 — Rolling mechanics.** Cadence of re-solve, planning horizon, executed block, terminal condition on SOC,
continuity across days, and what happens on infeasibility. Acceptable: these five stated, and reported results
produced by the loop. Failure: a full-window perfect-foresight optimum presented as the operating strategy;
free end-of-horizon energy; a battery that discharges before it charges; results whose window differs from the
stated one `[M]`.

**C3 — Split, folds and leakage.** How the data were divided in time, where hyperparameters were chosen, and
whether the capacity-selection window is the same as the reported out-of-sample window. Acceptable: explicit
temporal split with a rule for fold boundaries; selection on validation; the selection window and replay window
named separately. Failure: test-period tuning; overlapping folds called independent; capacity selected on the
same window that is then reported as performance.

**C4 — Baseline strength.** What is the comparison forecast and the comparison policy? Acceptable: persistence
(same half-hour previous day) and/or seasonal naive, plus a plain dispatch rule, with a skill score. Failure:
"better than random"; a baseline that is known to be weak; a baseline evaluated in a different period.

**C5 — Metric choice.** Which metric, on what scale, over which horizon, with what treatment of near-zero
denominators? Acceptable: metric matched to the economic use, per-fold dispersion shown, zero handling stated.
Failure: MAPE on near-zero generation; a single pooled number that hides fold variance; error in units that
cannot be converted to value.

**C6 — Forecast error → money.** What does forecast error cost? Acceptable: rolling policy vs the same policy
on a naive forecast, and the gap to a perfect-foresight bound, both on the same window and equipment. Failure:
quoting the perfect-foresight value as achievable; reporting accuracy and value in separate sections with no
link; a "value of forecasting" number that mixes information quality with capacity changes.

**C7 — Model selection and complexity.** What was compared, on which data, with what seed variance, and why
the chosen configuration? Acceptable: an ablation table whose rows change one thing, judged on both predictive
and realised-operating metrics. Failure: architecture shopping judged on accuracy alone; a selected model whose
advantage is inside run-to-run noise; hyperparameters from the test window.

**C8 — Comparator discipline and attribution.** Are gross operating gain, annualised capital cost and net gain
computed on the same window with the same equipment? Acceptable: a table whose rows differ in one dimension,
plus a decomposition of value that adds up. Failure: a rolling-with-battery row against a no-battery
perfect-foresight row; a net figure that annualises capital over a different period than the operating gain;
gross gain quoted as ROI.

**C9 — Recommendation robustness.** Is the chosen capacity stable across windows and folds, and what are the
break-even thresholds? Acceptable: a stability table and at least one quantified threshold for each assumption
that the brief says to vary. Failure: a single-window optimum presented as robust; a break-even asserted
without arithmetic `[M]`.

**C10 — Stress and edge behaviour.** Low-renewable days, high-price days, negative prices, prolonged surplus:
what does the policy do, and is that behaviour visible in the results? Acceptable: worst-window performance and
a mechanism. Failure: an average that hides collapse; a stress section that only repeats the annual number.

**C11 — Reproducibility of the Tier 2B pipeline.** Seeds, saved outputs, configs, runtime, dataset identity, and
whether the printed tables are generated by the shipped code. Failure: a number that cannot be regenerated
from the package.

**C12 — Claim-to-evidence mapping.** Every headline number mapped to a table row or file, marked
`recomputed` / `author-reported` / `contradicted` by me. Failure: a number that appears only in the PDF.

Chapter-level criteria and weights (diagnostic, used to organise evidence; the scored grade comes from the
rubric mapping in `ADDENDUM_1`):

| Criterion | Weight | Primary probes |
|:--|--:|:--|
| C1 Framing, continuity with Tier 1, decision statement | 10 | A16, A14, B1 |
| C2 Chronological operating model integrity | 18 | A1–A3, C2, C10 |
| C3 Information set, forecasting and calibration | 18 | A19–A22, C1, C3–C5 |
| C4 Comparator and economic attribution | 16 | A11, C6, C8, B2 |
| C5 Performance through time: stress, resilience, sensitivity | 14 | A4–A7, A12, C9, C10 |
| C6 Recommendation, thresholds and what would change it | 14 | A8, A13–A15, B5 |
| C7 Reproducibility and five-page presentation | 10 | A10, A18, C11–C12, B3, B4 |

## 6. Severity taxonomy

- **P0 — invalidates or misleads.** The conclusion does not follow, or the reader is misled about what was
  known: look-ahead in a reported policy; a comparator in a different window or with different equipment
  presented as like-for-like; a headline gain that annualises cost and energy over different periods; a
  capacity that cannot be reproduced from the package; a recommendation at a scale the evidence does not
  support. Effect: the mapped dimension(s) drop at most one full anchor step, and the defect must be fixed
  before submission.
- **P1 — material weakness.** A required element is missing or thin: no simple-alternative comparator, no
  break-even for a decision parameter, no temporal split statement, no stress window, an unsourced parameter,
  a metric that cannot support the claim. Effect: up to 40% of that criterion's weight lost.
- **P2 — clarity and polish.** Legibility, notation, dead space, caption-only messages, duplicated tables.
  Effect: up to 20%, not double-counted with the presentation dimension.

No double penalty: each defect is scored once, in its primary criterion, and cross-referenced elsewhere.
A defect that is only a matter of my taste (colour, density) is not P1/P2 unless it costs the reader content.

## 7. Audit protocol

1. Read the five printed pages end to end, in the client's order, noting claims without scoring.
2. Build a claim table: page, claim, value, unit, named source, status.
3. Open the evidence package; map every headline number to a file; recompute the identities that carry the
   argument (SOC recursion, energy balance, cost annualisation, gain decomposition, skill scores, capture and
   supply arithmetic).
4. Check the information-set claims against the shipped code (C1, C3, C7) — this is the one place where I
   inspect implementation rather than prose, because look-ahead is invisible in prose.
5. Render the printed pages and look at them: legibility, table craft, figure messages.
6. Score per `ADDENDUM_1`, write findings in severity order with locators and concrete corrections, then state
   which findings would change the score and which would change the recommendation.
7. Record what I could not verify; mark it `author-reported`, never as confirmed.

Where the chapter's own evidence contradicts its prose, the contradiction is the finding. Where the chapter is
silent and the evidence package answers, I record "silent in chapter, present in evidence" rather than either
passing or failing the requirement silently.

## 8. Score anchors

| Band | Meaning for a five-page Tier 2B chapter |
|:--|:--|
| A1 85–100 | Chronology real and validated; information set explicit and clean; comparators like-for-like; forecast error converted to money; recommendation with quantified break-evens; five pages each doing a job; every headline recomputable |
| A2 78–84 | As A1 with minor slips — one thin element, no misleading claim |
| A3 70–77 | Complete chain with one material but non-fatal weakness (e.g. one sensitivity missing, a stress section thin) |
| B 60–69 | Chronology present but partly cosmetic, or information set ambiguous, or comparators not like-for-like; several requirements thin |
| C 50–59 | Partial: results shown, but the chapter cannot support its recommendation; or a P0 that undermines a headline |
| D <50 | The client cannot act on the chapter, or the temporal claims are not actually tested |

The chapter score is a chapter score. It is not the report grade, and it will be re-aggregated with the Tier 1
half (and with cross-tier consistency) when a combined PDF exists.

## 9. Out of scope — things I will not penalise

- Not using machine learning, or not using a neural network. The course asks for forecasts available at
  decision time and a daily re-solve; a published forecast plus a rule-based policy is a legitimate answer.
- Not covering Tier 2A, or not testing every item in A8 when the chapter shows which ones can move the decision.
- Not reproducing the brief's default parameters, provided the departure is labelled and sourced.
- Not resolving Tier 1's open P2 items inside the Tier 2B chapter (they belong to the Tier 1 half), except where
  the chapter depends on the disputed number.
- Layout taste, prose register and section numbering, beyond legibility.

## 10. What would change my findings

- Evidence that the forecast features are computed only from data available before the decision (closes a
  leakage finding).
- A comparator table showing the same window and equipment for every row (closes a like-for-like finding).
- A shipped rerun that reproduces the printed table (converts `author-reported` to `recomputed`).
- A course document from 2026/27 that changes the page rule, the parameter defaults or the marking grid
  (supersedes the relevant section by addendum, not by silent edit).

Limits I accept now: I do not have the 2026/27 marking grid; I cannot audio-check the transcript; a five-page
chapter is judged on what it printed, so a good analysis that stayed in the appendix will read as thin — and I
will say so explicitly rather than infer the missing content.
