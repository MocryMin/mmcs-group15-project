# pgd12h-w24x59-trf1x864h4-p6097320-20261119T031915Z

Featured Transformer for the frozen dispatch comparison.

This bundle takes a standardized 24×59 feature window and emits 24×3 joint residuals in price, total generation and demand order.
Use the [reference loader](../../inference.py) with the [shared input contract](../../INPUTS.md).
The selected weights and the training/evaluation replay are stored alongside the configuration.

| Evaluation window | Full 12h MSE | First 4h MSE | First 30 min MSE |
|:--|--:|--:|--:|
| 2025 Jan–Aug | 0.083262 | 0.072975 | 0.067026 |
| 2025 Sep–Dec | 0.064687 | 0.052233 | 0.043729 |
| 2026 Jun–Aug | 0.072817 | 0.060122 | 0.055918 |

[Configuration](config.json) · [Full test and validation scores](test_and_validation.csv) · [Evaluation snapshots](training_replay.csv)
