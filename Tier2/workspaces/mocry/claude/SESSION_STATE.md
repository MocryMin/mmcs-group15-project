# mocry-claude Tier 2 session state

Updated 2026-11-25T02:00Z · agent `mocry-claude` · member `mocry` (Ran Min)

## Work
- `forecasting/20261110-v1/REPORT.md`: data features, rolling-origin backtest (validation 2023, test 2024–25, horizons 1/2/3/7/14), event skill, interval coverage, a battery decision-value experiment and a literature survey for the three Tier 2B forecasting tasks (price, demand, generation). Personal research draft, not a group decision.
- `review/20261125-tier2b-outline/REVIEW.md`: review of the two Tier 2B five-page outlines (Ran Min vs Codex), reply to request `03d22096cca149b59486cd264ef8894a`. Recommend Codex's outline as the skeleton with three changes: make the recommended plant the subject, cut forecasting to ~0.6 page judged by decision value, and use p.4 for seasonal/stress conditions plus a what-changes table. Finding from the 12.5% ledger: plant-only A per window is 14.35/6.05/7.90/14.74/13.95/15.41 (mean 12.07, sd 3.67). Adding one block gives mean 12.84, sd 2.29, worst 8.86; correlation −0.78, so one block hedges the plant against high-price years.

## Main findings
- Demand: calendar regression + residual carry-over is best (MAE 20.7 GWh at 1 day).
- Generation / surplus: ridge direct multi-step; statistical skill ends after 1–3 days.
- Price: asinh regression / boosting helps at 1–2 days only; beyond 3 days nothing beats a 28-day mean.
- A model fitted once on 2020–22 fails on the test period; re-estimate on a rolling basis.
- Lowest MAE did not give the highest realised battery value.

## Open
- Owner to decide which intertemporal coupling makes forecasts decision-relevant (day-ahead commitment, periodic hydrogen delivery contract, fixed non-zero battery, multi-year scenarios).
- Not yet sent to mocry-codex; relevant to Chapter III of the v4.1 report.
- Pending request from mocry-codex (`1bff0d2d1ba0416fa541b818d5c2012f`, Tier1): review of the v4.1 academic report. Not started.
