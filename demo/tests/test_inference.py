from __future__ import annotations

import math

import pytest

from demo.experiments.inference import (
    InferenceError,
    apply_holm,
    bootstrap_mean_ci,
    descriptive_summary,
    holm_adjust,
    paired_comparison,
)


def test_descriptive_summary_has_preregistered_fields_and_is_deterministic() -> None:
    first = descriptive_summary([1.0, 2.0, 3.0], denominator={"reports": 9})
    second = descriptive_summary([1.0, 2.0, 3.0], denominator={"reports": 9})

    assert first == second
    assert first["mean"] == 2.0
    assert first["median"] == 2.0
    assert first["standard_deviation"] == 1.0
    assert first["denominator"] == {"reports": 9}
    assert len(first["paired_confidence_interval"]) == 2


def test_paired_comparison_orients_lower_as_positive_improvement_and_keeps_ties() -> None:
    comparison = paired_comparison(
        [1.0, 2.0, 3.0, 4.0],
        [2.0, 2.0, 4.0, 3.0],
        direction="lower",
        denominator={"seeds": 4},
    )

    assert comparison["mean_difference_candidate_minus_comparator"] == -0.25
    assert comparison["mean"] == 0.25
    assert comparison["n_candidate_better"] == 2
    assert comparison["n_comparator_better"] == 1
    assert comparison["n_ties"] == 1
    assert comparison["effect_size"]["orientation"] == (
        "positive means candidate is better"
    )
    assert comparison["holm_adjusted_p_value"] is None


def test_all_ties_are_reported_not_dropped() -> None:
    comparison = paired_comparison(
        [1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0],
        direction="higher",
        denominator=3,
    )
    assert comparison["raw_p_value"] == 1.0
    assert comparison["n_ties"] == 3
    assert comparison["effect_size"]["paired_standardized_mean"] == 0.0


def test_holm_step_down_is_monotone_in_sorted_order() -> None:
    adjusted = holm_adjust({
        "a": 0.01,
        "b": 0.04,
        "c": 0.03,
        "unavailable": None,
    })
    assert adjusted == {
        "a": pytest.approx(0.03),
        "c": pytest.approx(0.06),
        "b": pytest.approx(0.06),
        "unavailable": None,
    }

    rows = apply_holm({
        key: {"raw_p_value": raw, "preserved": key}
        for key, raw in {"a": 0.01, "b": 0.04, "c": 0.03}.items()
    })
    assert rows["a"]["holm_adjusted_p_value"] == pytest.approx(0.03)
    assert rows["b"]["preserved"] == "b"


@pytest.mark.parametrize(
    "values",
    [[], [1.0, math.nan], [1.0, math.inf]],
)
def test_inference_rejects_empty_or_nonfinite_vectors(values) -> None:
    with pytest.raises(InferenceError):
        bootstrap_mean_ci(values)


def test_inference_rejects_unpaired_lengths_and_invalid_direction() -> None:
    with pytest.raises(InferenceError, match="equal paired length"):
        paired_comparison([1.0], [1.0, 2.0], direction="higher", denominator=1)
    with pytest.raises(InferenceError, match="direction"):
        paired_comparison([1.0], [2.0], direction="sideways", denominator=1)
