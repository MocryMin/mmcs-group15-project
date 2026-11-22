# First exploratory analysis of the raw data

中文版：[README_ZH.md](README_ZH.md)

13 November 2026 · MMCS Group 15 · Personal exploratory draft; some conclusions have been superseded by later work

A first pass of cleaning and descriptive statistics on the five raw CSVs. It produces one daily table, a summary of key numbers and seven figures. It was done before reading the repository, to get a feel for the data. **Read "Known issues" below before using any figure or number.**

- [Summary of key numbers](results/summary.txt) · [Cleaned daily table](results/clean_daily.csv) · [Analysis script](data_analysis.py)
- Figures: [overview](results/fig1_overview.png) · [generation mix](results/fig2_generation_mix.png) · [seasonality](results/fig3_seasonality.png) · [wind farm capacity factor distribution and duration curve](results/fig4_wind_farm_profile.png) · [price against wind](results/fig5_price_vs_wind.png) · [windy and calm spells](results/fig6_wind_spells.png) · [surplus against the size of a hypothetical client demand](results/fig7_surplus_vs_scaling.png)

## Findings that still hold

| Question | Evidence from this pass |
|---|---|
| How large is the wind farm | 75 turbines of 15 MW, 1,125 MW in total. Mean output 424 MW, capacity factor 37.7%, about 3,718 GWh a year, about 1.5% of national demand. Zero output on 10 days and rated output on 29 days. |
| What is missing from the files | 30 days of generation, 30 days of prices and 1 day of demand. The sum of the fuel components equals total generation on every common date. |
| Obvious anomalies | Demand of 636 MW on 2 August 2022. A set of days on which thermal, nuclear and hydro are all zero at the same time. |
| Structure in time | Autocorrelation of the wind farm's output: 0.59 at one day, 0.33 at two days, 0.20 at seven days. Weekend demand is 8.1% below weekday demand. The daily correlation between demand and solar is −0.59. |

## Known issues

This pass did not detect the first three points below, so numbers and figures that involve the level of prices or demand cannot be quoted directly. The fourth point is a change of convention.

| Issue | Effect | Where to look instead |
|---|---|---|
| The price file is about half the true level | The mean price and the wind farm's sales revenue in the summary, and the price axes of figures 1 and 5, are too low by about half | [Data cleaning in the independent Tier 1](../../tier1-independent/20261116-v1/README.md), or the repository's [full repair](../../../../../public/data_quality/full_data_repair/20261104-v2/REPAIR_SUMMARY_ZH.md) |
| On the last day of every 7-day block (always a Tuesday), demand and price hold a single early-morning reading | The daily demand and price series have one low point every week | As above |
| Days with incomplete generation were identified with a broader rule (127 days) | The later count is 107 days with all zeros plus 18 days partly missing | As above |
| Figure 7 assumes the client has its own demand, a scaled-down copy of national demand | This was an early idea, later replaced by the convention in `get_data.py` (the wind farm against the national supply–demand gap) | [Problem definition in the independent Tier 1](../../tier1-independent/20261116-v1/RESULTS.md) |

## Replication

Requires numpy, pandas and matplotlib. By default the script reads the five raw CSVs at the repository root and writes to `results/`. A lightweight clone does not include the raw CSVs by default; first run:

```sh
git sparse-checkout add -- '/daily_demand.csv' '/daily_generation_by_fuel.csv' '/daily_generation_total.csv' '/daily_market_index_price.csv' '/wind_farm_generation.csv'
python data_analysis.py
```
