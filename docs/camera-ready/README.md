# ISDS-2026 camera-ready workspace

This directory tracks the revision of submission 6444 from the submitted
`v1.0.1` artifact. The working manuscript is `paper/main.tex` on `clean`.

The conference email gives 16 September 2026 as the camera-ready and
registration deadline. Page limits, upload contents, and response-letter
requirements remain pending the conference's follow-up instructions.

## Current state

- The paper now defines the named clustering variants, explains comparator
  roles, corrects the top-k pseudocode, documents the separate tuning grids,
  and limits the matched-density interpretation.
- Existing RQ2/RQ3 evidence was checked against its SHA-256 manifests. The
  paper now summarizes all 11 RQ2 stress scenarios and all three RQ3 resource
  scenarios without changing the primary 40-seed inference.
- The supplementary RQ1 reviewer stress experiment is prepared as a Colab
  notebook. Its results are pending a group-run artifact and are not claimed
  in the manuscript.
- The RQ1 rerun package pins source/configuration snapshot `6ac75c2`, validates
  the tracked result files, and refuses to aggregate while a failure log is
  non-empty.
- `paper/main.pdf` builds successfully at 15 pages with hidden link borders;
  the conference's final camera-ready rules still need to be applied when sent.
- Author, corresponding-author, and funding changes after `v1.0.1` are group
  confirmed and retained.

## Files

- `REVISION_TRACKER.md`: comment-to-change evidence and open gates.
- `REVIEWER_RESPONSE.md`: English response draft.
- `RQ1_STRESS_RUNBOOK.md`: instructions for the group member running Colab.
- `../checkpoints/2026-09-08-01-isds-camera-ready-revision.md`: reproducible
  handoff checkpoint.

Do not mark the supplementary experiment complete until its ZIP and executed
notebook pass the checks in the runbook. Submission, registration, and a new
release are outside this workspace update.
