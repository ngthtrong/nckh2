# Checkpoint: camera-ready finalization and RQ1 v2 reconciliation

Date: 2026-09-11 UTC

## Baseline, authorization, and scope

- Submitted baseline: tag `v1.0.1` at `be95d4c`.
- Working baseline at the start of this implementation: branch `clean`, HEAD
  `edefb9c`, with user changes in `remind_for_camera_ready.md`, `temp-plan.md`,
  and the new untracked `rq1_results_v2/` preserved.
- The author explicitly approved the full EasyChair/RQ1-v2 plan. This work
  audits, edits, builds, packages, and documents; it does not commit, push,
  publish, register, sign, or upload.
- No clustering batch, algorithm, selected configuration, source dataset, or
  returned primary/v2 artifact was changed.

## Artifact audit

- Both runs share protocol SHA-256
  `8618feb9e58683dc33392fffb5a977777108ca76dd5828f145a2a4ca05dc7245`,
  locked source `6ac75c202d04934deb46d84486132e54d42d735f`, and data tree
  `5bb8f9e5f1bb1c4deec8f0db1351e27d1bf30333`.
- Primary: 288/288 manifest hashes; Python 3.13.15; executed notebook checked.
- V2: 287/287 manifest hashes; Python 3.12.13; executed notebook missing after
  recorded self-capture error.
- Each run passes 280 checkpoints, 1,400 keyed fits, 92,617 mappings, 35
  independently recomputed summary rows, and 300 exact 5,000-resample paired
  bootstrap rows with NumPy 2.5.1 and tolerance `1e-10`.
- Seven v2 smoke checkpoints/35 fits match the corresponding full results in
  all fields except runtime; they are not added to the sample size.
- The 1,400-key comparison finds 43 changed original-report ARI rows, all at
  copy 2x in four graph methods. Control, GPS, timestamp, and copy-5x ARI are
  unchanged. Duplication mappings are byte-identical. Other graph/result and
  runtime changes are recorded without a causal attribution.
- Primary remains the predetermined manuscript/heatmap source; v2 is an
  unpooled replication.

Audit command:

```bash
PYTHONPATH=/home/ngthtrong/.local/share/nckh2-rq1-audit/site-packages \
  python3 src/results/verify_camera_ready_evidence.py --artifact-only \
  --comparison-output src/results/rq1_results_v2/comparison_with_primary.csv
```

## Manuscript and figure integration

- The confidence, contextual-similarity, graph-affinity, and priority equation
  groups are numbered 1–4 and define their variables, units, ranges, scale
  parameters, weights, and priority bound. Pseudocode references the equations
  rather than repeating them.
- The RQ1 stress table is replaced by a 30-cell vector-PDF heatmap generated
  from primary paired effects. Values are signed to four decimals and remain
  legible in grayscale. The Product-Louvain 5x result `-.6108` with CI
  `[-.6318,-.5881]` remains in text.
- The two redundant RQ2/RQ3 figures and headline table were removed; benchmark,
  robustness, sensitivity, adverse findings, and synthetic/field boundaries
  remain.
- The manuscript states that v2 slightly changes 2x graph ARI without changing
  the main stress conclusions, does not pool the runs, and does not assign a
  cause.
- Eight authors are retained under the user's recorded organizer approval;
  Thanh-Trong Nguyen is the only corresponding author.
- Data and Code Availability separates `v1.0.1`, primary stress, and v2.
  Current licensing states MIT for code only, no new CC BY grant for current
  non-code content, and preserves permissions attached to older snapshots.

## Build, PDF, and package evidence

- Dockerized Tectonic build: 15 pages, no LaTeX errors, undefined
  citation/reference, or overfull box.
- Clean extracted-ZIP build used TeX Live 2026 and completed the required
  sequence `xelatex -> bibtex -> xelatex -> xelatex`: 15 pages, no errors,
  undefined citation/reference, or overfull box. Required CTAN packages
  `aliascnt`, `algorithms`, `algorithmicx`, and `needspace` were installed into
  the disposable build container; EasyChair/Springer are expected by their
  instructions to provide current CTAN packages.
- Remaining warnings are non-blocking: obsolete `aliascnt` notice inherited by
  `llncs.cls`, an `amsmath` accent notice, two narrow-table underfull hboxes,
  and one underfull vbox. Fonts/margins/template were not reduced or changed.
- The Tectonic and XeLaTeX PDFs have the same 15 page sizes and normalized text
  on every page. `paper/main.pdf` and the packaged PDF now use the clean
  XeLaTeX output.
- Minimal source ZIP SHA-256:
  `a4a3657e2de1fa591fb7bf1cc28e6258a5eaccca559e23ea1342f7547f1ea30a`.
- Matching PDF SHA-256:
  `917d83a4be423f5a96d2bc257903107cdc08f9dcda9b4d3f0753fe646875f623`.
- Generated files are in ignored `paper/submission/`. ZIP root contains
  `main.tex`, `references.bib`, `main.bbl`, `llncs.cls`, `splncs04.bst`, and
  only the two referenced PDF figures. Alt text is in
  `docs/camera-ready/FIGURE_ALT_TEXT.md`.

## Status matrix

| Gate | Status | Evidence or next step |
|---|---|---|
| Numerical audit primary/v2 | Complete | Full verifier and comparison CSV pass |
| Manuscript integration | Complete | Formula/figure/claim checks pass |
| PDF 12–15 pages | Complete | Clean XeLaTeX PDF is 15 pages |
| Source package dry run | Complete | Extracted ZIP builds through four-command chain |
| Original experiment package provenance | Pending group | Supply both original ZIPs, runtime/resume history, and v2 notebook |
| Conference-rule confirmation | Partly complete | Confirm deadline time zone and alt-text channel |
| Author/metadata approval | Pending group | Approve final PDF, ZIP, title, author order, ORCIDs and funding |
| LTP | Pending group | Complete, hand-sign, scan and verify metadata |
| Registration/upload/release | Not performed | Separate authorized external actions |

## Next concrete task

The group reviews `paper/submission/paper-6444-camera-ready.pdf`, the source
ZIP, metadata, and LTP. Before upload, re-run the package script after any
approved manuscript edit, repeat the clean XeLaTeX/BibTeX build, and retain
the final hashes and EasyChair receipt.
