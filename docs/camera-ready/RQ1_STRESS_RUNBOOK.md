# RQ1 reviewer stress experiment: group runbook

Use `src/results/RQ1_Reviewer_Stress_Colab.ipynb` only for an explicitly
approved future rerun. The completed Colab outputs are in
`src/results/rq1_results/`, and their independent audit is recorded in
`RQ1_STRESS_AUDIT.md`. Do not rerun RQ1/RQ2/RQ3 unless a separate evidence
audit finds a conclusion-changing defect.

## Returned-run status

- Numerical audit accepted all 288 manifest hashes, 280 checkpoints, 1,400
  fits, 92,617 copy mappings, 35 summaries, and 300 paired bootstrap rows.
- The returned run used Python 3.13.15 with the pinned package versions. Its
  manifest records that version, but its protocol did not hash
  `python_version`.
- The current notebook and builder do hash `python_version`. They are therefore
  stricter than the executed protocol and cannot resume its checkpoints.
- The original ZIP is not in the repository. Its notebook-recorded SHA-256 is
  `d53624bbb3e681504ce9691a77b93610559183187bfe731a3f7fd10de6e034c2`.
  The group must provide that ZIP and state whether checkpoints were resumed
  across a runtime change to close package-level provenance.

## Locked design

- RQ1 benchmark source commit: `6ac75c202d04934deb46d84486132e54d42d735f`.
- RQ1 data tree: `5bb8f9e5f1bb1c4deec8f0db1351e27d1bf30333`.
- Source benchmark-notebook SHA-256:
  `13a586af7ac5331dd1afe354b9e5c9a46b90e0ff2f6ac6f71dbdc3badd6ca7ef`.
- Selected-configuration SHA-256:
  `e3c9f1ad333575862126315595835f01a7b660ac59c240ed0e282f653fb265f6`.
- Stress implementation ID: `rq1-reviewer-stress-2026-09-08-v1`.
- Test runs: `run_041` through `run_080`.
- Seven conditions: control; GPS Gaussian noise at 100 m and 300 m;
  timestamp Gaussian noise at 15 min and 60 min; total exact transport-copy
  multiplicity 2 and 5.
- Five methods: Product Louvain, independently selected Additive Louvain,
  matched-density Additive Louvain, Product Leiden, and geo-time DBSCAN.
- Total: 40 × 7 × 5 = 1,400 clustering fits. No tuning is permitted.

The noise levels are synthetic stress settings, not field-error estimates.
For duplicate conditions, only the report/transport identifier changes. The
mapping to the source report is evaluator-only.

## Colab steps

1. Upload or open the notebook in Google Colab and use a CPU runtime. Python
   3.12 is recommended because it matches the source benchmark; Python
   3.11-3.13 is accepted when 3.12 is unavailable. The notebook records the
   exact Python version in its protocol and manifest and will reject checkpoints
   produced by a different runtime.
2. Run steps 1–6 in order. Step 1 may restart the runtime once after installing
   the exact package versions recorded by the source benchmark; reconnect and
   run from the beginning. The notebook then verifies the source
   notebook/data/configuration hashes, tests transformation invariants, and
   performs a 35-fit smoke run.
3. Read the smoke table and record its measured duration; this is the basis for
   the notebook's runtime estimate. Do not replace it with an assumed time. The
   notebook defaults to `RUN_FULL = True`; set it to `False` only for an
   intentional smoke-only run, then stop after step 6.
4. Keep Google Drive enabled so each run-condition checkpoint survives a
   disconnected runtime.
5. Continue through steps 7–9. If interrupted, reconnect, rerun setup/integrity steps, keep
   the same Drive directory, and rerun step 7; matching checkpoints resume.
6. Download the timestamped `nckh2-rq1-reviewer-stress-*.zip`. If the notebook reports
   `manual-download-required`, also use **File → Download → Download .ipynb**
   and place that executed notebook beside the ZIP.
7. Send the ZIP, its printed SHA-256, and the executed notebook to the person
   integrating the camera-ready revision. Do not edit generated CSV/JSON.

## Acceptance checks after return

- `manifest.json`, `protocol.json`, and `selected_configs.used.json` agree on
  the locked protocol SHA, source commit, data tree, configuration values, and
  configuration hash.
- There are exactly 280 run-condition checkpoints and 1,400 fit rows.
- Every run-condition-method tuple appears exactly once; all paired effects
  have 40 runs where the metric applies.
- `failures.jsonl` is absent or empty. Any recorded failure must be resolved
  and the affected checkpoint rerun; it must not be omitted from aggregation.
- All artifact hashes in the manifest recompute exactly.
- The executed notebook shows the integrity gate, smoke run, full-run count,
  and aggregation checks passing.
- Null and adverse results remain visible. The camera-ready text must not claim
  robustness beyond these fixed stresses.

These checks have passed for the extracted artifact, and the audited results
are integrated into the manuscript. The experiment status is **numerically
accepted; original ZIP and runtime/resume confirmation pending**.
