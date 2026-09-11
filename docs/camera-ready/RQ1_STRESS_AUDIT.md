# RQ1 fixed-stress artifact audit

Date: 2026-09-11 UTC

## Scope

This audit covers the returned fixed-configuration RQ1 stress artifact in
`src/results/rq1_results/` and the executed notebook
`src/results/RQ1_Reviewer_Stress_Colab_After_Run.ipynb`. It does not rerun the
1,400 clustering fits or alter any returned CSV, JSON, checkpoint, or notebook.

The locked source is commit
`6ac75c202d04934deb46d84486132e54d42d735f`, data tree
`5bb8f9e5f1bb1c4deec8f0db1351e27d1bf30333`, selected-configuration SHA-256
`e3c9f1ad333575862126315595835f01a7b660ac59c240ed0e282f653fb265f6`,
and protocol SHA-256
`8618feb9e58683dc33392fffb5a977777108ca76dd5828f145a2a4ca05dc7245`.

## Reproduction command

The independent audit used Python 3.12.3 with NumPy 2.5.1 installed in an
isolated user directory:

```bash
PYTHONPATH=/home/ngthtrong/.local/share/nckh2-rq1-audit/site-packages \
  python3 src/results/verify_camera_ready_evidence.py --artifact-only
```

Running the command without `--artifact-only` also checks every quoted
RQ1/RQ2/RQ3 manuscript value, including each cell of the fixed-stress ARI
table.

## Passed checks

- All 288 files named by `manifest.json` recompute to their recorded SHA-256.
- The artifact contains exactly 280 run-condition checkpoints and 1,400 unique
  run-condition-method rows: 40 held-out runs, seven conditions, and five
  methods.
- No non-empty `failures.jsonl` is present. Every checkpoint uses the locked
  source commit, data tree, and protocol hash.
- The 120 required input files match the locked source snapshot byte for byte;
  their canonical inventory hash and the selected configurations match the
  protocol.
- Every per-run CSV value agrees with its checkpoint. Every control ARI and
  pairwise-F1 value agrees exactly with the original RQ1 benchmark row.
- All 35 summary rows were recomputed for mean, sample standard deviation, and
  count with absolute tolerance `1e-10`.
- All 300 paired-effect rows were recomputed, including the exact seeded 5,000
  bootstrap resamples and 2.5/97.5 percentiles, with NumPy 2.5.1 and absolute
  tolerance `1e-10`.
- All 92,617 duplication-mapping rows agree with their checkpoints. Each source
  report has exactly two or five total copies, all perturbed identifiers are
  unique, and every mapping points back to the correct source identifier.
- The executed notebook contains no error output and records passing source,
  data, transformation, formula, smoke, full-batch, and aggregation gates.

## Evidence-supported findings

All tested GPS and timestamp noise conditions lower mean ARI relative to each
method's control. No method has the highest mean ARI in all seven conditions.
For Product Louvain, mean ARI is `.9072` at control, `.7816` under 300 m GPS
noise, and `.7442` under 60 min timestamp noise.

Exact-copy behavior is non-monotone. Twofold total multiplicity slightly raises
mean ARI for the four graph variants. Fivefold multiplicity lowers them to
approximately `.29`--`.30`; Product Louvain changes by `-.6108` with an
unadjusted paired-bootstrap 95% CI `[-.6318,-.5881]`. Geo-time DBSCAN remains
at `.4978` under both copy conditions from a substantially lower control
baseline. The artifact does not isolate the mechanism behind the graph-method
discontinuity.

These findings concern upstream clustering. Exact-copy invariance of the
family-wise priority score applies when the evidence grouping and other score
inputs are fixed; it does not imply clustering or end-to-end invariance.

## Open provenance gates

- The notebook output records the original ZIP SHA-256 as
  `d53624bbb3e681504ce9691a77b93610559183187bfe731a3f7fd10de6e034c2`,
  but the ZIP file itself is not in the repository and could not be hashed
  independently.
- Colab ran Python 3.13.15 with the pinned package versions. The manifest
  records the full version, but the returned protocol did not include
  `python_version` in its protocol hash. The current notebook includes this
  additional guard, so it must not be treated as byte-identical to the
  executed protocol or used to resume these checkpoints.
- The group still needs to state whether any saved checkpoint was resumed
  across a Colab runtime change. This affects provenance reporting, not the
  arithmetic checks above.

The numerical artifact is accepted for manuscript integration. Package-level
provenance remains pending the original ZIP and the group's runtime/resume
confirmation.
