"""Locked statistical reporting helpers for revision experiments.

All functions operate on paired seed-level observations.  Positive
``effect_size`` means the candidate is better after applying the endpoint's
declared direction.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.stats import rankdata, wilcoxon


class InferenceError(ValueError):
    """Raised when an inference request violates the paired-data contract."""


def _finite_vector(values: Sequence[float], name: str) -> np.ndarray:
    vector = np.asarray(list(values), dtype=float)
    if vector.ndim != 1 or vector.size == 0:
        raise InferenceError(f"{name} must be a non-empty one-dimensional vector")
    if not np.isfinite(vector).all():
        raise InferenceError(f"{name} contains a non-finite value")
    return vector


def bootstrap_mean_ci(
    values: Sequence[float],
    *,
    confidence: float = 0.95,
    resamples: int = 5000,
    seed: int = 20260729,
) -> list[float]:
    """Return a deterministic percentile bootstrap CI for the mean."""

    vector = _finite_vector(values, "values")
    if not 0.0 < confidence < 1.0:
        raise InferenceError("confidence must lie strictly between zero and one")
    if isinstance(resamples, bool) or not isinstance(resamples, int) or resamples < 1:
        raise InferenceError("resamples must be a positive integer")
    if vector.size == 1:
        value = float(vector[0])
        return [value, value]
    generator = np.random.default_rng(seed)
    indices = generator.integers(
        0,
        vector.size,
        size=(resamples, vector.size),
    )
    means = vector[indices].mean(axis=1)
    tail = (1.0 - confidence) / 2.0
    return [
        float(np.quantile(means, tail)),
        float(np.quantile(means, 1.0 - tail)),
    ]


def descriptive_summary(
    values: Sequence[float],
    *,
    denominator: int | float | Mapping[str, int | float],
    bootstrap_seed: int = 20260729,
) -> dict[str, Any]:
    """Return every preregistered descriptive field with an explicit denominator."""

    vector = _finite_vector(values, "values")
    return {
        "mean": float(np.mean(vector)),
        "standard_deviation": (
            float(np.std(vector, ddof=1)) if vector.size > 1 else 0.0
        ),
        "median": float(np.median(vector)),
        "paired_confidence_interval": bootstrap_mean_ci(
            vector,
            seed=bootstrap_seed,
        ),
        "denominator": denominator,
        "n_seed_pairs": int(vector.size),
    }


def _rank_biserial(improvement: np.ndarray) -> float:
    nonzero = improvement[improvement != 0.0]
    if nonzero.size == 0:
        return 0.0
    ranks = rankdata(np.abs(nonzero), method="average")
    positive = float(ranks[nonzero > 0.0].sum())
    negative = float(ranks[nonzero < 0.0].sum())
    total = positive + negative
    return (positive - negative) / total if total else 0.0


def paired_comparison(
    candidate: Sequence[float],
    comparator: Sequence[float],
    *,
    direction: str,
    denominator: int | float | Mapping[str, int | float],
    bootstrap_seed: int = 20260729,
) -> dict[str, Any]:
    """Compare paired seeds with direction-aware effects and no dropped ties."""

    candidate_vector = _finite_vector(candidate, "candidate")
    comparator_vector = _finite_vector(comparator, "comparator")
    if candidate_vector.size != comparator_vector.size:
        raise InferenceError("candidate and comparator must have equal paired length")
    if direction not in {"higher", "lower"}:
        raise InferenceError("direction must be 'higher' or 'lower'")

    raw_difference = candidate_vector - comparator_vector
    improvement = raw_difference if direction == "higher" else -raw_difference
    if np.all(improvement == 0.0):
        statistic = 0.0
        raw_p_value = 1.0
    else:
        result = wilcoxon(
            improvement,
            zero_method="wilcox",
            alternative="two-sided",
            method="auto",
        )
        statistic = float(result.statistic)
        raw_p_value = float(result.pvalue)
    standard_deviation = (
        float(np.std(improvement, ddof=1)) if improvement.size > 1 else 0.0
    )
    standardized_effect = (
        float(np.mean(improvement) / standard_deviation)
        if standard_deviation > 0.0
        else (0.0 if np.mean(improvement) == 0.0 else None)
    )
    return {
        "direction": direction,
        "mean": float(np.mean(improvement)),
        "standard_deviation": standard_deviation,
        "median": float(np.median(improvement)),
        "paired_confidence_interval": bootstrap_mean_ci(
            improvement,
            seed=bootstrap_seed,
        ),
        "effect_size": {
            "paired_standardized_mean": standardized_effect,
            "matched_pairs_rank_biserial": _rank_biserial(improvement),
            "orientation": "positive means candidate is better",
        },
        "mean_difference_candidate_minus_comparator": float(
            np.mean(raw_difference)
        ),
        "raw_p_value": raw_p_value,
        "holm_adjusted_p_value": None,
        "wilcoxon_statistic": statistic,
        "denominator": denominator,
        "n_seed_pairs": int(improvement.size),
        "n_candidate_better": int(np.count_nonzero(improvement > 0.0)),
        "n_comparator_better": int(np.count_nonzero(improvement < 0.0)),
        "n_ties": int(np.count_nonzero(improvement == 0.0)),
    }


def holm_adjust(
    p_values: Mapping[str, float | None],
) -> dict[str, float | None]:
    """Apply Holm's step-down adjustment, preserving unavailable tests."""

    valid: list[tuple[str, float]] = []
    adjusted: dict[str, float | None] = {}
    for identifier, raw in p_values.items():
        if raw is None:
            adjusted[identifier] = None
            continue
        value = float(raw)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise InferenceError(f"invalid p-value for {identifier!r}: {raw!r}")
        valid.append((identifier, value))

    valid.sort(key=lambda item: (item[1], item[0]))
    running_max = 0.0
    family_size = len(valid)
    for index, (identifier, raw) in enumerate(valid):
        candidate = min(1.0, (family_size - index) * raw)
        running_max = max(running_max, candidate)
        adjusted[identifier] = running_max
    return adjusted


def apply_holm(
    comparisons: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Copy comparison rows and attach family-wise Holm adjusted p-values."""

    adjusted = holm_adjust({
        identifier: (
            None
            if comparison.get("raw_p_value") is None
            else float(comparison["raw_p_value"])
        )
        for identifier, comparison in comparisons.items()
    })
    output: dict[str, dict[str, Any]] = {}
    for identifier, comparison in comparisons.items():
        row = dict(comparison)
        row["holm_adjusted_p_value"] = adjusted[identifier]
        output[identifier] = row
    return output
