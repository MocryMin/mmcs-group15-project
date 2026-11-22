# MMCS Group 15 — shared project

Maintainer: **Ran Min** · GitHub `MocryMin` · member ID `mocry` · agent ID `mocry-codex`.

Each person works with their own AI assistant and local clone. Assistants coordinate through versioned files in this repository. Humans decide direction and resolve important choices; assistants maintain the project state, exchange requests and carry out agreed work.

This repository is public. The project overview, original brief PDF and five supplied CSVs are now shared at the root at the repository owner's explicit request. Read [PROJECT.md](PROJECT.md) and [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json) for their meaning and provenance. Preserve the supplied files; publish processed versions separately. Keep credentials, personal information and unrelated materials out of Git.

The original project overview records the starting context. Use the dated research summaries below to find the later outputs and their status.

## Start here

Give your assistant the repository URL and this instruction:

> Use the lightweight clone below. Read AGENTS.md, agent_protocol.md and the research summaries relevant to my work. Register me and this assistant using my chosen nickname, a unique member ID and agent ID, and the actual model/harness information you can verify. Set up my workspaces in both tiers and the local pre-push check. Read the relevant public rules and messages, then tell me the next decision or action that needs my attention. Do not invent my identity, model version or an agreed project decision.

将仓库链接交给自己的 agent，按下面的轻量克隆方式获取 brief、协作规则和研究摘要，再按任务选取正文、代码或数据。

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

### Clone the brief and research summaries

```sh
git clone --filter=blob:none --no-checkout --no-tags --single-branch --branch main https://github.com/MocryMin/mmcs-group15-project.git
cd mmcs-group15-project
git show HEAD:tools/review-sparse-paths.txt | git sparse-checkout set --no-cone --stdin
git checkout main
```

The initial checkout includes the original brief, the source inventory, the collaboration tools and logs, and the summary pages below. Full reports, message bodies, CSVs, weights and archives are downloaded when you select them. GitHub's Clone command needs the options above for this behaviour.

| Topic | Summary available after checkout |
|:--|:--|
| Course materials | [Brief](Project_Brief.pdf) and [course reference index](Tier1/public/reference/course-project-materials-20261122/README.md) |
| Data repair | [Issues, sources and fixes](Tier1/public/data_quality/full_data_repair/20261104-v2/REPAIR_SUMMARY_ZH.md) |
| Tier 1 | [Initial assumptions and research requests](Tier1/public/baseline_1103/INDEX.md), [13 November study history](Tier1/workspaces/mocry/codex/work-history/20261113-v1/README.md), [22 November report candidate notice](Tier1/public/updates/20261122-tier1-report-v5-review.md) |
| Tier 2B forecasting | [13 November study history](Tier2/workspaces/mocry/codex/work-history/20261113-v1/README.md), [v1 feature research](Tier2/workspaces/mocry/codex/work-history/20261119-in-12h-exact-v1/README.md), [v2 architecture research](Tier2/workspaces/mocry/codex/work-history/20261119-in-12h-exact-v2/README.md), [released model cards and weights index](Tier2/public/models/README.md) |
| Tier 2B dispatch and follow-up research | [22 November archive summary and selective restore instructions](Tier2/workspaces/mocry/codex/work-history/20261122-post-v2/README.md) |

Select a file by its repository path, starting with `/`. For example, this adds only the Tier 1 candidate PDF.

```sh
git sparse-checkout add -- '/Tier1/workspaces/mocry/codex/technical-report-latex/20261122-v5/report.pdf'
```

A trailing `/` adds a folder with its descendants. For binary archives, select the ZIP or all parts of the specific ZIP group you need. Read the archive summary first to identify the group.

### Register a new agent

Choose lowercase IDs such as `alex` and `alex-codex`; an ID is not a real name. The assistant should use the actual details of its session, or explicitly record `unknown`. The examples below are commands for the assistant to adapt, not registrations for fictitious members.

```sh
git sparse-checkout add -- '/Tier1/workspaces/alex/' '/Tier2/workspaces/alex/'
python tools/collab.py setup --agent alex-codex
python tools/collab.py register --member alex --agent alex-codex --nickname Alex --model unknown --model-version unknown --harness "Your assistant application" --harness-version unknown
git add agent_protocol.md Tier1/workspaces/alex Tier2/workspaces/alex
python tools/collab.py commit --tier registration --message "Register Alex and assistant"
python tools/collab.py push
```

Set your local Git author to your own GitHub identity, preferably a GitHub noreply address, before committing. `setup` does not change your author. An already registered agent runs `setup` after cloning. For an established workspace with large archives, select the exact working files or subfolders needed for your assignment. A later model or harness change uses `register --update` and appends an event.

## Daily work

1. Start with a clean working tree and `git fetch --no-tags origin main`. Preview changed paths with `git diff --name-status --no-renames HEAD origin/main`. Use `git merge --ff-only origin/main` to catch up when there are no unpublished commits. Rebase unpublished work if necessary. Read new registration events, public changes and relevant messages.
2. Work freely in your own tier workspace. Promote a result with `publish`; send a request, reply or announcement with `message`. Both create their required log records.
3. Stage explicit paths. Use `commit --tier Tier1` or `--tier Tier2`. A commit has one acting tier; cross-tier additions belong to the receiving public area and must still declare their source tier.
4. Run `push`. The installed hook validates the unpublished commits against the remote tip from the push connection. If another agent pushed first, fetch, rebase unpublished commits, and resolve any conflict preserving both agents' additions before retrying.

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
