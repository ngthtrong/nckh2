# Flood-rescue short-paper protocol and accepted evidence v2

This directory contains the frozen protocol and accepted synthetic evidence for
the ISDS 2026 eight-page short paper. It supersedes the exploratory Exp23
evidence for every claim in `paper/short.tex` and `paper/main.tex`.

## Accepted state

- Protocol SHA-256:
  `754cdb90a592003dbf5319535ebb476d2baebe19f07a67eaab562ba99c3f575e`.
- Implementation/environment SHA-256:
  `c4100c5e8abd4c6cea36593c4b277a9f9e2694faf8c0da377188e9fa6b00e0c5`.
- Confirmation result SHA-256:
  `a7497eaa80d8d7260cc12a603a2240364184b04574260dee2bc685ead7333cf8`.
- Confirmation analysis SHA-256:
  `60550c2b09295928ed3c27113a4ca8955f12228e4b64d0af5432ca9cf9b33ffb`.
- `results/confirmation_manifest.json`: `status=accepted` and
  `coverage_complete=true`.

Coverage is exact: 40 paired master seeds, 40 ID and 40 mechanism-shift OOD
datasets, 320 clustering rows, 480 priority rows, 4,800 stress rows and 1,680
predicted-cluster dispatch rows. Seeds 4300--4339 are permanently retired;
4400--4439 were released once by the managed accepted execution and must not be
run again for model or claim selection.

## Frozen protocol

`bundle.json` names exactly five protocol inputs:

- `seed_partitions.json`: development, calibration, active confirmation and
  retired partitions;
- `method_registry.json`: 128 matched product/additive nuisance pairs and the
  complete ST-DBSCAN/HDBSCAN grids;
- `analysis_contract.json`: 150-min observation snapshot, one-SE selection,
  endpoints, Holm families and fail-closed claim gates;
- `public_sources.json`: rights, access, coverage and redistribution state;
- `public_anchor.json`: checksum-verified aggregate-only NOAA/UK/IDRISI audit,
  plus explicit TREC/CrisisFACTS blockers.

`protocol-lock.json` freezes the bundle before results. Files below `results/`
and all documentation are excluded from the protocol hash.

Product and additive share the same 128-point search space, but the common
one-standard-error rule selects each method independently. Their confirmatory
contrast is therefore an independently selected pipeline comparison, not an
operator-only causal effect.

## Reproduce core synthetic evidence

From the repository root with the locked environment active:

```bash
python -m demo.v2.reproduce reproduce_core
pytest -q demo/tests/test_v2_*.py
```

`reproduce_core` is read-only. It verifies the protocol and accepted artifact
SHA-256 chain, recomputes all descriptives/bootstrap/Wilcoxon/Holm outputs from
the stored synthetic confirmation rows, regenerates `short_results.tex` in a
temporary directory, and requires byte equality. It does not generate a seed,
read the oracle diagnostic or require restricted data.

Build the canonical PDF with:

```bash
cd paper
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

Both `main.pdf` and `short.pdf` must be exactly eight pages with no undefined
citation/reference and no overfull box.

## Reproduce the public-source audit

Authorized holders of the three pinned snapshots can run:

```bash
python -m demo.v2.public_audit reproduce_external \
  --noaa /path/noaa_storm_events_2024.csv.gz \
  --uk /path/uk_flooding_water_rescue.ods \
  --idrisi /path/idrisi_3dfd62d.zip \
  --output /tmp/public_anchor.reproduced.json
```

The command verifies each pinned SHA-256 before parsing. It emits aggregate
descriptive checks only and never fits the generator. TREC-IS and CrisisFACTS
remain blocked, and no raw social-media text may be redistributed.

## Interpretation and submission boundary

Only exact-duplicate score invariance passed its synthetic claim gate. Product
clustering, general priority alignment and predicted-cluster dispatch benefit
did not. External priority/consolidation/location, real incident clustering,
real dispatch benefit, Vietnamese transfer and deployment claims remain
blocked.

See `IMPLEMENTATION_STATUS.md` for current paper QA and non-code submission
blockers. `paper/generated/revision_results.tex` belongs to the legacy Exp23
workflow and must not be included or mined for v2 values.
