# Profile — Group_8.pdf (year not stated on cover; banking fraud detection, 15 PDF pp)

Evidence basis: `document_open` on `Tier1/public/reference/past_project_reports/20261103-v1/Group_8.pdf`
(sha256 `0a8d4ab54bba1412fc1c33fcc471218144438bd60560f0761d311cb1a8e5e487`, 15 pages, text extracted,
`heading_count=0` / `block_count=0`). Full extracted text read page by page via `document_read`; a `find` for
"Reference" over the whole text returned no matches (so the absence of a reference list is established on
extracted text, not on a visual check). Layout and figure legibility were **not** visually inspected.

Page convention: three unnumbered front pages (cover, Executive Summary, Contents), so
**printed page = PDF page − 3**. Both are given where it matters.

## 1. Question and scope

- **Decision answered:** on each day, which suspect transactions a bank should investigate, and whether each is
  handled by in-house or external investigators, given capacity, priority time requirements and next-day staffing
  knock-on — with a learning layer that sharpens the fraud probabilities feeding the decision.
- **Client framing:** a bank or banking group inside "a small-scale simulation of the UK banking system"
  (printed p.1) with several banks, each with in-house investigators. The client is referenced explicitly once
  functionally: the cap on external investigators is "requested by our client" (printed p.3). There is no named
  consultancy, no stakeholder map, no engagement narrative. The cover (PDF p.1) gives a title, "Operational Research
  MSc / Methodology, Modelling and Consulting Skills", and four author names — no institution, no date, no year.
- **Stated objectives (printed p.1), three of them:** (1) formulate an optimisation problem minimising expected
  fraud losses plus investigation cost under constraints; (2) devise a learning strategy exploiting historical data;
  (3) assess performance on the second batch and where only investigated-case information is available.
- **Stated assumptions (printed p.3), four plus one implicit:**
  - fraud is an unauthorised *outflow*, so incomes and cash withdrawals are excluded from investigation;
  - a bank only investigates transactions it is party to (shared when both parties are UK banks);
  - an investigation cannot be split between an external and another investigator (external fees are per case);
  - external investigators per bank ≤ in-house investigators per bank (client requirement).
  - Implicit and consequential: in-house investigator time is costed at **zero** — the glossary defines investigation
    cost as the external hire cost, "in case the transaction is not investigated or investigated by internal team,
    the cost is zero" (printed p.1). Every "money saved" KPI inherits this.

## 2. Data

- **Source:** a supplied-style simulation of the UK banking system; the report never names the data provider, the
  generator, or file characteristics. External data is used only for context (a Police Scotland statistic, footnote
  1, printed p.1) and one behavioural citation on repeat victimisation (Snyder & Golladay 2024, footnote 2,
  printed p.5).
- **Structure:** two batches — "first batch data (also called 'training set')" and "second batch (also called 'test
  set')" (PDF p.2). Each transaction carries a fraud probability decomposed into customer, transactional and
  description probabilities (printed p.1), an amount, a priority class 1–4, a time requirement, and bank
  involvement. Calibration uses "the information from October, 2023" (printed p.5) — the year is stated once and
  never reconciled with the test-period discussion.
- **Size:** never stated directly. Derived from the Appendix 6.1 crosstabs (printed pp.11–12): Model 1's table sums
  to 526 + 19,114 + 1,955 + 216,562 = **238,157** first-batch transactions; Model 3's out-of-time table sums to
  733 + 19,450 + 273 + 103,067 = **123,523** second-batch transactions. These totals are my arithmetic, not the
  report's.
- **Cleaning/validation:** the "cleaning" is model-side and is the analytical core — a daily risk threshold removes
  low-probability transactions before optimisation; a reliability diagram (Fig. 2) diagnoses mis-calibration; four
  amount bins at roughly the 25th/50th/75th percentiles (£45/£75/£120) are calibrated separately. There is no
  duplicate/missing-value treatment, no fraud-rate descriptive table, and no data appendix.
- **Ethics/provenance:** none. For a report that scores individual customers on scam likelihood and adjusts those
  scores using victimisation history, the total silence on data protection, fairness or disparate impact is a
  visible gap.

## 3. Model

- **Optimisation:** stated as a "Linear Programming (LP) problem" (printed p.3) with binary x_i (investigate),
  binary y_{ib} (external investigator from bank b), continuous z_{ib} (in-house investigation time, fraction of a
  day). Objective (printed p.4): maximise Σ_i p_i·a_i·x_i − Σ_i Σ_b c_{k_i}·y_{ib} — expected recovered amount minus
  external investigation fees. Nine numbered constraints: y ≤ x; y ≤ r_{ib} (only involved banks); z ≤ tk_i·r_{ib};
  Σ_b z_{ib} = tk_i·x_i; per-bank in-house capacity Σ_i(z_{ib} − tk_i·y_{ib}) ≤ f_b − u_b; external headcount
  Σ_i y_{ib} ≤ f_b; at most one external per case plus tk_i·y_{ib} ≤ z_{ib} (no split); priority-4 control
  Σ_{i:k=4}(z_{ib} − y_{ib}) ≤ f_b − m_b with m_b = ½f_b; non-negativity.
- **Honest self-assessment inside the model:** constraint 8 is annotated "Results show that this constraint do not
  matter due to the low amount of suspicious priority 4 transactions" (printed p.4) — good practice, rare in these
  reports.
- **Learning layer (printed pp.5–6), three mechanisms:**
  1. dynamic threshold = min(75th percentile of non-fraud probabilities, 25th percentile of fraud probabilities),
     updated daily, initialised at 0.05 to admit more transactions on day 1;
  2. weekly customer-probability update: for customers with ≥1 prior scam, replace the base probability with the
     conditional probability of being scammed again, estimated within probability bands;
  3. monthly calibration by "Regression of observed on estimated values (ROE)",
     Y_ROE = α_ROE + β_ROE·Y_pred, fitted on 5%-wide probability bins with log-normalised dependent variable, then
     exponentiated and capped at 1, run separately per amount bin.
- **Size, solver, language, runtime: not stated anywhere.** No row/column counts, no solver name, no modelling
  language, no solve times — for a daily LP over ~20,000–44,000 investigated candidates with 5 banks this is a real
  omission, and there is no discussion of whether the LP is integral or needs branching.
- **Model/report mismatch:** the objective is expected *net gain*, but the results are reported as success rates and
  "money saved"; the model's own expected gain is never compared with realised outcomes.

## 4. Analysis design

- **A genuine ablation ladder (the report's main analytical asset):** Model 1 baseline (no learning) → Model 2
  (+ customer-probability adjustment) → Model 3 (+ calibration). Same LP, same data, one change at a time.
- **Out-of-time validation:** parameters frozen on batch 1, re-run on batch 2 (Table 5, printed p.8).
- **Information-constrained stress test:** the model re-run assuming only investigated cases are known, i.e. no
  false-negative labels — the realistic deployment case (Section 4.2, printed p.9).
- **Segment decomposition:** every result is cut three ways — by priority, by home bank, by transaction amount bin —
  in both batches and both information regimes (Tables 2–4, 6–8, 10–12, 14–16). This is systematic.
- **Benchmarks:** Model 1 acts as the naive comparator; per-priority "success targets" of 50/60/70/80% are shown
  alongside achieved rates (Tables 6, 14), apparently client-agreed targets (source not stated).
- **Sensitivity:** none. The 75/25 percentile rule, the 0.05 seed threshold, m_b = ½f_b, the four amount bins and
  the external-cost schedule are all fixed and never varied. No scenario on fraud-rate drift or investigation
  capacity. No confidence intervals on any success rate (with ~1,800 frauds in batch 1, sampling error on 75.5% is
  roughly ±2pp — the report never says so).
- **"What would change the recommendation":** absent as an explicit analysis, though the paper does explain observed
  changes after the fact (test-set mean scam amount £348 vs £102 on the training set, printed p.8; Bank A fraud rate
  0.5% → 0.6%, printed p.9). Those are post-hoc explanations, not pre-specified switch points.

## 5. Results and presentation

- **KPIs:** success rate on cases (recall over fraudulent transactions); success rate on £; number and cost of
  external investigations; money saved. Headline: Model 3 75.5% of fraud cases and 77.3% of £ at 108 external cases
  and £10,800, versus 21.2%/48.6% (Model 1) and 32.6%/62.9% (Model 2) at 500 external cases and £50,000 each
  (Table 1, printed p.7). Out-of-time: 72.9% cases / 55.0% £ with zero external hires (Table 5, printed p.8).
  Limited-information: 40.7% cases / 45.5% £ on batch 1, 39.9% / 43.0% on batch 2 (Tables 9, 13).
- **Figures: 2. Tables: 16 numbered**, plus five unnumbered confusion-matrix style crosstabs in the appendix.
  Fig. 1 = process flowchart of the daily loop with the Model 1/2/3 branch points (printed p.2) — genuinely useful;
  Fig. 2 = reliability diagram, predicted vs observed fraud probability, with the 45° reference line and four amount
  bins (printed p.6) — the single best exhibit in the report, because it *diagnoses* rather than reports.
  Everything else is tabular: no bar chart of model comparison, no cumulative-gain or lift curve, no heatmap, no
  time series, no capacity-utilisation chart. For a study whose whole story is "better ranking of a large queue",
  the absence of a cumulative-gains curve is the biggest presentational miss.
- **Executive summary:** one page, dense, number-first, structured as model-by-model narrative then a 3-item findings
  list (PDF p.2). It does promote the training-set numbers as headline (75.5%) and buries the deployment-case 40%
  in paragraph four; the ordering flatters the result.
- **Recommendation format:** none. There is no "we recommend Model 3, run monthly calibration, cap external hires at
  X" statement with owner or timing; the conclusion (printed p.10) restates findings.
- **Limitations/discussion:** no section. There are candid explanations of performance drops and an admission that
  the model is "not meeting all success criteria" (printed p.10), but no consolidated threats-to-validity list. The
  zero-cost in-house labour assumption is never revisited even though it drives "money saved".

## 6. Structure and length

- **Order:** cover → Executive Summary → Contents → 1 Introduction (with 1.1 Main terms) → 2 Objectives →
  3 Solution Approach (3.1 overview, 3.2 assumptions, 3.3 optimisation model, 3.4 learning model) → 4 Results
  (4.1 all information available, 4.2 only investigated cases known) → 5 Conclusion → 6 Appendix (6.1 detailed
  results). Printed pp.1–12.
- **Page allocation (12 printed pages):** introduction/objectives ≈1.5, approach and models ≈4, results ≈3.5,
  conclusion ≈0.7, appendix ≈1.5. Reasonable balance; no literature review at all.
- **Appendix content:** the only appendix is five sets of crosstabs (fraud/not-fraud × investigated/not) for each
  model variant, in counts and £. No parameter table, no code, no per-day output, no robustness output.
- **References: zero.** Two footnotes carry the entire external evidence base (a Police Scotland statistic and
  Snyder & Golladay 2024). There is no literature review section, so no citations for LP-based fraud screening,
  calibration/ROE, or NBV-style cost-sensitive detection. As a marker-facing artefact this is the report's most
  obvious formal failure.
- **Formatting:** plain LaTeX, no institutional identity; headers hyphenate badly ("Success tar-get, cases",
  Tables 6 and 14; "Home Bank" columns split); appendix matrices lose their column alignment in the source; the
  cover has no date or year, which is why the README records the year as unstated. Section numbering is consistent
  and the writing is clear.

## 7. Level judgment

**Band estimate: Merit (upper end of merit; a distinction would need references, solver evidence and two charts).**

Strengths a marker would reward:
- A clean, controlled ablation ladder on one LP with one change at a time — the correct experimental design and
  better than most reports in this collection manage.
- Validation that goes beyond the usual: out-of-time test set *and* an information-poor regime that mimics
  deployment without false-negative labels (printed p.9), with honest reporting of the drop from 75.5% to 40.7%.
- Diagnostics with a purpose: the reliability diagram motivates the calibration step and the four-bin split is
  derived from amount percentiles rather than picked arbitrarily.
- Operational realism inside the constraints: in-house vs external split, per-case fees, next-day staffing impact of
  two-day priority-4 investigations, dependency cap on external hires.
- Segment-by-segment reporting (priority, bank, amount) so a reader can see where the gain comes from — the £0–45
  bin going from 0% to 76.6% detection (Table 4) is a genuinely interesting finding, properly evidenced.

Weaknesses a marker would penalise:
- **No references and no literature review.** Sixteen tables and zero citations of the fraud-detection/OR literature.
- **No solver, no model size, no runtime.** The reader cannot judge whether a 20,000-variable daily LP is
  implementable; no gap, no integrality discussion.
- **No sensitivity analysis** on any of the five fixed design parameters, and no uncertainty bands on success rates.
- In-house investigator time valued at zero, so "money saved" and the model's objective are both optimistic — never
  discussed, though it is a one-line fix.
- Presentation is table-heavy with two figures and no lift/cumulative-gains curve; the results chapter reads as a
  dump of outputs rather than an argument.
- No consolidated limitations section and no decision-shaped recommendation; the executive summary leads with the
  training-set number.
- No ethics/data-protection discussion for customer-level scoring.

Why merit: the analysis design is genuinely good and the reported numbers are internally coherent; what holds it
back is scholarly apparatus (references), engineering evidence (solver/runtime), and communication (visuals,
recommendation). Those are exactly the things a distinction rewards.

## 8. Transferability to an energy-storage investment project

Reusable:
- **The staged ablation ladder is the transferable backbone.** Model 1 naive → Model 2 + one mechanism → Model 3 +
  another, all on an identical instance, with a single KPI table. Energy version: no-investment comparator →
  investment with a simple rule-based dispatch → investment with optimised dispatch → investment with forecast
  uncertainty/rolling re-optimisation. The brief explicitly demands comparison "against simpler/no-investment
  alternatives", and this report shows how to present that as an escalating ladder rather than one number.
- **Out-of-time validation and an information-poor regime.** Freeze parameters on an early period, test on a later
  period, then re-test under the information actually available at decision time. Direct analogue: calibrate
  battery/electrolyser value on 2020–2023 prices and test on 2024–2026, then re-run assuming only day-ahead prices
  are known (no perfect foresight). This is the cheapest credible answer to "validate your results".
- **Segment decomposition of every KPI** (here priority/bank/amount): energy version by asset, by season, by price
  decile. It converts one aggregate number into evidence.
- **Reliability/calibration diagram** (predicted vs observed with the 45° line): reuse for forecast calibration —
  wind output or price forecasts against realised, which the brief's "validate results" requirement invites.
- **Reservation-capacity logic in constraints** (external ≤ in-house; next-day staffing): the pattern "resource A
  cannot exceed resource B, and today's assignment consumes tomorrow's capacity" transfers to cycling limits, state
  of charge carried across days, and maintenance windows.
- **The KPI quartet** (hit rate on cases, hit rate on value, resource used, net benefit) adapts to (MWh cycled,
  £/MWh captured, capacity used, net present value).

Not transferable:
- The fraud-probability decomposition (customer × transaction × description), the percentile threshold rule and the
  ROE calibration machinery — these are classification-specific and would be replaced by price/output forecasting
  and scenario generation.
- The investigation-cost structure (per-case external fees) has no storage analogue.
- The executive-summary habit of leading with the most favourable sample: do not copy this.
