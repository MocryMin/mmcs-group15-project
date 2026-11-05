# Tier 1 technical report — LaTeX template and 4-page cut

Published copy of my working draft (the scratch directory `release/report-template/20261105/`
is git-excluded; the bytes here are identical except for this README line and the build log,
which is not published). Two deliverables:

| file | what it is |
|---|---|
| `MMCS_TechnicalReport_template.pdf` | the template rendered, 7 pages, placeholders filled with guidance |
| `Tier1_4pp.pdf` | the Tier 1 report written into the first four pages, real numbers |
| `mmcsreport.sty` | the house style both documents share |
| `MMCS_TechnicalReport_template.tex` | authoring skeleton (12–15 page report) |
| `Tier1_4pp.tex` | the filled four pages |
| `make_fig_attribution.py` | redraws the attribution panel used in the 4-page cut |
| `figures/` | figure inputs for the 4-page cut |

## How to compile

System TeX is not installed here. A self-contained Tectonic binary was downloaded to
`.clever-user/tex/tectonic.exe` and fetches its package bundle on first use:

```
cd <this directory>
"C:\...\.clever-user\tex\tectonic.exe" -X compile MMCS_TechnicalReport_template.tex
"C:\...\.clever-user\tex\tectonic.exe" -X compile Tier1_4pp.tex
```

`\usepackage{mmcsreport}` resolves from the same directory. Page furniture (header rule,
footer rule, `n / N`) is automatic via `fancyhdr` and `lastpage`.

## Design decisions, and why

These follow the evidence collected from past MMCS reports in
`Tier1/workspaces/mocry/cleveruser/synthesis/REFERENCE_EXEMPLARS_ASSESSMENT.md` and the two
`reference_review/BATCH_*_SUMMARY.md` files:

1. **Numbers before framing.** The strongest past report opens with the numbers a reader may
   stop at. Page 1 therefore carries a four-figure strip and a one-paragraph decision box
   before any prose.
2. **A validation ladder.** Baseline → rule-based → optimised → imperfect foresight, same KPIs
   down the rows. No past report did this, and it is what proves an optimiser earns its keep.
3. **Solver evidence in the body**, not an appendix: instance size, objective, wall-clock time,
   status, and a literal `N/A` where a case was not run. A table with no failed cells has not
   been tested.
4. **Sensitivity, break-even and switching points get a fixed section.** No exemplar did
   sensitivity on the decision parameters; this is the cheapest place to beat past work.
5. **Quantified concessions.** Every limitation is costed; an unquantified one reads as an
   apology.
6. **Figure-to-table ratio at least 1:1 in results.** The weakest past report had sixteen tables
   and two figures and read as a spreadsheet.
7. **Units in the column header, one fixed number of decimals per column, no vertical rules,
   captions above tables and below figures, every table with a source note.**

## Typesetting rules the style enforces

* Body face is TeX Gyre Pagella with matching maths; headings are Heros bold in one accent
  colour (`#17456B`). Loaded by file name, not by font name: on this machine fontconfig has no
  configuration file, so name lookup fails.
* **All table columns are vertically centred (`m{}`), not top-aligned (`p{}`).** Mixing
  `p{}` columns with `c` or `S` columns puts text cells on a lower baseline than numeric cells;
  the first draft of this template showed exactly that defect.
* Numeric columns are right-aligned `R{}` cells with `\num{}` for thousands separators.
  `siunitx` `S` columns were abandoned: inside `tabularx` they are not compressible and
  produced a permanent 2.6 pt overflow of the right margin.
* Section headings reserve `\sectionkeep` of vertical space, so a heading cannot be stranded at
  the foot of a page. The 4-page cut lowers this to 3.2 baselines to keep density.

## What the 4-page cut contains, and where the numbers come from

Every number in `Tier1_4pp.pdf` is from `Tier1/workspaces/mocry/cleveruser/tier1/20261105-v1`
(`results/results.json`, `results/cases.csv`, `VERIFICATION.json`), not recomputed for the
document. The 2023 generation and demand totals (215.7 and 245.8 TWh) and the unused energy
(549.9 GWh on 29 days) were re-derived directly from `data/daily_model_inputs.csv` and
`results/plans/A_0.csv` while checking the text.

One figure is redrawn: panel (a) of Figure 1 comes from
`figures/fig2_attribution_redrawn.png`, because the package version of that panel labels the
same two numbers three times (in-bar, legend-style, and a leader-line callout) and is
unreadable at page width. Same data, one label per segment; the package itself is untouched and
its caption says so.

## Status and intent

This is an offered template and a filled demonstration, not a decision about the group's
submission. It shows that the numbers in `tier1/20261105-v1` can be laid out as four pages of
a ten-page report with the validation ladder, solver evidence and sensitivity section in the
body. Whether the group adopts this style, and how the remaining six pages are allocated, is a
group decision.

## Known imperfections

* The template skeleton leaves 6–7 lines of white space at the foot of pages 1, 2 and 4. That
  is the cost of showing every structural element with short placeholder text; the real report
  fills it.
* Page 1 of the 4-page cut also ends with about six lines of white space, because §2 plus its
  first subsection would not fit.
* The system has no TeX installation; the PDFs are reproducible only while
  `.clever-user/tex/tectonic.exe` exists.
