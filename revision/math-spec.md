# Localization mathematics specification (A1)

**Status:** implementation contract for WS-A; manuscript text remains unchanged  
**Decision source:** `revision/decision-log.md`, Q2--Q3  
**Threshold convention:** an edge is retained exactly when \(w_{ij}>\theta\)

This document specifies an implementation property of the product similarity.
It does not claim that the similarity is a Mercer/PSD kernel, nor that the
Gaussian edge cutoff is a new kernel construction. In revised claims,
“product similarity” is the preferred term. If “kernel” is retained anywhere,
it means only a similarity function unless a separate PSD proof is supplied.

## 1. Assumptions and notation

Let

\[
G(d)=\exp\!\left(-\frac{d^2}{2\sigma^2}\right),\qquad
T,C\in[0,1],\qquad \sigma>0,
\]

and let \(\alpha,\beta,\gamma\ge 0\) be finite. Define
\(B=\beta+\gamma\). The two similarities are

\[
w^\times=G(d)(\beta T+\gamma C)
\]

and

\[
w^+=\alpha G(d)+\beta T+\gamma C.
\]

All thresholds below are finite real numbers. “Unbounded” means that no
non-trivial finite cutoff follows from \(\alpha,\beta,\gamma,\sigma,\theta\)
alone on the model domain \(d\ge0\). On a spherical Earth there is of course
the ambient antipodal-distance bound; that unrelated bound is not a
threshold-induced localization guarantee.

The implementation uses three explicit bound states:

- `finite`: retained edges obey a strict distance cutoff `radius_m`;
- `unbounded`: retained edges can occur at arbitrarily large model distance;
- `empty`: no edge can pass the strict threshold.

Only `finite` rows are eligible for theorem-violation or cluster-bound counts.
An `empty` state is a vacuous edge set, not a zero-radius localization result.

## 2. Product edge-localization theorem

**Theorem 1 (general product edge bound).** Since
\(\beta T+\gamma C\le B\),

\[
w^\times\le B\,G(d).
\]

If \(B>0\) and \(0<\theta<B\), every retained product edge satisfies

\[
d<r^\times_\theta
 :=\sigma\sqrt{2\log\!\left(\frac{B}{\theta}\right)}.
\]

If \(\theta\ge B\), no product edge is retained. If \(B>0\) and
\(\theta\le0\), there is no non-trivial finite cutoff. In the degenerate case
\(B=0\), \(w^\times=0\): the retained set is empty for \(\theta\ge0\), while a
negative threshold retains all pairs.

**Proof.** For a retained edge,

\[
\theta<w^\times\le B\exp[-d^2/(2\sigma^2)].
\]

When \(B>0\) and \(0<\theta<B\), division by \(B\), the strict monotonicity of
the logarithm, and rearrangement give the stated strict bound. If
\(\theta\ge B\), then \(w^\times\le B\le\theta\), which contradicts strict
retention. For \(B>0,\theta\le0\), take \(T=C=1\); the Gaussian is positive at
every finite \(d\), so distances are not uniformly bounded. The \(B=0\) cases
follow from \(w^\times=0\). \(\square\)

The complete domain table is:

| Parameter region | Product bound state | Consequence |
|---|---:|---|
| \(\theta<0\) | unbounded | Even zero-weight pairs satisfy \(0>\theta\). |
| \(\theta=0,\ B>0\) | unbounded | \(G(d)>0\) at every finite \(d\). |
| \(\theta\ge0,\ B=0\) | empty | \(w^\times=0\) cannot exceed \(\theta\). |
| \(0<\theta<B\) | finite | \(d<\sigma\sqrt{2\log(B/\theta)}\). |
| \(\theta\ge B,\ B>0\) | empty | The maximum possible weight is \(B\). |

When \(B\le1\), the older radius
\(\sigma\sqrt{2\log(1/\theta)}\) is a looser corollary only in the
non-vacuous domain \(0<\theta<B\). The \(B\)-aware radius is the primary
statement and is strictly tighter when \(B<1\).

## 3. Conditional component/community corollary

Let the thresholded graph contain only edges with \(w^\times>\theta\), with
\(B>0\) and \(0<\theta<B\). Deleting more edges through \(k\)-NN
sparsification cannot invalidate Theorem 1.

**Corollary 1 (conditional hop bound).** Let \(U\) be a connected set with at
least two vertices, and let its unweighted hop-diameter in the retained graph
be \(h<\infty\). Its geographic diameter \(D(U)\) satisfies

\[
D(U)<h\,r^\times_\theta.
\]

**Proof.** Any two vertices have a retained path of at most \(h\) edges.
Every path edge is shorter than \(r^\times_\theta\) by Theorem 1. The metric
triangle inequality gives a path length, and hence endpoint distance, below
\(h r^\times_\theta\). Taking the maximum over vertex pairs proves the
claim. \(\square\)

A singleton has \(h=0\) and \(D=0\) and is reported separately as a trivial
case. A disconnected Louvain community has no finite within-community
hop-diameter; the corollary is not evaluated for it.

This is conditional, not an ex-ante compact-cluster guarantee. The current
pipeline neither fixes nor enforces a useful \(h\). Without such a mechanism,
a chain can contain arbitrarily many edges each just below the edge radius, so
its component diameter grows with \(h\) (at worst \(h\le n-1\)).

## 4. Additive theorem by threshold region

**Theorem 2 (additive geographic bound).** For
\(w^+=\alpha G+\beta T+\gamma C\),

\[
w^+\le \alpha G+B.
\]

When \(\alpha>0\) and

\[
B<\theta<B+\alpha,
\]

every retained edge satisfies

\[
d<r^+_\theta
 :=\sigma\sqrt{2\log\!\left(\frac{\alpha}{\theta-B}\right)}.
\]

At \(\theta\ge B+\alpha\), no edge can satisfy the strict threshold.
For \(\theta\le B\), there is generally no non-trivial data-independent
geographic cutoff; the exact degenerate boundary
\(\alpha=0,\theta=B\) is empty rather than unbounded.

**Proof in the finite region.** Retention and the upper bound imply

\[
\theta< w^+\le\alpha G+B,
\quad\text{so}\quad
G>\frac{\theta-B}{\alpha}.
\]

The finite-region assumptions put the right side strictly in \((0,1)\);
solving the Gaussian inequality yields the radius. If
\(\theta\ge B+\alpha\), then \(w^+\le B+\alpha\le\theta\), so strict retention
is impossible. Counterexamples for the remaining regions are listed below.
\(\square\)

The complete domain table is:

| Parameter region | Additive bound state | Consequence |
|---|---:|---|
| \(\theta<0\) | unbounded | Every non-negative weight exceeds \(\theta\). |
| \(\theta=0,\ \alpha+B=0\) | empty | The similarity is identically zero. |
| \(\theta=0,\ \alpha+B>0\) | unbounded | Equal time/context or the positive Gaussian retains arbitrarily distant pairs. |
| \(0<\theta<B\) | unbounded | Non-geographic terms alone can equal \(B>\theta\). |
| \(\theta=B,\ \alpha>0\) | unbounded | \(B+\alpha G(d)>B\) for every finite \(d\). |
| \(\theta=B,\ \alpha=0\) | empty | \(w^+\le B=\theta\). |
| \(B<\theta<B+\alpha\) | finite | \(d<\sigma\sqrt{2\log(\alpha/(\theta-B))}\). |
| \(\theta\ge B+\alpha\) | empty | The maximum possible weight is \(B+\alpha\). |

Thus the scientifically correct contrast is not “addition has no geographic
guarantee.” It is that addition has no threshold-induced cutoff throughout
its low-threshold region, while it does have the stated cutoff above the
maximum non-geographic contribution \(B\).

## 5. Counterexamples and boundary checks

1. **Additive, \(0<\theta<B\).** Choose two reports at the same time with
   identical context, so \(T=C=1\). Then
   \(w^+=\alpha G+B\ge B>\theta\) for any distance.
2. **Additive, \(\theta=B,\alpha>0\).** With \(T=C=1\),
   \(w^+=B+\alpha G(d)>B\) at every finite \(d\), however small \(G(d)\)
   becomes.
3. **No ex-ante cluster compactness.** Form a retained chain of \(h\) edges,
   each with geographic length arbitrarily close to
   \(r^\times_\theta\). Its endpoint distance can approach
   \(h r^\times_\theta\); without controlling \(h\), the edge theorem supplies
   no fixed operational cluster radius.
4. **Strict-threshold equality.** Set \(T=C=1\) and
   \(d=\sigma\sqrt{2\log(B/\theta)}\) in the finite product region. Then
   \(w^\times=\theta\), so this pair must be removed. Code using `< theta`
   instead of `<= theta` would contradict the theorem's retained-edge set.
5. **Empty is not radius zero.** At \(\theta=B\) for the product form, no edge
   passes. Recording a numerical cutoff of `0.0` and then counting ordinary
   distances as “violations” would test a theorem outside its finite domain.

## 6. Executable contract

`demo/pipeline/weighting.py` exposes structured product and additive bound
classifiers. Callers must branch on `status`. The legacy
`implied_distance_cutoff` name is retained, but it returns a number only for
the finite product region and raises outside that region.

`demo/experiments/exp14_localization_bounds.py` must:

- emit only finite-domain edge/cluster bound checks;
- report `domain_eligible`, the structured bound state, and zero counted rows
  outside the finite domain;
- report connectivity for every output cluster;
- for each connected non-singleton cluster report \(h\),
  \(h r_\theta\), actual geographic diameter, and their tightness ratio;
- never reinterpret an empty retained set as a zero-radius violation.

The experiment is diagnostic evidence. It measures the realized \(h\); it
does not promote \(h\) to a pipeline-controlled constant.
