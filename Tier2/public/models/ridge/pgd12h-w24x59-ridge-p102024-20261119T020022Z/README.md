# pgd12h-w24x59-ridge-p102024-20261119T020022Z

Frozen original full-output Ridge baseline (alpha 10).

This bundle takes a standardized 24×59 feature window and emits 24×3 joint residuals in price, total generation and demand order.
Use the [reference loader](../../inference.py) with the [shared input contract](../../INPUTS.md).
The selected weights and the training/evaluation replay are stored alongside the configuration.

| Evaluation window | Full 12h MSE | First 4h MSE | First 30 min MSE |
|:--|--:|--:|--:|
| 2025 Jan–Aug | 0.102028 | 0.083632 | 0.070966 |
| 2025 Sep–Dec | 0.080979 | 0.053886 | 0.032776 |
| 2026 Jun–Aug | 0.080706 | 0.059887 | 0.044805 |

[Configuration](config.json) · [Full test and validation scores](test_and_validation.csv) · [Evaluation snapshots](validation_replay.csv)
