# Draft response to reviewers

Paper 6444: *Stress-Testing Product-Gated Clustering and Bounded Priority
Ranking for Flood-Rescue Reports: A Synthetic Study*

This draft describes changes already supported by the repository. Text marked
**PENDING GROUP RERUN** must be replaced with audited results before this
document is submitted or shared as a final response.

## General response

We thank the reviewers for recognizing the importance, auditability, and
honest reporting of negative results in this study. We revised the manuscript
to state the contribution more precisely: the proposed components provide
checkable safeguards and expose failure propagation, but the experiments do
not establish general performance superiority, policy validity, or field
readiness. We also expanded the synthetic-data construction and limitations,
defined the named method variants, explained the comparator roles, and exposed
additional robustness and resource-condition results.

## Reviewer 1

### 1. Specific advantage and practical value

We agree that neither proposed component consistently outperforms the
baselines. The revised Introduction and Discussion now identify three narrower
benefits supported by the evidence: a finite edge-localization condition for
the product gate, invariance of the family-wise score to exact transport
copies, and an end-to-end audit that reveals when clustering quality does not
improve dispatch. We explicitly state that these are engineering checks and
diagnostic findings rather than evidence of overall superiority or field
benefit.

### 2. Realism of the synthetic scenarios

We added a construction table in Experimental Design. Generator 3.0 uses the
Copernicus EMSR848 event context, OSM-derived geographic anchors, and a 2025
WorldPop constrained population surface. Its incidents, reports, duplicates,
attacks, reported need, vulnerability, and labels remain simulated.
Candidate 4.1 is fully synthetic and is not described as EMSR848-anchored.
Benefit, deadlines, service demand, access delay, and harm are also simulated
evaluator-only outputs. We further disclose that the archived artifact lacks
the raw upstream snapshots, source checksums, and per-row lineage, so the
evaluation does not demonstrate field representativeness.

### 3. Additional robustness experiments

The revised Results now report all 11 existing RQ2 perturbation scenarios,
including exact and near duplicates, missingness, contradictory evidence,
four low-confidence inflation attacks, and a coordinated high-confidence
campaign. It also reports descriptive results under all three locked RQ3
resource conditions.

**PENDING GROUP RERUN:** We prepared a fixed, no-retuning RQ1 stress protocol
covering independent Gaussian GPS noise at 100 m and 300 m, timestamp noise at
15 min and 60 min, and exact transport-copy multiplicities of 2 and 5. The
protocol applies five fixed methods to 40 locked test runs (1,400 fits) and
uses paired bootstrap differences from the unperturbed condition. Insert the
audited result and manuscript location here after the group returns the ZIP.

### Minor comments: terminology and baselines

The revised Introduction defines Product Louvain, Product Leiden, Additive
Louvain, and matched-density Additive. Experimental Design now explains that
the graph variants examine affinity composition, community detection, and
sparsity; the density and geometry methods provide non-community alternatives.
The ranking baselines isolate raw multiplicity, single-factor ordering, linear
combination, chance ordering, and travel time. None is described as an endorsed
rescue policy.

## Reviewer 2

### 1. Downstream alignment

We agree. The revised Results separate the RQ1 clustering suite from the
Candidate-4.1 RQ3 suite and do not infer dispatch utility from ARI. We now show
descriptive harm and deadline-miss means for each of the lean, nominal, and
surge resource conditions, and relate them to split, merge, and fake-only
destinations. The primary RQ3 inference still averages the three conditions
within each seed, retaining 40 independent seed-level pairs. The expanded
analysis reinforces the original conclusion: attractive proxy metrics do not
guarantee operational benefit.

### 2. Field readiness

We retained and strengthened the limitation throughout the Abstract,
Experimental Design, Discussion, and Conclusion. The work does not establish
misinformation robustness, expert policy validity, source authenticity, or
field deployment readiness. In particular, the coordinated high-confidence
campaign remains a documented adverse result.

## Reviewer 3

Reviewer 3 raises the same substantive issues concerning advantage, synthetic
realism, robustness, downstream alignment, misinformation/field readiness,
terminology, and baseline rationale. The corresponding revisions are described
in the responses above. The final response will add exact page and line numbers
after the conference format and final PDF pagination are known.
