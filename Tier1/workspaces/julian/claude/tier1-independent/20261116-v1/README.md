# Independent Tier 1: farm boundary, brief parameters, four methods

中文版：[README_ZH.md](README_ZH.md)

16 November 2026 · MMCS Group 15 · Personal research draft and replication material, not a group decision

Starting from the brief, the course slides, `get_data.py`, `farm_generator.py` and the five supplied CSVs, this study defines the boundary, cleans the data and researches costs independently, solves the problem with four methods that check one another, and then compares the result with the repository's Tier 1 v6 (daily). Money is in 2023 pounds. The results were obtained with HiGHS through SciPy. The Xpress branch has not been run; see "Replication".

- [Problem definition, data preparation, parameter sources, the four methods, sensitivities](RESULTS.md) · [Comparison with the repository's Tier 1 v6 and decomposition of the difference](COMPARISON.md)
- [Summary of results](results/summary.json) · [Results by method](results/method_results.csv) · [Sensitivities](results/sensitivity.csv) · [Battery value](results/battery_value.csv) · [Optimum by year](results/by_year_optimum.csv)
- [Data cleaning](t1_data.py) · [Model and the four methods](t1_model.py) · [Full study and figures](t1_run.py) · [Comparison with the repository](t1_compare_repo.py)
- [Cleaned daily table](data/clean_daily.csv) · [Log of data adjustments](data/data_quality_log.txt) · [Snapshot and hashes of the inputs used for the comparison](repo_data/MANIFEST.json)

## Conclusions and trade-offs

| Question | Evidence from this study |
|---|---|
| How much of the wind farm's output cannot be sold | Mean output in 2020–25 is 3,705 GWh a year, of which 804 GWh (21.7%) has no buyer. By year: 19%, 13%, 26%, 12%, 13% and 47%. Annual revenue is £352.6m if all output is assumed sold, and £283.2m for what can actually be sold. |
| Should a battery be built | All four methods choose zero. The brief's two-hour battery costs £27,381 per MWh per year. When one is forced in, it is worth £2,890–3,175 per MWh per year with perfect foresight and £1,840–2,580 under rule-based operation. The capital cost would have to fall from about £245k/MWh to £26–28k/MWh to break even. |
| How large an electrolyser, using only unsold output | Two 20 MW modules, 40 MW in total. Net gain £0.71m a year, capital cost £80m, payback 9.75 years, 1,201 t of hydrogen a year. Negative in 2021, 2023 and 2024. Break-even for the first module: hydrogen at £8.72/kg, or a capital cost of £2.18m/MW, or a discount rate of 9.5%. |
| If saleable electricity may be diverted to hydrogen | 600 MW (620 MW from the representative-weeks method). Net gain £118.4m a year, capital cost £1.2bn, payback 5.2 years, 46,623 t of hydrogen a year. Break-even hydrogen price £5.52/kg. |
| When the hydrogen offtake is limited | With diversion allowed and a daily offtake limit of 10, 25, 50 and 100 t, the size is 20, 60, 120 and 240 MW and the net gain £9.7m, £25.8m, £46.8m and £78.2m a year. The first module nets £9.70m a year and pays back in 2.98 years, which corresponds to about 7.3 t/day. |
| What the conclusion is sensitive to | In the surplus-only case, any one of the following reduces the size to zero: hydrogen at £8/kg or less, a capital cost of £2.5m/MW, a 10% discount rate, a 5% fixed operating cost, or using 2023–25 only. The size is 240 MW at a capital cost of £1.5m/MW, and 520 MW on 2025 alone. |
| Where the gap to the repository's v6 comes from | With the repository's data and assumptions, the model reproduces 739.557 MW and £37.712m for policy B. Replacing one assumption at a time: counting only the wind farm's own surplus, 740 → 267 MW; my cost and an 8% discount rate, → 60 MW; hydrogen at £9.5, → 65 MW; my data cleaning, → 45 MW; whole 20 MW modules, → 40 MW. |

## Implementation and conventions

### Boundary and policies

The client's asset is the 1,125 MW wind farm, not the whole power system. This follows from how the brief describes the wind-farm data and from the analysis function supplied in `get_data.py`: on deficit days the farm covers the deficit, and on surplus days the farm's output counts as surplus. Saleable energy each day is min(farm output, max(demand − national generation, 0)), and nothing is sold when the price is negative.

- **Surplus only** (central case): only energy with no buyer may be used for hydrogen or for charging.
- **Diversion allowed**: when the electricity price is below the value of electricity as hydrogen (£158/MWh), saleable electricity may also be used for hydrogen.

This boundary is an interpretation and has not been confirmed with the course staff. The repository's v6 and report v5 use a system-pool convention (national generation plus the wind farm against national demand).

### Data

Only the five raw CSVs are used. Each adjustment has a flag column in `data/clean_daily.csv`.

| ID | Issue | Treatment |
|---|---|---|
| D1, P1 | The last day of every 7-day block (always a Tuesday) holds a single early-morning reading, about 0.84 times the mean of its two neighbours | Replaced by the mean of the two neighbouring days |
| P2 | The price series as a whole is about half the published level | Multiplied by 2 |
| P3 | 30 days of prices missing | Linear interpolation |
| G1 | 30 days of generation missing, 107 days with thermal, nuclear and hydro all at zero, 18 days with an incomplete record | The non-wind, non-solar part is estimated by regression on demand and wind and solar output (R² 0.89, mean absolute error 1,311 MW) |
| R1 | Nominal prices | Converted to 2023 pounds with the annual ONS CPI |

This is a statistical repair, and it is less accurate than the repository's [full repair](../../../../../public/data_quality/full_data_repair/20261104-v2/REPAIR_SUMMARY_ZH.md), which goes back to the Elexon and NESO sources. The two datasets are compared in [COMPARISON.md](COMPARISON.md): they agree on whether a day is in surplus on 97.4% of days, and the share of output with no buyer is 21.7% against 22.3%.

### Parameters

| Asset | Values | Source |
|---|---|---|
| Electrolyser | Whole 20 MW modules, 20% minimum load, 55.9 kWh/kg, capital cost £2.0m/MW, fixed operating cost 3% a year, life 25 years, stack replaced after 50,000 hours at 30% of capital cost | Brief; IEA Global Hydrogen Review 2024 and 2025; TNO; Andoni et al. |
| Battery | Two-hour, 90% round-trip efficiency, usable range 20–80%, capital cost £244.8k/MWh, fixed operating cost 1% a year, life 20 years | Brief; operating cost and life are assumptions |
| Hydrogen price | £9.5/kg | Brief (HAR1 £241/MWh × 39.4 kWh/kg) |
| Discount rate | 8% real | Chosen within the 6–15% range given by NESO |

### The four methods

| Method | Approach | Purpose |
|---|---|---|
| M1 Duration curve | Closed-form marginal value of the E-th MW; upper bound on battery cycles | Explains the mechanism and gives the break-even points |
| M2 Representative weeks | KMeans selects 52 representative weeks, rescaled to match energy totals; mixed-integer programme | Tests whether simplified time gives the same size |
| M3 Full chronology | Mixed-integer programme over 2,192 days with perfect foresight; about 17,500 variables, 2,193 of them integer | Benchmark |
| M4 Rule simulation | Operating rules that see only the current day, with exhaustive search | Tests how much can be captured without foresight |

The four methods choose the same size under both policies; M2 differs by one module when diversion is allowed.

## Relation to report v5

Added on 22 November 2026. This draft was finished before v5 and is compared with v6. v5 moved to half-hour resolution and added a four-hour battery, and this draft does not reproduce v5's results. Points where the two can be set side by side:

| Issue raised in the v5 reviews | What this draft already contains |
|---|---|
| The brief's £9.5/kg case is not reported | Every result uses £9.5/kg; the break-even hydrogen prices are in the table above |
| No conclusion on the supplied daily data with the brief's two-hour battery | This draft uses only the supplied daily data and the brief's battery parameters, and concludes zero battery |
| Capacity, capital cost, payback and break-even points are missing at the recommended scale | Available at two scales: 40 MW, and 20 MW with a 10 t/day offtake |
| Too few figures in Tier 1 | Eight figures in `results/` |

Conventions need converting before anything is merged into the report: this draft uses 2023 pounds, an 8% discount rate and £2.0m/MW; v5 uses 2020 pounds, 5% and £1.46m/MW. Daily resolution understates both the surplus and the value of a battery, and v5's half-hour results show that the difference is not small.

## Replication

Requires Python 3.10 or later with numpy, pandas, scipy, scikit-learn and matplotlib. Run from this folder.

```sh
python t1_run.py --check       # consistency check, about 10 seconds
python t1_run.py               # full study, about 6 minutes
python t1_compare_repo.py      # comparison with the repository's v6, about 10 seconds
python t1_data.py              # rebuilds data/clean_daily.csv from the five raw CSVs
```

`t1_data.py` reads the five raw CSVs at the repository root. A lightweight clone does not include them by default; first run:

```sh
git sparse-checkout add -- '/daily_demand.csv' '/daily_generation_by_fuel.csv' '/daily_generation_total.csv' '/daily_market_index_price.csv' '/wind_farm_generation.csv'
```

**About Xpress.** The brief asks for the main modelling to use Xpress. `t1_model.py` has a `--solver xpress` branch that builds the same model through the Xpress Python interface, but it has never been run. M3 is larger than the community licence allows and needs the University's full licence. Run `python t1_run.py --check --solver xpress` first, and quote the results only after the output matches the following:

```
surplus  modules  exact 3  M1 3  M3 3  M4 3   net gain exact 0.6038  M3 0.6038
divert   modules  exact 36  M1 36  M3 36  M4 36   net gain exact 174.7346  M3 174.7346
```

## What has been checked

- For a fixed design, the closed-form formula and the mixed-integer programme give the same result.
- When a battery is forced in, the gain from rule simulation never exceeds the gain with perfect foresight.
- Hand example: one day with 600 MWh of surplus and one 20 MW module produces 8.587 t of hydrogen.
- Recomputed directly from the cleaned daily table without going through the model code, the annual net gain is £0.709m for 40 MW and £118.4m for 600 MW.
- With the repository's v6 data and assumptions, the model reproduces the published 739.557 MW and £37.712m (B), and gives 3,632 MW and £1,638.5m for A (published: 3,631 MW and £1,638.7m).

## Index of sources

- Brief and raw data: [Project_Brief.pdf](../../../../../../Project_Brief.pdf) and the five CSVs at the repository root.
- Repaired data used for the comparison: [full_data_repair/20261104-v2](../../../../../public/data_quality/full_data_repair/20261104-v2/REPAIR_SUMMARY_ZH.md); file-by-file hashes are in [repo_data/MANIFEST.json](repo_data/MANIFEST.json).
- The origin of each cost figure and how it was derived are in section 3 of [RESULTS.md](RESULTS.md).
