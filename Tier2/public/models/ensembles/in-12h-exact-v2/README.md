# in-12h-exact v2

**Current highest-accuracy frozen Tier 2B forecasting ensemble.** On the matched three-window benchmark, v2 reduces joint 12-hour standardized MSE by **6.07%** relative to v1, from 0.043761 to 0.041105. This rating uses the released three-seed predictor and the established full-path metric. The same recipe trained with six new seeds gives a 7.00% pooled reduction. The six-seed figures are a replication of the recipe.

v2 uses the same [24 × 76 input](../../INPUTS-exact-76.md) and forecasts price, total generation and demand for all 24 slots at once. Every selected target/lead output averages 50% [v1](../in-12h-exact-v1/README.md) and 50% of its specialized branch. Each neural branch itself averages seeds 17, 29 and 43.

| Used output | Transformer branch | Additive Ridge term |
|:--|:--|--:|
| Price, all 24 slots | 4 layers × 320 dimensions, optimized for price | 0.5 |
| Generation, all 24 slots | 2 layers × 256 dimensions, independently parameterized generation encoder | 1.0 |
| Demand, first 8 slots | 1 layer × 128 dimensions, zero-initialized correction head | 1.0 |
| Demand, last 16 slots | 2 layers × 128 dimensions, local readout plus a constant and three discrete-cosine terms | 1.0 |

Each demand branch was trained over all 24 slots; the lead-range split applies during inference. All branches use four attention heads. The [frozen routing configuration](config.json) links both versions and the six Transformer bundles and shared 76-input Ridge. The generation export contains the active encoder from the grouped training checkpoint. The released loader reconstructs both versions independently from the public weights.

| Metric | Sep–Dec 2025 | Jan–May 2026 | Jun–Aug 2026 |
|:--|--:|--:|--:|
| Joint standardized path MSE | 0.036443 | 0.038211 | 0.052055 |
| Joint MSE reduction from v1 | 5.61% | 6.01% | 6.56% |
| Joint MSE reduction, six new training seeds | 6.83% | 7.61% | 6.43% |
| A gross battery increment, £m | 1.340 | 1.932 | 1.739 |
| B gross battery increment, £m | 1.392 | 2.248 | 2.043 |

At a common annual battery cost of £4.695m, v2 earns £0.334m of net battery increment under A and £1.006m under B over 363.5 days. Relative to v1, the paired change is +£203k in A [£90k, £299k] and −£92k in B [−£229k, £27k]. The intervals use paired seven-day blocks. Summer gap-sign accuracy decreases from 88.0% to 87.3%, and the rare high-price tail shows higher price error. The tested directional-attention substitution has a lower pooled point estimate on both cohorts and changes the across-window ranking as the seed set changes. Its validation error is higher for the generation blend, and it is recorded as an exploratory alternative in the architecture archive.

[Forecast profile](forecast_profile.csv) · [six-seed replication](forecast_profile_six_new_seeds.csv) · [error by lead](component_forecast_error_profiles.png) · [MPC returns](mpc_returns.csv) · [paired comparisons](mpc_paired_differences.csv) · [replay verification](inference_verification.json) · [Architecture and MPC research history](../../../../workspaces/mocry/codex/work-history/20261119-in-12h-exact-v2/README.md)
