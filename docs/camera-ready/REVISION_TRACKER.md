# ISDS-2026 reviewer revision tracker

Baseline: submission 6444, Git tag `v1.0.1` (`be95d4c`).  Working baseline:
`clean` at `d73549b` before this revision. Deadline stated in the acceptance
email: 16 September 2026.

Status meanings: **complete** is backed by tracked text or verified existing
artifacts; **prepared** means a reproducible rerun package exists but the group
has not returned results; **waiting** requires external information.

| Reviewer comment | Manuscript response | Evidence | Status |
|---|---|---|---|
| R1/R3: proposed methods do not consistently beat baselines; explain advantage and practical value | Introduction contributions and Discussion distinguish checkable spatial localization, exact-copy invariance, and downstream failure detection from superiority or field utility | RQ1 theorem/results; RQ2 robustness CSV; RQ3 seed-level analysis | Complete |
| R1/R3: justify realism and representativeness of synthetic data | Experimental Design now separates geographic anchors, simulated reports, simulated operational truth, and unsupported representativeness claims for generator 3.0 and Candidate 4.1 | `src/data/README.md`, run manifests, Copernicus EMSR848 activation record, WorldPop dataset record | Complete |
| R1/R3: add robustness under noise, duplication, and operational variation | Results now report all 11 existing RQ2 stress scenarios and the three locked RQ3 resource scenarios. A fixed RQ1 GPS/time/copy experiment is ready for group execution | RQ2/RQ3 manifest checks pass; `src/results/RQ1_Reviewer_Stress_Colab.ipynb` | Prepared; group result pending |
| R2/R3: ARI is poorly aligned with operational utility | RQ3 text explicitly interprets split/merge/fake destinations and reports resource-specific descriptive means while retaining 40 seed-level pairs for primary inference | `rq3_partition_losses.csv`, `rq3_destination_assignments.csv`, seed-level reanalysis provenance | Complete |
| R2/R3: no misinformation, policy, or field readiness proof | Abstract, Results, Discussion, data-realism table, and Conclusion retain the coordinated-campaign failure and deployment limitations | RQ2 coordinated-campaign rows; manuscript threats to validity | Complete |
| R1/R3: define product/additive terms | Definitions are placed at the first detailed clustering discussion; the abstract describes additive affinity and spatially gated product affinity | Similarity equations and selected configurations | Complete |
| R1/R3: explain baseline selection | Experimental Design groups clustering baselines by the question each controls; ranking section does the same for policy comparators | Locked RQ1/RQ2/RQ3 configurations | Complete |
| Internal consistency: top-k pseudocode | Pseudocode now keeps only each endpoint's top-k above-threshold neighbours and symmetrizes by OR | Exact RQ1 benchmark notebook at `6ac75c2` | Complete |
| Internal consistency: tuning grids | Paper now records the actual Product and Additive grids separately | RQ1 notebook/configuration snapshot at `6ac75c2` | Complete |
| Internal consistency: matched-density claim | Language now says the diagnostic reduces density imbalance but does not identify a causal operator effect | Density diagnostics and paper discussion | Complete |
| Camera-ready format, page limit, and required files | Apply conference instructions when received; scientific cuts or metadata changes require group confirmation | Follow-up email not yet received | Waiting |

## Evidence gates

- Do not add RQ1 supplementary stress results to the paper until all 40 test
  runs, seven conditions, and five methods are present exactly once (1,400 fit
  rows), the protocol/configuration hashes match, and no failure is hidden.
- Keep adverse and null results. Do not tune from the RQ1 test stresses.
- Treat RQ2 scenario summaries and RQ3 resource summaries as descriptive.
  Primary RQ3 inference remains 40 seed-level pairs after averaging the three
  resource scenarios within seed.
- The archived upstream geographic snapshots, source checksums, and per-row
  lineage are unavailable. Current source pages describe provenance intent but
  do not independently verify each generated row.
