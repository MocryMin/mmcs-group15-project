# MMCS Group 15 — shared project

Maintainer: **Ran Min** · GitHub `MocryMin` · member ID `mocry` · agent ID `mocry-codex`.

Each person works with their own AI assistant and local clone. Assistants coordinate through versioned files in this repository. Humans decide direction and resolve important choices; assistants maintain the project state, exchange requests and carry out agreed work.

This repository is public. The project overview, original brief PDF and five supplied CSVs are now shared at the root at the repository owner's explicit request. Read [PROJECT.md](PROJECT.md) and [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json) for their meaning and provenance. Preserve the supplied files; publish processed versions separately. Keep credentials, personal information and unrelated materials out of Git.

The current Tier1 discussion package is [Baseline 1103](Tier1/public/baseline_1103/INDEX.md): teacher source wording and interpretations, an information-gap register, the deterministic A/B baseline proposal, and research requests. It is open to all members' comments and independent research.

## Start here

Give your assistant the repository URL and this instruction:

> Read AGENTS.md and agent_protocol.md. Register me and this assistant using my chosen nickname, a unique member ID and agent ID, and the actual model/harness information you can verify. Set up my workspaces in both tiers and the local pre-push check. Read the relevant public rules and messages, then tell me the next decision or action that needs my attention. Do not invent my identity, model version or an agreed project decision.

中文：将仓库链接交给自己的 agent，让它先读 `AGENTS.md` 和 `agent_protocol.md`，再注册、建立工作区并接手协同；成员无需手工维护消息和日志。

Requirements for the helper: Git and Python 3.10 or newer, with no third-party Python packages. A public repository can be cloned by anyone. To push, the repository owner must first grant your GitHub account collaborator access. Do not share account credentials. The bootstrap does not invite unnamed teammates.

```text
agent_protocol.md                 Global rules and append-only registration events
PROJECT.md                        Project overview and input guide
Project_Brief.pdf                 Original six-page project brief
daily_*.csv / wind_farm_generation.csv  Five original input datasets
SOURCE_MANIFEST.json              Sources, dates, hashes and data inventory
Tier1/
  public/                         Shared current artifacts, immutable archives, logs
    agent_skill_protocol.md
    logs/<agent-id>.jsonl
    archive/<event-id>/<path>
  agent_message/                  Immutable messages and per-sender logs
    agent_skill_protocol.md
    messages/<time>_<agent>_<uuid>.md
    logs/<agent-id>.jsonl
  workspaces/<member-id>/          Member-owned working files
Tier2/                            Same structure; its work is independently managed
tools/collab.py                    Registration, publishing, messaging, checks, push
.githooks/pre-push                 Local check installed by setup
```

## First session

Choose lowercase IDs such as `alex` and `alex-codex`; an ID is not a real name. The assistant should use the actual details of its session, or explicitly record `unknown`. The examples below are commands for the assistant to adapt, not registrations for fictitious members.

```sh
git clone https://github.com/MocryMin/mmcs-group15-project.git
cd mmcs-group15-project
python tools/collab.py setup --agent alex-codex
python tools/collab.py register --member alex --agent alex-codex --nickname Alex --model unknown --model-version unknown --harness "Your assistant application" --harness-version unknown
git add agent_protocol.md Tier1/workspaces/alex Tier2/workspaces/alex
python tools/collab.py commit --tier registration --message "Register Alex and assistant"
python tools/collab.py push
```

Set your local Git author to your own GitHub identity, preferably a GitHub noreply address, before committing. `setup` does not change your author. Existing agents run `setup` after cloning and do not register a second identity unnecessarily. A later model/harness change uses `register --update`; it appends an event.

## Daily work

1. Start with a clean working tree, `git fetch origin`, then `git rebase origin/main`. Read the new registration events, both tiers' public changes and the messages relevant to you. Follow the detailed zone protocols.
2. Work freely in your own tier workspace. Promote a result with `publish`; send a request, reply or announcement with `message`. Both create their required log records.
3. Stage explicit paths. Use `commit --tier Tier1` or `--tier Tier2`. A commit has one acting tier; cross-tier additions belong to the receiving public area and must still declare their source tier.
4. Run `push`. It fetches and checks whether your commit contains the latest remote head. If another agent pushed first, it stops without changing your work. Rebase unpublished commits, resolve any conflict preserving both agents' additions, validate, then retry.

```sh
python tools/collab.py publish --tier Tier1 --area Tier1 --path findings/baseline.md --source Tier1/workspaces/alex/baseline.md --summary "Publish baseline and its assumptions"
python tools/collab.py message --tier Tier1 --area Tier2 --to mocry-codex --body-file Tier1/workspaces/alex/request.md --kind request --priority action
git add Tier1/public/findings/baseline.md Tier1/public/logs/alex-codex.jsonl Tier2/agent_message
python tools/collab.py commit --tier Tier1 --message "Share baseline and request Tier2 comparison"
python tools/collab.py push
```

After a public update, also stage the newly generated archive. Use one update per public path per commit. If you made an error before committing, reconcile your own uncommitted work; never remove a published log entry or archive. To restore an older public file, pass the archive as `--source` to `publish`: restoration becomes a new recorded update.

## Branches and checks

`main` is the shared integration branch and the only branch published by this workflow. Short-lived local branches are optional for larger proposals; integrate their commits onto local `main` before publishing. There are no permanent branches per member or tier. Publish only ordinary fast-forward pushes; never force-push or delete `main`. Rebase only commits that have not been published. Do not squash away registration, message or audit history. A merge commit is not accepted by the local checker; rebase the local work instead.

The helper checks ownership, immutable messages/archives, append-only logs, message recipients, registration history, public update archives and cross-tier rules. Run its regression tests with `python -m unittest discover -s tools -p "test_*.py"`.

GitHub protection on `main` disables force pushes and branch deletion and requires linear history, including for administrators. Ordinary direct pushes remain available to collaborators; pull requests are not required by this workflow. These settings were verified during setup on 2026-11-03.

GitHub write permissions apply to the whole repository. The local hook is a cooperative check, not access control: a writer can bypass it or use GitHub's web editor. Install it in every clone and avoid web edits. Protocol/tool changes are maintainer control commits. Root course inputs are preserved originals; propose corrections through public artifacts and messages rather than replacing them. See [the global protocol](agent_protocol.md) for governance and conflict recovery. No background agent, automatic reminder or hosted CI service is implied by this repository.
