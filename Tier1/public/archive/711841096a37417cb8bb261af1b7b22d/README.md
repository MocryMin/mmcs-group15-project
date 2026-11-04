# Tier1 shared artifacts

Read [agent_skill_protocol.md](agent_skill_protocol.md) before writing here.

Start with [Baseline 1103](baseline_1103/INDEX.md): original teacher excerpts and interpretation, information gaps, proposed deterministic A/B assumptions, research requests and a result template. [PROJECT_SCOPE.md](PROJECT_SCOPE.md) gives the short scope.

The [project overview](../../PROJECT.md), original PDF, five supplied CSVs and complete transcripts are at the repository root. [SOURCE_MANIFEST.json](../../SOURCE_MANIFEST.json) records hashes and provenance. Keep those originals unchanged; publish processed inputs and corrections separately.

- `logs/<agent-id>.jsonl`: append-only operation records.
- `archive/<event-id>/...`: immutable previous versions created by updates.
- `research_1103/<package>/<agent-id>/<result-id>/...`: suggested unique location for independent research outputs and later syntheses.

All members/agents may propose changes to teacher interpretations, the gap system or Baseline 1103. Research is open to additional independent contributions and aggregation. Use messages with specific IDs and file pointers; retain evidence conflicts and do not imply consensus merely from publication.

## Reviewed research release

The [20261103-v1.1 release](research_1103/controller/mocry-codex/20261103-v1.1/README.md) publishes the completed four-topic research, independent first passes, cross-reviews, controller dispositions and [recommended parameter family](research_1103/controller/mocry-codex/20261103-v1.1/BASELINE_CANDIDATE.json). The controller has closed this research round; substantive independent contributions remain welcome. It is a reviewed proposal, not group consensus or a replacement of Baseline1103 by implication.


The original v1 is preserved. Version v1.1 corrects four Markdown manifest hashes after Git line-ending conversion; research text and numerical recommendations are unchanged.

## Past project report examples

[Six teacher-supplied examples](reference/past_project_reports/20261103-v1/README.md) are now archived with years/topics, source links and original/public hashes. They are historical completed reports, useful for structure and presentation; current project requirements remain separate.

## Generation data quality

[Generation provenance audit and 107-day repair candidate](data_quality/generation_repair/20261103-v1/README.md) includes official-source evidence, a per-date audit, two model-ready CSVs and an offline verifier. It is a Tier 1 comparison input. See the audit for known data issues outside the patch.
