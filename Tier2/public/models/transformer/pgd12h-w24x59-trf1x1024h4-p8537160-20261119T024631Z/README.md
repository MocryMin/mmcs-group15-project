# pgd12h-w24x59-trf1x1024h4-p8537160-20261119T024631Z

Frozen alternative with strong short-horizon point estimates.

This bundle takes a standardized 24×59 feature window and emits 24×3 joint residuals in price, total generation and demand order.
Use the [reference loader](../../inference.py) with the [shared input contract](../../INPUTS.md).
The selected weights and the training/evaluation replay are stored alongside the configuration.

| Evaluation window | Full 12h MSE | First 4h MSE | First 30 min MSE |
|:--|--:|--:|--:|
| 2025 Jan–Aug | 0.084127 | 0.071398 | 0.062026 |
| 2025 Sep–Dec | 0.065008 | 0.047423 | 0.033458 |
| 2026 Jun–Aug | 0.076468 | 0.061722 | 0.053714 |

[Configuration](config.json) · [Full test and validation scores](test_and_validation.csv) · [Evaluation snapshots](training_replay.csv)
