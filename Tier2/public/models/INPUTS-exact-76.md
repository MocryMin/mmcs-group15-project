# in-12h-exact input and output contract

Both versions take an array called `x` with shape `(N, 24, 76)`. One row within each forecast aligns with one future delivery half-hour. Every feature value must be available at the forecast issue time. Use [the ordered training feature contract](engineered-76-features.json) to standardize raw values and set missing values to their training mean. The supplied loader accepts already-standardized inputs.

| Columns | Source and preparation |
|:--|:--|
| First 59 | The [publication-aware base contract](INPUTS.md), including the source-specific historical windows and eligible auction and external forecasts |
| Next 12 | Forecast-shape features built from the same visible price, demand and wind information. Differences include the reference level, the first forecast slot and the previous slot. Net demand and other cross-series terms use the original documented units |
| Next 3 | Elexon national INDGEN value, age of the latest eligible release, and availability flag |
| Last 2 | TSDF value and age of the latest eligible release |

Use the latest matching released value known by the issue time. Retain the base N2EX auction availability convention and the same-slot seasonal reference. For construction code and source provenance see the feature-engineering archive linked from the [v1 model card](ensembles/in-12h-exact-v1/README.md).

The output shape is `(N, 24, 3)` in price, total generation and demand order. Supply an optional `reference` array of that shape in the input NPZ to obtain physical predictions. The loader multiplies standardized residuals by the three fixed training scales and adds the reference. The physical units are GBP at 2020 prices per MWh and half-hour MWh for generation and demand. The project generation target includes the independent wind farm. The matched MPC applies its existing non-negativity rule before planning.

From `Tier2/public`, run

```bash
python models/ensemble_inference.py models/ensembles/in-12h-exact-v2 inputs.npz forecasts.npy
```

The loader accepts `--device cuda` and uses PyTorch, NumPy and Safetensors. The shipped checkpoints use deterministic, fixed route weights. Historical feature archives and realized target series must be prepared from the documented upstream sources.
