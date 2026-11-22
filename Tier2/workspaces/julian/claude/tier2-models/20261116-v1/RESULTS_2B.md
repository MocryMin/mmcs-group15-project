# Tier 2B results: daily operation under limited information

中文版：[RESULTS_2B_ZH.md](RESULTS_2B_ZH.md)

## Starting point

Tier 1 concludes that only an electrolyser is built, with no battery, and that hydrogen is sold up to a limit of 10 t a day. Without storage each day is solved independently, and neither the order of days nor forecasting matters. For 2B to have any content, there must first be a mechanism through which today's decision affects tomorrow. Two were tried here.

## Mechanism 1: a hydrogen buffer tank (does not work)

The electrolyser and a tank are optimised together, using the DEA steel-tank cost from the group's research (about £185 per usable kg per year):

| Tank cost | Tank chosen under policy A | Tank chosen under policy B |
|---|---:|---:|
| Researched cost | 0 | 0 |
| 25% of the researched cost | 0 | 0 |
| 5% of the researched cost (close to a salt cavern) | 20 t | 26 t |
| Free | 4,202 t | 5,435 t |

A steel tank would have to be about 95% cheaper before it is chosen. This route does not work.

## Mechanism 2: a settlement window in the offtake contract (the main model)

Instead of buying storage, change the contract. The buyer accepts the same quantity, but it is settled on the total over W days (W = 1 is the daily contract of Tier 1). Production can move to the cheapest days in the window, provided the electrolyser has spare capacity. Each day the operator faces exactly the problem the lecturer described: use the quota today, or keep it for a tomorrow that may be cheaper.

- **Design**: the electrolyser capacity is chosen on 2020–2022 with perfect foresight and then frozen.
- **Operation**: 2023–2025 is replayed day by day, and each rule sees only the past.
- **Rules compared**: an even daily share; greedy; a price-quantile threshold; rolling optimisation with a naive forecast; rolling optimisation with a ridge-regression forecast re-estimated at the start of each year; perfect foresight.

## Main results

**1. Seen through time, the Tier 1 design behaves very differently under the two policies.**

| | Policy A | Policy B |
|---|---:|---:|
| Payback date (investment at the start of 2020) | April 2022 | Not paid back within six years |
| Share of days with production | 89% | 21% |
| Longest continuous shutdown | 36 days | 302 days |
| Years with a negative net gain | None | 2021, 2023, 2024 |

Under policy B the electrolyser uses only surplus and stands idle on four days in five. No buyer who needs a steady hydrogen supply would accept this.

**2. The value of the contract window is small even with perfect foresight.** Over the whole history:

| Settlement window | Policy A net gain £m/yr | Electrolyser MW | Policy B net gain £m/yr | Electrolyser MW |
|---:|---:|---:|---:|---:|
| 1 day | 12.74 | 23.3 | 2.46 | 23.3 |
| 7 days | 12.91 | 27.2 | 2.72 | 32.6 |
| 28 days | 13.21 | 31.1 | 3.11 | 38.4 |
| 365 days | 15.27 | 47.6 | 5.92 | 76.8 |

A weekly contract adds only 1.3% under policy A.

**3. Under policy A, a weekly contract is actually worse without foresight.** For 2023–2025, net gain in £m a year:

| Operating rule | 7-day window | 28-day window |
|---|---:|---:|
| Daily contract (Tier 1) | 13.08 | 13.08 |
| Greedy | 12.48 | 12.11 |
| Price threshold | 12.74 | 12.93 |
| Rolling optimisation, naive forecast | 12.84 | 12.91 |
| Rolling optimisation, ridge regression | 12.95 | 12.76 |
| Perfect foresight | 13.24 | 13.44 |

Perfect foresight would earn £0.16–0.37m a year more, but every rule that could be used in practice earns £0.12–0.97m a year less than the daily contract. The extra electrolyser capacity costs about £0.58m a year, and forecasting does not recover that money.

**4. The reason is that forecast skill is gone after two days.** Mean absolute error for the electricity price: one day ahead, £11.2 for ridge regression against £13.5 for the naive forecast; from three days ahead the two are level. The supply–demand gap also has an advantage only one day ahead (34 against 42 GWh), and it has largely disappeared by day seven. A weekly window needs exactly the information about a week ahead.

**5. Under policy B a weekly contract helps, and it needs no forecast.** When only surplus is used, greedy is already optimal (in the model, greedy and perfect foresight give the same result). The 2023–2025 net gain rises from £0.93m to £1.19m (weekly) or £1.26m (monthly). The absolute amounts are small.

## What would change the conclusion

Difference between rolling optimisation on a weekly contract and the daily contract, policy A (£m a year):

| Scenario | Difference |
|---|---:|
| Central scenario | −0.12 |
| Hydrogen netback £6/kg | −0.14 |
| Hydrogen netback £10/kg | −0.55 |
| Electrolyser cost −30% | −0.13 |
| Electrolyser cost +30% | 0.00 (the electrolyser is no longer enlarged) |
| Offtake 100 t/day | −1.40 |
| Electricity price ×0.5 | −0.35 |
| Electricity price ×1.5 | +0.05 |
| Price volatility doubled | −0.31 |

Only one of the nine scenarios is marginally positive. The conclusion is robust.

## Advice for the client

- **Policy A**: keep the daily contract and operate with the simplest rule, which is to run whenever the electricity price is below £139.5/MWh (the break-even for hydrogen). Do not enlarge the electrolyser for the sake of flexibility, and it is not worth building a forecasting system for this plant.
- **Policy B**: if supply must come first, negotiate weekly or monthly settlement with the buyer. The gain rises by about 30%, and the operating rule is to produce whenever there is surplus. But policy B does not pay back in the first place.
- **Hydrogen tank**: do not build one at current costs.

## Limitations

- **Daily data cannot see price spreads within the day.** The group's half-hour screening shows that most of a battery's arbitrage value lies within the day, which this model cannot assess.
- **The forecaster is a simple ridge regression.** The group already has stronger forecasting models (demand mean squared error lower by about 38%), and they can be run by replacing the `Forecaster` class in `tier2b.py`. This would also fill a gap recorded in the repository: the forecasting improvements have not yet been turned into a comparison of operating profit.
- **The contract window is an assumed negotiating term**, with no evidence from a buyer.
- **The training period 2020–2022 includes the energy crisis**, so the capacity chosen on it is not necessarily optimal for 2023–2025. The tables also list the hindsight-optimal design for comparison.

## Result files

`results_2b/chronology_tier1_design.csv`, `tank_screen.csv`, `contract_window_value.csv`, `operating_policies.csv`, `forecast_skill.csv`, `sensitivity.csv`, `monthly_operating_cash.csv`, and six figures.
