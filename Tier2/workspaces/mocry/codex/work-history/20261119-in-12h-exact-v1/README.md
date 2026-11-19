# 19 November research history · feature engineering and in-12h-exact v1

This archive preserves Ran Min’s feature-engineering process and the selection and initial MPC replay of v1. The [public model card](../../../../../public/models/ensembles/in-12h-exact-v1/README.md) connects to the exact 76-column inference bundles and the matched three-window operating results.

1. Start with `REPORT_ZH.md`, `README.md` and `SOURCES.md` inside the archive. They explain source timing, feature-family screens, representations, and seed and time-window confirmation.
2. Review `run_scores.csv`, `feature_catalogue.csv`, `exact_lead_scores.csv` and the paired interval tables. The screened recipes, raw value and difference features, whitening and projection tests, and intermediate experiments remain in their original configuration files.
3. The per-run folders hold the configurations, validation trajectories and results. The `in-12h-exact-v1/` subfolder holds the original ensemble recipe, market replay and diagnostic results. The included source and prepared-input definitions identify dependencies on the course archive and the published national sources.

[Research records](research-records-v1.zip) · [file inventory and hashes](MANIFEST.json)

The ZIP contains study code, manifests, scores, validation traces, charts and provenance. Raw acquired feeds and intermediate binary tensors are kept in the originating workspace. The public release contains the final model weights and input scales.
