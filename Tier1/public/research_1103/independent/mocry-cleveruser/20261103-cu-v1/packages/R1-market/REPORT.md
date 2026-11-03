# R1 — Electricity markets and trading (independent first pass)

Result ID: `R1-market/firstpass-2026-11-03`
Package: R1 (gap IDs E-01..E-07; informs M-01, M-03, M-04)
Author identity: CU Builder researcher `res-r1-market`; model `deepseek-v4.1-flash-1017`; harness = Clever User worker (build/version not exposed to me).
Session: single session on 2026-11-03. The tool environment does not expose a clock; the only externally observed
timestamp in this session was `2026-11-03T20:09:36Z` (returned inside a search-engine block page). All access times
below are therefore given as "2026-11-03 (UTC), evening session", not as per-page exact times.
Status: first pass (not a synthesis, not a cross-review).

## 1. Independence and scope

**Independence statement.** I did not open, list or read anything under `Tier1/public/research_1103/`, any other
folder under `Tier1/workspaces/mocry/cleveruser/firstpass/` (the only other folder visible to me, `R2-battery/`, was
never opened — I saw its two `_scratch` filenames in a directory listing only), or any `mocry-codex` working file.
My only project inputs were the files inside `Tier1/workspaces/mocry/cleveruser/inputs/` plus the instruction files
handed to me (`RESEARCH_BRIEF.md`, and the task text). No peer finding, synthesis or parameter candidate informed
this pass. I did not browse the repository for context.

**Scope discipline.** This is a market/trading pass, not an equipment or finance pass. Battery and electrolyser
parameters are referenced only where the trading interface needs them (round-trip efficiency for the arbitrage
threshold; electrolyser conversion for the H2 outlet price basis). Currency/price-year and discounting conventions
belong to R4 (F-01/F-02) and are flagged, not decided, here.

**Crossing findings.** Two observations genuinely belong to R4's D-01/D-02 but were unavoidable while characterising
the price file, so they are reported here with an explicit "R4 owns this" flag: (a) the exact arithmetic identity
between the two price columns, and (b) the undocumented daily aggregation rule and the date intersection size.

## 2. What the supplied price series is, and what it is not (E-01)

### 2.1 Identity of the series

The file is named `daily_market_index_price.csv`, and "Market Index" is a defined BSC term. Elexon's glossary states
that Market Index Data "reflects the price of wholesale electricity in Great Britain in the short term markets", and
that "The Market Price (the volume weighed average Market Index Price) is used to derive the Reverse Price (SBP or
SSP)". Elexon's imbalance-pricing page adds that "Market Index Data (MID) is used in the calculation of the Market
Index Price for each Settlement Period, and reflects the price of wholesale electricity in the short-term market."

So the closest real-world object is the **Market Index Price (MIP)**: a half-hourly, volume-weighted average of
short-term wholesale trades, used as a reference/reverse price in imbalance settlement. That is a defensible reading
of the file name, and it is the interpretation adopted here — but it is an *inference from the name plus the BSC
definition*, not a documented statement in `SOURCE_MANIFEST.json`, which lists only the two column names. This
distinction matters and is carried into the uncertainty table (§7, U-1).

What the series is **not**, on the evidence I obtained:

| Candidate meaning | Verdict | Evidence |
|---|---|---|
| Supplier retail tariff (what a consumer pays) | **No** | Ofgem's price cap is built from wholesale cost *plus* network, policy, operating, EBIT, headroom and VAT components; the wholesale term is one input, necessarily below the tariff. |
| PPA / offtake price actually received by a generator | **No** | No PPA is documented for the constructed system; a PPA price is a bilateral contract term. |
| CfD strike price or CfD reference price | **No** | A CfD is "a private law contract between a low carbon electricity generator and the Low Carbon Contracts Company"; no CfD contract exists for the hypothetical farm. |
| Smart Export Guarantee tariff | **No** | SEG is capped at "up to a capacity of 5MW" (Ofgem); the supplied farm peaks at 1,125 MW. |
| Price actually received for every MWh generated | **Only under an explicit modelling assumption** | A generator is paid for *contracted* volume and settles *deviations* at the single cash-out price. With perfect foresight and full contracting, revenue = price × energy and imbalance is zero — which is exactly the Tier1 deterministic setting. |

### 2.2 Consequence for the model

Within a perfect-foresight run, using a daily average of this index as the unit revenue for each sold MWh is
**internally consistent**: no imbalance arises because the plan is assumed to be contracted to match realised output.
It is *not* a claim that a real generator would clear at the index on every MWh; the gap is the PPA discount, shape
risk and imbalance exposure, all of which are outside a deterministic Tier1 model.

The decisive limitation is temporal: a daily figure collapses ~48 half-hourly settlement periods. Battery value in
the real market is substantially *intraday* spread; a daily average cannot represent it. This is consistent with
BL-04 ("daily data do not reveal intraday price spreads") and it constrains what the team may claim: the model can
value **day-to-day shifting**, not intraday arbitrage. Any intraday claim needs half-hourly Elexon/NESO data, which
is an extension, not this file.

### 2.3 Unit check (arithmetic performed)

Computed over all 2,422 price rows:

- `max |avg_price_GBP_per_MW_day − 24 × avg_price_GBP_per_MWh| = 0.000000`
- rows failing that identity with tolerance 0.05: **0 of 2,422**

Therefore the second column is **not a second market price**. It is the same daily average expressed as GBP per MW
of average power held for a day; the identity is exact because 1 MW held for 24 h = 24 MWh. Example: a day at
£50.00/MWh is £1,200.00/MW-day. **Practical hazard:** multiplying the `£/MW_day` column by 24 a second time
overstates revenue by 24×. The interface below uses `avg_price_£_per_MWh` only, with `£/MW-day ÷ 24` as the
cross-check.

### 2.4 Descriptive statistics (own computation from the input copy)

| Quantity | Value |
|---|---|
| Rows / date range | 2,422 / 2020-01-01 .. 2026-09-17 |
| Mean / median | £48.17 / £41.13 per MWh |
| Min / max | −£8.46 / £333.83 per MWh |
| Negative-price days | 9 (0.37%), min −£8.46 |
| Negative days by year | 2020: 2, 2021: 1, 2023: 2, 2024: 1, 2025: 3 |

The mean is nominal, spanning a period that includes the 2021–22 gas crisis; it is **not** a forward expectation.
For orientation on the current price level, LCCC published a Baseload Market Reference Price for Winter 2026
(Oct 2026–Mar 2027) of £114.50/MWh — more than twice the 2020–2026 daily mean. That is evidence that the historical
mean is a poor central forecast and that price-level sensitivity is mandatory, not optional.

## 3. Demand, absorption and export limits (E-02)

### 3.1 What the supplied demand series is

`daily_demand.csv` has 2,451 rows, all with `recordType = VD`, covering 2020-01-01 .. 2026-09-17. Own computation:
mean 28,113 MW (674.7 GWh/day), 1st percentile 20,779 MW, 99th percentile 38,489 MW, max 42,031 MW.
`daily_generation_total.csv` has 2,422 rows, mean 25,583 MW (614.0 GWh/day).

The four series are **not coextensive**: intersection of price, demand, generation-total and wind-farm dates =
**2,406 days** (2020-01-01 .. 2026-09-17). Relative to that intersection, 16 price/gen dates, 45 demand dates and
47 wind dates fall outside it. (R4 owns D-02; recorded here because the interface's price coverage is 16 days
shorter than demand's.)

### 3.2 Is D_t a real "absorption limit"?

**No — and this is the most important R1 correction to the framing.** In the GB wholesale market there is no
per-generator absorption quota that stops a wind farm selling because "demand is already covered". Generators trade
volume; the system operator balances the aggregate; a generator's output is metered and settled, not rationed
against a demand allocation. The real, hard limit on a generator is its **connection capacity / Transmission Entry
Capacity**, i.e. a MW export cap, not an energy cap.

BL-02's construction (`D_t` = "the system's sales/absorption limit") is therefore a **modelling convention for a
constructed integrated system** (generation + demand treated as one portfolio), not a market rule. It is a legitimate
convention — it makes the "surplus" story legible and it is what policy B (`q_t = min{G_t, D_t}`) is built on — but
it must be labelled as such, and the alternative "merchant" interface (sell all output at the index, drop the `D_t`
cap) is equally defensible and should be run as a sensitivity, because it changes the battery/H2 business case: with
a `D_t` cap, storage is the only way to monetise surplus; without it, surplus is simply sold (possibly at negative
prices) and storage must justify itself on price spread alone.

### 3.3 Recommended treatment

1. Keep `D_t` as specified in BL-02 for the baseline runs, labelled "modelled absorption limit (constructed system)".
2. Add a hard **export cap** per day: `s_t ≤ E_cap` (MW × 24 h), where `E_cap` defaults to the farm's observed
   maximum of 1,125 MW (own computation) unless the team documents a connection size. This is the only limit with a
   real-world analogue.
3. Report "unserved demand" and "unused generation" as constructed-system KPIs (the brief asks for them), never as
   observed GB curtailment.
4. Run the merchant variant (no `D_t` cap) as sensitivity S3.

## 4. Purchases: admissible or not (E-03)

**Real-world position.** Buying electricity for resale requires being a licensed supplier: Elexon defines a Supplier
as a party that "holds a Supply Licence and is responsible for Exports and/or Imports". A generator that wants to
import and resell either becomes a supplier or buys through a third party; either way it pays wholesale **plus**
non-commodity costs, not the index alone. Ofgem's price cap decomposition shows the non-wholesale components
explicitly: network costs, policy costs, operating costs, EBIT, headroom and VAT (5%). Business contracts are outside
the cap, so there is no published ceiling for a commercial import tariff.

**Recommended baseline: purchases disabled.** This agrees with BL-07 ("purchases are disabled until an admissible
documented interface exists") and with the brief's silence on buying. It also avoids a concrete artefact: if imports
were free at the index, the optimiser would buy at the nine negative-price days and at every cheap day, and — with
no connection limit and no adder — manufacture unlimited profit. That is exactly the "unlimited import-to-H2
business" BL-07 prohibits.

**If the team enables purchases**, the interface must carry all four of:

1. **Eligibility**: supplier licence/third-party supply agreement (an assumption to be declared, not evidenced).
2. **Quantity limit**: `b_t ≤ I_cap` (MW × 24 h), connection import capacity, plus the physical demand of the battery
   and electrolyser.
3. **Price**: `p_buy,t = p_t + a`, with `a` = per-MWh network + policy + operating adder + VAT treatment.
4. **Net metering** (see E-04).

I could **not** close the numeric value of `a` in this pass: it needs the current Ofgem price-cap component tables and
business-tariff evidence, which is R4's F-01/F-03 territory. Bounded fallback for a scenario: `a ∈ {0, 10, 20, 30}`
£/MWh with `a = 0` explicitly flagged as an unrealistic lower bound; report the break-even `a` rather than asserting
a value. Note that `a = 0` is *known to be wrong*, since Ofgem's own decomposition shows non-wholesale costs are a
material share of a retail bill.

**Direction of the bias.** Disabling purchases biases the battery business case downward (no cheap-day charging) and
biases the electrolyser case downward too. That is a conservative choice consistent with BL-07, and it should be
stated as such in the report rather than left implicit.

## 5. Import/export asymmetry, negative prices, simultaneous trade (E-04)

### 5.1 Negative prices are real and must be kept

Nine of 2,422 days (0.37%) have a negative daily average, minimum −£8.46/MWh. A negative *daily average* implies most
or all of that day's settlement periods were negative, so these are genuine negative-price episodes, not one noisy
half-hour diluted to a positive average. BL-11 says keep genuine extremes; that is correct and I support it. A
"clamp to zero" variant is available as an explicitly labelled tail treatment (S2), never as "cleaning".

Economic content: on a negative day, selling destroys value. A 100 MWh sale at −£8.46/MWh costs £846. The correct
optimal response is to curtail, or to store if a later day's price exceeds the round-trip threshold. In a daily model
this is the only non-trivial role negative prices play, and it is worth reporting separately because it interacts
with policy B: B's mandated `q_t = min{G_t, D_t}` forces current generation to be allocated even when the price is
negative, so B pays for its priority rule precisely on these days (BL-06 already anticipates this; R1 supplies the
count: 9 days).

### 5.2 Import/export price difference

The asymmetry is structural, not incidental: an exporter receives the wholesale value (or a PPA discount to it),
while an importer pays wholesale **plus** non-commodity adders. So the same MWh is worth less sold than it costs
bought. Consequence for storage: arbitrage is profitable only if

```
η_rt · p_sell  >  p_buy          (η_rt = 0.90 from the brief)
=> p_sell / p_buy > 1/0.90 = 1.1111
```

i.e. the higher-priced day must be more than **11.11%** above the lower-priced day before a 2-hour battery earns
anything, before adders. With a non-zero adder `a` the threshold becomes `p_sell > (p_buy + a)/0.90`. At the sample
mean (£48.17 both sides) the trade is a loss of £4.82 per MWh cycled even before adders: **storage cannot be justified
by average prices, only by dispersion.** This is a check the team should run explicitly rather than inferring battery
value from a positive objective.

### 5.3 Simultaneous import and export

At one connection there is one metered net position per settlement period; importing and exporting at the same
instant is not a market strategy, it is a metering impossibility. Two model formulations are acceptable:

- **Net formulation (recommended).** Define `net_t = sales_t − purchases_t − charge_t − h2_use_t + discharge_t` and
  apply one price to `net_t ≥ 0`, a different price to `net_t < 0`. This structurally forbids same-day
  buy-and-sell arbitrage without a binary variable.
- **Binary formulation.** `sales_t ≤ M·z_t`, `purchases_t ≤ M·(1−z_t)` with `z_t ∈ {0,1}` and a documented big-M.

A battery charging from current generation and discharging to the grid on the same day is **not** a violation: that
is internal conversion; the restriction applies to the metered net position only. Confusing the two would wrongly
forbid the main battery use case, so the constraint must be written on the net position, not on charge/discharge.

## 6. Price-taking versus market impact (E-05)

### 6.1 Scale evidence from the supplied data

| Quantity | Value | Share of mean demand (28,113 MW) |
|---|---|---|
| Farm mean output | 424.6 MW | 1.51% |
| Farm maximum output | 1,125.0 MW | 4.00% |
| Farm maximum vs 1st-percentile demand (20,779 MW) | 1,125.0 MW | 5.41% |

A single asset that is at most ~4% of national demand, and ~5.4% in the tightest low-demand decile, cannot plausibly
set the national clearing price by itself. **Price-taking is a defensible assumption for this farm's own output**,
and it is the only assumption the supplied data can support, because the file is a daily average of realised trades:
it contains no supply curve, no bid stack and no quantity, so the marginal price of one extra MWh is simply not
identifiable from it.

### 6.2 What a price-impact model would need

A non-price-taking scenario needs a residual supply curve: price as a function of offered quantity, per settlement
period. Ingredients: half-hourly bids/offers and BM acceptances (Elexon/NESO), fuel-specific marginal costs, and
interconnector flows. None of that is in the five supplied files. A workable approximation the team could adopt later:

```
p_t(q) = p_t · (1 − q / Q_ref)        with q = farm output, Q_ref = a documented "price-elastic quantity"
```

but `Q_ref` (equivalently a slope in £/MWh per GW) is **not** something I obtained a defensible public value for, and
inventing one would repeat the "unsupported parameter" failure mode the research request warns about. Fallback:
retain price-taking, and *report the threshold* — e.g. the farm's output required to move price by 1% — so the reader
can judge the risk, rather than pretending to quantify it.

### 6.3 A second-order caveat worth stating

Price-taking for *output* is not the same as price-taking for *investment*. If the recommended portfolio includes
large batteries whose discharge concentrates in the highest-price days, correlated behaviour across many such assets
would erode the very spread the model exploits. This is a portfolio-level effect, invisible in a single-asset model
and not estimable from daily data; it should appear in the report as a stated limitation.

## 7. Curtailment and unused-generation economics (E-06)

**Baseline: unused generation earns nothing, costs nothing, and attracts no compensation.** Supporting structure:

- The Balancing Mechanism is where constraint-driven payments arise, and only registered units participate:
  "BM Units are used as units of trade within the Balancing Mechanism." The constructed farm has no documented BM
  Unit, no BSC accession and no metering registration, so it has no route to a constraint payment.
- The payments that do exist are system actions for physical limits — NESO describes "System actions deal with the
  physical limits of the energy system" — and they are costs recovered through balancing charges, not a general
  subsidy for not generating. Balancing costs are, in NESO's words, "one of many components making up consumer energy
  bills".
- I found **no** source establishing any general compensation for unused generation by a non-registered generator,
  and I explicitly do **not** claim this fictional system is eligible for any real scheme.

**Avoiding double counting (BL-09).** If electricity not sold is already an opportunity cost inside the profit
objective (`R_electricity` falls), then adding a separate "curtailment penalty" would charge the same MWh twice. The
baseline must choose one representation. Recommendation: opportunity cost only, no penalty term, no compensation
term.

**Optional, clearly labelled ablation (S6).** A curtailment/constraint payment `c_cur ∈ {0, 10, 20}` £/MWh, introduced
only to answer "what if the asset could be paid for constraint", with the eligibility caveat printed next to it. This
is a scenario about an alternative market, not a modelled entitlement.

## 8. Network and locational constraints deliberately omitted (E-07)

The brief and the launch transcript explicitly set aside the grid (TC-07: "anywhere there's demand, if we have
generation somewhere in the UK we can get it there"). R1's job is to say precisely what that omission costs and how
it should be represented if the team ever relaxes it.

**The four real charge families** (NESO charging overview):

| Charge | Who pays | Basis | Status for this model |
|---|---|---|---|
| TNUoS | "all suppliers and generators" | "Generators are charged according to Transmission Entry Capacity (TEC)", zonal | Fixed £/kW/year on connection capacity — **not** a per-MWh export cost |
| BSUoS | final demand only since Apr 2023 | ex-ante fixed tariff | **Zero** for the generator |
| Connection charges | the connecting user | assets specific to the connection | Capex/fixed, outside a dispatch model |
| AAHEDC | north of Scotland assistance | per-MWh/MW | Scope-dependent; a Scottish site could be affected |

Two findings that matter for modelling:

1. **BSUoS is not a generator charge.** NESO's BSUoS page lists generators with a cross (not charged) and states that
   "CMP308 defined that BSUoS charges are recovered solely from final demand, and CMP361 introduced an ex-ante fixed
   BSUoS tariff." A model that deducts a BSUoS £/MWh from export revenue is wrong for the post-April-2023 regime.
2. **TNUoS is a capacity charge, not a volumetric one.** Because it is levied on TEC in £/kW/year, it does not change
   the marginal decision to sell one more MWh; it changes the fixed cost of holding connection capacity, including
   capacity held for a battery. Putting it in as £/MWh would distort dispatch, which is the opposite error.

**Recommended baseline:** all network charges zero, consistent with the brief's simplification, but recorded as an
explicit omission with a stated direction of bias: omitting TNUoS **understates fixed costs**, and for a Scottish
site the omitted zonal charge is likely above the national average. A sensitivity (S5) applies a £/kW/year TNUoS
figure on TEC; I did **not** obtain a current numeric tariff, so the parameter is left open with a placeholder rather
than a fabricated number. NESO publishes TNUoS tariffs annually by 31 January for effect from 1 April, which is where
the team should take it.

**Locational/transmission limits.** Omitted by design. The honest statement is the one already in TC-07: the model
cannot establish actual Scottish curtailment or any site's deliverability. A locational extension needs zonal
constraints or a network model, and that is an extension, not a correction.

## 9. Recommended minimum baseline trading interface

Designed to be instantiable today from the supplied files with no invented number, and to satisfy BL-07's requirement
that every route be documented and finite.

### 9.1 Routes

| ID | Route | Direction | Volume limit | Price | Status |
|---|---|---|---|---|---|
| R-EXP | Daily index sale (merchant) | export | `s_t ≤ min(available, E_cap·24)`; `E_cap` default 1,125 MW (observed farm max) | `p_t` = `avg_price_£_per_MWh` | **enabled** |
| R-H2 | Direct hydrogen sale | product | `h2_t ≤` electrolyser output; outlet volume unconstrained at `£9.5/kg` (brief benchmark) | `£9.5/kg` ÷ 55.9 kWh/kg → `£169.95/MWh` of input electricity | **enabled** (R3 owns the price) |
| R-IMP | Grid purchase | import | `b_t ≤ I_cap·24`; default `I_cap = 0` | `p_t + a`, `a` open | **disabled** |
| R-CUR | Constraint/curtailment payment | n/a | n/a | `c_cur`, default 0 | **disabled** (no eligibility) |
| R-CFD | CfD top-up | export | n/a | strike vs reference | **not applicable** (no contract) |
| R-SEG | Smart Export Guarantee | export | ineligible: SEG applies up to 5 MW | n/a | **ineligible** |

Arithmetic behind the H2 electricity-equivalent price: £9.5/kg ÷ 55.9 kWh/kg = £0.16995/kWh = **£169.95/MWh** of
electricity consumed. This is why H2 can outbid direct sale on a high-price day but not on an average one — a useful
economic sanity check that the H2 route is not automatically superior. (Electrolyser capex and operating range are R3's
parameters; this figure is only the revenue-per-input-MWh conversion.)

### 9.2 Fees and charges carried by the interface

| Item | Value in baseline | Reason |
|---|---|---|
| BSUoS | 0 £/MWh | generators not charged post-CMP308 |
| TNUoS | 0 (fixed cost, excluded) | charged on TEC in £/kW/year; excluded by brief simplification |
| Connection charges | 0 | capex, outside dispatch model |
| AAHEDC | 0 | omitted with the other locational charges |
| CfD payments | 0 | no contract documented |
| Supplier obligation / policy levies | 0 on export; would apply on import | levied on suppliers/final demand |
| VAT | not applied | business-to-business treatment differs; R4 owns |
| PPA discount / imbalance exposure | 0 | perfect-foresight, fully contracted assumption (declared) |

### 9.3 Mapping of the supplied demand series to the interface

`D_t` enters in exactly two places and nowhere else:

1. **Policy constraint (regime B).** `q_t = min{G_t, D_t}` with `q_t` tracked as *direct current-generation sales*,
   separately from battery discharge and imports, so that discharge cannot silently satisfy the mandate (BL-06).
2. **KPI denominator.** Coverage = (served demand)/`D_t`; unserved demand = `D_t` − served.

`D_t` is **not** a market quota in regime A beyond the team's chosen modelling convention (§3.2). Units: `D_t` is an
average MW for the day; multiply by 24 to obtain MWh. 674.7 GWh/day at the sample mean.

### 9.4 Prices, units and the one number that must not be double-counted

- Use `avg_price_£_per_MWh` as `p_t`. Never multiply the `£/MW_day` column by 24 again.
- All energies in MWh/day; all powers in MW; cost in £.
- `p_t` is a **daily average of half-hourly index prices**; no intraday information is recoverable from it.

### 9.5 Sensitivity and alternative-market scenarios

| ID | Scenario | Parameter | Purpose |
|---|---|---|---|
| S1 | Price level | multiplier 0.75 / 1.00 / 1.25 on all `p_t` | historical mean is not a forecast (Winter 2026 baseload £114.50/MWh vs 2020–26 mean £48.17) |
| S2 | Negative-price treatment | retain (baseline) vs clamp `p_t ≥ 0` | labelled tail treatment, not cleaning; isolates the value of the 9 negative days |
| S3 | Merchant vs integrated | drop / keep the `D_t` cap in regime A | tests whether the "surplus" story drives the investment answer |
| S4 | Purchases enabled | `a ∈ {0, 10, 20, 30}` £/MWh; report break-even `a` | quantifies the cost of the closed-market default |
| S5 | Network charges | TNUoS `£/kW/year` on TEC, value to be taken from NESO tariff tables | direction of bias of the omission |
| S6 | Constraint payment | `c_cur ∈ {0, 10, 20}` £/MWh, eligibility caveat printed | alternative-market ablation only |
| S7 | Market impact | linear slope parameter, or price-taking with reported threshold | shows what cannot be estimated from daily data |

## 10. Conversions and checks (all arithmetic shown)

1. **Price unit identity.** `£/MW-day = 24 × £/MWh`. Verified: max absolute deviation 0.000000 over 2,422 rows.
   Worked example: £48.17/MWh → £1,156.08/MW-day.
2. **Demand energy.** 28,113 MW × 24 h = 674,712 MWh/day = 674.7 GWh/day.
3. **Generation energy.** 25,583 MW × 24 h = 613,992 MWh/day = 614.0 GWh/day. The gap (60.7 GWh/day) is the
   constructed system's average shortfall and is the scale of the problem the flexibility assets address.
4. **Farm share of demand.** 424.6/28,113 = 1.51%; 1,125.0/28,113 = 4.00%; 1,125.0/20,779 = 5.41%.
5. **Gross revenue anchor.** 424.6 MW × 24 h = 10,190.4 MWh/day; × £48.17/MWh = £490,872/day; × 365 =
   **£179.2m/year** at the sample mean price, before any cost. This is the scale against which battery/electrolyser
   capex must be judged, and it is a useful sanity anchor for the investment story (electricity revenue at the index
   dominates the flexibility revenue streams).
6. **Battery cycling threshold.** `p_sell/p_buy > 1/0.90 = 1.1111`; at equal prices, £48.17 cycled loses
   `48.17 − 0.90 × 48.17 = £4.82` per MWh purchased.
7. **Negative-day loss.** 100 MWh sold at −£8.46/MWh = −£846 (a cost, i.e. a reason to curtail).
8. **H2 electricity-equivalent.** £9.5/kg ÷ 55.9 kWh/kg = £0.16995/kWh = £169.95/MWh of input electricity.
9. **Buy/sell break-even adder.** Profit per MWh bought = `0.90·p_sell − p_buy − a`; setting to zero gives
   `a* = 0.90·p_sell − p_buy`. At `p_sell = p_buy = £48.17`, `a* = −£4.82`, i.e. no positive adder is ever recovered
   at equal prices; at `p_sell = £80`, `a* = £72.00 − £48.17 = £23.83/MWh`. This is the number the S4 scenario should
   report rather than an asserted tariff.

## 11. Proposed decisions

- **Supports Baseline 1103:** BL-02's `D_t` treatment *as a labelled convention*; BL-04's prohibition on intraday
  claims; BL-06's requirement to track direct current-generation sales separately; BL-07's closed set with purchases
  disabled; BL-09's single-counting of opportunity cost; BL-11's retention of negative prices.
- **Should change or be sharpened:** (a) BL-02 should say explicitly that `D_t` is a modelling convention with no
  market analogue, and that the merchant variant is a required sensitivity rather than an alternative universe;
  (b) BL-07 should note that a *non-zero* per-MWh adder is required before purchases can be enabled at all — `a = 0`
  is already known to be wrong from Ofgem's own cost decomposition; (c) any curtailment-payment scenario must carry
  an eligibility caveat, because BM participation is what makes constraint payments possible.
- **Minimal parameter set instantiable now:** `p_t` from the file; `E_cap` = 1,125 MW; `D_t` from the file;
  all charges zero; purchases off; H2 at £9.5/kg with the 55.9 kWh/kg conversion.
- **Unknowns and fallbacks:** non-commodity adder `a` (bounded 0–30, break-even reported); TNUoS £/kW/year (0 with
  placeholder); price-impact slope (price-taking, threshold reported); day-level aggregation rule of the supplied
  price (assume equal-weighted daily mean of settlement-period prices, flag it).
- **Extensions and their information needs:** intraday arbitrage needs half-hourly MID/BM data; market impact needs
  half-hourly bids/offers and interconnector flows; constraint income needs BM registration and metering; CfD support
  needs a CfD contract and the negative-pricing rule.
- **Findings most likely to change the investment recommendation:** the scale anchor in §10.5 (electricity revenue
  dwarfs flexibility revenue at the index), the 11.11% cycling threshold (§10.6), and the S3 merchant-vs-integrated
  switch, which decides whether storage is the *only* route to surplus value or merely one route among several.

## 12. Uncertainty register and known gaps

| ID | Gap | Why it matters | Fallback used |
|---|---|---|---|
| U-1 | The file is named "market index price" but neither `SOURCE_MANIFEST.json` nor any supplied document states which index, which aggregation, or weighted vs unweighted | If it is not the BSC MIP, the whole E-01 reading shifts | Treated as BSC Market Index Price, equal-weighted daily mean; declared as inference |
| U-2 | Daily aggregation rule (weighted by volume across 48 periods, or simple mean of period prices?) | Affects the level, especially in spiky periods | Assume simple mean; flag for R4/D-01 |
| U-3 | No CfD negative-pricing rule obtained (LCCC negative-pricing page returned 404; GOV.UK search did not surface the provision) | Only matters if a CfD-supported scenario is adopted; the constructed system has no CfD | CfD route marked "not applicable"; rule left as an explicit gap |
| U-4 | No numeric non-commodity adder for business import | Purchases cannot be priced defensibly | Purchases disabled; `a` bounded 0–30 with break-even reported |
| U-5 | No current TNUoS £/kW/year tariff obtained | Understates fixed cost of a Scottish connection | 0 in baseline; placeholder parameter with NESO as the source of record |
| U-6 | No price-impact coefficient, and none derivable from a daily average | Price-taking is an assumption, not a measurement | Price-taking plus a reported threshold |
| U-7 | Demand series has 45 dates not in the four-way intersection; price has 16 | Coverage loss affects comparability of A/B runs | 2,406-day common window identified; R4 owns D-02 |
| U-8 | Business/industrial tariff evidence not obtained (Ofgem's published cap covers domestic and micro-business) | Blocks any claim about what a commercial buyer actually pays | Stated as a gap; no tariff asserted |

## 13. Cross-validation

Not performed. This is a preserved first pass and, per the instruction, I did not read any peer or earlier-round
result. The only cross-checks executed were **internal**: the 24× price identity (2,422 rows, zero failures), the
`recordType` census of the demand file (all `VD`), and the four-way date intersection (2,406 days). Cross-validation
against another researcher's independently derived adder, TNUoS figure and price-impact treatment remains to be done
in a later pass, and should reproduce §10 items 1, 6, 8 and 9 as the shared arithmetic.

## 14. Handoff

Files (all under `Tier1/workspaces/mocry/cleveruser/firstpass/R1-market/`):

| File | Content |
|---|---|
| `REPORT.md` | this report |
| `parameters.json` | 35 typed claims with units, price year, scope, source reference, strength and baseline value |
| `sources.json` | 17 entries: 12 public primary sources actually read (with locators and verbatim quotes ≤25 words each), 3 local inputs, 2 own-computation pseudo-sources; plus a failed-retrieval list |
| `FIRST_PASS.md` | identity, independence declaration, timestamps, failed retrievals |
| `_scratch/analyze_inputs.py` | reproducible descriptive script for §2.4, §3.1 and §6.1 figures |
| `_scratch/validate.py` | schema and arithmetic assertions over `parameters.json` / `sources.json` (all pass) |

Suggested next actions: (1) R4 to supply the price-file aggregation rule and the business import adder; (2) whoever
owns the run manifest to adopt §9 verbatim or record a departure; (3) a cross-reviewer to independently reproduce
the four arithmetic checks in §13. No blocker prevented completion; the eight items in §12 are the honest residue.
