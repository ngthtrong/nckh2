# Baseline and ablation protocol

**Task:** E1  
**Status:** registry frozen before test  
**Machine-readable source:** `demo/protocol/baselines.json`

## Questions answered

The registry separates four scientific questions:

1. Does product composition help after fair calibration?
2. Do geography, time, and context each contribute?
3. Does the representation help independently of the partitioner?
4. Can a direct spatio-temporal or spatially constrained method obtain the
   same operational quality?

Coordinate-only K-Means remains a weak diagnostic. It is not presented as an
equivalent competitor because it lacks time and context.

## Common contract

All methods use the same development/calibration/test seeds, observable report
view, endpoint implementation, candidate cap, and failure policy. Each main
method evaluates no more than 128 configurations per track. Calibration
selects configurations; test reports only the frozen selection.

The shared operational-calibration rules are machine-readable in
`demo/protocol/calibration_contract.json`. Every method uses the same
standard review policy, where an unresolved report is one queue item and the
predicted-noise label is never a destination. Label-free stability is adjusted
Rand agreement between a partition and the partition obtained after reversing
observable report order and mapping labels back; it never reads incident
truth. Numeric stability, workload, diameter, graph connectivity, and graph
density guardrails apply to per-seed extrema, as declared in that contract.

For graph methods, threshold candidates are calibration-derived weight
quantiles rather than shared raw values across incompatible weight scales.
Matched retained-fraction and mean-degree comparisons are additional locked
tracks. A preset or oracle `K` is always marked diagnostic.

Composition selection is joint but symmetric: among operationally feasible
product configurations, Exp15 selects the objective-best configuration for
which every declared non-product composition family has at least one feasible
retained-fraction/mean-degree match. Each comparator is then selected only
inside its matched feasible set. This prevents an independently optimal
product density from making the preregistered comparison impossible; it does
not enlarge any grid or relax any guardrail.

Noise label `-1` means unassigned and is not a cluster. Methods without a
noise mechanism assign every report to a cluster; their noise absorption and
false destinations are evaluated as such.

## Registry

- **Product similarity + Louvain:** proposed representation and partitioner.
- **Additive similarity + Louvain:** direct composition family comparison.
- **Convex multiple-similarity + Louvain:** feasible calibration of geographic,
  temporal, and contextual mixture weights; not claimed as a full learned
  multiple-kernel method. Its symmetric seven-point simplex grid (three
  dominant vertices, three two-component faces, and the equal mixture) crosses
  four quantiles, two k-NN choices, and two resolutions: 112 configurations,
  below the common ceiling.
- **ST-DBSCAN:** direct spatial/temporal density baseline.
- **DBSCAN/HDBSCAN on standardized geo-time-context features:** density
  alternatives with explicit feature scaling and equivalent inputs.
- **Spatially constrained agglomerative:** context/time feature distances with
  a geographic connectivity graph; tests an explicit spatial constraint.
- **Leiden on the selected product graph:** same representation, alternative
  partitioner.
- **Leiden/spectral on selected product affinity:** same-representation
  partitioner diagnostics; spectral `K` is calibration-chosen and an
  oracle-`K` version is upper-bound-only.

Package-dependent methods may be replaced only before Gate 2, with the reason,
license, evaluation count, and implementable equivalent recorded. Silent
omission is prohibited.

Each registry row now records a falsifiable method-specific hypothesis,
implementation entry point, exact dependency set, implementation status, and
literature identifiers. The top-level dependency audit was generated from the
installed metadata of the `requirements.lock` environment on 2026-07-29.
BSD-family packages are available in the locked environment. `leidenalg` and
`igraph` are also available, but their GPL redistribution obligations require
release review; this registry records feasibility and does not offer legal
advice. Repository-local adapters introduce no additional third-party
dependency. All five required adapters are now available: convex similarity,
direct conjunctive ST-DBSCAN, standardized geo-time-context DBSCAN/HDBSCAN,
and spatially constrained agglomerative.

The literature audit anchors the registry to the original or canonical method
sources: Blondel et al. for Louvain, Birant and Kut for ST-DBSCAN, Ester et al.
for DBSCAN, Campello et al. for hierarchical density clustering, Traag et al.
for Leiden, Ng et al. for spectral clustering, and the scikit-learn
connectivity-constraint specification for the implemented spatially constrained
agglomerative adapter. The convex-mixture comparator is deliberately described
as a feasible similarity mixture, not as a learned multiple-kernel method.
The spatial adapter partitions disconnected geographic components before
agglomeration so the library cannot silently complete the connectivity graph.

## Factorial ablations

Clustering runs all 16 on/off combinations of geography, time, context, and
k-NN. An “off” component is removed from the formula, not set to a misleading
scale; retained density is matched where required.

The cell with geography, time, and context all off contains no data-dependent
similarity. A strict threshold can therefore yield only a degenerate graph
(and tied k-NN cannot generally match both targets). It remains in the
16-cell table with `density_matched=false`; it is never relabeled as a matched
comparison or silently dropped. Any main effect spanning this cell is reported
as a full-factorial diagnostic and read together with the match-failure count.

Priority runs the declared combinations of confidence gate, vulnerability
amplification, and aggregation estimator. All interaction orders are reported:
orders 1–4 for the clustering factorial and 1–3 for priority. Main effects are
not interpreted without checking interactions. Effects, paired intervals,
Holm-corrected tests, evaluation counts, failures, and wall time are reported.

## Selection and reporting

Track A maximizes labeled-report ARI under the frozen stability, connectivity,
diameter, workload, and applicable graph-density constraints. Track B is
label-free and maximizes reverse-order partition stability under the same
operational constraints. Ties use the
predeclared order: lower burden, lower complexity, then lexical config hash.

Test output reports co-primary and secondary endpoints, per-family errors,
configuration/evaluation counts, calibration wall time, and test wall time.
Negative, tied, failed, and infeasible methods remain in the table.
