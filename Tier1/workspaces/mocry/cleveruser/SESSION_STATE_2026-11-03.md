# Clever User harness session — resumable state

Agent: `mocry-cleveruser` · Member: `mocry` (Ran Min / GitHub `MocryMin`) · Model: deepseek-v4.1-flash 1017 · Harness: Clever User (build not exposed) · Registered 2026-11-03T19:0xZ, registration commit `66d7c8a`.

This subfolder is this agent's own writing area inside member `mocry`'s workspace, kept separate from `mocry-codex` material. `mocry-codex` remains the maintainer agent; nothing here is a group decision or a revision of its publications.

## What this session has done

1. Cloned the repository and read: `AGENTS.md`, `agent_protocol.md`, root `README.md`, `PROJECT.md`, both tiers' `public/agent_skill_protocol.md` and `agent_message/agent_skill_protocol.md`, `Tier1/public/PROJECT_SCOPE.md`, `Tier2/public/PROJECT_SCOPE.md`, all of `Tier1/public/baseline_1103/` (INDEX, BASELINE_1103, GAPS, TEACHER_CLARIFICATIONS, TEACHER_ORIGINAL_EXCERPTS, RESEARCH_REQUEST), the v1.1 research release README and `EXECUTIVE_SUMMARY_EN.md`, and the six published Tier1 messages (all seen, see below).
2. Registered as a second, concurrent agent of member `mocry` under a different harness, per the root bootstrap instruction: setup, `register`, one registration commit, helper checks and `19` tool regression tests passed, pushed as `5edc7d4..66d7c8a`.
3. Local clone note: `origin` was switched to `git@github.com:MocryMin/mmcs-group15-project.git` because HTTPS push could not authenticate non-interactively in this shell while the machine's SSH identity (`gh` reports git protocol SSH, `Hi MocryMin!`) works. Pull requests, branches and history were untouched.

## Seen message checkpoint

`d000f731b5e84c8091b877d464b3536a`, `9a14b411d65745efa6caec11dd8a8d69`, `6e5538392d904dc2b395b7e4fff01bde`, `f5bee2e6ae1c4cee93a6ba845d0b07cc`, `3c584488cd574978828f7db7c13a4508`, `3d77da4be9d04bc4b5ebf9aa0a098071`.

## Verified project state (as read at 2026-11-03T19:00Z, commit 5edc7d4)

- Tier1: Open only so far. Baseline 1103 (model family BL-01..BL-15, gaps M/E/B/H/F/D/V/X/Q, A/B four-way comparison A0/A1/B0/B1) and the controller-reviewed research release `20261103-v1.1` exist as proposals. The release gives typed parameters (`BASELINE_CANDIDATE.json`) for market, battery, electrolyser/H2 and finance/data.
- No optimisation code, no solved investment result and no tier-wide agreed parameterisation exist in the repository yet. `.py` content in the repo is only `tools/collab.py` and its tests.
- Tier2: scaffold only; the extension route (Tier2A generation investment vs Tier2B strategy/operation through time) is explicitly not chosen, and no Tier2 decision, interface or dependency is recorded.
- Membership: only member `mocry` has registrations (`mocry-codex`, and now `mocry-cleveruser`). No other members are registered, so group adoption of any baseline cannot be evidenced yet.
- The 2026-11-03T13:39:02Z request asked Ran Min to dispatch independent researchers including "DS v4.1 flash1017/Clever User"; the v1 research round was completed by other models and explicitly claims no Clever User result. This session therefore has a standing, unfilled invitation to contribute independent Tier1 research.
- Root inputs: five unchanged CSVs, brief PDF, two transcripts, `SOURCE_MANIFEST.json`. Report due 27 Nov 2026 10:00 Europe/London; presentation 30 Nov 2026.

## Open items owned by the human (Ran Min), not decided here

1. Whether this agent should now produce independent Tier1 research (which packages R1/R2/R3/R4, or instead the model/optimisation) and at what depth.
2. Whether the group commits to Baseline 1103 as the working baseline, and how other real members are invited/onboarded.
3. Tier2 route choice and who owns it; until chosen, Tier2 work stays provisional.
4. Report/pitch scope limits (ten-page limit, reference/appendix counting) — course rules are unresolved in the repository.

## Next safe actions for this agent

- Stay inside `Tier1/workspaces/mocry/cleveruser/` for drafts; publish new uniquely named public artifacts through `tools/collab.py publish`; send messages for coordination, not for routine status.
- Do not overwrite `mocry-codex` publications, root infrastructure, or `Tier1/public/baseline_1103/` current files; add versioned/correction artifacts and message the maintainer instead.
- Any claim about the datasets or parameters must be reproduced from the repository inputs or cited to a public source with units and date; this session has not independently re-verified the v1.1 parameter values yet.
