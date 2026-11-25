# mocry-claude Tier 2 session state

Updated 2026-11-25T11:50Z · agent `mocry-claude` · member `mocry` (Ran Min)

## Work
- `forecasting/20261110-v1/REPORT.md`: data features, rolling-origin backtest (validation 2023, test 2024–25, horizons 1/2/3/7/14), event skill, interval coverage, a battery decision-value experiment and a literature survey for the three Tier 2B forecasting tasks (price, demand, generation). Personal research draft, not a group decision.
- `review/20261125-tier2b-outline/REVIEW.md`: review of the two Tier 2B five-page outlines (Ran Min vs Codex), reply to request `03d22096cca149b59486cd264ef8894a`. Recommend Codex's outline as the skeleton with three changes: make the recommended plant the subject, cut forecasting to ~0.6 page judged by decision value, and use p.4 for seasonal/stress conditions plus a what-changes table. Finding from the 12.5% ledger: plant-only A per window is 14.35/6.05/7.90/14.74/13.95/15.41 (mean 12.07, sd 3.67). Adding one block gives mean 12.84, sd 2.29, worst 8.86; correlation −0.78, so one block hedges the plant against high-price years.
- `review/20261125-tier2b-preview/REVIEW.md`: acceptance review of the Tier 2B 5-page preview (`067a317`), reply to request `537a9b2fa5d5444394821c1db6028853`. Structure accepted; content conditional. F1 (must fix): the 'A: plant oracle' £51.40m is mostly the value of avoiding system-wide negative-price sales. The oracle−forecast gap matches Σmax(−p,0)·min(G,D) per window (12.3/19.6/51.8/67.6/38.4 vs 13.1/22.0/47.0/65.9/35.7 £m), so the comparator needs a perfect-information direct-sales reference; it should then be close to Tier 1's £13.46m. P1: link 11.95 to Tier 1's 13.46; B break-even and Table III.2 use the classifier while the recommendation uses the prior-slot rule (1.46, −0.55 excl. 2021/22, ~£127/£94 per kWh); £97/kWh vs the brief's ~£256/kWh; fill p.7 whitespace with §2.2 findings; Tier 1 v7.1 §5.5, Chapter III and App. C still cite the 12.5% replay.

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
