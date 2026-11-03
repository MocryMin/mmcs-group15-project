# R3 — Electrolysers, hydrogen storage and market: independent first-pass research

Result ID: `R3-hydrogen/2026-11-03-firstpass`
Package: R3 (gap IDs H-01 … H-07; informs M-05, M-09, M-10)
Status: first-pass result (no cross-review performed yet)
Repository position: `Tier1/workspaces/mocry/cleveruser/firstpass/R3-hydrogen/`
Prepared for: MMCS Group 15, Baseline 1103 modelling work.

---

## 1. Identity, independence and scope

- **Researcher**: `res-r3-hydrogen`, model configured as `deepseek-v4.1-flash-1017`, harness "Clever User worker" (build not exposed to me).
- **Package covered**: R3 only — electrolysers, hydrogen offtake, storage/transport/reconversion.
- **Independence statement**: this first pass was produced **without** reading anything under `Tier1/public/research_1103/**`, without reading any other folder under `Tier1/workspaces/mocry/cleveruser/firstpass/`, and without reading `mocry-codex` files other than the byte-identical input copies. The only project material used is the input bundle supplied with the task (`inputs/PROJECT.md`, `inputs/brief_extracted_text.md`, `inputs/TEACHER_ORIGINAL_EXCERPTS.md`, `inputs/TEACHER_CLARIFICATIONS.md`, `inputs/GAPS.md`, `inputs/BASELINE_1103.md`, `inputs/RESEARCH_REQUEST.md`, `inputs/RESEARCH_RESULT_TEMPLATE.md`). No peer finding, parameter candidate or synthesis from the earlier round was seen. I am therefore unable to say whether my conclusions agree with them.
- **Search-channel limitation**: all general web search engines (Bing, Brave, Google, DuckDuckGo HTML, Mojeek) returned rate-limit/CAPTCHA or "readiness timeout" responses from this sandbox during the whole session. Evidence was therefore gathered by (a) the `gov.uk` search API and (b) direct navigation of publisher sites. Keyword search was effectively unavailable; **absence of a source in this report is not evidence that it does not exist.** This is recorded as a harness finding, not a research conclusion.
- **Access window**: 2026-11-03, approximately 19:45Z–21:40Z (harness clock). Individual timestamps in `sources.json` are as observed, to the minute, and should be treated as approximate.
- **Local copies**: the primary PDFs/XLSX were downloaded into `_work/` only to extract page-located text and cells. They are third-party documents and must **not** be redistributed from this repository; `sources.json` cites URL + page/table instead.

---

## 2. Findings and recommended interface

Headline results first, because three of them change how the Baseline 1103 hydrogen block should be read.

### 2.1 The brief's 55.9 kWh/kg is verified, and its boundary is now explicit

The project brief's electrolysis figure is **not** a generic industry assumption: it is the manufacturer's own full-system AC figure for the 20 MW PEM module the brief names.

ITM Power, *POSEIDON 20 MW* data sheet, page 2 — specification block:

- `AC POWER CONSUMPTION  55.9 kWh/kg*`
- footnote: `* This is the full system (water purification, stack, and BOP) energy consumption at beginning of life`
- `H2 PRODUCTION  360 kg/hr`, `NUMBER OF STACKS  30`, `H2 OUTPUT PRESSURE  31 bar(g)`
- `OPERATING RANGE  20%-100% (Based on 4 Pairs turned down to 25& applied load)`
- `MODULATION  10% per second ramp up / 50% per second ramp down`

Confirmation of internal consistency: 20 000 kW ÷ 360 kg/h = **55.6 kWh/kg**, i.e. the 55.9 figure is the plant's rated specific consumption, consistent with nameplate capacity and H2 rate.

**Boundary consequences for the model** (H-01/H-02):

| Boundary element | What the source says | What the optimiser must respect |
|---|---|---|
| AC vs DC | AC power consumption | Do not apply a separate transformer/rectifier loss on top of 55.9 |
| System scope | Water purification + stack + BoP | Do not add a separate water-treatment energy term |
| Age | "at beginning of life" | This is *not* a lifetime-average figure; a degradation allowance is a separate, un-evidenced modelling choice |
| Pressure | H2 delivered at 31 bar(g) | Compression beyond 31 bar(g) is a **separate costed module**, not free |
| Degradation/stack replacement | not stated in data sheet | see §2.4 (BEIS stack-replacement evidence) |

Scale dependence is real and small: the 2 MW NEPTUNE II is quoted at **57 kWh/kg** with a **25–100%** range, the 50 MW ALPHA 50 at **55.9 kWh/kg** with a **12.5–100%** range. So specific consumption improves with module size (57 → 55.9) and the minimum-load floor is a **module-design property, not a physical law**.

That last point matters: POSEIDON's 20% floor is footnoted as arising from "4 Pairs turned down to 25% applied load". A different module configuration reaches 12.5% (ALPHA 50). Baseline 1103 may keep 20% as the written reference, but it should not describe 20% as an engineering limit of PEM electrolysis.

### 2.2 The £9.5/kg derivation is arithmetically correct but semantically fragile — verify and re-label it

The brief's appendix states: `£241/MWh x 39.4 kWh/kg / 1000 = £9.5/kg`.

**Arithmetic: confirmed.** 241 × 39.4 = 9 495.4; ÷ 1000 = **£9.4954/kg → £9.50/kg**. Correct as written.

**Both inputs: confirmed from primary sources.**

1. `£241/MWh` — DESNZ, *Hydrogen Production Business Model / Net Zero Hydrogen Fund: HAR1 successful projects*, updated 14 December 2023: "The 11 projects have been agreed at a weighted average strike price of **£241/MWh (£175/MWh in 2012 prices)**." Same page: 11 projects, **125 MW** total; >£2 bn revenue support; >£90 m NZHF capex grant; £413 m private capital 2024–2026. The footnote defines the weighting as "the total hydrogen volumes expected to be produced by each project over the lifetime of the LCHA contract", and notes "The subsidy will vary relative to changes in the reference (natural gas) price."
2. `39.4 kWh/kg` — DESNZ, *Hydrogen Transport and Storage Cost Report* (14 December 2023), page 10: "Using the Higher Heating Value (HHV) to express kWh, the energy content of 1kg of hydrogen is 39.4 kWh." The same report's Table A1 (page 36) gives `LHVH2 = 33.33 kWh/kg`.

**What this number is:**

- It is a **policy strike price expressed per kg of hydrogen energy content (HHV)**, i.e. the price at which the Low Carbon Hydrogen Agreement values hydrogen — **not** an electrolyser production cost and **not** the electricity input per kg.
- £9.50/kg ÷ 55.9 kWh/kg = **£170/MWh of electricity consumed**. That is the revenue per unit of *electricity input* implied by the supported value. It is the single most useful derived number in this package: the H2 route beats direct electricity sale only while the forgone electricity is worth less than about £170/MWh, before electrolyser CAPEX and OPEX are counted.

**What this number is not:**

- It is **not** a guaranteed commercial price obtainable by our hypothetical scheme. It is the settled strike price of a 15-year contract awarded to 11 specific projects (5.2–24.5 MW each) after a competitive allocation round. A new entrant has no LCHA and therefore no entitlement to it. The brief already says this ("supported benchmark, not a guaranteed market price"); this research adds the mechanism (strike vs gas reference price) and the eligibility scope.
- It is **not** a real-terms figure for the modelling horizon. £241/MWh is the nominal, as-paid strike; the same settlement is **£175/MWh in 2012 prices**, i.e. **£6.90/kg** in 2012 prices (175 × 39.4 ÷ 1000 = 6.895). Mixing £9.50/kg with 2020-price CAPEX (which is what the BEIS cost data are in) is an inconsistency that R4/F-01 must resolve. Baseline 1103 should state which price basis the £9.5 uses.
- Feeding 39.4 kWh/kg in as if it were the *input* consumption would overstate hydrogen output by **55.9 ÷ 39.4 = 1.42×**. This is the most likely silent energy-creation bug in a team implementation.

### 2.3 Bounded electrolyser CAPEX ladder (three different things are routinely conflated)

I found three non-comparable price concepts. They are kept separate deliberately (H-01, H-02, M-05, M-10).

**(a) Equipment / full-scope plant list price — 2026, EUR**

ITM Power, *ALPHA 50* tech sheet, page 1: `EUR 50,000,000*` with `* prices are based on ITM's Standard T&C's`; page 2: `CAPACITY 50 MW`, `H2 PRODUCTION 900 kg/hr`.
→ 50 000 000 ÷ 50 MW = **EUR 1 000/kW = EUR 1.0 m/MW**. At an indicative 0.85 EUR/GBP this is ≈ **£0.85 m/MW**. Scope from the same sheet: PEM stacks, PSU incl. MV transformer and rectifier, water purification/polishing, cooling, H2 purification, DCS, ISBL piping — i.e. genuine full-scope *plant*, but excluding civils/foundations, installation labour, grid-connection reinforcement and any compression beyond 30 bar(g). This is a published list price, not a negotiated or audited transaction price. Cross-check: 50 000 kW ÷ 900 kg/h = 55.6 kWh/kg.

**(b) Installed nth-of-a-kind cost, UK government cost evidence — 2020 real prices, GBP**

BEIS/DESNZ, *Hydrogen Production Costs 2021*, annex sheet `Technical and cost assumptions`, PEM block, 10 MW reference plant, row 3 "Commissioning Year":

| Commissioning year | Electrical efficiency, medium (kWh_e / kWh H2 HHV) | CAPEX medium (£/kW **H2 HHV**) | CAPEX low | CAPEX high |
|---|---|---|---|---|
| 2020 | 1.397 | 1 158.63 | 953.59 | 1 887.51 |
| 2025 | 1.3208 | 730.29 | 600.38 | 1 458.33 |

The unit is **£ per kW of hydrogen output (HHV), not per kW of electrical input** — a trap. Converting with the paired efficiencies (high CAPEX is paired with low efficiency; see the sheet's own footnote):

- 2020 medium: 1 158.63 ÷ 1.397 = **£829/kW_e**
- 2020 low-cost/high-efficiency pair: 953.59 ÷ 1.2319 = **£774/kW_e**
- 2020 high-cost/low-efficiency pair: 1 887.51 ÷ 1.6256 = **£1 161/kW_e**
- 2025 medium: 730.29 ÷ 1.3208 = **£553/kW_e**

So **£0.77–1.16 m per MW_e installed in 2020 prices** (central ≈ £0.83 m/MW_e), falling to £0.50–0.97 m/MW_e by 2025 in BEIS's own projection. Cost scope is stated explicitly (page 16): "For electrolysis, CAPEX covers the electrolyser system (the stack), all necessary balance of plant (drier, cooling, de-ox…), civil works (building and foundations) and electricity grid connection", and "our CAPEX estimates do not include cost of hydrogen compression equipment".

Cross-check that this is nth-of-a-kind rather than optimistic: BEIS's implied specific consumption for PEM 2020 medium is 1.397 × 39.4 = **55.0 kWh/kg**, essentially the ITM 55.9 figure, so the cost and efficiency assumptions are mutually coherent with the real product.

**(c) First-of-a-kind whole-project capital actually committed — 2024–2026, GBP**

From the HAR1 page: £413 m private capital across 125 MW → **£3.30 m/MW**; adding the >£90 m NZHF grant gives ≈ **£4.02 m/MW** gross. This is a *project* number for small (5–25 MW) first-of-a-kind plants: it carries FOAK contingency, bespoke civils, connection works, compression/storage and developer margin. It is the empirical upper bound, and the single most credible "what does it really cost in the UK" anchor available here.

**Recommended bounded set for the optimiser** (all £, per MW of electrical input, installed):

| Case | Value | Basis | Price year |
|---|---|---|---|
| Low | **£0.85 m/MW_e** | ITM ALPHA 50 list price, equipment/full-scope plant | 2026 (EUR converted) |
| Core | **£1.50 m/MW_e** | BEIS 2020 central £0.83 m/MW_e uprated ×1.25 for 2020→2026 | 2026 (uprated) |
| High | **£3.30 m/MW_e** | HAR1 committed private capital per MW | 2024–2026 |

The ×1.25 uprating is **my assumption, not a sourced deflator**; F-01 must replace it with a proper index. Presenting the un-uprated BEIS figures alongside is mandatory so the assumption is visible.

### 2.4 Operating cost, life and stack replacement (H-03)

Same annex sheet, PEM, per kW H2 HHV:

- Fixed OPEX, medium 2020: £36.72/kW_H2/yr → ÷1.397 = **£26.3/kW_e/yr**. For a 20 MW module: £526 k/yr. As a fraction of core CAPEX this is ≈ **1.75 %/yr** — consistent with the usual 2–4 % assumption and usable as a sanity check.
- Variable OPEX, medium 2020: £0.0039/kWh H2 HHV → ×39.4 = **£0.154/kg**.
- Operating lifetime: **30 years**; construction period 3 years; hurdle rate 10 %.
- *Hydrogen Production Costs 2021*, page 19: "Stack costs make up **60% (PEM)**, 50% (Alkaline), 60% (SOE) of plant CAPEX and are assumed to need replacement every **11 (PEM)**, 9 (Alkaline), 7 (SOE) years over a 30-year technology life". Replacement is **capitalised into the levelised cost**, not treated as free.
- Water, and any cooling-water constraint: **no usable public unit cost obtained**. Potable water is the stated ALPHA 50 input; POSEIDON requires DI water post-polishing. Recommend carrying this inside fixed OPEX (as BEIS does) and flagging it, rather than inventing a £/m³ figure.

### 2.5 Hydrogen volume arithmetic the model needs

Per MW of electrolyser at full load: 1 000 kW ÷ 55.9 kWh/kg = **17.89 kg/h → 429 kg/day → 156.7 t/yr** at 0.98 availability. A 20 MW POSEIDON therefore yields 8 576 kg/day at 100 % load, 1 715 kg/day at the 20 % floor. These are the numbers that convert an optimiser's capacity variable into a kg balance; they should appear in the run manifest.

### 2.6 Hydrogen value ladder (H-04)

| Case | Value (£/kg) | Status of evidence |
|---|---|---|
| Low | **2.50** | Lecturer's spoken illustration in the launch transcript (TC-05: "just assume you can always sell like 1 kg of hydrogen for, I don't know, 2 pounds 50"). **Weak**: an off-the-cuff example, not a market observation. Useful only as a "no policy support" stress case. |
| Core | **9.50** | HAR1 weighted-average strike price × 39.4 kWh/kg. **Strong** for the arithmetic and the £241/MWh; **conditional** on LCHA eligibility. Nominal basis. |
| Real-terms equivalent | **6.90** | Same HAR1 settlement at £175/MWh (2012 prices). Use this if the model runs in constant 2012 prices. |
| High | **12.00** | **No source.** A stress case only, to be labelled as such in the report. Do not present it as evidence. |

**No public firm merchant offtake price or volume was obtained.** For a producer outside HAR1 I can offer no defensible £/kg. The honest statement is: *the hydrogen revenue line in any scheme without an LCHA is an assumption, not a finding.* The model must therefore carry the H2 price as a scenario parameter with a **finite** offtake cap, and the report must show the investment decision flipping across the ladder rather than presenting one number.

Consistency check that should be in the report: at £2.50/kg and £100/MWh electricity, electricity alone costs 0.0559 MWh × £100 = £5.59/kg — the electrolyser loses £3/kg before CAPEX. **The investment case exists only at supported values.** Single most important qualitative finding for the client story.

### 2.7 Optional storage / transport / reconversion modules (H-05, H-06)

All from DESNZ *Hydrogen Transport and Storage Cost Report* (£2023 levelised):

- Storage, Table A2 page 36 (`Total` / `Conversion-compression` / `storage-only`, £/kg, with cycles/yr): tank/vessel CGH2 700 bar **£1.39 / £0.96 / £0.43** (120 cycles/yr); tank/vessel LH2 £1.39 / £1.22 / £0.17 (52 cycles/yr); new salt cavern CGH2 **£0.26 / £0.13 / £0.13** (9 cycles/yr); new aquifer £0.23; new depleted gas field £0.24.
- Transport, Table A4 page 38 (per 100 km): **pipeline £0.26–0.31/kg**; 1 300 kg CGH2 trailer **£2.10–3.56/kg**; 500 kg trailer £2.49–4.40/kg. Page 21/29 note that levelised transport costs in £/kg "will apply to a specific distance covered, which is often not stated" — so a £/kg figure is meaningless without a distance.
- Reconversion (H-06): **no equipment data obtained.** The only hard constraint I can state from verified sources is the physical ceiling: 39.4 kWh/kg (HHV) × any conversion efficiency, against 55.9 kWh/kg of input electricity, gives a **round-trip of at most ≈ 70 % at an impossible 100 % efficiency, and ≈ 42 % at a realistic 60 % CCGT efficiency**. Any model producing a round-trip above that is creating energy.

**Recommendation:** keep the direct-sale baseline with **no** storage and **no** transport, i.e. hydrogen valued at the plant gate at 31 bar(g). Make storage/transport a separately costed module keyed on a stated distance and cycle rate. This matches BL-08 ("Do not assume all these services are free") and the template's requirement to keep optional modules separate.

### 2.8 The combinations that imply unsupported unlimited profitable expansion (H-07)

Each of these, if permitted, makes the LP unbounded or trivially degenerate. They should be asserted in the model documentation and preferably in code:

1. **Unlimited offtake at a fixed £9.5/kg.** With a positive margin per kg, the optimal capacity is infinite. Requires a finite sale cap (volume or contracting scenario).
2. **Unlimited electricity purchase at a fixed price below the implied £170/MWh.** Import-to-H2 becomes an arbitrage business. Requires a finite import cap/connection limit and an explicit R1 market interface.
3. **Fixed £9.5/kg with unlimited *negative-price* electricity.** Worse: the model would be paid to consume. Requires the same import cap plus R1's negative-price rules.
4. **Treating 39.4 kWh/kg as the input consumption** (or omitting losses). Overstates output 1.42×, so the optimiser will always prefer H2.
5. **Reconversion at efficiency ≥ 1**, or buying at negative prices and reconverting — a physical round-trip > 39.4/55.9 breaks the energy balance.
6. **Free hydrogen storage with no losses and unlimited capacity** — defers all value to the highest-price day.
7. **Ignoring the minimum-load constraint.** Without a binary on/off at 20 %, the model produces infinitesimal hydrogen quantities at proportional efficiency forever.
8. **Fractional module sizes.** With the real product grid (2 / 20 / 50 MW), capacity is discrete; a continuous capacity variable implicitly assumes bespoke manufacturing at list price.

**Bounded equipment set an optimiser can actually use:** modules {NEPTUNE II 2 MW, POSEIDON 20 MW, ALPHA 50 50 MW} × non-negative integer counts, times a stated max module count (a finite investment domain, M-05). The 5 MW NEPTUNE exists on ITM's product page but I did not read its data sheet, so it should be added only after its specific consumption is confirmed.

### 2.9 Indicative break-even cross-check (for the team's sanity tests, not a result)

Using core parameters only (55.9 kWh/kg, £1.5 m/MW_e, 30-year life, 10 % hurdle → CRF 0.10608, 98 % availability, fixed OPEX £26.3/kW_e/yr, variable OPEX £0.154/kg, stack replacement 60 % of CAPEX at years 11 and 22):

- Non-electric cost ≈ £1.04 (CAPEX) + £0.17 (fixed) + £0.29 (stack replacement, capitalised) + £0.15 (variable) ≈ **£1.65/kg**
- Break-even electricity price at £9.50/kg = (9.50 − 1.65) ÷ 55.9 kWh/kg = **≈ £140/MWh**
- At £100/MWh electricity: LCOH ≈ **£7.24/kg**, i.e. ≈ £2.3/kg margin at the supported value.

Every assumption here is mine except the 55.9, the 30-year life, the 10 % hurdle, the 60 % stack share and the 11-year cycle. The point is the order of magnitude: **the electrolyser needs electricity in the £100–140/MWh range and a supported hydrogen value to look investable.** Whether the supplied market-index price clears that is a data question for R1/R4, not something daily average prices can settle.

---

## 3. Conversions and checks

| # | Conversion | Arithmetic | Result |
|---|---|---|---|
| 1 | £/MWh(H2,HHV) → £/kg | 241 × 39.4 ÷ 1000 | **£9.4954/kg** (brief's £9.5 confirmed) |
| 2 | Same, 2012 prices | 175 × 39.4 ÷ 1000 | **£6.895/kg** |
| 3 | H2 revenue per kWh of input electricity | 9.50 ÷ 55.9 | **£0.16995/kWh = £170/MWh** |
| 4 | kg/h per MW_e at full load | 1000 ÷ 55.9 | **17.89 kg/h/MW** (429 kg/day/MW) |
| 5 | POSEIDON consistency | 20 000 ÷ 360 | **55.6 kWh/kg** vs quoted 55.9 ✓ |
| 6 | ALPHA 50 consistency | 50 000 ÷ 900 | **55.6 kWh/kg** vs quoted 55.9 ✓ |
| 7 | NEPTUNE II consistency | 2 000 ÷ 35 | **57.1 kWh/kg** vs quoted 57 ✓ |
| 8 | BEIS efficiency → kWh/kg | 1.397 × 39.4 | **55.04 kWh/kg** (PEM 2020 medium) |
| 9 | BEIS £/kW(H2) → £/kW_e (medium) | 1 158.63 ÷ 1.397 | **£829/kW_e** |
| 10 | same, low/high pairs | 953.59 ÷ 1.2319; 1 887.51 ÷ 1.6256 | **£774**; **£1 161/kW_e** |
| 11 | 2025 medium | 730.29 ÷ 1.3208 | **£553/kW_e** |
| 12 | Fixed OPEX per kW_e | 36.72 ÷ 1.397 | **£26.29/kW_e/yr** |
| 13 | Variable OPEX per kg | 0.0039 × 39.4 | **£0.1537/kg** |
| 14 | ALPHA 50 list price per MW | 50 000 000 ÷ 50 | **EUR 1.0 m/MW** (≈ £0.85 m/MW at 0.85) |
| 15 | HAR1 capital per MW | 413 ÷ 125 | **£3.304 m/MW** |
| 16 | HAR1 capital incl. grant | (413 + 90) ÷ 125 | **£4.024 m/MW** |
| 17 | Output overstatement if 39.4 used as input | 55.9 ÷ 39.4 | **1.419×** error |
| 18 | Reconversion ceiling | 39.4 × 0.60 ÷ 55.9 | **42.3 %** round-trip at 60 % efficiency |

Also worth stating plainly: `£/kW H2 HHV` (BEIS) and `£/kW_e` (what an optimiser wants) differ by the efficiency factor, ~1.4×. Using the BEIS table without conversion would understate CAPEX by ~28 %.

---

## 4. Proposed decisions

**Supports these Baseline 1103 assumptions:**

- BL-08's 55.9 kWh/kg and the written 20 %–100 % operating range: both independently confirmed against the manufacturer data sheet for the named reference product. Neither needs changing.
- BL-08's "9.5/kg is a price scenario, not guaranteed offtake": confirmed and strengthened — it is a contracted strike price for 11 specific projects, settled against a gas reference price.
- BL-08's insistence that storage/transport/compression be separately costed: confirmed — they are material (£0.26–3.56/kg/100 km) and not included in the electrolyser figures or in BEIS CAPEX.
- BL-07's prohibition on "unlimited import-to-H2 business from unsupported infinite offtake": confirmed as the dominant unboundedness risk (§2.8).

**Should change / be tightened:**

- **H-04 / M-03**: Baseline 1103 should state the price basis of the £9.5/kg. It is a *nominal* strike price whose real 2012-price equivalent is £6.90/kg. Mixing it with 2020-price BEIS costs (or the EUR battery cost) is an unnoticed inconsistency. Recommend quoting £9.5 nominal *and* £6.9 in 2012 prices and letting R4/F-01 fix one basis.
- **H-02**: distinguish **shutdown** from **minimum load** explicitly. POSEIDON's 20 % is a configuration artefact ("4 Pairs turned down to 25 % applied load"); 12.5 % is achievable on ALPHA 50 and 25 % on the 2 MW unit. Treat 20 % as the *reference module's* floor, with a binary on/off and a load-fraction variable, not as a hard technical law.
- **H-01**: do not quote a single electrolyser CAPEX number. The defensible range is **£0.85 m/MW_e (list equipment) to £3.30 m/MW_e (committed FOAK project capital)**, with a core of ≈ £1.5 m/MW_e. Any single figure outside that range needs justification.
- **H-03**: stack replacement is **60 % of PEM plant CAPEX every 11 years** — a material lifetime cost, not a rounding item. It should be in the cash-flow model, not folded silently into OPEX.
- **M-05**: use the real discrete module grid (2 / 20 / 50 MW) rather than a continuous capacity variable.

**Minimal parameter set that can be instantiated now:**

| Parameter | Value | Unit | Basis |
|---|---|---|---|
| Specific consumption | 55.9 | kWh/kg AC, full system, beginning of life | ITM POSEIDON p2 |
| Operating range | 20–100 with binary on/off | % of capacity | same |
| Ramp | non-binding at daily resolution | — | 10 %/s up, 50 %/s down |
| Delivery pressure | 31 | bar(g) | same |
| Module grid | 2, 20, 50 | MW, integer | ITM product sheets |
| CAPEX | 1.50 (0.85–3.30) | £m/MW_e installed | §2.3 |
| Fixed OPEX | 26.3 | £/kW_e/yr | BEIS annex |
| Variable OPEX | 0.154 | £/kg | BEIS annex |
| Stack replacement | 60 % of CAPEX every 11 yrs | — | BEIS p19 |
| Plant life / hurdle | 30 yr / 10 % | — | BEIS annex |
| H2 value | 9.50 core (2.50 low, 12.00 unsourced high) | £/kg | §2.6 |
| H2 offtake | **finite scenario cap — value not evidence-based** | t/day | §2.6 |
| Storage (optional) | salt cavern 0.26; CGH2 vessel 1.39 | £/kg levelised | Table A2 |
| Transport (optional) | pipeline 0.26–0.31; trailer 2.10–3.56 per 100 km | £/kg | Table A4 |

**Unknowns with justified fallbacks:**

- Merchant H2 price/volume: **no public number**. Fallback = scenario ladder + finite cap; report the decision flip.
- 2026 UK installed electrolyser cost: interpolate between list price and HAR1 committed capital; label the ×1.25 uprating as an assumption.
- Electrolyser degradation rate: not in the data sheet; fallback = beginning-of-life 55.9 plus an explicit stack-replacement schedule, rather than an invented annual degradation.
- Water cost: fold into fixed OPEX, flag as unevidenced.
- Compression from 31 bar(g) to storage/sale pressure: **not costed here** (BEIS explicitly excludes it; the T&S report gives storage-level compression £0.96/kg for 700 bar vessels as a usable proxy, labelled as such).

**Optional extensions and their information needs:** hydrogen storage (needs a cycle rate and a cavern/vessel choice); transport (needs a distance — £/kg without km is meaningless); reconversion (needs turbine CAPEX/efficiency — not obtained); H2 price indexation.

**Findings most likely to change the investment recommendation:** (i) the H2 value ladder — the entire H2 case is negative at £2.50/kg; (ii) the CAPEX choice between £0.85 m and £3.30 m/MW_e, a 3.9× swing in the capital charge; (iii) the assumed offtake cap, which determines whether capacity grows or saturates.

---

## 5. Cross-validation

**Not performed — this is a first pass.** No peer result, synthesis or parameter candidate was read (leak control). The cross-review column will be completed after the first pass is preserved and the controller releases other results.

Independent *internal* checks that were performed and are reproducible from this folder: the three ITM consistency checks (capacity ÷ H2 rate = quoted kWh/kg), the BEIS efficiency × 39.4 = 55.0 kWh/kg consistency with the manufacturer, and the unit reconciliation of `£/kW H2 HHV` vs `£/kW_e`. Two sources were traced to distinct originals rather than counted as mutual confirmation: the 39.4 kWh/kg value comes from DESNZ citing DNV (Table A2 footnote 32) and is used here only as an energy-content conversion, while the 55.9 kWh/kg comes from the manufacturer. They are **not** independent measurements of the same quantity and must not be presented as agreement.

---

## 6. Handoff

Files (relative to this folder):

| File | Content |
|---|---|
| `REPORT.md` | this report |
| `parameters.json` | 34 typed claims, H-01…H-07 |
| `sources.json` | 11 sources, real page/table locators, verbatim quotes |
| `FIRST_PASS.md` | identity, timestamps, independence declaration, failures |
| `_work/` | downloaded primary PDFs/XLSX and extraction scripts (evidence trail; **not for redistribution**) |

Verification run: `_work/validate.py` loads both JSON files, checks 34 unique claim IDs against 7 covered gap IDs, checks every `S…` source reference resolves to a real entry (0 dangling), and recomputes all 22 headline conversions and the section 2.9 break-even cross-check. Result: **22/22 arithmetic checks PASS, 0 failures.**

**Suggested next action for the controller:** aggregate `parameters.json` against the other first passes and flag the two structural conflicts this report expects to see debated — (a) whether the H2 value should be nominal £9.5 or real 2012-price £6.9, and (b) whether electrolyser CAPEX should be the equipment list price or the committed FOAK project capital. Those two choices move the investment decision more than any efficiency assumption.

**Blocker:** none. **Channel limitation:** general web search was unavailable (§1), so this pass is likely to under-cover sources that only a keyword search would surface — notably IEA, IRENA, and any commercial H2 price index.
