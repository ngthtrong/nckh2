# Draft response to reviewers

Paper 6444: *Stress-Testing Product-Gated Clustering and Bounded Priority
Ranking for Flood-Rescue Reports: A Synthetic Study*

This is an internal response draft. It describes only changes supported by the
repository and should be submitted only if the conference or author group
requires a response document. The current final-layout draft is 15 pages. The
page references below identify the generated camera-ready PDF and must be
refreshed if the manuscript changes after author sign-off.

## General response

We thank the reviewers for recognizing the importance, auditability, and
honest reporting of negative results in this study. We revised the manuscript
to state the contribution more precisely: the proposed components provide
checkable safeguards and expose failure propagation, but the experiments do
not establish general performance superiority, policy validity, or field
readiness. We also expanded the synthetic-data construction and limitations,
defined the named method variants, explained the comparator roles, and exposed
additional robustness and resource-condition results. The Results are now
organized by RQ so clustering, ranking, and dispatch safeguards and
limitations are assessed separately.

The fixed RQ1 measurement/copy stress is the additional experiment introduced
for the camera-ready revision. The complete 11-scenario RQ2 table, the
resource-specific RQ3 means, and the 840-observation local sensitivity study
expand reporting of analyses already present in the submitted study and are
not presented as newly collected field evidence.

## Reviewer 1

### 1. Specific advantage and practical value

We agree that neither proposed component consistently outperforms the
baselines. The revised Introduction and Discussion now identify three narrower
benefits supported by the evidence: a finite edge-localization condition for
the product gate, invariance of the family-wise score to exact transport copies
when evidence grouping and other score inputs are fixed, and an end-to-end
audit that reveals when clustering quality does not improve dispatch. We
explicitly state that these are engineering checks and diagnostic findings
rather than evidence of overall superiority or field benefit (Introduction,
pp. 2--3; Discussion, p. 13).

### 2. Realism of the synthetic scenarios

We added a construction table in Experimental Design. Generator 3.0 uses the
Copernicus EMSR848 event context, OSM-derived geographic anchors, and a 2025
WorldPop constrained population surface. Its incidents, reports, duplicates,
attacks, reported need, vulnerability, and labels remain simulated.
Candidate 4.1 is fully synthetic and is not described as EMSR848-anchored.
Benefit, deadlines, service demand, access delay, and harm are also simulated
evaluator-only outputs. We further disclose that the archived artifact lacks
the raw upstream snapshots, source checksums, and per-row lineage, so the
evaluation does not demonstrate field representativeness. The construction
table appears on p. 9 and the corresponding validity limits on p. 13.

### 3. Additional robustness experiments

The revised Results now report all 11 existing RQ2 perturbation scenarios,
including exact and near duplicates, missingness, contradictory evidence,
four low-confidence inflation attacks, and a coordinated high-confidence
campaign. It also reports descriptive results under all three locked RQ3
resource conditions.

The fixed, no-retuning RQ1 stress protocol covers independent Gaussian GPS
noise at 100 m and 300 m, timestamp noise at 15 min and 60 min, and exact
transport-copy multiplicities of 2 and 5. It applies five fixed methods to 40
locked test runs (1,400 fits) and uses paired bootstrap differences from each
method's unperturbed control. All 1,400 rows, 280 checkpoints, artifact hashes,
copy mappings, summaries, and 300 paired effects passed independent audit in
both the primary run and an unpooled replication. The manuscript heatmap uses
the primary run selected before comparison.

The fixed protocol is defined on p. 8, its paired results begin on p. 9, and
the benchmark table and annotated heatmap appear on p. 10. The expanded RQ2
table is on p. 11; the resource-specific RQ3 figure is on p. 12.

All tested GPS and timestamp conditions lower mean ARI. No method has the
highest mean ARI in every condition. Twofold exact copies slightly increase
mean ARI for the four graph methods, whereas fivefold copies reduce them to
approximately .29--.30. Product Louvain falls from .9072 to .2964, a paired
change of -.6108 with unadjusted bootstrap 95% CI [-.6318,-.5881]. Geo-time
DBSCAN remains at .4978 under exact copying from a lower control baseline. The
manuscript distinguishes score-level exact-copy invariance under fixed
grouping from clustering and end-to-end invariance, and does not assign a
causal mechanism to the graph-method discontinuity.

The replication changes 43 original-report ARI rows, all for graph methods at
twofold copies. Its aggregate twofold values differ slightly, while control,
GPS, timestamp, and fivefold-copy ARI and the main conclusions are unchanged.
The runs are not pooled, and the differences are not attributed to Python or
sparsification without an isolating experiment.

### Minor comments: terminology and baselines

The revised Introduction defines Product Louvain, Product Leiden, Additive
Louvain, and matched-density Additive. Experimental Design now explains that
the graph variants examine affinity composition, community detection, and
sparsity; the density and geometry methods provide non-community alternatives.
The ranking baselines isolate raw multiplicity, single-factor ordering, linear
combination, chance ordering, and travel time. None is described as an endorsed
rescue policy.

The Abstract now also identifies Louvain and Leiden as community detectors and
Product/Additive as graph-affinity constructions, so the terminology is
readable from its first occurrence (Abstract, p. 1; full definitions, p. 2).

## Reviewer 2

### 1. Downstream alignment

We agree. The revised Results separate the RQ1 clustering suite from the
Candidate-4.1 RQ2/RQ3 suite and do not infer dispatch utility from ARI. RQ2
uses oracle incident grouping to isolate ranking; because alignment remains
weak there, the limitation cannot be attributed solely to clustering. A new
two-panel presentation shows descriptive harm and deadline-miss means for the
lean, nominal, and surge resource conditions and relates them to split, merge,
and fake-only destinations. The primary RQ3 inference still averages the three
conditions within each seed, retaining 40 independent seed-level pairs. The
expanded analysis reinforces the original conclusion: attractive proxy
metrics do not guarantee operational benefit.

### 2. Field readiness

We retained and strengthened the limitation throughout the Abstract,
Experimental Design, Discussion, and Conclusion. The work does not establish
misinformation robustness, expert policy validity, source authenticity, or
field deployment readiness. In particular, the coordinated high-confidence
campaign remains a documented adverse result (Abstract, p. 1; Discussion and
Conclusion, pp. 13--14).

## Reviewer 3

Reviewer 3 raises the same substantive issues concerning advantage, synthetic
realism, robustness, downstream alignment, misinformation/field readiness,
terminology, and baseline rationale. The corresponding revisions are described
in the responses above. Exact page and line references should use the approved
submission PDF rather than this internal draft.
