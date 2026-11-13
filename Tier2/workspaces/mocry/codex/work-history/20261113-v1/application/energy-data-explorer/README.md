# MMCS Energy Data Explorer

Public application: https://mmcs-energy-data-explorer-ran.mocrymin.chatgpt.site

An interactive daily view of the course energy data, NESO National Demand (ND), Transmission System Demand (TSD), and the corresponding official forecasts. Public access was explicitly requested by Ran Min. This is a maintained application with a stable URL; a running laptop is not required after deployment.

## Use

The default demand comparison overlays course VD, actual ND and TSD, and official ND and TSD forecasts. Each has an independent checkbox. Actuals use solid lines and forecasts use dashed lines. The optional sixth series is the original experiment's ND cardinal-point forecast mean. It is a different aggregation from the half-hourly daily mean and remains separately labelled.

Date inputs, presets, wheel zoom, pan, box zoom, the bottom range slider, hover values, optional moving averages, training split bands, quality flags, CSV and PNG export are retained. The overview selector restores the original generation/demand/gap/price panels. Curve choices are saved in the visitor's own browser; visitors do not edit shared data.

## Data and provenance

- Current displayed period: 2021-01-01 to 2026-09-17, 2,086 UTC days.
- Actual ND and TSD: official NESO historical half-hours, with complete 48-period UTC daily aggregation. The original settlement day is correctly converted from Europe/London, including clock changes.
- Forecast ND and TSD: NESO forecasts distributed by Elexon BMRS, national boundary N. For each target day, the historical snapshot at 23:59:59 UTC on the preceding day is requested. A curve value requires 48 distinct valid half-hours and publication strictly before the target day starts.
- Current full-day coverage: actual ND/TSD 2,086/2,086; forecast ND/TSD 1,863/1,899. Gaps are null, not zero, and are not interpolated. `data/forecast-gaps.json` lists incomplete dates and period counts.
- The older cardinal summary is aligned by valid date, one day after its input CSV origin. Its missing/imputed entries are left null in this chart.
- No training datasets, trained models, reported loss values or formal reports were changed by adding these curves. The new NDF/TSDF half-hourly histories are additional material, not the source used in the previous NESO-cardinal experiments.

Source metadata, retrieval time, coverage and hashes are embedded in `data/app-data.json` and exposed under `dist/data/metadata.json`. `DATA_AUDIT.json` verifies source-date alignment, publication cutoffs and full-period aggregation. The local raw historical snapshot is retained under `evidence/` but excluded from the source repository and public web deployment; derived public records remain reproducible from their documented API.

Official sources:

- [NESO historic demand](https://www.neso.energy/data-portal/historic-demand-data)
- [NDF/TSDF historical snapshot API](https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/demand/day-ahead/history)
- [Original ND cardinal forecasts](https://api.neso.energy/api/3/action/package_show?id=1-day-ahead-demand-forecast)

## Maintain

`src/index.html` is the editable shell and `src/app.js` is the interaction/rendering code, `data/app-data.json` is the versioned dataset, and `dist/` is the exact static publication. The Apache ECharts 6.0.0 Canvas runtime is stored locally in `dist/assets/echarts.min.js`; visitors need no third-party chart service, API key or account.

For display changes or a versioned data update, use Python 3 and Node.js:

```text
python rebuild.py
python check.py
python preview_server.py
```

`rebuild.py` uses Python's standard library and the tracked chart bundle. The development preview binds only to localhost. Check the default view, all six curve toggles, range selection, both view modes, CSV export and narrow-screen layout before publishing. Save the checks in `UI_QA.json`; data/code checks are in `CHECKS.json`.

For refreshing original source data, `collect_forecasts.js` is a Playwright MCP collector with bounded concurrency and retries. Adjust its date range for an incremental pull. It returns a compressed snapshot without credentials. On the course workstation, `build.py` imports the original frozen course inputs and NESO outturn evidence, independently recalculates all forecast aggregates, refreshes the derived app data, and updates the original single-file GUI. It expects the existing course folder layout and the vendored ECharts bundle. Other maintainers can use the portable build without that layout.

## Publish and versions

Keep the opaque project ID in `.openai/hosting.json` unchanged. Publish through the Sites source workflow: obtain a fresh source credential for the same project, use `site-workflow.mjs` to commit/push and package, save the exact returned commit/archive, then deploy that saved version. Credentials must be passed through hidden stdin and never written into this repository. The website's audience is public; preserve that setting unless Ran requests a change.

The source repository and Sites saved versions provide rollback. `CHANGELOG.md` records user-visible changes. This app is available continuously, but data collection is explicit: no automatic background scraping or scheduled updates were created.

## Local original GUI

The familiar `MMCS/assignments/FinalProject/data-explorer-20261110/MMCS-data-explorer.html` is refreshed as a self-contained offline copy. `MMCS-data-explorer-v1-original.html` preserves the first version. The maintained source of truth is this application directory.
