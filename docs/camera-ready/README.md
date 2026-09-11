# ISDS-2026 camera-ready workspace

This directory tracks the camera-ready state of submission 6444 from the
submitted `v1.0.1` artifact. The working manuscript is `paper/main.tex` on
`clean`; the current integration baseline is commit `9fbc49c` (`CR_0.1`).

The conference email gives 16 September 2026 as the camera-ready and
registration deadline. Page limits, upload contents, and response-letter
requirements remain pending the conference's follow-up instructions.

## Current state

- The paper defines the named clustering variants, explains comparator roles,
  corrects the top-k pseudocode, documents the separate tuning grids, and
  limits the matched-density interpretation.
- Existing RQ2/RQ3 evidence was checked against its SHA-256 manifests. The
  paper now summarizes all 11 RQ2 stress scenarios and all three RQ3 resource
  scenarios without changing the primary 40-seed inference.
- The fixed RQ1 clustering stress run has returned. Its 288 manifest hashes,
  280 checkpoints, 1,400 fits, 92,617 duplicate mappings, 35 summaries, and 300
  paired bootstrap rows pass independent audit with NumPy 2.5.1. The paper now
  reports its fixed GPS, timestamp, and exact-copy conditions.
- Numerical integration is complete. Package provenance remains open because
  the original ZIP is absent and the group has not confirmed whether a
  checkpoint was resumed across a Colab runtime change. The executed run used
  Python 3.13.15; that version appears in the manifest but was not included in
  the returned protocol hash.
- `paper/main.pdf` builds successfully with hidden link borders. The integrated
  draft is 17 pages; a measured 15-page layout that removes two redundant
  figures and one redundant headline table is awaiting author approval.
- Author, corresponding-author, and funding changes after `v1.0.1` are group
  confirmed and retained.

## Files

- `RQ1_STRESS_AUDIT.md`: reproducible numerical and provenance audit.
- `REVISION_TRACKER.md`: evidence-based assessment and open gates.
- `REVIEWER_RESPONSE.md`: internal English response draft, used only if the
  conference or author group requires it.
- `RQ1_STRESS_RUNBOOK.md`: locked protocol, returned-run reconciliation, and
  future rerun instructions.
- `../checkpoints/2026-09-11-01-rq1-stress-integration.md`: current handoff
  checkpoint.

Submission, registration, archival release creation, and push are outside this
workspace update. The group tasks and completion criteria are recorded in the
current checkpoint.
