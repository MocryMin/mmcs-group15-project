# Teacher wording, clarifications and interpretation

The source text and our interpretation have different roles. `Written` means the supplied brief. `Transcript` means wording in the owner's transcript export, not an audio-verified quotation. `Reported discussion` means Ran Min's report of a teacher conversation; no original recording/email of that conversation is available here. `Interpretation` and `generalisation` are our own modelling readings and remain open to challenge.

Read the [complete original TXT](Project_Launch_Transcript.txt), [complete timestamped TXT](Project_Launch_Transcript_Timed.txt), [selected exact segments](TEACHER_ORIGINAL_EXCERPTS.md) and [original brief](Project_Brief.pdf) alongside this document.

## TC-01 — existing position and constructed system

Written, brief page 2:

> For the purposes of this project, treat the infrastructure using the supplied datasets as the client's existing position.

> The supplied generation, demand and pricing data represent a constructed energy system and should not be interpreted as a detailed picture of Scottish transmission constraints or actual curtailment events.

Interpretation: Tier1 inherits generation rather than requiring new generation investment. The actual asset/data connection must be made explicit. Ran Min's proposed connection is total generation plus the independent simulated farm; this particular addition/non-inclusion convention is a baseline assumption, not a verbatim teacher statement about a facility's inclusion in the national total.

## TC-02 — daily national-scale background and simulated farm

Transcript EX-03, 01:09:38–01:10:26, describes generation and demand on UK scale. EX-04, 01:11:32–01:12:27, explains the farm simulation:

> And then I used the weather data together with the, let's say the characteristics of a wind farm that's to be developed. And I simulated what the energy generation would have been,

Interpretation: the separate farm series is a hypothetical output under dated weather conditions. It is not an observed extra national fuel category or a forecast for future calendar years. The demand column is not an additional unpaid internal company load. The total file aggregates the fuel-level file, including wind categories; do not add those fuel rows to the total again.

## TC-03 — deterministic Tier1 and investment

Transcript EX-05, 01:12:27–01:13:24:

> The baseline model, OK, we should think of this as something purely deterministic. OK. So we know exactly in the future.

EX-06, 01:13:24–01:14:23, introduces installation at the start and says investment timing could also be modelled differently.

Interpretation: perfect-information operation is valid for Tier1. A single initial investment is a suitable baseline convention. Dynamic acquisition timing is an optional extension, not a requirement inferred from the example.

Written, brief page 3:

> Tier 1 models should use a simplified treatment of time – detailed chronological operation of storage is not required at this stage.

Interpretation: daily chronological modelling is our choice, not a compulsory Tier1 requirement. It does not by itself address Tier2B's unknown-future decisions.

## TC-04 — direct sale competes with storage

Transcript EX-07, 01:14:23–01:15:17, explicitly asks whether to charge or sell. EX-08, 01:15:18–01:16:13:

> The first reason is because when we produce more than demand, we don't throw it away, we store it. OK. The second reason it's useful is because when prices are low, We can decide not to sell the energy on the market and rather store it in the battery so that we can sell it later when prices are high.

Interpretation: restricting every model to charging only otherwise-unsaleable generation would omit one stated battery use. Baseline A permits the competition; B deliberately studies the restricted current-generation-supply-priority policy. The exact market absorption/import/export rules remain model inputs/assumptions.

## TC-05 — hydrogen outlet and optional reconversion

Transcript EX-09, 01:16:13–01:17:11:

> to just sell it on the open market. OK, so just assume you can always sell like 1 kg of hydrogen for, I don't know, 2 pounds 50 or whatever it is, OK.

The same segment introduces storing hydrogen and generating electricity later as another option.

Interpretation: direct H2 sale is a suitable minimum outlet. The spoken GBP2.50 is an example, not a replacement for the written GBP9.5/kg supported benchmark. H2 storage, transport and reconversion need their own costs, limits and evidence if added.

## TC-06 — unknown-future extensions

Transcript EX-10, 01:18:07–01:19:02, discusses making investment decisions before realising scenarios. EX-11, 01:19:03–01:19:59:

> But I don't know the price and I don't know the energy generation, and I don't know the demand in the future. I know nothing about the future.

Interpretation: separate known-path Tier1, held-out capacity evaluation and causal operation. Fixing trained capacity but optimising over all validation-day observations is a fixed-capacity operational oracle, not a causal strategy. Complete chronological accounting alone does not remove foresight.

## TC-07 — grid/geography simplification

Transcript EX-12, 01:22:48–01:23:44:

> And we just say, well, OK, well, anywhere there's demand, if we have generation somewhere in the UK we can get it there.

Interpretation: a baseline without spatial/transmission constraints matches this simplification. It cannot establish actual Scottish curtailment or a particular site's deliverability. Network constraints are an optional extension.

## TC-08 — costs, modules and permission to change assumptions

Source: Ran Min's report of teacher discussion, recorded on 2 November. This is the owner's original report, not the teacher's verbatim speech:

> 教师表示这个你可以自己调研，甚至可以用调研结果覆盖288000的数值；甚至可以引入类似真实商业中的"多买更便宜“这类机制；然后提到一般不是纯粹的连续integer的”定制化“电池，而是有一个变化grid。我认为，可能，电池，电解池，我们可以用自己调研的参数、价格覆盖它的题设参数。teacher说”no right and wrong"，但是如果你改变参数，你需要说明为什么改变（调研来源）

Reported teacher clarification: researched battery costs may replace EUR288000/MWh if sourced and explained; bulk discounts and commercially discrete capacity grids can be considered.

Our interpretation: research should identify real installed-cost boundaries, modules and price schedules rather than assume endlessly customised fractional devices.

Generalisation proposed by Ran Min: the same source-and-explain principle may extend to electrolyser prices and other equipment parameters. The discussion report does not enumerate permission for replacing every efficiency, SOC or duration requirement. Preserve the written defaults and explicitly identify proposed departures.

## TC-09 — equipment reference values

Written brief pages 3 and 6 specifies/recommends: two-hour battery; 90% roundtrip efficiency; normal SOC range 20%–80%; indicative EUR0.288m/MWh; electrolyser capacity as a decision with 20MW PEM reference; operating range 20%–100%; 55.9kWh/kg H2; initial GBP9.5/kg policy-supported H2 benchmark with price sensitivity.

Interpretation: reference equipment sizes are not fixed optimal capacities. Research parameters must be accompanied by units, cost scope, operational applicability and an explanation of deviations. Electrolyser minimum load applies when running; a workable model must also specify shutdown. Parameter replacement is not silently treated as a teacher correction.

## TC-10 — objectives, validation and client recommendation

Written brief page 1:

> There is no single required objective function, model architecture or data processing route.

Page 5 requires comparison with simpler alternatives, sensitivity and a distinction between data-supported conclusions and modelling assumptions.

Interpretation: net profit/net benefit is a legitimate primary objective. Coverage/unused energy can be reported separately. A/B policies and no-investment comparisons can support the consulting story; adding mechanisms alone does not establish a better recommendation.

## TC-11 — report and pitch

Transcript EX-01, 01:05:51–01:06:49:

> And this has a 10-page limit.

EX-02, 01:06:49–01:07:45:

> OK, this is a business pitch.

The full segment explicitly excludes maths and code from that pitch. Interpretation: technical details belong in the report; the pitch explains investment and consequences. The earlier six-page/appendix discussion concerns Assignment2 and is not a project appendix rule.
