# Independent research and cross-validation request — 1103

Status: ready for Mocry to dispatch; no named external researcher has been started or registered by publishing this request. No completed research result is implied.

## Request to Mocry

Please arrange targeted independent research and subsequent cross-validation using the following requested model/harness labels:

- GPT-6 Astra.
- GPT-6.1 Sol / Codex research agent.
- DS v4.1 flash1017 / Clever User agent.

These are the owner's requested labels, not verified runtime metadata. Each actual researcher records its observed model/version, harness/version, timestamp, scope and limitations when registering/submitting. Do not invent a result or registration for an agent that has not run.

There are four initial work packages. Mocry may dispatch each researcher over all four, or allocate subsets while retaining independent overlap across every important package. Suggested default: each researcher examines all four at a useful level, flags its strongest evidence, then cross-checks the others' high-impact claims. Allocation and any deadline are for Mocry to set; none is fabricated here.

## Shared input pack

Give each researcher the original [brief](../../../Project_Brief.pdf), [project overview](../../../PROJECT.md), [complete transcript](../../../Project_Launch_Transcript.txt) with [time-indexed version](../../../Project_Launch_Transcript_Timed.txt), five root CSVs, [teacher clarifications](TEACHER_CLARIFICATIONS.md), [gap register](GAPS.md), and [Baseline 1103](BASELINE_1103.md).

First-pass researchers should not read peers' findings before producing their own evidence/parameter recommendations. They may challenge the baseline; they should distinguish a factual correction, a parameter estimate and an alternative modelling choice. Preserve the first-pass output before cross-review.

## R1 — electricity markets and trading

Closes E-01–E-07 and informs M-01/M-03/M-04.

Investigate relevant UK sale/offtake arrangements, interpretation of the supplied wholesale price, absorption/export limits and data, admissible grid purchases, import/export tariff differences/fees, negative prices, transaction restrictions, market-volume effects and unused-generation/curtailment treatment. Distinguish real market rules from the project's deliberately simplified system.

Deliver: a usable baseline trading interface (routes, eligibility, units, prices/fees and finite limits), an explicit mapping of given demand versus any extra outlet, recommended fallbacks for unavailable evidence, and sensitivity/alternative-market scenarios. Explain when a price-taking assumption is adequate and what cannot be estimated from daily data.

## R2 — batteries

Closes B-01–B-06 and informs M-05/M-07/M-09/M-10.

Investigate suitable commercial systems/technologies and module grids, MW/MWh/nameplate/usable capacity, two-hour configuration, charge/discharge limits/efficiencies, SOC, calendar/cycle life, degradation, warranty, installed CAPEX boundaries, maintenance/replacement/disposal/residual costs, commercial price grids and bulk discounts. Explain uncertainty where actual quotes are unavailable.

Deliver: a sourced candidate catalogue and normalised cost/technical table suitable for optimisation, baseline choices and ranges, recommended daily-model throughput conventions, and reasons for any departure from the brief. A broad catalogue is welcome; mark which candidates are comparable rather than pretending the whole market has been exhaustively priced. Current products can be tested on historical conditions without assuming historical commercial availability.

## R3 — electrolysers, H2 storage and market

Closes H-01–H-07 and informs M-05/M-09/M-10.

Investigate PEM/reference products and justified alternatives; module size, installed CAPEX and scope; electricity use, load/shutdown limits, stack life, balance of plant, water/compression/maintenance/replacement; credible H2 prices/offtake/demand/delivery quality; policy eligibility versus guaranteed revenue; storage and transport requirements; optional reconversion economics.

Deliver: a normalised equipment-and-product-outlet interface with investment/operating costs, efficiency, finite capacity/offtake conditions, a minimal direct-sale baseline and optional costed storage/reconversion modules. Test low/core/high H2 values and identify unsupported assumptions, especially any combination implying unlimited profitable expansion.

## R4 — miscellaneous data, finance, implementation and missing topics

Closes F-01–F-03, D-01–D-03, V-01; optionally X-01.

Investigate consistent base currency/price year, FX/inflation, real/nominal and effective-annual discounting, risk-free comparison versus investor hurdle rate, evaluation horizon, investment/replacement/residual/payback accounting; exact daily power/energy and price units; date/quality/gap/state conventions; historical design/validation/oracle fairness. Suggest meaningful solver/energy/cash-flow validation and a runtime pilot, without claiming unrun hardware benchmarks.

Optional: research which UK generation technologies can be dispatched and what capacities/costs/operating restrictions would be needed for a labelled extra scenario. Identify additional material gaps missed by R1–R3 rather than hiding them in a generic assumption.

Deliver: a financial/data/run interface, recommended conventions and sensitivity values, unit/normalisation checks, and any new justified research packages. Normative choices remain explicit choices, even when evidence is strong.

## Result form and aggregation

Use [RESEARCH_RESULT_TEMPLATE.md](RESEARCH_RESULT_TEMPLATE.md). Supply a readable report plus machine-readable parameter tables where useful. Each adopted-capable claim needs a source/date/location, unit and scope; record weak evidence and missing prices honestly. Prefer primary regulations, market documentation, manufacturer datasheets and public technical/financial studies. Avoid double-counting multiple websites repeating one original source as independent confirmation.

More research is welcome: other members and agents can independently cover any package, add a fifth topic or revisit a disputed parameter. Do not wait for named researchers to finish. Register, identify the scope, work in your own folder, then publish a uniquely named result such as `research_1103/R2/<agent-id>/<result-id>/REPORT.md` and notify the group.

Aggregation records each claim, source, competing values, cause of disagreement, recommended baseline value/range and the decision to adopt/defer. Preserve original independent results; publish a new synthesis rather than rewriting them into apparent consensus. Cross-review should reproduce important conversions/cost calculations and check applicability, not vote by model count.

## Open review of the entire starting package

All members/agents may challenge teacher interpretation, propose a missing gap, simplify research, adjust A/B policy semantics, question the financial objective or replace a baseline assumption with a reasoned alternative. Use IDs and describe impact. Send suggestions through the message area; nothing in this request implies that the current proposal is immune to revision.
