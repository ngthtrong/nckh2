from __future__ import annotations

import pytest

from demo.v2.statistics import (
    StatisticalContractError,
    assert_complete_coverage,
    holm_adjust,
    paired_bootstrap_mean_ci,
    paired_comparison,
    paired_comparison_by_key,
    perturbation_drift,
    ranking_metrics,
)


def test_paired_bootstrap_is_deterministic_and_uses_requested_resamples() -> None:
    first = paired_bootstrap_mean_ci([1.0, 2.0, 3.0], resamples=10_000, seed=9)
    second = paired_bootstrap_mean_ci([1.0, 2.0, 3.0], resamples=10_000, seed=9)
    assert first == second
    assert first[0] <= 2.0 <= first[1]


def test_paired_comparison_keeps_ties_and_explicit_denominator() -> None:
    row = paired_comparison(
        [2.0, 1.0, 3.0],
        [1.0, 1.0, 4.0],
        direction="higher",
        denominator={"unit": "master seed", "n": 3},
    )
    assert row["n_candidate_better"] == 1
    assert row["n_comparator_better"] == 1
    assert row["n_ties"] == 1
    assert row["denominator"]["n"] == 3
    assert "median_improvement" in row


def test_keyed_comparison_rejects_mispairing() -> None:
    with pytest.raises(StatisticalContractError, match="pairing keys"):
        paired_comparison_by_key(
            {1: 0.5, 2: 0.7},
            {1: 0.4, 3: 0.6},
            direction="higher",
            denominator={"unit": "master seed", "n": 2},
        )
    row = paired_comparison_by_key(
        {2: 0.7, 1: 0.5},
        {1: 0.4, 2: 0.6},
        direction="higher",
        denominator={"unit": "master seed", "n": 2},
    )
    assert row["pairing_key"] == "master_seed"
    assert row["pairing_key_count"] == 2


def test_holm_is_monotone_in_sorted_raw_p_values() -> None:
    base = {
        "a": {"raw_p_value": 0.01},
        "b": {"raw_p_value": 0.04},
        "c": {"raw_p_value": 0.03},
    }
    adjusted = holm_adjust(base)
    ordered = sorted(base, key=lambda item: base[item]["raw_p_value"])
    values = [adjusted[item]["holm_adjusted_p_value"] for item in ordered]
    assert values == sorted(values)


def test_ranking_metrics_reward_the_ideal_order() -> None:
    benefit = {"a": 1.0, "b": 0.8, "c": 0.1}
    perfect = ranking_metrics(benefit, benefit, k=2)
    reversed_scores = {"a": 0.1, "b": 0.8, "c": 1.0}
    reversed_result = ranking_metrics(reversed_scores, benefit, k=2)
    assert perfect["ndcg_at_k"] == pytest.approx(1.0)
    assert perfect["top_k_recall"] == pytest.approx(1.0)
    assert perfect["rank_regret"] == pytest.approx(0.0)
    assert reversed_result["ndcg_at_k"] < perfect["ndcg_at_k"]
    assert reversed_result["rank_regret"] > 0.0


def test_ndcg_is_invariant_to_positive_benefit_unit_rescaling() -> None:
    predicted = {"a": 0.2, "b": 0.9, "c": 0.4}
    benefit = {"a": 1.0, "b": 0.3, "c": 0.6}
    scaled = {key: 100.0 * value for key, value in benefit.items()}
    assert ranking_metrics(predicted, benefit, k=3)["ndcg_at_k"] == pytest.approx(
        ranking_metrics(predicted, scaled, k=3)["ndcg_at_k"]
    )


def test_perturbation_drift_separates_rank_from_score_change() -> None:
    original = {"a": 0.9, "b": 0.5, "c": 0.1}
    shifted = {"a": 0.8, "b": 0.4, "c": 0.0}
    drift = perturbation_drift(original, shifted, k=2)
    assert drift["mean_normalized_rank_drift"] == 0.0
    assert drift["top_k_set_drift"] == 0.0
    assert drift["max_absolute_score_drift"] == pytest.approx(0.1)


def test_coverage_audit_rejects_missing_rows() -> None:
    rows = [
        {"method": "product", "seed": 1, "regime": "id"},
        {"method": "product", "seed": 1, "regime": "ood"},
    ]
    with pytest.raises(StatisticalContractError, match="coverage mismatch"):
        assert_complete_coverage(
            rows,
            methods=["product", "additive"],
            seeds=[1],
        )
