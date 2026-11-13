# Changelog

## 2.1.0 — 2026-11-10

- Replaced the SVG chart path with Apache ECharts Canvas, filtered to the visible date range, with throttled native zoom. Removed the extra Y-axis relayout after every wheel event.
- Defaulted to lines, retaining scatter and combined modes. Cached moving averages and numeric formatters, and coalesced hover updates.
- Assigned six distinct curve colors, synchronized their checkbox swatches, and hid irrelevant supply/gap/price readouts in the demand comparison.
- Preserved range slider, wheel zoom, pan, box selection, both views, moving averages, split shading, missing-data gaps and exports. Regression checks and before/after performance evidence are saved.

## 2.0.0 — 2026-11-10

- Added independently selectable ND/TSD outturn and official historical forecasts to the course-demand chart.
- Retrieved 2,086 historical national snapshots with zero failed requests; required publication before target UTC day and exactly 48 half-hours per daily forecast.
- Preserved missing forecasts as visible gaps and exposed their coverage and source definitions.
- Retained the original overview, zoom/pan, presets, quality flags and exports; added browser-local curve selection memory.
- Separated editable app, versioned data, provenance and static output; established public Sites hosting and portable rebuild instructions.
- Preserved the original offline GUI and refreshed its familiar entry point.
