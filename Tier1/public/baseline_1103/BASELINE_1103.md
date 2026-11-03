# Deterministic Tier1 — Baseline 1103

Version: 2026-11-03. Proposed by Mocry. Status: common structure and A/B family defined; research-dependent parameterisation and team adoption are pending. References: [teacher evidence](TEACHER_CLARIFICATIONS.md), [gap IDs](GAPS.md), [research request](RESEARCH_REQUEST.md).

## BL-01 — study purpose and investment boundary

Assess whether adding batteries and/or electrolysers improves the given starting system. Existing generation is fixed, not a Tier1 investment decision. Initial device type/count/capacity is chosen once per evaluation run; daily operation cannot resize it with hindsight. No additional generation CAPEX is charged merely because the specified farm curve originated in a development-project simulation.

The no-addition case and battery-only, electrolyser-only and combined additions are comparable investment alternatives. Zero additional capacity is admissible.

## BL-02 — given generation and demand connection

Use given total generation plus the specified independent simulated wind profile. Total already aggregates fuel-level rows, including wind technologies. The independent-farm addition/non-inclusion is our constructed-system connection convention, not a teacher-confirmed facility accounting fact.

After verifying daily power definitions, convert average MW to daily MWh consistently. Denote resulting available energy by G_t and given system demand by D_t. Demand is the system's sales/absorption limit, not an extra unpaid company internal load. Additional external markets require an explicit, common R1 market scenario; missing market data do not automatically erase D_t.

## BL-03 — fixed generation, pooled energy and network

All given generation is exogenous and non-dispatchable in the baseline. Pool energy for physical/economic allocation, preserving technology data for reporting. A renewable-specific claim requires source attribution; otherwise use total-energy metrics. Ignore location/transmission constraints under the classroom simplification.

## BL-04 — time and information

Use daily granularity, actual chronology and known generation/demand/prices within each Tier1 optimisation run. Every observed day has statistical weight one. Financial discounting is separate from those observation weights. Daily data do not reveal intraday price spreads or establish the full revenue potential of a two-hour asset.

## BL-05 — regime A: economic allocation

Choose direct electricity sales, battery charging/discharging, H2 production and unused generation jointly to maximise scheme profit, within physical and market limits. There is no hard full-demand guarantee or baseline monetary deficit penalty. Forgoing current sales to charge or make H2 is allowed. Unserved demand and unused generation are measured.

## BL-06 — regime B: current-generation supply priority

Proposed executable interpretation of the user's priority policy: let q_t be direct electricity supplied from current given generation, distinct from battery discharge and imports. Require:

$$
q_t=\min\{G_t,D_t\}.
$$

Only current generation remaining after that allocation may be charged, converted to H2 or discarded. Battery discharge may serve remaining demand, subject to market limits and economic operation. This policy does not impose obligatory battery depletion or unlimited purchases to eliminate all unmet demand. Supply priority remains binding during negative-price periods; its profit consequences are part of the A/B comparison.

The implementation must track direct current-generation sales so imports or battery output cannot silently substitute for the mandated generation allocation. A stronger supply-guarantee policy would be a separately labelled change, not an implicit implementation of B.

## BL-07 — shared technology and trade constraints

A and B use identical equipment candidates, installation bounds, cost schedules, lifetime, efficiency and operating constraints. Respect energy balance, battery power and energy limits, SOC range, losses and electrolyser operating/shutdown rules. Specify source/destination routes and disallow duplicate sales or energy creation.

R1 determines whether purchases and extra sales channels are supported, their prices, fees, capacities and restrictions. Purchases are disabled until an admissible documented interface exists. If enabled, use a finite justified trading/investment domain. Do not create an unlimited import-to-H2 business from unsupported infinite offtake/capacity assumptions.

## BL-08 — batteries and H2 outlet

Keep brief reference parameters documented: two-hour battery, 90% roundtrip efficiency and 20%–80% normal SOC. R2 proposes sourced alternatives/modules and explains deviations, rather than silently changing the brief. Current-technology candidates may be tested on historical conditions; no product launch-year constraint is needed for this explicitly present-technology counterfactual.

Electrolyser capacity is a decision; the 20MW PEM reference is not a fixed answer. Keep 55.9kWh/kg and the written operating range as documented reference values while R3 researches suitable equipment. Specify shutdown separately from minimum operating load.

Direct H2 sale is the minimum baseline outlet, with researched sale conditions/limits. The written GBP9.5/kg supported benchmark is a price scenario, not guaranteed offtake. Storage, transport, compression and reconversion are separate costed modules when materially required/adopted. Do not assume all these services are free.

## BL-09 — primary objective and cost accounting

Maximise absolute scheme net profit/net benefit, not an additional standalone supply-coverage reward:

$$
\max\Pi = R_{\mathrm{electricity}}+R_{\mathrm{H2}}
-C_{\mathrm{new\ investment}}-C_{\mathrm{purchase}}-C_{\mathrm{affected\ operation}}.
$$

Use one declared financial horizon and cost/discount basis for every compared scheme. Under the earlier discounting proposal, apply the chosen discount factors consistently to cash flows and label the result discounted net benefit (NPV); annual-equivalent reporting must likewise treat CAPEX consistently. Do not compare one year of sales with a full-lifetime cost as if that alone were a lifetime investment result.

Fixed existing sunk CAPEX and unchanged costs can cancel in incremental comparisons. All costs changed by operation/investment remain, including replacement or residual value where relevant. Electricity used for H2/charging is unavailable for direct sale; the full sales balance represents that opportunity cost without charging it twice.

## BL-10 — four principal comparisons

| Scheme | Policy | Additional equipment |
|---|---|---|
| A0 | Free allocation | None |
| A1 | Free allocation | Optimised battery/electrolyser additions |
| B0 | Current-generation priority | None |
| B1 | Current-generation priority | Optimised battery/electrolyser additions |

Report deltaPi_A = Pi_A1 - Pi_A0 and deltaPi_B = Pi_B1 - Pi_B0, as well as absolute profits. Baseline constants need not appear in the optimisation objective. If B only restricts A with identical accounting and feasible equipment, optimal absolute profit A1 must be at least B1. Incremental improvements need not share that ordering because A0 and B0 may differ. Full-period coverage in B is not automatically superior after investments change; measure it.

## BL-11 — data and state boundaries

Raw root files stay unchanged. Build a documented date intersection and a deterministic adjustment log. Keep negative prices and genuine extreme supply/demand/price events. Statistical rarity alone is not proof of a data error. Any fitted cleaning threshold is estimated on training data only.

Recommended implementation defaults for review: start with no usable stored battery energy above the minimum-SOC buffer; apply the same terminal usable-energy condition; account for commissioning energy if relevant. Do not create free initial usable energy or a terminal inventory subsidy. Do not join dates across an unmodelled gap as adjacent days. Choose documented continuous segments or a supported gap-handling method, with coverage loss disclosed. The chosen daily charge/discharge/throughput convention belongs in the run manifest.

## BL-12 — research interfaces and run manifest

R1 supplies trade routes/limits/prices; R2 equipment/cost/operation candidates; R3 electrolyser and H2 outlet/cost conditions; R4 data units, financial conventions and evaluation/implementation checks. Each parameter has a unit, source date, applicable scope, recommended value and uncertainty/sensitivity range. The parameterised run records which researched recommendations and departures were adopted.

## BL-13 — historical design and held-out checks

Choose chronological fitting/evaluation years after data-quality inspection; do not select them to maximise held-out profit. Investment is fixed after fitting. Distinguish:

1. Training-selected capacity with an operational policy fitted only on available earlier information.
2. Training-selected capacity with full validation-path operation: a fixed-capacity operational oracle.
3. Validation-only design/operation oracle, with matched horizon/cost/boundary conditions.
4. All-years design oracle, a full-sample hindsight reference that need not dominate on the validation subset.

If validation results guide repeated model selection, retain a final untouched test period. Tier1 perfect-information analysis can be completed before developing causal operation; the latter supports the optional time/uncertainty extension. Current equipment evaluated under historical conditions is a counterfactual, not a claim that a historical investor knew those products or future observations.

## BL-14 — outputs and tests

Report absolute and incremental profit, CAPEX/capacity, cash-flow components, payback metrics where defined, energy sold/H2/unused energy, demand coverage/deficit and battery usage. Check energy and money independently, zero-investment cases, device limits and solver status/gap. Compare simple alternatives under the same information/cost boundaries.

## BL-15 — sensitivity/ablation tags, not baseline requirements

- Remove the independent wind profile while leaving other inputs/accounting matched.
- Research-backed dispatchable generation with real costs/capacity/operating limits.
- Alternative trade channels, import tariffs, absorption limits, price impact and curtailment economics.
- Technology/cost/H2-value/discount ranges, commercial module sizes and discounts.
- Genuine-extreme-inclusive versus explicitly tail-excluded datasets; do not call both ordinary data cleaning.
- Dynamic equipment acquisition, hydrogen storage/reconversion, network constraints and causal operation where selected for an extension.

These are candidates for prioritisation, not a promise to implement every feature. Anyone may propose additions, removals or changes using the ID system and agent messages. Only recorded adoption changes the shared model specification.
