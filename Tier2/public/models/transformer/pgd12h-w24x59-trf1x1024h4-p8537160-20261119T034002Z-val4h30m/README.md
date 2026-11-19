# pgd12h-w24x59-trf1x1024h4-p8537160-20261119T034002Z-val4h30m

Supplementary short-validation checkpoint, full 12h training objective.

This bundle takes a standardized 24×59 feature window and emits 24×3 joint residuals in price, total generation and demand order.
Use the [reference loader](../../inference.py) with the [shared input contract](../../INPUTS.md).
The selected weights and the training/evaluation replay are stored alongside the configuration.

| Evaluation window | Full 12h MSE | First 4h MSE | First 30 min MSE |
|:--|--:|--:|--:|
| 2025 Jan–Aug | 0.085614 | 0.071166 | 0.059220 |
| 2025 Sep–Dec | 0.070575 | 0.050659 | 0.037459 |
| 2026 Jun–Aug | 0.072763 | 0.057671 | 0.046053 |

[Configuration](config.json) · [Full test and validation scores](test_and_validation.csv) · [Evaluation snapshots](training_replay.csv)
