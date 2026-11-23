# Independent Tier 2B: the Tier 1 portfolio operated day by day

中文版：[RESULTS_ZH.md](RESULTS_ZH.md)

23 November 2026. This study follows on from my [independent Tier 1](../../../../../../Tier1/workspaces/julian/claude/tier1-independent/20261116-v1/RESULTS.md) and keeps its conventions: the client owns the 1,125 MW wind farm, parameters are those of the brief, data are the supplied daily series for 2020–2025, and money is in 2023 pounds. It is a personal research draft, not a group decision. Results were obtained with HiGHS; the Xpress branch has not been run.

## Conclusions

1. **The surplus-only plan from Tier 1 cannot be operated as Tier 1 assumed.** Tier 1 let the electrolyser switch on and off every day. With a five-day minimum run and no other electricity, the same 40 MW plant runs on 7% of days and loses £6.1m a year. No plant size is viable under that rule.
2. **Covering minimum load with other electricity restores it.** If the plant may take just enough saleable or bought electricity to hold minimum load, the same 40 MW earns £4.5m a year, and the best size rises to 340 MW at £17.3m a year. About half of the hydrogen then comes from electricity that had a buyer, and three of the six years are loss-making.
3. **With diversion allowed, the result hardly changes.** The best size is 660 MW with a net gain of £127.8m a year and a payback of 5.2 years. The five-day minimum run costs less than 1%.
4. **Still no battery.** With the state of charge carried from day to day, a battery is worth £2,100–4,300 per MWh per year, or at most £14,200 where it replaces bought electricity, against an annual cost of £27,400.
5. **Operation can be simple.** At £9.5/kg, never switching off earns 94–96% of what perfect foresight would. Almost the whole shortfall falls in 2022. Better forecasts did not earn more: the NESO day-ahead wind forecast cut the one-day error in farm output by 24%, yet the plans built on regression forecasts earned less than plans built on "tomorrow equals today".
6. **Operating skill starts to matter when hydrogen is worth less.** At £6/kg, never switching off earns only 76–77% of the full-foresight result, and re-planning every day recovers 7–10 points of that.

## 1. What Tier 2B adds

Tier 1 treated each day separately. Here the days are linked in three ways, as the brief asks.

| Link between days | How it is modelled | Basis |
|---|---|---|
| The electrolyser cannot follow the wind day by day | A started module stays on for at least five days and takes at least 20% of its capacity every day it is on | Course Q&A of 16 November: an electrolyser is not switched on and off daily; "at least 4 or 5 days"; minimum load 20% in the brief |
| A battery holds energy over time | The state of charge carries from each day to the next, within the 20–80% window | Brief |
| The future is unknown | Modules are committed one day ahead on forecasts that are refreshed every day; the day then brings whatever it brings | Course Q&A: start from the published forecasts and solve a model every day |

**What electricity may the electrolyser take?** Once a module has to stay on, this question decides everything, so three rules are compared.

| Rule | Electricity allowed | Corresponds to |
|---|---|---|
| Unsold only | Wind-farm energy that has no buyer | Tier 1 central case, taken literally |
| Top-up | Energy with no buyer, plus saleable or imported electricity only to hold minimum load on a committed day | A firm supply for the mandatory minimum, as suggested in the Q&A |
| Diversion | Energy with no buyer, plus the farm's saleable output whenever that pays; imports only to hold minimum load | Tier 1 diversion case |

Electricity that is not surplus costs the market price of the day. Hydrogen is valued at £9.5/kg throughout, so one MWh turned into hydrogen is worth £158, which is also the break-even electricity price.

**Objective.** Annualised net gain: hydrogen revenue minus the cost of non-surplus electricity, start costs, and the annual cost of the equipment. Return on capital is the investor's first concern, as the client said in the Q&A. The use made of renewable energy and the resilience of the result are reported beside it for every plan, and section 4 puts the three together.

## 2. Model, data and forecasts

**Chronological programme.** Each day has the number of running modules (integer), module starts, and the electricity taken from each of three sources: unsold energy, the farm's saleable output, and the grid. The battery adds charging, discharging and a state of charge. The constraints are: load between minimum and full load of the running modules; the minimum run; the top-up rule (other electricity only on days when the plant sits exactly at minimum load); the battery balance; and an optional hydrogen offtake limit. One 20 MW module takes 480 MWh a day at full load and 96 MWh at minimum load. The whole record of 2,192 days is solved as one mixed-integer programme, in seconds for a given plant size.

**Data.** `inputs/clean_daily.csv` is the cleaned daily table from my Tier 1 study. The two NESO files are copies of files already in the repository, built by mocry-codex from the NESO data portal; `inputs/MANIFEST.json` gives sources and hashes.

**Forecasts.** Three quantities are forecast up to seven days ahead: wind-farm output, the national gap between demand and generation, and the electricity price. Every forecast uses only what is known on the day it is made.

| Method | Description |
|---|---|
| Tomorrow equals today | Persistence |
| Regression | Ridge regression for each horizon on recent values, the same weekday a week earlier and calendar terms, re-estimated every month on all earlier data |
| Regression + NESO | As above; the one-day-ahead model also uses the NESO day-ahead demand and wind forecasts issued that day |
| Expected unsold energy | The same forecast, with the errors of the previous 365 days added before the unsold energy is computed (see section 3.6) |
| Perfect | The realised values, as an upper bound |

## 3. Results

### 3.1 The Tier 1 plans through time

| | Plan | Net gain £m/yr | Payback, years | Days running | Longest idle spell, days | Loss-making years (of 6) | Hydrogen t/yr | Share of hydrogen from unsold energy |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A | 40 MW, unsold only, free daily switching (the Tier 1 assumption) | 0.71 | 9.8 | 20% | 240 | 3 | 1,201 | 100% |
| B | 40 MW, unsold only, five-day minimum run | −6.09 | none | 7% | 853 | 5 | 431 | 100% |
| C | 40 MW, top-up, five-day minimum run | 4.47 | 6.7 | 89% | 39 | 2 | 2,073 | 58% |
| D | 340 MW, top-up, five-day minimum run (best size) | 17.26 | 8.4 | 89% | 39 | 3 | 15,251 | 51% |
| F | 600 MW, diversion, five-day minimum run (Tier 1 size) | 127.00 | 5.0 | 90% | 39 | 0 | 49,001 | 23% |
| G | 660 MW, diversion, five-day minimum run (best size) | 127.80 | 5.2 | 90% | 39 | 0 | 51,711 | 23% |

Net gain by year, £m:

| Plan | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| A | 3.5 | −3.9 | 8.8 | −5.1 | −5.3 | 6.2 |
| B | −5.1 | −6.6 | 0.9 | −9.9 | −9.9 | −5.9 |
| C | 9.6 | −1.1 | 9.2 | −1.1 | 0.3 | 10.0 |
| D | 46.8 | −25.2 | 28.6 | −15.2 | −1.9 | 70.5 |
| F | 273.1 | 19.9 | 34.4 | 72.0 | 173.3 | 189.3 |
| G | 283.7 | 15.8 | 26.7 | 68.8 | 178.0 | 193.8 |

**Why plan B fails.** Unsold energy sufficient for one module at minimum load occurs on 20% of days, but in short stretches: 167 of them in six years, 2.6 days long on average and 11 at most. Only 23 stretches (3.8 a year) last five days or more, and they cover 7% of days. The longest gap between them is 240 days, from 20 December 2022 to 16 August 2023.

**Paying back within the record.** With the investment paid on 1 January 2020, only the diversion plans recover it by the end of 2025: plan F on 30 March 2025 and plan G on 17 June 2025 (`fig1_cash_through_time.png`).

The Tier 1 diversion plan earned £118.4m with free switching and the farm's own output only. Plan F earns more (£127.0m) despite the minimum run, because it may also import to hold minimum load on calm days, and at £9.5/kg that import is profitable. This is an addition to the opportunity set, not an effect of chronology, and section 3.7 shows what an import charge does to it.

### 3.2 How long the minimum run is

Net gain in £m a year, plant size fixed (`fig2_minimum_run.png`):

| Minimum run, days | 1 | 2 | 3 | 5 | 7 | 14 | 28 | Never off |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Unsold only, 40 MW | 0.71 | −0.97 | −2.55 | −6.09 | −8.10 | −9.89 | −9.89 | n/a |
| Top-up, 40 MW | 4.53 | 4.51 | 4.50 | 4.47 | 4.42 | 4.39 | 4.33 | 3.83 |
| Top-up, 340 MW | 17.70 | 17.63 | 17.49 | 17.26 | 16.94 | 16.56 | 15.97 | 11.24 |
| Diversion, 660 MW | 128.70 | 128.59 | 128.33 | 127.80 | 127.22 | 126.52 | 125.20 | 115.64 |

Under the unsold-only rule a two-day minimum run is already enough to turn the plan into a loss. From 14 days the plant never starts and the figure is simply its annual cost. Under the other two rules the length of the minimum run is a second-order matter: going from one day to five costs between 1% and 2.5%, and even a 28-day run costs under 10%.

### 3.3 Does chronology change the investment

| Rule | Best size, free switching | Best size, five-day minimum run | Net gain £m/yr | Payback, years |
|---|---|---|---:|---:|
| Unsold only | 40 MW | No plant (one module would lose £3.0m a year) | 0 | none |
| Top-up | 340 MW | 340 MW | 17.26 | 8.4 |
| Diversion | 660 MW | 660 MW | 127.80 | 5.2 |

The minimum run does not move the best size under the top-up and diversion rules. What moves it is the rule itself (`fig3_sizing.png`). Under the top-up rule the plant earns the difference between £158 and the market price on every MWh of minimum load it holds through a gap. On a typical day that is a profit, so capacity that would not pay on unsold energy alone becomes worth building, up to 340 MW. The price of this is in section 4: half of the hydrogen is no longer made from surplus.

### 3.4 Battery

The battery is the brief's two-hour type at £245k/MWh, with the state of charge carried from day to day. In every case the model chooses none when it is free to choose.

| Rule and plant | Forced size | Value created, £ per MWh per year | Capital cost at which it would break even, £k/MWh |
|---|---:|---:|---:|
| Unsold only, 40 MW | 100 MWh | 2,646 | 24 |
| | 500 MWh | 14,221 | 127 |
| | 2,000 MWh | 6,075 | 54 |
| Top-up, 40 MW | 100–2,000 MWh | 2,146–2,514 | 19–22 |
| Diversion, 660 MW | 100–2,000 MWh | 4,187–4,315 | 37–39 |

The annual cost is £27,381 per MWh. The one case where chronology gives the battery a real job is the unsold-only rule: at about 500 MWh it can hold one module at minimum load through short gaps, and its value rises fivefold. It would still need to cost about half of the brief's figure, and the plant as a whole would still lose money. Daily data cannot show arbitrage within the day; that question belongs to the group's half-hour model.

### 3.5 Seasons and hard stretches

**Seasons** (`fig4_seasonal.png`). Unsold energy is lowest in February and March (about 0.9 GWh a day) and highest in September (3.8 GWh a day). The top-up plant makes 29–35 t of hydrogen a day from January to March against 44–55 t from April to September, and the share made from unsold energy moves between 22% and 72%. The diversion plant behaves the other way round: it makes most hydrogen in winter (168–190 t a day in January and February), when the farm produces most and diversion is largest, and then only 6–13% of it comes from unsold energy.

**Hard stretches**, with the behaviour of the 340 MW top-up plant (average over the whole record: 41.8 t of hydrogen and £277k of operating cash a day):

| Stretch | Dates | Days | Mean price £/MWh | Modules running | Hydrogen t/day | Operating cash £k/day |
|---|---|---:|---:|---:|---:|---:|
| Too little unsold energy for one module | 20 Dec 2022 – 16 Aug 2023 | 240 | 101 | 95% | 27.7 | 94 |
| Price above the hydrogen break-even | 27 Jun – 25 Sep 2022 | 91 | 300 | 60% | 64.4 | 542 |
| Highest prices | 9 Aug – 5 Sep 2022 | 28 | 402 | 43% | 50.2 | 438 |
| Calmest 28 days | 19 Aug – 15 Sep 2021 | 28 | 187 | 46% | 13.6 | 19 |
| Highest demand | 4 – 31 Jan 2025 | 28 | 115 | 93% | 52.1 | 337 |
| Unsold energy every day | 3 – 14 Aug 2022 | 12 | 308 | 73% | 89.2 | 787 |

Two patterns stand out. During the eight months without usable surplus the plant keeps running on bought electricity at minimum load and earns a third of its usual cash; under the unsold-only rule it would have stood idle throughout. During the 2022 price spike the plant shuts down between windy spells and restarts for them (`fig5_stress_window.png`); unsold energy was plentiful that summer, so those 91 days were in fact better than average. The worst stretch for this plant is a calm spell with high prices, as in August and September 2021.

### 3.6 Operating without knowing the future

**Forecast errors**, 2022–2025, mean absolute error (`fig6_forecasts.png`):

| Quantity | Days ahead | Tomorrow equals today | Regression | Regression + NESO |
|---|---:|---:|---:|---:|
| Wind-farm output, MW | 1 | 230 | 215 | 164 |
| | 7 | 334 | 260 | 260 |
| Demand minus generation, MW | 1 | 1,473 | 1,363 | 1,382 |
| | 7 | 2,005 | 1,715 | 1,715 |
| Price, £/MWh | 1 | 17.7 | 17.6 | 18.6 |
| | 7 | 30.9 | 29.6 | 29.6 |

The NESO wind forecast improves the one-day forecast of farm output by 24%. Neither NESO series helps with the supply gap or the price, and one day ahead the price is as well predicted by today's price as by the regression.

**Calibration.** The NESO demand forecast is on a different level from the course demand series, so it cannot be used as published. Mean absolute error one day ahead, in MW:

| Year | As published | After yearly re-calibration | Tomorrow equals today |
|---|---:|---:|---:|
| 2022 | 3,865 | 2,082 | 1,521 |
| 2023 | 2,738 | 914 | 1,397 |
| 2024 | 2,999 | 760 | 1,456 |
| 2025 | 3,491 | 1,020 | 1,460 |

With one year of history the calibrated forecast is worse than persistence; from the second year it is 30–50% better. This is the pattern the client described: the gap between expected and actual narrows as the calibration accumulates data.

**What each way of operating earns.** Operating cash in £m a year over 2022–2025, with the commitment for each day decided the evening before (`fig7_rolling_operation.png`):

| Way of operating | Top-up 340 MW, £9.5/kg | Share of full foresight | Diversion 660 MW, £9.5/kg | Share of full foresight |
|---|---:|---:|---:|---:|
| Never switch off | 98.5 | 94.2% | 267.4 | 95.5% |
| Run when yesterday's price was below break-even | 87.6 | 83.8% | 256.6 | 91.6% |
| Re-plan daily, tomorrow equals today | 98.5 | 94.2% | 269.4 | 96.2% |
| Re-plan daily, regression | 93.5 | 89.4% | 258.2 | 92.2% |
| Re-plan daily, regression + NESO | 92.6 | 88.5% | 260.0 | 92.8% |
| Re-plan daily, same forecast, expected unsold energy | 95.6 | 91.4% | 265.2 | 94.7% |
| Re-plan daily, perfect seven-day forecast | 104.6 | 100.0% | 280.0 | 100.0% |
| Full foresight | 104.6 | 100% | 280.0 | 100% |

Four findings:

- **A week of foresight is all there is to gain.** Re-planning daily with a perfect seven-day forecast reaches the full-foresight result.
- **Nearly the whole shortfall is in 2022.** In 2023, 2024 and 2025 every method but one is within 1% of full foresight for the top-up plant; the exception is the expected-unsold-energy variant, which gives up 6% in 2023. In 2022 full foresight earns £112.7m, never switching off £89.0m, and the simple price rule £45.3m.
- **More accurate forecasts earned less.** The regression plans did worse than the plan built on persistence. The main reason is a bias, not noise: unsold energy is what is left when farm output exceeds the supply gap, so it is positive mainly on the days when the point forecast is wrong. Putting point forecasts into that formula gave an expected 0.9–1.0 GWh a day against an actual 2.5 GWh, and the plan shut down too readily in 2022. Averaging the formula over past forecast errors raises the expectation to 2.0 GWh and recovers about half of the lost money. Persistence has no such bias, because it copies a realised day.
- **Skill matters more when the margin is thin.**

| Hydrogen value | Never switch off | Re-plan daily, tomorrow equals today | Re-plan daily, expected unsold energy |
|---|---:|---:|---:|
| £9.5/kg | 94.2% / 95.5% | 94.2% / 96.2% | 91.4% / 94.7% |
| £7.5/kg | 87.9% / 89.6% | 91.0% / 94.3% | 88.4% / 92.6% |
| £6.0/kg | 76.0% / 77.1% | 83.5% / 86.6% | 82.4% / 85.2% |

Shares of full foresight; first figure top-up 340 MW, second diversion 660 MW.

### 3.7 What would change the strategy

Each row changes one assumption and re-sizes the plant, with a five-day minimum run unless stated (`fig8_sensitivity.png`). The last column asks whether a single module would pay under the unsold-only rule, and gives its net gain in £m a year.

| Assumption | Top-up: best size | Net gain £m/yr | Diversion: best size | Net gain £m/yr | Unsold only: does one module pay |
|---|---:|---:|---:|---:|---|
| **Central case** | 340 MW | 17.3 | 660 MW | 127.8 | no (−3.0) |
| Hydrogen value £5/kg | none | 0 | none | 0 | no (−4.0) |
| Hydrogen value £6/kg | none | 0 | 100 MW | 2.3 | no (−3.8) |
| Hydrogen value £7/kg | none | 0 | 320 MW | 22.6 | no (−3.5) |
| Hydrogen value £8/kg | 100 MW | 2.1 | 480 MW | 57.9 | no (−3.3) |
| Hydrogen value £11/kg | 580 MW | 47.1 | 800 MW | 211.6 | no (−2.7) |
| Hydrogen value £12/kg | 760 MW | 75.0 | 840 MW | 272.8 | no (−2.4) |
| Electrolyser cost £1.5m/MW | 700 MW | 51.6 | 820 MW | 183.2 | no (−1.7) |
| Electrolyser cost £2.5m/MW | 100 MW | 2.5 | 500 MW | 83.7 | no (−4.3) |
| Discount rate 5% | 560 MW | 37.2 | 780 MW | 160.5 | no (−2.1) |
| Discount rate 10% | 220 MW | 8.1 | 580 MW | 107.2 | no (−3.7) |
| National demand −10% | 820 MW | 240.3 | 820 MW | 283.6 | yes (+10.5) |
| National demand +10% | none | 0 | 580 MW | 80.7 | no (−4.9) |
| Wind and solar output −20% | none | 0 | 460 MW | 68.7 | no (−4.8) |
| Wind and solar output +20% | 920 MW | 183.7 | 940 MW | 266.3 | yes (+3.3) |
| Electricity price −25% | 460 MW | 27.8 | 740 MW | 175.8 | no (−3.0) |
| Electricity price +25% | 260 MW | 10.5 | 580 MW | 90.8 | no (−3.0) |
| Charge on grid imports £20/MWh | 320 MW | 16.4 | 640 MW | 124.9 | no (−3.0) |
| Charge on grid imports £40/MWh | 300 MW | 15.7 | 620 MW | 122.3 | no (−3.0) |
| Start cost £10k per module start | 320 MW | 16.6 | 660 MW | 126.5 | no (−3.0) |
| Start cost £50k per module start | 300 MW | 15.4 | 640 MW | 123.9 | no (−3.2) |
| Minimum run 3 days | 340 MW | 17.5 | 660 MW | 128.3 | no (−1.2) |
| Minimum run 14 days | 320 MW | 16.6 | 660 MW | 126.5 | no (−4.9) |
| Hydrogen offtake limit 10 t/day | 20 MW | 2.4 | 20 MW | 9.7 | no (−3.0) |
| Hydrogen offtake limit 25 t/day | 60 MW | 5.9 | 60 MW | 25.8 | no (−3.0) |
| Hydrogen offtake limit 50 t/day | 120 MW | 10.0 | 120 MW | 47.0 | no (−3.0) |
| 2023–2025 only | 500 MW | 20.1 | 720 MW | 147.4 | no (−4.3) |
| 2020–2022 only | 280 MW | 17.9 | 620 MW | 109.2 | no (−1.7) |

**Assumptions that change the strategy**

- **Hydrogen value.** The top-up plant disappears at £7/kg and is down to 100 MW at £8/kg. The diversion plant disappears at £5/kg and is down to 100 MW at £6/kg. Both grow quickly above £9.5/kg.
- **The balance between national demand and renewable output.** Demand 10% higher, or wind and solar 20% lower, removes the top-up plant altogether; the opposite changes take it to 820–920 MW and are the only cases in which the unsold-only rule pays. The reason is scale: unsold energy is the small difference between two national totals, and 10% of national demand is about two and a half times the wind farm's capacity. This is the least certain input to the whole strategy.
- **Hydrogen offtake.** When the offtake is limited, it sets the size under both rules: 20 MW for 10 t a day, 60 MW for 25 t, 120 MW for 50 t.
- **Electrolyser cost and discount rate.** These move the size a great deal (top-up 100–700 MW, diversion 500–820 MW) but do not reverse the decision in the range tested.

**Assumptions that do not change it**

- **The length of the minimum run** (3 or 14 days), **start costs** up to £50k per module start, and **a charge on grid imports** up to £40/MWh each move the result by 11% or less for the top-up plant and by less than 5% for the diversion plant.
- **Electricity price** 25% higher or lower changes the size but not the decision.
- **The choice of years** matters less than in Tier 1: on 2023–2025 alone the top-up plant is larger (500 MW), because bridging is cheap in those years and 2025 has much more unsold energy.

## 4. Sustainability of the three plans

The brief asks for sustainability in three senses. The plans with a five-day minimum run compare as follows.

| | Top-up 40 MW | Top-up 340 MW | Diversion 660 MW |
|---|---:|---:|---:|
| **Use of capital** | | | |
| Investment, £m | 80 | 680 | 1,320 |
| Net gain, £m a year | 4.5 | 17.3 | 127.8 |
| Net gain as a share of investment | 5.6% | 2.5% | 9.7% |
| Payback, years | 6.7 | 8.4 | 5.2 |
| **Use of renewable energy** | | | |
| Unsold energy put to use | 8% | 54% | 83% |
| Hydrogen made from unsold energy | 58% | 51% | 23% |
| Saleable output diverted, GWh a year | 48 | 370 | 2,075 |
| Grid imports, GWh a year | 1 | 46 | 149 |
| **Resilience** | | | |
| Loss-making years (of 6) | 2 | 3 | 0 |
| Worst year, £m | −1.1 | −25.2 | 15.8 |
| Share of full foresight earned by never switching off | n/a | 94% | 96% |

No plan is best on all three. The diversion plant uses capital best and is the most resilient, but more than three quarters of its hydrogen is made from electricity that had a buyer. The 40 MW top-up plant keeps most of its hydrogen on unsold energy and risks little capital, but uses 8% of what is available. The 340 MW top-up plant is the weakest of the three on return and on resilience.

**Recommendation.**

1. Do not plan on an electrolyser that runs on unsold energy alone. It cannot hold a minimum run.
2. Whatever the size, secure a firm supply for minimum load before investing: the farm's own saleable output, or a contract.
3. If the client can sell hydrogen at scale at the supported price, the diversion case is the one that pays, and its size should follow the offtake (section 3.7).
4. If the purpose is to use energy that has no buyer, start with 40 MW under the top-up rule. Its return does not depend on diversion at scale.
5. Do not build a battery at the brief's cost.
6. Operate simply: keep the plant on, stop it only for sustained price spikes, and re-plan every day with a one-week view. Forecasting effort is worth paying for only if the hydrogen value falls towards the electricity price.

## 5. Checks

`python t2b_run.py --check` runs these in about 20 seconds; all pass.

- With free daily switching and the unsold-only rule, the programme reproduces the Tier 1 dispatch for 1, 2 and 4 modules (£0.478m, £0.709m, £0.474m).
- On 18 random nine-day windows across the three rules, with and without start costs and import charges, the programme gives the same optimum as an exhaustive search over every commitment path.
- Operating the optimal commitment with the closed-form daily rule reproduces the programme's cash exactly.
- Re-planning daily with a perfect 28-day forecast reproduces the full-foresight optimum.
- A longer minimum run never raises the optimum, and a looser rule never lowers it.
- The battery's state of charge stays within its usable window.

Solver status and gap are recorded for the battery runs in `results/battery.csv`. One of the thirteen stopped at the time limit with a gap of 0.1%; the rest solved to optimality.

## 6. Limitations

- **Daily resolution.** Surplus and shortage within a day cancel in a daily mean, and the battery's arbitrage within the day is invisible. Daily totals also overstate how continuous the surplus is: this study finds stretches of up to 11 days with enough unsold energy for one module, while the half-hour site study in this folder, on the group's data and boundary, finds at most 56 hours. Plan B is therefore, if anything, worse than shown, and the top-up plans would need more bought electricity within the day than a daily balance shows. The half-hour models address these points, and their results should take precedence where they differ.
- **The boundary is an interpretation.** As in my Tier 1, only the wind farm belongs to the client. This has not been confirmed with the course staff.
- **Imports at the wholesale price.** Network and policy charges on imported electricity are not in the central case. Section 3.7 tests charges of £20 and £40 per MWh.
- **One hydrogen price.** Hydrogen made from bought electricity is valued like hydrogen made from surplus. If the support price applied only to the latter, the top-up and diversion results would be lower.
- **Only one-day-ahead official forecasts.** The repository's daily NESO files hold the day-ahead forecast only; days two to seven use my own regression. The wind forecast is missing on 175 of 1,825 days and is then carried forward.
- **Start costs and the minimum run are assumptions.** The Q&A gave "4 or 5 days" and no cost figure. Both are varied in section 3.7.
- **Plans are evaluated with the forecast point values**, not with a stochastic programme. The expected-unsold-energy variant is a partial correction.
- **Not run with Xpress**; see [README.md](README.md).

## 7. Relation to the group's Tier 2B

The group's Tier 2B work is at half-hour resolution with neural forecasts and a fixed 100 MW / 400 MWh battery. This study is complementary: it is daily, uses the brief's parameters, and concentrates on the electrolyser. Three of its results bear on the report:

- The minimum-run rule from the Q&A changes the surplus-only conclusion, and this holds at daily resolution as it does in the group's half-hour sensitivity.
- Forecast accuracy did not translate into operating value here either. The group found the same with its half-hour forecasts.
- The seasonal pattern, the hard stretches and the sensitivity table are the kind of evidence the brief lists for Tier 2B and that report v5 does not yet contain.

**Two half-hour studies in this folder.** On 22–23 November two site-scale studies on the group's half-hour data and conventions (2020 pounds, £7.80/kg, a 10 t/day offtake cap, 5 MW units, no grid imports) were added under `codex/`: an [operating sensitivity](../../../../../../Tier1/workspaces/julian/codex/electrolyser-sensitivity/20261122-v1/README.md) and a [contract-window backtest](../../../codex/studies/tier2b-site-backtest/20261123-v1/README.md). They and this study were made independently and agree where they overlap:

- Under supply priority, surplus enough for one unit at 20% load never lasts longer than 56 hours in the half-hour data, so a four- or five-day minimum run cannot be met and the best choice is no electrolyser. This study reaches the same conclusion from daily data (plan B in section 3.1) and adds what restores the plan: electricity from elsewhere to hold minimum load.
- With diversion allowed, the minimum run costs little in both: about £0.03m of £13.2m a year there, under 1% here.
- Under supply priority the simple operating rule matches full foresight there; here, never switching off earns 94–96% of it.

They differ in what they can see. The half-hour studies capture the value of timing production within a day against a capped quota, which this study cannot. This study covers grid imports, plant sizes without an offtake cap, a battery carried across days, the official forecasts and the sensitivity of the strategy, which they do not.

## Sources

- Project brief, Tier 2B and appendix.
- Course Q&A sessions of 2 and 16 November 2026 (transcripts): minimum run and minimum load of the electrolyser, use of published forecasts with daily re-solving, calibration, objective.
- NESO, 1-day-ahead demand forecast: https://www.neso.energy/data-portal/1-day-ahead-demand-forecast
- NESO, day-ahead wind forecast: https://www.neso.energy/data-portal/day-ahead-wind-forecast
- Cost and technical parameters: as in the independent Tier 1 study, section 3 of its results document.
