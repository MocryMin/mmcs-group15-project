# Tier1 — Baseline 1103 discussion and research package

Date: 3 November 2026. Proponent: Ran Min, assisted by `mocry-codex`.

Status: a proposed group baseline, assembled from Ran Min's decisions and explicitly labelled operational defaults. One controller-led research round and review are now complete; group adoption and a final investment optimisation are not implied by publication.

## Reviewed research now available

The [20261103-v1.1 controller research release](../research_1103/controller/mocry-codex/20261103-v1.1/README.md) contains four topic reports, saved first passes, source/parameter catalogues, three cross-reviews, the modern-electrolyser-cost follow-up,20 controller dispositions and the [recommended parameter family](../research_1103/controller/mocry-codex/20261103-v1.1/BASELINE_CANDIDATE.json). Open-ended searching for this controlled round is closed. Other members' independent contributions and challenges remain welcome.

The v1.1 snapshot corrects four line-ending-dependent manifest hashes in v1; findings and numerical recommendations are unchanged. The original v1 remains preserved. The release is a reviewed proposal, not a silent revision of [BASELINE_1103.md](BASELINE_1103.md). Actual hydrogen contracts/eligibility, private discounting and identified source conflicts remain explicitly labelled scenarios. The original research request below remains as the historical agenda.

## Read in this order

| Document | Purpose |
|---|---|
| [Project overview](../../../PROJECT.md) and [original brief](../../../Project_Brief.pdf) | Original task, inputs and outputs |
| [TEACHER_ORIGINAL_EXCERPTS.md](TEACHER_ORIGINAL_EXCERPTS.md) | Verbatim timestamped segments from the supplied transcript |
| [TEACHER_CLARIFICATIONS.md](TEACHER_CLARIFICATIONS.md) | Source wording, reported after-class discussion, our interpretation and limits of generalisation |
| [GAPS.md](GAPS.md) | What the project still leaves to discussion, research or modelling choices |
| [BASELINE_1103.md](BASELINE_1103.md) | Proposed deterministic model family, A/B supply rules and evaluation conventions |
| [RESEARCH_REQUEST.md](RESEARCH_REQUEST.md) | Four research packages; request for Ran Min to dispatch independent researchers |
| [RESEARCH_RESULT_TEMPLATE.md](RESEARCH_RESULT_TEMPLATE.md) | Comparable evidence, parameter and cross-validation output format |

Complete shared sources: [original TXT](../../../Project_Launch_Transcript.txt), [complete timestamped TXT](../../../Project_Launch_Transcript_Timed.txt), [source manifest](../../../SOURCE_MANIFEST.json), and the five CSVs at the repository root.

## Current direction

Keep given total generation plus the specified independent wind profile fixed. Choose battery/electrolyser additions. Compare A (electricity sales/charging/hydrogen allocation chosen economically) and B (current generation serves current demand first). Maximise the scheme's net profit/net benefit; report improvement relative to the matching no-investment comparator. Use daily inputs and perfect information for Tier1. Research supplies technology, market and financial parameters.

## Open participation

Every member and registered agent may comment on any teacher interpretation, gap definition, baseline assumption, research question or implementation default. Cite an ID such as `TC-04`, `M-02` or `BL-09`, explain the issue, and propose a specific alternative with its consequences. A useful challenge may expose a missing gap or argue that a proposed gap is unnecessary.

Send a new targeted/broadcast message in `Tier1/agent_message` and publish a new uniquely named public proposal or research artifact if needed. Follow both area's `agent_skill_protocol.md`. Do not rewrite another member's workspace or erase earlier proposals. Silence is not agreement. A change becomes adopted when its decision and scope are recorded.

Independent research is welcome from any number of members/agents. More evidence, alternatives and substantive cross-checks are encouraged; results can be aggregated without discarding conflicting findings. No researcher is assumed to be running merely because they are named in the request.
