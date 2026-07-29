# Clean-room reproduction report

## Outcome

- Profile: `full`
- Completed at: `2026-07-29T16:03:19Z`
- Status: **PASS**
- Held-out execution: **not invoked**
- Clean workspace:
  `/home/ngthtrong/.cache/nckh2-gate4-bootstrap-5988a0d/repo`

Entrypoint:

```bash
capture_root=/home/ngthtrong/.cache/nckh2-gate4-bootstrap-5988a0d
./reproduce.sh --profile full \
  --report "$capture_root/verification.json" \
  >"$capture_root/full.log" 2>&1
```

The workflow created a temporary CPython 3.12 virtual environment, installed
every exact pin in `requirements.lock`, verified and materialized the companion
artifact allowlist without overwriting any file, ran the complete test suite,
verified the Gate-3 recomputation binding and independently checked the compact
projection, selectors, claim graph, and publication values, then built the
paper with XeLaTeX--BibTeX--XeLaTeX twice and verified the final submission
lock before reporting `PASS`.

This evidence-generation run used a clean detached Git worktree, not the
Windows working repository. Before execution it had no virtual environment,
materialized `demo/artifacts/runs` tree, or LaTeX auxiliary outputs. The
tracked PDF and prior sealed evidence were present as baseline members; the
workflow reconstructed the allowlisted run members, rebuilt the PDF from
source, and verified byte identity.

The report and stdout/stderr were captured outside the checkout and then
integrated byte-for-byte. They were not written through `tee` to their tracked
paths because the final lock verifies the transcript itself. After evidence
integration, the submission manifest is regenerated and verified in a
separate fresh-clone pass.

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

- Full suite: **242 passed, 41 subtests passed** in 58.04 seconds.
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
`d669e4b403b564d7a93aa8c864f6bb6cd83dcc996bea1cb658c9cd504d4d21af`.
The persisted full transcript is `revision/clean-room-full.log` with SHA-256
`6f58d49ef556a0bbec2be3ec99cbcd696dfe7888bb6da465ddc35767508d4cad`.

## Scope of the pass

This is a locked-output reproduction: it independently checks source locks,
run manifests, the lossless X0 archive, compact projection, selectors, claim
rendering, tests, and publication outputs. It verifies the Gate-3 record of
aggregate/inference recomputation rather than rerunning that validation or X0.
A new X0 invocation would violate the locked protocol unless the relevant
gates were formally reopened.

The clean run retained the Gate-1, Gate-2, Gate-3, and G0 bindings and rebuilt
the same PDF. No generator, weighting, priority, selected configuration,
held-out result, or promoted scientific artifact changed. Post-run edits are
limited to integrating generated Gate-4 evidence and updating reproduction
documentation; the regenerated submission manifest binds that documentary
state and is checked separately from a fresh clone.

The technical local submission profile passes. Real-data collection, expert
elicitation, authorship/contact/ORCID approval, funding and competing-interest
declarations, a public repository or DOI, and the venue-specific page-limit
decision remain external-blocked. The paper therefore retains the
synthetic-methodological scope, uses an anonymous author placeholder, and makes
no field-validation or public-release claim.
