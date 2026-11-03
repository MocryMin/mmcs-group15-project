# First-pass declaration - R2 (batteries)

## Identity

- Result ID: `R2-battery-firstpass-20261103`
- Package: R2 (batteries); gap IDs B-01 to B-06
- Worker: `res-r2-battery` (owner member `mocry`)
- Model as configured: `deepseek-v4.1-flash-1017`
- Harness: Clever User worker harness; **build not exposed** to me, so it is reported as unknown
- Role: independent first-pass researcher. I am not the controller; I do not publish, commit or push.

## Timing (UTC)

- Start of work: 2026-11-03T19:33Z (session began; first successful search shortly after)
- Document captures: 2026-11-03T19:36:01Z (Lazard LCOE+), 2026-11-03T19:49:52Z (Tesla Megapack 2 XL datasheet), 2026-11-03T20:02:57Z (PNNL ESGC 2022), 2026-11-03T20:09:01Z (DEA Technology Data for Energy Storage)
- Finish of first pass: 2026-11-03T20:25Z (files written)

Timeline note, stated rather than reconciled: the workspace clock reads 2026-11-03. The public pages I retrieved presented a Lazard June 2025 report plus a 2026 edition landing page, and a DEA catalogue whose Li-ion chapter was updated in May 2025. I report the vintages I actually saw. I did not edit either the date or the documents.

## Independence

I declare:

- I read **only** files inside `Tier1/workspaces/mocry/cleveruser/inputs/` (the course brief, transcript extracts, baseline, gaps, research request and template) and the material I created in `firstpass/R2-battery/`.
- I did **not** open, list, grep or read anything under `Tier1/public/research_1103/`.
- I did **not** open, list or read any other folder under `Tier1/workspaces/mocry/cleveruser/firstpass/`.
- I did **not** consult peer findings before producing this pass, because none were read.
- External evidence is from public web sources only, cited by URL in `sources.json`; no vendor PDF is redistributed, and no course material was modified.

If the controller finds any of the above to be false, this first pass should be treated as contaminated and discarded rather than silently merged.

## Method summary

1. Read the assigned package and gap definitions, then searched for primary sources named or implied by the brief: the DEA energy-storage catalogue (the brief's own cost citation), a manufacturer datasheet for the product family named in the brief, and a national-laboratory cost database.
2. Captured each document immutably, read specific pages/tables, and recorded the locator plus a short quotation in `sources.json`.
3. Reconstructed the brief's EUR 0.288 m/MWh from the DEA component tables rather than accepting it, and cross-checked the result against an independent industry benchmark (Lazard) and an independent national-lab assessment (PNNL).
4. Converted findings into an optimisation-ready interface, keeping nameplate versus usable energy, power versus energy, and equipment-only versus installed cost strictly separate.
5. Time-boxed: after the fourth primary document I stopped fetching and turned gaps into explicit bounded ranges instead of chasing further products.

## Evidence-level honesty

- **Directly read by me** (extracted text I received and can quote): the Tesla Megapack 2 XL datasheet in full; Lazard LCOE+ p.43 assumptions table; DEA Tables 8 and 10 plus surrounding text on pp.176-181; the DEA landing page.
- **Read through a helper over my own captured copy, locators recorded but wording reported rather than verified character by character**: PNNL ESGC 2022 Tables 4.3/4.4, its O&M/refurbishment and cycle-life passages; the DEA front-matter cost-definition statements (price level, cost boundary, no scale rule).
- **Not read**: DEA Figure 7 (a chart), the DEA Li-ion round-trip-efficiency row, any non-Tesla product datasheet, NREL ATB (network failure), any UK-specific battery quote or price list.

## Sources I tried and failed to obtain

| Source | Failure | Effect |
|---|---|---|
| NREL ATB utility-scale battery storage | DNS resolution failure (gaierror 11001, retryable) in the browser sandbox | One fewer independent catalogue; Lazard and PNNL still bracket the DEA value |
| DEA storage datasheet download (`ens.dk/media/6589/download`) | Harness reported unsupported document type | Summary table (RTE, lifetime) unread; used chapter text and component tables instead |
| DEA older energy-storage URL | HTTP 404 (page moved) | Resolved via the new landing page |
| A second/third commercial battery datasheet | Not attempted inside the time box | Module-grid evidence rests on one product; disclosed |
| Public bulk-discount schedule for grid BESS | None located; DEA applies no scale rule | Explicit gap; two-step scale sensitivity used as fallback |
| Standby/self-discharge figure for a grid BESS | None obtained | Explicit gap; 0 baseline with 0.5%/day sensitivity |
| Residual/disposal value for a grid BESS | None obtained; DEA excludes decommissioning | Explicit gap; residual 0, disclosed as a modelling choice |

## What a reviewer should check first

1. The DEA reconstruction arithmetic in `REPORT.md` Section 3 (0.298 vs 0.288) - it is the load-bearing claim of this pass.
2. The PNNL values, which were helper-mediated; a one-step re-read of p.17-22 would settle them.
3. Whether the one-cycle-per-day convention (B-04-03, B-06-01) is the convention the team wants in the run manifest.
