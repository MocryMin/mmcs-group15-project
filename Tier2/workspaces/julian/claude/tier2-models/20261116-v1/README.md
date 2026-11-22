# Runnable models for Tier 2A and Tier 2B (daily resolution)

中文版：[README_ZH.md](README_ZH.md)

16 November 2026 · MMCS Group 15 · Personal research draft and replication material, not a group decision

One runnable model was built for each Tier 2 route, on the data and conventions of Tier 1 v6, to compare the routes while the choice was still open. Money is in 2020 pounds. The results were obtained with HiGHS through SciPy. The Xpress branch has not been run; see "Replication".

The group later took the half-hour Tier 2B route (forecasting with rolling dispatch, and a fixed 100 MW / 400 MWh battery). This draft is a different approach, at daily resolution and without a battery. It can serve as supporting evidence and is not an alternative plan.

- [2A results](RESULTS_2A.md) · [2B results](RESULTS_2B.md)
- [2A tables and figures](results_2a/) · [2B tables and figures](results_2b/)
- [Data loading, cost parameters, linear-programme builder](common.py) · [2A model](tier2a.py) · [2B model](tier2b.py) · [Input snapshot and hashes](data/MANIFEST.json)

## Conclusions and trade-offs

### 2A: investment in new generation

| Question | Evidence from this study |
|---|---|
| Which generation technology | Offshore wind is zero at every budget: its levelised cost in this model, £72/MWh, is above the £62/MWh it can realise. Onshore wind enters first, and solar only after onshore wind saturates. |
| How to split a £500m budget | 352 MW of onshore wind plus a 23.3 MW electrolyser, no battery. Net gain £44.14m a year under A and £34.19m under B, of which £31.40m and £31.73m are above Tier 1. Payback 6.6 and 7.6 years. |
| Diminishing returns | Annual net return on each additional £1 invested: about 6.9% for the first £100m, about 5.3% between £1bn and £2bn, about 2.8% between £2bn and £4bn, and about 0.5% above £4bn. With no budget limit the model stops at 3.4 GW of onshore wind plus 1.8 GW of solar. |
| Does new generation change the electrolyser or the battery | No. At every budget the electrolyser is 23.3 MW and the battery is zero. The electrolyser's size is set by the hydrogen offtake. |
| What the conclusion is sensitive to | The electricity price most of all: at half the price no generation is built. Under Arup's high-cost scenario the choice switches to 710 MW of solar. Excluding 2021–22 leaves the choice unchanged and reduces the net gain from £44.1m to £24.8m a year. |

### 2B: daily operation under limited information

| Question | Evidence from this study |
|---|---|
| Without a battery, what makes the order of days matter | Two mechanisms were tried. A hydrogen buffer tank does not work: a steel tank would have to be about 95% cheaper before it is chosen. What does work is a settlement window in the offtake contract: the buyer settles on the total over W days, so production can move to the cheaper days in the window. |
| What the window is worth (perfect foresight, whole history) | With settlement windows of 1, 7, 28 and 365 days, the net gain under A is £12.74m, £12.91m, £13.21m and £15.27m a year. A weekly contract adds only 1.3%. |
| How much can be captured without foresight (A, 2023–25) | Daily contract £13.08m. With a weekly window: greedy £12.48m, price threshold £12.74m, rolling optimisation with a naive forecast £12.84m, rolling optimisation with ridge regression £12.95m, perfect foresight £13.24m. Every rule that could be used in practice is worse than the daily contract. |
| Why | Forecast skill is gone after two days. Mean absolute error for the price one day ahead is £11.2 for ridge regression against £13.5 for the naive forecast, and the two are level from three days ahead. |
| Under policy B | When only surplus is used, greedy is already optimal and no forecast is needed. The 2023–25 net gain rises from £0.93m to £1.19m (weekly) or £1.26m (monthly) a year. |

## Implementation and conventions

- 2,192 days in 2020–2025. Supply is total national generation plus the independent wind farm, and national demand is the limit on sales. Prices are converted to 2020 pounds, the real discount rate is 5%, the hydrogen netback is £7.80/kg and the hydrogen offtake limit is 10 t/day.
- The electrolyser is sized in continuous MW, so Tier 1 is reproduced as 23.29 MW with £12.74m and £2.46m. v6 uses whole units with a minimum load and gives 23.42 MW with £12.68m and £2.44m, a difference within 0.5%.
- The battery uses the unit cost of the Tesla Megapack 2XL, sized in continuous MWh, and is available under policy A only.
- Generation costs in 2A come from the central scenario of Arup's 2024 cost update for DESNZ. The daily output shapes come from the course data and are scaled to that source's load factors.
- In 2A, policy A is a linear programme. Under policy B, whether a day has surplus depends on the new capacity; it is solved by fixed-point iteration and then evaluated with a closed-form daily dispatch.
- In 2B, the electrolyser capacity is chosen on 2020–22 with perfect foresight and then frozen. 2023–25 is replayed day by day, and each rule sees only the past.

## Limitations

- Daily data cannot see price spreads within the day, so arbitrage by a battery within the day cannot be assessed.
- The forecaster in 2B is a simple ridge regression. The repository already has stronger forecasting models, and they can be run by replacing the `Forecaster` class in `tier2b.py`.
- The settlement window is an assumed negotiating term, with no evidence from a buyer.
- 2A is a price-taker model. New wind at GW scale would depress the electricity price, so the gains at large budgets are optimistic.

## Replication

Requires Python 3.10 or later with numpy, pandas, scipy, scikit-learn and matplotlib. Run from this folder.

```sh
python tier2a.py --check     # reproduces Tier 1: 23.29 MW electrolyser, net gain 12.74 / 2.46 under A / B
python tier2a.py             # about 10 seconds
python tier2b.py --check
python tier2b.py             # about 40 seconds
```

**About Xpress.** Both models are linear programmes. `common.LP` has a `--solver xpress` branch that builds the same model through the Xpress Python interface, but it has never been run. Run `python tier2a.py --solver xpress --check` first, and quote the results only after they match the numbers above.

## Index of sources

- The input data are byte-identical to the repository's [full repair](../../../../../../Tier1/public/data_quality/full_data_repair/20261104-v2/REPAIR_SUMMARY_ZH.md); hashes are in [data/MANIFEST.json](data/MANIFEST.json).
- Cost sources are in the "Sources" and "Inputs" sections of the two results documents.
