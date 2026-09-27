# Checkpoint: ISDS-2026 camera-ready reviewer revision

Date: 2026-09-08 UTC

## Baselines

- Submitted artifact: tag `v1.0.1`, commit `be95d4c`.
- Working branch: `clean`.
- Pre-revision working commit: `d73549b`.
- Historical generator/external-benchmark source:
  `a6be3e988dad1aa442c8c8e158c2bba96b2b7fb9`.
- Exact RQ1 clustering notebook/configuration snapshot:
  `6ac75c202d04934deb46d84486132e54d42d735f`.
- Working tree was clean before this revision.

## Confirmed decisions

- Keep the eight-author metadata, corresponding authors, and funding text in
  the current manuscript.
- Correct paper descriptions against the code that generated the results.
- Prepare heavy experiments for a group member to run in Colab; do not execute
  the 1,400-fit supplementary batch locally.
- Treat 16 September 2026 as the deadline stated by the acceptance email while
  waiting for the conference's formatting and upload instructions.

## Completed work

- Defined product/additive method names and explained baseline roles.
- Corrected the top-k pseudocode and documented the actual separate Product
  and Additive tuning grids.
- Limited the matched-density interpretation to a non-causal density-control
  diagnostic.
- Added a source-faithful data construction/representativeness table.
- Added descriptive summaries for all 11 RQ2 robustness scenarios and all
  three RQ3 resource conditions.
- Verified every file listed in the RQ2 and RQ3 SHA-256 manifests. Verified the
  seed-level RQ3 provenance for 40 paired seeds.
- Added the reviewer tracker, English response draft, Colab notebook builder,
  generated notebook, and group runbook.
- Rebuilt `paper/main.pdf` successfully as a 15-page XeLaTeX-compatible PDF;
  no undefined citations/references or overfull boxes remain in the build log.
- Checked the public Copernicus EMSR848 and WorldPop records on 2026-09-08;
  the paper does not infer row-level provenance from those live pages.

## Limitations and open gates

- Supplementary RQ1 stress results are pending the group's Colab run. No
  result from that protocol has been inserted into the paper or response.
- Raw upstream geographic snapshots, their original checksums, and per-row
  lineage are unavailable.
- Camera-ready page limit and required upload files remain unknown. Final page
  and line references in the reviewer response therefore remain pending.
- This checkpoint does not submit the manuscript, register the paper, create a
  release, or push a commit.

## Next concrete task

Give the group `RQ1_Reviewer_Stress_Colab.ipynb` and the runbook. When the ZIP
returns, validate its manifest and completeness before integrating any result.
