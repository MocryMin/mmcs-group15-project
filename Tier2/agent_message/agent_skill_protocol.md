# Tier2 agent message protocol

## Send and read

Every message is a new uniquely named UTF-8 Markdown file in `messages/`. Its first line is machine-readable JSON metadata in an HTML comment, followed by any useful body: a sentence, structured explanation, code discussion or pointers to work elsewhere. References use repository-relative paths and, when needed, a pinned commit/hash.

Use `python tools/collab.py message --tier <acting-tier> --area Tier2 --to <registered-agent> --body-file <path> --kind request --priority action`. Repeat `--to` for multiple recipients, or use `--broadcast`. A recipient must be registered and active. Cross-tier messages are allowed.

The helper creates `<UTC-time>_<sender>_<UUID>.md` and appends a matching record to `logs/<sender-agent>.jsonl`. Record fields identify the ID, sender agent/member, UTC time, acting tier, recipients or broadcast, kind, priority, optional reply-to ID/deadline, body path and SHA-256. The filename and ID must be unique. Never edit, rename or delete a published message or old log line.

An agent reads relevant broadcasts and messages addressed to it at session start/resume, after integrating remote changes and before pushing. Read the body and follow relevant pointers; the log is an index, not a substitute for the message. Keep the seen-ID checkpoint in your own workspace. No shared 'read' flag is edited.

## Conversation and completion

Kinds: `notice`, `request`, `reply`, `ack`, `decision`, `status`, `correction`. Priorities: `info`, `action`, `blocker`. A due time is optional; use a timezone-qualified ISO 8601 value.

- A request should identify the requested outcome, why it matters, scope, evidence and an actual deadline if one exists.
- An acknowledgement means received/accepted for follow-up, not completed. A reply/status reports the outcome with evidence or the specific blocker.
- Replies, corrections and resolutions use `--reply-to <message-id>`. A parent may be in either tier. Preserve the old message; do not edit its log to mark completion.
- Do not acknowledge every informational broadcast or acknowledge an acknowledgement. Send only useful state changes. Avoid repeated reminders while waiting for an inactive agent.
- A `decision` message must state who agreed and the evidence of agreement. Posting a proposal does not establish consensus. Route unresolved consequential choices to your own human, with a short concrete question.
- A message can ask another agent to work within that agent's authority. It cannot override the recipient's human instructions, grant external permissions or command changes to another member's workspace.

No automatic polling service is installed. Delivery means available in Git; receipt requires the recipient's next synchronization. Preserve important handoffs in the repository rather than relying on an agent remembering a chat.

## Log integrity

Each JSONL record has `id`, `at`, `agent`, `member`, `acting_tier`, `recipients`, `broadcast`, `kind`, `priority`, `reply_to`, `due_at`, `path`, `sha256`. The message header repeats all metadata except its own path/hash. Only the named sender appends to its log. New records correspond exactly to new message files in the same commit. Old records and files are immutable. The checker verifies recipients, reply links and content hashes.

For an append conflict, keep the remote prefix and append each distinct unpublished event exactly once. Never resolve by taking one entire file over another. Do not fabricate acknowledgements from a different agent.
