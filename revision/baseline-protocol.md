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

For graph methods, threshold candidates are calibration-derived weight
quantiles rather than shared raw values across incompatible weight scales.
Matched retained-fraction and mean-degree comparisons are additional locked
tracks. A preset or oracle `K` is always marked diagnostic.

Noise label `-1` means unassigned and is not a cluster. Methods without a
noise mechanism assign every report to a cluster; their noise absorption and
false destinations are evaluated as such.

## Registry

- **Product similarity + Louvain:** proposed representation and partitioner.
- **Additive similarity + Louvain:** direct composition family comparison.
- **Convex multiple-similarity + Louvain:** feasible calibration of geographic,
  temporal, and contextual mixture weights; not claimed as a full learned
  multiple-kernel method.
- **ST-DBSCAN:** direct spatial/temporal density baseline.
- **DBSCAN/HDBSCAN on standardized geo-time-context features:** density
  alternatives with explicit feature scaling and equivalent inputs.
- **Spatially constrained agglomerative:** context/time feature distances with
  a geographic connectivity graph; tests an explicit spatial constraint.
- **Leiden on the selected product graph:** same representation, alternative
  partitioner.
- **Spectral/agglomerative on selected affinity:** same-representation
  partitioner diagnostics; any selected `K` is calibration-chosen and an
  oracle-`K` version is upper-bound-only.

Package-dependent methods may be replaced only before Gate 2, with the reason,
license, evaluation count, and implementable equivalent recorded. Silent
omission is prohibited.

## Factorial ablations

Clustering runs all 16 on/off combinations of geography, time, context, and
k-NN. An “off” component is removed from the formula, not set to a misleading
scale; retained density is matched where required.

Priority runs the declared combinations of confidence gate, vulnerability
amplification, and aggregation estimator. Main effects are not interpreted
without checking interactions. Effects, paired intervals, Holm-corrected
tests, evaluation counts, failures, and wall time are reported.

## Selection and reporting

Track A maximizes the declared calibration objective under connectivity,
diameter, workload, and density constraints. Track B is label-free and ranks
feasible candidates by stability and operator burden. Ties use the
predeclared order: lower burden, lower complexity, then lexical config hash.

Test output reports co-primary and secondary endpoints, per-family errors,
configuration/evaluation counts, calibration wall time, and test wall time.
Negative, tied, failed, and infeasible methods remain in the table.
