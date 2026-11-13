# Ran Min Tier 2B forecasting and feature engineering history

Publication snapshot: 13 November 2026. This archive contains the complete saved sequence of forecasting experiments, including unsuccessful model changes, training trajectories, checkpoints, external-feature research, data-scope checks and the GUI application. These are prediction experiments and method proposals; the later forecasting studies have not been integrated into a completed MPC operating-profit evaluation.

## Current reading order

1. [Feature-engineering synthesis](studies/tier2b-feature-engineering-20261110/README_ZH.md), [feature task ledger](studies/tier2b-feature-engineering-20261110/research/FEATURE_LEDGER.md), and [selected neural checkpoints](studies/tier2b-feature-engineering-20261110/RECOMMENDED_NEURAL_MODELS.json).
2. [Unified traditional/neural comparison](studies/tier2b-unified-forecast-comparison-20261110/README_ZH.md). Compare identical targets, dates and loss scales; distinguish fixed-parameter from rolling-refitted methods.
3. [NESO-only calibration](studies/neso-only-regression-20261110/REPORT_ZH.md) and [NESO scope audit](studies/neso-scope-audit-20261110/). A third-party forecast is valuable, but it is not a same-definition observation or evidence that a neural network created the full improvement.
4. [Decision information and timing](notes/TIER2B_DECISION_INFORMATION.md) and [route review](notes/TIER2_ROUTE_REVIEW_20261112.md). Prediction accuracy matters only if the operating decision uses unavailable future information or couples periods. Zero storage and known current-day inputs can make daily operation separable.
5. [Maintained application source](application/energy-data-explorer/README.md) and [public GUI](https://mmcs-energy-data-explorer-ran.mocrymin.chatgpt.site). The deployed application remains daily; it has not been replaced with the Tier 1 half-hour v7 data.
6. [Tier 1 archive and latest half-hour model](../../../../../../Tier1/workspaces/mocry/codex/work-history/20261113-v1/README.md).

## Evaluation contract for the later experiments

The three independent targets are daily generation, demand and price. Each network predicts one target while inputs may include the history of all three series and known calendar information. Training target dates are 2022–2024 (1,096), validation January–August 2025 (243), and monitored test September 2025–August 2026 (365). 2021 supplies historical context only. Earlier pilot experiments used different dates and must be read as historical stages, not ranked directly against this contract.

The objective is next-day sample-mean MSE after scaling each target by training-label statistics. Original-unit MSE, MAE and RMSE are also retained. Batch size is 64, normally 18 updates per epoch. The later neural studies evaluate all three complete sets after every update. Checkpoint selection and early stopping use validation loss. The test period has been repeatedly inspected and is a monitored holdout, not an untouched final test.

RNN, LSTM and Transformer are compared with persistence, seasonal baselines, OLS, Ridge, LASSO, calendar-plus-residual autoregression and gradient boosting. Parameter grids target approximately 2k/5k/10k in the feature study; earlier experiments also tested roughly 5k versus 54k. Three-seed confirmation is retained separately from single-seed smoke tests. Merely increasing width, adding attention, or adjusting plateau regularisation did not deliver a consistent large improvement.

## Feature research and retained results

The feature study contains 495 neural fits (477 primary plus 18 stricter-normalisation confirmations), 495 saved checkpoints and 419,571 full train/validation/test evaluation rows. Features were tested in motivated groups: calendar/holidays, recent levels and volatility, supply-demand balance, fuel mix, price transforms, temperature forecasts, wind forecasts, cloud/daylight proxies and NESO system forecasts. Rejected and missing-data-heavy candidates remain in the task ledger.

| Target | Final neural candidate features | Validation MSE reduction | Monitored-test MSE reduction |
|:--|:--|--:|--:|
| Generation | NESO day-ahead demand forecast plus JMA wind forecast | 10.02% | 15.33% |
| Demand | NESO day-ahead demand forecast | 51.97% | 37.83% |
| Price | NESO day-ahead demand forecast plus JMA wind forecast | 19.62% | 30.45% |

These reductions are relative to the frozen neural baseline in that study. All three targets improved across the matched confirmation seeds. They are not increases in operating profit. Traditional histogram gradient boosting remains the stronger validation-selected price candidate: its feature-enhanced validation/test losses are approximately 0.070071/0.043680. The corresponding neural price candidate is not declared best merely because it is neural.

Weather uses archived fixed-lead forecasts, not realised future weather. NESO inputs target the next day and must have been issued before the forecast origin cutoff. Its cardinal-point mean is not a time-weighted daily mean, and National Demand is not proven identical to the course's VD demand definition. The separate calibration study retains simple OLS/Ridge and historical-error correction controls. NESO wind forecasts were excluded from the final feature pool because of 341 missing origin dates, including a 148-day gap.

Without third-party electricity forecasts, calendar/temperature improved demand and wind forecasts improved price. Generation's smaller balance-feature result did not independently establish a strong improvement. Remaining limitations include reused test years, forecast archive/release-vintage details and unresolved conversion of predictive skill into decision value.

## Experiment sequence

| Stage | What changed |
|:--|:--|
| Initial pilot | Joint supply/demand/price, multistep prediction and simple baselines. |
| Next-day joint and independent | Switch the training target to next-day MSE; compare shared and separate target models, train/validation behaviour and persistence. |
| New temporal split | Freeze train/validation/monitored-test periods and record complete losses after each update. |
| History-window smoke | 365, 182, 91, 56, 30, 14 and 7 days; retain each target/family's validation-selected window. |
| Attention and Transformer | Temporal attention, similar-sized Transformer, three-seed confirmation and 10-fold width experiments. |
| Larger joint models and plateau schedules | Joint RNN/LSTM size increase, learning-rate changes and regularisation, with replay plots and seed comparisons. |
| Traditional methods | OLS/Ridge/calendar autoregression, Fable research review, and common-scale comparisons including boosting and rolling refits. |
| Feature engineering | Approximately 2k/5k/10k independent models, external forecasts and calendar features, strict input-boundary confirmation, causal perturbation checks. |
| NESO and application follow-up | ND/TSD/VD scope audit, NESO-only calibration, forecast horizons and maintained interactive data explorer. |

## Files and reproduction

All saved checkpoints, training logs, predictions, figures, features, public source captures, evaluation scripts and audit outputs are included, subject to [CONTENT_MANIFEST.json](CONTENT_MANIFEST.json). It records source paths, hashes and runtime exclusions. [release_manifests](release_manifests/) maps the earlier ZIP versions to their exact file payloads, and [release_history](release_history/) retains old entries no longer present in the working folders. Historical "not uploaded" statements describe the original study date.

Run [verify_archive.py](verify_archive.py) to check the archive without training. [restore_workspace.py](restore_workspace.py) reconstructs the course-relative study layout in an empty output directory so sibling-study imports can be restored. Install dependencies from each experiment's own requirements. Historical absolute machine paths may need configuration; archived provenance is not silently edited. No GPU environment, installed dependency tree, credential or Git directory is included. The original source records include the exact forecast inputs used; reproducing results does not require querying a newer forecast in place of an old one.

## Complete study directory

| Study | Reading entry | Archived files |
|:--|:--|--:|
| data-explorer-20261110 | [Open folder](studies/data-explorer-20261110/) | 11 |
| fable-forecast-review-20261110 | [Open report](studies/fable-forecast-review-20261110/REVIEW_ZH.md) | 11 |
| forecast-loss-interpretation-20261109 | [Open report](studies/forecast-loss-interpretation-20261109/README.md) | 2 |
| neso-only-regression-20261110 | [Open report](studies/neso-only-regression-20261110/REPORT_ZH.md) | 48 |
| neso-scope-audit-20261110 | [Open folder](studies/neso-scope-audit-20261110/) | 2 |
| tier2b-analysis-20261108 | [Open folder](studies/tier2b-analysis-20261108/) | 4 |
| tier2b-feature-engineering-20261110 | [Open report](studies/tier2b-feature-engineering-20261110/README_ZH.md) | 2,555 |
| tier2b-forecast-pilot-20261109 | [Open report](studies/tier2b-forecast-pilot-20261109/REPORT_ZH.md) | 65 |
| tier2b-independent-newsplit-20261109 | [Open report](studies/tier2b-independent-newsplit-20261109/REPORT_ZH.md) | 71 |
| tier2b-joint-plateau-20261110 | [Open report](studies/tier2b-joint-plateau-20261110/REPORT_ZH.md) | 170 |
| tier2b-joint-rnn-lstm-10x-20261110 | [Open report](studies/tier2b-joint-rnn-lstm-10x-20261110/REPORT_ZH.md) | 95 |
| tier2b-lookback-grid-smoke-20261109 | [Open report](studies/tier2b-lookback-grid-smoke-20261109/REPORT_ZH.md) | 285 |
| tier2b-nextday-independent-20261109 | [Open report](studies/tier2b-nextday-independent-20261109/REPORT_ZH.md) | 102 |
| tier2b-nextday-rnn-lstm-20261109 | [Open report](studies/tier2b-nextday-rnn-lstm-20261109/REPORT_ZH.md) | 51 |
| tier2b-temporal-attention-grid-20261109 | [Open report](studies/tier2b-temporal-attention-grid-20261109/REPORT_ZH.md) | 420 |
| tier2b-traditional-regression-20261110 | [Open report](studies/tier2b-traditional-regression-20261110/REPORT_ZH.md) | 136 |
| tier2b-transformer-10x-20261110 | [Open report](studies/tier2b-transformer-10x-20261110/REPORT_ZH.md) | 80 |
| tier2b-transformer-grid-20261109 | [Open report](studies/tier2b-transformer-grid-20261109/REPORT_ZH.md) | 357 |
| tier2b-unified-forecast-comparison-20261110 | [Open report](studies/tier2b-unified-forecast-comparison-20261110/README_ZH.md) | 539 |
| energy-data-explorer maintained application | [Open report](application/energy-data-explorer/README.md) | 40 |

Recorded payload: 5,083 files; 358.07 MB before Git deduplication. See the manifest for auxiliary provenance and release-history entries.
