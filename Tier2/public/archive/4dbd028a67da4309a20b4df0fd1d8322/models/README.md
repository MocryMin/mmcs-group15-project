# Tier 2B model bundles

**Featured Transformer: 1×864.** These weights use the frozen 59-feature publication-aware input.
Each bundle contains Hugging Face Safetensors weights, configuration, a card, numerical replay snapshots and held-out scores.
The supplied PyTorch loader implements the project-specific encoder and the original Ridge.
Its dependencies are torch, numpy and safetensors. The [input contract](INPUTS.md) defines units and timing.

| Model | Status | Parameters | Bundle |
|:--|:--|--:|:--|
| **1×864** | Featured Transformer for the frozen dispatch comparison | 6,097,320 | [Model card](transformer/pgd12h-w24x59-trf1x864h4-p6097320-20261119T031915Z/README.md) |
| 1x1024 | Frozen alternative with strong short-horizon point estimates | 8,537,160 | [Model card](transformer/pgd12h-w24x59-trf1x1024h4-p8537160-20261119T024631Z/README.md) |
| 1x768 | Frozen single-layer width reference | 4,830,024 | [Model card](transformer/pgd12h-w24x59-trf1x768h4-p4830024-20261119T025642Z/README.md) |
| 3x448 | Frozen three-layer alternative, strongest full-path summer result | 4,891,784 | [Model card](transformer/pgd12h-w24x59-trf3x448h4-p4891784-20261119T032632Z/README.md) |
| ridge | Frozen original full-output Ridge baseline (alpha 10) | 102,024 | [Model card](ridge/pgd12h-w24x59-ridge-p102024-20261119T020022Z/README.md) |
| 1x1024-short | Supplementary short-validation checkpoint, full 12h training objective | 8,537,160 | [Model card](transformer/pgd12h-w24x59-trf1x1024h4-p8537160-20261119T034002Z-val4h30m/README.md) |

Bundle IDs encode joint price/generation/demand and the 12-hour output, the 24×59 input window, architecture, exact parameter count and UTC training time. For the short-selected alternative, the suffix indicates the checkpoint selection criterion.

Transformers retain the step 0–1080 full-split evaluation table at ten-step intervals. Ridge retains the validation regularisation grid from its closed-form fit. Every tensor was checked after serialization and loaded through the public inference implementation.

For physical predictions, prepare an NPZ with `x` and the seasonal `reference` arrays. Run `python inference.py BUNDLE INPUT.npz OUTPUT.npy` from this directory. The benchmark CSV includes the same errors and units used in the forecast exploration note.

[Model manifest and weight SHA-256 values](catalogue.json) · [Forecast exploration and benchmark](../findings/forecast-exploration-20261119/README.md)

The `example.npz` file contains synthetic standardized features and a synthetic reference path for an installation smoke test.
