# RQ1 fixed-stress primary and replication audit

Date: 2026-09-11 UTC

## Scope and source selection

The audit covers the primary artifact in `src/results/rq1_results/`, its
executed notebook, the independent replication in
`src/results/rq1_results_v2/full/`, and the seven v2 smoke checkpoints. It does
not rerun the 1,400 clustering fits or alter any returned artifact.

The primary run is the fixed source for manuscript values and the heatmap; v2
is a replication check. They are not pooled and the source was not selected by
which run performed better. Both use protocol SHA-256
`8618feb9e58683dc33392fffb5a977777108ca76dd5828f145a2a4ca05dc7245`, source
commit `6ac75c202d04934deb46d84486132e54d42d735f`, and data tree
`5bb8f9e5f1bb1c4deec8f0db1351e27d1bf30333`.

## Reproduction commands

```bash
PYTHONPATH=/home/ngthtrong/.local/share/nckh2-rq1-audit/site-packages \
  python3 src/results/verify_camera_ready_evidence.py --artifact-only \
  --comparison-output src/results/rq1_results_v2/comparison_with_primary.csv

MPLCONFIGDIR=/tmp/nckh2-matplotlib \
PYTHONPATH=/tmp/nckh2-camera-ready-figures \
  python3 src/results/plot_rq1_stress_heatmap.py
```

The audit environment is Python 3.12.3 with NumPy 2.5.1 isolated from the
project environment. Absolute tolerance for finite recomputed results is
`1e-10`.

## Passed checks

| Check | Primary | V2 |
|---|---:|---:|
| Manifest SHA-256 entries | 288/288 | 287/287 |
| Run-condition checkpoints | 280 | 280 |
| Unique run-condition-method rows | 1,400 | 1,400 |
| Duplication mappings | 92,617 | 92,617 |
| Recomputed summary rows | 35 | 35 |
| Replayed paired-effect rows | 300 | 300 |
| Executed notebook | Present and checked | Missing; manual download required |
| Python recorded by manifest | 3.13.15 | 3.12.13 |

For each artifact, all CSV rows match their checkpoints; every control ARI and
pairwise-F1 value matches the locked benchmark; all source inventory and
selected configurations match the protocol; and no non-empty failure log is
present. Mean, sample standard deviation, counts, and exact seeded 5,000-sample
bootstrap intervals were recomputed. Metrics not applicable to DBSCAN have
count zero and blank outputs as specified.

The v2 smoke directory contains exactly seven run-041 checkpoints and 35 fits.
Every scientific field and duplication mapping agrees with the corresponding
full checkpoint; only runtime differs. Smoke results are not added to the
sample size.

## Keyed primary-v2 comparison

`src/results/rq1_results_v2/comparison_with_primary.csv` compares all 1,400
keys `(run_id, scenario, method)` and separates runtime, differences no larger
than `1e-10`, and larger result changes. Runtime differs on all 1,400 rows.
The duplication mapping is byte-identical.

There are 43 changed `ari_original` rows, all in `exact_transport_copy_2x` and
all in the four graph methods. Aggregate means are:

| Method | Primary | V2 |
|---|---:|---:|
| Product Louvain | .9314 | .9342 |
| Additive Louvain | .9337 | .9322 |
| Matched-density Additive | .9181 | .9183 |
| Product Leiden | .9313 | .9289 |

Control, GPS, timestamp, and fivefold-copy ARI values are unchanged. The main
conclusions also remain: twofold copies slightly raise graph-method ARI,
fivefold copies cause a large collapse, and no method leads every condition.
Product Louvain at 5x remains Delta `-.6108`, unadjusted 95% CI
`[-.6318,-.5881]`. Differences in graph density, edge count, other metrics,
and runtime are recorded but do not identify a causal mechanism.

## Open provenance gates

- Obtain the original ZIP for each run and compare its SHA-256. The primary
  notebook recorded
  `d53624bbb3e681504ce9691a77b93610559183187bfe731a3f7fd10de6e034c2`.
- Obtain the executed v2 notebook; its manifest records
  `manual-download-required` after notebook self-capture failed.
- Record whether either run resumed checkpoints across a runtime change.
- Both manifests record Python, but the shared returned protocol did not hash
  `python_version`. Therefore cross-environment reproducibility is not marked
  complete and the observed differences are not attributed to Python.

The numerical evidence is accepted for the stated manuscript use. Package
provenance remains pending the items above.
