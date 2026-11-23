# Independent Tier 2B: the Tier 1 portfolio operated day by day

中文版：[README_ZH.md](README_ZH.md)

23 November 2026 · MMCS Group 15 · Personal research draft and replication material, not a group decision

A chronological study that follows on from the [independent Tier 1](../../../../../../Tier1/workspaces/julian/claude/tier1-independent/20261116-v1/README.md) and keeps its conventions: the client owns the wind farm, parameters are those of the brief, data are the supplied daily series for 2020–2025, and money is in 2023 pounds. Days are linked through a minimum run for the electrolyser, a battery state of charge, and an operation that is re-planned every day on updated forecasts. The results were obtained with HiGHS through SciPy. The Xpress branch has not been run; see "Replication".

The group's own Tier 2B work is at half-hour resolution with a fixed battery. This study is daily and concentrates on the electrolyser. It is supporting evidence, not an alternative plan. Two half-hour site-scale studies under this folder's `codex/` subfolder ([operating sensitivity](../../../../../../Tier1/workspaces/julian/codex/electrolyser-sensitivity/20261122-v1/README.md), [contract-window backtest](../../../codex/studies/tier2b-site-backtest/20261123-v1/README.md)) reach the same conclusion on the surplus-only plan; section 7 of the results compares them.

- [Results and analysis](RESULTS.md)
- Tables: [plans through time](results/through_time.csv) · [by year](results/through_time_by_year.csv) · [minimum run](results/min_run.csv) · [best size](results/sizing_optimum.csv) · [battery](results/battery.csv) · [seasons](results/seasonal.csv) · [hard stretches](results/stress_windows.csv) · [forecast errors](results/forecast_skill.csv) · [calibration](results/calibration.csv) · [rolling operation](results/rolling.csv) · [sensitivity](results/sensitivity.csv)
- Figures: [cash through time](results/fig1_cash_through_time.png) · [minimum run](results/fig2_minimum_run.png) · [sizing](results/fig3_sizing.png) · [seasons](results/fig4_seasonal.png) · [a hard stretch day by day](results/fig5_stress_window.png) · [forecasts](results/fig6_forecasts.png) · [rolling operation](results/fig7_rolling_operation.png) · [sensitivity](results/fig8_sensitivity.png)
- Code: [chronological model](t2b_model.py) · [forecasts](t2b_forecast.py) · [study stages](t2b_run.py) · [figures](t2b_figures.py) · [Tier 1 model, unchanged copy](t1_model.py) · [inputs and hashes](inputs/MANIFEST.json)

## Conclusions and trade-offs

| Question | Evidence from this study |
|---|---|
| Can the Tier 1 surplus-only plan be operated | Not with a realistic electrolyser. With a five-day minimum run and no other electricity, the 40 MW plant runs on 7% of days and loses £6.1m a year. Unsold energy sufficient for one module lasts five days or more only 3.8 times a year. |
| What makes it workable | A firm supply for minimum load. If saleable or bought electricity may be used only to hold minimum load, the same 40 MW earns £4.5m a year (payback 6.7 years). The best size is then 340 MW at £17.3m a year, with half of the hydrogen made from electricity that had a buyer and three loss-making years in six. |
| Does chronology change the diversion case | Hardly. Best size 660 MW, £127.8m a year, payback 5.2 years. The five-day minimum run costs under 1%. |
| How much does the length of the minimum run matter | Decisive under the unsold-only rule (two days already give a loss). Second-order otherwise: 1–2.5% for five days, under 10% for 28 days. |
| Should a battery be built | No. With the state of charge carried between days it is worth £2,100–4,300 per MWh per year, at most £14,200 where it replaces bought electricity, against a cost of £27,400. |
| How should the plant be operated | Simply. At £9.5/kg, never switching off earns 94–96% of the full-foresight result over 2022–2025, and nearly all of the shortfall is in 2022. A perfect seven-day forecast would close the gap completely. |
| Do better forecasts pay | Not here. The NESO day-ahead wind forecast cuts the one-day error in farm output by 24%, but plans built on regression forecasts earned less than plans built on persistence, because point forecasts understate unsold energy (0.9–1.0 against 2.5 GWh a day). |
| When does operating skill matter | When the hydrogen value approaches the electricity price. At £6/kg never switching off earns 76–77% of full foresight and daily re-planning 84–87%. |
| What would change the strategy | The hydrogen value (the top-up plant disappears at £7/kg, the diversion plant at £5/kg), the balance between national demand and renewable output (10% more demand removes the top-up plant; 10% less takes it to 820 MW), and the hydrogen offtake, which sets the size when it is limited (20 MW for 10 t a day). Electrolyser cost and discount rate change the size but not the decision. The length of the minimum run, start costs, import charges and the choice of years change little. |

## Implementation and conventions

- **Chronological programme** (`t2b_model.py`). Integer number of running modules per day, module starts, electricity from three sources (unsold energy, the farm's saleable output, the grid), optional battery with a daily state of charge, optional hydrogen offtake limit. Minimum run of five days and minimum load of 20% per running module in the central case.
- **Three rules** for the electricity the electrolyser may take: unsold energy only; unsold energy plus other electricity only to hold minimum load ("top-up"); diversion of the farm's saleable output whenever it pays, with imports only to hold minimum load.
- **Rolling operation.** The number of modules for each day is decided the evening before by solving the programme over the next seven days on the latest forecasts. The day is then operated on what actually happens. Scored on 2022–2025.
- **Forecasts** (`t2b_forecast.py`). Persistence; ridge regression re-estimated monthly; the same with the NESO day-ahead demand and wind forecasts for the first day; and a variant that averages unsold energy over past forecast errors. All use only information available on the day of the forecast.
- **Conventions.** Farm boundary, 2023 pounds, 8% real discount rate, electrolyser £2.0m/MW in 20 MW modules, two-hour battery at £245k/MWh, hydrogen at £9.5/kg: all as in the independent Tier 1. Non-surplus electricity costs the market price of the day.

## Replication

Requires Python 3.10 or later with numpy, pandas, scipy and matplotlib. Run from this folder.

```sh
python t2b_run.py --check                  # consistency checks, about 20 seconds
python t2b_run.py                          # every stage and the figures, about 45 minutes on two cores
python t2b_run.py --stage rolling figs     # selected stages; results are cached in results/
```

**About Xpress.** The brief asks for the main modelling to use Xpress. `--solver xpress` sends the same matrices to Xpress through the Tier 1 helper, but this branch has never been run. Run `python t2b_run.py --check --solver xpress` on a licensed machine first and quote results only if every check passes.

## What has been checked

- With free switching and the unsold-only rule the programme reproduces the Tier 1 dispatch (£0.709m at 40 MW).
- The programme matches an exhaustive search over all commitment paths on 18 random nine-day windows.
- A closed-form daily rule applied to the optimal commitment reproduces the programme's cash.
- Daily re-planning with a perfect 28-day forecast reproduces the full-foresight optimum.
- Longer minimum runs never raise the optimum and looser rules never lower it.

## Limitations

Daily resolution hides everything that happens within a day, including battery arbitrage, and overstates how continuous the surplus is; the half-hour models should take precedence where they differ. The farm boundary is an interpretation. Imports are priced at the wholesale price in the central case. Hydrogen from bought electricity is valued like hydrogen from surplus. Official forecasts are available one day ahead only. Details are in section 6 of [RESULTS.md](RESULTS.md).
