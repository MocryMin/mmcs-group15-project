# Profile — Group_23.pdf (2024, TV scheduling and advertising, 17 PDF pp)

Evidence basis: `document_open` on `Tier1/public/reference/past_project_reports/20261103-v1/Group_23.pdf`
(sha256 `6e603a7bbe9b478f8ce94b84c7f7adba0ffb264c2f2ddd72d8af987d168254ca`, 17 pages, text extracted,
`heading_count=0` / `block_count=0`, 7 external URI links, 58 internal). Full extracted text read page by page via
`document_read`. Layout and figure legibility were **not** visually inspected; visual judgements rest on captions
and axis text.

Page convention: three unnumbered front pages (cover, Executive Summary, Contents), so
**printed page = PDF page − 3**. Both are given where it matters.

## 1. Question and scope

- **Decision answered:** what content Channel A should license and schedule across a rolling 12-week plan, and how
  it should price its own ad slots and choose which rival slots to buy, to maximise viewership and profit
  (profit is defined on printed p.1 as "advertising revenue minus licensing fees").
- **Client framing:** the strongest of the three reports. The cover (PDF p.1) is a branded "Sopra Steria
  Consultancy Report" for "Team # 23", Department of Mathematics, University of Edinburgh, November 2024, with the
  instructor named. The Executive Summary opens "Channel A engaged our team" (PDF p.2) and structures the answer as
  two workstreams with three headline takeaways each — an actual consulting shape.
- **Stated assumptions:** all revenue comes from advertising, so ad pricing is the core of the business model
  (printed p.1, justified by excluding BBC/Sky/subscription models); competitors' slot prices are given, and one's
  own slot's opportunity cost is its market price; adverts only push viewers to movies *after* the slot; no film is
  repeated and no film shown by a competitor in the coming week is scheduled; conversions are represented by the
  expectation of the client's stochastic genre-similarity conversion rate; the advertising model assumes every slot
  is available and that showing a rival's film does not hurt own viewership (printed p.12, Appendix A).
- **Scope limits declared rather than hidden:** the report explicitly excludes subscription revenue models and
  admits it does not distinguish sales to rival channels from sales to commercial advertisers (printed pp.1, 4).

## 2. Data

- **Source:** the supplied simulated dataset for the fictional setting — the report says so plainly: "As the
  problem is posed in a fictional setting" (printed p.6). No scraping, no external data purchased; external sources
  are used only for context (Statista market outlook, ITV Media and toast ad-cost guides, two academic papers).
- **Size:** 5,920 movies (printed p.1), four channels, continuous streaming 07:00–24:00 with one ad break roughly
  every 30 minutes, 34 ad slots per day (printed p.12), three demographic groups, per-slot rival prices and
  viewership, and 10 replicate viewership series per slot (implied by the worst-case minimum used in pricing).
- **Cleaning/validation:** no data-audit section, but three *modelling-side* transformations are documented with
  their effect: 5-minute → 30-minute aggregation ("reduced the problem size by a factor of six", printed p.3), a
  near-Pareto/non-domination filter on the movie set ("reductions of closer to a factor of 60", typically leaving
  100–200 movies per week, printed p.3), and a heuristic exclusion of anything a rival airs next week or Channel A
  aired before (printed p.3). Each is justified in words; none is validated by a back-test.
- **Ethics/provenance:** one honest paragraph on why the ad-viewer value V is inferred from competitor prices rather
  than imposed (printed p.6). No other provenance or ethics content.

## 3. Model

Two components: a weekly MILP for scheduling and a greedy market algorithm for advertising.

- **Scheduling MILP (1a)–(1f), printed p.2.** Binary x_{m,t,d} (movie m in slot t on day d), binary y_{m,d}, integer
  start/end s_{m,d}, e_{m,d}. Objective (1a) maximises Σ f_{m,t,d}·x_{m,t,d}, where f is expected viewership =
  baseline viewership of the three groups × scaled popularity × prime-time factor. Constraints: exactly one movie
  per slot (1b); duration equality (1c); end−start = duration (1d); big-M style start/end definitions (1e)–(1f).
- **Computational treatment (printed pp.3–4), the report's best feature:** stated one-hour target was infeasible,
  so (i) horizon aggregated to 30 minutes, (ii) movie set Pareto-pruned to 100–200 per week, (iii) diversity by
  heuristic pre-filter, (iv) "target MIP gap was 5% and the timeout was 600 seconds", with actual performance
  reported: "typically taking only 1 or 2 minutes per week", and one exception — week 2024-10-29 to 2024-11-05
  reached only a 6.4% gap at timeout. That is exactly the evidence trail a marker asks for, including the failure.
- **Advertising model (printed pp.4–7), not an optimisation model but a priced greedy algorithm:** market value of
  a slot = Σ_g V_g·ν_g, simplified to V·ν; conversion E[Δν̃_m] = E_{k,m}·ρ_m·r̃_m·ν_k (expected conversion rate ×
  popularity × remaining convertible audience × slot viewership); buy rule ranked by cost per additional unit of ad
  viewership W_{k,m} = p_k /(Δν̃_m·b_m); a 9-step loop that repeatedly picks min W, stops when W ≥ V, raises the
  price of own slots in the advertised movie, decrements the convertible audience, and recomputes. Greedy is
  justified explicitly ("This greedy strategy is known not to be theoretically optimal", printed p.6) with the
  reason for accepting it (a larger nested optimisation with diminishing returns) and with a reservation-price
  fallback: sell if the offer exceeds max_m{V·Δν̃_m·b_m} (printed p.7).
- **Integrated MILP in Appendix A (2a)–(2e), printed p.12:** adds y_{m,j,k,d} ad-placement binaries, a one-movie-
  per-slot rule, an "advertise only before the movie starts" rule, a budget constraint and a per-movie ad cap. This
  appendix model is **not** the model used for results and is left broken: the objective adds bare y terms with no
  coefficient, the budget constraint uses B while the parameter list defines "C: adverting budget", constraint (2e)
  uses an undefined L, the channel indexing flips from {0,1,2} + own channel in the body to "Channels 1, 2, and 3 …
  Channel 4 is our channel", and the variable definition reads "= 0 if … ; = 0 otherwise".
- **Size, solver, language: partly not stated.** No variable/constraint counts, no solver name, no language. Solver
  *behaviour* (MIP gap, timeout, runtimes) is stated; the tool is not. Code is referenced only as a private GitHub
  repository (printed p.12).
- **Note:** the results text refers to "Model (2.1)" (printed p.7) although the scheduling model is numbered (1a).

## 4. Analysis design

- **Rolling horizon:** one-week MILP solved repeatedly with an updated, exclusion-filtered movie database
  ("rolling-forward approach", printed p.7) over 12 weeks — a legitimate decomposition, and the source of the
  "unique schedule every week" claim.
- **Scenarios/ablations:** one implicit ablation is described in words — the standalone scheduling model is said to
  hold market share "even without considering advertisements" (printed pp.1–2) — but no before/after numbers are
  tabulated. There is **no** sensitivity analysis, no parameter sweep, no tornado, and no formal scenario set.
- **Benchmarks:** descriptive peer comparison rather than model comparison: market share against three rivals
  averaged to 22% (Figure 2, printed p.7), and Table 1 comparing mean movie age and mean licence fee for the movie
  database and all four channels (printed p.9). Both are positioning checks ("we are like the competitors"), which
  is weaker than a no-model or greedy comparator but at least quantified.
- **Uncertainty:** only through the client's stochastic conversion rate, taken in expectation (printed p.5); the
  authors flag that a per-demographic disaggregation would be better. No distributional robustness, no worst case
  on prices.
- **"What would change the recommendation":** partially and unusually well handled. The reservation-price logic
  (printed p.7) states the two switch points explicitly — do not sell below max_m{V·Δν̃_m·b_m}, and always sell
  above it — and Section 2.3.7 ("Potential objections to the calculation of the value of a viewer", printed p.7)
  pre-empts the strongest criticism of V. What is missing is the quantitative part: no statement of how V, ρ or the
  5% gap would have to move to flip a recommendation.

## 5. Results and presentation

- **KPIs:** average market share 22% (printed p.7); weekly profit margin ≥60% for all 12 weeks with the weekly
  revenue, licence cost, profit and advert count tabulated in Appendix C (printed pp.13–14, margins 60–90%);
  mean movie age and licence fee vs peers (Table 1, printed p.9); genre and demographic composition of the schedule.
- **Figures: 5. Tables: 1 in the body** (plus the 12-week numeric log in Appendix C, which is a table in substance
  but set as plain text). Fig. 1 = weekly viewership trends for four channels, week 1; Fig. 2 = weekly market-share
  evolution by channel; Fig. 3 = PCA scatter of genre categories (four thematic buckets); Fig. 4 = representative
  baseline viewership across the day by demographic; Fig. 5 = effect of the advertising strategy in a typical week,
  by demographic. No heatmap, tornado, dashboard, dispatch-style Gantt of the schedule, or marginal-value curve —
  notably, the report never plots W_{k,m} against slot, which would have been the natural exhibit for its own
  algorithm.
- **Executive summary style:** the best of the three — one page, two numbered workstreams, three bullets each, one
  hard number per workstream, and a closing claim. It is also where the overclaim lives ("we are confident that it
  will allow Channel A to dominate the United Kindom's television market", PDF p.2, typo in original).
- **Recommendation format:** six bullets in the Conclusion (printed p.10), three per workstream, each actionable
  ("Capitalize on competitors' mispriced advertisement slots…", "Price own advertisement slots based on expected
  viewership", "Advertise movies within similar genres"). No owner, no timing, no costed action plan.
- **Limitations/discussion:** better than most — the greedy-optimality caveat, the V-circularity objection, the
  demographic-disaggregation gap, and the sales-channel ambiguity are all stated. There is still no limitations
  section and no statement of what would invalidate the whole approach.

## 6. Structure and length

- **Order:** cover → Executive Summary → Contents → 1 Introduction (printed pp.1–2) → 2 Methodology (pp.2–6:
  scheduling, computationally feasible approximation, advertising strategy in seven sub-questions) →
  3 Results (pp.7–9: scheduling results, content strategy, advertising and pricing) → 4 Conclusion (p.10) →
  References (p.11) → Appendix A Advertisement planning (p.12), B Source code (p.12), C Full advertisement strategy
  results (pp.13–14).
- **Page allocation (14 printed pages):** introduction ≈1.5, methodology ≈4.5, results ≈3, conclusion ≈1,
  references ≈0.5, appendices ≈3. Well balanced for a consulting report; appendices carry real content.
- **Appendix content:** a full second MILP (flawed), a code-repository pointer, and a 12-week results log. No worked
  schedule, no parameter table, no sensitivity output.
- **References: 6**, well-matched to their use: Horen (1980) and Reddy–Aronson–Stam (1998) for scheduling,
  Lobato (2018) for linear schedules vs catalogues, Statista and ITV Media and toast for market prices. Small but
  each is actually used.
- **Formatting:** professional cover with institutional branding, numbered equations, prose that argues rather than
  lists. Defects: the Appendix A model is internally inconsistent (above), "Model (2.1)" vs (1a), a typo in the
  closing sentence, and hyphenation breakage in table headers. Visually polished where it counts (front matter,
  section structure), sloppy where a marker with a calculator will look (Appendix A).

## 7. Level judgment

**Band estimate: Distinction.**

Strengths a marker would reward:
- The computational-feasibility section (printed p.3) is the single best thing in any of the three reports: each
  simplification is named, quantified (factor 6, factor 60, 100–200 movies), and paired with solver settings, actual
  runtimes and one honest failure (6.4% gap at timeout).
- A decomposition with a stated rationale and a stated cost (greedy instead of a nested MILP), plus a documented
  reservation-price rule that converts the model into a decision rule for a negotiator.
- Self-critique that anticipates the examiner: Section 2.3.7 rebuts the circularity in V before anyone raises it.
- Quantified, segment-checked results (12-week table with margins), a real peer benchmark (Table 1), and a
  one-page executive summary with numbered takeaways.
- Reference set is small but genuinely used.

Weaknesses a marker would penalise:
- **No sensitivity analysis at all.** The report's central parameter V is estimated, then never varied; the 5% MIP
  gap is never stress-tested; no statement of how far a price or viewership assumption must move to flip the buy
  list. For a consulting brief this is the most costly omission.
- Appendix A is a second model that does not run as written (undefined L, B vs C, bare objective terms, channel
  indexing flip). A marker who reads appendices will discount the "two formulations" impression.
- The "maintains market share" result has no control: no baseline/naive schedule is reported, so 22% is
  uninterpretable as value added.
- The PCA exhibit (Fig. 3) is decorative — four "thematic buckets" are asserted from a scatter with no loadings,
  and the conclusion drawn from it ("equal representation across all categories") does not follow from a PCA.
- Overclaiming in the final sentence ("dominate the United Kindom's television market") undercuts an otherwise
  disciplined tone.
- Code and data are not reproducible from the report (private repo, no parameter table).

Why distinction rather than merit: solver evidence with a reported failure, an explicitly rejected optimisation
alternative with a stated reason and a fallback rule, and pre-emptive self-critique are the three things that
separate a consulting answer from a coursework answer, and this report has all three. The missing sensitivity
analysis is a strong demerit but not enough to drop it.

## 8. Transferability to an energy-storage investment project

Reusable, in priority order:
- **The "computationally feasible approximation" section, verbatim in structure.** State the ideal model, state that
  it misses the time limit, then list each compromise (temporal aggregation, candidate pruning, gap/timeout) with its
  quantified cost and the achieved runtime. For a battery/electrolyser MILP in Xpress with daily series that must be
  expanded to half-hourly dispatch, this is the exact disclosure the brief's "explicit rationale and validation"
  requirement demands, and it protects against "did you actually solve it?".
- **Reservation-price / switch-point logic.** "Do not transact below X, always transact above Y", derived from the
  model's own shadow value, is directly the "which assumptions change the recommendation" requirement. Energy
  analogue: the £/MWh spread, capex or efficiency at which storage stops being worth building, or the price at which
  selling flexibility beats arbitraging it.
- **Rolling-forward re-optimisation with an updated candidate set.** One week (or one month) at a time with an
  exclusion list maps onto operating a portfolio through time (Tier2B) and onto re-running the investment model as
  realised prices arrive; it also creates a natural validation path (compare rolling plan to realised).
- **Ranked marginal-cost selection with diminishing returns.** The W_{k,m} = cost per additional unit of value
  ranking, with the audience (resource) decremented after each pick, is a clean transferable heuristic for choosing
  between competing flexibility options (battery vs electrolyser vs curtailment) when a full MILP is out of reach —
  and the report's honesty about greedy sub-optimality is the template for presenting it.
- **Peer-benchmark table.** Table 1's format (our portfolio vs database vs each rival, two metrics) adapts directly
  to "our recommended portfolio vs no-investment vs current-generation-priority", which the brief explicitly asks
  for.
- **Executive-summary shape:** two workstreams × three takeaways × one number each.

Not transferable:
- Genre cosine similarity, prime-time factor, demographic scaling and the movie catalogue machinery.
- The V-from-competitor-prices construction: it exists because a fictional ad market had to be priced; energy prices
  are given in the data, so there is no analogue.
- The 12-week ad log format (per-week advert counts) — replace with per-period dispatch/settlement KPIs.
