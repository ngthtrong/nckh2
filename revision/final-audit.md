# Gate 4 final scientific audit

## Decision

**PASS — locked local synthetic-methodological submission.**

The minimum technically executable branch of `revision-plan.md` satisfies
Gate 4. This decision does not represent a public release, field validation,
expert validation, venue compliance, author approval, or approved funding and
competing-interest declarations. Those inputs remain external-blocked and are
listed below.

## Audited scope and authority

- Scientific source of truth: the single Gate-3-accepted X0 run
  `20260728T213934Z-85f2a6686a1b-9797f31f-x0-exp23-heldout`, plus only the
  Gate-1 data audit and accepted Exp22 runtime evidence named in
  `revision/result-lock.json`.
- Gate 1 SHA-256:
  `ed564170a768b6ef1c41c6c1e8b36bdd4079576189333618a9b9373629c51e7c`.
- Gate 2 SHA-256:
  `3b386afff6fccb5652395dd1689d990539b5ad2650fb06dde053341253f653d5`.
- Gate 3 SHA-256:
  `7a2976d2aa767858a688eecf31876a7be7374c479373a2e939ff742d552b5c98`.
- G0 result-lock SHA-256:
  `6ec2613168c3984f7a6bb3d72a2224fc8ade3333acee8cfd5457bd040590eeb9`.
- Submission policy SHA-256:
  `6a125d465b4a8a43a1dd9e51c3a308deccd714f9baf35f3df2aeb5f79eadfc1a`.

All rejected or superseded runs remain excluded. The audit did not execute X0
again, alter a protocol JSON file after Gate 2, or modify any G0-promoted
artifact.

## Protocol and result integrity

| Check | Evidence | Result |
|---|---|---|
| Data/method freeze | Gate 1 binds 80 datasets, generator/schema, method contracts, 20/20/40 disjoint seeds, and the accepted run manifest | Pass |
| Pre-test protocol lock | Gate 2 records zero test-dataset reads and zero evaluation starts before lock; 12 method/track selections and 8 no-feasible exclusions are retained | Pass |
| Single held-out execution | Gate 3 binds one successful X0 invocation, 40 test seeds, 480 selected rows, and 320 exclusion rows | Pass |
| Prediction/scientific coverage | Gate 3 records zero selected-prediction failures and zero scientific-seed failures | Pass |
| Negative-result retention | 1,086 clustering-adverse, 289 priority-adverse, 3,057 dispatch-adverse, and 80 factorial density-unmatched records remain in the accepted evidence | Pass |
| Promotion transaction | `revision/result-lock.json` binds exactly nine promoted artifacts and the promotion program | Pass |
| Complete/compact equivalence | Gate 3 binds its independent aggregate/inference recomputation; Gate 4 rechecks the canonical gzip projection/omissions and independently resolves selectors, claim values/rounding, macros, and mandatory disclosures | Pass |

The complete X0 archive has raw SHA-256
`f73bfcd03d57bbd1457c569fedc44ce4f230b0c4d24eb6155653a37ed0c97163`
and content SHA-256
`ddafd634fbf9f48ddc4dcc583518a11ae5bb4d342fc29087e9865aefbeb18761`.
All 448 Gate-3 selectors resolve against both the complete archive and compact
projection. The publication catalog contains 461 selector roots and 9,451
mechanically rendered numeric claims.

## Scientific claim audit

- The mathematical statement and implementation use complete product/additive
  domains and the same strict threshold convention.
- The product-component diameter corollary is conditional on a component with
  at least two vertices; the singleton case is stated separately with
  \(h=D=0\).
- Product is not described as uniformly superior. Leiden ties it on the
  highlighted clustering comparison, additive has the smaller destination
  diameter, ST-DBSCAN has favorable split/noise outcomes, and substantial
  review/false-destination burden remains visible.
- All factorial density-match failures remain disclosed rather than being
  silently dropped.
- Exact-duplicate invariance does not become a general robustness claim:
  coordinated high-confidence reports worsen the revised priority estimator in
  the accepted stress evidence.
- Priority is a bounded synthetic policy heuristic, not an expert-validated
  triage score. The independent dispatch endpoints do not establish a general
  dispatch benefit; unfavorable nearest-policy comparisons remain in the main
  text.
- G0 contains no multimodal-specific numeric selector, and the manuscript makes
  no quantitative multimodal performance claim; it only discloses that the
  scenario-family table is preserved. Dedicated multimodal analysis remains
  unresolved.
- The study is explicitly synthetic-methodological. It makes no claim of field
  effectiveness or real-data external validity.

The final TeX sources contain 183 numeric-claim occurrences, 161 unique claim
IDs, all 10 mandatory adverse/neutral disclosures, and zero unresolved claim
IDs. `revision/response-to-reviewer.md` dispositions all eight major concerns,
the minor concerns, and the reviewer's questions without converting partial or
external-blocked work into a completed claim. Its manually displayed empirical
values were independently checked against the exact claim roots named beside
them and are sealed by the final source-state manifest.

## Literal clean-room reproduction

The evidence-generation full profile ran in
`/home/ngthtrong/.cache/nckh2-gate4-bootstrap-5988a0d/repo`, a clean detached
Git worktree with canonical LF text, no virtual environment, no materialized
run directory, and no LaTeX auxiliary outputs. A fresh CPython 3.12
environment installed the exact `requirements.lock` pins. Report and transcript
outputs were captured outside the checkout so the manifest-bound transcript
was never overwritten during final-lock verification.

- Materialization from the companion package: 72 created, 0 pre-existing,
  0 replaced.
- Full suite: 242 passed and 41 subtests passed in 58.04 seconds.
- Locked-output verifier: 11 checks passed, 0 failed, 0 incomplete.
- Held-out/test seed datasets in the package: 0; the sole seed fixture is a
  development fixture required by tests.
- Companion package: 72 members, 79,801,263 bytes unpacked and 4,706,161 bytes
  compressed.
- Companion-package SHA-256:
  `e7b9bcfcda6897853074fa9c21820545440bf0f3022a2c02ab80d64dd9192d1a`.
- Machine-report SHA-256:
  `d669e4b403b564d7a93aa8c864f6bb6cd83dcc996bea1cb658c9cd504d4d21af`.
- Full-transcript SHA-256:
  `6f58d49ef556a0bbec2be3ec99cbcd696dfe7888bb6da465ddc35767508d4cad`.

The machine result is preserved in
`revision/clean-room-verification.json`; the human-readable execution record
and full transcript are `revision/clean-room-report.md` and
`revision/clean-room-full.log`.

The run retained every Gate-1, Gate-2, Gate-3, and G0 binding and rebuilt the
same PDF. It did not modify the generator, weighting, priority, selected
configurations, held-out results, or promoted scientific artifacts. Generated
Gate-4 evidence and documentary updates were integrated afterward, bound by a
regenerated submission manifest, and then subjected to a separate fresh-clone
seal verification.

## Publication-output audit

- Build sequence: XeLaTeX, BibTeX, XeLaTeX, XeLaTeX.
- Deterministic source epoch: `1785275159`.
- Final PDF: 11 pages, SHA-256
  `440b944bce1df3dbdb41086f534e65f94a397bb746aca9f43e9c883ec8ab58f6`.
- The clean-room PDF and working-repository PDF are byte-identical.
- Undefined references/citations: 0.
- Overfull boxes: 0.
- Underfull boxes: 1, permitted by the locked local policy.
- TeX warnings: 1 explicitly allowlisted `amsmath` warning, 0 unallowed.
- BibTeX warnings: 0.
- Included figures: 0; available/orphan manuscript figures: 0.
- Source/output freshness: pass.
- The manuscript uses an anonymous author block and pending funding/interest
  declarations rather than asserting unapproved submission metadata.

The former Loop-17 figures and build log are preserved as historical material
under `archive/loop17-paper-assets/` and are not publication evidence.

## Documentation and traceability

`README.md` points to the verification reports; both `README.md` and
`demo/README.md` document the locked workflow, exact dependency installation,
XeLaTeX build, companion package, external evidence capture, and final
submission-lock step. `.gitattributes` forces canonical LF for submission text
even when `core.autocrlf=true`, while binary artifacts are marked `-text`.
Every required submission member, including `revision/clean-room-full.log`, is
present and Git-tracked.
`loop/revision/traceability.md`, the response, this audit, and the change ledger
all use the G0 source of truth. No stale Loop-17 result path, manually typed
live-manuscript headline value, unresolved claim ID, or live manuscript figure
remains.

## External blockers and release boundary

The following are outside the authority and evidence available in this
workspace:

1. real-report access, rights/ethics review, annotation, and a held-out
   real-data sanity check;
2. an independent expert panel and completed expert-validation summary;
3. author names/order, affiliations/contact, authorship consent, and ORCID
   approval;
4. funding and competing-interest declarations;
5. a venue-specific page-limit decision;
6. a public repository/archive, DOI, author-approved clean commit/tag, and
   release authority.

The local submission checksum manifest therefore seals the exact technical
source state but does not substitute for a public immutable release. Gate 4 is
locked only as `locked-local-submission`; reopening the held-out protocol is not
authorized by any remaining external action.
