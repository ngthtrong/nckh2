# Gate 2 protocol-lock audit

**Status:** PASS  
**Locked:** 2026-07-28T21:03:14.646890+00:00  
**Gate-2 lock:** `revision/gate2-lock.json`  
**Gate-2 lock SHA-256:** `3b386afff6fccb5652395dd1689d990539b5ad2650fb06dde053341253f653d5`

## Frozen protocol and Gate-1 binding

- Final protocol SHA-256 (including `selected_configs.json`):
  `9797f31f3bc7739e935a26f11597a0988adf28b099cb52d97c98381da63e67e7`.
- Pre-selection calibration protocol SHA-256:
  `0060e5dc7edb74afd5ac49dfedee0ea13c27cf9387c302efde5a2fc52e918d4e`.
- Selected-config registry SHA-256:
  `22256afac1786a5758fca754f59a169fabe8d8f74e9aee65a9b15f7b8d968969`.
- Gate-1 lock SHA-256:
  `ed564170a768b6ef1c41c6c1e8b36bdd4079576189333618a9b9373629c51e7c`.
- Accepted Gate-1 run-manifest SHA-256:
  `626a8f36a73f94a554b1fb98efe756726084ca74b13186b4f659bae0d0963175`.
- Frozen dataset-manifest SHA-256:
  `74b9e80a085651b70a9ee18f5e9c7cb9846d47197d89c0717c05ac6af2fd1f7a`.
- Test dataset reads before the lock: **0**.

The transactional promotion command recomputed seed-level aggregates,
per-seed extrema, operational feasibility, joint product/comparator density
matching, feasible counts, and deterministic winner/tie-break identities. It
then loaded the completed registry through the Gate-2 release loader before
atomically installing the lock.

## Calibration selection

- Method/track pairs required by the registry: **20**.
- Feasible selected pairs: **12**.
- Authenticated `no_feasible_candidate` pairs: **8**.
- Configuration evaluations: **1,036**.
- Calibration seed-runs: **20,720**.
- Failed configurations: **0**.

The infeasible records are not omissions. DBSCAN, HDBSCAN, product-spectral,
and coordinate K-Means have no configuration satisfying every frozen
per-seed guardrail in either track. Their complete grids, rejection reasons,
ties, and adverse outcomes remain in the sealed Exp18 table. No threshold,
search-space axis, objective, or guardrail was relaxed after observing these
results.

## Accepted immutable evidence

| Task | Run ID | Manifest SHA-256 | Main audit |
|---|---|---|---|
| B2 / Exp15 | `20260728T195200Z-85f2a6686a1b-0060e5dc-gate2-exp15-calibration` | `bdb96c33746b356201505b22ca6dd61033383e2ecc0d78b53c00ee7629b1019f` | 672 configurations; 13,440 seed-runs; 0 failures; both tracks have joint matched composition selections |
| E2 / Exp18 | `20260728T203919Z-85f2a6686a1b-0060e5dc-gate2-exp18-connectivity-fix` | `7c5975369d6bad88ad803dc573cc08bbf9ae6357ad9afbb1702d0fbefc5f98f6` | 364 configurations; 7,280 seed-runs; 0 failures; 6 selected and 8 infeasible method/track rows |
| E2 / Exp19 | `20260728T204804Z-85f2a6686a1b-0060e5dc-gate2-exp19-factorial` | `31cb1913b50fd1eb66397c1cf8341ccc3f1a525b01bb68eb48b91a92e7fa1c6c` | 320/320 clustering and 160/160 priority cell-seed rows; all interaction orders retained |
| C3 / Exp16 | `20260728T205003Z-85f2a6686a1b-0060e5dc-gate2-exp16-priority-robust` | `12d5669f1fc01caec4fe6992702c01550859e10c0b5d5de53ae7caee1d281841` | 2,508 rows over 40 development/calibration seeds; adverse and known campaign failure retained |
| C4 / Exp17 | `20260728T205218Z-85f2a6686a1b-0060e5dc-gate2-exp17-dispatch` | `273b3227519203dac41eebc057717719b4bbf9a021e0a8fc0da0174992232415` | 720 policy-resource rows; 270 paired comparisons; outcome contract is algebraically independent of reported priority |
| E3 / Exp20 | `20260728T205406Z-85f2a6686a1b-0060e5dc-gate2-exp20-output-burden` | `bf3c64096fdcba899e76f3da2936e96a5602c3c235b0960c46fa04c03208dd0f` | 60/60 method-seed rows; 100% report coverage; zero failures; selectors sealed |
| F4 / Exp22 | `20260728T205453Z-85f2a6686a1b-0060e5dc-gate2-exp22-runtime` | `429d82f4897c2c52313e7bc38d0109949d256cb8e5484988d9f47bff2bd46de6` | 3 sizes × 5 measured repeats; one-core eligible; equal edges, zero matrix difference, and equal labels |

## Rejected evidence and negative outcomes

Run
`20260728T202747Z-85f2a6686a1b-0060e5dc-gate2-exp18-baselines`
is permanently rejected. Constraint decomposition showed that
same-representation graph adapters omitted
`disconnected_communities`, spuriously making product-Leiden infeasible. The
metric-only bug was fixed for every affected adapter and the complete grid was
rerun with unchanged data, seeds, grids, objectives, and guardrails. The
rejected immutable run remains listed in `revision/rejected-runs.json`.

The accepted Exp19 artifact also retains 40 density-match failures. Exp16
retains 284 adverse, 1,270 favorable, and 646 tied paired directions. Exp17
retains 3,010 adverse, 2,055 favorable, and 335 tied paired directions.

## Verification

- Pre-lock full suite: **197 passed, 41 subtests passed**, zero failures.
- Mutation coverage includes sealed non-optimal winners, empty seed metrics,
  altered aggregate extrema, invalid joint-density selection, duplicate
  selection scope, path escape, protocol mutation, and unauthenticated source
  swaps.
- Gate-1 method/data source hashes were rechecked immediately before lock and
  remained exact.
- C5 expert validation and D4 real-data validation remain
  `external-blocked`; the synthetic operational thresholds and dispatch
  results must therefore remain explicitly illustrative in the manuscript.
