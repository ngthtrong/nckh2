# Checkpoint: audited RQ1 stress integration

Date: 2026-09-11 UTC

## Baseline and authorization

- Submitted artifact: tag `v1.0.1`, commit `be95d4c`.
- Camera-ready baseline at the start of this work: branch `clean`, commit
  `9fbc49c` (`CR_0.1`), with a clean working tree.
- The author approved Q1--Q5: independent artifact audit, manuscript
  integration, internal documentation updates, PDF validation, and a dated
  handoff checkpoint.
- The manuscript presents the final scientific design and evidence. Committee
  comments and revision history remain in internal documentation.
- No algorithm, selected configuration, source dataset, or returned experiment
  artifact was changed, and the 1,400 fits were not rerun.

## Artifact received and audited

- Returned paths: `src/results/rq1_results/` and
  `src/results/RQ1_Reviewer_Stress_Colab_After_Run.ipynb`.
- Locked source commit: `6ac75c202d04934deb46d84486132e54d42d735f`;
  data tree: `5bb8f9e5f1bb1c4deec8f0db1351e27d1bf30333`;
  protocol SHA-256:
  `8618feb9e58683dc33392fffb5a977777108ca76dd5828f145a2a4ca05dc7245`.
- Passed: 288 manifest hashes, 280 checkpoints, 1,400 unique fits, 92,617
  duplication mappings, 35 recomputed summaries, and 300 paired effects with
  exact replay of 5,000 bootstrap resamples under NumPy 2.5.1.
- All control ARI and pairwise-F1 values match the locked RQ1 benchmark by run.
  No missing tuple, duplicate tuple, or non-empty failure log was found.
- Audit command:

```bash
PYTHONPATH=/home/ngthtrong/.local/share/nckh2-rq1-audit/site-packages \
  python3 src/results/verify_camera_ready_evidence.py --artifact-only
```

- Full evidence-to-manuscript verification passes with the same command after
  removing `--artifact-only`.
- Detailed evidence and interpretation are in
  `docs/camera-ready/RQ1_STRESS_AUDIT.md`.

## Manuscript integration

- Experimental Design now records the fixed seven-condition, five-method,
  40-run protocol and the `1,400`-fit total without describing the publication
  revision process.
- Endpoints distinguish metrics on original incident-linked reports from
  full-payload diagnostics and identify the 5,000-resample unadjusted paired
  intervals as within-method stress-versus-control descriptions.
- Results include all seven mean-ARI conditions for all five methods. Both the
  slight twofold-copy improvement and the fivefold graph-method failure are
  retained; Product Louvain changes by `-.6108`, 95% CI
  `[-.6318,-.5881]` at fivefold multiplicity.
- Abstract, Introduction, Discussion, and Conclusion now limit exact-copy
  invariance to the family-wise score under fixed evidence grouping and state
  that score-level invariance does not imply clustering or end-to-end
  invariance.
- Data and Code Availability distinguishes the current development artifact
  from archived release `v1.0.1`.
- No dispatch effect is inferred from the new RQ1 stresses because RQ3 uses a
  separate Candidate-4.1 suite.

## PDF and tooling state

- Tectonic 0.16.9 was installed at
  `/home/ngthtrong/.local/bin/tectonic`; NumPy 2.5.1 and PyMuPDF 1.28.2 were
  installed in the isolated user directory
  `/home/ngthtrong/.local/share/nckh2-rq1-audit/site-packages`.
- Dockerized Tectonic successfully built the integrated PDF. The build has no
  undefined citations/references, LaTeX errors, or overfull boxes. It retains
  non-fatal `algorithm.sty` UTF-8, underfull-box, included-PDF-version, and
  duplicate-object-label warnings.
- PyMuPDF confirms that the current integrated PDF is 17 pages. A temporary,
  uncommitted layout experiment confirms a 15-page result after removing the
  two result figures and headline RQ2/RQ3 table whose values are already in
  tables/prose, tightening the Results summary, and shortening the RQ1 stress
  caption. The author must approve this scientific-layout choice before it is
  applied to `paper/main.tex`.

## Open provenance and publication gates

- The original ZIP is absent. Its recorded SHA-256 is
  `d53624bbb3e681504ce9691a77b93610559183187bfe731a3f7fd10de6e034c2`.
- Colab used Python 3.13.15 with pinned packages. The manifest records the
  version, but the executed protocol did not include `python_version` in its
  hash. The current stricter notebook cannot resume those checkpoints.
- The group has not stated whether saved checkpoints were resumed across a
  Colab runtime change.
- Authoritative camera-ready page limit, upload-file list, response-document
  requirement, deadline time zone, and submission procedure remain unrecorded.
- Final author review, metadata review, archival release, registration, and
  submission remain external actions.

## Work required from the group

| Priority | Owner role | Action | Completion evidence |
|---|---|---|---|
| P0 | Colab runner | Provide the original ZIP and state whether checkpoints were resumed across a runtime change | ZIP SHA-256 matches; runtime/resume history is recorded |
| P0 | Conference contact | Provide authoritative camera-ready instructions | Page limit, files, response requirement, deadline/time zone, and submission route are confirmed |
| P1 | Author group | Review the RQ1 table and the score-versus-clustering invariance interpretation | Scientific wording is accepted or concrete corrections are supplied |
| P1 | Manuscript owner | Review final PDF and all author, ORCID, affiliation, and funding metadata | Final PDF and metadata are approved |
| P2 | Artifact owner | Decide whether to create a new archival release containing the stress artifact | Manuscript points to an exact archive containing every claimed output |
| P2 | Submission owner | Register and upload only after final approval | Registration and submission receipts are retained |

No RQ1/RQ2/RQ3 rerun is assigned by default. A rerun requires a
conclusion-affecting audit defect and a separately approved protocol.

## Next concrete task

Obtain the author's decision on the measured 15-page layout. After that
decision, rebuild and visually inspect the final PDF, rerun the full verifier,
and update this checkpoint with the final page count and layout status.
