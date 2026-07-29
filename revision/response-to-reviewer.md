# Response to the independent reviewer

Manuscript: *Product-Similarity Graph Clustering and Bounded Priority
Heuristics for Flood-Rescue Reports: A Synthetic Held-Out Study*

We thank the reviewer for the detailed Reject-and-Resubmit report. We accepted
all eight major concerns as scientific work items. The revision changes the
method, evaluation protocol, evidence base, and scope rather than replacing
isolated manuscript numbers. We did not optimize for a favorable held-out
result: negative, tied, infeasible, and failed comparisons remain in the
locked artifact and in the revised discussion.

The revised evidence chain is:

1. Gate 1 freezes method, generator v4, schema, and 80 synthetic datasets.
2. Gate 2 freezes calibration selections and the complete protocol before test.
3. One authorized X0 invocation evaluates all selected configurations on all
   40 test seeds.
4. Gate 3 independently recomputes the result and locks the accepted run.
5. G0 promotes the result transactionally and generates 448 base selectors,
   a numeric claim catalog, and the manuscript macros.

The accepted X0 run is
`20260728T213934Z-85f2a6686a1b-9797f31f-x0-exp23-heldout`; its manifest SHA-256
is `cbedfe1c7089540c050929bae913fea1efb0231f36d199339c3b451ca80d11b5`.
The complete binding is in `revision/result-lock.json`.

## Major concerns

### MC1 — Mathematical scope and additive threshold regions

**Disposition: accepted and corrected; the requested ex-ante cluster guarantee
is not claimed.**

We replaced the old statement with the complete domain analysis in
`revision/math-spec.md` and the revised Method section.

- Let \(B=\beta+\gamma\). For \(B>0\) and \(0<\theta<B\), a retained product
  edge satisfies
  \(d<\sigma\sqrt{2\log(B/\theta)}\).
- At \(\theta\ge B\), the product retained set is empty; at
  \(\theta\le0\), no non-trivial threshold-induced cutoff follows.
- The component statement is explicitly conditional on observed finite
  hop-diameter \(h\). The pipeline does not control a useful \(h\), so the
  paper no longer calls this an operational compact-cluster guarantee.
- For additive similarity, the finite region
  \(B<\theta<B+\alpha\) and radius
  \(\sigma\sqrt{2\log(\alpha/(\theta-B))}\) are now stated. The
  low-threshold and empty regions are distinguished.
- Code and proof use strict retention \(w>\theta\); equality is removed.

Executable boundary/domain tests cover finite, empty, and unbounded states.
The old out-of-domain violation counts and figure were removed from the
manuscript rather than repurposed as revised evidence. Because no Gate-3
accepted Exp14 table exists, we do not add new empirical \(h\)-tightness
numbers to the paper.

Evidence: `revision/math-spec.md`,
`demo/pipeline/weighting.py`, theorem tests, and the revised manuscript
sections “Product Similarity and Localization Domain” and “Discussion and
Threats to Validity.”

### MC2 — Unfair shared-threshold product/additive comparison

**Disposition: accepted and addressed with disjoint calibration/test data.**

The historical shared-default comparison is no longer primary and none of its
numbers remains in the revised manuscript. The new protocol uses 20
development, 20 calibration, and 40 untouched test seeds. Each method has the
same search ceiling and operational constraints. Graph thresholds are
calibration-derived quantiles; composition comparisons require feasible
matched retained fraction and mean degree. Two tracks are frozen:

- benchmark label-aware calibration under operational constraints; and
- operational label-free calibration using reverse-order stability and the
  same constraints.

Gate 2 promoted 12 feasible method-track configurations and retained eight
authenticated no-feasible exclusions. X0 evaluated the selected set once over
all 40 test seeds. Product Louvain exceeds additive Louvain on ARI in both
tracks, but the paper also reports additive’s smaller destination diameter and
other adverse trade-offs.

Evidence: `demo/protocol/seed_manifest.json`,
`demo/protocol/calibration_contract.json`,
`demo/protocol/selected_configs.json`, `revision/gate2-lock.json`,
`revision/gate3-lock.json`, and selectors beginning
`clustering.paired.*.additive_louvain.vs.product_louvain`.

### MC3 — Endogenous synthetic data and external validity

**Disposition: accepted; internal protocol strengthened, external validation
remains unresolved.**

Generator v4 adds latent incident truth, duplicates, missingness, adversarial
cases, and independent outcome parameters. Gate 1 applies only
method-agnostic quality checks and freezes all 80 datasets before calibration.
These changes improve internal validity but do not make an author-designed
generator external evidence.

No authorized real flood-report source, usage rights, incident annotations, or
annotators are available in the repository. We therefore changed the title,
abstract, contributions, threats, and conclusion to “synthetic methodological
study” and removed field-effectiveness and deployment claims. We also provide
`revision/real-data-protocol.md`, but do not present that protocol as completed
validation.

Evidence: `revision/data-spec.md`, `revision/gate1-lock.json`,
`demo/results/tables/data_distribution_report_v4.json`, and
`revision/real-data-protocol.md`.

### MC4 — Confidence bypass and report-level double counting in priority

**Disposition: accepted; implementation corrected, policy/expert validity
remains unresolved.**

The revised estimator:

- gates \(E,F,N,V\) consistently by clipped confidence;
- collapses exact payload duplicates with an inference-visible fingerprint;
- coalesces observable near duplicates with frozen tolerances;
- uses strongest capped \(N/V\) evidence rather than summing reports; and
- names these quantities “reported demand/vulnerability evidence,” not unique
  population estimates.

Latent `N_true` and `V_true` are evaluator-only. Exact duplicates at
multiplicity 10 produce zero priority drift, rank drift, and top-k churn.
However, coordinated distinct high-confidence reports remain a failure:
direction-adjusted revised-versus-legacy priority-drift improvement is
`-0.13788`, CI `[-0.1678232,-0.1084072]`, with revised worse on all 40 seeds.
The revised paper headlines this result and does not claim adversarial-report
robustness.

The caps, weights, and score are not expert-validated. The expert protocol is
provided, but collection remains external-blocked.

Evidence: `revision/priority-contract.md`, `demo/pipeline/priority.py`,
priority/adversarial tests, and selectors
`priority.summary.exact_duplicate_10x.duplicate_aware_robust` and
`priority.paired.coordinated_high_confidence_campaign.priority_drift_abs_normalized`.
The displayed drift, CI, and seed count resolve respectively through that
paired root's `.mean`, `.paired_confidence_interval.0`,
`.paired_confidence_interval.1`, and `.n_seed_pairs` claim IDs.

### MC5 — Self-confirming dispatch metric and incomplete trade-offs

**Disposition: accepted; outcome redesigned, result is negative.**

The new latent harm/deadline model does not algebraically reuse priority,
reported flood, vulnerability, demand, or score components. Three resource
scenarios report latent harm, deadline misses, mean/max/CVaR arrival, equity
gap, workload, workload balance, and unique population reached by deadline.
All policies and endpoints are retained.

The revised priority policy does not show a Holm-significant latent-harm
benefit over legacy priority in any resource scenario. In the nominal
dual-depot scenario, its direction-adjusted harm improvement versus
nearest-first is `-204.935`, CI `[-225.612,-184.895]`; its deadline-miss
improvement is `-0.278125`, CI `[-0.339063,-0.220313]`. These adverse results
are in the main Results table. A concrete countervailing effect is the
direction-adjusted boat-workload-CV benefit `0.034572883`, CI
`[0.01364342665,0.05551125630624994]`, Holm `p=0.006096451763369259`.
We label dispatch illustrative and do not recommend nearest-first universally
because the endpoint trade-offs remain policy-dependent.

Evidence: `revision/priority-contract.md`,
`demo/experiments/exp17_dispatch_outcomes.py`, the `dispatch.*` selector
families, and the manuscript table “Selected dispatch effects.” The manual
values above use the exact roots
`dispatch.paired.nominal_dual_depot.revised_priority.vs.nearest_first.latent_harm`,
`dispatch.paired.nominal_dual_depot.revised_priority.vs.nearest_first.deadline_miss_rate`,
and
`dispatch.paired.nominal_dual_depot.revised_priority.vs.nearest_first.boat_workload_cv`,
with `.mean`, `.paired_confidence_interval.0`,
`.paired_confidence_interval.1`, and (for workload CV)
`.holm_adjusted_p_value`.

### MC6 — Weak baselines and missing factorial ablation

**Disposition: accepted in part and materially expanded.**

The frozen registry includes:

- product and additive Louvain;
- a fixed convex similarity grid (explicitly not called learned
  multiple-kernel clustering);
- tuned ST-DBSCAN;
- standardized geo-time-context DBSCAN/HDBSCAN;
- spatially constrained agglomerative;
- product-graph Leiden/spectral diagnostics.

Every method uses the same calibration ceiling, endpoint contract, and noise
convention. Infeasible DBSCAN/HDBSCAN/spectral method-track pairs remain as
eight authenticated exclusions rather than disappearing. The test result
reports every feasible registered method family in both tracks. ST-DBSCAN
demonstrates a real trade-off: lower ARI but much lower split loss, zero false
destinations, and substantially higher noise rejection.

The clustering factorial evaluates all predeclared binary combinations of
geography, time, context, and k-NN; priority evaluates confidence,
vulnerability, aggregation, and all interaction orders. The artifact retains
80 density-unmatched cells (claim ID
`gate3.retention.factorial_density_match_failures`), and the manuscript warns
against causal interpretation of main effects.

We did not implement a learned multiple-kernel method, and we state this
limitation rather than treating the convex grid as equivalent.

Evidence: `demo/protocol/baselines.json`,
`revision/baseline-protocol.md`, the `clustering.summary.*` and
`factorial.*` selectors.

### MC7 — ARI hides fragmentation, noise, and operator burden

**Disposition: accepted and mostly addressed; multimodal-specific analysis
remains unresolved.**

ARI remains restricted to labeled reports, but it is now co-primary with
incident split/merge loss and false destinations/review burden over all
reports. Noise rejection/absorption and destination diameter are key secondary
endpoints. Noise `-1` is never a destination. The main table reports ARI,
split, merge, false destinations, and noise rejection for every feasible
method on both tracks where applicable.

For product Louvain on the label-aware track, split loss is `0.09375`, merge
loss `0.0340585`, false destinations `34.85`, review burden `35.4` (95% CI
`[35.1,35.7]` across 40 seeds; registered denominator `2026` review decision
units, defined as emitted destinations plus unclustered reports), and noise
rejection `0`. ST-DBSCAN’s split/noise improvements and merge/ARI losses are
reported alongside them. The discussion explicitly states that high ARI does
not remove operational fragmentation.

Evidence: `demo/protocol/metric_contract.json`, `demo/pipeline/metrics.py`,
the `clustering.summary.*` and `clustering.paired.*` selector families, and
Table “Held-out means by calibration track.” Specifically, each manual value
above is rooted at
`clustering.summary.benchmark_label_aware.product_louvain` under
`.incident_split_loss.mean`, `.incident_merge_loss.mean`,
`.false_operational_destinations.mean`, `.operator_review_burden.mean`,
`.operator_review_burden.paired_confidence_interval.0`,
`.operator_review_burden.paired_confidence_interval.1`,
`.operator_review_burden.denominator.analyzed_seeds`,
`.operator_review_burden.denominator.metric_denominator_sum`,
or `.noise_rejection_rate.mean`.

### MC8 — Publication-grade reproducibility

**Disposition: local reproducibility addressed; public DOI/release authority
remains external-blocked.**

The repository now has exact Python dependency pins, isolated no-overwrite
candidate runs, environment/hardware/BLAS capture, input snapshots, per-file
checksums, Gate locks, and a transactional G0 source of truth. Exp22 records
one warm-up and five measured repeats with one thread/core eligibility,
matrix/edge/partition equivalence, peak whole-worker RSS, and honest dense
storage. Packet size is 190--232 bytes (median 205) for application JSON only.
Those three values resolve to `runtime.packet.min_bytes`,
`runtime.packet.max_bytes`, and `runtime.packet.median_bytes`.

The revised README and clean-room verifier use XeLaTeX--BibTeX--XeLaTeX twice,
validate all locked checksums and claim IDs, run tests without another X0
invocation, and audit the PDF log. The complete X0 JSON is promoted as a
lossless gzip archive so the evidence is not confined to gitignored run
directories.

No approved author list/order/contact record, funding or competing-interest
declaration, public repository URL, DOI, ORCID, venue page limit, or release
authority was supplied. The manuscript therefore uses an anonymous author
placeholder and marks both declarations as pending; we do not invent those
values or claim a public immutable release. They remain explicit submission
actions.

Evidence: `pyproject.toml`, `requirements.lock`,
`demo/experiments/artifacts.py`, `revision/result-lock.json`,
`loop/revision/traceability.md`, `reproduce.sh`,
`revision/artifact-package-manifest.json`,
`revision/clean-room-verification.json`, and
`revision/clean-room-report.md`. The final local release boundary and exact
source-state binding are recorded in `revision/final-audit.md` and
`revision/submission-checksums.json`.

## Minor concerns

| Concern | Disposition and evidence |
|---|---|
| Threshold equality | Fixed: code and theorem retain only `weight > theta`; equality tests pass. |
| “Kernel” ambiguity | The title and claims use “product similarity”; no PSD/Mercer property is claimed. |
| Tighter \(B=\beta+\gamma\) bound | The primary theorem is \(B\)-aware and includes every threshold region. |
| `N_ref` saturation | The score definition and threats state saturation at the illustrative fixed reference. |
| Arithmetic latitude/longitude centroid | Retained as metadata and explicitly identified as a non-geodesic limitation. |
| Reused bootstrap seed | Deterministic inference seeds are recorded; paired bootstrap, SD, CI, and test denominator are distinguished. |
| Multiple comparisons | Holm correction is applied within predeclared families and reported with raw tests/effect sizes. |
| SD versus CI | The manuscript labels SD and paired 95% CI separately. |
| Subjective `~` in positioning table | Removed; entries now use explicit yes/no/conditional terms. |
| Related work depth | Added ST-DBSCAN and spatially constrained clustering context; novelty is narrowed to the evaluated property/protocol. |
| Packet assumptions | Schema-derived confidence is used; application-payload scope and excluded overhead are explicit. |
| Stale comments/artifacts | Revision workflow does not use historical tables/figures; stale documentation is replaced or archived. |
| Fully sparse scaling | Not claimed. Candidate pruning is exact, but compatibility storage remains dense \(O(n^2)\). |

## Answers to the reviewer’s questions

1. **How is \(h\) controlled?** It is not. The manuscript now calls the
   component result conditional on observed \(h\), not an operational
   guarantee.
2. **Does additive have a bound above \(\beta+\gamma\)?** Yes. The complete
   finite, empty, and generally unbounded regions are now stated and proved.
3. **Why were \(\theta\ge1\) values counted?** That historical diagnostic was
   invalid for the claimed domain. It is removed; executable checks now count
   only finite-domain rows.
4. **Why was Exp12 not calibrated separately?** That was a design defect. The
   replacement uses separate calibration, matched density/degree, and
   untouched test seeds.
5. **Why was the compact additive configuration omitted?** It is no longer
   omitted conceptually: calibrated additive is evaluated on test, and its
   smaller destination diameter is discussed as an adverse result for product.
6. **Where was the study preregistered?** It was not externally preregistered.
   The manuscript says “pre-specified and checksum-locked before test,” not
   “preregistered.”
7. **How is repeated population counting avoided?** The revised estimator
   collapses duplicates and uses strongest capped evidence rather than sums.
   Without person identity, it does not claim unique population estimation.
8. **Why did \(V\) bypass confidence?** It should not have. The revised
   implementation gates \(V\) consistently and preserves the legacy behavior
   only as an explicit ablation.
9. **Why was the old dispatch metric external?** It was not sufficiently
   independent. The replacement latent outcomes exclude score inputs and
   produce a negative validation result.
10. **How is the old mean-arrival cost interpreted?** Historical Exp7 is no
    longer evidence. The new dispatch artifact jointly reports all declared
    arrival, harm, deadline, equity, workload, and coverage endpoints.
11. **Why were multimodal/split errors omitted?** The general omission is only
    partially corrected: split/merge/noise/destination/review metrics are main
    outcomes, but G0 exposes no multimodal-specific claim selector. The locked
    result preserves the scenario-family table, while the manuscript makes no
    quantitative multimodal claim and identifies dedicated multimodal error
    analysis as unresolved.
12. **Where will code/data be published?** The local artifact is fully bound
    by Gate/result locks, but no release URL/DOI authority was provided. The
    manuscript states this honestly; the final public destination must be
    supplied by the authors during submission.

## Remaining external work

The following are deliberately not marked complete: real-data access and
annotation, expert elicitation, public repository/DOI, author
order/contact/ORCID approval, funding and competing-interest declarations, and
venue-specific page-limit approval. Until those inputs exist, the manuscript
remains scoped as a synthetic methodological study and the priority policy
remains illustrative.
