# Tier1 research findings and controller recommendations

Release 20261103-v1.1. Prepared for Ran Min and Group 15 on 3 November 2026. Three delegated researchers and the controller completed the first research round, targeted cross-reviews and one follow-up on contemporary electrolyser installation costs. Open-ended searching is now closed. The result is a reviewed, conditional parameter proposal; publication does not establish agreement by the whole group or a new optimal investment result.

## Proposed common model

Keep the supplied total generation plus the independent simulated wind profile fixed, following Baseline 1103's constructed-system convention. Treat supplied demand as the common electricity-sales absorption limit, rather than a second unpaid internal load. Use daily chronology and Tier1 perfect foresight. Choose initial equipment capacity once, then optimise its operation.

Regime A lets direct sales, battery charging/discharging and hydrogen production compete economically. Regime B requires direct sales from current generation to equal min(G,D); only the remainder of current generation may charge batteries or make hydrogen. Battery discharge may serve the remaining sales headroom. B does not require imports or compulsory battery depletion. Compare A0/A1 and B0/B1 with identical accounting. Maximise annual-equivalent scheme net profit and report matching incremental improvements and physical coverage metrics.

## Market boundary

Use the supplied daily wholesale price as an electricity-value proxy. Direct sales and battery-output sales share the same demand cap. Set imports and extra export outlets to zero in the minimum baseline, and award no automatic payment or penalty for unused generation. Zero sales fees and zero price impact are explicit simplifications, not verified contracts or proof of a conservative profit lower bound. Additive sales-fee sensitivity uses p-f, which also behaves correctly for negative prices.

Elexon distinguishes contracted trading from imbalance settlement. Wholesale or imbalance prices do not establish a complete supplier import tariff. NESO balancing-cost information does not entitle this constructed system to curtailment compensation. Keep negative prices; A may withhold a loss-making sale, while the chosen B rule remains binding.

## Battery capacity and costs

Retain the brief's two-hour nameplate ratio, 90% AC round-trip efficiency and 20–80% state-of-charge range. The usable internal window is 60% of nameplate energy. With symmetric charge/discharge efficiencies sqrt(0.9), one full usable-window discharge supplies approximately 1.138 hours at rated output, rather than two usable hours.

The Danish Energy Agency workbook gives a 2025-technology, EUR2020 installed reference for 3 MWh/1.5 MW: EUR288,000 per nameplate MWh. Its component costs already cover the stated installation scope; do not add the same power-conversion or EPC items again.

The workbook has a real maintenance-cost inconsistency. The displayed unit gives EUR8,3522020/MW/year, whereas applying the footnote's 2.9% to total installed CAPEX gives EUR16,7042020/MW/year. Independent source-workbook review confirmed the factor of two. Use the latter as the proposed main case and retain the former as sensitivity; neither is an officially confirmed correction. Do not separately charge the same inverter replacement already covered by the catalogue's maintenance convention.

A 3 MWh/1.5 MW integer reference grid is a convenient analytical choice, not a commercial SKU. TESVOLT provides real container-energy candidates of 1.9/4.2/4.6 MWh, but no complete current installed quotation or matching external PCS contract was obtained. No bulk discount was invented. A conservative daily model allows one direction and at most one usable-energy window per day, with power, losses and inventory constraints. It does not recover intraday arbitrage from daily data.

## Electrolyser and hydrogen outlet

ITM POSEIDON supports a 20 MW module reference, 20–100% load while on and a separate off state. Its 55.9 kWh/kg is beginning-of-life, whole-system AC consumption, including the specified water-treatment and balance-of-plant energy. Do not add that energy twice. Use the energy identity for output; 20 MW/55.9 implies about 357.78 kg/hour, with the advertised 360 treated as rounded.

The controller's follow-up obtained IEA's 2025 executive summary: manufacturing and installing electrolysers outside China in 2024 cost USD2,000–2,600/kW. Use this modern generic installed range ahead of the old UK proxy; USD2,300 is an analyst-selected midpoint. This is not an ITM, PEM-specific or UK-site quote. The summary does not explicitly label a constant-dollar base or AC/DC power point. The reporting scenario treats the observed costs as nominalUSD2024 and infers electrical-input capacity, retaining those assumptions.

With the declared ECB annual-rate conversion and ONS CPI convention, the range becomes GBP2020 1,269.95–1,650.93 per assumed electrical kW, midpoint 1,460.44. These GBP figures are the controller's conversion, not directly quoted IEA values. EPC and contingency are already in the installed scope. Do not transfer BEIS's old 60%-of-plant stack share onto this differently composed new total. Historical UK costs remain labelled sensitivity; old absolute O&M/replacement proxies remain independently uncertain.

The minimum outlet scenario sells hydrogen at a declared plant-gate boundary on the production day, with finite offtake and no cross-day hydrogen inventory or reconversion. Quality, drying, compression and downstream responsibilities must match the net price. The brief's GBP9.5/kg is a supported-value reference, not a signed buyer contract. The explicit HAR1 GBP175/MWh2012 reference converts to about GBP7.7992020/kg using the brief's39.4kWh/kg and CPI. Neither reference proves eligibility; no second copy of the same subsidy is added. Offtake limits0/2,000/10,000/50,000kg/day are analyst scenarios, not researched customer demand.

## Data and finance

The five unchanged CSVs have2,406 common dates in28 continuous segments. The longest segment runs from24September2022 to17September2026. Complete2023/2024/2025 permit chronological design/validation/final-test years, with early crisis periods retained as separate stress tests. Do not connect state of charge across an unmodelled date gap. Nine negative-price common dates remain. Demand636 on2August2022 is flagged, not proven wrong or deleted.

Fuel-category sums exactly reconcile to total generation, and the price-per-MW-day column equals24times the price-per-MWh column. These checks do not independently prove the producer's demand aggregation definition. If daily meanMW is assumed, convert consistently by24 toMWh/day.

Report in constant2020GBP, using monthly ONS CPI for historical electricity prices and the documented ECB annual reference conversion for EUR2020 costs. General CPI is a reporting deflator, not an equipment price forecast. Propose5% real discounting with0/3/8/12% sensitivity; these are analyst choices, not an identified private hurdle rate. The Green Book's public social discount rate does not identify this client's cost of capital.

Use consistent annual-equivalent costs: capital recovery by declared asset life, affected operating costs and either explicit stack-replacement events or a replacement reserve, never both for the same expense. Do not compare a single year's revenue with all lifetime capital expenditure as if that were a complete investment valuation.

## Controller disposition and remaining choices

Source evidence or explicit bounded modelling fallbacks now exist for the minimum Tier1 interfaces. Reopen a topic for a specific buyer netback/offtake agreement, a comparable installation or maintenance quotation, manufacturer guarantees, producer data corrections, or a model result showing that an unresolved assumption controls the investment conclusion. Imports, empirical market-impact fitting, hydrogen storage/reconversion, bulk discounts and detailed network models are deferred extensions.

The actual research team comprised one GPT6Astra market worker, two GPT6.1Sol equipment workers and the controller. Initial analyses were preserved before peer review. A shared anonymous browser broker transported source documents during a browser-profile conflict; the analyses were independent, but the retrieval was not independently repeated three times. No DS/Clever User run is claimed. Three cross-reviews checked FX/discount scope, hydrogen units/cost scope and the battery maintenance conflict; the IEA addition received a further bounded review.

## Selected primary references

- Elexon Market Index Data: https://www.elexon.co.uk/bsc/glossary/market-index-data/
- Elexon BSC: https://www.elexon.co.uk/bsc/about/
- NESO balancing costs: https://www.neso.energy/industry-information/balancing-costs
- DEA storage workbook: https://ens.dk/media/6589/download
- TESVOLT technical sheet: https://www.tesvolt.com/_media/05%20SERVICE/03%20Downloads/E-Serie/TPS-E/Datenblatt/RD.TI.094.E.en-US_v.B.02.pdf
- ITM POSEIDON technical sheet: https://itm-power-assets.s3.eu-west-2.amazonaws.com/POSEIDON_DATA_SHEET_2_7_2e1f89da3f.pdf
- IEA modern installed costs: https://www.iea.org/reports/global-hydrogen-review-2025/executive-summary
- BEIS original costs: https://assets.publishing.service.gov.uk/media/611b710e8fa8f53dc994e59d/Hydrogen_Production_Costs_2021.pdf
- BEIS original Annex: https://assets.publishing.service.gov.uk/media/611a706ed3bf7f63a7b29216/Hydrogen_Production_Cost_2021_Annex.xlsx
- HAR1 supported values: https://www.gov.uk/government/publications/hydrogen-production-business-model-net-zero-hydrogen-fund-shortlisted-projects/hydrogen-production-business-model-net-zero-hydrogen-fund-har1-successful-projects
- ONS CPI: https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23
- ECB2020 GBP/EUR: https://data-api.ecb.europa.eu/service/data/EXR/A.GBP.EUR.SP00.A?startPeriod=2020&endPeriod=2020&format=csvdata
- ECB2024 GBP/EUR: https://data-api.ecb.europa.eu/service/data/EXR/A.GBP.EUR.SP00.A?startPeriod=2024&endPeriod=2024&format=csvdata
- ECB2024 USD/EUR: https://data-api.ecb.europa.eu/service/data/EXR/A.USD.EUR.SP00.A?startPeriod=2024&endPeriod=2024&format=csvdata
- Green Book2026: https://www.gov.uk/government/publications/the-green-book--2/the-green-book-2026
