# Controller cross-review notes

Author: `mocry-cleveruser`. Date: 2026-11-03. Status: controller verification of high-impact claims plus one explicitly **non-blind** comparison. This file does not change the package first passes; it records what reproduced, what did not, and what remains unverified.

## Method

Every arithmetic check below was recomputed by the controller from the cited source value or from the supplied CSVs, not read off a package report. Data checks use an independent implementation (`controller-data-audit/tools/audit_data.py` and `tools/crosscheck_r4_artefact.py`) written before R4's results were read, so agreement between the two is replication by different code on the same bytes, not mutual quotation.

## CR-1 — Electrolyser CAPEX: the stated core does not follow from its own arithmetic (material)

R3 states: core `£1.50 m/MW_e` = BEIS 2020 central `£0.83 m/MW_e` "uprated ×1.25 for 2020→2026".

Recomputed: `0.829 × 1.25 = 1.036`, i.e. **£1.04 m/MW_e (2026)**, not £1.50 m. The package's own conversion table for the other BEIS rows is consistent, so this is a single derived value, not a systematic error: the ladder (0.85 list / 3.30 FOAK) and the BEIS 2020 range (£0.77–1.16 m/MW_e) both stand.

Consequences:
- Do not carry £1.50 m/MW_e into a run as a "sourced" central case. Either use **£1.04 m/MW_e (2026)** with the ×1.25 assumption visible, or state an explicit different multiplier (≈1.81) and justify it.
- This also changes the common-basis comparison in CR-5.

## CR-2 — The 107-date zero-dispatch artefact reproduces

R4 reports 107 dates on which every dispatchable fuel (nuclear, gas, coal, oil, biomass, run-of-river, pumped storage, other) is exactly 0 MW. Recomputed independently: **107 dates confirmed**, spanning 2022-10-17 → 2026-08-03, with total generation between 1,450 and 17,614 MW on those days.

One difference: R4 describes "five contiguous blocks"; the recomputation finds **nine** contiguous blocks (1, 2, 42, 10, 12, 4, 10, 1, 25 days). The date count matches exactly; the block count differs, most likely because adjacent short gaps were merged in R4's grouping. Not material for the exclusion rule, but the run manifest should use the date list, not the block count.

Excluding those 107 dates plus the 2022-08-02 demand outlier: deficit **160.30 → 111.41 TWh** (recomputed: 111,405,252 MWh), surplus **40.63 → 40.01 TWh** (recomputed: 40,009,834 MWh). Both match R4 to the last digit at the reported precision.

## CR-3 — Two independent data audits agree exactly

| Check | R4 implementation | Controller implementation |
|---|---|---|
| Data rows per file | 2,451 / 2,422 / 26,642 / 2,422 / 2,453 | identical |
| Common dates | 2,406 (2020-01-01 → 2026-09-17) | identical |
| Continuous segments | 28, longest 2022-09-24 → 2026-09-17 (1,455 days) | identical |
| Fuel sum vs total | max abs diff 0 MW on all 2,422 dates | identical |
| Price identity | `£/MW-day = 24 × £/MWh`, max relative deviation 1.5e-16 | identical (exact to float) |
| Negative / zero price days | 9 / 1 | identical |
| Duplicate dates | none | none |

This is a strong check on the data facts and on the parsing conventions (Elexon-style `recordType`/`startTime` in the demand file is the trap here).

## CR-4 — Headline conversions recomputed

| Claim | Recomputation | Result |
|---|---|---|
| Battery installed cost, 2-hour (R2) | (0.077+0.023+0.081+0.010+0.037) + (0.069+0.017)/2 = 0.271; ×1.10 EPC | **0.2981 m€(2020)/MWh** — reproduces; +3.5 % vs the brief's 0.288 |
| Usable battery window (R2) | 0.60·E at P = E/2 | **1.2 h at rated power** — reproduces |
| Hydrogen price derivation (R3) | 241 £/MWh × 39.4 kWh/kg ÷ 1000 | **£9.4954/kg** — reproduces |
| Hydrogen real-terms (R3) | 175 £/MWh(2012) × 39.4 ÷ 1000 | **£6.895/kg(2012)** — reproduces |
| Hydrogen electricity-equivalent (R1/R3) | 9.4954 ÷ 55.9 kWh/kg | **£169.85–169.95/MWh** of input electricity — reproduces |
| Battery EUR→GBP (R4) | 0.288 m€/MWh × 0.86097 | **£247,959/MWh ≈ £0.496 m per MW** of 2-hour battery — reproduces |
| CPI 2020→2026 (R4) | factor 1.30595 | consistent with the individual annual values cited in its `finance_evidence.json` |

One rounding discrepancy worth noting for citation discipline: the electricity-equivalent of £9.5/kg is £169.95/MWh using 55.9 kWh/kg; R3's text also writes "£170/MWh". Both are the same number at different precision; quote one.

## CR-5 — Non-blind comparison with the earlier round (20261103-v1.1)

**This section is not blind.** The controller had read the v1.1 `README.md` and `EXECUTIVE_SUMMARY_EN.md` during repository exploration, before designing this work. The four first passes remained blind; this comparison did not. It is reported because an independent replication is only useful if its agreements and disagreements are stated, and because two of the items below are genuine disagreements that a human modelling decision must settle.

| Item | Earlier round (as read in its executive summary) | This round (independent) | Reading |
|---|---|---|---|
| Battery installed CAPEX | EUR 288,000 per nameplate MWh for a 3 MWh / 1.5 MW (2-hour) system, DEA workbook | €0.2981 m(2020)/MWh reconstructed from the same catalogue's cost elements | **Agreement within 3.5 %** — two routes to the same catalogue |
| Dataset facts (dates, segments, negative prices, demand outlier) | 2,406 common dates, 28 segments, 9 negative-price days, 636 MW demand on 2022-08-02 flagged | identical, by different code | **Agreement** |
| Battery maintenance cost | A factor-of-two conflict kept as two scenarios (a displayed unit cost vs 2.9 % of total CAPEX) | €3.0/kWh-yr, also flagged as a conflict | **Both flag a conflict, but the numbers differ by roughly 1.4–2.8×** on a 3 MWh unit. Unresolved; needs one convention plus a sensitivity |
| Electrolyser installed CAPEX | IEA 2024 outside-China range USD 2,000–2,600/kW, deflated to **GBP2020 1,270–1,651/kW_e**, midpoint **1,460** | BEIS 2020 UK nth-of-a-kind **£0.77–1.16 m/MW_e**, core as computed **£1.04 m/MW_e (2026)** ≈ £0.79 m/MW_e (2020) | **Genuine disagreement, ≈1.8× on a common 2020 basis.** Different evidence routes: a global IEA installed-cost survey vs UK government nth-of-a-kind engineering estimates. The UK FOAK anchor (£3.30 m/MW_e) sits above both. This is the single most consequential unresolved parameter for the H2 case |
| Hydrogen support value in real terms | £175/MWh(2012) → **£7.799/kg(2020)** | £6.895/kg(2012) | **Agreement after deflation** (6.895 × ≈1.13 ≈ 7.80): independent derivations, different price bases, consistent |
| Discount rate | 5 % real, sensitivity 0 / 3 / 8 / 12 % | 7 % real central, band 3 / 7 / 10 % | **Disagreement.** Neither is evidence-based for this client; pick one convention and report the band |
| Price basis | Constant 2020 GBP | Real 2026 GBP with CPI deflation and FX at the source's price year | **Framework difference**, not an error; mixing the two silently is the real risk |
| 107 zero-dispatch dates | Not reported in the earlier executive summary | Found and reproduced | **New finding this round**; affects deficit reporting materially |

## What this cross-review does not establish

- It does not validate any parameter: two implementations parsing the same bytes agree on the bytes, and two research routes agreeing on a catalogue value do not make the catalogue a market price.
- It does not resolve CR-1's arithmetic, the battery maintenance conflict, the electrolyser CAPEX disagreement or the discount-rate choice. Those are recorded decisions for the team.
- Vendor documents were read by workers with recorded locators and quotes; the controller did not re-open every PDF. The two claims that matter most (55.9 kWh/kg, £241/MWh with its 2012-price parenthetical, 39.4 kWh/kg HHV) are quoted in the packages with page locators and are reproducible from the public links.
