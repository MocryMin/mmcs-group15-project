# Batch A summary — three past MMCS reports profiled

Profiles: [`group_10/PROFILE.md`](group_10/PROFILE.md), [`group_23/PROFILE.md`](group_23/PROFILE.md),
[`group_8/PROFILE.md`](group_8/PROFILE.md).

Evidence basis: all three PDFs opened with `document_open` (sha256 recorded in each profile) and read in full via
`document_read` page by page. Structural indexes were not available (`heading_count=0`, `block_count=0` in every
case), so extracts came from page ranges. Figures and layout were **not** visually inspected; all visual judgements
are inferred from captions and axis text. These are example reports, not templates and not a page-allowance
authority (see the collection README).

## Comparison

| Dimension | Group_10 (2024, TV) | Group_23 (2024, TV) | Group_8 (year unstated, fraud) |
|---|---|---|---|
| PDF pages / printed pages | 14 / 12 | 17 / 14 | 15 / 12 |
| Client framing | Weak: "Channel A" only, no consultancy identity, no stakeholders | Strongest: branded "Sopra Steria Consultancy Report", "Channel A engaged our team", one-page exec summary | Functional only: client referenced once (external-hire cap), no engagement narrative, no date on cover |
| Core model | Two-layer MILP (movie selection + intraday schedule) plus an ad-buy binary block | One-week scheduling MILP + a priced greedy ad-selection algorithm + an unused integrated MILP in Appendix A | Daily LP (investigate / internal vs external) + three-part learning layer (threshold, customer probability, ROE calibration) |
| Model size stated | No | No | No |
| Solver / runtime evidence | None — only an unsupported claim that layering "reduce[s] the runtime" | Yes: 5% MIP gap, 600 s timeout, 1–2 min/week typical, one week at 6.4% gap; ad stage "runs in seconds per week" | None — no solver, no language, no solve times |
| Data | Simulated, 5,919 movies, 84 days, 5-min slots, 3 demographics, 10 viewership replicates; only resampling described | Supplied fictional dataset; 5,920 movies, 4 channels, 34 ad slots/day; aggregation (÷6) and Pareto pruning (÷60) documented | Simulated bank system, two batches (~238k and ~124k transactions, derived from appendix), 5 banks, 4 amount bins |
| Ablation / benchmark | None | Only a worded "schedule-only holds share" claim; peer table (age, licence fee) | Strong: 3-model ladder + out-of-time batch + information-poor regime + per-priority targets |
| Sensitivity analysis | One sweep: % of own slots sold, 0–45%, with reported slopes | None | None (five design parameters fixed and unvaried) |
| Uncertainty | Worst-case min viewership used inside two parameters; no distributional robustness; abstract's "stochastic" claim unimplemented | Expectation of the client's stochastic conversion rate only | None; no confidence intervals on success rates |
| "What would change the recommendation" | Absent | Partial and good in kind: reservation-price switch points + a pre-emptive objections subsection; not quantified | Absent (only post-hoc explanations of drops) |
| KPIs | View counts, converted views, ad cost, licence fee, profit; budget £32.81m, profit £2.62m | Market share 22%; weekly profit margin ≥60% over 12 weeks; mean age/price vs peers | Success rate on cases and on £; external cases and cost; money saved; 75.5%/77.3% headline vs 40.7%/45.5% limited info |
| Figures / tables | 8 figures / 1 table | 5 figures / 1 body table (+12-week log in appendix) | 2 figures / 16 numbered tables (+5 crosstab matrices) |
| Best exhibit | Revenue-vs-%ads-sold trade-off curve (Fig. 6) | Computational-feasibility section + 12-week results log | Reliability diagram (Fig. 2) motivating calibration |
| Missing exhibit | Benchmark/ablation of any kind | Sensitivity on the central price parameter V | Lift/cumulative-gains curve for the ranked queue |
| References | 6, two used only as method labels | 6, small but genuinely used | **0** (two footnotes carry all external evidence) |
| Limitations section | None | Caveats scattered, none consolidated | None consolidated |
| Recommendation format | Strategy-pillar bullets, not decision-shaped | Six actionable bullets, no owner/timing | Findings restated, no recommendation |
| Band estimate | **Merit (low)** | **Distinction** | **Merit (upper)** |

## Three most valuable transferable devices

**1. Group_23's "computationally feasible approximation" section (printed p.3) — quantified compromise disclosure.**
State the ideal model, state that it misses the limit, then list every compromise with its measured cost: 30-minute
aggregation (problem size ÷6), Pareto pruning of the candidate set (÷60, leaving 100–200 per week), solver settings
(5% gap, 600 s), achieved runtimes (1–2 min/week) and the one failure (6.4% gap at timeout). For our battery/
electrolyser MILP in Python/Xpress with daily supplied series and half-hourly dispatch, this is precisely the
"explicit rationale and validation" the brief demands, and it pre-empts the question "did you actually solve it?".
Reuse the *structure* (compromise → quantified loss → achieved performance), not the numbers.

**2. Group_8's validation architecture — staged ladder, out-of-time test, information-poor case (printed pp.7–10).**
One instance, identical inputs, one mechanism added per stage (baseline → +adjustment → +calibration), a single KPI
table across stages, then the frozen model re-run on a later period, then re-run under the information actually
available at decision time (no false-negative labels). Energy translation: no-investment comparator → investment
with rule-based dispatch → investment with optimised dispatch → investment under imperfect foresight, each with the
same four KPIs. This satisfies the brief's "compare against simpler/no-investment alternatives" and "validate
results" in one coherent design, and produces exhibits rather than assertions.

**3. Group_23's switch-point analysis (printed pp.6–7) — turning a model into a decision rule.**
Two devices: (a) a reservation-price rule derived from the model's own shadow value ("never sell below
max_m{V·Δν̃_m·b_m}; always sell above it"), and (b) a pre-emptive "potential objections" subsection that confronts
the weakest parameter before the examiner does. Translation: give the £/MWh spread, capex or round-trip-efficiency
threshold at which storage stops paying back, and a short subsection stating which assumption would overturn the
recommendation and by how much. This is the most direct way to answer the brief's "which assumptions change the
recommendation" requirement, and it costs one paragraph plus one table.

Honourable mention (4th, not top three): Group_10's one-parameter trade-off sweep with reported slopes (Fig. 6) —
cheap, effective, and the shape we want for capacity-vs-revenue curves.

## Notes, limits and residual risk

- Bands are my judgement on the evidence read (full text, no visual inspection, no marking grid). The three reports
  are from different years/topics; they are evidence of what was accepted as good practice, not of current marking
  standards or page limits.
- Two report-level defects are worth remembering as "do not copy": Group_10's dimensionally inconsistent
  "robust" constraint (printed p.6) and arbitrary ±£50,000 fairness band (printed p.4); Group_23's Appendix A model
  that cannot run as written (undefined L, B vs C, channel renumbering, printed p.12).
- Group_8's cover carries no year or institution, matching the collection README's note that its year is unstated;
  I did not infer a cohort year.
- The two TV reports are near-identical instances: Group_10 sizes the candidate set at 5,919 movies (printed p.2),
  Group_23 at 5,920 (printed p.1), with the same 4 channels, same three demographics and same 5-minute baseline
  series. Treat their differences as approach differences, not data differences — useful when comparing what each
  team did with the same brief.
