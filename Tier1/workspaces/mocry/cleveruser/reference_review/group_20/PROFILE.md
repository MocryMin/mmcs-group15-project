# Profile — `Group_20.pdf` (2023, banking fraud investigation)

Source: `Tier1/public/reference/past_project_reports/20261103-v1/Group_20.pdf`, 18 PDF pages,
sha256 `db1341ff7be4a8f74fe6beedbba1070b245ec2dfdd63b6505c96439cbf15a0c1`, document `doc-033a3849b8a743f0bd3b8316d9346f03`.
Read: all 18 pages by page range; text extraction clean; pages 8 and 16 also rendered and viewed.

**Anchor convention:** `PDF p.N / printed p.M`, where printed = PDF − 3 (PDF p.4 carries the footer "1";
confirmed footers "4" on PDF p.7 and "5" on PDF p.8). Front matter = cover (PDF p.1), Executive Summary
(PDF p.2), Contents (PDF p.3). Body = printed pp.1–10, References p.11, Appendix pp.12–15.

Authors on cover: Daniel Kopisitskiy, Nicolas Talia, Teng Wei Yeo, Sara Brdnik; "Methodology, Modelling and
Consulting Skills", School of Mathematics, University of Edinburgh, November 2023 (PDF p.1).

## 1. Question and scope

- **Decision answered:** which transactions should a bank investigate on a given day, given a fixed
  investigation team and the option of paying external investigators, in order to minimise money lost to
  fraud (printed p.1). Framed as "a small-scale simulation of the UK banking system" with five banks A–E
  (printed p.1).
- **Client framing:** the task is attributed to an external brief, K. Searle / Sopra Steria (reference [5],
  printed p.11); the regulatory context is the 2024 APP-fraud reimbursement duty, with refunds and
  investigation costs split 50:50 between sending and receiving bank (printed p.1).
- **Two competing objectives are made explicit rather than averaged:** Model 1 optimises detection
  ("protecting customers and ensuring their trust"), Model 2 optimises net cost. The Executive Summary states
  the decision rule directly — "if the regulator prioritises catching frauds, it should use the first model.
  If the regulator prioritises costs, it should use the second model" (PDF p.2).
- **Stated assumptions:** only banks party to a transaction may investigate it; priority-4 cases (2 days of
  work) are simplified to 2 investigators working one day; 50:50 cost sharing unless the counterparty is
  international, the same bank, or declines; weights estimated on "perfect information" from previous days
  remain valid for the next day (printed pp.2–3); all cash withdrawals are assumed genuine (printed p.2);
  seasonality is compressed from 31 daily dummies to three month-parts (printed p.4, p.5).

## 2. Data

- **Source:** supplied course/client dataset only; no scraping and no external data collection is described.
  The report never states where the data came from, how large the file is, or that it is simulated — this is a
  real gap, because the transaction dates (Aug–Dec 2024, PDF p.8 figure axis) post-date the November 2023
  report.
- **Size (as evidenced in the tables, not in a data section):** test window 1 Aug–31 Dec 2024 =
  123,523 transactions containing 1,006 frauds (Table 4, printed p.4; Table 8, printed p.7); the same window is
  used for all comparisons. Full dataset used in §5.2 = 361,679 transactions, 3,487 frauds (Table 11,
  printed p.9). Training window 1 Oct 2023–31 Jul 2024 for the first test day (printed p.7), 180 days of
  history per rolling fit for Model 1 (printed p.4).
- **Fields:** transaction amount, 15–20 spending categories, four priority levels, day of month, plus three
  supplied probabilities — customer probability (constant per user, range [0.2, 0.9]), transaction probability
  [0.1, 0.8] and description probability [0.1, 0.9] (nomenclature, printed pp.14–15).
- **Cleaning/validation:** one paragraph only — cash withdrawals and money paid in were removed, "It is
  assumed that all withdrawals are genuine" (printed p.2). No missing-value handling, outlier treatment,
  class-imbalance handling, or train/test leakage discussion is given, despite a 0.81% fraud rate
  (1,006/123,523) that dominates the modelling problem.
- **Provenance/ethics:** not stated. No mention of anonymisation, GDPR, or the fact that the three supplied
  probabilities already embed bank-internal scoring. Fairness across banks is acknowledged only as future work
  (printed p.10).

## 3. Model

Two two-stage models; stage 1 estimates weights by regression/linear programme, stage 2 solves a small
integer programme for the day's investigation plan.

- **Model 1, stage 1 (printed pp.2–3):** multivariate linear regression / least squares classification,
  min Σ(sᵢ − ŝᵢ)² with ŝ a linear index in bank dummies, priority dummies, category dummies, day-of-month
  dummies and the three supplied probabilities, plus intercept. Explicitly OLS, not a logit.
- **Model 1, stage 2 (printed p.3):** binary ILP,
  max Σᵢ (aᵢ·qᵢ·x_{i,bf} − y_{i,bf}·E_p), with team-capacity constraint C1 (fractional person-days, halved
  when two banks share), joint-investigation symmetry (C2), 50:50 external split (C3), external-only-if-
  investigated linking (C4, C5), binaries (C6). `qᵢ` is a hand-tuned piecewise map of ŝ: 1 above 0.8,
  raw transaction probability in the middle band, 0 below a lower cut-off. **The lower cut-off is stated
  inconsistently** — "0 if ŝ < 0.3" in the display but "≤ 0.03" in the surrounding text (printed p.3), and the
  Executive Summary repeats 0.03 (PDF p.2).
- **Model 2, stage 1 (printed pp.5–6):** a linear programme whose decision variables are the weights
  themselves: min Σᵢ (1 − combinedᵢ)·sᵢ·aᵢ + Σ_{d,b,i} ext_{d,b,i}·Eᵢ, where combinedᵢ is a weighted index
  over amount, transaction probability, customer probability, 19 category dummies and three month-part
  dummies; constraints on expected time by bank/priority (D1–D3), boxes on combinedᵢ and the weights (D4–D5)
  and an ad-hoc cap w_c ≤ 0.9 on category weights (D6). Weights are bounded so the "probability" stays in
  [0,1]: this is weight-fitting by LP, not a calibrated classifier.
- **Model 2, stage 2 (printed pp.6–7):** candidate generation by Bernoulli sampling, Xⱼ ~ Bernoulli(combinedⱼ),
  then a small MIP min Σ_f (exttwo_f·E_f + (1 − y_f)·a_f) s.t. time allocation E1–E3. The sampling step is the
  device that lets the model cope with unobserved false negatives.
- **Stated size and solver:** "Python Xpress is used throughout" (printed p.2); Model 2 runs "approximately
  12,000 decision variables" (printed p.10). **No constraint counts, no runtimes, no solver version, no
  optimality gaps** anywhere — despite the claim that Model 1 is "more scalable, because it requires less
  computation time to train" (printed p.8), which is asserted with no numbers.

## 4. Analysis design

- **Evaluation protocol (the strongest design element):** rolling-origin backtest, one solve per calendar
  day for 153 days, retraining each day on all prior data; Model 1 uses a fixed 180-day training window
  (printed p.4), Model 2 an expanding window (printed p.7).
- **Naive benchmark:** only the do-nothing baseline, reported as "theoretical max loss" £350,328.25 in every
  balance sheet (Tables 5, 7, 13). There is no random-allocation, no priority-only, no "investigate largest
  transactions first" benchmark — so the value added over an obvious heuristic is never measured.
- **Ablation / robustness:** §5.3 (printed p.9) retrains Model 2 with false negatives hidden — the bank sees
  only outcomes of cases it actually investigated — starting from uninformative weights (w_cp = w_tp = 0.4).
  Because that path is stochastic, it is run 5 times and reported as mean ± SD (Table 13), and losses cut fall
  from 84.63% to 53.59% ± 15.58%. This is the single most methodologically interesting result in the report.
- **In-sample check:** §5.2 (printed p.8) fits on the whole dataset and applies it retrospectively. This is
  presented as a success but is in-sample; the drop from 84.63% to 73.13% is described as high, not as a
  warning sign.
- **Sensitivity analysis:** none in the formal sense. The 0.8 and 0.03/0.3 thresholds are "determined by
  analyzing the training dataset" (printed p.3) with no sweep, no curve, no stability check. Team sizes,
  external-investigator fees (Table 3: £40/60/100/150) and the 50:50 split rule are never varied.
- **"What would change the recommendation":** handled qualitatively through the two-model trade-off and the
  regulator's stated priority; there is no one-way sensitivity or break-even analysis that says how far
  hiring costs would have to move before Model 1 becomes preferable.

## 5. Results and presentation

- **KPI set:** theoretical maximum loss, value of detected scams, hiring cost, actual loss, proportion of
  losses cut (the headline metric), confusion-matrix counts, and success rate by priority band. All monetary
  results are in pounds and reconcile arithmetically (e.g. Model 1: 350,328 − 314,369.50 + 50,950 = 86,909,
  Table 5).
- **Counts:** 5 figures, 16 tables, 11 references. Table 1 in the Executive Summary duplicates Tables 5, 7
  and 13 — the summary table is a composite of three later tables with a mean/SD column grafted on, and it is
  hard to read (PDF p.2).
- **Figures (types):** Fig. 1 (PDF p.8) two stacked time-series panels — transactions and scams on dual axes,
  then daily fraud probability; Fig. 2 (PDF p.10), Fig. 3 (PDF p.11) and Fig. 4 (PDF p.12) are near-identical
  dual-line time charts of detected-scam value against cost+loss; Fig. 5 (PDF p.16, appendix) a Pareto bar
  chart with a cumulative-percentage overlay by category. **No maps, no heatmaps, no tornado diagrams, no
  marginal-value or threshold curves** — the report would have gained a lot from one threshold-sensitivity
  curve.
- **Executive summary style:** dense single page, no bullet list; leads with the regulatory problem, then
  "we have two models that satisfy different needs", then the identical/different structure of the two models,
  then Table 1, then "for elaboration … see the technical report" plus a private GitHub link (PDF p.2).
  Effective at stating a decision rule; bloated with mechanism the reader does not need.
- **Recommendation format:** conditional ("if the regulator prioritises X, use model Y"), plus one concrete
  operational recommendation — renegotiate external investigator prices, "especially priority 2 cases", because
  low-value fraud is left uninvestigated when the fraud value is below the investigation price (printed p.10).
- **Limitations stated:** no inter-bank fairness; the 0.9 category-weight cap is admitted to be
  non-performance-driven, chosen only to keep the model linear and less deterministic (printed p.10);
  Bernoulli sampling leaves internal capacity idle; external investigation time modelled as continuous
  "as a shorthand to preserve linearity" (printed p.10); sensitivity to parameter tuning; transaction
  description probability unused in Model 2 (printed p.10).

## 6. Structure and length

- Order: Cover → Executive Summary → Contents → 1 Introduction → 2 Problem (outline, data cleaning,
  modelling motivations) → 3 Model 1 → 4 Model 2 → 5 Discussion and Extensions (model comparison, full-data
  refit, no-false-negatives) → 6 Future Model Improvements → 7 Conclusion → References → Appendix A.
  This is a model-per-section structure, not a decision-first consulting structure.
- **Page allocation (printed):** Introduction + Problem 2 pp.; Model 1 2.5 pp. (pp.2–4); Model 2 3.5 pp.
  (pp.4–7); Discussion 2 pp. (pp.8–9); Future improvements + Conclusion 1 p. (p.10); References 1 p.;
  Appendix 4 pp. (pp.12–15). Appendix is 27% of printed pages and consists of a restated formulation (A.1),
  a weights table (A.2), the category chart (A.3) and two nomenclature tables (A.4, A.5).
- **References:** 11, numbered, IEEE-ish style with access dates; mix of regulator/press sources, one textbook
  chapter, one PhD thesis, and ML papers used only to motivate future work.
- **Formatting quality:** consistent LaTeX-like typesetting, but sub/superscripts in the maths are cramped and
  reflow badly (e.g. the C1 constraint on printed p.3 is barely readable), a chart in Fig. 2/3/4 has orphan
  axis labels ("60000 / 62000") from a secondary axis, and the appendix figure page is two-thirds white space
  (PDF p.16, seen in render). Typos exist: "costs are to be spit 50:50" (printed p.1). Table 10 is captioned
  "Balance sheet from model 1" although the section is a Model 2 full-data refit (printed p.9) — a real
  labelling error in the results block.

## 7. Level judgment

**Estimated band: Merit (roughly 65–72). Not a distinction on the evidence of the document.**

Strengths a marker would reward:
- Two genuinely different formulations (least-squares index + ILP; LP-fitted weights + sampled candidate
  generation + allocation MIP) rather than two cosmetic variants, with the difference in *what is optimised*
  stated up front.
- A real rolling-origin backtest over 153 days with daily retraining, and an explicit do-nothing baseline in
  every results table.
- The no-false-negatives experiment (§5.3) is a serious piece of modelling: it identifies the actual
  information asymmetry in the real problem, re-solves, and reports mean ± SD over 5 trials. That is the kind
  of "does the recommendation survive realistic information?" analysis the brief rewards.
- Honest limitations section, including the admission that a constraint was imposed for tractability rather
  than from the problem, and a concrete commercial recommendation (renegotiate investigator fees).
- Arithmetic in the balance sheets reconciles across all three variants, and confusion matrices are given so
  a reader can (as I did) derive precision/recall — Model 1 recall 557/1,006 ≈ 55%, precision 557/14,163 ≈ 4%;
  Model 2 recall 440/1,006 ≈ 44%, precision 440/12,884 ≈ 3%. Those figures are never stated by the authors,
  which is a presentation miss.

Weaknesses a marker would penalise:
- The decision threshold that drives Model 1 is stated as both 0.3 and 0.03 in the same subsection, and both
  constants are hand-tuned with no sensitivity curve. A distinction-level marker reads that as an
  unvalidated modelling choice, not a result.
- No data section in any real sense: no source, no size, no cleaning statistics, no class-imbalance strategy,
  no ethics/anonymisation note — for a fraud dataset that is a conspicuous omission.
- No runtimes, no model sizes beyond one "approximately 12,000 decision variables", no solver versions, no
  optimality gaps; the "Model 1 is faster" claim is unsupported.
- No proper sensitivity analysis anywhere: fees, team sizes, 50:50 split, training-window length and the
  threshold constants are all frozen, so "what would change the recommendation" is only answered by
  qualitative assertion.
- The headline model comparison is partly an artefact: Model 1's hiring cost is £50,950 against Model 2's
  £1,900 (Tables 5, 7) — a 27× difference that is never explained. That single parameter drives the
  "Model 2 saves more money" conclusion, and it is unexplained.
- Presentation defects: mis-captioned Table 10, a garbled composite Table 1, unreadable constraint typesetting,
  chart axis-label artefacts, and a two-thirds-empty appendix page.

Why not distinction: the report is competent and well structured, and §5.3 shows real modelling judgement, but
the core comparison rests on two hand-set thresholds and one unexplained cost parameter, with no sensitivity or
runtime evidence. Why comfortably above pass: the formulations are correct and non-trivial, the evaluation is
out-of-sample and rolling, and the results are internally consistent and decision-oriented.

## 8. Transferability to an energy-storage investment project

Reusable:
- **Two-objective framing with an explicit decision rule.** "If the regulator prioritises A, choose model X;
  if B, choose model Y" is exactly the shape an energy-storage investment recommendation needs (security of
  supply vs arbitrage return vs capex), and it is cheaper to write than a weighted objective.
- **The balance-sheet KPI table** (theoretical maximum, gains captured, operating cost, net position,
  percentage of the theoretical maximum captured) maps one-to-one onto storage: theoretical maximum arbitrage
  value with perfect foresight, value captured by the policy, degradation/cycle cost, net margin, % of
  perfect-foresight value captured. Adopt the table shape and the "% of an unattainable bound" normalisation.
- **Rolling-origin backtest with an explicit naive benchmark**, and especially **the "hidden-outcome" ablation**:
  in storage terms, the operator cannot observe what it would have earned on hours it did not bid, so a
  variant trained only on realised dispatch is a legitimate and impressive robustness device — with mean ± SD
  over repeated stochastic runs.
- **Success-rate-by-segment tables** (here by priority; for storage by season, price decile or asset) — a cheap
  way to show where performance actually comes from.
- **Pareto bar + cumulative curve** (Fig. 5) for showing concentration — directly reusable to show that a small
  number of hours or assets carry most of the value.

Not transferable:
- The 50:50 inter-bank reimbursement split, ATM/withdrawal filtering, and the Bernoulli sampling of "cases"
  are artefacts of the fraud setting.
- The MLR classifier stage and the three supplied bank probabilities have no storage analogue.
- The industry-specific regulator narrative (PSR, APP fraud) supplies the motivation only.

Cheapest single import: the "% of theoretical maximum captured" KPI with a hidden-outcome ablation. Most
important thing to do better: replace the hand-tuned thresholds with a swept parameter and a break-even chart.
