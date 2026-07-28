# Revision decision log

**Locked on:** 2026-07-28  
**Source commit:** `85e8080964303abf13b048400b944ac544d599b3` (`main`)  
**Gate:** R0 / Gate 0  
**Decision authority:** `revision-plan.md`, checked against `phan-bien.md`, the
current manuscript, loop 16–17 records, source code, and generated JSON.

This log records the decisions that implementation and manuscript work must
follow. A later change to Q1–Q8 reopens Gate 0 and invalidates every downstream
run whose result depends on that decision.

## Audit result

The worktree was clean at the source commit. The audit reproduced the eight
major-concern classifications in `revision-plan.md`:

| Concern | Disposition | Direct repository evidence |
|---|---|---|
| MC1 | Accept | `weighting.py::sparsify` retains equality although the proof uses `>`; `implied_distance_cutoff` maps out-of-domain thresholds to numerical values; the manuscript overstates the additive case. |
| MC2 | Accept in part | `exp12_multiseed.py` compares a shared default; `exp13_theta_calibration.py` selects on a single seed without an untouched test split. |
| MC3 | Accept; external branch blocked | `generate.py::_GROUP_SPECS` deliberately creates cases for time/context; no authorized real incident-level dataset exists in the workspace. |
| MC4 | Accept in part | `priority.py` gates `E`, `F`, and `N`, but sums raw `V`; both `N` and `V` are report-level sums. The score is nevertheless bounded by `tanh` and `mu`. |
| MC5 | Accept | `exp7_equity_outcome.py` derives its main endpoint from fields also used in priority and does not make the efficiency trade-off co-primary. |
| MC6 | Accept | `exp4_baselines.py` is single-seed and its same-graph methods primarily test the partitioner; direct tuned spatio-temporal and factorial baselines are absent. |
| MC7 | Accept | `metrics.py::cluster_quality` excludes `gt=-1`; split, merge, false-destination, and review-burden measures are absent from the primary result contract. |
| MC8 | Accept | both READMEs are stale; dependencies are unpinned; current runs overwrite `demo/results`; runtime and packet artifacts lack required provenance. |

Historical result files are evidence about the old pipeline only. They are not
eligible as evidence for the revised claims.

## Q1 — Manuscript scope without real data

**Decision: locked — synthetic methodological study.**

The minimum submission is a methodological, synthetic proof-of-concept. It
must not claim field effectiveness, rescue impact, deployment readiness, or
validated misinformation detection. Real-data and expert-validation work are
enhancement branches and do not block synthetic P0 work.

**External status:** no authorized real flood-report dataset, annotations,
access terms, or rescue/logistics experts are present in the workspace.
Collection and endorsement therefore remain `external-blocked`; only protocols
and explicit fallback wording may be produced locally.

## Q2 — Central mathematical statement

**Decision: locked — edge localization plus a conditional cluster corollary.**

Let \(B=\beta+\gamma\), with non-negative coefficients.

- For the product similarity, \(w^\times\le B S_{\rm geo}\). If
  \(B>0\) and \(0<\theta<B\), every edge satisfying \(w^\times>\theta\)
  has
  \(d<\sigma\sqrt{2\log(B/\theta)}\). If \(\theta\ge B\), no such edge
  exists. The looser \(B\le1\) form using \(\log(1/\theta)\) may be shown
  only as a corollary.
- A cluster statement is conditional on measured or enforced finite
  hop-diameter \(h\): geographic diameter is below \(h r_\theta\). The
  pipeline does not know a useful \(h\) ex ante unless a separate mechanism
  enforces one.
- For the additive form
  \(w^+=\alpha S_{\rm geo}+\beta S_{\rm temp}+\gamma S_{\rm ctx}\),
  no finite, data-independent geographic cutoff follows when
  \(\theta\le B\). When \(\alpha>0\) and
  \(B<\theta<B+\alpha\), a retained edge satisfies
  \(d<\sigma\sqrt{2\log(\alpha/(\theta-B))}\). At
  \(\theta\ge B+\alpha\), no edge can satisfy the strict threshold.
- Proof, code, and diagnostics use the strict relation
  `weight > theta`; equality is removed.

No result may be called an ex-ante compact-cluster guarantee unless the
pipeline actually enforces the stated \(h\).

## Q3 — Meaning of “kernel”

**Decision: locked — use “product similarity” in claims.**

“Kernel” may appear only when explicitly defined as a similarity function or
when discussing prior kernel methods. No Mercer/PSD property is claimed for
the Haversine-domain construction. The revised title, abstract, method, and
conclusion use “product similarity”.

## Q4 — `N`, `V`, and duplicate-report semantics

**Decision: locked — incident truth is latent; inference uses observable
report evidence only.**

- Every generated incident has latent `N_true` and `V_true`.
- Reports contain noisy, partial observations of that incident and a hidden
  `incident_id` used only by generation and evaluation.
- Inference, clustering, priority, and tuning may not read `incident_id`,
  `N_true`, or `V_true`.
- `N`, `V`, `F`, and `E` supplied by a report all pass through the same
  confidence/provenance policy. A report with `C=0` contributes zero to every
  report-derived component.
- Candidate aggregators are raw sum, capped sum, max, confidence-weighted
  robust aggregation, and inference-feasible duplicate-aware aggregation.
  Selection uses development/calibration only. Raw legacy behavior remains an
  explicit ablation, never the revised default.
- The default estimator must be exactly invariant to an exact duplicate with
  the same observable fingerprint. Near-duplicate tolerance and marginal
  influence limits are declared before test.
- If unique population cannot be identified from observable reports, the
  quantity is named “reported demand evidence”, not population truth.

## Q5 — Confidence threat model

**Decision: locked.**

Required cases are exact duplicates, near duplicates, low-confidence inflation
of each of `N/V/F/E`, coordinated high-confidence campaigns, and missing
image/corroboration. The objective is bounded marginal influence under
uncertainty, not a claim that `C` detects misinformation. A successful
high-confidence campaign remains a known human-verification failure mode.

## Q6 — Tuning and test protocol

**Decision: locked.**

- Development seeds: `1000..1019`.
- Calibration seeds: `2000..2019`.
- Test seeds: `3000..3039`.
- The three sets are disjoint and materialized in a checksum-protected
  manifest.
- Each method/track evaluates at most 128 candidate configurations (or its
  complete smaller grid) with the same metric contract and stopping policy.
- Track A uses labels on calibration subject to operational constraints.
- Track B is label-free and uses retained density, stability, connectivity,
  diameter, and workload constraints.
- Selected configurations and the full protocol are hashed before test.
  Tuning modules cannot import the test list, and test intermediates are not
  exposed before protocol lock.
- A post-test code defect requires an incident record and a symmetric rerun of
  every affected method; results never expand the search space.

## Q7 — Endpoints and multiplicity

**Decision: locked.**

Clustering co-primary families are:

1. ARI on labeled reports;
2. incident split/merge loss;
3. false operational destinations/operator review burden over all reports.

Noise handling and geographic compactness are key secondary endpoints.
Dispatch primary outcomes are generated latent deadline/harm measures that do
not algebraically reuse priority, `core`, `F_max`, or `V_agg`. Mean response,
deadline misses, maximum/CVaR response, and unique-population coverage are
reported together as a Pareto trade-off. If the independent outcome model
fails its preregistered validity checks, dispatch is labeled illustrative.

Paired bootstrap intervals and paired Wilcoxon tests use untouched test seeds.
Holm correction is applied within each declared co-primary family. Effect
sizes, mean, SD, median, CI, denominators, and all unfavorable results are
retained.

## Q8 — Source of truth and artifact promotion

**Decision: locked.**

- Candidate output is written only below
  `demo/artifacts/runs/<run_id>/`; development runs never overwrite
  `demo/data/dataset.json` or `demo/results/**`.
- Run IDs contain UTC time, git short hash, and protocol-hash prefix.
- Every run records code/dirty-patch identity, environment and hardware,
  protocol/config/seed/dataset hashes, command, timestamps, exit status, and
  checksums.
- Exactly one Gate-3-approved run may be promoted by a script. Promotion
  cannot proceed with an incomplete manifest.
- Every quantitative manuscript claim maps to a locked manifest plus a JSON
  selector or source constant. Negative and tied results are never deleted.

## Gate 0 outcome

**PASS.** Q1–Q8 are locked and contain no unresolved placeholders. C5
collection, D3 access
confirmation, D4 real-data evaluation, public DOI/repository release, ORCID,
and authorship approval are explicitly external-blocked. All locally
executable workstreams may proceed.
