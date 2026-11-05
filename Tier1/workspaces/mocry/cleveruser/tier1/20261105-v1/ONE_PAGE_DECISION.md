# One-page investment decision — Tier 1 (2023 design year)

**Client question:** how much battery and/or electrolyser capacity should we add, how much unused renewable electricity will it capture, and is it worth the capital?

**Decision:** build **20 MW of PEM electrolyser** and **no battery**, subject to the contract conditions below.

| | |
|---|---|
| Capital | £29.2m |
| Annual net value | **+£8.57m/year** (hydrogen revenue £23.97m, electricity sales forgone £12.39m, FOM £0.52m, stack reserve £0.59m, capital charge £1.90m) |
| Payback | 2.6 years before stack replacement; 2.8 years with the stack reserve |
| ROI / NPV | 29%/year; +£132m over 30 years at 5% real on constant reference-year operation |
| Unused electricity captured | 13.9 GWh/year (8.1% of the 171.8 GWh input; 2.5% of the 549.9 GWh annual surplus) |
| Electricity diverted from sale | 157.9 GWh/year (0.073% of current sales) |
| Hydrogen output | 3,074 t/year (8.4 t/day against a 10 t/day buyer cap) |
| Battery | none: £13.25k/unit/year of value against £96k/year of cost; break-even capital cost £7k/MWh (lower FOM), none at the primary FOM |

**Three conditions. If any fails, do not invest.**

1. **A buyer for at least ~2.2 t/day at £7.80/kg** (or ~1.7 t/day at £9.5/kg). Below £4.62/kg the investment is loss-making at 10 t/day.
2. **Freedom to allocate generation economically** — the client must be allowed to divert about 0.07% of current electricity sales to hydrogen. Under a current-generation-first obligation the same 20 MW loses £1.07m/year in 2023 and £1.00m in 2024.
3. **A site netback consistent with £7.80/kg.** The £9.5/kg brief value is a policy-supported benchmark, not a contract; every £1/kg below the reference removes roughly £3.1m/year at 20 MW.

**Do not pre-build for a larger contract.** The 20 MW size is set by the 10 t/day cap, not by the size of the surplus. At 50 t/day the model builds 120 MW (capital £175m, +£49.1m/year); at 30 t/day, 80 MW; at 15 t/day, 40 MW. Stage the investment with the contract.

**Do not buy batteries for this project in Tier 1.** At the brief's €288k/MWh the annual cost of a 1.5 MW unit is about seven times its modelled value. The daily Tier 1 model cannot see intraday arbitrage, frequency response or firming value; if the client wants a storage case, it needs an intraday Tier 2B analysis and an explicit ancillary-revenue assumption.

**Year risk.** With the size fixed at 20 MW, the annual value under economic allocation ranges from +£6.29m (2021) to +£16.78m (2020) across 2020–2026 and is positive every year. Under the supply-first rule it is negative in 2023–24. Headline figures use 2023, the design year.

**Next steps.** (1) Secure a term sheet for ≥2.2 t/day at ≥£7.80/kg netback. (2) Confirm the operating mandate and metering boundary. (3) Order 20 MW; hold expansion until the contract expands. (4) Re-run the trigger map when the term sheet arrives; the model is parameterised, not hard-coded.

*All values constant 2020 GBP, repaired price series, 5% real discount rate, perfect-foresight daily operation. Baseline 1104 is an independent comparison, not a group-adopted plan. Full evidence: `TIER1_REPORT.md`, `results/results.json`, `VERIFICATION.json`.*
