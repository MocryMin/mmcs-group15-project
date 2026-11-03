# Information gaps and modelling decisions

Read the teacher evidence first. A gap is not automatically a question for the teacher: some call for evidence, others require a documented team choice. Baseline 1103 already proposes choices for several gaps. New findings may challenge them through a recorded proposal.

Types: **research** (external evidence/parameters), **discussion** (business or modelling choice), **implementation** (precise numerical convention), **requirement** (course rule needing confirmation).

## M — model and system choices

| ID | Gap | Type | Current position / next step |
|---|---|---|---|
| M-01 | How national total, separate farm and demand form the studied system | Discussion | Proposed: fixed total + independent farm, demand as system absorption cap. Inclusion is a model convention; alternatives require explicit change |
| M-02 | Meaning of supply priority | Discussion/implementation | A free allocation; B current-generation direct supply first. Stronger battery depletion or mandatory purchases are not implied |
| M-03 | Scheme profit definition and financial horizon | Discussion + R4 | Choose one consistent cash-flow/discount/horizon convention for A/B and comparators; research supplies values and recommendations |
| M-04 | Optional buying, extra sales outlets, price impact and curtailment treatment | Research/discussion + R1 | Default closed set of documented routes; no automatic unlimited extra market |
| M-05 | Technology/size grids and finite admissible investment domain | Research + R2/R3 | Sourced candidate set; distinguish physical, commercial and arbitrary numerical bounds |
| M-06 | Source attribution of pooled electricity | Discussion | Pool for economic balance; renewable-specific KPIs require provenance/attribution, otherwise label total-electricity KPIs |
| M-07 | Chronology, commissioning, initial/final inventories and gap days | Implementation + R4 | No free initial usable energy; state boundary and missing-day conventions documented before solving |
| M-08 | Perfect-foresight vs trained-capacity vs causal validation | Discussion/implementation + R4 | Keep separate experiments and labels; validation-only oracle upper bound requires matched accounting |
| M-09 | Single-investment vs dynamic acquisition/replacement decisions | Discussion + R2/R3/R4 | Baseline sizes at start; replacement/lifetime accounted consistently; dynamic acquisition is an extension |
| M-10 | Which departures from brief technical references to adopt | Discussion + R2/R3 | Log source, reason and effect; reported battery-cost permission is not a blanket original teacher quote for every parameter |

## R1 — electricity market

| ID | Needed information |
|---|---|
| E-01 | Relevant UK wholesale/offtake arrangements; how supplied price relates to actual feasible sales |
| E-02 | Demand/absorption/export limits and any additional outlet; data coverage and scope |
| E-03 | Whether purchases are admissible; purchase tariff, fees, taxes relevant to chosen scope, access and quantity limits |
| E-04 | Import/export price differences, negative-price treatment, simultaneous trade restrictions and arbitrage conditions |
| E-05 | Evidence for price taking or quantity-dependent price/market impact, with parameters if available |
| E-06 | Curtailment/unused-generation economic treatment: opportunity cost, charges, compensation eligibility and double counting |
| E-07 | Which network/locational constraints are intentionally omitted under TC-07, versus optional research scenario |

## R2 — batteries

| ID | Needed information |
|---|---|
| B-01 | Suitable commercial technologies/products, power and energy sizes, module grids and two-hour compatibility |
| B-02 | Installed-system CAPEX boundary, balance-of-plant/connection costs, bulk discounts, currency and price year |
| B-03 | Charge/discharge limits and efficiencies, usable/nameplate energy, SOC operating range, standby losses |
| B-04 | Calendar/cycle life, degradation, warranties, maintenance, replacement and residual/disposal value |
| B-05 | Evidence of price/parameter uncertainty and sensitivity ranges; any unsupported quotation gaps |
| B-06 | What daily data can support for a two-hour asset; conservative throughput/cycle assumptions and missing intraday value |

## R3 — electrolysers, H2 storage and markets

| ID | Needed information |
|---|---|
| H-01 | PEM and justified alternatives; products/modules, capacity grids and installed-cost boundaries |
| H-02 | Electricity consumption, minimum stable load/shutdown, efficiency variation, ramp/startup if material |
| H-03 | Balance of plant, water, compression, maintenance, stack life/replacement and other operational costs |
| H-04 | Plausible sales price, buyer/demand scale, quality/delivery conditions, policy support and eligibility; benchmark vs guaranteed revenue |
| H-05 | Storage, transport and sale timing: costs, losses, capacity and why required or optional |
| H-06 | Optional reconversion: equipment, efficiency and economics, kept separate from direct-sale baseline |
| H-07 | Parameter ranges and combined market/equipment bounds that prevent unsupported unbounded expansion |

## R4 — miscellaneous data, finance and implementation

| ID | Needed information or decision |
|---|---|
| F-01 | Base currency/year, exchange rates, inflation and consistent real/nominal cash-flow treatment |
| F-02 | Evaluation horizon, effective annual discount/hurdle rate, risk-free comparison and sensitivity |
| F-03 | Investment/operating/replacement costs, residual value, annualisation and comparable payback metrics |
| D-01 | Dataset definitions, daily MW-to-MWh convention and price-column consistency |
| D-02 | Date intersection, duplicates, actual errors vs genuine extremes, retained coverage and missing-day treatment |
| D-03 | Chronological training/validation/test splits, preprocessing fit boundary, capacity and operation information sets |
| V-01 | Runtime/model-size pilot on available hardware, solver status/gap, energy/cash-flow checks |
| X-01 | Optional source-backed generation dispatchability scenario: capacities, costs and constraints, not baseline free redispatch |

## Q — course requirements still outside this model definition

Report counting of references/appendices/cover; detailed marking grid; code/data submission instructions; pitch duration and group slot are not resolved by choosing a baseline. Seek the actual course rule when needed. This research request does not authorise contacting teachers, sending mail or submitting coursework.

## Review and change process

Members may add gaps, dispute evidence, simplify unnecessary questions or propose different baseline choices. Cite the ID, show what is missing, propose a resolution and explain which experiments change. Publish a new contribution and message; do not silently convert a proposal into a teacher rule. Aggregate research by claim/evidence, retaining conflicts and unfilled cells.
