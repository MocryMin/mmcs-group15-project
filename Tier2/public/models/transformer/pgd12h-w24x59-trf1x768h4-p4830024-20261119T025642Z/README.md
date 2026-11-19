# pgd12h-w24x59-trf1x768h4-p4830024-20261119T025642Z

Frozen single-layer width reference.

This bundle takes a standardized 24×59 feature window and emits 24×3 joint residuals in price, total generation and demand order.
Use the [reference loader](../../inference.py) with the [shared input contract](../../INPUTS.md).
The selected weights and the training/evaluation replay are stored alongside the configuration.

| Evaluation window | Full 12h MSE | First 4h MSE | First 30 min MSE |
|:--|--:|--:|--:|
| 2025 Jan–Aug | 0.083788 | 0.075194 | 0.072575 |
| 2025 Sep–Dec | 0.071515 | 0.056578 | 0.044488 |
| 2026 Jun–Aug | 0.072653 | 0.059303 | 0.055309 |

[Configuration](config.json) · [Full test and validation scores](test_and_validation.csv) · [Evaluation snapshots](training_replay.csv)
