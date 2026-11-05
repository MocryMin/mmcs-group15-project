# Tier 1 — independent CU build (20261105-v1)

Complete, reproducible Tier 1 package for Group 15, built in the `mocry-cleveruser` workspace. It contains the model, the case grid, the report, the one-page decision, the pitch points, the figures and the verification record.

**Status:** independent working build for group discussion. It does not adopt or overwrite Baseline 1104, the v1.1 research release or any other member's work. Where it reproduces Baseline 1104 reference numbers, that is an arithmetic cross-check between two implementations, not an endorsement of every shared assumption.

## Recommendation in one line

20 MW of PEM electrolyser, no battery, conditional on a hydrogen offtake of at least ~2.2 t/day at £7.80/kg and on freedom to divert 0.07% of current electricity sales: +£8.57m/year, £29.2m capital, 2.6-year payback, 29% ROI, 13.9 GWh/year of otherwise unused electricity captured.

## Contents

| Path | What it is |
|---|---|
| `TIER1_REPORT.md` | Full technical report (model, data, results, validation, recommendation, appendices) |
| `SUBMISSION_SECTION_4PP.md` | Four-page cut for the 10-page group report |
| `ONE_PAGE_DECISION.md` | One-page investment decision for the client/pitch |
| `PITCH_TALKING_POINTS.md` | Two-minute business pitch outline, no formulas or code |
| `data/` | Repaired inputs copied from `20261104-v2`, ONS CPI snapshot, `daily_model_inputs.csv`, `SOURCE_MANIFEST.json` |
| `src/prepare_data.py` | Builds the daily model table (G, D, deflated price, renewable split, quality flags) |
| `src/model.py` | Daily energy-pool MILP (A/B, battery modules, electrolyser modules, offtake cap) |
| `src/run_cases.py` | Runs all cases, writes `results/results.json`, `results/cases.csv`, `results/plans/` |
| `src/verify.py` | 20 independent checks, writes `VERIFICATION.json` |
| `src/make_figures.py` | Builds the eight report figures |
| `src/stats.py`, `src/summary*.py` | Small diagnostics used while building (not required to reproduce) |
| `results/results.json` | All case results, trigger grid, battery sweep, supply frontier, attribution |
| `figures/` | Report figures (PNG, 150 dpi) |
| `VERIFICATION.json` | Check list, model size, reference-value comparisons |

## Reproduce

Environment used: Python 3.14, `xpress==9.9.1` (FICO Xpress Community, rows + columns ≤ 5,000), `numpy`, `matplotlib`. The Xpress licence is local to the machine; no licence file is distributed.

```text
set PYTHONPATH=<path to pydeps>
python src/prepare_data.py
python src/run_cases.py
python src/verify.py
python src/make_figures.py
```

`reproduce.py` runs the four steps in order. The model data are rebuilt from the copied repaired CSVs, so no other package is needed at run time. `run_cases.py` takes about two minutes (185 optimisation solves plus 72 bisection solves).

## Data and parameters

- Inputs: `20261104-v2` full repair (five tables, 2,452 days, 2020-01-01 to 2026-09-17). The course originals are used only for the price ablation.
- Price: repaired wholesale series, deflated to GBP2020 with ONS D7BT (2020 annual = 108.7).
- Technology and finance parameters: the reviewed v1.1 candidate (battery €288k/MWh × 0.8897, FOM £14,861.62/MW/year primary and £7,430.81 table, electrolyser £1,460,439.72/MW modern midpoint with £816k legacy and £1,270k/£1,651k modern bounds, FOM £25,861.65/MW/year, stack £489,609.26/MW at years 11 and 22, hydrogen £7.799/kg, 5% real, 15/30-year lives).
- Every parameter and its status (brief, research, analyst choice) is listed in Appendix A of the report.

## Results at a glance (2023 design year, £m/year incremental)

| Case | A | B |
|---|---|---|
| No investment | 0 | 0 |
| Battery only | 0 | 0 |
| H2 only (20 MW) | +8.57 | 0 |
| Both | +8.57 | 0 |
| Rule-based 20 MW | −1.07 | −1.07 |

Key thresholds: netback £4.62/kg at 10 t/day; offtake 2,230 kg/day at £7.80/kg; battery break-even £7.0k/MWh with the lower FOM and none at the primary FOM; 120 MW at a 50 t/day offtake.

## Verification

`VERIFICATION.json`: 20/20 checks pass. Reference values match Baseline 1104: A0 17,139.332; 20 MW 17,147.905 and +8.572; B fixed 20 MW −1.065; simple rule −1.065; 2024 +11.951; old price +15.188; netback threshold 4.623 vs 4.61. Model size 2,556 rows × 2,192 columns; all optimisation cases optimal.

## Known limitations

Daily averages (no intraday or ancillary value); annual battery balance is a relaxation (an upper bound on battery value); perfect foresight; hydrogen value is policy-supported, not contracted; CAPEX is a modern installed midpoint while FOM and stack replacement use older UK absolute proxies; no degradation, hydrogen storage, network constraints or ancillary markets; 125 days have imputed fuel composition (85 in 2023); 2026 is partial and used only as a replay year.

## Change log

- 2026-11-05: first complete build (model, 185 cases, figures, report, decision page, pitch, verification). Cross-checked against Baseline 1104 and the v1.1 parameters.
