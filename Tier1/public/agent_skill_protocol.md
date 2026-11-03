# Tier1 public area protocol

## What belongs here

Share project inputs that may be published, data manifests, assumptions, model interfaces, reviewed code/results, decisions and reproducibility notes. Drafts stay in their owner's workspace until deliberately shared. Start new work under a descriptive path, such as `findings/<topic>.md` or `interfaces/<name>.json`; use a unique name if a shared path is contested.

Current public artifacts may change. Their archives and operation logs never lose history. This applies even when you replace a file that you originally wrote.

## Publish an artifact

Use `python tools/collab.py publish --tier <acting-tier> --area Tier1 --path <relative-public-path> --source <local-file> --summary "<reason>"`.

- A new path creates the file and one operation record.
- A replacement saves the exact old bytes under `archive/<event-id>/<relative-public-path>`, writes the new bytes, and appends one record. The record includes actor/member, UTC time, source tier, old/new SHA-256, base commit, archive and restoration instructions. Publish once per target path in a commit; the checker compares that update with its actual parent.
- Restore by publishing the archived file as the source for the current path. This creates a fresh archive and a new log. Never rewind the shared branch.
- Do not delete current artifacts. Mark an obsolete artifact as superseded using a documented update, or add a deprecation note pointing to its replacement. Archives and old log lines are immutable.
- If your acting tier is not Tier1, only add new paths here. Ask a Tier1 agent to integrate an update. Do not overwrite an existing cross-tier import.
- `logs/` and `archive/` are reserved; never publish arbitrary files into them. Protocol changes require the maintainer's control commit, but still need an archived previous version and an operation record.

## Logs and concurrent updates

Append JSON Lines to `logs/<agent-id>.jsonl`. Each line is one event; use a fresh UUID. The union of these per-agent files is the area's operation log. Only that agent appends to its log. Reading a log does not modify it. Directory structure is deliberately split by sender to reduce collisions.

Required operation fields: `id`, `at`, `agent`, `member`, `acting_tier`, `action` (add/update), `path` (repository relative), `summary`, `base_commit`, `old_sha256`, `new_sha256`, `archive`, `restore`. An add has no old hash or archive. A replacement's archive must exactly match the version in the parent commit. The helper fills these fields.

Before replacing a shared file, read its latest remote version and relevant messages. Discuss changes that alter an agreed assumption or another member's conclusion. Archiving protects recoverability; it does not make an unagreed decision a group decision. If an update becomes stale during a rebase, merge the substance first, then regenerate its archive and unpublished log entry against the new parent.

## Shared results and dependencies

Include meaning, units, provenance, applicable assumptions, status and how to reproduce a result. Label proposals explicitly. Pin important cross-tier inputs to a path and Git commit or content hash. The producer announces a changed interface; the consumer decides when to adopt it. Do not silently rewrite the other tier's baseline.

Messages requesting work or review belong in `../agent_message/`, following that area's protocol. An agent's workspace is readable for context, but its files remain owned by that member. A public copy is a separate artifact and must cite its source.
