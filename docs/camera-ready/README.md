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
  vector heatmap, removes redundant RQ2/RQ3 visuals, has eight authors and one
  corresponding author, and builds to 15 pages with Dockerized Tectonic.
- Source packaging and alt text are prepared. The extracted ZIP passes the
  XeLaTeX/BibTeX four-command build in TeX Live 2026 at 15 pages. Signed LTP,
  author approval, and upload remain external gates.
- Package provenance is still open for both original ZIP files, runtime/resume
  history, and the v2 executed notebook.

## Working files

- `RQ1_STRESS_AUDIT.md`: reproducible two-run numerical/provenance audit.
- `RQ1_STRESS_RUNBOOK.md`: returned-run status and future-rerun boundary.
- `REVISION_TRACKER.md`: internal evidence and publication decision tracker.
- `SUBMISSION_CHECKLIST.md`: EasyChair fields, package contents, and final gates.
- `FIGURE_ALT_TEXT.md`: alt text for the two final figures.
- `REVIEWER_RESPONSE.md`: internal draft only; submit only if requested.
- `../../temp-plan.md`: implementation status and owner handoff.
- `../checkpoints/2026-09-11-02-camera-ready-finalization.md`: latest checkpoint.

No commit, push, public release, registration, LTP signature, or EasyChair
upload is performed by this workspace update.
