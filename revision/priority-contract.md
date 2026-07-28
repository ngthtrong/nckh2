# Priority semantics and robustness contract

**Tasks:** C1–C2  
**Status:** locally implemented; estimator selection remains subject to the
locked development/calibration protocol  
**Authority:** Q4, Q5, and Q7 in `revision/decision-log.md`  
**Scope:** synthetic methodological study, not a validated rescue policy

## 1. Unit, provenance, and prohibited information

The physical incident is the ground-truth unit. A report is only a noisy,
partial, and possibly overlapping observation. Consequently, priority
inference estimates **reported demand evidence**; it does not estimate unique
population truth unless an external identification mechanism is later
validated.

| Quantity | Inference meaning | Observable source | Confidence rule | Incident aggregation |
|---|---|---|---|---|
| `E` / urgency | reported urgency evidence in `[0,1]` | report | multiply by clipped `C` before aggregation | reliability-mass robust mean across independent evidence units |
| `F` / flood | reported maximum flood evidence in `[0,1]` | report | multiply by clipped `C` | maximum across independent evidence units |
| `N` / `n_trapped` | reported demand evidence, not unique people | report | multiply by clipped `C` | strongest capped evidence; never sum overlapping reports |
| `V` / vulnerability | reported vulnerability-mass evidence, not unique vulnerable people | report | multiply by clipped `C` | strongest capped evidence; never sum overlapping reports |
| `C` / confidence | provenance/corroboration reliability heuristic in `[0,1]` | computed only from inference-visible signals | clipped to `[0,1]`; not a truth probability | gate, never an outcome or ground-truth label |
| location/time | report routing and duplicate evidence | report | used for near-duplicate grouping; reliable-family weights are used for revised centroid metadata | no latent incident center |
| `N_true`, `V_true` | unique incident truth | latent incident table | not applicable | evaluation only |

Inference, clustering, priority, and tuning must not read `incident_id`,
`gt_cluster`, `N_true`, `V_true`, `duplicate_family_id`, `duplicate_kind`,
coverage fractions, scenario/adversary labels, `is_fake`, latent
deadline/harm/service fields, or any equivalent alias. The implementation
constructs the duplicate fingerprint from an explicit observable allow-list;
it never serializes an `Event` generically.

In candidate data, incident-linked V is a vulnerable-person count constrained
to `V<=N`; unlinked V-inflation attacks intentionally need not satisfy that
latent plausibility relation. Inference does not receive linked/unlinked truth,
so the robust estimator still applies its universal observable cap and reports
those attacks rather than silently repairing them.

## 2. Exact duplicate identity

The inference-visible exact fingerprint is SHA-256 over canonical UTF-8 JSON
containing exactly:

```text
lat, lng, created_at, flood, urgency, n_trapped, vulnerability,
has_image, source_type, province, missing_fields
```

Canonical JSON uses sorted keys, compact separators, exact serialized numeric
values and timestamp, and a terminal newline. `event_id`, free text `note`,
confidence-derived corroboration, evaluation flags, and every latent field are
excluded. This definition matches `demo/data/schema.py::report_fingerprint`.

Reports with one fingerprint form one evidence unit. Multiplicity never enters
`E_hat`, `F_hat`, `N_hat`, `V_hat`, the priority centroid, or priority.
Therefore adding an exact duplicate with the same derived confidence changes
all priority components by exactly zero. If one fingerprint arrives with
different derived confidence values, inference fails closed with a
data/provenance error; it does not silently choose the maximum or minimum.
The operational member count and member-ID audit list may increase because
they describe received traffic, not independent evidence.

The candidate generator must compute confidence symmetrically for an exact
duplicate family. If equal raw payloads arrive with materially inconsistent
confidence, that is a provenance/data-quality conflict to report; it is not
permission to use hidden duplicate lineage.

## 3. Revised duplicate-aware robust estimator

Let `U` be exact-payload evidence units and `G` the observable near-duplicate
families described below. For a report, all numeric fields are finite,
`C,F,E` are clipped to `[0,1]`, `N` is clipped to `[0,N_cap]`, and `V` is
clipped to `[0,V_cap]`.

The current policy caps are:

- `N_cap = params.n_ref` when that reference is positive, otherwise `500`;
- `V_cap = 50`;
- `mu in [1,2]`, `v_scale > 0`, and all `omega` values finite and
  non-negative.

Within each near-duplicate family only the maximum gated evidence is retained.
Across the resulting independent evidence families:

```text
E_hat = sum_g max_{i in g}(C_i E_i) / max(1, sum_g max_{i in g} C_i)
F_hat = max_g max_{i in g}(C_i F_i)
N_hat = max_g max_{i in g}(C_i clip(N_i, 0, N_cap))
V_hat = max_g max_{i in g}(C_i clip(V_i, 0, V_cap))

N_tilde = min(1, log(1 + N_hat) / log(1 + N_ref))
V_agg   = 1 + (mu - 1) tanh(V_hat / v_scale)
core    = omega_E E_hat + omega_F F_hat + omega_N N_tilde
P       = V_agg * core
```

The maximum for `N/V` is deliberate: without observable person identity,
adding partial report counts would silently assert disjoint population. It
gives a conservative strongest-evidence statistic. Its calibration error
against latent truth must still be compared with raw sum, capped sum, raw max,
and other confidence-weighted candidates on development/calibration data.
No test result may be used to choose the estimator.

The additive-V form retained for a declared ablation is
`P_add = core + (V_agg - 1)`. Turning off confidence or the `F` gate is also an
explicit non-contractual ablation; it cannot be described as the revised
policy.

## 4. Near-duplicate drift policy

Near duplicates are identified without lineage labels by connected components
of report pairs satisfying all of:

| Observable difference | Tolerance |
|---|---:|
| Haversine distance | `<= 100 m` |
| absolute report-time difference | `<= 10 min` |
| `F` | `<= 0.10` |
| `E` | `<= 0.10` |
| `N` | `<= max(5, 0.25 * max(N_a,N_b,1))` |
| `V` | `<= 2.0` |
| `C` | `<= 0.10` |
| source-missingness mask | identical sorted `missing_fields` |

The first six values align with the generator quality gate. The `C` tolerance
is an additional inference safeguard: two otherwise similar reports with
materially different provenance are not silently treated as one evidence
unit.

The preregistered C3 acceptance threshold for adding one valid near duplicate
is:

```text
abs(P_after - P_before) / (P_upper - P_lower) <= 0.30
```

and each normalized component remains in `[0,1]`. Exact duplicates have the
strict threshold `0`. The 30% threshold applies only to one report inside this
declared envelope; all 2x/5x/10x bursts and boundary-crossing cases are
reported separately rather than relabeled after seeing results.

The initial local draft used 10%. A Gate-1 audit falsified that value before
release of any locked test result: the valid boundary pair
`(C,E,F,N,V)=(0.9,0.9,0.9,0,9.5)` to
`(1.0,1.0,1.0,5,11.5)` produces normalized priority drift `0.235816`.
A deterministic boundary grid over integer `N=0..500`, confidence and
saturation boundaries, and `V`, cross-checked with fixed-seed SciPy global
optimization, found no larger default-policy case. The ceiling was therefore
raised to 0.30, leaving an explicit numerical margin without changing the
near-duplicate envelope. This is a preregistered stress ceiling, not a proof of
real-world safety; C3 must still report the full distribution and all failures.

## 5. Confidence consistency and influence bounds

With default gates:

- `C=0` contributes zero to `E_hat`, `F_hat`, `N_hat`, and `V_hat`;
- a single report can add at most `C` to `E_hat` and `F_hat`, `C*N_cap` to
  raw `N` evidence, and `C*V_cap` to raw `V` evidence before saturation;
- exact multiplicity contributes zero after the first copy;
- `N_tilde` is capped at one and `V_agg` is below `mu`;
- low-confidence inflation is bounded but not guaranteed to have zero effect.

For non-negative weights, let `W = omega_E + omega_F + omega_N`.
The declared closed ranges are:

```text
P_multiplicative in [0, mu * W]
P_additive       in [0, W + mu - 1]
```

With normalized weights and `mu <= 2`, both are subsets of `[0,2]`. The code
checks the declared bound and fails closed if a custom estimator violates it.

## 6. Legacy estimator and API

`score_clusters(..., estimator=None)` uses
`duplicate_aware_robust`. Historical reproduction must explicitly use
`estimator="legacy_raw"` (aliases: `"legacy"`, `"raw"`).

The legacy path preserves:

```text
E_legacy = sum(E_i C_i) / report_count
F_legacy = max(F_i C_i)
N_legacy = sum(N_i C_i)
V_legacy = sum(V_i)                # confidence bypass
```

It also preserves raw report multiplicity and the old arithmetic centroid. It
is an ablation only, not a compliant revised estimator. The public
`aggregate_cluster_evidence` API supports one-cluster unit/adversarial tests,
and every `ClusterScore` records estimator name, raw `V` evidence, evidence
unit count, exact/near coalescence counts, and declared score bounds.

## 7. Threat matrix and required reporting

| Threat | Expected local property | Mandatory limitation/result |
|---|---|---|
| exact duplicate, any multiplicity | zero component/priority drift | traffic/member count may grow |
| near duplicate within envelope | single-addition drift `<=30%` of declared range | report boundary and burst results |
| low-C inflation of `E/F/N/V` | field goes through the same C gate and a finite cap/range | bounded influence is not fake detection |
| coordinated high-C campaign | finite score; exact/near copies coalesced when observable criteria match | distinct high-C claims can still manipulate ranking |
| missing image/corroboration | acts only through the declared confidence/provenance calculation | missingness mechanism and rates reported |
| overlapping genuine reports | no summation claim about unique people | `N_hat/V_hat` named evidence, error to latent truth reported |
| dynamic `N_ref` | bounded within a run | not comparable over time; static reference is primary |

Every C3 scenario is reported, including ties and failures. A successful
high-confidence campaign is a known human-verification failure mode and must
not be reframed as evidence that `C` detects misinformation.

## 8. Generator/schema interface required by C2

WS-D must provide:

1. an inference loader producing `Event` objects with `source_type` plus the
   existing observable fields, and no forbidden latent/evaluation attributes;
2. timezone-aware `created_at`, finite coordinates and `F/E/N/V`, `F/E` in
   `[0,1]`, non-negative `N/V`, and confidence in `[0,1]` before priority;
3. exact duplicate families identical on the fingerprint fields, with
   differing `event_id` allowed and equal derived confidence after the common
   confidence pass;
4. near duplicates satisfying the six generator tolerances above, while C3
   separately checks the additional confidence tolerance;
5. latent `incident_id/N_true/V_true`, duplicate lineage, coverage fractions,
   `is_fake`, scenario labels, and outcome fields available only through an
   evaluation loader;
6. overlapping partial `N/V` observations, exact/near bursts, low-C
   single-field inflation for every field, coordinated high-C campaigns, and
   missing provenance/image cases in every registered split;
7. evaluator-side error metrics comparing each estimator's `N_hat/V_hat`
   against incident truth without making latent fields available to the
   estimator.

The fingerprint and near-duplicate checks must be cross-tested between
`demo/data/schema.py` and `demo/pipeline/priority.py` before Gate 1. Any schema,
cap, or tolerance change after observing test outcomes reopens the method/data
freeze.

## 9. Acceptance tests and scientific status

Unit/metamorphic tests must establish:

- exact-fingerprint invariance for `E/F/N/V/core/P`;
- no effect from a `C=0` report on priority components;
- the declared single-near-duplicate drift threshold;
- bounded output under extreme finite claims;
- no dependence on `incident_id` or other dynamically attached latent fields;
- legacy reproduction of the pre-revision equations within numeric tolerance.

Passing these tests establishes implementation consistency only. It does not
validate the weights, policy caps, real-world report distributions, or dispatch
benefit. Those claims require locked calibration, C3/C4 outcomes, and the
external expert protocol.
