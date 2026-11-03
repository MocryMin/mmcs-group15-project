# Tier2 shared artifacts

Read [agent_skill_protocol.md](agent_skill_protocol.md) before writing here.

- `PROJECT_SCOPE.md`: initial scope and current decisions still to be made.
- `logs/<agent-id>.jsonl`: append-only operation records, created on first publication.
- `archive/<event-id>/...`: immutable previous versions, created on first replacement.

Current files are updated through the publication helper. Logs and archives retain every published change. This scaffold contains no original course files or private data.
