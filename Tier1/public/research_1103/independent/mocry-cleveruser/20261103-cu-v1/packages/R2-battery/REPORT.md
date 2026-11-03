# R2 - Batteries: independent first-pass research

Package: R2 (batteries). Gaps covered: B-01 to B-06.
Status: first-pass result (independent). Not a synthesis, not a cross-review.
Scope note: I did not read any earlier research round or any other researcher's first pass (see `FIRST_PASS.md`).

Companion files: `parameters.json` (machine-readable claims), `sources.json` (sources actually read, with locators), `FIRST_PASS.md` (identity, independence, failed retrievals).

---

## 0. Headline answers

1. **The brief's EUR 0.288 m per MWh is reproducible.** Reconstructing the Danish Energy Agency (DEA) *Technology Data for Energy Storage* Li-ion chapter (May 2025 update) for a **2-hour** grid BESS from its own cost elements gives **about EUR 0.298 m(2020)/MWh of nameplate energy, fully installed and including EPC**. Price year **2020 (real EUR), excluding VAT**, cost scope **EPC/overnight installed cost including shallow grid connection, excluding deep reinforcement, land and decommissioning**. That is within +3.5% of the brief's 0.288. The brief's number is therefore not arbitrary: it matches a 2025-vintage DEA estimate for a 2-hour system, and it should be carried forward as the baseline with an explicit sensitivity band (Section 4).
2. **A 2-hour asset is a power/energy pair, not one number.** Verified commercial product: Tesla Megapack 2 XL, 2-hour configuration = **1927 kW AC / 3854 kWh per unit** (exactly 2.0 h), with AC output scalable from 400 kVA in 50 kVA steps, so a continuous capacity variable is an acceptable relaxation and the module grid can be applied at reporting/rounding time.
3. **At daily resolution the 2-hour power rating effectively disappears.** A 2-hour system has only 1.2 h of *usable* energy at rated power inside the brief's 20-80% SOC window; over a whole day that usable-energy cap binds before any power cap does. The honest daily model is therefore a *daily energy shifter with a throughput cap*, and it **cannot** represent intraday arbitrage. This must be stated, not hidden.

---

## 1. Identity, independence and scope

- Result ID: `R2-battery-firstpass-20261103`.
- Registered member/agent: worker `res-r2-battery` (owner `mocry`).
- Model/harness as configured: `deepseek-v4.1-flash-1017`, Clever User worker harness (build not exposed).
- Access window (UTC): 2026-11-03T19:36Z to 2026-11-03T20:10Z (document capture timestamps in `sources.json`).
- Environment/timeline note: the workspace clock reads 2026-11-03, and the public pages I fetched presented 2025 and 2026 editions (Lazard LCOE+ June 2025 and a 2026 edition landing page; DEA catalogue updated May 2025). I report the document vintages I actually saw and do not reconcile them to the project timeline.
- Packages/gaps: B-01..B-06 only. Electricity-market, hydrogen and finance gaps touched in passing are flagged as crossed, not claimed.
- Peer findings seen before this pass: **none**. I did not open `Tier1/public/research_1103/**` or any other `firstpass/` package.

---

## 2. Findings and recommended interface (by gap)

### B-01 Suitable commercial systems, power/energy sizes, module grids, two-hour compatibility

**Verified product (primary, manufacturer datasheet).** Tesla *Megapack 2 XL Datasheet*, Rev. 1.5.1, 10 February 2023:

| Configuration | AC power per unit | Energy per unit | Duration |
|---|---|---|---|
| 2-hour | 1927 kW | 3854 kWh | 2.00 h |
| 4-hour | 979 kW | 3916 kWh | 4.00 h |

- Duration is explicitly **configurable**; 2-hour and 4-hour are the standard configurations.
- Inverter power per unit: 2-hour max 2400 kVA; **AC output scalable from 400 kVA minimum in increments of 50 kVA**.
- Nominal energy is specified at 25 C; weight 38,100 kg max; IP66/NEMA 3R main enclosure.

**Reference commercial project size (industry benchmark).** Lazard *LCOE+ v10.0*, June 2025, p.43, models utility-scale standalone storage at **100 MW / 200 MWh (2.0 h)** and 100 MW / 400 MWh (4.0 h), with 90% depth of discharge, **1 cycle/day, 350 operating days/year, 20-year project life**, giving 63,000 MWh/year and 1,260,000 MWh lifetime output for the 2-hour case.

**Modelling consequence.** Energy capacity `E` (MWh) is the natural decision variable and power is `P = E/2` for the brief's 2-hour requirement. Because a real unit is 3.854 MWh / 1.927 MW, the honest modelling choices are:
- (a) continuous `E >= 0` in the optimisation, then report the nearest integer number of 1.927 MW modules and the resulting residual; or
- (b) integer modules `n >= 0` with `E = 3.854 n`, `P = 1.927 n`.

Recommendation: use (a) for the baseline LP and (b) as a robustness check, because 3.854 MWh granularity is coarse relative to a plausible optimum and an integer-only model risks reporting "zero battery" purely as a granularity artefact.

**Known gap.** I verified **one** product datasheet in full (Tesla). Other commercial systems (e.g. CATL TENER, Sungrow PowerTitan, Fluence Gridstack, Wartsila GridSolv) were not opened, so this is a *catalogue with one verified entry*, not an exhaustive market survey. Their module sizes are likely in the 2.5-6.3 MWh per container range at 2-4 h, but I did not verify that and do not assert it.

### B-02 Installed CAPEX boundary, balance of plant, connection, currency and price year

**The DEA reconstruction (this is the answer to the explicit reproducibility question).**

Source: DEA *Technology Data for Energy Storage*, chapter 180 "Lithium-Ion Batteries for Grid-scale Storage" (chapter updated May 2025 per the revision table, p.3). The catalogue reports costs in **real 2020 EUR, excluding VAT**, on an **EPC / overnight installed-cost** basis expressed as **MEUR per MWh of storage capacity**, split into cost-of-energy (MEUR/MWh), cost-of-capacity (MEUR/MW) and other project costs. Shallow grid connection is included; deep network reinforcement, land rent, owners' predevelopment costs, interest during construction and decommissioning are excluded; **no economy-of-scale rule is applied**, so values are valid only near the typical capacity.

Table 10 (p.181), 2025 values, real 2020 EUR:

| Element | 2025 cost | Unit | Learning rate |
|---|---|---|---|
| Container, TMS and FSS | 0.081 | MEUR2020/MWh | 10% |
| Labour and installation | 0.010 | MEUR2020/MWh | 5% |
| PCS (incl. DC-DC converter) | 0.069 | MEUR2020/MW | 10% |
| BOS (foundation, wiring, EMS, switchgear...) | 0.037 | MEUR2020/MWh | 7% |
| Grid connection (transformer, metering, breakers) | 0.017 | MEUR2020/MW | 0% |
| EPC | 10% of all other costs | - | 0% |

Table 8 (p.180), 2025: projected **cell cost 0.077 MEUR2020/MWh** and **pack cost 0.023 MEUR2020/MWh**.

Reconstruction for a **2-hour** system (1 MW per 2 MWh, so power costs divide by 2):

```
energy-side per MWh : 0.077 (cell) + 0.023 (pack) + 0.081 (container/TMS/FSS)
                      + 0.010 (labour) + 0.037 (BOS)                    = 0.228
power-side per MWh  : (0.069 PCS + 0.017 grid) / 2 h                   = 0.043
subtotal                                                               = 0.271
EPC 10% of others   : 0.10 x 0.271                                     = 0.0271
TOTAL installed     :                                                   = 0.298 MEUR2020/MWh
```

**Answer: EUR 0.298 m(2020)/MWh installed, versus the brief's EUR 0.288 m/MWh - a +3.5% difference. Reproducible.**

Sensitivity of that reconstruction: using 2023 rather than 2025 cell+pack (0.084 + 0.025 = 0.109, Table 8) and holding the other elements at 2025 gives about **0.308 MEUR2020/MWh** (machine-checked). So the DEA family of estimates around the brief's value is roughly **0.29-0.31 m(2020)/MWh** for a 2-hour system.

**Independent cross-check (different publisher, different method).** Lazard LCOE+ v10.0 (June 2025), p.43, utility-scale standalone **100 MW / 200 MWh (2.0 h)**, in **USD**:

- Initial Capital Cost (DC): **$113-244/kWh**
- Initial Capital Cost (AC): **$26-70/kW** -> at 2 h this is **$13-35/kWh**
- EPC costs: **$29-122/kWh**
- Sum of the three: **$155-401/kWh**
- Reported "Total Initial Installed Cost": **$34-88 m** for 200 MWh -> **$170-440/kWh** (Lazard notes 10% overbuild)

So Lazard's fully installed 2-hour range is about **$0.17-0.44 m/kWh**, which brackets the DEA/brief value. I did not convert this to EUR because I have no verified 2025 EUR/USD rate in this pass; at an indicative 1.08 USD/EUR it would be roughly EUR 0.16-0.41 m/MWh. **The conversion rate is an unresolved input, not a finding.**

**Scope warning to carry into the model.** The brief's 0.288 and the DEA 0.298 are *installed, 2-hour, EPC-inclusive, shallow-connection-only* figures at a specific price year. Lazard's US data implies materially higher costs at the top of its range (interconnection, permitting, EPC premium). Charging 0.288 as a flat EUR/MWh for a small Scottish scheme is defensible for the coursework but is likely **optimistic** for a first-of-a-kind sub-10 MW project, where fixed BOP and connection costs dominate.

### B-03 Charge/discharge limits, efficiency, SOC window, standby losses

**Round-trip efficiency (RTE) - three independent sources, different bases:**

| Source | Value | Basis |
|---|---|---|
| Brief (written) | 90% | assumption for the model |
| Tesla Megapack 2 XL, 2-hour | **92.0%** | "full-depth cycle including all power conversion and thermal system losses, at 25 C" |
| Tesla Megapack 2 XL, 4-hour | 93.7% | same basis |
| Lazard 2025, utility 2-hour | **87-91%** | "Efficiency of Storage Technology %" |
| Lazard 2025, utility 4-hour | 86-92% | same |
| PNNL ESGC 2022, Table 4.4, p.22 | DC-DC 89.55% (2021) / 91.63% (2030); AC-AC at inverter 86.00/88.00; **AC-AC at transformer 82.59/84.52** | transformer-level AC-AC is the value PNNL uses in its summary table and LCOS |

The brief's 90% sitting between Lazard's 87-91% and Tesla's 92% is well supported. PNNL's transformer-level 82.6-84.5% is the conservative end and is the number to use if the team wants a "whole-plant AC" view rather than a "behind-the-meter at the inverter" view.

**Recommendation:** keep RTE = 0.90 as baseline, split symmetrically as `eta_charge = eta_discharge = sqrt(0.90) = 0.9487` (state this convention explicitly; a 50/50 split is a modelling choice, not a datasheet fact). Sensitivity: 0.83, 0.86, 0.92.

**Power limits.** `P = E/2` (MW) for a 2-hour system; simultaneous charge and discharge must be excluded (binary, or rely on the absence of a same-day price spread - see B-06 - and *verify* in the solution rather than assuming it).

**SOC window.** Brief: normal operation 20-80% of total capacity, i.e. **usable energy = 0.60 E**. This is an operating-window convention, not a datasheet value; Tesla publishes round-trip efficiency and warranty energy retention but the datasheet I read does not state a 20-80% operating band. Keep the brief's window as the baseline and label it a team assumption (per TC-09).

**Important interaction at daily resolution.** Usable energy 0.60 E at power 0.50 E gives only **1.2 hours** of full-power discharge. Within a day, the usable-energy cap therefore binds before the power cap: a daily model does not need a separate intraday power constraint to be feasible, but it also cannot represent one.

**Standby losses.** No standby/self-discharge figure was obtained. Tesla states thermal-system losses are inside the quoted RTE; PNNL's augmentation model treats capacity fade separately. Recommendation: **no explicit standby loss in the baseline**, disclosed, with a sensitivity at 0.5%/day of stored energy (which is material over multi-day shifting).

### B-04 Calendar/cycle life, degradation, warranty, replacement, residual value

- **Tesla warranty (datasheet):** "All-inclusive, equipment and energy retention", **15 years standard, extendable to 20 years**. So a 15-year baseline life is defensible and a 20-year life requires the extended warranty.
- **Lazard (2025, p.43):** project life **20 years**; extended warranty starting **year 3** costing **0.65%-1.50% of capital cost per year** (2-hour utility case); storage O&M **$3.0-8.2/kWh-year**.
- **PNNL ESGC 2022:** calendar life **16 years (LFP)**, **13 years (NMC)**; target plant life **20-25 years** achieved by augmentation, with cycling at **60% DOD** and augmentation to reach the target life. Cycle life to the halfway state-of-health point: **LFP 2,400 cycles, NMC 1,520 cycles at 80% average DOD** (Table 4.3, p.22). Fixed O&M **0.43% of direct capital cost** plus power-equipment refurbishment of **30% of power-equipment cost every 10 years**, which works out at about **$4.59/kW-year for a 10 MW / 4-hour LFP system**.
- **PNNL also reports** that warranties "typically limit users to one full 100% DOD-equivalent cycle per day".

**The arithmetic the team must confront.** One cycle/day for 20 years is **~7,000 cycles**, versus **2,400 LFP cycles** to 80% state of health at 80% DOD. A single purchase cannot serve 20 years of daily cycling without augmentation or replacement. Any model that charges 0.288 m/MWh once, then cycles the battery every day for 20 years with no degradation cost, is **understating lifecycle cost materially**.

**Recommended convention (with uncertainty):**
- Baseline (simple, defensible): single investment, **usable energy held constant at 0.60 E for the whole horizon**, horizon **15 years** (within the standard warranty), plus a **replacement/augmentation cash flow at year 10 equal to 30% of the power-electronic (PCS) cost**, per PNNL's refurbishment assumption. Because PCS is roughly 0.069 MEUR/MW = 0.035 MEUR/MWh at 2 h, this is about **0.010 m/MWh of energy capacity** discounted, which is small - the honest point is that it is *not zero*, not that it is large.
- Sensitivity A: 20-year horizon with the extended warranty and an augmentation at year 10 sized to restore nameplate (PNNL-style, expensive).
- Sensitivity B: capacity fade linear to **80% of nameplate by year 15** applied to the usable window (i.e. usable energy falls from 0.60 E to 0.48 E), no replacement.
- **Residual/disposal:** no reliable public figure obtained. Lazard and PNNL both stop at project life; DEA explicitly **excludes decommissioning** from investment cost. Recommendation: residual value **0** in the baseline and disclose that this is a modelling choice; do not invent a scrap or second-life credit.

### B-05 Price/parameter uncertainty and sensitivity ranges; bulk discounts

- **Cost uncertainty:** DEA 0.29-0.31 m(2020)/MWh (2 h) versus Lazard USD 0.17-0.44 m/kWh (2 h). Recommended sensitivity band on installed capex: **0.16 to 0.41 m/MWh** around a **0.29** baseline. This is a wide band and the band itself is the finding: the investment answer is likely to be capex-sensitive.
- **Efficiency:** 0.83-0.92 (see B-03).
- **O&M:** PNNL implies about **0.43% of capex per year** (approximately EUR 1.2/kWh-year at 0.29 m/MWh); Lazard implies **$3.0-8.2/kWh-year** for a 2-hour utility asset. These differ by a factor of about 3-6. This is a genuine conflict, not a rounding difference: PNNL's 0.43% is a bottom-up component estimate, Lazard's is a market all-in O&M including warranty and augmentation. **Recommendation: baseline EUR 3.0/kWh-year (low end of the Lazard range, above PNNL), sensitivity 1.2-8.0.** Flag as a conflict to be resolved in synthesis.
- **Bulk discounts / price grids:** I found **no** public, citable, quantity-discount schedule for grid BESS. DEA explicitly states it applies **no economy-of-scale rule** and that values are valid only near the reference capacity; Lazard's C&I (1 MW / 2 MWh) capital cost of $238-445/kWh versus utility (100 MW / 200 MWh) $113-244/kWh is the best available evidence of scale effects - roughly a **2x** penalty at 1 MW scale. Recommendation: do **not** model a discount curve. Instead implement a **step/scale sensitivity**: utility-scale price for E above some threshold (order 100 MWh), small-scale price (about 2x) below it, and state the threshold as an assumption. TC-08 permits bulk-discount mechanisms, but no defensible public schedule was obtained, so an invented curve would not be evidence.

### B-06 What daily data can honestly support for a two-hour asset

This is the most consequential gap and the one most likely to be mishandled.

**The structural problem.** All supplied series are daily. A two-hour battery earns most of its real-world arbitrage revenue *within* a day (charging in low-priced hours, discharging into the evening peak). Daily data contain **one price per day**, so:
- the model can only shift energy **between days**;
- same-day charge-and-discharge is **never profitable** at a single daily price (RTE < 1 loses energy at an unchanged price), so with daily prices the optimiser will avoid it *by construction* - which means the model is feasible without charge/discharge binaries, but the binaries (or an explicit check) should still be included/run to *prove* no simultaneous flow appears, especially under negative prices;
- the value the model attributes to storage is therefore **inter-day arbitrage plus avoided curtailment**, and the true intraday arbitrage value is **missing**. Any battery value reported from a daily model is a **lower bound** on arbitrage value in the real system, but an **upper bound** on what the 2-hour duration can physically capture per day, because a 2-hour asset cannot hold a multi-day position at full energy.

**What I recommend the team implement and disclose:**
1. **Energy balance per day**, with `charge_t <= P` and `discharge_t <= P` (P = 0.5 E), SOC in [0.20 E, 0.80 E] when the 20-80% window is applied, and `eta_ch * charge_t` / `discharge_t / eta_dis`.
2. **Throughput convention: at most one equivalent full cycle per day**, `discharge_t <= 0.60 E` (usable energy), citing the warranty practice PNNL reports ("one full 100% DOD-equivalent cycle per day") and Lazard's modelling assumption (1 cycle/day, 350 days/year). Sensitivity: 1.25 cycles/day, 0.5 cycles/day.
3. **Operating-days convention**: Lazard uses **350 days/year** of cycling. For a daily historical model with 2,422 observed days this is not directly applicable; instead **cap total annual cycles** at 350 in any annualised or extrapolated reporting, and disclose that the daily model can otherwise imply up to 365.
4. **No same-day charging and discharging** - enforce with binaries in a validation run, or verify ex post that no day has both flows above tolerance; report the maximum same-day throughput observed.
5. **Report throughput diagnostics** alongside profit: MWh charged, MWh discharged, equivalent full cycles, days with any activity, share of charged energy sourced from otherwise-unused generation. Without these, a "battery makes money" result cannot be interpreted.
6. **State the missing intraday value explicitly** in the report and in the recommendation. A daily model cannot establish "the full revenue potential of a two-hour asset" (this is also BL-04's warning). If the team wants an intraday claim, it needs an intraday price series, which the supplied data do not contain.

**A subtle trap to avoid.** With usable energy 0.60 E and power 0.50 E, a daily model lets the battery discharge its whole usable energy in one day at the daily average price. That is *not* a claim that a 2-hour battery can sell 1.2 hours of energy into the highest-priced hours of that day; it is a claim about a day-average. Phrase all results in those terms.

---

## 3. Conversions and checks

```
1. DEA 2-hour installed-cost reconstruction (Section B-02)
   0.077 + 0.023 + 0.081 + 0.010 + 0.037 = 0.228 MEUR2020/MWh   (energy-side)
   (0.069 + 0.017) / 2 = 0.043 MEUR2020/MWh                     (power-side, /2 h)
   0.228 + 0.043 = 0.271;  x 1.10 (EPC) = 0.2981 MEUR2020/MWh
   Brief: 0.288 -> difference (0.2981 - 0.288)/0.288 = +3.5%

2. Brief unit check
   EUR 0.288 million per MWh = EUR 288,000/MWh = EUR 288/kWh. Consistent with the
   brief's "EUR 0.288m per MWh of storage capacity".

3. Lazard 2-hour total installed, USD
   DC 113-244 + AC (26-70)/2 = 13-35 + EPC 29-122  = 155-401 $/kWh
   Reported total for 100 MW/200 MWh: $34-88 m / 200,000 kWh = $170-440/kWh

4. Tesla 2-hour duration check
   3854 kWh / 1927 kW = 2.000 h. Confirms a true 2-hour product.

5. Usable-energy window
   0.60 x E MWh usable at P = 0.5 E MW -> 0.60/0.50 = 1.2 h of full-power discharge.

6. Cycle-count check
   1 cycle/day x 365 = 365/yr; Lazard uses 350/yr.
   20 years x 350 = 7,000 cycles vs PNNL LFP 2,400 cycles to 80% SoH (80% DOD)
   -> augmentation or replacement unavoidable for a 20-year daily-cycled asset.

7. Efficiency split
   sqrt(0.90) = 0.94868 -> eta_ch = eta_dis = 0.9487 (convention, not a datasheet value).
```

**Checks that passed:** Tesla duration 2.000 h exact; Lazard 200 MWh x 90% DoD x 350 d = 63,000 MWh/yr matching its stated annual output; DEA element sum reproduces the brief within 3.5%.

**Checks I could not complete:** EUR/USD conversion (no verified rate obtained); DEA's Figure 7 (projected capex of the 1.5 MW / 3 MWh system) is a chart, so I reconstructed from its component tables instead of reading the total off the figure; DEA's Li-ion round-trip efficiency row was not read (the chapter's efficiency values were outside the pages I opened).

---

## 4. Proposed decisions

**Supports the baseline:**
- BL-08's "two-hour battery, 90% roundtrip, 20-80% SOC" is well supported by Lazard (87-91% at 2 h) and Tesla (92.0% at 2 h). No change needed; label the 90% and the SOC window as assumptions.
- BL-08's battery cost reference (EUR 0.288 m/MWh) is reproducible from the DEA catalogue at 2020 price level on a full installed, EPC-inclusive, 2-hour basis. Keep it, and state its scope.

**Should change (with reasons):**
- **B-04 / M-09:** the baseline must not combine a 20-year horizon with unconstrained daily cycling and no degradation or replacement cost. Recommend the 15-year + year-10 PCS refurbishment convention in B-04, or an explicit augmentation module. Reason: 7,000 cycle-equivalents against a 2,400-cycle LFP rating.
- **B-05 / M-05:** do **not** adopt a bulk-discount curve. No public schedule was obtained; DEA explicitly applies no scale rule. Use a two-step scale sensitivity instead, and mark the threshold as arbitrary.
- **B-06 / M-07:** the run manifest should record the one-cycle-per-day throughput convention, the 350-day annualisation cap, the symmetric efficiency split, and the statement that intraday value is unobservable.

**Minimal baseline parameter set that can be instantiated now:** see `parameters.json` ids `B-01-01`, `B-02-01`, `B-03-01`, `B-03-02`, `B-03-03`, `B-04-01`, `B-05-01`, `B-06-01`.

**Unknowns and fallbacks:**
- DEA Li-ion RTE: fallback = brief 0.90 (supported by Lazard and Tesla).
- Standby loss: fallback = 0 in baseline, 0.5%/day sensitivity.
- Residual/disposal value: fallback = 0, disclosed.
- Bulk-discount schedule: fallback = none, two-step scale sensitivity.
- Non-Tesla module grids: fallback = single-module grid from Tesla, disclosed as a one-entry catalogue.

**Optional extensions:** degradation-aware SOC (capacity fade), replacement optimisation, intraday dispatch with an external intraday price series, and a finance module applying a discount rate to the replacement cash flow. Each needs data not in the input bundle.

**Findings likely to change the investment recommendation:**
1. **CAPEX band 0.16-0.41 m/MWh** - a 2.5x spread; the "worth adding?" answer will likely flip inside this band.
2. **The 20-year-single-purchase trap** - adding replacement/augmentation cost raises lifecycle cost and can push marginal batteries to negative net benefit.
3. **Daily-resolution ceiling** - if intraday value is the main real-world battery revenue stream, a daily model systematically understates battery value; the team should not present a "battery is unattractive" conclusion as a market fact without this caveat.

---

## 5. Cross-validation

Not performed: this is a first pass and I did not read peer results. The internal cross-checks I *did* run (DEA against its own components; Lazard against its own totals; Tesla against its own power/energy ratio) are recorded in Section 3 and are self-consistency checks, not independent validation.

---

## 6. Handoff

- Files: `REPORT.md`, `parameters.json`, `sources.json`, `FIRST_PASS.md` in `Tier1/workspaces/mocry/cleveruser/firstpass/R2-battery/`.
- Suggested next action for the controller: (i) have a cross-reviewer independently reconstruct the DEA 0.298 figure; (ii) obtain a verified 2025 EUR/USD rate so the Lazard range can be expressed in EUR; (iii) add at least two more manufacturer datasheets to the module catalogue before publishing a "candidates" table.
- Blocker: none. Publication, commit and push are the controller's, not mine.
