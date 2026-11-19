# 19 November research history · Transformer tuning and in-12h-exact v2

This archive preserves Ran Min’s architecture and operator search with the v1 features frozen. The [v2 public model card](../../../../../public/models/ensembles/in-12h-exact-v2/README.md) records the four target-specific corrections, inference weights and benchmark. v2 is the current highest-accuracy released predictor on the matched three-window full-path benchmark. Variants and paired financial results provide the scope of that conclusion.

1. Start with `REPORT_ZH.md` and `validation_runs.csv`. The study compares depth and width, separate target streams, attention and position variants, feed-forward operators, temporal mixing, Ridge residuals, and output readouts.
2. Open `component_lock.json` for the final routing and `component_replication.json` for the six-new-seed confirmation. The `runs/` records retain intermediate trial configurations, validation trajectories and numerical results, including directional attention and like-for-like parameter controls.
3. Open `tier2b-mpc-replay/REPORT_ZH.md` for the matched three-window A/B study at the fixed equipment and battery cost. The accompanying tables separate forecast error, gross and net earnings, and block-resampled uncertainty.

[Research records](research-records-v2.zip) · [file inventory and hashes](MANIFEST.json)

This archive includes 727 completed training records and 15 same-family comparison fits. It preserves the exact local experiment structure as a research record. The [public input contract](../../../../../public/models/INPUTS-exact-76.md) and release loader handle inference from already prepared features.
