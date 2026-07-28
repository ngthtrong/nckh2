# Synthetic incident-data specification

**Task:** D1  
**Status:** locked for D2 implementation  
**Schema:** `flood-rescue-synthetic-v4`  
**Generator:** `4.1.0`  
**Scope:** methodological synthetic study; this specification is not evidence
about real flood-report distributions.

## Unit of analysis and causal separation

The physical incident, not the report, is the unit whose demand and outcome
exist in ground truth. Reports are noisy, partial observations emitted by an
incident or by a noise/adversarial process.

```text
incident state
  ├─ location/time process ──> report location/time
  ├─ flood/urgency process ──> reported F/E
  ├─ unique N_true/V_true ───> partial reported N/V
  ├─ deadline/harm process ──> latent dispatch outcome
  └─ reporting process ──────> duplicates, missing fields, images, provenance

adversarial/noise process ───> unlinked reports and coordinated campaigns
```

The generator may use `incident_id` to emit reports. Evaluation may use
incident truth. Clustering, priority inference, calibration, and operational
metrics must receive a sanitized view that excludes `incident_id`, `N_true`,
`V_true`, latent deadlines, duplicate lineage, and scenario labels.

## Dataset envelope

Each generated seed yields one document:

```json
{
  "schema_version": "flood-rescue-synthetic-v4",
  "generator_version": "...",
  "seed": 1000,
  "split": "development",
  "incidents": [],
  "reports": [],
  "quality": {}
}
```

`split` is derived only from the locked seed manifest. A seed outside the
manifest is allowed for local smoke tests and is labeled `unregistered`; it is
not eligible for a reported result.

## Locked generator parameters

The following numeric choices are fixed before any candidate method result is
examined. Changing one changes the generator hash and reopens Gate 1.

| Process | Locked value/range |
|---|---|
| Registered seeds | development `1000..1019`; calibration `2000..2019`; test `3000..3039` |
| Incident count | 16 per seed across eight required families |
| Incident report-count multiplier | uniform `[0.85, 1.15]`, lower bounded at 6 |
| Incident spread multiplier | uniform `[0.85, 1.15]` around family-specific `120..900 m` |
| Report time noise | Normal `(0, 18 min)` |
| Flood/urgency noise | Normal `(0, 0.11)`, clipped to `[0,1]` |
| Population coverage draw | Beta `(2.3, 3.0)`, at least one member |
| Reported N noise | Normal `(0, 2 people)`, clipped to `[0,n_true]` |
| Reported V noise | Normal `(0, 0.5)`, clipped to `[0,n_reported]` |
| Source missingness | independent probabilities: F `0.04`, E `0.03`, N `0.06`, V `0.08` |
| Missing-value handling | deterministic zero imputation plus observable sorted `missing_fields` mask |
| Report serialization order | deterministic seed-based permutation after all report processes |
| Supportive-overlap gate | center distance `<=900 m`, start delta `<=30 min`, latent F/E L1 delta `>=0.90` |
| Adversarial-overlap gate | center distance `<=800 m`, start delta `<=30 min`, latent F/E L1 delta `<=0.25` |
| Same-location temporal gate | center distance `<=300 m`, start delta `>=180 min`, latent F/E L1 delta `<=0.30` |
| Distant-context gate | center distance `>=60 km`, start delta `<=30 min`, latent F/E L1 delta `<=0.25` |
| Unequal-density gate | report-count ratio `>=3.5`, spread ratio `>=5.0` |
| Independent-stress process | three incidents; center uniform over study envelope, time uniform `[-30,260] min`, F/E uniform `[0,1]`, reports integer `[8,35]`, spread uniform `[120,900] m` |
| Background reports | 32 per seed; fake probability `0.35` |
| Low-confidence attacks | four per seed; mutually outside `400 m/60 min` corroboration window |
| Coordinated campaign | five image-bearing reports within approximately `45 m/6 min` |
| Exact duplicate tolerance | identical observable fingerprint |
| Near coordinate/time tolerance | at most `100 m` and `10 min` |
| Near F/E tolerance | absolute difference at most `0.10` each |
| Near N tolerance | `max(5, 0.25 × max(N_base,1))` |
| Near V tolerance | absolute difference at most `2.0` |
| Coverage reconciliation | absolute tolerance `1e-6` |

Family-specific centers, counts, latent context values, and base spread values
are the immutable `_CANDIDATE_INCIDENT_SPECS` table in
`demo/data/generate.py`; its source checksum is recorded in every frozen
bundle. The schema checksum, this specification checksum, and the seed
manifest checksum are recorded separately.

### Latent incident record

| Field | Type/domain | Meaning |
|---|---|---|
| `incident_id` | stable string | Evaluation key; never an inference feature. |
| `gt_cluster` | non-negative integer | Partition label corresponding one-to-one with `incident_id`. |
| `scenario_family` | enum | Stratified evaluation only; hidden from inference. |
| `center_lat/lng` | valid coordinate | Generator reference, not a report centroid. |
| `start_at` | timezone-aware ISO-8601 | Latent incident start. |
| `n_true` | positive integer | Unique people needing service at the incident. |
| `v_true` | `[0,n_true]` | Unique vulnerability mass on the same population. |
| `deadline_min` | positive float | Latent response deadline generated independently of reported priority components. |
| `service_demand_min` | positive float | Latent service workload/capacity demand. |
| `harm_curve` | declared enum + parameters | Outcome model using lateness/capacity, not the priority formula. |

`deadline_min` and `harm_curve` may depend on an unobserved incident-severity
variable and scenario parameters. They must not be computed as a transform of
reported `F`, `V`, `priority`, `core`, `F_max`, or `V_agg`. Correlation through
a common latent incident state is allowed and disclosed.

### Observable report record

The existing operational fields remain available:

- stable opaque `event_id` in one uniform `EV-<20 hex>` format; it encodes no
  report source, scenario, truth, or duplicate lineage;
- `lat`, `lng`, and timezone-aware `created_at`;
- reported `flood`, `urgency`, `n_trapped`, and `vulnerability`;
- `has_image`, source/provenance category, and corroboration inputs;
- `province` and a non-identifying note/category.
- a sorted `missing_fields` mask distinguishing source-missing `F/E/N/V`
  values from observed zeros; the operational loader applies the locked
  conservative zero imputation.

Evaluation-only fields are serialized in a separate nested object
`evaluation_only`:

- `incident_id` or `null`;
- `duplicate_family_id` or `null`;
- `duplicate_kind`: `none`, `exact`, or `near`;
- latent per-report coverage fractions for `N` and `V`;
- explicit population and vulnerable-member index subsets used to verify
  overlap and coverage;
- scenario/adversary label and `is_fake` evaluation truth.

The loader exposes two explicit functions: an evaluation loader returning the
full record and an inference loader returning only observable `Event` objects.
There is no optional flag that silently leaks evaluation fields into inference.

For incident-linked synthetic reports where `N` is observed, vulnerability is
a person-count mass on the reported subset and therefore satisfies
`0 <= vulnerability <= n_trapped`. When `N` is source-missing, its operational
zero imputation is not treated as a population bound on an observed `V`.
Deliberate unlinked adversarial claims may
violate that relation (for example the V-inflation threat case); those are
evaluation stress inputs, not plausible linked observations.

## Report generation

For each incident:

1. Draw `n_true`, `v_true`, a spatial/temporal reporting process, and a number
   of reports.
2. Draw overlapping subsets of the unique population. Reported `N` and `V`
   therefore need not add to incident truth.
3. Add bounded measurement noise and missingness to `F/E/N/V`; round only at
   serialization.
4. Emit realistic repeated reports:
   - exact duplicates repeat every observable payload field except
     `event_id` and transport metadata;
   - near duplicates vary time/coordinate/text-independent numeric fields
     within declared tolerances;
   - independent reports may still overlap in represented people.
5. Generate image/provenance/corroboration signals with overlapping
   distributions for real and false reports.

An exact duplicate fingerprint uses only observable payload: serialized
latitude/longitude and timestamp, `F/E/N/V`, image flag, and
source/provenance. It excludes `event_id`, fake/incident ground truth,
free-text notes, and all latent lineage. Time/coordinate tolerances belong to
the separate near-duplicate estimator.

## Scenario families

Every split contains all families, with seed-dependent counts, positions,
density, and difficulty:

1. separated ordinary incidents;
2. spatially overlapping, context-supportive incidents;
3. spatially overlapping, context-adversarial incidents;
4. same-location, temporally separated incidents;
5. geographically separated but context/time-similar incidents;
6. multimodal reports from one physical incident;
7. unequal-density and wide-spread incidents;
8. sparse/noise reports;
9. low-confidence single-field inflation for each of `N/V/F/E`;
10. exact and near-duplicate bursts;
11. coordinated high-confidence campaigns.
12. three generic independent-stress incidents whose centers, times, context,
    density, and spread are sampled without curating pairwise relations for the
    proposed similarity.

No family is accepted or rejected based on whether product similarity wins.
Results are reported both overall and by family.

Before any method is run, family-property gates verify the intended latent
geometry directly: supportive/adversarial spatial overlap, temporal
separation, distant-context similarity, multimodality, and count/spread
imbalance. These gates inspect no predicted labels or performance metric.

## Method-agnostic quality gates

These gates run before any method metric:

- schema validation and required-field completeness;
- domain/range and cross-field validity;
- unique incident/report IDs and valid evaluation foreign keys;
- every linked report resolves to exactly one incident;
- `0 <= v_true <= n_true` and report vulnerability is non-negative;
- latent unique totals reconcile exactly from the incident table;
- exact-duplicate groups have identical fingerprints;
- near duplicates satisfy the declared observable tolerance;
- all registered scenario families are represented;
- seed/split mapping matches the locked manifest and split seed sets do not
  overlap;
- inference serialization contains none of the forbidden latent keys;
- the same seed and generator version produce byte-identical canonical JSON;
- distributions are summarized by split and family, but no acceptance gate
  contains ARI, product/additive performance, ranking, or a preferred method.

Changing a quality threshold after observing test performance reopens Gate 1.

## Distribution report

Each seed manifest records counts/rates rather than only totals:

- incidents, reports, reports per incident, and unlinked noise;
- exact/near duplicate shares;
- missingness and provenance shares by field;
- unique `N_true/V_true` and reported `N/V` distributions;
- report overlap ratios;
- coordinate/time/context dispersion by family;
- real/fake and low/high-confidence overlap;
- latent deadline, service-demand, and harm-curve distributions.

Robust quantiles and family-stratified rates are primary; means alone are
insufficient for long-tailed counts.

## Freeze and storage rules

- Development/calibration/test datasets are written below the candidate run
  directory and never to `demo/data/dataset.json`.
- Canonical serialization uses sorted keys, UTF-8, stable float formatting,
  and a terminal newline.
- A dataset manifest records the seed, split, schema/generator hash, byte
  checksum, incident/report counts, quality-gate result, seed-manifest hash,
  and this data-spec hash.
- Gate 1 freezes generator source, schema, registered seed lists, and all
  dataset checksums.
- The current v3 dataset remains historical and unchanged.

## External validity

This generator intentionally tests declared failure modes; it cannot establish
real-world prevalence or transfer. External data must follow
`revision/real-data-protocol.md`. In its absence, every manuscript claim is
explicitly synthetic-only.
