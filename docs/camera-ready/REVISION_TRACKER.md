# ISDS-2026 camera-ready evidence tracker

Submission baseline: tag `v1.0.1` (`be95d4c`). Camera-ready integration
baseline: branch `clean` at `9fbc49c`. Deadline stated in the acceptance email:
16 September 2026; the group must confirm the time zone and final instructions.

This tracker evaluates the committee comments against the study's direction
and repository evidence. It is an internal decision record, not a checklist
that the manuscript must reproduce and not part of the camera-ready narrative.

Status meanings: **integrated** is backed by audited evidence and manuscript
text; **retained** means the existing position remains appropriate;
**conditional** requires an external decision or artifact.

| Observation | Evidence assessment | Fit with the study | Camera-ready decision | Status |
|---|---|---|---|---|
| Proposed methods do not consistently beat baselines; practical value needs a narrower statement | Correct: the adjusted RQ1 comparisons do not establish composition superiority, and RQ2/RQ3 do not establish policy benefit | Central to an audit and failure-boundary study | Frame edge localization, fixed-group score invariance, and downstream failure exposure as diagnostic checks | Integrated |
| Synthetic-data realism and representativeness need clearer boundaries | Correct: geographic anchors are documented, but incidents, reports, attacks, labels, and operational outcomes are simulated; source snapshots and row lineage are unavailable | Central to credible scope claims | Keep the construction table and explicit non-representativeness limitations | Integrated |
| Robustness under measurement noise, copies, and resource variation should be exposed | Correct and directly testable without changing the locked methods | Strengthens the stated stress-testing direction | Report audited RQ1 fixed stresses, all 11 RQ2 scenarios, and all three RQ3 resource conditions | Integrated |
| ARI alone is insufficient for operational utility | Correct: RQ1 and RQ3 use different suites, and dispatch endpoints contradict a simple proxy-to-utility inference | Central to end-to-end failure analysis | Keep RQ1 clustering and RQ3 dispatch conclusions separate; retain 40 seed-level RQ3 pairs | Integrated |
| Misinformation and field readiness are not demonstrated | Correct: the coordinated campaign is adverse and no field or expert validation exists | Defines the valid evidence boundary | Retain explicit limitations; make no deployment, policy, or misinformation-robustness claim | Retained |
| Product/Additive terms and comparator roles require definitions | Correct and consistent with the implemented methods | Improves reproducibility without changing the contribution | Retain definitions, separate tuning grids, and comparator-control rationale | Integrated |
| Top-k pseudocode must match executable behavior | Correct: the code thresholds, selects endpoint-wise directed top-k, then symmetrizes by OR | Required for technical accuracy | Describe the implementation exactly; do not redesign the method | Integrated |
| Matched-density isolates the composition operator | Too strong: density is approximately aligned, while weights and edge membership still differ | A causal claim would exceed the study | Retain it as a non-causal density-control diagnostic | Retained |
| Camera-ready format, page limit, and upload package | Not established by repository evidence; only the email deadline is recorded | Publication requirement rather than a scientific result | Apply only after the group supplies authoritative instructions | Conditional |

## RQ1 stress evidence gate

- Numerical audit passed: 288 hashes, 280 checkpoints, 1,400 unique fits,
  92,617 mapping rows, 35 summaries, and 300 independently replayed paired
  bootstrap rows.
- Control ARI and pairwise F1 match the locked benchmark per run; no retuning
  or hidden failure was found.
- Both the slight 2x improvement and the adverse 5x graph-method collapse are
  retained. The study does not assign a causal mechanism to the discontinuity.
- Score-level exact-copy invariance is stated only for fixed evidence grouping
  and other score inputs; it is not extended to upstream clustering or the
  end-to-end pipeline.
- Package provenance is conditional on receiving the original ZIP with
  SHA-256 `d53624bbb3e681504ce9691a77b93610559183187bfe731a3f7fd10de6e034c2`
  and the group's runtime/resume confirmation.

## Open publication gates

- The current integrated PDF is 17 pages. A temporary build verified that
  removing the two figures whose values are already in tables/prose, removing
  the duplicate headline RQ2/RQ3 table, and tightening the Results summary and
  RQ1 stress caption produces 15 pages without changing reported results.
- Final page/line references in the internal response draft wait for the final
  layout.
- Submission, registration, archival release creation, and final author-group
  approval have not occurred.
