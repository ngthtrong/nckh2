# ISDS-2026 camera-ready workspace

This is the status entry point for paper 6444. Work continued from branch
`clean` at `edefb9c`; the submitted archive remains tag `v1.0.1` (`be95d4c`).
The manuscript contains the final scientific design and evidence, not the
review or revision history.

## Current state

- Both RQ1 stress runs pass independent numerical audit: 280 checkpoints,
  1,400 fits, 92,617 mappings, 35 summaries, and 300 paired effects per run.
  The first run is the fixed manuscript source; v2 is an unpooled replication.
- The 43 changed ARI rows are confined to graph methods under 2x copies. The
  major GPS, time-noise, and 5x conclusions are unchanged.
- The manuscript defines all equation variables, uses a validated 30-cell
  vector heatmap and a two-panel descriptive RQ3 figure, and has eight authors
  and one corresponding author with an explicit email. The strict component
  bound excludes singletons, and Results separate clustering, ranking,
  dispatch, and sensitivity claims.
- The public `clean` branch was verified at `5fad10d`; it contains the two RQ1
  stress artifacts, which remain separate from release `v1.0.1`.
- Source packaging and alt text are prepared. The edited source and a fresh
  ZIP extraction pass the available Tectonic build at 15 pages. The required
  XeLaTeX/BibTeX four-command build must be repeated in a TeX Live environment
  before upload. Signed LTP, author approval, and upload remain external gates.
- Package provenance is still open for both original ZIP files, runtime/resume
  history, and the v2 executed notebook.

## Working files

- `RQ1_STRESS_AUDIT.md`: reproducible two-run numerical/provenance audit.
- `RQ1_STRESS_RUNBOOK.md`: returned-run status and future-rerun boundary.
- `REVISION_TRACKER.md`: internal evidence and publication decision tracker.
- `SUBMISSION_CHECKLIST.md`: EasyChair fields, package contents, and final gates.
- `FIGURE_ALT_TEXT.md`: alt text for the three final figures.
- `REVIEWER_RESPONSE.md`: internal draft only; submit only if requested.
- `../../temp-plan.md`: implementation status and owner handoff.
- `../checkpoints/2026-09-11-04-ltp-metadata-prepared.md`: latest checkpoint.

No commit, push, public release, registration, LTP signature, or EasyChair
upload is performed by this workspace update.
