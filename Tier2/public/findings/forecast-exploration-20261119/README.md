# Tier 2B forecast exploration and frozen shortlist

Ran Min · 19 November 2026 · Forecasting experiment and replay inventory.

**Primary Transformer for the next matched dispatch comparison: 1×864.** Freeze 1×1024, 1×864, 1×768 and 3×448 on their 12-hour validation-selected checkpoints, with the original full-output Ridge (alpha 10) as the linear baseline. The short-validation-selected 1×1024 checkpoint remains a separately labelled variant.

| Model | Parameters | Validation 12h | 2025 Sep–Dec 12h / first 4h / first 30 min | 2026 Jun–Aug 12h / first 4h / first 30 min |
|---|---:|---:|---|---|
| **1×864** | **6,097,320** | **0.08326** | **0.06469 / 0.05223 / 0.04373** | **0.07282 / 0.06012 / 0.05592** |
| 1×1024 | 8,537,160 | 0.08413 | 0.06501 / 0.04742 / 0.03346 | 0.07647 / 0.06172 / 0.05371 |
| 1×768 | 4,830,024 | 0.08379 | 0.07152 / 0.05658 / 0.04449 | 0.07265 / 0.05930 / 0.05531 |
| 3×448 | 4,891,784 | 0.08262 | 0.07137 / 0.05114 / 0.03819 | 0.07016 / 0.05809 / 0.05052 |
| Ridge (original) | 102,024 | 0.10203 | 0.08098 / 0.05389 / 0.03278 | 0.08071 / 0.05989 / 0.04480 |

Scores are mean squared errors (MSE) over the indicated lead times and the three train-scale-standardised targets. The featured model combines the lowest autumn full-path MSE of the frozen set and a near-leading summer full-path MSE with 29% fewer parameters than 1×1024. That prioritisation reflects Ran Min's current shortlist. The validated alternatives capture lead- and season-dependent trade-offs, including 3×448's summer full-path result and Ridge's two leading half-hour point estimates. Forecast scores precede the matched dispatch economics test. [Weight bundles and model cards](../../models/README.md)

## What the experiments changed

| Stage | Scope | Result and effect on the next step |
|---|---|---|
| Small-model GPU grid | Four joint-output families, RNN, LSTM, attention LSTM and Transformer, at 5k, 10k and 50k parameters. Two forecasts/day. 21 features per row. | All families at 50k improved on their own 5k validation result. Attention LSTM had the best 50k validation point in that first grid. |
| Intermediate capacity and seed sweeps | 60/80/100/200/500k, then 200/500/700k, 1M and 2M with three seeds. | Validation improved up to the best tested 2M Transformer around 0.1416. The expanded grid established seed variability and supported moving beyond one small architecture. |
| 5M to 1B | 5M, 10M and 50M in all four families, Transformer-only 1B, then 100M and 200M across four families. Three seeds and matched 216-update budget. | Transformer 50M had mean validation MSE 0.13509, 100M 0.13582, 200M 0.14330 and 1B 0.16044. The 1B fit also had worse training loss than 50M. This measures training under the tested budget, with architecture and optimisation effects both relevant. The full per-step traces are available in the original research archive. |
| From two forecasts/day to every half hour | Refitted a 49.95M Transformer on all eligible half-hour origins, yielding 52,585 training windows with the earlier information set. Each update emits a new 12-hour forecast and executes one action in dispatch. | The same structure performed better at rolling issuance after matching the training cadence. Half-hour economic replay retained historical same-slot and perfect-information controls. Earlier decision-value work also tested 12/24-hour paths, peaks, shortage events and terminal inventory value. |
| Eight layers and alternative heads | 8×768 and 8×1024 with the 21-feature input, split-head trials, layer-wise probes, short-checkpoint checks and fine-tuning experiments. | The eight-layer models improved some validation scores over the prior one-layer 50M model. The old protocol's 8×768 and 8×1024 scored 0.13963 and 0.13948 on 2025 full-path test. Width changes did not yield a stable improvement under that protocol. |
| Publication-aware 59-feature rebuild | Physical observations and forecast vintages joined at publication time. Market-index label stays distinct from day-ahead price inputs. 4×768 and 8×768 trained from scratch over five epochs under the new protocol. | 4×768 full-path MSE was 0.06569 on 2025 and 0.07691 on 2026, versus 0.07030 and 0.07780 for 8×768. A matched Ridge comparison isolating a 48h extra reporting lag gave a 2025 fall from 0.11924 to 0.08098 after allowing recent published physical observations. The old and new grids differed in available information and training budget. |
| Return to shallower encoders | 2×1024, 2×576 and 3×448, then one-layer choices with widths 128, 256, 512, 768, 864 and 1024. Same input, splits, learning schedule and seed 17. Also ran parameter-matched tanh RNN and LSTM at ~4.83M. | 1×256 was competitive against 1×512 for full paths, and 1×128 lost accuracy on both tests. 1×864 and 3×448 showed the most useful full-path trade-offs. At about 4.83M, 1×768 Transformer consistently beat the recurrent alternatives on aggregate MSE. 3×448 reduced first-slot errors in both periods against the similarly sized 1×768. |
| Explicit 4h and first-slot selection | Direct short Ridge fits with shared and per-output strength, plus fresh 12h Transformer training for 1×1024 and 3×448 with separate validation checkpoint selection. | Both Transformers selected step 860 for both short scopes. Their 4-hour point estimates beat the two specialist Ridge variants in both periods, with overlapping paired uncertainty. Ridge remained stronger by point estimate at the first half hour. Original alpha-10 Ridge remains the baseline. |

Scopes, seeds and information sets are carried through each stage. The experiments reused the two test periods across architecture comparisons. Short-horizon checkpoints, intermediate-size trials and legacy runs remain traceable research results. The frozen shortlist is the input for a subsequent matched operating comparison.

The common equipment input is pinned to Tier 1 commit `f8f5cc04ed71034a51e3c89db1aea40202cf815b`. It fixes one 100 MW / 400 MWh storage unit and the existing A and B replay portfolios.

[Prior work-history archive](../../../workspaces/mocry/codex/work-history/20261113-v1/README.md) · [Public benchmark table](benchmark.csv) · [Historical grid summaries](history) · [Short-horizon comparison](short-horizon-scores.csv) · [Short-horizon paired intervals](short-horizon-paired.csv) · [Tier 1 equipment and economics handoff](../../../../Tier1/public/findings/battery-entry-and-tier2b-handoff-20261119/README.md)
