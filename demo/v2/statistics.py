"""Confirmatory ranking and paired-inference utilities for protocol v2.

The functions in this module are deliberately independent of the synthetic
generator.  They consume complete seed-level rows, keep ties, attach explicit
denominators, and use the master seed as the paired resampling unit.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np
from scipy.stats import kendalltau, rankdata, wilcoxon


class StatisticalContractError(ValueError):
    """Raised when an analysis would violate the frozen statistical contract."""


def _finite_vector(values: Sequence[float], name: str) -> np.ndarray:
    vector = np.asarray(tuple(values), dtype=float)
    if vector.ndim != 1 or vector.size == 0:
        raise StatisticalContractError(f"{name} must be a non-empty vector")
    if not np.isfinite(vector).all():
        raise StatisticalContractError(f"{name} contains non-finite values")
    return vector


def paired_bootstrap_mean_ci(
    paired_differences: Sequence[float],
    *,
    confidence: float = 0.95,
    resamples: int = 10_000,
    seed: int = 20260811,
) -> tuple[float, float]:
    """Percentile CI obtained by resampling complete paired master seeds."""

    values = _finite_vector(paired_differences, "paired_differences")
    if not 0.0 < confidence < 1.0:
        raise StatisticalContractError("confidence must be in (0, 1)")
    if isinstance(resamples, bool) or not isinstance(resamples, int) or resamples < 1:
        raise StatisticalContractError("resamples must be a positive integer")
    if values.size == 1:
        value = float(values[0])
        return value, value
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, values.size, size=(resamples, values.size))
    means = values[indices].mean(axis=1)
    alpha = (1.0 - confidence) / 2.0
    return float(np.quantile(means, alpha)), float(np.quantile(means, 1.0 - alpha))


def _rank_biserial(improvement: np.ndarray) -> float:
    nonzero = improvement[improvement != 0.0]
    if nonzero.size == 0:
        return 0.0
    ranks = rankdata(np.abs(nonzero), method="average")
    positive = float(ranks[nonzero > 0.0].sum())
    negative = float(ranks[nonzero < 0.0].sum())
    return (positive - negative) / (positive + negative)


def paired_comparison(
    candidate: Sequence[float],
    comparator: Sequence[float],
    *,
    direction: str,
    denominator: Mapping[str, int | float | str],
    bootstrap_seed: int = 20260811,
) -> dict[str, Any]:
    """Return effect, 10k paired CI, tie counts, and unadjusted inference."""

    candidate_values = _finite_vector(candidate, "candidate")
    comparator_values = _finite_vector(comparator, "comparator")
    if candidate_values.size != comparator_values.size:
        raise StatisticalContractError("candidate/comparator pairing is incomplete")
    if direction not in {"higher", "lower"}:
        raise StatisticalContractError("direction must be 'higher' or 'lower'")
    raw_difference = candidate_values - comparator_values
    improvement = raw_difference if direction == "higher" else -raw_difference
    if np.all(improvement == 0.0):
        statistic, raw_p_value = 0.0, 1.0
    else:
        test = wilcoxon(
            improvement,
            zero_method="wilcox",
            alternative="two-sided",
            method="auto",
        )
        statistic, raw_p_value = float(test.statistic), float(test.pvalue)
    standard_deviation = (
        float(np.std(improvement, ddof=1)) if improvement.size > 1 else 0.0
    )
    mean_improvement = float(np.mean(improvement))
    return {
        "direction": direction,
        "mean_improvement": mean_improvement,
        "median_improvement": float(np.median(improvement)),
        "mean_difference_candidate_minus_comparator": float(np.mean(raw_difference)),
        "paired_confidence_interval": list(
            paired_bootstrap_mean_ci(improvement, seed=bootstrap_seed)
        ),
        "standard_deviation": standard_deviation,
        "paired_standardized_mean": (
            mean_improvement / standard_deviation
            if standard_deviation > 0.0
            else (0.0 if mean_improvement == 0.0 else None)
        ),
        "matched_pairs_rank_biserial": _rank_biserial(improvement),
        "raw_p_value": raw_p_value,
        "holm_adjusted_p_value": None,
        "wilcoxon_statistic": statistic,
        "n_seed_pairs": int(improvement.size),
        "n_candidate_better": int(np.count_nonzero(improvement > 0.0)),
        "n_comparator_better": int(np.count_nonzero(improvement < 0.0)),
        "n_ties": int(np.count_nonzero(improvement == 0.0)),
        "denominator": dict(denominator),
    }


def paired_comparison_by_key(
    candidate: Mapping[str | int, float],
    comparator: Mapping[str | int, float],
    *,
    direction: str,
    denominator: Mapping[str, int | float | str],
    bootstrap_seed: int = 20260811,
) -> dict[str, Any]:
    """Compare paired values after a fail-closed key audit.

    Confirmation results are paired by master seed.  Accepting two positional
    vectors makes an accidental reordering statistically invisible, so the
    public analysis API requires identical keys and records their count.
    """

    if not candidate or set(candidate) != set(comparator):
        raise StatisticalContractError(
            "candidate/comparator must have the same non-empty pairing keys"
        )
    keys = sorted(candidate, key=lambda value: (str(type(value)), str(value)))
    result = paired_comparison(
        [float(candidate[key]) for key in keys],
        [float(comparator[key]) for key in keys],
        direction=direction,
        denominator=denominator,
        bootstrap_seed=bootstrap_seed,
    )
    result["pairing_key"] = "master_seed"
    result["pairing_key_count"] = len(keys)
    return result


def holm_adjust(comparisons: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Apply Holm correction within exactly one caller-declared endpoint family."""

    ordered: list[tuple[str, float]] = []
    for identifier, row in comparisons.items():
        value = float(row["raw_p_value"])
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise StatisticalContractError(f"invalid p-value for {identifier}")
        ordered.append((identifier, value))
    ordered.sort(key=lambda item: (item[1], item[0]))
    adjusted: dict[str, float] = {}
    running = 0.0
    family_size = len(ordered)
    for index, (identifier, value) in enumerate(ordered):
        running = max(running, min(1.0, (family_size - index) * value))
        adjusted[identifier] = running
    output: dict[str, dict[str, Any]] = {}
    for identifier, row in comparisons.items():
        copied = dict(row)
        copied["holm_adjusted_p_value"] = adjusted[identifier]
        output[identifier] = copied
    return output


def _ordered_ids(scores: Mapping[str, float]) -> list[str]:
    if not scores:
        raise StatisticalContractError("ranking cannot be empty")
    clean: dict[str, float] = {}
    for identifier, value in scores.items():
        number = float(value)
        if not identifier or not math.isfinite(number):
            raise StatisticalContractError("ranking ids and scores must be valid")
        clean[str(identifier)] = number
    return sorted(clean, key=lambda identifier: (-clean[identifier], identifier))


def ranking_metrics(
    predicted_scores: Mapping[str, float],
    latent_benefit: Mapping[str, float],
    *,
    k: int = 5,
) -> dict[str, Any]:
    """Evaluate ranking against an independently generated non-negative target."""

    if set(predicted_scores) != set(latent_benefit):
        raise StatisticalContractError("predicted and target rankings must align exactly")
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise StatisticalContractError("k must be a positive integer")
    predicted_order = _ordered_ids(predicted_scores)
    ideal_order = _ordered_ids(latent_benefit)
    identifiers = sorted(predicted_scores)
    target = np.asarray([float(latent_benefit[item]) for item in identifiers])
    scores = np.asarray([float(predicted_scores[item]) for item in identifiers])
    if (target < 0.0).any() or not np.isfinite(target).all():
        raise StatisticalContractError("latent benefit must be finite and non-negative")
    tau = kendalltau(scores, target, variant="b", nan_policy="raise").statistic
    tau_value = 0.0 if tau is None or math.isnan(float(tau)) else float(tau)
    cutoff = min(k, len(identifiers))

    def dcg(order: Sequence[str]) -> float:
        # Latent benefit is a continuous synthetic outcome, not an ordinal
        # relevance grade. Linear gain keeps NDCG invariant to a positive
        # change of outcome units; exponential gain would make the result
        # depend arbitrarily on the authored benefit scale.
        return float(
            sum(
                float(latent_benefit[item]) / math.log2(rank + 2.0)
                for rank, item in enumerate(order[:cutoff])
            )
        )

    ideal_dcg = dcg(ideal_order)
    selected_gain = sum(float(latent_benefit[item]) for item in predicted_order[:cutoff])
    ideal_gain = sum(float(latent_benefit[item]) for item in ideal_order[:cutoff])
    return {
        "ndcg_at_k": dcg(predicted_order) / ideal_dcg if ideal_dcg > 0.0 else 1.0,
        "kendall_tau_b": tau_value,
        "top_k_recall": len(
            set(predicted_order[:cutoff]).intersection(ideal_order[:cutoff])
        )
        / cutoff,
        "rank_regret": ideal_gain - selected_gain,
        "k": cutoff,
        "n_ranking_units": len(identifiers),
        "denominator": {
            "ranking_units": "caller-aligned evaluation units",
            "n_ranking_units": len(identifiers),
        },
    }


def perturbation_drift(
    original_scores: Mapping[str, float],
    perturbed_scores: Mapping[str, float],
    *,
    k: int = 5,
) -> dict[str, Any]:
    """Report rank/top-k drift without treating robustness as target accuracy."""

    if set(original_scores) != set(perturbed_scores):
        raise StatisticalContractError("perturbation rankings must contain the same ids")
    original = _ordered_ids(original_scores)
    perturbed = _ordered_ids(perturbed_scores)
    cutoff = min(max(1, int(k)), len(original))
    original_rank = {identifier: rank for rank, identifier in enumerate(original)}
    perturbed_rank = {identifier: rank for rank, identifier in enumerate(perturbed)}
    denominator = max(1, len(original) - 1)
    return {
        "mean_normalized_rank_drift": float(
            np.mean(
                [
                    abs(original_rank[item] - perturbed_rank[item]) / denominator
                    for item in original
                ]
            )
        ),
        "top_k_set_drift": 1.0
        - len(set(original[:cutoff]).intersection(perturbed[:cutoff])) / cutoff,
        "max_absolute_score_drift": max(
            abs(float(original_scores[item]) - float(perturbed_scores[item]))
            for item in original
        ),
        "k": cutoff,
        "n_incidents": len(original),
    }


def assert_complete_coverage(
    rows: Iterable[Mapping[str, Any]],
    *,
    methods: Sequence[str],
    seeds: Sequence[int],
    regimes: Sequence[str] = ("id", "ood"),
) -> None:
    """Fail on silent omissions or duplicate method/seed/regime result rows."""

    expected = {
        (str(method), int(seed), str(regime))
        for method in methods
        for seed in seeds
        for regime in regimes
    }
    observed: list[tuple[str, int, str]] = [
        (str(row["method"]), int(row["seed"]), str(row["regime"])) for row in rows
    ]
    if len(observed) != len(set(observed)):
        raise StatisticalContractError("coverage matrix contains duplicate rows")
    missing = sorted(expected.difference(observed))
    extra = sorted(set(observed).difference(expected))
    if missing or extra:
        raise StatisticalContractError(
            f"coverage mismatch: missing={missing[:5]}, extra={extra[:5]}"
        )


__all__ = [
    "StatisticalContractError",
    "assert_complete_coverage",
    "holm_adjust",
    "paired_bootstrap_mean_ci",
    "paired_comparison",
    "paired_comparison_by_key",
    "perturbation_drift",
    "ranking_metrics",
]
