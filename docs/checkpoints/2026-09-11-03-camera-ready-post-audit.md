# Checkpoint: camera-ready post-audit corrections

Date: 2026-09-11 UTC

## Baseline and scope

- Work started from branch `clean` at `5fad10d`; the only pre-existing working
  tree item was the untracked comparison report
  `docs/camera-ready/ORIGINAL_VS_CURRENT_REVIEW_AUDIT_2026-09-11.md`, which was
  preserved and updated with the resolution of its findings.
- The submitted release remains `v1.0.1` at `be95d4c`.
- No experiment, algorithm, configuration, dataset, result row, author order,
  affiliation, or ORCID was changed. No commit, push, release, signature, or
  EasyChair upload was performed.

## Manuscript corrections

- The conditional component bound `D < h r` now applies only to components
  with at least two nodes and `1 <= h < infinity`; a singleton is handled
  separately with `h=D=0`. The edge-localization theorem is unchanged.
- Manual boundary checks cover all cases: a singleton invokes no strict
  inequality; a two-node component has `h=1` and inherits `D < r` from its
  retained edge; a larger component uses a shortest path of at most `h` edges,
  each strictly shorter than `r`, to obtain `D < h r` by triangle inequality.
- The RQ2 summary now reports that the revised score is also more sensitive
  than legacy to low-confidence urgency inflation, matching the existing
  robustness table. No value or inference family changed.
- The Abstract identifies Louvain and Leiden as community detectors and the
  Product/Additive terms as graph-affinity constructions at first occurrence.
- Thanh-Trong Nguyen remains the only corresponding author. His complete
  header email is `trongb2305615@student.ctu.edu.vn`; the other seven authors,
  their order, affiliations, emails, and ORCIDs remain present.
- Remote read-only verification found `clean` at `5fad10d` and `v1.0.1` at
  `be95d4c`. Data and Code Availability links the exact public commit containing
  the RQ1 stress artifacts and explicitly excludes them from `v1.0.1`.

## Reviewer-response and evidence boundaries

- The response identifies the fixed RQ1 measurement/copy protocol as the new
  camera-ready experiment. The full 11-scenario RQ2 table, resource-specific
  RQ3 means, and 840-observation sensitivity analysis are described as expanded
  reporting of existing analyses, not new field evidence.
- Current PDF page references were added to the internal reviewer response.
- Primary and v2 remain independently audited and unpooled. Original ZIPs,
  runtime/resume confirmation for both runs, and the executed v2 notebook remain
  open provenance gates; no Python or sparsification cause is assigned.

## Verification and package

- `git diff --check` and Python compilation passed.
- `verify_camera_ready_evidence.py` passed the RQ2/RQ3 manifests, RQ3 40-seed
  provenance, the submitted RQ1 snapshot, both 1,400-fit stress artifacts, the
  seven-checkpoint v2 smoke comparison, the 1,400-key primary/v2 comparison,
  and the updated manuscript assertions.
- Dockerized Tectonic built 15 pages. A fresh extraction of the generated ZIP
  completed `xelatex -> bibtex -> xelatex -> xelatex` with TeX Live 2026 and
  also produced 15 pages.
- The final clean log has no TeX errors, undefined citations/references, or
  overfull boxes. Non-blocking warnings remain for obsolete `aliascnt`, the
  inherited `amsmath` accent notice, two underfull table hboxes, and one
  underfull vbox.
- The Tectonic and clean XeLaTeX PDFs have equal page sizes and normalized text
  on all 15 pages. Visual inspection covered the title/author block, Abstract,
  component bound, RQ1/RQ2/RQ3 results, heatmap, and references.
- Final source ZIP SHA-256:
  `619cfe94660c4be805c2fca9e546d9186efe7184635748c21017cd16d743541a`.
- Final PDF SHA-256:
  `e3a1a939fb74c908ca89960de94a91374d5123f0ac6691dde5e8329b53c7586a`.
- Generated handoff files remain under ignored `paper/submission/`.

## Open external gates

- Group approval of the PDF, source ZIP, title, eight-author metadata,
  corresponding-author email, funding statement, alt text, and LTP contents.
- Completion and handwritten signature of the LTP with Thanh-Trong Nguyen as
  the Corresponding Author Name after group authorization.
- Organizer confirmation of deadline time zone and the alt-text delivery
  channel.
- Original RQ1 run-package provenance described above.
- EasyChair upload, receipts, registration, and any new archival release.
