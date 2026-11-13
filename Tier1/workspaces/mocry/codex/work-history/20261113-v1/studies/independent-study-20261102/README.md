# Independent project pilot — 2 November 2026

Read [the short Chinese report](REPORT.md) first. This directory is an assistant-run exploratory Tier 1 + Tier 2B study, not the team's final submission. No original course input is modified. Trial costs and system-boundary choices are explicit in [assumptions.json](assumptions.json).

## Reproduce locally

The local `.venv` uses Xpress 9.9 and the existing Community licence at `C:/xpressmp/bin/xpauth.xpr`. The licence file is not included or modified. The scripts do not require the university network licence. Anaconda installation was not performed or verified by this experiment.

From this directory in PowerShell:

```powershell
.\.venv\Scripts\python.exe -X utf8 audit_data.py
.\.venv\Scripts\python.exe -X utf8 run_study.py
.\.venv\Scripts\python.exe -X utf8 verify_and_plot.py
```

The existing environment is ready. On another computer, create a Python environment, install [requirements.txt](requirements.txt), and provide your own valid compatible Xpress licence. `run_study.py` currently contains the local licence path; change that path for another installation. Do not copy the licence file into a submission. Input paths are resolved relative to this directory, in `../../../materials/sync-20261030/`.

## Files

| File | Purpose |
|---|---|
| `audit_data.py` | Input hashes, missing/duplicate dates, fuel/total reconciliation and price-unit check |
| `run_study.py` | Capacity and dispatch optimisation, sensitivity cases and current-day-information rules |
| `verify_and_plot.py` | Independent hydrogen breakpoint calculation, chronology/loss tests and figures |
| `aligned_data.csv` | Complete-date intersection; no missing date is filled with zero |
| `data_audit.json` | Input provenance and statistical audit |
| `assumptions.json` | Trial assumptions used in the run |
| `results.csv` / `results.json` | 23 main cases: 21 optimisations and two policy simulations |
| `verification.json` | Independent checks and maximum numerical residual |
| `outputs/` | Daily schedules for the 23 main cases plus three toy checks |
| `findings.png` / `battery_chronology.png` | Visually checked comparison and chronological state plot |

The CSV results are analysis intermediates. Large monetary values are GBP; powers are MW; daily energy flows and usable battery state are MWh. `hydrogen_kg_year` is kg per model year. Capacity is chosen from 2023–2024. Cases labelled `2025_fixed_design` hold that capacity fixed; `2025_reoptimized_hindsight` is an explicitly hindsight benchmark. Cases prefixed `diagnostic_` are tests, not investment recommendations.

## Mathematical choices in the implementation

Let $G_t,D_t,W_t$ be daily-average background generation, demand and wind MW, and $p_t$ the price in GBP/MWh. In the base interpretation, existing wind is additional to $G_t$ and the background has dispatch priority. Immediate wind sales are $q_t=\min\{W_t,(D_t-G_t)^+\}$ when $p_t>0$, and zero otherwise. Eligible energy is $S_t=24(W_t-q_t)$. Battery export is limited to positive-price residual headroom $24(D_t-G_t-q_t)^+$. Alternative cases change the inclusion of wind or the allocation of curtailment.

Battery power $B$ implies nameplate energy $2B$, with usable energy $1.2B$ above the 20% floor. Let $c_t,d_t,h_t$ denote charge, discharge and electrolyser input in MWh. Then $c_t+h_t\leq S_t$. The chronological model has

$$
s_t=s_{t-1}+\sqrt{0.9}\,c_t-\frac{d_t}{\sqrt{0.9}},\qquad 0\leq s_t\leq1.2B.
$$

Surplus and positive-price export-headroom days are disjoint under these boundary definitions. Consequently the state bounds imply the one-usable-swing-per-day limits, without separate redundant rows. Physical power limits are looser at a 24-hour step for a two-hour battery. This daily approximation does not represent intraday arbitrage or multiple cycles. Each calendar year begins at the physical 20% floor, i.e. usable state zero. Final usable energy is allowed but has no salvage value and is not carried into the next training year.

The pooled Tier 1 model instead uses an annual energy balance $\sum_t d_t\leq0.9\sum_t c_t$, with daily swing limits. It is an optimistic relaxation that can use energy before it arrives; the two-day test demonstrates this difference explicitly.

Electrolyser capacity $H$ has an on/off indicator. In the full-day approximation, input is zero when off and between $4.8H$ and $24H$ MWh when on. Hydrogen output is $h_t/0.0559$ kg. The `subdaily_electrolyser_duty_cycle` comparison removes the lower daily energy bound, representing part-day operation, while retaining the installed power limit. No hydrogen inventory, offtake cap, water cost, compression or transport cost is included in this pilot.

The objective is average annual incremental electricity/hydrogen revenue less annualised new investment and fixed operation/maintenance cost. Capital recovery uses 8% over 15 years; it is not a discounted simulation of fifteen distinct future years. Existing wind investment costs are outside this incremental comparison. Battery cost is the brief's EUR 288,000/MWh translated at a trial GBP 0.85/EUR, not a verified exchange rate. Electrolyser cost and maintenance assumptions require evidence before final recommendations.

The policy simulation sees the current day's aggregate supply, demand and price, but no later days. It sends surplus to hydrogen first, stores the remainder, and sells stored energy whenever positive-price headroom is available. Current-day inputs being known is an explicit information assumption, not a tested forecasting capability. Base battery capacity is zero, so that case alone does not demonstrate a meaningful temporal-policy benefit.

## Validation limits

All 21 main optimisations and three toy models returned optimal status within Xpress tolerances. Numeric feasibility and the objective were independently recomputed from the extracted solutions; the hydrogen-only investment was also enumerated without the solver. Solver status establishes the computed optimum for the implemented model, not the validity of the economic assumptions or a final client recommendation.
