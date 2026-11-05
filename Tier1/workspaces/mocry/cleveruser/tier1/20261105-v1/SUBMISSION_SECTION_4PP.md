# Tier 1 — submission section (4-page cut)

This is the trimmed version for the 10-page technical report. It uses the full package in `../TIER1_REPORT.md` and the figures in `../figures/`.

## 3.1 The question and the answer

The client's portfolio produced 215.7 TWh in 2023 against 245.8 TWh of demand: 87.5% of demand can be served, and 549.9 GWh of generation is stranded on 29 days when supply exceeds demand. The Tier 1 question is how much battery and/or electrolyser capacity is worth adding, and how much otherwise unused electricity it captures.

**The answer is 20 MW of electrolyser and no battery**, conditional on a hydrogen offtake of at least ~2.2 t/day at £7.80/kg and on the client being free to divert 0.07% of current electricity sales. The 20 MW module costs £29.2m, adds £8.57m/year, pays back in 2.6 years before stack replacement (2.8 years with the reserve), and captures 13.9 GWh/year of electricity that would otherwise be unused. Under a current-generation-first supply rule the same asset loses £1.07m/year in 2023.

## 3.2 Boundary, data and conventions

We use the five supplied tables in the independently repaired release (2,452 days, 2020-01-01 to 2026-09-17) and keep the course originals for comparison. The repair matters: the original price includes zero-volume placeholder providers and is about half the repaired value, and the original demand is truncated on the last day of each weekly query. Decisions use the repaired series; the originals are reported as a data sensitivity.

The supplied generation plus the specified wind farm is a constructed system, not observed curtailment. Demand is the absorption cap; there are no purchases, no extra export route and no curtailment payment. The analysis is daily and perfect-foresight, with no network constraints, intraday prices, ancillary markets or hydrogen storage. Money is constant 2020 GBP, deflated by ONS CPI; the discount rate is 5% real. The battery is the brief's 2-hour 1.5 MW / 3 MWh module with 90% round-trip and a 20–80% usable window; the electrolyser is a 20 MW PEM module at 55.9 kWh/kg; the hydrogen reference is £7.80/kg GBP2020, the policy-supported strike value (the brief's £9.5/kg in 2023 money is £7.91 in 2020 money).

## 3.3 Model

For day \(t\), generation \(G_t\), demand \(D_t\), price \(p_t\), the model chooses direct sale \(q_t\), battery charge \(c_t\) and discharge \(d_t\), electrolyser input \(h_t\), unused energy \(u_t\), operating modules \(z_t\), and installed units \(n_B,n_H\):

\[
\max \Pi=\frac{1}{Y}\sum_t\left[p_t(q_t+d_t)/1000+v\,h_t/55.9\right]-a_Bn_B-a_Hn_H
\]

subject to \(q_t+c_t+h_t+u_t=G_t\), \(q_t+d_t\le D_t\), the battery charge/discharge caps, the module limits \(0.096z_t\le h_t\le0.48z_t\le0.48n_H\), the offtake cap \(h_t\le55.9L/10^6\), and the annual battery balance \(\sum_t d_t=0.9\sum_t c_t\). Policy A lets the model allocate each day's generation economically. Policy B adds \(q_t=\min(G_t,D_t)\): current generation serves current demand first. Costs use a capital recovery factor by asset life (15 years battery, 30 years electrolyser), fixed O&M, and stack replacement at years 11 and 22, discounted and annualised.

The annual battery balance is the Tier 1 time simplification and is an upper bound on battery value; no selected configuration uses a battery, so it cannot change the recommendation. One design-year case has 2,556 rows and 2,192 columns, solves to proven optimality in under 0.1 s with Xpress, and 185 optimisation cases plus 2 rule-based comparators were run. Twenty independent checks pass.

## 3.4 Results

**Configuration comparison (2023, £m/year incremental versus the matching no-investment case).**

| | No investment | Battery only | H2 only | Both | Rule-based 20 MW |
|---|---|---|---|---|---|
| A: economic allocation | 0 | 0 | **+8.57** | +8.57 | −1.07 |
| B: current generation first | 0 | 0 | 0 | 0 | −1.07 |

The battery is never selected. The same 20 MW asset is worth £9.64m/year more under optimised dispatch than under a simple "sell first, then make hydrogen" rule; that difference is the value of dispatch.

**Where the electricity comes from.** The 171.8 GWh electrolyser input splits exactly into 13.9 GWh of electricity that would otherwise be unused (8.1%) and 157.9 GWh diverted from direct sale (91.9%). On the 29 surplus days the renewable share of generation is 52.7%, so a pro-rata attribution of the captured energy is about 7.3 GWh; at daily resolution the strict renewable bound is 0–13.9 GWh. The honest headline is that 8% of the hydrogen input is avoided waste and 92% is an alternative use of saleable electricity.

**Why no battery.** At zero capital cost and zero FOM, a 1.5 MW unit is worth £13.25k/year; the primary FOM alone is £22.3k per unit, so no unit is economic at any non-negative capital cost. With the lower table-based FOM the break-even capital cost is £7.0k/MWh, about 37 times below the brief's €288k/MWh (£256k/MWh). This is a Tier 1 time-resolution result: intraday arbitrage, frequency response and firming value are outside the daily model and belong to Tier 2B. Because the annual-pool model overstates battery value, the conclusion is robust.

**Why 20 MW.** The module produces at most 8.59 t/day, just under the 10 t/day buyer cap. The capacity ladder is driven by the contract, not by the surplus: 0 MW at ≤2 t/day, 20 MW at 5–10 t/day, 40 MW at 15 t/day, 60 MW at 20 t/day, 80 MW at 30 t/day and 120 MW at 50 t/day (+£49.1m/year). At 10 t/day the investment switches on at a netback of £4.62/kg; at £7.80/kg it needs 2,230 kg/day; at £9.5/kg, 1,717 kg/day.

**Financial case.** Hydrogen revenue £23.97m/year, electricity revenue forgone £12.39m, fixed O&M £0.52m, stack reserve £0.59m and capital charge £1.90m give the net £8.57m. The 30-year NPV at 5% on constant reference-year operation is +£132m; this is a scenario value, not a forecast, because it assumes no hydrogen-price decay, no degradation and no terminal value. If the buyer takes 50 t/day, the model builds 120 MW with £175m of capital and a £49.1m annual increment.

**Cross-year robustness.** Fixing 20 MW and replaying each year, A gives +£16.72m (2020), +£6.29m (2021), +£8.91m (2022), +£8.57m (2023), +£11.95m (2024), +£13.17m (2025) and +£12.85m (2026 to 17 September). B gives +£3.11m, −£0.13m, +£7.31m, −£1.07m, −£1.00m, +£4.48m and +£7.01m. The investment is positive in every year under A, with 2021 the weakest; under B it loses money in 2023–24. The spread is business risk: the asset depends on the freedom to allocate generation.

**What changes the recommendation.** Electrolyser CAPEX over £0.82m–£1.65m/MW gives +£9.41m to +£8.33m with capacity unchanged. A real discount rate of 0–12% gives +£9.44m to +£6.99m, capacity unchanged. The strict 2023 sample gives +£8.69m; removing the independent farm gives +£8.13m; the unrepaired price would give +£15.19m and is not used. The sharpest test is the supply obligation: the 20 MW case gives up 157.9 GWh, 0.073% of current sales. A 99.9% floor still allows the full £8.57m; a 99.99% floor allows only 35 GWh of hydrogen and £1.04m; a 100% floor excludes the investment.

## 3.5 Validation and limitations

Every stored plan closes its daily energy balance, respects the demand, charge/discharge, module and offtake caps, uses integer units and satisfies the annual battery balance; revenues and costs are recomputed from the plans. The reference cases reproduce the independently built Baseline 1104 package (A0 17,139.332; 20 MW +8.572; B fixed 20 MW −1.065; simple rule −1.065; 2024 +11.951; old price +15.188), which is arithmetic agreement between two implementations, not an endorsement of shared assumptions.

Limitations: daily averages remove intraday value; the annual battery balance is a relaxation; the model is perfect-foresight; the hydrogen value is a policy-supported reference, not a contract; CAPEX is a modern installed midpoint while FOM and stack replacement use older UK absolute proxies; there is no degradation, hydrogen storage, network constraint or ancillary market; 125 days have imputed fuel composition (85 in 2023), so the renewable attribution is conditional on the repair; 2026 is partial.

## 3.6 Recommendation

1. No battery in Tier 1 at the brief's cost; re-open only with intraday/ancillary revenue or a capital cost near £7k/MWh.
2. Negotiate the hydrogen contract first: at least ~2.2 t/day at £7.80/kg (or ~1.7 t/day at £9.5/kg); below £4.62/kg, do not build.
3. Build 20 MW only with the contract and the operating mandate (freedom to divert about 0.07% of sales).
4. Stage the expansion: 20 MW for a 10 t/day contract, 120 MW for 50 t/day; do not pre-build.
5. Report the capture honestly: 13.9 GWh avoided waste (8% of input), 157.9 GWh diverted from sale (92%).
6. Keep the supply-first alternative visible: under B the same asset loses money in 2023–24, so a current-generation-first obligation means no investment.
