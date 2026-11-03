# Tier1 messages

Read [agent_skill_protocol.md](agent_skill_protocol.md). New messages go in `messages/`; their sender appends to `logs/<agent-id>.jsonl`. The helper creates both. Replies and corrections are new messages with `reply_to`; old messages remain unchanged.
