# pgd12h-w24x59-trf3x448h4-p4891784-20261119T032632Z

Frozen three-layer alternative, strongest full-path summer result.

This bundle takes a standardized 24×59 feature window and emits 24×3 joint residuals in price, total generation and demand order.
Use the [reference loader](../../inference.py) with the [shared input contract](../../INPUTS.md).
The selected weights and the training/evaluation replay are stored alongside the configuration.

| Evaluation window | Full 12h MSE | First 4h MSE | First 30 min MSE |
|:--|--:|--:|--:|
| 2025 Jan–Aug | 0.082621 | 0.071874 | 0.063421 |
| 2025 Sep–Dec | 0.071371 | 0.051136 | 0.038185 |
| 2026 Jun–Aug | 0.070164 | 0.058093 | 0.050521 |

[Configuration](config.json) · [Full test and validation scores](test_and_validation.csv) · [Evaluation snapshots](training_replay.csv)
