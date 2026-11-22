# Independent Tier 1: problem definition, four methods, integrated results

中文版：[RESULTS_ZH.md](RESULTS_ZH.md)

16 November 2026. Built only from the brief, the course slides, `get_data.py`, `farm_generator.py` and the five supplied CSVs, plus public cost sources. It does not reuse the group repository's data, conventions or parameters. The comparison with the repository is in [COMPARISON.md](COMPARISON.md). Money is in 2023 pounds.

## Conclusions

1. **Do not build a battery.** All four methods give zero battery. A battery creates at most about £2,900–3,200 of value per MWh per year against an annual cost of £27,400, a gap of about nine times.
2. **Using only the output that cannot be sold, the electrolyser barely breaks even.** The optimum is two 20 MW modules (40 MW in total), with a net gain of £0.71m a year, a payback of 9.8 years and losses in three of the six years. This does not support an investment on its own.
3. **If saleable electricity may also be diverted to hydrogen, the electrolyser is very profitable.** The optimum is 600 MW, with a net gain of £118m a year and a payback of 5.2 years. But this needs 47,000 t of hydrogen to be sold each year, all at £9.5/kg.
4. **So the real constraint is the hydrogen offtake.** Each 7 t/day or so of secured offtake justifies one 20 MW module. The first module nets about £9.7m a year and pays back in 3 years.
5. **The original plan overstates revenue.** 21.7% of the wind farm's output has no buyer. Annual revenue is £353m if all output is assumed sold, and £283m for what can actually be sold, a difference of £69m.

## 1. Problem definition

**The client's asset is the wind farm, not the whole power system.** Two pieces of evidence support this:

- The brief describes the wind-farm data as the daily generation profile of the wind-farm facility in the baseline plan, and the remaining data as a "constructed energy system". `farm_generator.py` simulates 75 turbines of 15 MW, 1,125 MW in total.
- The analysis function supplied in `get_data.py` works this way: it first compares national generation with demand; on deficit days the wind farm covers the deficit, and on surplus days the farm's output counts as surplus. Revenue, however, is computed as the farm's whole output times the price.

This gives the following daily definitions:

| Quantity | Definition |
|---|---|
| Saleable energy | min(farm output, max(demand − national generation, 0)); nothing is sold when the price is negative |
| Unsold energy | farm output − saleable energy |
| Headroom for selling battery discharge | max(demand − national generation − farm output, 0) |

**Decisions**: the number of electrolyser modules (20 MW each, integer) and the battery capacity (MWh, two-hour type).

**Objective**: maximise annualised net gain, that is, the incremental revenue from hydrogen and electricity sales minus the equipment annuity and fixed operating cost.

**Two operating policies**:

- **Surplus only** (central case): only unsold energy may be used for hydrogen or for charging. This is the literal wording of Tier 1 in the brief.
- **Diversion allowed**: when the electricity price is below the value of electricity as hydrogen (£158/MWh), saleable electricity may also be used for hydrogen.

## 2. Data preparation

Everything starts from the raw CSVs. Each adjustment has a flag column in `data/clean_daily.csv` and can be switched off in a sensitivity run. The study window is the six complete years 2020–2025.

| ID | Issue | Evidence | Treatment |
|---|---|---|---|
| D1 | Demand: the last day of every 7-day block holds a single early-morning reading | `get_data.py` downloads in 7-day blocks; the seventh day of each block (always a Tuesday) is 0.84 times the mean of its two neighbours, while the other positions lie between 0.94 and 1.15 | Replaced by the mean of the two neighbouring days, 350 days in total |
| P1 | Price: the same block fault | The seventh day is 0.84 times the mean of its two neighbours | As above |
| P2 | Price: the whole series is about half the true level | The script averages over all records without filtering by data provider; the file's 2024 and 2025 means are 0.48 and 0.49 times the published day-ahead averages | Multiplied by 2 |
| P3 | Price: 30 days missing | — | Linear interpolation |
| G1 | Generation: 30 days missing from the file, 107 days with thermal, nuclear and hydro all at zero, 18 days with an incomplete record (125 of these days fall in 2020–2025) | Nuclear below 75% of its 11-day median, and the generation-to-demand ratio below 85% of its 31-day median | The non-wind, non-solar part is estimated by regression (explanatory variables: demand, wind and solar output, quarter; R² 0.89, mean error 1,311 MW) |
| R1 | Prices in different years are not on the same basis | — | Converted to 2023 pounds with the ONS Consumer Prices Index |

I first learned about the block fault behind D1 and P1 from the group repository's repair report. Here it is verified and treated independently, using the supplied scripts and data.

After cleaning: national generation exceeds demand on 15.1% of days. The farm generates 3,705 GWh a year, of which 804 GWh (21.7%) has no buyer. The share varies widely by year: 12–14% in 2021, 2023 and 2024, 19% in 2020, 26% in 2022 and 47% in 2025.

## 3. Parameters

| Parameter | Value | Basis |
|---|---|---|
| Hydrogen value | £9.5/kg | Brief; the HAR1 average strike price of £241/MWh is in prices of around 2023 (£175/MWh in 2012 prices) |
| Electricity use | 55.9 kWh/kg | Brief |
| Electrolyser module | 20 MW, operating range 4–20 MW | Brief (ITM POSEIDON) |
| Electrolyser capital cost | £2.0m/MW | IEA Global Hydrogen Review 2025: installed PEM cost of €2,365/kW in 2024 (as cited by ACER), converted at 0.85 |
| Electrolyser fixed operating cost | 3% of capital cost a year | IEA Global Hydrogen Review 2024, assumptions annex |
| Stack life and replacement | 50,000 operating hours; replacement cost set at 30% of capital cost | IEA (life); TNO's stack cost range is about 16–45% of capital cost, and Andoni et al. use 48% |
| Electrolyser life | 25 years | NESO levelised cost of green hydrogen data |
| Battery capital cost | £245k/MWh | The brief's €0.288m/MWh, converted at 0.85 |
| Battery efficiency and usable range | 90% round trip, 60% usable | Brief |
| Battery life and operating cost | 20 years, 1% a year | My assumption, generous to the battery |
| Discount rate | 8% real | NESO's modelling range is 6–15% |

These give:
- Net value of one MWh of electricity turned into hydrogen = 9.5 × 1000 / 55.9 − stack wear of £12 = **£158/MWh**.
- Annual electrolyser cost of **£247k/MW**, and annual battery cost of **£27.4k/MWh**.
- The electrolyser must run at full load for **1,566 hours a year (about 18% of the time)** to break even.

Stack replacement is charged as a variable cost per operating hour, not in fixed years. In the surplus-only case utilisation is only 19%, so the stack would not need replacing within 25 years, and this treatment is closer to reality.

## 4. The four methods

| Method | Approach | Treatment of time | Purpose |
|---|---|---|---|
| M1 Duration-curve analysis | Sort the unsold energy from largest to smallest, compute how many hours a year the E-th MW can run, and find where this meets the annual cost | No dates at all | Can be checked by hand; gives an upper bound on battery value |
| M2 Representative-weeks MILP | Cluster the 313 weeks into 52 representative weeks, keep the order of days within each week, and let the battery cycle only within a week | Simplified time (what the brief asks for in Tier 1) | The simplified model the course asks for |
| M3 Full chronological MILP | 2,192 consecutive days with perfect foresight | Full chronology | Theoretical upper bound |
| M4 Rule simulation with exhaustive search | Each day sees only the past and follows a simple rule; every module count and battery size is enumerated | Full chronology, no foresight | Realistic lower bound |

M2 and M3 are mixed-integer programmes (integer module counts, and binary variables for the minimum load). They are solved here with HiGHS through SciPy.

## 5. Results by method

| Policy | Method | Electrolyser | Battery | Net gain £m/yr |
|---|---|---:|---:|---:|
| Surplus only | M1 | 40 MW | 0 | 0.71 |
| | M2 (52 weeks) | 40 MW | 0 | 0.71 |
| | M3 | 40 MW | 0 | 0.71 |
| | M4 | 40 MW | 0 | 0.71 |
| Diversion allowed | M1 | 600 MW | 0 | 118.4 |
| | M2 (52 weeks) | 620 MW | 0 | 118.3 |
| | M3 | 600 MW | 0 | 118.4 |
| | M4 | 600 MW | 0 | 118.4 |

Each net gain is the design chosen by that method, evaluated exactly on the whole history. The figures M2 reports inside its own model are 0.63 and 113.6.

**Surplus only, 40 MW**: capital cost £80m, payback 9.8 years, 1,201 t of hydrogen a year, utilisation 19%, and only 8.4% of the unsold energy is used. The first MW can run 1,744 hours a year, only slightly above the break-even of 1,566 hours.

**Diversion allowed, 600 MW**: capital cost £1.2bn, payback 5.2 years, 46,600 t of hydrogen a year, utilisation 50%, 79% of the unsold energy is used, and a further 1,972 GWh a year of saleable electricity is diverted.

**Battery**:
- Upper bound from M1: in the surplus-only case a battery can complete at most about 28 cycles a year of storing surplus and releasing it on a deficit day, worth no more than £2,960 per MWh per year.
- M3 with a forced 25–400 MWh battery: the realised value is £2,890–3,170 per MWh per year with perfect foresight, and only £1,840–2,580 under rule-based operation.
- The battery capital cost would have to fall from £245k/MWh to about £26–28k/MWh (a fall of about 89%) to break even.

## 6. Integration

**Agreement between methods**: M1, M3 and M4 agree exactly. With zero battery each day is independent and the three methods are mathematically equivalent. This is a finding in itself: the Tier 1 answer does not depend on how time is treated.

**Reliability of the simplified model** (M2, four random starts for each number of weeks):

| Representative weeks | Size chosen, surplus only | Size chosen, diversion allowed |
|---:|---|---|
| 8 | 0 MW in every run | 580–640 MW |
| 12 | 0–240 MW | 560–580 MW |
| 26 | 40–80 MW | 560–620 MW |
| 52 | 20–40 MW | 600–620 MW |
| 104 | 20–40 MW | 560–600 MW |

When the decision itself sits at the break-even margin (surplus only), a simplified model with fewer than 26 representative weeks gives anything from 0 to 240 MW. Where the profit curve is steep (diversion allowed), 8 weeks are enough.

**Cross-evaluation by year**:

| Policy | Design | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---:|---:|---:|---:|---:|---:|
| Surplus only | 40 MW | 3.5 | −3.9 | 8.8 | −5.1 | −5.3 | 6.2 |
| Diversion allowed | 600 MW | 258.3 | 10.7 | 37.7 | 61.3 | 163.6 | 178.8 |

In £m. The size that is optimal for each year alone: 120, 0, 260, 0, 0 and 520 MW for surplus only; 800, 300, 360, 460, 700 and 720 MW with diversion allowed.

**Out-of-sample test**:
- Surplus only: sizing on 2020–2022 gives 100 MW, which loses £4.14m a year on 2023–2025. Sizing on 2023–2025 instead gives no investment.
- Diversion allowed: sizing on the first three years gives 560 MW, which earns £133.4m a year in the last three years, only £1.4m below the hindsight optimum.

**Integrated recommendation**:
- The surplus-only case is not robust, and I do not recommend investing on that basis alone.
- The diversion case is robust, and its size is set by the hydrogen offtake that can be secured (see section 7).
- Do not build a battery.

## 7. What would change the conclusion

**Surplus only** (central case: 40 MW, £0.71m):

| Change | Optimal size | Net gain £m/yr |
|---|---:|---:|
| Hydrogen value ≤ £8/kg | 0 | 0 |
| Hydrogen value £11 / £12 | 120 / 200 MW | 4.4 / 8.5 |
| Electrolyser capital cost £1.5m/MW | 240 MW | 9.1 |
| Electrolyser capital cost £2.5m/MW | 0 | 0 |
| Discount rate 5% / 10% | 160 MW / 0 | 5.1 / 0 |
| Fixed operating cost 2% / 5% | 80 MW / 0 | 2.1 / 0 |
| 2023–2025 only | 0 | 0 |
| 2025 only | 520 MW | 45.9 |
| Demand block fault left uncorrected | 240 MW | 14.9 |

Break-even points for the first module: a hydrogen value of £8.72/kg, or a capital cost of £2.18m/MW, or a discount rate of 9.5%. The central assumptions are close to all three.

Two points deserve particular attention:
- **2025 is a watershed.** In that year 47% of output has no buyer, two to four times the share in earlier years. If this is the new normal, the surplus-only case would justify 520 MW. If it is only a change in how the data are recorded (the offshore wind record doubles from 2025), it would justify nothing. This needs to be confirmed with the client or the tutor.
- **A data error turns directly into investment advice.** Without correcting the Tuesday demand readings, the model would recommend six times the electrolyser capacity and report 21 times the gain.

**Diversion allowed** (central case: 600 MW, £118.4m):

| Change | Optimal size | Net gain £m/yr |
|---|---:|---:|
| Hydrogen value £5/kg | 0 | 0 |
| Hydrogen value £7 / £8 / £11 | 300 / 440 / 720 MW | 22 / 55 / 193 |
| Electrolyser capital cost £1.5m / £2.5m per MW | 760 / 480 MW | 168 / 78 |
| Electricity price ×0.75 / ×1.25 | 660 / 540 MW | 160 / 86 |
| Price without the ×2 correction | 720 MW | 215 |
| Hydrogen offtake limit 10 t/day | 20 MW | 9.7 |
| Hydrogen offtake limit 25 / 50 / 100 t/day | 60 / 120 / 240 MW | 26 / 47 / 78 |

Break-even points for the first module: a hydrogen value of £5.52/kg, or a capital cost of £4.89m/MW. This case is not sensitive to cost. It is sensitive to the hydrogen price and to the offtake.

If the minimum load is taken as 20% of the whole plant instead of 4 MW per module, the diversion optimum falls to 540 MW and £110m a year, and the surplus-only case does not change. Dropping the days with estimated generation changes the surplus-only case to 60 MW and £1.34m, and leaves the diversion case unchanged.

The full 9×7 decision table (hydrogen value against electrolyser capital cost) is in `results/decision_map.csv` and `fig4_decision_map.png`.

## 8. Comparison with simple alternatives

| Option | Surplus only £m/yr | Diversion allowed £m/yr |
|---|---:|---:|
| Do nothing | 0 | 0 |
| One 20 MW reference module only | 0.48 | 9.70 |
| Optimised result | 0.71 (40 MW) | 118.4 (600 MW) |
| Sized to the wind farm's capacity (1,140 MW) | −155.1 | 52.2 |
| 100 MWh battery added to the optimal electrolyser | −1.74 | 116.0 |

Sizing the electrolyser to the amount of surplus is the most intuitive simple approach. In the surplus-only case it loses £155m a year.

## 9. Limitations

- **Daily data cannot see movements within the day.** Surpluses and deficits within a day cancel in the daily mean, so the unsold energy is understated and battery arbitrage within the day cannot be assessed. Only daily data were supplied, and I cannot correct for this.
- **The boundary is my interpretation.** Counting only the wind farm's own surplus is supported by the script, but the brief does not say so explicitly. If the whole system belonged to the client, the surplus-only optimum would be 220 MW (see the comparison document).
- **The electrolyser cost is a generic figure**, not a quotation for the ITM POSEIDON. The 0.85 exchange rate and the battery life and operating cost are assumptions.
- **National generation is estimated on 125 days of the study window**, and the estimation error (about 1,300 MW) is of the same size as the wind farm's capacity. Dropping those days does not change the conclusion (surplus only becomes 60 MW).
- **£9.5/kg is a policy support price**, not a market price. HAR1 awarded only 125 MW across the whole country.
- **The models have not been run with Xpress**; see [README.md](README.md).

## Sources

- GOV.UK, HAR1 successful projects (£241/MWh, £175/MWh in 2012 prices, 11 projects and 125 MW): https://gov.uk/government/publications/hydrogen-production-business-model-net-zero-hydrogen-fund-shortlisted-projects/hydrogen-production-business-model-net-zero-hydrogen-fund-har1-successful-projects
- ACER, citing electrolyser capital costs from successive IEA Global Hydrogen Reviews (PEM €2,365/kW in 2024, €1,647/kW in 2030): https://aegis.acer.europa.eu/chest/dataitems/967/view
- IEA, Global Hydrogen Review 2024, assumptions annex (annual operating cost 3%, stack life 50,000 hours): https://iea.blob.core.windows.net/assets/36017d2f-747b-4993-b06d-33209fe143fa/GHR24AssumptionsAnnex.pdf
- NESO, levelised cost of green hydrogen (life 25 years, discount rate 6–15%): https://www.neso.energy/data-portal/levelised-cost-green-hydrogen/levelised_cost_of_green_hydrogen_modelling_2025_to_2050
- Andoni et al., techno-economic comparison of wind-to-hydrogen pathways (stack replacement 48%, operating cost 5%, £1,500/kW): https://arxiv.org/html/2509.00136v1
- Krishnan et al. (TNO), electrolyser stack costs (PEM €384–1,071/kW): https://publications.tno.nl/publication/34641390/JxEDSQ/krishnan-2023-present.pdf
- Montel, average GB wholesale electricity price in 2024 of £72.58/MWh: https://info.montel.energy/2024-gb-electricity-market-summary
- Electricity Maps, GB day-ahead average prices of £74.0 and £81.2/MWh in 2024 and 2025: https://www.electricitymaps.com/grid-in-review-2025/great-britain
- Consumer Prices Index: ONS series D7BT, annual averages (2015 = 100).
