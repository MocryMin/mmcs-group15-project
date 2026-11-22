# Independent Tier 1 compared with the repository's Tier 1

中文版：[COMPARISON_ZH.md](COMPARISON_ZH.md)

16 November 2026. The comparison is with Ran Min's (mocry-codex) Tier 1 v6 daily model in the repository, and with the published results of the v7 half-hour model. The repository's repaired inputs are copied into `repo_data/`. Money is in 2023 pounds unless stated otherwise. The repository reports in 2020 pounds, and the conversion factor is 1.2006.

## Conclusions

1. **The qualitative conclusions agree.** Both sides build no battery and only an electrolyser. In both, allowing diversion is far better than using surplus only, and the surplus-only case has loss-making years.
2. **The sizes differ by an order of magnitude, and the cause is two assumptions, not the method.** Surplus only: 740 MW in the repository, 40 MW in mine. Most of the gap comes from whose surplus counts (740 → 267 MW), followed by the electrolyser cost and the discount rate (267 → 60 MW). Differences in data cleaning are a small part (65 → 45 MW).
3. **The methods have been shown to be equivalent.** Given the repository's data and assumptions, my model reproduces its published 739.557 MW and £37.712m.
4. **My cleaning, which uses only the supplied files, is close to the repository's reconstruction from source.** The share of output with no buyer is 21.7% against 22.3%, and the two datasets agree on whether a day is in surplus on 97.4% of days.
5. **The repository's half-hour results suggest my surplus-only case is conservative.** Daily means cancel surpluses and deficits within a day, and I cannot correct for this with the daily data supplied.

## A. Data: my cleaning against the repository's reconstruction

The repository rebuilt every series from the original Elexon and NESO records, so it can serve as a reference for the quality of my estimates. For 2020–2025:

| Item | My treatment | Gap to the repository's rebuilt value |
|---|---|---|
| Demand, every Tuesday (313 days) | Mean of the two neighbouring days | Mean absolute error 689 MW (about 2.4%), 0.8% too low. The raw values are 17.1% too low on these days |
| Demand, other days | Unchanged | Mean absolute error 17 MW |
| Price, days left unchanged | Multiplied by 2 | Median ratio 1.000; 91% of days are within 1% |
| Price, the 338 replaced days | Mean of the two neighbouring days, or interpolation | Mean absolute error £12.7/MWh |
| Price, six-year mean (nominal) | £98.1/MWh | £98.4/MWh in the repository |
| National generation, the 125 days I estimated | Regression | Mean absolute error 1,250 MW, 164 MW too high |
| National generation, other days | Unchanged | Mean absolute error 166 MW; 167 days differ by more than 100 MW, which the repository corrected separately and I did not detect |

Effect on the results:

| Indicator | My data | Repository's data |
|---|---:|---:|
| Days on which national generation exceeds demand | 15.1% | 15.9% |
| Days on which generation exceeds demand once the farm is added | 19.9% | 21.0% |
| Share of the farm's output with no buyer | 21.7% | 22.3% |

The judgement that the price had been halved is fully confirmed. The simple replacement of Tuesday demand has a systematic bias of under 1%, which is good enough. The regression estimate of generation has a sizeable error on individual days but is unbiased overall.

## B. Can my model reproduce the repository's results

Using the repository's data, system boundary, costs (ITM NEPTUNE V, 5% real discount rate, 30 years, stack replacement in years 11 and 22) and a hydrogen netback of £7.799/kg, with money in 2020 pounds:

| Case | Published by the repository | Reproduced by me |
|---|---|---|
| B supply first, no offtake limit | 739.557 MW, £37.712m | 739.557 MW, £37.712m |
| A economic dispatch, national offtake limit | 3,631.341 MW, £1,638.660m | 3,632.382 MW, £1,638.538m |
| B, 10 t/day | 23.424 MW, £2.440m | 25.155 MW, £2.180m |
| A, 10 t/day | 23.424 MW, £12.681m | 25.155 MW, £12.462m |

The first two rows match. The two 10 t/day rows differ because the repository can mix eight product models to fit the offtake limit, whereas here I round to whole units of a single 5.031 MW model.

## C. Decomposition: from the repository's answer to mine

Each step changes one assumption and keeps everything else as in the step before.

**Surplus only (the repository's policy B)**

| Step | Electrolyser MW | Net gain £m/yr |
|---|---:|---:|
| Repository result, restated in 2023 pounds | 740 | 45.3 |
| Count only the wind farm's own surplus | 267 | 13.9 |
| Use my electrolyser cost and an 8% discount rate | 60 | 1.2 |
| Hydrogen value of £9.5/kg (the repository's equals £9.36) | 65 | 1.4 |
| Use my data cleaning | 45 | 0.7 |
| Whole 20 MW modules with a 4 MW minimum per module | 40 | 0.7 |

Taken in a different order: keeping the repository's boundary and data and changing only to my cost and discount rate gives 231 MW and £4.2m. Each of the two assumptions on its own therefore removes about two thirds of the size.

**Diversion allowed (the repository's policy A)**

| Step | Electrolyser MW | Net gain £m/yr |
|---|---:|---:|
| Repository result, restated in 2023 pounds | 3,632 | 1,967 |
| Count only the wind farm's own electricity | 780 | 192 |
| Use my cost and discount rate | 589 | 113 |
| Hydrogen value of £9.5/kg | 599 | 119 |
| Use my data cleaning | 599 | 118 |
| Whole 20 MW modules | 600 | 118 |

Here the boundary explains almost the whole gap. The repository treats all 28 GW of national generation as electricity that can be diverted to hydrogen, and then caps it with national hydrogen consumption (1,559 t/day). Under my convention the wind farm's 1,125 MW is itself the upper limit.

**How the two key assumptions differ**

| | Repository | Mine |
|---|---|---|
| Whose electricity | National generation plus the wind farm, all belonging to the client | Only the wind farm belongs to the client |
| Surplus | Everything by which national generation plus the wind farm exceeds demand | The part of that which belongs to the wind farm, no more than the farm's output |
| Electrolyser capital cost | £1.46m/MW (2020 prices), about £1.75m in 2023 prices; manufacturer's product data | £2.0m/MW; IEA installed PEM cost |
| Fixed operating cost | About 1.8% a year | 3% a year |
| Stack replacement | Fixed replacement in years 11 and 22 | Charged as a variable cost per operating hour |
| Discount rate, life | 5% real, 30 years | 8% real, 25 years |
| Annual cost per MW (2023 prices) | About £181k | £247k, plus £12 per MWh |

## D. Putting each design into the other's world

| Design | In my model £m/yr | In the repository's model £m/yr |
|---|---:|---:|
| Surplus only: my 40 MW | 0.7 | 5.0 (the repository's optimum is 45.3) |
| Surplus only: the repository's 740 MW | **−71.2** | 45.3 |
| Diversion allowed: my 600 MW | 118.4 | 376 (the repository's optimum is 1,967) |
| Diversion allowed: the repository's 3,631 MW | 52.2 (capped at the wind farm's 1,140 MW) | 1,967 |

The risk is asymmetric. If the world is as I assume, building 740 MW under the repository's policy B loses £71m a year. If the world is as the repository assumes, building my 40 MW only earns less. This is the reason to lean towards the small scale until the boundary is confirmed.

## E. What the repository's v7 (half-hour) means for my results

When the repository moved from daily to half-hour resolution in v7, the electrolyser under B rose from 740 MW to 1,821 MW and the annual net gain from £37.7m to £118.4m (2020 prices), with the battery still at zero. The reason it gives is that netting within a day cancels surpluses and deficits on the same day; the positive supply–demand gap at system level rises from 2,276 GWh to 5,165 GWh a year.

This has two implications for my results:
- My surplus-only conclusion is probably conservative. Only daily data were supplied, so I cannot quantify by how much.
- The no-battery conclusion still holds in the repository's half-hour model. That is more convincing than my daily model, because a half-hour model can see arbitrage within the day.

## F. How I suggest the group uses this comparison

1. **Confirm the boundary first.** This is the largest disagreement and is worth asking the tutor directly: does the surplus cover the whole system, or only the client's wind farm? The algorithm in the supplied `get_data.py` supports the latter.
2. **Review the electrolyser cost and the discount rate.** Even with the repository's boundary, changing to the IEA installed cost and an 8% discount rate reduces B from 740 MW to 231 MW. The report should at least list this set of assumptions as a sensitivity case.
3. **The repository's model is more mature, and I do not suggest replacing it.** It has an integer product catalogue, half-hour chronology and optimality certificates. My version is suitable as an independent check and as a conservative case in the report.
4. **Three statements the report can use directly**: two independent models both build no battery; the electrolyser size is highly sensitive to the boundary and cost assumptions, ranging from 40 MW to 740 MW; and the Tuesday demand error in the data, if left uncorrected, would inflate the recommendation several times over.

## Result files

`results/repo_comparison.json`, `repo_reproduction.csv`, `repo_bridge.csv`, `repo_design_swap.csv` and `fig8_bridge_to_repository.png`. Run `python t1_compare_repo.py` to recompute them.
