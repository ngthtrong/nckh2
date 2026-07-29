# Clean-room reproduction report

## Outcome

- Profile: `full`
- Completed at: `2026-07-28T23:07:29Z`
- Status: **PASS**
- Held-out execution: **not invoked**
- Clean workspace: `/tmp/nckh2-cleanroom-final.Bg31pI/repo`

Entrypoint:

```bash
set -o pipefail
./reproduce.sh --profile full \
  --report revision/clean-room-verification.json 2>&1 \
  | tee revision/clean-room-full.log
```

The workflow created a temporary CPython 3.12 virtual environment, installed
every exact pin in `requirements.lock`, verified and materialized the companion
artifact allowlist without overwriting any file, ran the complete test suite,
verified the Gate-3 recomputation binding and independently checked the compact
projection, selectors, claim graph, and publication values, then built the
paper with XeLaTeX--BibTeX--XeLaTeX twice.

This run used a literal clean source copy, not the working repository. Before
execution, the copy had no `.git`, `.venv`, `demo/.venv`,
`demo/artifacts/runs`, `paper/main.pdf`, `paper/main.log`, prior
machine-verification report, or prior full-run transcript. The source copy
excluded all LaTeX build outputs; the workflow reconstructed the locked run
members from the companion archive and generated the publication outputs from
source.

## Environment

| Component | Audited value |
|---|---|
| OS | Linux 6.6.87.2-microsoft-standard-WSL2, x86_64 |
| Python | CPython 3.12.3 |
| XeTeX | 3.141592653-2.6-0.999995, TeX Live 2023/Debian |
| BibTeX | 0.99d, TeX Live 2023/Debian |
| `SOURCE_DATE_EPOCH` | `1785275159` |
| Time zone during build | UTC |

The Python environment was discarded after the run. Package installation used
the exact versions in `requirements.lock`; the lock SHA-256 is
`3da31ce6433e7318f0970685616015c76cd522f6b70aa5a01827d2ecd74d86f2`.

## Test and artifact evidence

- Full suite: **235 passed, 41 subtests passed** in 32.47 seconds.
- Artifact package: 72 allowlisted members, 79,801,263 bytes unpacked,
  4,706,161 bytes compressed.
- Package SHA-256:
  `e7b9bcfcda6897853074fa9c21820545440bf0f3022a2c02ab80d64dd9192d1a`.
- Materialization: 72 created members, 0 exact existing, 0 replaced.
- Held-out/test seed datasets in the package: **0**. One development fixture
  (`development/seed_1000.json`) is included solely because the full test suite
  consumes it.
- Complete promoted X0 JSON: canonical gzip round-trip passed; decompressed
  SHA-256
  `f73bfcd03d57bbd1457c569fedc44ce4f230b0c4d24eb6155653a37ed0c97163`.
- Compact projection: exactly five declared raw-row blocks and 4,256 rows
  omitted; all omitted rows remain in the complete archive.
- Gate-3 selectors: 448/448 resolve against both complete and compact results.
- Publication catalog: 461 selector roots, 9,451 numeric claims, and all 10
  mandatory adverse/neutral disclosures verified.
- Manuscript: 183 claim occurrences, 161 unique claim IDs, 0 unresolved IDs.
- Figures: 0 referenced, 0 available in `paper/figures`, 0 orphan.

## Paper build

- Sequence: XeLaTeX, BibTeX, XeLaTeX, XeLaTeX.
- Output: 11 pages.
- Undefined citations/references: 0.
- Overfull boxes: 0; maximum excess 0 pt.
- Underfull boxes: 1, allowed by `revision/submission-policy.json`.
- TeX warnings: 1 explicitly allowlisted `amsmath` warning; 0 unallowed.
- BibTeX warnings: 0.
- Source/output freshness: pass.
- PDF SHA-256:
  `440b944bce1df3dbdb41086f534e65f94a397bb746aca9f43e9c883ec8ab58f6`.

The machine-readable post-build report is
`revision/clean-room-verification.json` with SHA-256
`99890788fde80bdc47c493ad285c25fa30f7d99352946f85aa233c2d8f2691b2`.
The persisted full transcript is `revision/clean-room-full.log` with SHA-256
`082f33376d2f87d125c1c46a956ac74018457d4aa0dc2c8a6e2c6272795bc24e`.

## Scope of the pass

This is a locked-output reproduction: it independently checks source locks,
run manifests, the lossless X0 archive, compact projection, selectors, claim
rendering, tests, and publication outputs. It verifies the Gate-3 record of
aggregate/inference recomputation rather than rerunning that validation or X0.
A new X0 invocation would violate the locked protocol unless the relevant
gates were formally reopened.

The frozen clean-room source was byte-identical to the current scientific
code, manuscript source, READMEs, reviewer response, policy, verifier, lock
tool, and tests at execution time. Post-run edits are limited to integrating
the generated report/transcript/PDF and updating this report/final audit with
their hashes; the final submission manifest binds that complete documentary
state.

The technical local submission profile passes. Real-data collection, expert
elicitation, authorship/contact/ORCID approval, funding and competing-interest
declarations, a public repository or DOI, and the venue-specific page-limit
decision remain external-blocked. The paper therefore retains the
synthetic-methodological scope, uses an anonymous author placeholder, and makes
no field-validation or public-release claim.
