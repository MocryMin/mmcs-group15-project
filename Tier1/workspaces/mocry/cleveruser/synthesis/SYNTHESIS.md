# Independent Tier1 research — controller synthesis (release 20261103-cu-v1)

Author: registered agent `mocry-cleveruser` (member `mocry`, human owner Ran Min). Date: 2026-11-03. Status: **controller synthesis of four independent first passes; a proposal for the group, not an adopted decision, and not a replacement of Baseline 1103.**

Package reports: [R1 market](packages/R1-market/REPORT.md) · [R2 battery](packages/R2-battery/REPORT.md) · [R3 electrolyser/H2](packages/R3-hydrogen/REPORT.md) · [R4 finance/data](packages/R4-finance-data/REPORT.md). Machine-readable: each package's `parameters.json` and `sources.json`, plus the assembled [BASELINE_CANDIDATE_CU.json](BASELINE_CANDIDATE_CU.json).

## 1. What this release is, and how independence was protected

The project's own request (`Tier1/public/baseline_1103/RESEARCH_REQUEST.md`) asks for independent first passes that do not read peers' findings before producing their own evidence, with first-pass output preserved before cross-review. This release follows that structure:

- Four researcher workers of agent `mocry-cleveruser` were each given a byte-identical input bundle (`inputs/`, hashes in `INPUT_BUNDLE.json`) containing only the course question: the brief and its PDF text extract, the five CSVs, both transcripts, `PROJECT.md`, `TEACHER_*`, `GAPS.md`, `BASELINE_1103.md`, `RESEARCH_REQUEST.md` and the result template.
- Each worker was explicitly forbidden from reading `Tier1/public/research_1103/**` (the earlier research round) or any other package folder, and was required to declare in `FIRST_PASS.md` what it did or did not see. All four declared no peer or earlier-round material seen.
- First passes were written and left unmodified; this synthesis reads them only afterwards.
- **Disclosure that limits the "blind" claim at the controller layer:** before designing this work, the controller had already read `Tier1/public/research_1103/controller/mocry-codex/20261103-v1.1/README.md` and `EXECUTIVE_SUMMARY_EN.md` while exploring the repository. The workers never saw those files, so the four first passes are uncontaminated, but the controller's *choice of emphasis* in this synthesis cannot be certified blind. Cross-checking against the earlier round is therefore a separate, explicitly non-blind step ([CROSS_REVIEW_NOTES.md](CROSS_REVIEW_NOTES.md)).

## 2. Minimal Tier1 interface that can be instantiated today

Assembled from the four packages; each line is traceable to a package file and a source entry there.

### 2.1 Energy, prices and demand

| Item | Recommended value / rule | Basis |
|---|---|---|
| Study window | 2,406 common dates, 2020-01-01 → 2026-09-17, 28 continuous segments; SOC restarts at each segment start | R4 §2, controller audit |
| Daily energy | `E_t = 24 × MW_t`, one convention for every series and every scheme | R4 D-01; identity `£/MW-day = 24 × £/MWh` holds exactly on all 2,422 price rows |
| Electricity price | `avg_price_£_per_MWh` only; never re-multiply the £/MW-day column | R1 §9.4 |
| Demand role | policy constraint (regime B) plus KPI denominator; **not** a market quota in regime A unless the team chooses that convention | R1 §9.3 |
| Export route | daily merchant sale at `p_t`, volume ≤ available energy, cap `E_cap = 1,125 MW` (observed farm maximum) | R1 R-EXP |
| Purchases | **disabled** in the minimum baseline; if enabled require a non-zero adder `a` and report break-even `a* = 0.90·p_sell − p_buy` | R1 §10.9, E-03 |
| Hydrogen route | direct sale at £9.5/kg ⇒ £169.95 per MWh of input electricity; finite offtake cap is a scenario, not evidence | R1 §9.1, R3 §2.6 |
| Curtailment payment | 0, disabled; no eligibility exists for a constructed system | R1 E-06 |

### 2.2 Battery block

| Item | Recommended value | Range | Basis |
|---|---|---|---|
| Configuration | 2-hour: `P = E/2`, `E` in MWh as decision variable | — | brief; R2 B-01 |
| Module grid | 1.927 MW / 3.854 MWh per unit; continuous LP + integer check | — | Tesla Megapack 2 XL datasheet, R2 |
| Installed CAPEX | €0.298 m(2020)/MWh, EPC-inclusive, shallow connection, excl. VAT | 0.16–0.41 | R2 §3, DEA storage catalogue reconstructed |
| Round-trip efficiency | 0.90, split symmetrically η = √0.90 each way | 0.83–0.92 | brief; R2 |
| SOC window | 0.20–0.80 ⇒ 0.60·E usable ⇒ **1.2 h at rated power** | — | brief; R2 §0.3 |
| Throughput | ≤ 1 equivalent full cycle/day (0.60·E discharged) | — | R2 B-06 |
| Life / replacement | 15 y standard warranty; year-10 PCS refurbishment ≈ 0.0104 m€/MWh; 20 y sensitivity | — | R2 |
| Fixed O&M | €3.0/kWh-yr — **flagged conflict, see §3.3** | 1.2–8.0 | R2 |

### 2.3 Electrolyser and hydrogen block

| Item | Recommended value | Range | Basis |
|---|---|---|---|
| Specific consumption | 55.9 kWh/kg AC, full system incl. water treatment and BoP, beginning of life | — | ITM POSEIDON datasheet p.2 (confirms the brief) |
| Load range | 20–100 % with binary on/off; 20 % is a module-configuration floor, not a physics law | 12.5–25 % other modules | ITM product sheets, R3 H-02 |
| Installed CAPEX | £1.04 m/MW_e (2026) core — recomputed from the package's own BEIS basis ×1.25; the package text states £1.50 m/MW_e there and that value does not follow from its arithmetic (see CR-1) | £0.85 (list equipment) – £3.30 (committed FOAK capital) | R3 H-01; CROSS_REVIEW_NOTES CR-1 |
| Fixed / variable OPEX | £26.3/kW_e-yr; £0.154/kg | — | BEIS 2021 annex, R3 |
| Stack replacement | 60 % of CAPEX every 11 years | — | BEIS, R3 H-03 |
| Plant life / hurdle | 30 y / 10 % (R3 asset view; differs from the project-level rate, see §3.1) | — | BEIS annex |
| H2 value | £9.5/kg nominal **is an LCHA strike price for 11 contracted projects, settled against a gas reference price**; real-2012 equivalent £6.90/kg | 2.50 / 9.50 / 12.00 ladder | HAR1 + T&S report, verified arithmetic |
| H2 offtake | scenario cap required; no public merchant price or contracted volume obtained | — | R3 H-04 |

### 2.4 Financial conventions

| Item | Recommended value | Note |
|---|---|---|
| Currency / prices | GBP, real 2026 prices, CPI (ONS D7BT) deflation; EUR→GBP at ECB annual mean of the source's price year | R4 F-01 |
| Discounting | report every headline at 3.0 / 7.0 / 10.0 % real, 15-year horizon; **7 % is a declared team assumption** | R4 F-02; no source identifies this client's cost of capital |
| Capital accounting | annualise CAPEX or discount it once — never both; separate line for stack replacement; residual straight-line or zero | R4 F-03 |
| Validation | seven-item release gate: energy balance, money balance, device limits, degenerate cases, solver status+gap, runtime pilot, determinism | R4 V-01, stated as requirements only |

## 3. Where the independent evidence conflicts, and what the team must decide

### 3.1 Discount rate — no evidence-based answer exists
Green Book 2026 states 3.00 % real social time preference, while the review's own terms of reference (updated 28 Oct 2026) state 3.5 %; two official pages read on the same day disagree, and neither identifies a private investor's cost of capital. R3 works at a 10 % asset hurdle, R4 recommends a 3/7/10 % band. **Decision required:** one project-level rate convention, with the band reported.

### 3.2 Price basis — 2020 vs 2026 real
The battery CAPEX source is EUR(2020), the electrolyser cost evidence is GBP(2020) uprated by an assumed ×1.25, and the hydrogen support value is a nominal strike price, while the electricity series is a nominal historical price. R4 recommends GBP real 2026 with CPI deflation. Quoting the BEIS-based electrolyser figure (2020 prices) next to R4's 2026 deflators without an explicit conversion step would be an unnoticed error. **Decision required:** one price basis recorded in the run manifest, with every converted parameter labelled.

### 3.3 Battery maintenance — a genuine factor-of-two question
R2 recommends €3.0/kWh-yr (≈ €9 k/yr on a 3 MWh unit) but explicitly flags the catalogue's internal conflict between a displayed unit-cost row and a percentage-of-CAPEX footnote. This is the same unresolved conflict an earlier round must also confront; it is material because it is a recurring annual cost. **Action:** pick one convention, carry the other as sensitivity, and say which was used in every reported cash flow.

### 3.4 Data artefact that must not be silently repaired
Independent audit (two separate implementations, R4's and the controller's) agrees exactly on rows, duplicates, coverage, the 2,406-date / 28-segment intersection, the fuel-vs-total reconciliation (max |diff| = 0 MW on all 2,422 dates) and the price identity. R4 additionally finds **107 dates on which every dispatchable fuel (nuclear, gas, coal, oil, biomass, hydro, pumped storage, other) is exactly 0 MW**, in nine contiguous blocks between 2022-10-17 and 2026-08-03; the controller reproduced the count, the date range and the effect (deficit falls from 160.30 to 111.41 TWh when those 107 dates and the 2022-08-02 demand outlier are excluded; surplus barely moves, 40.63 → 40.01 TWh). **Action:** report the all-days run and the artefact-excluded run side by side; do not "repair" generator output.

## 4. Findings most likely to change the investment recommendation

1. **Scale anchor (R1):** at the sample mean the farm's gross electricity revenue is ≈ £179 m/yr; flexibility revenue is small against it, and flex assets must be justified by *incremental* value, not by the size of the surplus energy pool. R1 shows hydrogen can out-bid direct sale only on days when `p_t` exceeds ≈ £170/MWh.
2. **Usable window (R2):** a "2-hour" battery has 1.2 h of usable energy at rated power under the brief's 20–80 % rule, so daily-resolution results describe a *daily energy shifter*, not intraday arbitrage. Any claim of intraday value is unsupported by these data.
3. **Hydrogen economics (R3):** with electricity at the historical mean, hydrogen at £2.50/kg loses money before CAPEX (£5.59/kg just for electricity); the entire H2 case rests on the supported-value scenario, not on a merchant market.
4. **Surplus is thin (controller audit):** surplus energy is 2.7 % of generation and appears on 29 % of days; the largest single day is 1.5 % of the six-year total. Peak-day capacity and annual energy value are therefore different questions.
5. **Data artefacts (R4):** the 107 zero-dispatch dates and the 2022-08-02 demand point move deficit statistics materially and must be reported both ways.

## 5. What is still not known

No merchant hydrogen price, offtake volume, plant-gate netback or buyer contract; no 2026 UK installed electrolyser quotation; no itemised battery maintenance contract; no project cost of capital; no non-commodity import adder; no intraday price series. Each is recorded with a bounded fallback in the package reports rather than filled with an invented number.

## 6. Reproduce

- Input bundle: `inputs/` (byte-identical copies; hashes in `inputs/INPUT_BUNDLE.json`).
- Controller data audit: `controller-data-audit/tools/audit_data.py`, output `controller-data-audit/data_audit.json`; artefact cross-check `tools/crosscheck_r4_artefact.py`.
- Package deliverables: `packages/<package>/REPORT.md`, `parameters.json`, `sources.json`, `FIRST_PASS.md`; R4 also ships its audit scripts and JSON outputs.
- Release manifest with SHA-256 of every file: `RELEASE_MANIFEST.json`.
