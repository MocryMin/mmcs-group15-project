# Independent first-pass research — common instructions

Date: 2026-11-03. Issued by the registered agent `mocry-cleveruser` (member `mocry`, human owner Ran Min / GitHub `MocryMin`) for the MMCS Group 15 project. Status: internal instruction to researcher workers; it is not a shared group decision.

## What this work is

The project asked for **targeted independent research and cross-validation** in four packages (see `inputs/RESEARCH_REQUEST.md`). Another research round was already run inside this repository by other models. To get genuinely independent evidence, **your first pass must be produced without seeing that round.** This is a deliberate unleaky replication of the same research question.

## Absolute leak control — read this twice

You may read:

- every file inside `Tier1/workspaces/mocry/cleveruser/inputs/` (byte-identical copies of the course question and supplied inputs), and
- the files you create in your own package folder.

You must not read, grep, list or open:

- anything under `Tier1/public/research_1103/` (the earlier research round, its syntheses, parameter candidates, review decisions, cross-reviews or first passes);
- any other folder under `Tier1/workspaces/mocry/cleveruser/firstpass/` (other researchers' first passes);
- `Tier1/workspaces/mocry/` files created by `mocry-codex` other than the input copies you were given.

If you believe you have seen such content, stop using it and say so explicitly in `FIRST_PASS.md`. Do not browse the repository "for context": the only project context you may use is the input bundle. External public sources (web) are allowed and expected.

## The question you are answering

Read, in this order: `inputs/PROJECT.md`, `inputs/brief_extracted_text.md` (page-marked text extract of `Project_Brief.pdf`; the PDF itself is the authoritative input), `inputs/TEACHER_ORIGINAL_EXCERPTS.md`, `inputs/TEACHER_CLARIFICATIONS.md`, `inputs/GAPS.md`, `inputs/BASELINE_1103.md`, and your package section in `inputs/RESEARCH_REQUEST.md`. `inputs/RESEARCH_RESULT_TEMPLATE.md` defines the result form.

Your own package is stated in your task message. Do not silently expand into the other packages; note crossing findings briefly and stay accountable for your own.

## Deliverables

Write into your package folder (`Tier1/workspaces/mocry/cleveruser/firstpass/<package>/`):

1. `REPORT.md` — readable report following the sections of `RESEARCH_RESULT_TEMPLATE.md`. English. Cover the gap IDs of your package item by item, including the ones you could not close.
2. `parameters.json` — machine-readable claims: for each claim an `id`, `gap_id`, meaning, value or rule, unit, currency and price year, applicable scope, source reference, evidence strength, recommended baseline value and sensitivity range. Use typed numbers, not strings, where the quantity is numeric.
3. `sources.json` — one entry per source: publisher, title, URL, document type, access date and time (UTC, as observed), the locator you actually read (page/section/table/cell), a short verbatim quote (≤ 25 words) that you actually saw, and what it supports.
4. `FIRST_PASS.md` — declaration: researcher identity (model as configured, harness, harness build if exposed), UTC timestamps, package, explicit statement of which peer/earlier findings you did or did not see, and the list of sources you tried and failed to obtain.

## Evidence rules

- Prefer primary material: market/regulatory documents, manufacturer datasheets and price lists, official statistics, government publications, peer-reviewed or official technical studies. Secondary commentary is allowed only when labelled as such.
- Every number carries a unit, a currency/price year where relevant, and a scope statement (equipment-only vs installed; nameplate vs usable; wholesale vs supported price; national vs site).
- Show the arithmetic for every conversion (currency, price year, MW↔MWh, kWh/kg, efficiency, usable window, per-MW vs per-MWh).
- Do not invent quotes, prices or page numbers. If you cannot obtain a document (paywall, broken link, login), record the attempt and keep the value explicitly uncertain.
- Do not count several websites repeating one original source as independent confirmation; trace to the original.
- Separate: observed fact from a source, your own inference, and a modelling choice recommended to the team.
- Say plainly when the honest answer is a bounded range or "no usable public number obtained".

## Working conventions

- The system clock reads 2026-11-03; the public web will show the real-world state you find. Record the access date you actually observe and note any mismatch with the project timeline rather than editing either.
- Units: keep source units in the evidence table and give the converted value separately.
- Keep files UTF-8, LF or CRLF both acceptable; no non-ASCII smart quotes in JSON.
- Do not publish to `Tier1/public/**`, do not commit, and do not push: the controller agent reviews your first pass and handles publication through the collaboration helper.
