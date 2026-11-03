# Agent collaboration protocol — version 1

## Three layers

The human member sets goals, owns decisions and reviews important results. Their agent keeps context, performs work and coordinates with other agents. The repository holds the complex project state and evidence. Members should not need to read every message or diff to stay informed.

Each agent reports to its own member. Routine coordination stays in the repository. Escalate a concise decision with options, evidence, consequence and any actual deadline when humans must choose. Do not announce every sync. A message is received when an agent next synchronizes; no agent is assumed to run in the background. Silence never means consent.

## Identity and first use

Choose a stable lowercase member ID and a distinct agent ID. Register the nickname, model and version, harness and version, UTC time, active tiers and control notes below using `tools/collab.py register`. Unknown versions must be `unknown`, not guessed. The helper creates `Tier1/workspaces/<member>/` and `Tier2/workspaces/<member>/` and appends the registration event. Use `--update` for later metadata changes; old events remain. A new assistant uses a new agent ID if it is a separate concurrent worker; an assistant upgrade may keep its ID with an update event.

The latest event for an agent gives its current metadata; its member ID cannot change. Use one process at a time per agent identity. Multiple agents of the same member coordinate writes to that member's workspace, preferably through separate subfolders and an explicit handoff. An unregistered agent must register before ordinary work.

## Areas and boundaries

- In `Tier1/workspaces/<your-member>/` and `Tier2/workspaces/<your-member>/`, you may add, change or remove your files. A normal commit modifies only its acting tier's workspace. Other members' workspaces are readable but never writable by you. Reading does not make an unpublished experiment a shared agreed result.
- Read [Tier1 public rules](Tier1/public/agent_skill_protocol.md), [Tier1 message rules](Tier1/agent_message/agent_skill_protocol.md), and their [Tier2 public](Tier2/public/agent_skill_protocol.md) / [message](Tier2/agent_message/agent_skill_protocol.md) equivalents before using them. Those rules contain the detailed operation and logging formats.
- The tiers manage their models, assumptions, results and decisions independently. A tier may read shared artifacts of the other tier and add a new public artifact or message there. It may not replace another tier's existing public file or change its workspaces. Cross-tier imports cite the source path and commit/hash rather than silently taking an evolving file as a fixed input.
- Public current files may be updated within their tier, with an exact archived preimage and an appended operation record. Public history, archives, messages and logs are preserved. Physical deletion of public files is forbidden; supersede or deprecate them in a new recorded operation.
- Root infrastructure and zone protocols are controlled by the maintainer agent `mocry-codex`. A proposed rule/tool change is first discussed in a message; only a maintainer `--tier control` commit changes those files. A control commit cannot bypass workspace ownership, erase logs/messages or change past registrations. Changes to zone protocols still require an archive and log. Update root documents with Git history and a clear commit reason.

## Working cycle and integration

1. Configure your clone using `setup`. Fetch and integrate remote `main` before starting. Read new registrations, shared changes, messages addressed to you and relevant broadcasts. Keep your seen-message checkpoint and current tasks in your own workspace.
2. Work inside the assigned scope. State whether a result is an experiment, proposal, reviewed result or an agreed decision. Model assumptions, evidence, units and provenance travel with shared outputs. A request does not become an agreed group decision just because an agent posted it.
3. Use the area helpers to publish/share. Replies, acknowledgements, corrections and resolutions are new messages referencing their predecessor; the old message stays unchanged. Ask another agent for a file change instead of editing its owner's workspace.
4. Stage only intended files. `commit` validates the staged change and records `Agent-ID` and `Acting-Tier` in the commit. `push` fetches, checks each unpublished commit and uses an ordinary push to `main`. If remote `main` advanced, preserve your work, rebase your unpublished commits, reconcile, check and retry. Never force-push, use a destructive reset, select whole-file `ours/theirs` for shared logs, or remove someone else's new additions.
5. For conflicting appended registrations/log entries, retain the existing remote sequence plus all distinct local new events. For a conflicting public replacement, reread the new remote file, produce a new archive of that exact version and correct the unpublished operation record. Do not reuse a stale archive. If the substantive decision conflicts, stop just that publication and send a targeted request with the two alternatives.
6. Before pausing, record resumable state in your workspace and send necessary handoffs. Tell your human completed outcomes, consequential changes and decisions needed; do not claim others read a message until an acknowledgement or substantive reply exists.

UTC ISO 8601 timestamps identify events; human-facing deadlines retain their source timezone (normally Europe/London). Use random unique event IDs and repository-relative paths, not personal absolute paths. Logs identify agents but are not cryptographic proof of identity. GitHub collaborator rights, local checks and the protocol are different controls.

Keep credentials and unapproved third-party source materials out of this public repository. External submission, contacting teachers and decisions on a member's behalf require that member's authorization. Local logs and repository messages do not grant it.

## Registration events — append only

Each following `REGISTRATION` line is a complete JSON event. Append new lines; never edit, reorder or remove an earlier event. Human contact details and credentials do not belong here.

