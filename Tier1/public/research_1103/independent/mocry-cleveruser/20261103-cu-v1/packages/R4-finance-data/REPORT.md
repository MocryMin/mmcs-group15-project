# R4 — miscellaneous data, finance and implementation (independent first pass)

Package: R4 of `inputs/RESEARCH_REQUEST.md` (gap IDs F-01..F-03, D-01..D-03, V-01; X-01 not attempted).
Result path: `Tier1/workspaces/mocry/cleveruser/firstpass/R4-finance-data/`.
Status: first-pass result for controller review. Not published to `Tier1/public/**`, not committed.

## 1. Identity, independence and scope

- Result ID: `firstpass-R4-finance-data`, 2026-11-03 (started 2026-11-03T21:05Z, finished 2026-11-03T21:5xZ UTC; see `FIRST_PASS.md` for exact times and identity).
- Package: R4 only. B-*, H-*, E-* parameters are referenced but not researched; equipment costs, stack life and H2 prices are explicitly left to R2/R3.
- Independence: first pass produced without reading `Tier1/public/research_1103/**`, without reading any other folder under `.../cleveruser/firstpass/`, and without reading any `mocry-codex` file outside `inputs/`. Only `inputs/` and files created in this folder were used. No earlier-round parameter value is knowingly reproduced.
- Inputs used: the five CSVs, `BASELINE_1103.md`, `GAPS.md`, `TEACHER_CLARIFICATIONS.md`, `brief_extracted_text.md`, `RESEARCH_REQUEST.md`, `RESEARCH_RESULT_TEMPLATE.md`.
- Everything numeric below was computed by the scripts in this folder from the byte-identical input copies; the audit is reproducible with
  `python audit_inputs.py`, `python derived_checks.py`, `python data_quality.py`, `python fetch_finance.py`.

## 2. Findings and recommended interface

### 2.1 D-01 — exact units and daily power/energy convention

| Claim | Finding | Evidence |
|---|---|---|
| `daily_generation_by_fuel.csv` | `date`, `psrType` (11 technologies), `MW`; 26,642 rows = 2,422 dates × exactly 11 rows; no duplicate (date, technology) pair | `audit_results.json` → `checks.fuel_vs_total` |
| `daily_generation_total.csv` | `date`, `total_MW`; 2,422 rows; **equals the per-date sum of the 11 fuel rows on all 2,422 dates, maximum absolute difference 0 MW** | same |
| `daily_demand.csv` | `recordType` = `VD` on every row, `startTime` = `YYYY-MM-DDT00:00:00Z`, `demand`; 2,451 rows, no duplicates | `audit_results.json` → `files["daily_demand.csv"]` |
| `wind_farm_generation.csv` | `date`, `wind_farm_MW`; 2,453 rows, 2020-01-01..2026-09-18 (one day longer than every other file) | same |
| `daily_market_index_price.csv` | `date`, `avg_price_£_per_MWh`, `avg_price_£_per_MW_day`; **`per_MW_day = 24 × per_MWh` on all 2,422 rows (max relative deviation 1.5e-16)** | `checks.price_column_identity` |

Energy convention: **E_MWh(t) = MW(t) × 24**, because every file is one value per calendar day and the price file itself prices a "MW held for one day" as exactly 24 MWh. On the 2,406 common dates this gives mean generation 26,016 MW (total generation + wind farm) and mean demand 28,089 MW, i.e. ≈228 TWh/yr and ≈246 TWh/yr — national-scale magnitudes, consistent with the lecture's "UK scale" description.

**What the data cannot tell us.** A single daily value cannot distinguish a 24-hour mean power from an instantaneous snapshot (or a metered daily total mislabelled `MW`). Nothing in the five files, the brief or the transcript resolves this. Recommended assumption: the value is the **daily mean power**, so E = 24 × MW. Consequence, stated for the record: every energy and revenue total is exactly proportional to the assumed 24 hours, while CAPEX is not; a 12-hour assumption would halve all MWh, halve annual revenue and halve NPV without changing CAPEX, so the hours assumption is a first-order driver, not a detail. It must be written in the run manifest and must not be varied between schemes A0/A1/B0/B1.

Prices: use `avg_price_£_per_MWh` as £ per MWh sold; the `per_MW_day` column is only a check. The series is nominal £ of each historical year — it carries no deflator, so cross-year aggregation needs the CPI treatment in §2.2.

### 2.2 F-01 — base currency, price year and nominal/real

Recommended interface (a team decision, not a finding):

- **Reporting currency: GBP (£).** The revenue side is already GBP; only equipment CAPEX arrives in EUR.
- **Base price year: 2026** (appraisal date November 2026). Latest ONS CPI available at access: September 2026 = 144.1 (2015=100); the Jan–Sep 2026 mean is 142.022.
- **Real vs nominal: model in real 2026 £.** Deflate any nominal value of year *y* by CPI(2026)/CPI(*y*) using annual-mean indices: 2020→2026 ×1.30595, 2025→2026 ×1.02642. Then discount with a real rate (§2.3) — never add an inflation rate to a real discount rate.
- **EUR→GBP:** ECB daily reference rate, annual means of GBP per EUR (2019: 0.87777, 2020: 0.88970, 2021: 0.85960, 2022: 0.85276, 2023: 0.86979, 2024: 0.84662, 2025: 0.85679, 2026 to 3 Nov: 0.86097; latest observation 2026-11-03 = 0.83358).
- Conversion worked through for the brief's battery cost: €0.288m/MWh × 0.86097 = **£247,959/MWh ≈ £0.248m/MWh** at the 2026 mean; spot 0.83358 gives £240,071/MWh; the 2020–2026 annual-mean band £243.8k–£256.2k/MWh is −1.7 % to +3.3 % around the 2026 value. A 2-hour battery is therefore **£495,919 per MW** of power capacity.
- Caveat that must travel with the number: the €0.288m figure is a Danish Energy Agency technology-data value whose own price year is not established here (R2's job). The FX rate should match the source's price year, not the appraisal date; using the 2026 mean is a documented fallback worth about ±3%.

Deflator caveat: CPI is a household consumption basket, not a capital-goods deflator. The GDP deflator would be the better deflator for equipment and is **not** obtained in this pass — recorded as a gap (§5). For a 5-year span the difference is a few percentage points, which is small next to the discount-rate uncertainty.

### 2.3 F-02 — discount rate, horizon, and what the guidance does and does not cover

Official guidance actually read:

- HM Treasury **Green Book (2026)**, section "Discounting": *"It is set at 3.00% in real terms for years 1 to 30 of an appraisal"*, then 2.50% for years 31–75 and 2.25% from year 76; and *"The STPR is a real discount rate and must be applied only to values expressed in real terms"*.
- HM Treasury **Green Book Discount Rate Review 2026, Terms of Reference** (updated 28 October 2026): *"The STPR is currently set at 3.5% in real terms for the first 30 years of a proposal"*, with the pre-2003 alternative being a social opportunity cost of capital *"based on the rate of return that would be expected on funds left in the private sector"*.

Two official GOV.UK pages accessed on the same day state different rates (3.00% in the 2026 Green Book edition, 3.5% described as "currently set" in the review's terms of reference updated 28 October 2026). Both are real, social, welfare-based rates. This discrepancy is recorded, not resolved by preference.

**The decisive scope point:** the STPR is a *social* time-preference rate for appraising public policies in terms of social costs and benefits. It is **not evidence of this client's cost of capital**. A private consortium's required return reflects its own debt/equity mix, tax, market risk and investor hurdle rate, none of which any document read here supplies. Therefore:

- the discount rate is an **explicit team decision**, reported with a **sensitivity range**, and never presented as "the market rate";
- recommended reporting set: **3.0% real (Green Book social rate, lower bound/comparability case), 7.0% real (central case, team assumption), 10.0% real (upper sensitivity)**; every headline result is reported at all three, with the central case labelled as an assumption;
- no source in this pass estimates a project-specific WACC or hurdle rate. Anyone quoting a single "market" rate must cite one; this report does not.

Horizon: **15 years** base case (consistent with a 2-hour battery's typical commercial life and with keeping one battery purchase inside the horizon), **10 and 20 years** in sensitivity. Investment at t = 0 (undiscounted), real operating cash flows in years 1..15.

Discount factors and capital-recovery factors computed in `derived_checks.json`:

| rate (real) | DF year 1 | DF year 10 | DF year 15 | DF year 20 | CRF 15 yr | CRF 20 yr |
|---|---|---|---|---|---|---|
| 3.0% | 0.970874 | 0.744094 | 0.641862 | 0.553676 | 0.083767 | 0.067216 |
| 3.5% | 0.966184 | 0.708919 | 0.596891 | 0.502566 | 0.086825 | 0.070361 |
| 7.0% | 0.934579 | 0.508349 | 0.362446 | 0.258419 | 0.109795 | 0.094393 |
| 10.0% | 0.909091 | 0.385543 | 0.239392 | 0.148644 | 0.131474 | 0.117460 |

### 2.4 F-03 — annualisation, replacement, residual value, payback

- **Annualisation:** annual-equivalent CAPEX = CAPEX × CRF(r, n) with CRF = r / (1 − (1+r)^−n). For the 2-hour battery at £495,919/MW: ≈£41.5k/MW-yr at 3.0%, ≈£54.4k/MW-yr at 7.0%, ≈£65.2k/MW-yr at 10.0% (15-year life). Annualising CAPEX and also charging the full CAPEX once would double-count; pick one convention per table.
- **Replacement:** if the horizon exceeds an asset's life, charge the replacement as a discounted cash flow in the replacement year, or fold it into the annual charge via a sinking-fund factor — never both. Battery: one replacement only if the horizon is 20 years and the assumed life is 15. Electrolyser stack replacement (≈ every 10 years per R3's evidence, not established here) must be a separate line, because a 15-year horizon spans one stack replacement and it is material to the H2 case.
- **Residual value:** conservative default = 0. If a residual is credited, use straight-line depreciation of undiminished life and discount it: residual = CAPEX × (remaining years / life) × DF(horizon). The same rule must be applied to every scheme, including the zero-investment cases (where it is 0).
- **Payback:** report two definitions. *Simple payback* = CAPEX / mean annual net cash flow (real 2026, undiscounted); *discounted payback* = the first year in which cumulative discounted net cash flow ≥ 0 at the same rate. Also report NPV/CAPEX as ROI. Warning to carry into the report: simple payback built on one representative year hides the 2022 price spike and the 5×-varying annual mean price (16.1 → 95.4 £/MWh across 2020–2022), so payback must be shown against the low/central/high price years, not a single average.
- **Representative-year bridge (needed because only 6.59 years of data exist):** annual profit = (total profit over the 2,406 common dates) / 6.587 years. Multiplying by the annuity factor (15 yr: 11.938 at 3.0%, 9.108 at 7.0%, 7.606 at 10.0%) converts it to a 15-year present value. This assumes the observed years are representative, which is an assumption; the 2020–2026 window includes a pandemic year, the 2022 gas crisis and 27% cumulative inflation, so we also report the in-sample net profit over the observed days as a no-extrapolation check.

### 2.5 D-02 — dates, gaps, coverage and data-quality screens

Independent file audit (all five files hashed; hashes match `SOURCE_MANIFEST.json` exactly):

| file | rows | dates | first..last | duplicate dates | calendar days missing inside own span |
|---|---|---|---|---|---|
| daily_demand.csv | 2,451 | 2,451 | 2020-01-01..2026-09-17 | 0 | 1 |
| daily_generation_total.csv | 2,422 | 2,422 | 2020-01-01..2026-09-17 | 0 | 30 |
| daily_generation_by_fuel.csv | 26,642 | 2,422 | 2020-01-01..2026-09-17 | n/a (11 rows/date) | 30 |
| daily_market_index_price.csv | 2,422 | 2,422 | 2020-01-01..2026-09-17 | 0 | 30 (16 of which are dates that generation has) |
| wind_farm_generation.csv | 2,453 | 2,453 | 2020-01-01..2026-09-18 | 0 | 0 |

**The files do not drop the same days.** Pairwise differences: demand has 30 dates with no generation row; generation has 1 date with no demand row (2020-07-07); the price file has 16 dates that generation lacks while lacking 16 generation dates; the wind file has 31 dates that generation lacks and covers every generation date.

**Common-date intersection: 2,406 of 2,452 calendar days (98.1 %), 2020-01-01..2026-09-17, in 28 calendar-continuous segments with 27 gaps.** Gaps are 1–4 days each and cluster in 2020-07..2022-09; the longest segment is **2022-09-24..2026-09-17 (1,455 days)**, after which the record is unbroken. Coverage by year (common days): 2020 346, 2021 354, 2022 350, 2023 365, 2024 366, 2025 365, 2026 260.

**Energy and money on the intersection** (24 h/day, generation = total file + wind farm): 1,502.27 TWh generation (1,477.96 TWh from the total file + 24.31 TWh from the wind farm), 1,621.95 TWh demand, 40.63 TWh surplus on 702 days, 160.30 TWh deficit on 1,704 days.

**Data-quality screens (reported, nothing deleted):**

1. **S1 — 107 dates on which every dispatchable fuel row (nuclear, gas, coal, oil, biomass, hydro, pumped storage, other) is exactly 0 MW while wind and solar are populated.** These are not plausible days; they arrive in contiguous blocks (2022-12-01..2023-01-11 = 42 days; 2023-04-24..2023-05-03 = 10; 2024-02-08..2024-02-19 = 12; 2025-03-09..03-12 and 2025-03-22..03-31 = 14; 2026-07-10..2026-08-03 = 25) and therefore look like a reporting-completeness artefact in the source, not weather. 62 of them also fall below 10,000 MW total generation; every one of those 62 is inside S1.
   **Effect:** excluding S1 (plus the demand outlier in 3) reduces computed deficit from 160.30 to 111.41 TWh (−30 %) while surplus changes only from 40.63 to 40.01 TWh. A defect that removes a third of the deficit while leaving surplus intact is a supply-reporting gap, not scarcity.
2. **S3 — demand outlier:** 2022-08-02 = 636 MW against the next-lowest value of 19,241 MW and a median of 27,472 MW (only date with robust z > 6). It also creates the single largest "surplus" day (616 GWh) in the sample. Data-error candidate.
3. **S5 — wind farm saturates at exactly 1,125.0 MW on 29 dates** (clipping at the simulated installed capacity) and is exactly 0 MW on 10 dates.
4. **Price extremes retained:** 9 negative daily prices (minimum −8.465 £/MWh on 2024-01-02), one zero-price day, maximum 333.825 £/MWh on 2021-09-09; 32 dates have robust z > 6, concentrated in the 2021-09 and 2022-08 gas crises. These are genuine market events and stay in.
5. Generation values are never negative and demand is never negative or zero; 4,500 of 26,642 fuel cells are exactly 0 MW, normal for coal/oil/solar-by-night.

**Recommended convention:** model the 2,406-date intersection; keep every observed day at weight one, including negative prices and the 2021–22 price extremes (BL-04/BL-11); **never join dates across a gap as adjacent days** — a state variable (battery SOC) must restart at the minimum-SOC buffer at each of the 28 segment starts, and the 1,455-day segment is the only one long enough to support multi-day storage behaviour. Report the 1.9 % coverage loss. Pre-register the S1/S3 screen now (before seeing profit) and run **every** headline result twice: "all 2,406 days" and "SA-DQ excluding the 108 flagged days". If the battery/electrolyser recommendation flips between those two runs, that is a finding for the report, not a reason to choose the more convenient dataset.

### 2.6 D-03 — chronological design/validation/test split

Pre-registered, chronological, chosen before any optimiser exists, and not selected on held-out profit:

| window | dates | common days | use |
|---|---|---|---|
| fit / design | 2020-01-01..2022-12-31 | 1,050 | capacity and policy selection; includes the pandemic year and the 2022 gas crisis |
| validation | 2023-01-01..2024-12-31 | 731 | one confirmatory look at the frozen design |
| final test | 2025-01-01..2026-09-17 | 625 | untouched until the design is frozen; reported once |

Rules: capacity is chosen on the fit window only; a single validation pass is allowed; if validation is consulted more than once (e.g. after changing the cost assumption), the test window must be reported as "seen through validation influence" and the untouched status is lost. Selection rule fixed in advance: choose the capacity with the highest fit-window NPV, ties broken towards **smaller** capacity (a 5 % profit plateau counts as a tie). All years keep statistical weight one; discounting is a financial transformation, not a reweighting of observations (BL-04). Because storage state cannot cross the 27 gaps, chronological SOC experiments use the 2022-09-24..2026-09-17 continuous block, and the fit/validation/test windows above apply to day-independent (Tier 1) allocation. Fixed-capacity "operational oracle" runs on validation days must be labelled as oracles (BL-13), never as a strategy.

### 2.7 V-01 — validation and reporting checks the optimiser must produce

These are **requirements**, not results; no solver was run in this pass.

1. **Energy balance per day** (residual ≤ 1e-6 × that day's energy): generation + battery discharge + purchases = direct sales + battery charge + electrolyser input + unused generation. Check it independently of the objective, from the exported solution, in code that does not read the model object.
2. **Money balance**: revenue (Σ price × MWh sold + H2 kg × £/kg) − CAPEX − purchases − variable O&M = reported profit, recomputed from the export to within £1 or 1e-9 relative. CAPEX must be charged exactly once.
3. **Device limits**: SOC within [0.2, 0.8] × installed energy; charge/discharge energy per day ≤ power × 24; electrolyser either off or between 20 % and 100 % of capacity (a separate binary, with shutdown explicit — BL-08); H2 mass = MWh / 55.9 kWh/kg × 1000 with units checked.
4. **Degenerate cases**: A0 and B0 must both solve with zero investment and produce identical results when the policy is switched off; a forced minimum capacity must be infeasible-free; the relaxation LP must bound the MILP.
5. **Solver reporting**: status (optimal/feasible/…), objective value, MIP gap, node count and wall-clock, Xpress version, and the input file hashes. Accept "optimal" or gap ≤ 1e-4 relative; anything else is reported as a bound, not a result.
6. **Runtime pilot**: report the measured wall-clock for the full 2,406-day model on the team's machine and the date/time of the measurement. The lecture treats 5 min–1 h as the working envelope; a model that needs 16 h must be reformulated (aggregation, fewer binaries, tighter bounds). No runtime figure is claimed here.
7. **Determinism**: fixed solver threads/seed, one documented solve per scenario, and a stored solution export so every reported number can be re-derived.

## 3. Conversions and checks (arithmetic shown)

- Fuel reconciliation: 11 rows × 2,422 dates = 26,642 rows, per-date sums equal `total_MW` on all 2,422 dates (max |diff| = 0 MW). The total file is therefore an exact aggregate; adding fuel rows to the total again would double-count (BL-02).
- Price identity: `per_MW_day / per_MWh` = 24.000000 on all 2,422 rows (max relative deviation 1.5e-16) ⇒ one day = 24 MWh per MW.
- FX: €0.288m/MWh × 0.86097 GBP/EUR = £247,959/MWh; ×2 MWh/MW = £495,919 per MW of 2-hour battery. Sensitivity: 0.83358 → £240,071/MWh; 2020–2026 annual means → £243.8k–£256.2k/MWh.
- Deflation: CPI(2026 Jan–Sep mean) / CPI(2020 mean) = 142.022 / 108.750 = 1.30595; CPI(2026)/CPI(2025) = 142.022 / 138.367 = 1.02642. ONS annual inflation rates read: 2020 0.9 %, 2021 2.6 %, 2022 9.1 %, 2023 7.3 %, 2024 2.5 %, 2025 3.4 %; 2026 monthly 2.6 %–3.5 %.
- Discounting: DF(t) = 1/(1+r)^t; CRF(r,n) = r/(1−(1+r)^−n); annuity factor = (1−(1+r)^−n)/r. Values tabulated in §2.3; all generated in `derived_checks.json`.
- Sample length: 2,406 common days / 365.25 = 6.587 years; annual-average profit = total profit / 6.587.
- Decomposition check available to the team: adding up the four schemes' cash-flow components must equal the reported totals (money balance in §2.7).

## 4. Proposed decisions

Supports (no change needed): BL-02 (total file is already the aggregate — verified exactly), BL-04 (negative prices and genuine extremes retained), BL-11 (no free initial SOC; document gaps), BL-14 (cash-flow/energy checks).

Proposes changes / additions (for the controller, with IDs):

- **F-01:** adopt GBP as reporting currency, real 2026 prices, CPI (D7BT) deflation, ECB annual-mean FX matched to the source's price year. Recorded as a parameter interface; no teacher rule contradicted.
- **F-02:** report every headline NPV at 3.0 % / 7.0 % / 10.0 % real, 15-year horizon, with the central 7 % labelled a team assumption. **No source in this pass identifies the client's cost of capital**; a single-rate headline without the band would overstate precision.
- **F-03:** annualise CAPEX or discount it once, never both; separate stack-replacement line; residual = straight-line, or 0; two payback definitions.
- **D-01:** E = 24 × MW, stated in the manifest, never varied between schemes; price = `avg_price_£_per_MWh`.
- **D-02:** 2,406-date intersection, 28 segments, SOC restart at each segment start, 1.9 % coverage loss disclosed; mandatory SA-DQ re-run excluding the 107 S1 dates and the 2022-08-02 demand outlier (108 dates total).
- **D-03:** fit 2020–2022 / validate 2023–2024 / test 2025–2026-09 with the tie-break rule fixed in advance.
- **V-01:** the seven-item validation pack in §2.7 is a release gate for any number that reaches the report.

## 5. Unknowns and bounded fallbacks

- **GDP deflator not obtained** (CPI used instead; capital-goods deflation is a genuine gap). Fallback: CPI, disclose the substitution; a 2020→2026 CPI factor of 1.306 vs an unknown deflator factor is worth a few percentage points on deflated CAPEX, small against the discount-rate band.
- **No project-specific cost of capital / WACC / investor hurdle evidence** obtained; the 7 % central rate is a declared team assumption, not a finding.
- **Source price year of the €0.288m/MWh battery figure is not established here** — R2 owns it; the FX year should follow it.
- **No risk-free nominal anchor (Bank of England Bank Rate series)** was fetched in this pass; a real-rate framework does not need one, but a nominal-rate cross-check is missing.
- **Battery life, stack life, O&M and H2 price** are outside R4 and are assumed only where an example was needed (15-year battery life in the annualisation example).
- **107-date reporting artefact cannot be repaired**, only excluded in sensitivity; no public source can tell us what those days' missing fuel output was.
- **X-01 not attempted** in this pass.

## 6. Cross-validation

Not performed — this is a first pass and peer results must not be read yet (RESEARCH_BRIEF leak control). Planned cross-checks for the second pass: reproduce the power/energy and FX conversions from the primary files; re-derive the fuel-vs-total reconciliation independently; compare any proposed discount rate to the Green Book STPR quotation above and to the review's 3.5 % statement; and re-run the S1 screen to confirm the 107 dates are structural rather than threshold-dependent. Agreement between researchers will not by itself validate a parameter; the 3.00 % vs 3.5 % conflict already shows that two official documents can disagree.

## 7. Handoff

Files in `Tier1/workspaces/mocry/cleveruser/firstpass/R4-finance-data/`:

| file | content |
|---|---|
| `REPORT.md` | this report |
| `parameters.json` | typed parameter/claim records F-01..F-03, D-01..D-03, V-01 |
| `sources.json` | sources actually read, with locators, series IDs and verbatim quotes |
| `FIRST_PASS.md` | identity, timestamps, independence declaration, sources not obtained |
| `audit_inputs.py` / `audit_results.json` / `audit_summary.txt` | five-file audit: hashes, rows, duplicates, coverage, reconciliation, price identity, intersection and segments |
| `derived_checks.py` / `derived_checks.json` | anomaly lists, surplus/deficit, discount/annuity/CRF factors, FX and CPI conversions |
| `data_quality.py` / `data_quality.json` | S1–S5 screens with runs and the exclusion-scenario effect |
| `fetch_finance.py` / `finance_evidence.json` | ONS CPI (D7BT, D7G7) and ECB EUR/GBP series with the annual values used |
| `probe_sources.py`, `probe_sources2.py`, `check_dates.py`, `inspect_low_days.py`, `print_audit_highlights.py` | provenance of the probes; kept so the numbers above can be reproduced |

Suggested next action for the controller: give §2.7 to whoever builds the Xpress model as an acceptance checklist, and decide the discount-rate band (F-02) as a recorded team choice before any NPV is reported. No adoption is claimed and no other agent is asserted to have read this.
