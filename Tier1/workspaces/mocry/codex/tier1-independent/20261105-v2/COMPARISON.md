# Tier 1 independent comparison, 5 November 2026

Comparison of [Codex v1](../20261105-v1/README.md), committed at `6fa0acb`, and [Clever User v1](../../../cleveruser/tier1/20261105-v1/README.md), read at `6ef271b`. Both builds use the repaired course data and the 1104 reference parameter family. The code and runs are separate implementations.

## Agreement on the reference decision

All 2,452 dates and quality flags match. Daily generation, demand, wind and real electricity price agree to the precision of the stored values. Across 18 matched 2023 portfolios and rules and 2022–25 fixed-size replays, both implementations select the same sizes and match hydrogen input to the CSV precision. The largest annual-value difference is £49.54, within rounding to £0.0001m in the CU table.

| Matched case | Codex v1 | CU v1 |
|---|---:|---:|
| 2023 A, economic allocation | 20 MW H₂, 0 MW battery, +£8.572m/year | Same |
| 2023 B, daily electricity priority | 0 MW added, £0 incremental | Same |
| 2023 B, fixed 20 MW H₂ | −£1.065m/year | Same |
| 2023 sale-first rule, fixed 20 MW H₂ | −£1.065m/year | Same |
| 2023 A, electricity to H₂ | 171.84 GWh | 171.84 GWh |
| 2023 A, avoided unused energy and diverted sales | 13.92 and 157.92 GWh | Same |
| 2024, fixed 20 MW under A / B | +£11.951m / −£0.998m per year | Same |
| 2025, fixed 20 MW under A / B | +£13.169m / +£4.478m per year | Same |

## Differences in method and scope

- The central models are equivalent for the matched cases. Both use integer equipment and online electrolyser counts, day-level energy balance, an annual battery pool and the same two operating policies. CU writes explicit unused generation and maximises total annual value. Codex derives unused generation from the balance and subtracts policy-matched zero-investment receipts in the objective. CU sets zero MIP stopping gaps. Codex uses a scaled incremental objective with tight tolerances and checks cases against the daily enumeration.
- CU places the full £46.88 commissioning charge per battery in each equivalent year. Codex books £49.41 upfront for loss-adjusted initial energy and annualises it to £4.76. The same £13,299 pooled operating gain before commissioning gives £13,252 after the CU convention, which accounts for its £13.25k statement. Codex also solves a chronological one-module case. Its £4,313 operating gain is below even the lower £11,146 fixed cost. CU's £6,990/MWh break-even purchase cost belongs to its annual-pool case with lower fixed costs.
- CU groups biomass and run-of-river hydro with wind and solar. Codex v1 tracks wind and solar separately. Recomputing the capture bound with either definition gives 0–13.92 GWh. CU's 7.3 GWh is a pro-rata allocation using the renewable share of generation on surplus days. The reports can agree on physical capture without identifying the fuel source.
- CU tests removing the simulated wind profile from system supply. Codex tests giving the equipment access only to that wind profile and giving background generation priority on demand. The latter changes the investment boundary and the counterfactual as well as device access. The two sensitivities answer different questions.
- CU has a wider scenario inventory, including 2020–21, partial 2026, the original price, a higher-offtake capacity ladder and more single-factor sweeps. Codex maps A and B on the same contract axes and adds chronological stock, a daily revenue ceiling for the battery, a joint contract downside, the wind-site boundary and explicit cash-flow timing. All fixed-size replays optimise dispatch using the realised path.

## Report comparison and revision

| Aspect | CU v1 | Codex choice for v2 |
|---|---|---|
| Opening and structure | The long report has a quick executive table and a separate decision sheet. The short cut gives the answer up front, then places seven distinct findings in one results subsection. | Keep the four-page sequence of system, model and matched results, contract and service trade-offs, and robustness and decision. Put the reference contract directly in the opening decision. |
| What the client can negotiate | The capacity ladder and sales floors of 99.9%, 99.99% and 100% are easy to act on. The 2.23 t/day break-even acceptance limit at £7.799/kg appears beside the £8.57m reference gain in the opening, though the gain comes from the 10 t/day case. | Keep the paired trigger map, give the 99.99% result, and use percentage floors with the GWh denominator in the table. Show the 10 t/day reference separately from the break-even boundary and the 50 t/day expansion. |
| Sizing explanation | The long report explains the extra module's incremental cost and volume, and the short cut emphasises the contract. | Give the explicit fixed 40 MW counterfactual under the same 10 t/day cap. It is feasible and earns +£7.47m/year, below 20 MW at +£8.57m/year. At 50 t/day A chooses 120 MW, with £175.25m initial capital and +£49.09m/year. |
| Returns | The cash bridge is easy to audit. CU's 2.789 years divides CAPEX by operating cash after an equivalent annual stack reserve. It also reports the 2.640-year operating-cash payback. | Keep the accounting bridge and label the actual cash basis separately. Report 2.64 years simple and 2.90 years discounted from the dated cash series. The 30-year NPV agrees at £131.78m. |
| Reviewability | The technical report, short cut, decision sheet and eight separate figures support different readers. Some text needs synchronising with the tables. For example, the 2020 A replay reads £16.72m in the prose table versus £16.7781m in the result CSV. | Use the result records to render the English text and PDF together. The four-page PDF has been visually checked. CU's four-page cut is Markdown, so pagination and final figures depend on how it is typeset. |

The four added contract-policy combinations were solved in Xpress and checked against enumeration. At the annual 99.99% sales floor, the model gives up 21.51 GWh and earns £1.039m/year. At 100% it selects zero. This annual comparison is separate from daily supply priority. The revision is a report and evidence update, with the original v1 results retained.
