"""Fail-closed confirmatory analysis for the v2 synthetic experiment.

This module is intentionally a pure consumer of already-produced confirmation
rows.  It neither imports the generator/protocol nor reads files, and it never
repairs incomplete result matrices.  Coverage is audited on exact composite
keys before any descriptive or inferential statistic is computed.

The two declared Holm families are:

* synthetic clustering: product versus additive co-primary endpoints; and
* synthetic priority/dispatch: priority, stress, and predicted-dispatch tests.

All comparisons, including adverse and null results, remain in the returned
payload.  Claim gates are conservative views over those complete results; they
do not filter the evidence used to construct the views.
"""

from __future__ import annotations

import hashlib
import itertools
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import fmean, median, stdev
from typing import Any

from demo.v2.dispatch import POLICY_IDS
from demo.v2.evaluation import STRESS_FAMILIES_V2
from demo.v2.statistics import holm_adjust, paired_comparison_by_key


DEFAULT_METHODS = (
    "method.product_louvain",
    "method.additive_louvain",
    "method.st_dbscan",
    "method.hdbscan_geo_time",
)
DEFAULT_PRIORITY_POLICIES = tuple(
    policy for policy in POLICY_IDS if policy != "nearest_first"
)
DEFAULT_DISPATCH_POLICIES = tuple(POLICY_IDS)
DEFAULT_SCENARIOS = ("lean", "nominal", "surge")
DEFAULT_REGIMES = ("id", "ood")

CLUSTERING_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("ari_linked", "higher"),
    ("false_destinations_per_100_reports", "lower"),
)
CLUSTERING_SECONDARY_ENDPOINTS = (
    "split_loss",
    "merge_loss",
    "noise_rejection",
    "review_items_per_100_reports",
    "max_diameter_m",
    "singleton_rate",
)
PRIORITY_ENDPOINT = ("ndcg_at_k", "higher")
PRIORITY_SECONDARY_ENDPOINTS = (
    "kendall_tau_b",
    "top_k_recall",
    "rank_regret",
)
DISPATCH_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("total_harm", "lower"),
    ("deadline_miss_rate", "lower"),
)
STRESS_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("mean_normalized_rank_drift", "lower"),
    ("top_k_set_drift", "lower"),
)
STRESS_SECONDARY_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("max_absolute_score_drift", "lower"),
)
DISPATCH_GUARDRAILS = (
    "unreached_incidents",
    "false_trips",
    "duplicate_trips",
    "max_response_min",
    "cvar90_response_min",
    "workload_cv",
)
CAMPAIGN_ENDPOINT = ("false_priority_lift", "lower")


class ConfirmationAnalysisError(ValueError):
    """Raised when confirmation evidence violates the locked analysis contract."""


def _unique_text_axis(values: Sequence[str], name: str, expected_size: int) -> tuple[str, ...]:
    clean = tuple(str(value) for value in values)
    if len(clean) != expected_size or any(not value for value in clean):
        raise ConfirmationAnalysisError(
            f"{name} must contain exactly {expected_size} non-empty values"
        )
    if len(set(clean)) != len(clean):
        raise ConfirmationAnalysisError(f"{name} contains duplicate values")
    return clean


@dataclass(frozen=True, slots=True)
class ConfirmationAnalysisSpec:
    """Locked axes plus a caller-supplied list of expected master seeds.

    Tests and development audits can supply small seed identifiers.  The
    analysis does not know, generate, or discover the confirmation seed list.
    """

    seeds: tuple[int, ...]
    expected_seed_count: int = 40
    methods: tuple[str, ...] = DEFAULT_METHODS
    priority_policies: tuple[str, ...] = DEFAULT_PRIORITY_POLICIES
    stress_families: tuple[str, ...] = tuple(STRESS_FAMILIES_V2)
    dispatch_policies: tuple[str, ...] = DEFAULT_DISPATCH_POLICIES
    scenarios: tuple[str, ...] = DEFAULT_SCENARIOS
    regimes: tuple[str, ...] = DEFAULT_REGIMES
    product_method: str = "method.product_louvain"
    additive_method: str = "method.additive_louvain"
    revised_policy: str = "revised"

    def __post_init__(self) -> None:
        seeds = tuple(self.seeds)
        if (
            isinstance(self.expected_seed_count, bool)
            or not isinstance(self.expected_seed_count, int)
            or self.expected_seed_count < 1
        ):
            raise ConfirmationAnalysisError("expected_seed_count must be a positive integer")
        if len(seeds) != self.expected_seed_count:
            raise ConfirmationAnalysisError(
                f"expected exactly {self.expected_seed_count} master seeds, got {len(seeds)}"
            )
        if any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds):
            raise ConfirmationAnalysisError("master seeds must be integer identifiers")
        if len(set(seeds)) != len(seeds):
            raise ConfirmationAnalysisError("master seeds must be unique")
        object.__setattr__(self, "seeds", seeds)
        for field, size in (
            ("methods", 4),
            ("priority_policies", 6),
            ("stress_families", 10),
            ("dispatch_policies", 7),
            ("scenarios", 3),
            ("regimes", 2),
        ):
            object.__setattr__(
                self,
                field,
                _unique_text_axis(getattr(self, field), field, size),
            )
        locked_axes = {
            "methods": set(DEFAULT_METHODS),
            "priority_policies": set(DEFAULT_PRIORITY_POLICIES),
            "stress_families": set(STRESS_FAMILIES_V2),
            "dispatch_policies": set(DEFAULT_DISPATCH_POLICIES),
            "scenarios": set(DEFAULT_SCENARIOS),
            "regimes": set(DEFAULT_REGIMES),
        }
        for field, expected in locked_axes.items():
            if set(getattr(self, field)) != expected:
                raise ConfirmationAnalysisError(f"{field} differs from the locked analysis axis")
        if self.product_method not in self.methods or self.additive_method not in self.methods:
            raise ConfirmationAnalysisError("product/additive methods must be declared methods")
        if self.product_method == self.additive_method:
            raise ConfirmationAnalysisError("product and additive methods must differ")
        if self.revised_policy not in self.priority_policies:
            raise ConfirmationAnalysisError("revised policy must be a priority policy")
        if set(self.dispatch_policies) != set(self.priority_policies).union({"nearest_first"}):
            raise ConfirmationAnalysisError(
                "dispatch policies must be the six priority policies plus nearest_first"
            )
        if set(self.regimes) != {"id", "ood"}:
            raise ConfirmationAnalysisError("the locked regimes are exactly id and ood")


@dataclass(frozen=True, slots=True)
class ValidatedConfirmationPayload:
    clustering_rows: tuple[Mapping[str, Any], ...]
    priority_rows: tuple[Mapping[str, Any], ...]
    priority_stress_rows: tuple[Mapping[str, Any], ...]
    predicted_dispatch_rows: tuple[Mapping[str, Any], ...]
    schedule_hashes: tuple[Mapping[str, Any], ...]
    coverage: Mapping[str, Any]


def _rows(payload: Mapping[str, Any], name: str) -> tuple[Mapping[str, Any], ...]:
    if name not in payload:
        raise ConfirmationAnalysisError(f"missing confirmation table: {name}")
    raw = payload[name]
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
        raise ConfirmationAnalysisError(f"{name} must be a sequence of rows")
    result: list[Mapping[str, Any]] = []
    for index, row in enumerate(raw):
        if not isinstance(row, Mapping):
            raise ConfirmationAnalysisError(f"{name}[{index}] must be a mapping")
        result.append(row)
    return tuple(result)


def _row_key(row: Mapping[str, Any], fields: Sequence[str], table: str) -> tuple[Any, ...]:
    values: list[Any] = []
    for field in fields:
        if field not in row:
            raise ConfirmationAnalysisError(f"{table} row is missing key field {field}")
        value = row[field]
        if field == "seed":
            if isinstance(value, bool) or not isinstance(value, int):
                raise ConfirmationAnalysisError(f"{table}.seed must be an integer")
            values.append(value)
        else:
            text = str(value)
            if not text:
                raise ConfirmationAnalysisError(f"{table}.{field} cannot be empty")
            values.append(text)
    return tuple(values)


def _audit_exact_matrix(
    rows: Sequence[Mapping[str, Any]],
    *,
    table: str,
    key_fields: tuple[str, ...],
    axes: Sequence[Sequence[Any]],
) -> dict[tuple[Any, ...], Mapping[str, Any]]:
    expected = set(itertools.product(*axes))
    observed: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    duplicates: list[tuple[Any, ...]] = []
    for row in rows:
        key = _row_key(row, key_fields, table)
        if key in observed:
            duplicates.append(key)
        else:
            observed[key] = row
    if duplicates:
        raise ConfirmationAnalysisError(
            f"{table} contains duplicate composite keys: {sorted(set(duplicates))[:5]}"
        )
    missing = expected.difference(observed)
    extra = set(observed).difference(expected)
    if missing or extra:
        raise ConfirmationAnalysisError(
            f"{table} coverage mismatch: missing={sorted(missing)[:5]}, "
            f"extra={sorted(extra)[:5]}"
        )
    if len(rows) != len(expected):
        raise ConfirmationAnalysisError(
            f"{table} row count {len(rows)} does not equal locked count {len(expected)}"
        )
    return observed


def _finite(value: Any, path: str) -> float:
    if isinstance(value, bool):
        raise ConfirmationAnalysisError(f"{path} must be numeric, not boolean")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ConfirmationAnalysisError(f"{path} must be numeric") from error
    if not math.isfinite(number):
        raise ConfirmationAnalysisError(f"{path} must be finite")
    return number


def _positive_integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ConfirmationAnalysisError(f"{path} must be a positive integer")
    return value


def _metrics(row: Mapping[str, Any], table: str) -> Mapping[str, Any]:
    metrics = row.get("metrics")
    if not isinstance(metrics, Mapping):
        raise ConfirmationAnalysisError(f"{table}.metrics must be a mapping")
    return metrics


def _validate_clustering_metrics(rows: Sequence[Mapping[str, Any]]) -> None:
    for index, row in enumerate(rows):
        metrics = _metrics(row, f"clustering_rows[{index}]")
        ari = _finite(metrics.get("ari_linked"), f"clustering_rows[{index}].metrics.ari_linked")
        if not -1.0 <= ari <= 1.0:
            raise ConfirmationAnalysisError("ari_linked must be in [-1, 1]")
        false_rate = _finite(
            metrics.get("false_destinations_per_100_reports"),
            f"clustering_rows[{index}].metrics.false_destinations_per_100_reports",
        )
        if false_rate < 0.0:
            raise ConfirmationAnalysisError("false-destination rate cannot be negative")
        n_reports = _positive_integer(
            metrics.get("n_reports"), f"clustering_rows[{index}].metrics.n_reports"
        )
        n_false = metrics.get("n_false_destinations")
        if isinstance(n_false, bool) or not isinstance(n_false, int) or n_false < 0:
            raise ConfirmationAnalysisError("n_false_destinations must be a non-negative integer")
        expected_rate = 100.0 * n_false / n_reports
        if not math.isclose(false_rate, expected_rate, rel_tol=1e-9, abs_tol=1e-9):
            raise ConfirmationAnalysisError(
                "false_destinations_per_100_reports disagrees with its denominator"
            )
        review_rate = _finite(
            metrics.get("review_items_per_100_reports"),
            f"clustering_rows[{index}].metrics.review_items_per_100_reports",
        )
        n_review = metrics.get("n_review_items")
        if isinstance(n_review, bool) or not isinstance(n_review, int) or n_review < 0:
            raise ConfirmationAnalysisError("n_review_items must be non-negative")
        if not math.isclose(
            review_rate,
            100.0 * n_review / n_reports,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ConfirmationAnalysisError(
                "review_items_per_100_reports disagrees with its denominator"
            )
        denominator_pairs = (
            ("split_loss", "n_split_incidents", "n_incidents_with_reports"),
            ("merge_loss", "n_merged_linked_destinations", "n_linked_destinations"),
            ("noise_rejection", "n_noise_rejected", "n_noise_reports"),
        )
        for endpoint, numerator_name, denominator_name in denominator_pairs:
            value = _finite(metrics.get(endpoint), f"clustering_rows[{index}].metrics.{endpoint}")
            numerator = metrics.get(numerator_name)
            denominator = metrics.get(denominator_name)
            if (
                isinstance(numerator, bool)
                or not isinstance(numerator, int)
                or numerator < 0
                or isinstance(denominator, bool)
                or not isinstance(denominator, int)
                or denominator < 0
            ):
                raise ConfirmationAnalysisError(f"{endpoint} count denominator is invalid")
            expected_value = numerator / max(1, denominator)
            if not math.isclose(value, expected_value, rel_tol=1e-9, abs_tol=1e-9):
                raise ConfirmationAnalysisError(f"{endpoint} disagrees with its denominator")
        for endpoint in ("singleton_rate",):
            value = _finite(metrics.get(endpoint), f"clustering_rows[{index}].metrics.{endpoint}")
            if not 0.0 <= value <= 1.0:
                raise ConfirmationAnalysisError(f"{endpoint} must be in [0, 1]")
        if _finite(metrics.get("max_diameter_m"), f"clustering_rows[{index}].metrics.max_diameter_m") < 0.0:
            raise ConfirmationAnalysisError("max_diameter_m cannot be negative")


def _validate_priority_metrics(rows: Sequence[Mapping[str, Any]]) -> None:
    for index, row in enumerate(rows):
        if row.get("evaluation_partition") != "predicted_clusters_one_to_one_max_overlap":
            raise ConfirmationAnalysisError(
                "priority_rows must come from predicted-cluster one-to-one evaluation"
            )
        metrics = _metrics(row, f"priority_rows[{index}]")
        ndcg = _finite(metrics.get("ndcg_at_k"), f"priority_rows[{index}].metrics.ndcg_at_k")
        if not 0.0 <= ndcg <= 1.0 + 1e-12:
            raise ConfirmationAnalysisError("ndcg_at_k must be in [0, 1]")
        n_units = _positive_integer(
            metrics.get("n_ranking_units"),
            f"priority_rows[{index}].metrics.n_ranking_units",
        )
        denominator = metrics.get("denominator")
        if not isinstance(denominator, Mapping) or denominator.get("n_ranking_units") != n_units:
            raise ConfirmationAnalysisError("priority ranking denominator is absent or inconsistent")
        cutoff = _positive_integer(metrics.get("k"), f"priority_rows[{index}].metrics.k")
        if cutoff != min(5, n_units):
            raise ConfirmationAnalysisError("priority endpoint must use the NDCG@5 cutoff")
        tau = _finite(metrics.get("kendall_tau_b"), f"priority_rows[{index}].metrics.kendall_tau_b")
        recall = _finite(metrics.get("top_k_recall"), f"priority_rows[{index}].metrics.top_k_recall")
        regret = _finite(metrics.get("rank_regret"), f"priority_rows[{index}].metrics.rank_regret")
        if not -1.0 <= tau <= 1.0 or not 0.0 <= recall <= 1.0 or regret < -1e-12:
            raise ConfirmationAnalysisError("priority secondary metric is outside its valid range")


def _stress_value(row: Mapping[str, Any], endpoint: str, path: str) -> float:
    if endpoint == CAMPAIGN_ENDPOINT[0]:
        lift = row.get("false_priority_lift")
        if not isinstance(lift, Mapping):
            raise ConfirmationAnalysisError(f"{path}.false_priority_lift must be a mapping")
        return _finite(
            lift.get("normalized_score_change"),
            f"{path}.false_priority_lift.normalized_score_change",
        )
    drift = row.get("drift")
    if not isinstance(drift, Mapping):
        raise ConfirmationAnalysisError(f"{path}.drift must be a mapping")
    return _finite(drift.get(endpoint), f"{path}.drift.{endpoint}")


def _validate_stress_metrics(rows: Sequence[Mapping[str, Any]]) -> None:
    campaign = "coordinated_high_confidence_campaign"
    for index, row in enumerate(rows):
        path = f"priority_stress_rows[{index}]"
        if row.get("target_selection") != "observable_minimum_membership_hash":
            raise ConfirmationAnalysisError(
                "stress target selection must use the locked observable-only rule"
            )
        for endpoint, _ in (*STRESS_ENDPOINTS, *STRESS_SECONDARY_ENDPOINTS):
            value = _stress_value(row, endpoint, path)
            if value < 0.0:
                raise ConfirmationAnalysisError(f"{endpoint} cannot be negative")
        lift = row.get("false_priority_lift")
        assert isinstance(lift, Mapping)
        applicable = lift.get("applicable")
        expected_applicable = str(row.get("family")) == campaign
        if applicable is not expected_applicable:
            raise ConfirmationAnalysisError(
                "false_priority_lift applicability must be campaign-only"
            )
        value = _stress_value(row, CAMPAIGN_ENDPOINT[0], path)
        if not 0.0 <= value <= 1.0 + 1e-12:
            raise ConfirmationAnalysisError("normalized false-priority lift must be in [0, 1]")


def _validate_dispatch_metrics(rows: Sequence[Mapping[str, Any]]) -> None:
    for index, row in enumerate(rows):
        if row.get("partition") != "predicted_product_clusters":
            raise ConfirmationAnalysisError(
                "predicted_dispatch_rows cannot contain oracle-grouping results"
            )
        metrics = _metrics(row, f"predicted_dispatch_rows[{index}]")
        harm = _finite(metrics.get("total_harm"), f"predicted_dispatch_rows[{index}].metrics.total_harm")
        rate = _finite(
            metrics.get("deadline_miss_rate"),
            f"predicted_dispatch_rows[{index}].metrics.deadline_miss_rate",
        )
        if harm < 0.0 or not 0.0 <= rate <= 1.0:
            raise ConfirmationAnalysisError("dispatch harm/rate are outside valid bounds")
        n_incidents = _positive_integer(
            metrics.get("n_incidents"),
            f"predicted_dispatch_rows[{index}].metrics.n_incidents",
        )
        missed = metrics.get("missed_deadlines")
        if isinstance(missed, bool) or not isinstance(missed, int) or not 0 <= missed <= n_incidents:
            raise ConfirmationAnalysisError("missed_deadlines has an invalid denominator")
        if not math.isclose(rate, missed / n_incidents, rel_tol=1e-9, abs_tol=1e-9):
            raise ConfirmationAnalysisError("deadline_miss_rate disagrees with n_incidents")
        for endpoint in ("unreached_incidents", "false_trips", "duplicate_trips"):
            value = metrics.get(endpoint)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ConfirmationAnalysisError(f"{endpoint} must be a non-negative integer")
        for endpoint in ("max_response_min", "cvar90_response_min", "workload_cv"):
            if _finite(metrics.get(endpoint), f"predicted_dispatch_rows[{index}].metrics.{endpoint}") < 0.0:
                raise ConfirmationAnalysisError(f"{endpoint} cannot be negative")


def _validate_hashes(rows: Sequence[Mapping[str, Any]]) -> None:
    hexadecimal = set("0123456789abcdef")
    for index, row in enumerate(rows):
        values = [row[name] for name in ("schedule_hash", "hash") if name in row]
        if len(values) != 1:
            raise ConfirmationAnalysisError(
                f"schedule_hashes[{index}] must contain exactly one hash field"
            )
        digest = str(values[0])
        if len(digest) != 64 or any(character not in hexadecimal for character in digest):
            raise ConfirmationAnalysisError(
                f"schedule_hashes[{index}] is not a lowercase SHA-256 digest"
            )


def validate_confirmation_payload(
    payload: Mapping[str, Any],
    spec: ConfirmationAnalysisSpec,
) -> ValidatedConfirmationPayload:
    """Validate every locked composite key and scientific row denominator."""

    if not isinstance(payload, Mapping):
        raise ConfirmationAnalysisError("confirmation payload must be a mapping")
    if payload.get("schema_version") != "v2.confirmation-result.1":
        raise ConfirmationAnalysisError("unsupported confirmation payload schema")
    if payload.get("confirmation_master_seeds") != list(spec.seeds):
        raise ConfirmationAnalysisError(
            "confirmation payload does not bind the expected master seeds in order"
        )
    if payload.get("adverse_results_retained") is not True:
        raise ConfirmationAnalysisError("adverse/null result retention is not declared")
    if payload.get("priority_scoring_uses_truth") is not False:
        raise ConfirmationAnalysisError("priority scoring must be truth-free")
    if payload.get("truth_used_by_scheduler") is not False:
        raise ConfirmationAnalysisError("the scheduler must not consume evaluator truth")
    clustering = _rows(payload, "clustering_rows")
    priority = _rows(payload, "priority_rows")
    stress = _rows(payload, "priority_stress_rows")
    dispatch = _rows(payload, "predicted_dispatch_rows")
    hashes = _rows(payload, "schedule_hashes")

    matrices = {
        "clustering_rows": _audit_exact_matrix(
            clustering,
            table="clustering_rows",
            key_fields=("method", "seed", "regime"),
            axes=(spec.methods, spec.seeds, spec.regimes),
        ),
        "priority_rows": _audit_exact_matrix(
            priority,
            table="priority_rows",
            key_fields=("policy", "seed", "regime"),
            axes=(spec.priority_policies, spec.seeds, spec.regimes),
        ),
        "priority_stress_rows": _audit_exact_matrix(
            stress,
            table="priority_stress_rows",
            key_fields=("family", "policy", "seed", "regime"),
            axes=(spec.stress_families, spec.priority_policies, spec.seeds, spec.regimes),
        ),
        "predicted_dispatch_rows": _audit_exact_matrix(
            dispatch,
            table="predicted_dispatch_rows",
            key_fields=("seed", "regime", "scenario", "policy"),
            axes=(spec.seeds, spec.regimes, spec.scenarios, spec.dispatch_policies),
        ),
        "schedule_hashes": _audit_exact_matrix(
            hashes,
            table="schedule_hashes",
            key_fields=("seed", "regime", "scenario", "policy"),
            axes=(spec.seeds, spec.regimes, spec.scenarios, spec.dispatch_policies),
        ),
    }
    _validate_clustering_metrics(clustering)
    _validate_priority_metrics(priority)
    _validate_stress_metrics(stress)
    _validate_dispatch_metrics(dispatch)
    _validate_hashes(hashes)

    # Denominators that should be policy/method invariant are also audited
    # across rows.  Row-local arithmetic alone cannot detect a mixed dataset.
    clustering_index = matrices["clustering_rows"]
    priority_index = matrices["priority_rows"]
    dispatch_index = matrices["predicted_dispatch_rows"]
    for seed in spec.seeds:
        for regime in spec.regimes:
            report_counts = {
                _metrics(clustering_index[(method, seed, regime)], "clustering_rows")[
                    "n_reports"
                ]
                for method in spec.methods
            }
            if len(report_counts) != 1:
                raise ConfirmationAnalysisError(
                    "clustering methods disagree on the report denominator"
                )
            ranking_counts = {
                _metrics(priority_index[(policy, seed, regime)], "priority_rows")[
                    "n_ranking_units"
                ]
                for policy in spec.priority_policies
            }
            if len(ranking_counts) != 1:
                raise ConfirmationAnalysisError(
                    "priority policies disagree on the predicted-unit denominator"
                )
            incident_counts = {
                _metrics(
                    dispatch_index[(seed, regime, scenario, policy)],
                    "predicted_dispatch_rows",
                )["n_incidents"]
                for scenario in spec.scenarios
                for policy in spec.dispatch_policies
            }
            if len(incident_counts) != 1:
                raise ConfirmationAnalysisError(
                    "dispatch rows disagree on the incident denominator within a dataset"
                )

    expected_counts = {name: len(matrix) for name, matrix in matrices.items()}
    return ValidatedConfirmationPayload(
        clustering_rows=clustering,
        priority_rows=priority,
        priority_stress_rows=stress,
        predicted_dispatch_rows=dispatch,
        schedule_hashes=hashes,
        coverage={
            "status": "exact",
            "master_seed_count": len(spec.seeds),
            "expected_and_observed_counts": expected_counts,
            "duplicate_keys": 0,
            "missing_keys": 0,
            "extra_keys": 0,
        },
    )


def _describe(values: Sequence[float]) -> dict[str, float | int]:
    clean = tuple(float(value) for value in values)
    if not clean or not all(math.isfinite(value) for value in clean):
        raise ConfirmationAnalysisError("descriptive input must be non-empty and finite")
    return {
        "n": len(clean),
        "mean": fmean(clean),
        "standard_deviation": stdev(clean) if len(clean) > 1 else 0.0,
        "median": median(clean),
        "minimum": min(clean),
        "maximum": max(clean),
    }


def _derived_bootstrap_seed(base: int, identifier: str) -> int:
    if isinstance(base, bool) or not isinstance(base, int):
        raise ConfirmationAnalysisError("bootstrap seed must be an integer")
    digest = hashlib.sha256(identifier.encode("utf-8")).digest()
    return (base + int.from_bytes(digest[:8], "big")) % (2**63 - 1)


def _comparison(
    identifier: str,
    candidate: Mapping[int, float],
    comparator: Mapping[int, float],
    *,
    direction: str,
    candidate_id: str,
    comparator_id: str,
    regime: str,
    endpoint: str,
    base_bootstrap_seed: int,
    extra_denominator: Mapping[str, int | float | str] | None = None,
) -> dict[str, Any]:
    denominator: dict[str, int | float | str] = {
        "unit": "master_seed",
        "n_master_seeds": len(candidate),
        "regime": regime,
        "endpoint": endpoint,
        "candidate": candidate_id,
        "comparator": comparator_id,
    }
    if extra_denominator:
        denominator.update(extra_denominator)
    result = paired_comparison_by_key(
        candidate,
        comparator,
        direction=direction,
        denominator=denominator,
        bootstrap_seed=_derived_bootstrap_seed(base_bootstrap_seed, identifier),
    )
    result.update(
        {
            "comparison_id": identifier,
            "candidate": candidate_id,
            "comparator": comparator_id,
            "regime": regime,
            "endpoint": endpoint,
            "adverse_or_null": result["mean_improvement"] <= 0.0,
        }
    )
    return result


def _index(
    rows: Sequence[Mapping[str, Any]], key_fields: Sequence[str]
) -> dict[tuple[Any, ...], Mapping[str, Any]]:
    return {tuple(row[field] for field in key_fields): row for row in rows}


def _clustering_analysis(
    validated: ValidatedConfirmationPayload,
    spec: ConfirmationAnalysisSpec,
    bootstrap_seed: int,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    rows = _index(validated.clustering_rows, ("method", "seed", "regime"))
    descriptives: dict[str, Any] = {}
    comparisons: dict[str, dict[str, Any]] = {}
    for regime in spec.regimes:
        for method in spec.methods:
            for endpoint in (
                *(name for name, _ in CLUSTERING_ENDPOINTS),
                *CLUSTERING_SECONDARY_ENDPOINTS,
            ):
                identifier = f"clustering.{regime}.{method}.{endpoint}"
                descriptives[identifier] = _describe(
                    [float(_metrics(rows[(method, seed, regime)], "clustering_rows")[endpoint]) for seed in spec.seeds]
                )
        for endpoint, direction in CLUSTERING_ENDPOINTS:
            identifier = f"clustering.{regime}.{endpoint}.product_vs_additive"
            candidate = {
                seed: float(_metrics(rows[(spec.product_method, seed, regime)], "clustering_rows")[endpoint])
                for seed in spec.seeds
            }
            comparator = {
                seed: float(_metrics(rows[(spec.additive_method, seed, regime)], "clustering_rows")[endpoint])
                for seed in spec.seeds
            }
            comparisons[identifier] = _comparison(
                identifier,
                candidate,
                comparator,
                direction=direction,
                candidate_id=spec.product_method,
                comparator_id=spec.additive_method,
                regime=regime,
                endpoint=endpoint,
                base_bootstrap_seed=bootstrap_seed,
            )
    return descriptives, comparisons


def _priority_analysis(
    validated: ValidatedConfirmationPayload,
    spec: ConfirmationAnalysisSpec,
    bootstrap_seed: int,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    rows = _index(validated.priority_rows, ("policy", "seed", "regime"))
    endpoint, direction = PRIORITY_ENDPOINT
    descriptives: dict[str, Any] = {}
    comparisons: dict[str, dict[str, Any]] = {}
    comparators = tuple(policy for policy in spec.priority_policies if policy != spec.revised_policy)
    for regime in spec.regimes:
        for policy in spec.priority_policies:
            for descriptive_endpoint in (endpoint, *PRIORITY_SECONDARY_ENDPOINTS):
                identifier = f"priority.{regime}.{policy}.{descriptive_endpoint}"
                descriptives[identifier] = _describe(
                    [
                        float(
                            _metrics(
                                rows[(policy, seed, regime)], "priority_rows"
                            )[descriptive_endpoint]
                        )
                        for seed in spec.seeds
                    ]
                )
        for comparator_id in comparators:
            identifier = f"priority.{regime}.{endpoint}.revised_vs_{comparator_id}"
            candidate = {
                seed: float(_metrics(rows[(spec.revised_policy, seed, regime)], "priority_rows")[endpoint])
                for seed in spec.seeds
            }
            comparator = {
                seed: float(_metrics(rows[(comparator_id, seed, regime)], "priority_rows")[endpoint])
                for seed in spec.seeds
            }
            comparisons[identifier] = _comparison(
                identifier,
                candidate,
                comparator,
                direction=direction,
                candidate_id=spec.revised_policy,
                comparator_id=comparator_id,
                regime=regime,
                endpoint=endpoint,
                base_bootstrap_seed=bootstrap_seed,
            )
    return descriptives, comparisons


def _dispatch_seed_means(
    rows: Mapping[tuple[Any, ...], Mapping[str, Any]],
    spec: ConfirmationAnalysisSpec,
    *,
    policy: str,
    regime: str,
    endpoint: str,
) -> dict[int, float]:
    return {
        seed: fmean(
            float(
                _metrics(
                    rows[(seed, regime, scenario, policy)],
                    "predicted_dispatch_rows",
                )[endpoint]
            )
            for scenario in spec.scenarios
        )
        for seed in spec.seeds
    }


def _dispatch_analysis(
    validated: ValidatedConfirmationPayload,
    spec: ConfirmationAnalysisSpec,
    bootstrap_seed: int,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    rows = _index(
        validated.predicted_dispatch_rows,
        ("seed", "regime", "scenario", "policy"),
    )
    descriptives: dict[str, Any] = {}
    comparisons: dict[str, dict[str, Any]] = {}
    comparators = tuple(policy for policy in spec.dispatch_policies if policy != spec.revised_policy)
    for regime in spec.regimes:
        for endpoint, direction in DISPATCH_ENDPOINTS:
            per_policy = {
                policy: _dispatch_seed_means(
                    rows, spec, policy=policy, regime=regime, endpoint=endpoint
                )
                for policy in spec.dispatch_policies
            }
            for policy, values in per_policy.items():
                descriptives[f"dispatch.{regime}.{policy}.{endpoint}.scenario_mean"] = _describe(
                    list(values.values())
                )
            for comparator_id in comparators:
                identifier = f"dispatch.{regime}.{endpoint}.revised_vs_{comparator_id}"
                comparisons[identifier] = _comparison(
                    identifier,
                    per_policy[spec.revised_policy],
                    per_policy[comparator_id],
                    direction=direction,
                    candidate_id=spec.revised_policy,
                    comparator_id=comparator_id,
                    regime=regime,
                    endpoint=endpoint,
                    base_bootstrap_seed=bootstrap_seed,
                    extra_denominator={
                        "scenario_aggregation": "unweighted_mean_of_locked_scenarios",
                        "n_scenarios_per_seed": len(spec.scenarios),
                    },
                )
        for endpoint in DISPATCH_GUARDRAILS:
            for policy in spec.dispatch_policies:
                values = _dispatch_seed_means(
                    rows,
                    spec,
                    policy=policy,
                    regime=regime,
                    endpoint=endpoint,
                )
                descriptives[
                    f"dispatch.{regime}.{policy}.{endpoint}.scenario_mean"
                ] = _describe(list(values.values()))
    return descriptives, comparisons


def _stress_analysis(
    validated: ValidatedConfirmationPayload,
    spec: ConfirmationAnalysisSpec,
    bootstrap_seed: int,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    rows = _index(
        validated.priority_stress_rows,
        ("family", "policy", "seed", "regime"),
    )
    descriptives: dict[str, Any] = {}
    comparisons: dict[str, dict[str, Any]] = {}
    comparators = tuple(policy for policy in spec.priority_policies if policy != spec.revised_policy)
    campaign = "coordinated_high_confidence_campaign"
    for regime in spec.regimes:
        for family in spec.stress_families:
            endpoints = list(STRESS_ENDPOINTS)
            if family == campaign:
                endpoints.append(CAMPAIGN_ENDPOINT)
            for endpoint, direction in endpoints:
                values_by_policy: dict[str, dict[int, float]] = {}
                for policy in spec.priority_policies:
                    values_by_policy[policy] = {
                        seed: _stress_value(
                            rows[(family, policy, seed, regime)],
                            endpoint,
                            "priority_stress_rows",
                        )
                        for seed in spec.seeds
                    }
                    identifier = f"stress.{regime}.{family}.{policy}.{endpoint}"
                    descriptives[identifier] = _describe(
                        list(values_by_policy[policy].values())
                    )
                for comparator_id in comparators:
                    identifier = (
                        f"stress.{regime}.{family}.{endpoint}."
                        f"revised_vs_{comparator_id}"
                    )
                    comparisons[identifier] = _comparison(
                        identifier,
                        values_by_policy[spec.revised_policy],
                        values_by_policy[comparator_id],
                        direction=direction,
                        candidate_id=spec.revised_policy,
                        comparator_id=comparator_id,
                        regime=regime,
                        endpoint=endpoint,
                        base_bootstrap_seed=bootstrap_seed,
                        extra_denominator={"stress_family": family},
                    )
            for endpoint, _ in STRESS_SECONDARY_ENDPOINTS:
                for policy in spec.priority_policies:
                    values = [
                        _stress_value(
                            rows[(family, policy, seed, regime)],
                            endpoint,
                            "priority_stress_rows",
                        )
                        for seed in spec.seeds
                    ]
                    descriptives[
                        f"stress.{regime}.{family}.{policy}.{endpoint}"
                    ] = _describe(values)
    return descriptives, comparisons


def _replace_adjusted(
    sections: Sequence[dict[str, dict[str, Any]]],
    adjusted: Mapping[str, Mapping[str, Any]],
) -> None:
    for section in sections:
        for identifier in tuple(section):
            section[identifier] = dict(adjusted[identifier])


def _gate(
    claim_id: str,
    claim: str,
    scope: str,
    conditions: Mapping[str, bool],
) -> dict[str, Any]:
    failed = sorted(name for name, passed in conditions.items() if not passed)
    return {
        "claim_id": claim_id,
        "claim": claim,
        "scope": scope,
        "status": "eligible" if not failed else "blocked",
        "conditions": dict(conditions),
        "blocked_reasons": failed,
    }


def _positive_confirmatory(comparison: Mapping[str, Any]) -> bool:
    interval = comparison["paired_confidence_interval"]
    return (
        float(interval[0]) > 0.0
        and float(comparison["holm_adjusted_p_value"]) < 0.05
    )


def _claim_gates(
    spec: ConfirmationAnalysisSpec,
    clustering: Mapping[str, Mapping[str, Any]],
    priority: Mapping[str, Mapping[str, Any]],
    stress_descriptives: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    cluster_id = "clustering.id.ari_linked.product_vs_additive"
    cluster_ood = "clustering.ood.ari_linked.product_vs_additive"
    cluster_gate = _gate(
        "claim.synthetic_controlled_clustering",
        "product ARI advantage after symmetric independent selection",
        "controlled synthetic confirmation only",
        {
            "id_ari_ci_above_zero_and_holm_significant": _positive_confirmatory(clustering[cluster_id]),
            "ood_ari_not_reversed": float(clustering[cluster_ood]["mean_improvement"]) >= 0.0,
            "false_destination_co_primary_retained_id_and_ood": all(
                math.isfinite(
                    float(
                        clustering[
                            f"clustering.{regime}.false_destinations_per_100_reports.product_vs_additive"
                        ]["mean_improvement"]
                    )
                )
                for regime in spec.regimes
            ),
        },
    )

    priority_conditions: dict[str, bool] = {}
    for comparator in (policy for policy in spec.priority_policies if policy != spec.revised_policy):
        id_result = priority[f"priority.id.ndcg_at_k.revised_vs_{comparator}"]
        ood_result = priority[f"priority.ood.ndcg_at_k.revised_vs_{comparator}"]
        priority_conditions[f"id_beats_{comparator}"] = _positive_confirmatory(id_result)
        priority_conditions[f"ood_not_reversed_vs_{comparator}"] = (
            float(ood_result["mean_improvement"]) >= 0.0
        )
    priority_gate = _gate(
        "claim.synthetic_priority_alignment",
        "revised priority alignment",
        "independent synthetic gain on predicted clusters only",
        priority_conditions,
    )

    exact_conditions = {
        f"{regime}_exact_duplicate_score_invariance": float(
            stress_descriptives[
                f"stress.{regime}.exact_duplicate.{spec.revised_policy}.max_absolute_score_drift"
            ]["maximum"]
        )
        <= 1e-12
        for regime in spec.regimes
    }
    exact_conditions["coordinated_campaign_failure_retained"] = all(
        f"stress.{regime}.coordinated_high_confidence_campaign."
        f"{spec.revised_policy}.false_priority_lift" in stress_descriptives
        for regime in spec.regimes
    )
    exact_gate = _gate(
        "claim.synthetic_duplicate_invariance",
        "exact-duplicate priority score invariance",
        "locked synthetic exact-duplicate perturbation only",
        exact_conditions,
    )

    blocked_specs = {
        "claim.external_priority_sanity": (
            "external information-criticality sanity",
            "alignment_with_human_information_criticality",
            "authorized_trec_snapshot_and_held_out_adapter_unavailable",
        ),
        "claim.external_consolidation_sanity": (
            "external consolidation sanity",
            "redundancy_and_fact_retention_proxy",
            "authorized_crisisfacts_snapshot_and_adapter_unavailable",
        ),
        "claim.external_location_sanity": (
            "external location sanity",
            "location_feature_extraction_transfer",
            "released_idrisi_snapshot_has_no_labeled_test_partition",
        ),
        "claim.external_flood_context_descriptive": (
            "external flood context descriptive claim",
            "event_context_and_outcome_distribution_sanity",
            "source_manifest_access_gates_remain_blocked",
        ),
        "claim.real_incident_clustering_accuracy": (
            "real incident clustering accuracy",
            "none_until_new_authorized_annotation_exists",
            "no_physical_incident_partition",
        ),
        "claim.real_dispatch_benefit": (
            "real dispatch benefit",
            "none_for_current_public_sources",
            "no_observed_dispatch_outcomes_or_expert_validated_policy",
        ),
        "claim.vietnamese_transfer": (
            "Vietnamese-language transfer",
            "none_for_current_public_sources",
            "no_authorized_vietnamese_annotated_reports",
        ),
    }
    blocked = {
        claim_id: {
            "claim_id": claim_id,
            "claim": label,
            "scope": scope,
            "status": "blocked",
            "conditions": {reason: False},
            "blocked_reasons": [reason],
        }
        for claim_id, (label, scope, reason) in blocked_specs.items()
    }
    return {
        "claim.synthetic_controlled_clustering": cluster_gate,
        "claim.synthetic_duplicate_invariance": exact_gate,
        "claim.synthetic_priority_alignment": priority_gate,
        **blocked,
    }


def _dispatch_evidence_gate(
    spec: ConfirmationAnalysisSpec,
    dispatch: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Conservative synthetic evidence view, not a registered policy claim."""

    dispatch_conditions: dict[str, bool] = {}
    for comparator in (policy for policy in spec.dispatch_policies if policy != spec.revised_policy):
        for endpoint, _ in DISPATCH_ENDPOINTS:
            for regime in spec.regimes:
                result = dispatch[f"dispatch.{regime}.{endpoint}.revised_vs_{comparator}"]
                dispatch_conditions[f"{regime}_{endpoint}_beats_{comparator}"] = (
                    _positive_confirmatory(result)
                )
    dispatch_gate = _gate(
        "evidence.synthetic_predicted_cluster_dispatch",
        "revised predicted-cluster dispatch benefit",
        "three locked synthetic resource scenarios",
        dispatch_conditions,
    )
    return dispatch_gate


def analyze_confirmation_payload(
    payload: Mapping[str, Any],
    spec: ConfirmationAnalysisSpec,
    *,
    bootstrap_seed: int = 20260811,
) -> dict[str, Any]:
    """Return complete descriptives, paired inference, Holm results, and gates."""

    validated = validate_confirmation_payload(payload, spec)
    clustering_desc, clustering_cmp = _clustering_analysis(
        validated, spec, bootstrap_seed
    )
    priority_desc, priority_cmp = _priority_analysis(validated, spec, bootstrap_seed)
    dispatch_desc, dispatch_cmp = _dispatch_analysis(validated, spec, bootstrap_seed)
    stress_desc, stress_cmp = _stress_analysis(validated, spec, bootstrap_seed)

    clustering_adjusted = holm_adjust(clustering_cmp)
    priority_dispatch_unadjusted = {
        **priority_cmp,
        **dispatch_cmp,
        **stress_cmp,
    }
    priority_dispatch_adjusted = holm_adjust(priority_dispatch_unadjusted)
    _replace_adjusted((clustering_cmp,), clustering_adjusted)
    _replace_adjusted(
        (priority_cmp, dispatch_cmp, stress_cmp), priority_dispatch_adjusted
    )

    return {
        "schema_version": "confirmation-analysis-v2",
        "coverage": dict(validated.coverage),
        "analysis_contract": {
            "pairing_unit": "master_seed",
            "bootstrap_resamples": 10_000,
            "bootstrap_interval": 0.95,
            "wilcoxon": (
                "two-sided matched-pairs signed-rank; zero differences are reported "
                "and handled with zero_method=wilcox"
            ),
            "holm_families": {
                "synthetic_clustering": sorted(clustering_cmp),
                "synthetic_priority_dispatch": sorted(priority_dispatch_unadjusted),
            },
            "dispatch_scenario_aggregation": "unweighted mean within seed before inference",
            "adverse_and_null_results_retained": True,
        },
        "descriptives": {
            "clustering": clustering_desc,
            "priority": priority_desc,
            "dispatch": dispatch_desc,
            "stress": stress_desc,
        },
        "comparisons": {
            "clustering": clustering_cmp,
            "priority": priority_cmp,
            "dispatch": dispatch_cmp,
            "stress": stress_cmp,
        },
        "claim_gates": _claim_gates(
            spec,
            clustering_cmp,
            priority_cmp,
            stress_desc,
        ),
        "evidence_gates": {
            "predicted_cluster_dispatch": _dispatch_evidence_gate(
                spec, dispatch_cmp
            )
        },
    }


__all__ = [
    "CAMPAIGN_ENDPOINT",
    "CLUSTERING_ENDPOINTS",
    "CLUSTERING_SECONDARY_ENDPOINTS",
    "ConfirmationAnalysisError",
    "ConfirmationAnalysisSpec",
    "DEFAULT_DISPATCH_POLICIES",
    "DEFAULT_METHODS",
    "DEFAULT_PRIORITY_POLICIES",
    "DEFAULT_REGIMES",
    "DEFAULT_SCENARIOS",
    "DISPATCH_ENDPOINTS",
    "DISPATCH_GUARDRAILS",
    "PRIORITY_ENDPOINT",
    "PRIORITY_SECONDARY_ENDPOINTS",
    "STRESS_ENDPOINTS",
    "STRESS_SECONDARY_ENDPOINTS",
    "ValidatedConfirmationPayload",
    "analyze_confirmation_payload",
    "validate_confirmation_payload",
]
