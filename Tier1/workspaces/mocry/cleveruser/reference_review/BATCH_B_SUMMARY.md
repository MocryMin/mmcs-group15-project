# BATCH B summary — two past MMCS reports compared

Batch B = `Group_20.pdf` (banking fraud, 2023) and
`MethodologyModellingConsultingProject__74_.pdf` (Edinburgh cycle scheme, 2025). Full per-report evidence is in
`group_20/PROFILE.md` and `MethodologyModellingConsultingProject__74_/PROFILE.md`.

Both PDFs were opened with `document_open` and read page-by-page across all pages (18 and 15 PDF pages), with
four pages rendered and viewed for figure/formatting quality (Group_20 PDF pp.8, 16; bike PDF pp.5, 11). Figure
types for pages not rendered are taken from captions plus axis labels in the extracted text; no claim below
depends on unseen pixel detail.

## Side-by-side

| Dimension | Group_20 (fraud, 2023) | Cycle scheme (2025) |
|---|---|---|
| Decision answered | Which transactions to investigate today, given a fixed team | Which 40 stations to build and how to rebalance bikes |
| Client framing | Supplied brief (Sopra Steria); regulator reimbursement context | Edinburgh Council, framed against a failed previous scheme |
| Length | 18 PDF pp. / 15 printed; 4-author report | 15 PDF pp. / 13 printed; 2-author report |
| Data | Supplied simulation only; no source, size or ethics statement; 123,523 test transactions, 1,006 frauds | Four years of real trip data + SIMD 2020 (598 data zones) + local OSRM routing; Markov simulation for the 494 unserved zones |
| Core formulation | OLS index + binary ILP (Model 1); LP-fitted weights + Bernoulli candidate sampling + allocation MIP (Model 2) | Two-stage stochastic MIP for location (binary open, continuous scenario flow) + 3-index VRP-PD MIP with MTZ for rebalancing |
| Solver evidence | "Python Xpress"; one size figure (~12,000 variables); **no runtimes** | Xpress 186 s, Gurobi 21.4 s, CPLEX 1,140 s, CPLEX Benders 1,022 s; instance sizes to 10 M vars/constraints; hardware stated; code on GitHub |
| Uncertainty | Bernoulli sampling; 5-trial mean ± SD for the hidden-false-negative case | 24–25 demand scenarios with duration-based probabilities |
| Analysis design | Rolling-origin 153-day backtest, do-nothing baseline, one strong information-asymmetry ablation, no sensitivity analysis | Solver/heuristic scalability study with a clear 40-node crossover, one worst-case operating bound, **no sensitivity analysis** |
| Visuals | 5 figures (time series, Pareto bar), 16 tables, no maps — and 3 of the 5 figures are near-duplicates | 7 figures (line chart, architecture diagram, 2 real basemaps, 3 route plots), 3 tables |
| Business case | Conditional decision rule + renegotiate investigator fees | Costed capex, ranked funding strategy, 7-year undiscounted payback |
| Honest limitations | Good (lists five real ones) | Good, but silent on the two worst flaws (mixed-unit objective, no sensitivity) |
| **Band estimate** | **Merit, ~65–72** | **Distinction, ~72–80** |

## What separates them

1. **Evidence discipline.** The bike report states model sizes, three solvers' runtimes, hardware, defaults and
   a repository, and prints "N/A / 1,000 s" where a method failed. The fraud report asserts "Model 1 is more
   scalable" with no timing at all. That single difference is most of the band gap.
2. **What the recommendation rests on.** Group_20's headline ("Model 2 cuts 85% vs 75% of losses") is driven by
   two hand-tuned thresholds and one unexplained 27× hiring-cost difference. The bike report's headline
   (£1.4 m, 7-year payback) rests on a costed capex plus a bounded operating cost — traceable, even though the
   station count itself comes from a mixed-unit objective.
3. **Both fail the same test.** Neither varies a decision parameter. Neither answers "what would change the
   recommendation" with a curve, a break-even or a breakpoint. This is the single most reproducible
   differentiator available to us: doing it at all puts a report above both of these examples.

## Three most valuable transferable devices

**1. Two-stage stochastic investment formulation with an explicit exact-vs-heuristic scalability table.**
Evidence: bike printed pp.4–5 (variables, objective, constraints 9–14), printed pp.8–9 and Table 3 (10 → 1,000
nodes; Xpress/Gurobi optimal to 40 nodes; no feasible solution beyond 40 within 1,000 s; adapted LKH-3 feasible
to 1,000 nodes with transit time degrading 3.3 h → 29.2 h).
Why it transfers: storage siting/sizing is the same object — irreversible integer first-stage decisions, a
scenario-weighted continuous second-stage recourse, a budget-style constraint, per-asset capacity limits. The
scalability table is a near-verbatim import: instance size (assets × horizon), variable/constraint counts,
objective value, solve time, and explicit "N/A at time limit" cells, which is what justifies choosing a
full-year MILP for the core case and a rolling-horizon LP or heuristic for the stress cases. Fix the bike
report's flaw when reusing: put a £ value on the second-stage term so capex and operating value share units.

**2. A bound-normalised KPI balance sheet plus a limited-information ablation with repeated stochastic runs.**
Evidence: Group_20 Tables 5, 7 and 13 (theoretical max loss £350,328.25 → detected £314,370 / £298,387 →
hiring cost → net loss → "% of losses cut"), and §5.3 printed p.9 (retrain with false negatives hidden; 5
trials; mean 263,188, SD 42,173; losses cut falling 84.63% → 53.59% ± 15.58%).
Why it transfers: the same table becomes the investment appraisal — perfect-foresight maximum arbitrage value,
value captured by the policy, degradation/cycle cost, net margin, and "% of the unattainable bound captured".
The ablation is the honest test of an investment case: the operator cannot observe what it would have earned on
hours it did not bid, so re-solving on realised-only outcomes and reporting mean ± SD over repeated runs is a
direct, defensible robustness claim. Note the arithmetic trap the fraud report did get right: keep the identity
max − captured + cost = net true in every column, and normalise the "%" to the stated bound, not to the other
model.

**3. A one-page decision block: worst-case operating-cost bound → ranked funding stack → payback → site map.**
Evidence: bike printed p.9 (worst-case rebalancing: 2 vans, 2 h cap, every node visited, 50% ± 5 bikes → 3.11 h
transit → £5,000 fuel + £17,520 labour = £22,520/yr) and printed pp.9–10 (pay-per-ride at £1 vs a £2.20 bus
fare → £200,000/yr → 7-year payback; then advertising to cover maintenance and rebalancing; then subsidy
negotiation), with the 40-station network drawn on a real basemap (Fig. 4).
Why it transfers: for an energy-storage investment the equivalent block is a bounded operating cost
(degradation, balancing, connection/constraint charges), a revenue stack in priority order (arbitrage →
capacity/balancing → subsidy), a payback or NPV headline, and a site map with the network overlaid. It is the
cheapest way to turn model output into something a board or council can act on — and the ranked-stack ordering
is what makes it read as advice rather than a model dump. Improve on the source by discounting the cash flows
and adding a break-even ridership/price sensitivity bar.

## Devices that are topic-specific — do not import

- Fraud: the 50:50 inter-bank reimbursement split, ATM/withdrawal filtering, Bernoulli sampling of "cases", the
  MLR classifier stage, the three supplied bank probabilities, PSR/APP regulatory narrative.
- Bikes: VRP/MTZ subtour machinery, LKH-3 penalty adaptation, OSRM transit times, docking capacity and
  bikes-per-station ratios, SIMD data zones, the max-covering/p-median lineage, crime and maintainability
  narrative, CO₂/car-journey arithmetic.
- From both: the habit of leaving every business parameter fixed; and the bike report's mixed-unit objective.

## Verification notes and limits

- Page anchors: Group_20 printed page = PDF page − 3; bike printed page = PDF − 2 (footers read directly).
- Counts are document-derived: Group_20 5 figures / 16 tables / 11 references; bike 7 figures / 3 tables /
  17 references. Headings and table indexes were not machine-extracted (`structure_index` =
  not_extracted), so counts come from reading every page, not from an index.
- Derived arithmetic flagged as mine in the profiles (e.g. precision/recall from the confusion matrices, the
  balance-sheet reconciliation checks) is labelled as derived, not as author-stated.
- Nothing in this batch was written outside
  `Tier1/workspaces/mocry/cleveruser/reference_review/`; no public file was modified; nothing committed.
