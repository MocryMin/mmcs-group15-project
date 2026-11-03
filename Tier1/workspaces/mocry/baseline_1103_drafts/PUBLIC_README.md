# Tier1 shared artifacts

Read [agent_skill_protocol.md](agent_skill_protocol.md) before writing here.

Start with [Baseline 1103](baseline_1103/INDEX.md): original teacher excerpts and interpretation, information gaps, proposed deterministic A/B assumptions, research requests and a result template. [PROJECT_SCOPE.md](PROJECT_SCOPE.md) gives the short scope.

The [project overview](../../PROJECT.md), original PDF, five supplied CSVs and complete transcripts are at the repository root. [SOURCE_MANIFEST.json](../../SOURCE_MANIFEST.json) records hashes and provenance. Keep those originals unchanged; publish processed inputs and corrections separately.

- `logs/<agent-id>.jsonl`: append-only operation records.
- `archive/<event-id>/...`: immutable previous versions created by updates.
- `research_1103/<package>/<agent-id>/<result-id>/...`: suggested unique location for independent research outputs and later syntheses.

All members/agents may propose changes to teacher interpretations, the gap system or Baseline 1103. Research is open to additional independent contributions and aggregation. Use messages with specific IDs and file pointers; retain evidence conflicts and do not imply consensus merely from publication.
