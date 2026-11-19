# in-12h-exact v1

v1 is the frozen feature-engineering baseline for the Tier 2B half-hour forecast and dispatch comparison. Its input is the [same 76-column feature contract](../../INPUTS-exact-76.md) at each half-hour issue time. All members predict a 24-slot path in one call. The fit uses 2022–2024 and checkpoint selection uses January–August 2025.

| Target | Forecast route |
|:--|:--|
| Generation | 1 layer × 768 hidden dimensions for all 24 half-hours |
| Demand | Ridge for all 24 half-hours |
| Price | Ridge through 4 hours, then 1 layer × 864 hidden dimensions through 12 hours |

Transformer outputs average seeds 17, 29 and 43. The [configuration](config.json) links the exact member bundles. Each contains the trained Safetensors tensors, checkpoint metadata and validation history or Ridge tuning grid. Both Transformers use four-head self-attention, a sinusoidal slot position and a local-plus-global readout. 

| Metric | Sep–Dec 2025 | Jan–May 2026 | Jun–Aug 2026 |
|:--|--:|--:|--:|
| Joint standardized path MSE | 0.038607 | 0.040655 | 0.055712 |
| A gross battery increment, £m | 1.285 | 1.809 | 1.713 |
| B gross battery increment, £m | 1.377 | 2.356 | 2.041 |

Pooled standardized MSE is 0.043761 over 17,451 issue times. The dispatch replay uses 363.5 days in total, including the established window closing control. At the common £4.695m annualized battery cost, the combined historical net battery increments are £0.131m under A and £1.098m under B. See the [forecast profile](forecast_profile.csv), [MPC replay](mpc_returns.csv), [pooled returns](mpc_pooled_returns.csv) and [replay verification](inference_verification.json).

[Feature-engineering and v1 research history](../../../../workspaces/mocry/codex/work-history/20261119-in-12h-exact-v1/README.md) · [v2 release](../in-12h-exact-v2/README.md)
