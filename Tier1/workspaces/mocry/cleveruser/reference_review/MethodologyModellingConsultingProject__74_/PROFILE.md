# Profile — `MethodologyModellingConsultingProject__74_.pdf` (2025, cycle scheme facility location and network rebalancing)

Source: `Tier1/public/reference/past_project_reports/20261103-v1/MethodologyModellingConsultingProject__74_.pdf`,
15 PDF pages, sha256 `10a6018eaea6c732ec2b43779b47f6e63f5eb5f6f8ebe42a0ffa71f63791e087`,
document `doc-05b310688b744159a47ad2b34864a621`. Read: all 15 pages by page range; text extraction
complete (no fallback needed despite the 6.5 MB image content); pages 5 and 11 also rendered and viewed for
figure quality.

**Anchor convention:** `PDF p.N / printed p.M`, printed = PDF − 2 (footers verified: "3" on PDF p.5, "9" on
PDF p.11, "11" on PDF p.13). Front matter = cover (PDF p.1), Executive Summary (PDF p.2). Body printed
pp.1–10, References p.11, Appendix pp.12–13. **There is no table of contents.**

Cover: "Facility Location and Network Rebalancing with applications to Edinburgh's Cycle Scheme", by David
Fry, Edward Fry, November 26, 2025 (PDF p.1). Two authors — the report reads as a two-person consulting
deliverable, not a five-person group project.

## 1. Question and scope

- **Decision answered:** where to put a new Edinburgh bike-hire network's fixed stations, and how to rebalance
  bikes across them. The recommendation is an initial network of 40 stations and 400 bikes at £1.4 m capex,
  paying back in about 7 years under a stated funding mix (PDF p.2).
- **Client framing:** Edinburgh's Council; the previous scheme (Nov 2018–Sep 2021) failed commercially because
  of crime, maintenance cost, no rebalancing and low ridership, and covered only 20% of the Council's data
  zones (printed p.1). The Council "seek our guidance to propose a new set of bike station locations … and a
  network rebalancing solution" (printed p.1). The business objective (network design + funding) and the
  academic objective (three modelling contributions) are both stated in the first two pages.
- **Stated assumptions:** demand nodes = SIMD 2020 data zones (598 of them), with inbound and outbound demand
  separated because observed flow is asymmetric (printed p.4); demand allocation to stations is *continuous*,
  justified as a tractable approximation adequate for long-term planning (printed p.4); demand coverage is not
  enforced as a hard constraint, to avoid infeasibility from inputs (printed p.4); in a scenario, bikes are
  rebalanced only by customer usage (printed p.5); transit times asymmetric; every node must be visited once
  except the depot (printed p.6); rebalancing modelled as a static problem (printed p.2); bikes fungible —
  "bikes picked up from any node can be dropped at any other node" (printed p.10).
- **Self-declared contributions:** (i) a Markov-chain demand-scenario generator for the 80% of data zones the
  old scheme never served; (ii) a two-stage stochastic MIP for station location; (iii) a VRP-PD-style
  rebalancing MIP plus an adapted LKH-3 heuristic (PDF p.2, printed p.10).

## 2. Data

- **Own/supplied vs derived:** three real external sources plus one simulated layer. (a) Four years of trip
  data from the previous Edinburgh scheme, aggregated to hour-of-day × day-of-week (Fig. 1, printed p.3);
  (b) Scottish Index of Multiple Deprivation 2020 data zones, used for population and geography, 598 zones
  (printed p.3, p.8); (c) transit times from a locally hosted Open Source Routing Machine server, queried per
  edge (printed p.7); (d) Markov-chain simulated population flow for zones with no history (printed pp.3–4).
  No scraping of the scheme's own trip data is described, and the licence/access route is not stated.
- **Size:** 104 data zones served by the old scheme against 598 total, so the model claims "up to 494 more data
  zones" of accessibility (printed p.8). Location instance: "over 30,0000 candidate station locations" (sic —
  a digit error; the intended figure is not recoverable from the text) with **25 demand scenarios** weighted
  proportionately by time duration (printed p.8). The historical-trip route yields **24 scenarios**
  (4 seasons × weekday/weekend × 3 times of day, printed p.3). Rebalancing instances were built by random
  node selection at 10/20/30/40/50/100/1000 nodes with 2/2/2/2/3/5/40 vehicles (Table 3, printed p.8).
- **Cleaning/validation:** thin. Demand is mapped from cycle locations to the nearest data zone (printed p.3);
  an example summer scenario is shown as a map normalised to 750 trips (Fig. 3, printed p.8). There is **no
  train/test split, no validation of the Markov predictions against the 104 historically served zones**, and no
  descriptive statistics for the trip data beyond the two line charts. The Markov generator is asserted to
  produce sensible geography ("higher demand on nodes around the city centre", printed p.8) but never scored.
- **Provenance/ethics:** external sources are cited ([10] SIMD, OSRM named in text); no privacy or data-ethics
  discussion, which is defensible for aggregated trip counts, but ridership/population data at data-zone level
  is never checked for disclosure risk either. Reproducibility is addressed by publishing model files to a
  GitHub repository (printed p.8).

## 3. Model

- **Location model (printed pp.4–5):** two-stage stochastic **MIP**. First stage binary xᵢ (open station i);
  second stage continuous y^IB_{i,j,s}, y^OB_{i,j,s} demand allocated from node j to station i in scenario s.
  Objective (8): min Σ f·xᵢ − Σ_s p_s Σ_{i,j} (y^IB + y^OB) — install cost minus probability-weighted covered
  demand. Constraints: station budget Σxᵢ ≤ β (9); per-station scenario capacity Σ_j y^IB ≤ α_{i,s}·xᵢ (10);
  net-flow/dock-balance bounds ±(IB − OB) ≤ cᵢ·xᵢ (11); node demand caps (12); non-negativity (13); binary (14).
  Size, f, α and c values are **not tabulated**; the £1.2 m for 40 stations appears only in the results
  (printed p.9).
- **Rebalancing model (printed pp.5–7):** 3-index **MIP** VRP with pickup-delivery structure. Variables
  x_{i,j,v} binary, f_{i,j,v} integer bike flow, sᵢ integer consumed/released, u_{i,v} continuous MTZ
  ordering. Objective (15): min total transit time + β·Σ_{I⁺}sᵢ − β·Σ_{I⁻}sᵢ (rebalancing incentive; the same
  symbol β is also used for the station budget in the location model — a notation clash). Constraints: vehicle
  flow conservation (16), single visit per node (17), depot in/out (18), MTZ subtour elimination (19), tour time
  cap τ (20), edge capacity f ≤ c_v·x (21), bike flow conservation (22), surplus/deficit adherence (23),
  non-negativity/binaries (24–25). MTZ is chosen deliberately "due to its simplicity", with the weak LP
  relaxation acknowledged (printed p.6); the 3-index formulation is chosen over the more efficient 2-index one
  for extensibility (printed p.5).
- **Solution methods (printed pp.7–11):** location solved directly by **Xpress (186 s)**, **Gurobi (21.4 s)**,
  **CPLEX default (1,140 s)** and **CPLEX single-cut Benders out of the box (1,022 s, ~10% faster)** — all to
  optimality (printed p.8). Rebalancing solved by Xpress and Gurobi MIPs up to 40 nodes, and by an **adapted
  LKH-3** whose penalty function is re-defined as total absolute constraint violation plus unrealised
  rebalancing (printed p.7) with a custom Python I/O layer. Stated instance sizes: 50 nodes → over 15,000
  variables and constraints; 1000 nodes → over 10 million of each (printed p.9). Hardware: Mac M1 Pro, 16 GB,
  default solver parameters (printed p.8). Language: Python wrappers around commercial solvers and a C
  heuristic. **No optimality gaps or lower bounds reported for the heuristic cases**, only best-known transit
  times.

## 4. Analysis design

- **Scenarios as the uncertainty mechanism:** 24 (or 25) scenario demand sets, probabilities derived from time
  duration, both inbound and outbound. This is the report's central uncertainty treatment — no other
  distributional or robust treatment.
- **Benchmarking is computational, not economic:** three commercial solvers + a customised heuristic compared
  on transit time and wall-clock solve time across seven instance sizes with a 1,000 s limit (Table 3,
  printed p.8). The exact/heuristic crossover at 40 nodes is clearly established (Xpress and Gurobi find no
  feasible solution beyond 40 nodes; LKH-3 returns feasible solutions up to 1,000 nodes but with transit time
  degrading from 3.3 h to 29.2 h).
- **No sensitivity analysis on any decision parameter.** The station budget β, station capacity α, dock
  capacity cᵢ, tour time τ, fleet size, the £1 ride price, 200,000 annual journeys, the 10 bikes per station
  ratio and the 40-station count are all fixed. Nothing shows how the recommendation moves if, say, 30 or 60
  stations are built, or if ridership is 120,000 rather than 200,000.
- **One deliberately conservative bound:** a "worst-case scenario" rebalancing run (2 vans, 2 h cap, every node
  visited, half the nodes receiving 5 bikes and half donating 5) is costed and used as the annual operating
  cost bound (printed p.9). This is the report's best analytical instinct — but the 50% ± 5 bikes construction
  is arbitrary and is not derived from the demand scenarios, so the rebalancing model is effectively decoupled
  from the location model.
- **"What would change the recommendation":** essentially unaddressed. The only forward-looking statement is
  that the Council should "later evaluate if further bikes are required based on execution data of the new
  scheme" (printed p.9). There is no break-even ridership, no price elasticity, no comparison of a small dense
  network against a large sparse one.
- **Ablations:** none. The Markov scenario family is not compared against the historical-only family even
  though both are described as parallel approaches (printed pp.3–4); which one feeds the 25-scenario instance is
  ambiguous.

## 5. Results and presentation

- **Headline KPIs:** 40 stations; 400 bikes; £1.4 m total capex (£1.2 m stations + £200 k bikes at £500 each);
  200,000 journeys/yr; £200,000 annual revenue at £1/ride; ~7-year payback; annual rebalancing cost £22,520
  (£17,520 labour + about £5,000 fuel); 250 t CO₂ and 100,000 car journeys avoided (printed pp.9–10).
  Plus computational KPIs: transit time (h) and solve time (s) per instance and solver.
- **Counts:** 7 figures, 3 tables, 17 references.
- **Visuals:** Fig. 1 (printed p.3) seven-series line chart of outbound trips by hour and day of week — the
  clearest evidence in the report; Fig. 2 (printed p.7) a software architecture diagram; Fig. 3 (printed p.8)
  a **geographic map** of Edinburgh with data zones circled and sized/coloured by demand; Fig. 4 (printed p.9,
  verified in render) a **basemap of Edinburgh with 40 station markers and two coloured rebalancing routes** —
  the strongest presentation asset in the document; Figs. 5–7 (printed pp.12–13) three route plots for the
  20-node Xpress, 30-node Xpress and 1,000-node LKH-3 solutions. No heatmaps, tornado diagrams, or
  marginal-value/binding-constraint curves.
- **Executive summary style:** one page, three paragraphs, no bullets, no table: numbers first ("40 nodes …
  400 bikes … £1.4 million … pay back within 7 years"), then the three academic contributions, then the
  algorithmic result. Very effective; the only cost is that the funding mix is compressed into one clause.
- **Recommendation format:** a concrete plan, then a **ranked funding strategy** — pay-per-ride first
  (£1 vs a £2.20 bus fare as the comparator), advertising sponsorship second (to cover maintenance and the
  worst-case rebalancing cost), government subsidy negotiation third (printed pp.9–10). This ordering is the
  most consulting-like passage in either report.
- **Limitations stated:** commercial solvers fail beyond 40 nodes; heuristic quality untested at scale;
  experiments not broad enough in instance composition ("If time would have permitted, we would have done so",
  printed p.9); crime and socio-economic factors not modelled although they sank the previous scheme; no
  routing cost inside the location decision; static rather than dynamic rebalancing (printed p.10).

## 6. Structure and length

- Order: Cover → Executive Summary → 1 Introduction → 2 Background (facility location, stochastic programming
  and Benders, TSP/VRP/PDP/LKH) → 3 Modelling Approach (3.1 scenario generation with 3.1.1 historical and
  3.1.2 Markov; 3.2 location model; 3.3 rebalancing model) → 4 Algorithmic Approach (4.1 location module,
  4.2 rebalancing module) → 5 Analysis and Results (+5.1 Proposed Bike Network) → 6 Conclusions and Future
  Works → References → Appendix A (three route plots). **No contents page and no separate data section.**
- **Page allocation (printed):** Introduction + Background 2 pp.; Modelling 3.5 pp. (pp.2–5); Algorithms 1.5 pp.
  (pp.7–8, with Fig. 2); Results 3 pp. (pp.8–10); References 1 p.; Appendix 2 pp. Both models are stated in
  full before any results, which makes the middle of the report heavy but keeps the formulations readable.
- **Appendix content:** Figures 5–7 only — three screenshots of route solutions, no code, no data dictionary, no
  parameter table, no instance-generation details. A parameter table (f, α, cᵢ, β, τ, p_s) is the single most
  obvious missing appendix.
- **References:** 17, consistent numeric style, genuinely used (Benders 1962, Van Slyke–Wets 1969, MTZ 1960,
  Desrochers–Laporte 1991, Helsgaun 2000, Church–Velle 1974, Balas 1989, plus a 2025 location-routing survey).
  This is a properly literature-anchored report.
- **Formatting quality:** clean, professional, consistent LaTeX; figures legible; equations numbered and
  cross-referenced. Defects are textual rather than visual: "over 30,0000 candidate station locations"
  (printed p.8), "£5,0000" fuel cost (printed p.9), "10000 node instances" where 1,000 is meant (printed p.9),
  "4 years that the scheme previously ran" against a stated Nov 2018–Sep 2021 operating window (printed p.1 vs
  p.3), 24 scenarios in §3.1.1 against 25 in §5 (printed p.3 vs p.8), and β meaning two different things.

## 7. Level judgment

**Estimated band: Distinction (roughly 72–80).** Better than the banking-fraud report on almost every
dimension that markers weight, with two substantive analytical holes.

Strengths a marker would reward:
- Genuine two-stage stochastic formulation with correct here-and-now / wait-and-see separation, correct
  scenario weighting, and constraints that actually encode the operational story (dock balance, node demand
  caps, tour time limits, surplus/deficit targets). Both models are given variable tables and every constraint
  is justified in words.
- A real algorithmic contribution rather than a black-box call: three solvers benchmarked, Benders run
  out-of-the-box, and LKH-3 extended with a redefined penalty function via a custom Python interface. The
  exact/heuristic crossover (40 nodes) is a defensible, quantified conclusion.
- Honest, quantified scalability limits: "N/A / 1,000 s" cells in Table 3, stated instance sizes of 15,000 and
  10 million variables, stated hardware, stated default parameters, model files on GitHub. This is the level of
  reproducibility evidence the other report completely lacks.
- Real external data with a defensible geographic unit (SIMD data zones + population), a local OSRM routing
  service, and an explicit device for the data gap (Markov flow model for the 494 unserved zones).
- Presentation that a Council could act on: two real basemaps, a costed worst-case operating bound, and a
  ranked funding strategy with a payback headline.
- Limitation section that names the right things (crime, maintenance, routing-cost feedback into location,
  static rebalancing, solver scale).

Weaknesses a marker would penalise:
- **The location objective is dimensionally inconsistent.** Eq. (8) subtracts probability-weighted *trips*
  from *pounds* of station cost with no conversion weight. Nothing in the report states how many pounds of
  capex are worth one covered trip, so the station count and the coverage level are set by an implicit unit
  ratio, not by a decision. That is the largest single flaw; a sharp marker will find it immediately, and it
  undermines the "40 stations" recommendation's claim to optimality in any economic sense.
- **No sensitivity or parametric analysis on any business parameter.** β, α, cᵢ, τ, fleet size, price,
  ridership and the 10-bikes-per-station rule are frozen. The recommendation is a single point with no
  marginal-value curve, no break-even ridership, and no "if ridership is 30% lower, payback becomes N years".
  For an investment recommendation this is the missing chapter.
- **The payback is naive:** undiscounted, maintenance explicitly assumed away ("assuming constant ridership and
  no maintenance cost", printed p.9), no replacement capex, no demand response to the £1 price, and the
  advertising sponsorship is assumed to exactly cover the £22,520 operating cost by construction rather than
  negotiated.
- **The demand model is never validated.** The Markov generator is a headline contribution but is not
  back-tested on the 104 zones the old scheme did serve — the one experiment that would make it credible is
  available and not done.
- Location and rebalancing are solved as two unrelated problems: rebalancing demand γᵢ is user input, not an
  output of the demand scenarios, and the "worst-case" 50% ± 5 bikes construction is arbitrary. A joint or
  iterated treatment is gestured at in future work only.
- Presentation/number hygiene: no contents page, no data or parameter table, a three-figure appendix, and a
  cluster of numerical typos in the results section that weaken confidence in the numbers a reader is asked to
  trust.

Why distinction rather than merit: the modelling, algorithmic and computational evidence is well above the
level of a routine course report, the literature is genuinely used, and the deliverable is decision-shaped.
Why not higher: the objective function mixes units, and the investment recommendation has no sensitivity
analysis — the two things a consulting-style marker is most likely to probe.

## 8. Transferability to an energy-storage investment project

Reusable:
- **The two-stage stochastic investment template itself.** Integer first-stage siting/sizing decisions, a
  scenario set with explicit probabilities, continuous second-stage operating recourse, one budget-style
  constraint on the number of assets and per-asset capacity constraints. That is structurally the canonical
  storage siting-and-sizing model; bike §3.2 can be re-used almost line for line with "stations" → "storage
  units", "covered demand" → "energy arbitrage / peak shaving revenue", "dock capacity" → "power/energy
  rating". Add the missing feature the bike report lacks: an explicit £-per-MWh value so the objective is
  dimensionally consistent.
- **The scenario grid** (season × weekday/weekend × time-of-day, probabilities from duration) transfers
  directly to price/availability scenarios; and the Markov-transition trick for zones with no history
  transfers to years or assets with no observed prices.
- **The exact-vs-heuristic scalability table.** Reuse the exact format — instance size (assets × horizon),
  variables/constraints, objective value, solve time, and explicit "N/A at time limit" cells — to justify
  solving a full-year MILP with a heuristic and a shorter rolling-horizon LP exactly. Naming the crossover
  point is a cheap, high-credit device.
- **Worst-case operating-cost bound feeding the business case:** the rebalancing-cost paragraph (2 vans, 2 h
  cap, 5 bikes per node) is the pattern for bounding degradation/balancing/constraint costs so capex plus a
  bounded opex gives a defensible payback.
- **The ranked funding strategy and payback headline,** plus the site map with overlays. For storage: capex,
  revenue stack in priority order (arbitrage, capacity/balancing, subsidy), payback, and a map of candidate
  sites with the network drawn on it.

Not transferable:
- The whole VRP/MTZ/LKH-3 rebalancing apparatus, OSRM transit times, docking capacity, bikes-per-station
  ratios, and the 1,000-node routing instances. Storage operations are dispatch/state-of-charge problems, not
  routing problems; nothing here helps except as an analogy for "operational cost bound".
- The coverage-maximisation objective: storage value is not a coverage problem, and the max-covering /
  p-median lineage is topic-specific.
- SIMD data zones, crime and maintainability narrative, and the CO₂/car-journey marketing arithmetic.
- The unvalidated-Markov habit: for storage you need price scenarios with stated provenance, not simulated
  flows from a population gravity model.

Best single habit to steal: publish a scalability table with explicit failure cells. Worst habit to inherit:
freezing every business parameter and quoting an undiscounted payback.
