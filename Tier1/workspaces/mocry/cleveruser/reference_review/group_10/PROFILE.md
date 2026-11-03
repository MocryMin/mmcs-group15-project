# Profile — Group_10.pdf (2024, TV scheduling and advertising, 14 PDF pp)

Evidence basis: `document_open` on `Tier1/public/reference/past_project_reports/20261103-v1/Group_10.pdf`
(sha256 `8c8e836c9e9a265123e738321278ec861fc110fb1715ad69f19ef719879e147f`, 14 pages, text extracted,
`heading_count=0` / `block_count=0` — no structural index available), then `document_read` over every page.
The complete extracted text was delivered. Layout and figure legibility were **not** visually inspected; all
judgements about visuals below come from captions, axis text and page position only.

Page convention: this report has two unnumbered front pages (i = abstract, ii = contents), so
**printed page = PDF page − 2**. Both are given where it matters.

## 1. Question and scope

- **Decision answered:** which movies to license and place on which day/slot on "Channel A" over a three-month
  horizon, and which advertisement slots to buy on three rival channels, in order to maximise viewership-derived
  profit. The stated aim (printed p.1, PDF p.3) is a "strategic model that enhances movie scheduling and
  advertising slot allocation".
- **Client framing:** "Channel A" versus "three main competitors" (printed p.1). There is no consultancy identity,
  no named stakeholder, no stated client success criteria, and no client-supplied constraint set. The report reads
  as a course exercise, not a consulting engagement: the cover (PDF p.1) says only "MMCS Report", four author
  names, and "November 29, 2024".
- **Stated assumptions:** a "simulated dataset representing a competitive environment of four TV channels"
  (PDF p.1 abstract); conversions from rival audiences are "exclusively attributed to Channel A" and Channel A's own
  slots are "marketed on the open market" (printed p.7); licence fee is "dependent on the movie budget and movie
  revenue" (printed p.2) but the functional form is never given; CPM fixed at 15.04/1000 taken from a Statista
  source (printed p.7); a self-imposed "fair pricing" band of ±£50,000 against the competitor average (printed p.4)
  that is asserted, not derived.
- **Not stated:** budget ceiling as an input (the budget is an *output*: "a total budget of £32.81 million is
  required", printed p.10), planning horizon justification, or who the decision-maker is within Channel A.

## 2. Data

- **Source:** simulated, supplied-style dataset. No file names, row counts, generator description, licence terms or
  provenance statement anywhere; there is no data appendix. Nothing is scraped or downloaded except the single CPM
  citation.
- **Shape (from the model's index sets, printed p.2):** 84 days (Oct–Dec), 204 five-minute slots per day, 34
  thirty-minute slots per day, 5,919 candidate movies, 3 competitor channels, 3 demographic groups
  (children/adult/retirees), and a genre set. Rival viewership is supplied as "10 given data sets of true
  viewcount" per channel-time (printed p.5) — i.e. replicate series, which is what makes the worst-case rule below
  computable.
- **Cleaning/validation:** only resampling. The upper layer resamples 5-minute series to one day by "mean, minimum,
  and maximum"; Channel A's lower-layer series is resampled to 30 minutes by mean while rival series stay at 5
  minutes (printed p.2, Fig. 3). No missing-data handling, no outlier rule, no reconciliation, no validation of the
  simulated data against anything.
- **Ethics/provenance:** none discussed (arguably not needed for a synthetic dataset, but a marker will notice the
  silence given the report's "stochastic modeling" claim).

## 3. Model

Two-layer deterministic MILP (the word "stochastic" appears in the abstract but no stochastic programme exists).

- **Upper layer (movie selection + ad purchase, printed pp.2–4).** Binary decisions: η_{m,d} (consider movie m on
  day d), μ_{m,w} (movie in week w), α_{c,m,d} (buy an ad for movie m on rival channel c on day d), γ_{c,m,w}.
  Objective: maximise Σ W^Avg_{m,d}·η + Σ A^Avg_{c,m,d}·α, where W^Avg is views per £ of licence fee and A^Avg is
  worst-case converted views per £ of ad cost — i.e. a **value-for-money** objective, not a cash objective.
  Constraints: binarity; per week 1 ≤ Ση ≤ 2μ; no repeat of a movie across adjacent months; daily runtime ≥ 204
  slots; 10 ≤ number of movies/day ≤ 30; η_{m,d} + I_{c,m,d} ≤ 1 (never schedule a film a rival airs that day);
  γ ≥ α and γ ≤ Σμ in the following three weeks; Σ_m α_{c,m,d} ≤ N^ads_{c,d}; and the ±£50,000 fairness band.
- **Lower layer (intraday schedule, printed pp.5–7).** Binary x_{m,t,d}, y_{m,d}, a_{c,m,t} plus continuous
  s_{m,d}, e_{m,d}, b_{c,m,t}, c_t. Constraints: ads only for upper-layer-approved pairs; slots ≤ N^ads; runtime
  equality Σ_t x = R·y; at most one airing per movie per week; y ≤ η; exactly one movie per slot; big-M start/end
  time definitions; e − s = (R−1)y. Objective (printed p.7): maximise
  10^6·(15.04/1000)·(6Σ c_t + 6Σ b) − (ad purchase cost + licence fees), with the ×6 converting 30-minute to
  5-minute units.
- **Size, solver, language, runtime: not stated.** No variable/constraint counts, no solver name, no modelling
  language, no runtimes. The only computational claim is that the two-layer split is "designed to reduce the
  runtime required to obtain an optimal solution" (printed p.2) — with no single-layer comparison, no runtime table,
  and no solution-quality comparison, so the claim is unsupported.
- **Problematic detail:** the "robust optimisation" pair (printed p.6, constraints 1–2) sets
  c_t ≤ Σ_m Z_{m,t}·x_{m,t} and c_t ≤ 1 − Σ_c E^max_{c,t}. The second has a dimensionless right-hand side being
  used as an upper bound on a viewer count, so it cannot be doing what the text says. A marker who checks units
  will find this.

## 4. Analysis design

- **Sections that exist:** viewership/profit comparison (Table 1), time-series reading (Fig. 4), ad-price behaviour
  (Fig. 5), revenue trade-off (Fig. 6), demographics/genre/era (Figs. 7–8).
- **Sensitivity:** one one-way sweep only — share of Channel A's own slots sold, 0–45% (Fig. 6, printed pp.9–10),
  with reported trade-off slopes of "1:5" for viewership revenue and "4:3" for ad revenue and a stated worst case
  at 50% sold. No sensitivity on licence fee, CPM, popularity scaling, prime-time factor, conversion rate,
  competitor schedules or the arbitrary ±£50,000 band.
- **Robustness/worst case:** a min-viewership worst case enters A^Avg and TVCmin (printed pp.3, 5); it is labelled
  "Robust optimisation [2]" but is simply a pessimistic point estimate, not a robust counterpart with a budget of
  uncertainty.
- **Benchmarks / naive comparators: none.** There is no greedy or popularity-only schedule, no no-advertising
  counterfactual, no single-layer solve. Competitor channels appear in Table 1 but as other actors, not as a
  baseline. This is the single biggest analytical gap: the reader cannot tell how much of the +£2.62m comes from
  the model rather than from the data.
- **Uncertainty treatment:** expectation only; the abstract's "stochastic modeling" is not implemented.
- **"What would change the recommendation": not addressed.** No parameter threshold, no break-even statement.

## 5. Results and presentation

- **KPIs (Table 1, printed p.7):** base true view count, converted view, total view, ad cost/revenue, licence fee,
  profit, for all four channels. Derived ratios: conversion share 47.46% of Channel A views, ad cost per converted
  view £0.0095, licence fee per total view £0.0094, viewership 11.19% below market average, licence spend 86.04%
  below average.
- **Figures: 8. Tables: 1.** Fig. 1 = strategy infographic (five labelled blocks); Fig. 2 = two-layer schematic;
  Fig. 3 = resampling schematic; Fig. 4 = four-channel true view count over 12–15 Dec (multi-series line);
  Fig. 5 = ad slot price over the same window (multi-series line); Fig. 6 = total/sales/viewership revenue against
  "% of ads sold" 0–45% (three-series line — the closest thing to a marginal-value curve); Figs. 7–8 = paired pie
  charts of genre share and movie-era share, Channel A vs others, in the Annex. No heatmap, no tornado, no
  dashboard, no scatter/regression, no map.
- **Executive summary:** none. There is a single-paragraph abstract on page i and a bulleted conclusion on
  printed p.10 organised by "strategy pillar" (pricing, cost-effective selection, peak optimisation, underserved
  demographics) plus one budget/profit statement. The recommendation is not decision-shaped: it names strategies,
  not a schedule, a spend plan or a do-this-first ranking.
- **Limitations/discussion: none.** No caveats on synthetic data, no threats to validity, no discussion of what
  breaks if competitors respond (even though competitors are the whole premise).

## 6. Structure and length

- **Order:** Abstract (i) → Contents (ii) → 1 Literature Review (p.1) → 2 Introduction (pp.1–2) →
  3 Model Formulation (pp.2–7, with 3.1 sets, 3.2 upper layer, 3.3 lower layer) → 4 Results and Analysis
  (pp.7–10, five subsections) → 5 Conclusion (p.10) → References (p.11) → 6 Annex (pp.11–12).
- **Page allocation (12 printed pages):** literature review ≈0.7, introduction ≈1.3, formulation ≈5.0,
  results ≈3.0, conclusion ≈0.7, references ≈0.3, annex ≈1.5. Formulation-heavy, analysis-light — the inverse of
  what a consulting report usually needs.
- **Appendix content:** two pie-chart pairs with percentage labels only. No parameter table, no solution schedule,
  no code, no data dictionary — so the actual recommendation (the schedule) is never shown.
- **References: 6** (numeric style, mixed quality): one SVOD market paper, one data-driven robust optimisation
  paper, one two-layer VPP scheduling paper, the classic SPOT scheduling paper, one TV-industry strategy paper,
  one Statista CPM page. Two of the six (the robust-optimisation and two-layer papers) are cited for method
  labels rather than actually used.
- **Formatting:** plain LaTeX, no institutional template or branding; captions degenerate into
  "Figure 7: (a) ; (b)" and "Figure 8: (a) ; (b)" with empty descriptors (PDF pp.13–14); consistent typographic
  errors ("advertisement sots", printed p.10) and a contradictory time statement, "prime-time (6 PM to 4 PM)"
  (printed p.8). Table 1's sign conventions are unexplained. Overall: readable but visibly unchecked.

## 7. Level judgment

**Band estimate: Merit, low end (borderline pass if marked strictly).**

Strengths a marker would reward:
- A genuinely layered MILP with a defensible hierarchy: selection (value per £) then scheduling (cash), with clean
  linking constraints γ ≥ α and y ≤ η (printed pp.4, 6).
- The competitor-clash constraint η + I_{c,m,d} ≤ 1 is a real modelling idea, not decoration, and drives the
  "market gap on weekends" finding (printed p.8).
- A quantified KPI table with a derived budget and profit, plus a genuine one-parameter trade-off curve (Fig. 6),
  which is more analysis than many reports in this genre attempt.
- Recommendations are tied back to specific figures (each conclusion bullet names its exhibit, printed p.10).

Weaknesses a marker would penalise:
- No solver, no model size, no runtime, no code: the "reduce the runtime" claim is unfalsifiable as presented.
- No benchmark or ablation of any kind, so the value added by the model is unquantified.
- Dimensional error in the "robust" constraint and an arbitrary ±£50,000 fairness band, both unexamined.
- Six refs, two unused-in-substance; no limitations; no discussion of competitor reaction.
- Presentation defects that are cheap to fix and were not fixed (empty figure descriptors, wrong clock time,
  typo in the conclusion).
- Silent switch from "stochastic modeling" in the abstract to a deterministic model.

Why not higher: a distinction requires evidence that the formulation is computational and that the result beats
something. Neither is present. Why not lower: the formulation is real, the KPIs are quantified and internally
consistent in direction, and the trade-off curve does answer a decision question.

## 8. Transferability to an energy-storage investment project

Reusable:
- **Two-layer decomposition as investment-vs-dispatch hierarchy.** Upper layer = which assets/capacity to commit
  over the horizon under value-for-money ranking; lower layer = intraday dispatch with runtime, start/end and
  "one thing at a time" constraints. This maps almost directly onto battery/electrolyser sizing followed by
  half-hourly dispatch, and it is the standard defence for keeping an Xpress model solvable.
- **Value-per-£ objective for the investment layer** (W^Avg = expected views ÷ licence fee) is the right shape for
  a capex-constrained portfolio: £/MW or MWh of flexible capacity per unit of expected net revenue, then a cash
  objective at the dispatch layer. Using a *ratio* objective at the selection layer and *cash* at the operation
  layer is a transferable design choice, provided the ratio is explained (this report does not explain it well).
- **One-parameter sweep with reported slopes** (Fig. 6): share of a controllable quantity varied 0–45% with the
  effect on each revenue stream stated as a rate. Direct analogue: battery capacity or contracted share varied, with
  arbitrage revenue, capacity revenue and imbalance cost reported as separate curves.
- **Non-substitutability constraint ("do not show what a rival shows")** generalises to "do not commit the same
  asset/volume twice" — e.g. one cycle counted for both arbitrage and a reserve contract.
- **"Exhibit → conclusion bullet" discipline** in the conclusion (printed p.10): each recommendation names the
  figure it came from. Cheap and marker-friendly.

Not transferable:
- Movie licence/popularity/genre machinery, prime-time factor, demographic scaling: topic-specific and would need
  complete replacement by price/volume/efficiency data.
- The fairness band and "market price benchmarking" construction: arbitrary here, and there is no analogue for a
  price-taking storage asset.
- The annex pie charts: they present *shares of a catalogue*, which has no energy-project counterpart; do not copy
  the form.
