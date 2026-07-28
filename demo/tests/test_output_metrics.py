from __future__ import annotations

import math

import pytest

from demo.pipeline.metrics import (
    MetricInputError,
    ReviewPolicy,
    cluster_quality,
    evaluate_output_burden,
    false_operational_destinations,
    incident_merge_loss,
    incident_split_loss,
    noise_absorption_rate,
    noise_rejection_rate,
    operator_review_burden,
)


# Hand-worked fixture:
# - incident 10 is split across destinations 0 and 1;
# - incident 11 is split across destination 1 and one unresolved report;
# - destination 1 merges incidents 10 and 11 and absorbs one noise report;
# - destination 2 is a false, noise-only destination;
# - the final noise report is explicitly rejected.
PREDICTED = [0, 0, 1, 1, -1, 1, 2, -1]
INCIDENTS = [10, 10, 10, 11, 11, -1, -1, -1]
REVIEW_SCORES = [0.9, 0.8, 0.7, 0.6, 0.5, 0.3, 0.2, 0.4]


def test_hand_worked_split_and_merge_have_exact_denominators() -> None:
    split = incident_split_loss(PREDICTED, INCIDENTS)
    merge = incident_merge_loss(PREDICTED, INCIDENTS)

    assert split["numerator"] == 2
    assert split["denominator"] == 2
    assert split["rate"] == 1.0
    assert split["details"]["excess_output_units"] == 2

    assert merge["numerator"] == 1
    assert merge["denominator"] == 3
    assert merge["rate"] == pytest.approx(1 / 3)
    assert merge["details"]["n_noise_only_destinations"] == 1
    assert merge["details"]["n_unclustered_reports"] == 2


def test_noise_outcomes_form_an_exact_partition() -> None:
    rejection = noise_rejection_rate(PREDICTED, INCIDENTS)
    absorption = noise_absorption_rate(PREDICTED, INCIDENTS)

    assert rejection["numerator"] == 1
    assert rejection["denominator"] == 3
    assert rejection["rate"] == pytest.approx(1 / 3)
    assert absorption["numerator"] == 1
    assert absorption["denominator"] == 3
    assert absorption["rate"] == pytest.approx(1 / 3)

    partition = rejection["details"]
    assert partition["rejected"] == 1
    assert partition["absorbed"] == 1
    assert partition["assigned_to_noise_only_destination"] == 1
    assert (
        partition["rejected"]
        + partition["absorbed"]
        + partition["assigned_to_noise_only_destination"]
        == partition["total"]
    )


def test_false_destination_count_excludes_the_noise_bin() -> None:
    result = false_operational_destinations(PREDICTED, INCIDENTS)

    assert result["count"] == 1
    assert result["numerator"] == 1
    assert result["denominator"] == 3
    assert result["details"]["n_operational_destinations"] == 3
    assert result["details"]["noise_label_is_destination"] is False


def test_review_burden_uses_destinations_and_each_unclustered_report() -> None:
    standard = ReviewPolicy(
        id="standard",
        min_destination_reports=2,
        min_mean_confidence=0.5,
    )
    result = operator_review_burden(
        PREDICTED,
        REVIEW_SCORES,
        standard,
    )

    # Destination 2 is queued; the two -1 reports are two additional items.
    assert result["queue_size"] == 3
    assert result["numerator"] == 3
    assert result["denominator"] == 5
    assert result["rate"] == pytest.approx(3 / 5)
    assert result["details"]["n_reviewed_destinations"] == 1
    assert result["details"]["n_unclustered_report_reviews"] == 2
    assert result["details"]["n_reports_represented_in_review_queue"] == 3
    assert result["details"]["report_denominator"] == 8
    assert result["details"]["report_rate"] == pytest.approx(3 / 8)


def test_multiple_review_policies_are_reported_without_selecting_one() -> None:
    policies = (
        ReviewPolicy("conservative", 3, 0.75),
        ReviewPolicy("standard", 2, 0.5),
        ReviewPolicy("permissive", 1, 0.0),
    )
    result = evaluate_output_burden(
        PREDICTED,
        INCIDENTS,
        REVIEW_SCORES,
        policies,
    )

    assert list(result["operator_review_burden"]) == [
        "conservative",
        "standard",
        "permissive",
    ]
    assert result["operator_review_burden"]["conservative"]["queue_size"] == 5
    assert result["operator_review_burden"]["standard"]["queue_size"] == 3
    assert result["operator_review_burden"]["permissive"]["queue_size"] == 2


def test_review_score_generator_is_materialized_once_for_all_policies() -> None:
    policies = (
        ReviewPolicy("conservative", 3, 0.75),
        ReviewPolicy("standard", 2, 0.5),
    )
    result = evaluate_output_burden(
        PREDICTED,
        INCIDENTS,
        (score for score in REVIEW_SCORES),
        policies,
    )

    assert result["operator_review_burden"]["conservative"]["queue_size"] == 5
    assert result["operator_review_burden"]["standard"]["queue_size"] == 3


def test_every_metric_confirms_complete_point_coverage() -> None:
    result = evaluate_output_burden(
        PREDICTED,
        INCIDENTS,
        REVIEW_SCORES,
        (ReviewPolicy("standard", 2, 0.5),),
    )
    metrics = [
        result["incident_split_loss"],
        result["incident_merge_loss"],
        result["noise_rejection_rate"],
        result["noise_absorption_rate"],
        result["false_operational_destinations"],
        *result["operator_review_burden"].values(),
    ]
    assert result["n_points"] == len(PREDICTED)
    assert result["all_metrics_complete"] is True
    assert result["noise_label_is_destination"] is False
    for metric in metrics:
        assert metric["coverage"]["points_total"] == len(PREDICTED)
        assert metric["coverage"]["points_accounted"] == len(PREDICTED)
        assert metric["coverage"]["point_coverage_rate"] == 1.0
        assert metric["coverage"]["complete"] is True


def test_predicted_noise_reports_are_distinct_unresolved_units_not_a_cluster() -> None:
    predicted = [-1, -1]
    same_incident = [4, 4]
    scores = [0.8, 0.8]

    split = incident_split_loss(predicted, same_incident)
    merge = incident_merge_loss(predicted, same_incident)
    false_destinations = false_operational_destinations(predicted, same_incident)
    review = operator_review_burden(
        predicted,
        scores,
        ReviewPolicy("all-unresolved", 1, 0.0),
    )

    assert split["numerator"] == 1
    assert split["details"]["output_units_per_incident"] == {"integer:4": 2}
    assert merge["denominator"] == 0
    assert merge["rate"] is None
    assert false_destinations["denominator"] == 0
    assert review["queue_size"] == 2
    assert review["denominator"] == 2


def test_noise_label_none_means_every_prediction_is_a_destination() -> None:
    merge = incident_merge_loss(
        [-1, -1],
        [1, 2],
        noise_label=None,
    )
    rejection = noise_rejection_rate(
        [-1, -1],
        [-1, -1],
        noise_label=None,
    )

    assert merge["numerator"] == 1
    assert merge["denominator"] == 1
    assert rejection["numerator"] == 0
    assert rejection["denominator"] == 2


def test_integer_and_string_labels_remain_distinct_in_json_details() -> None:
    result = incident_split_loss([0, 1], [1, "1"])
    assert result["denominator"] == 2
    assert result["details"]["output_units_per_incident"] == {
        "integer:1": 1,
        "string:1": 1,
    }


def test_zero_population_reports_none_rate_and_explicit_zero_denominator() -> None:
    rejection = noise_rejection_rate([0, 0], [1, 1])
    assert rejection["numerator"] == 0
    assert rejection["denominator"] == 0
    assert rejection["rate"] is None
    assert rejection["coverage"]["points_accounted"] == 2


@pytest.mark.parametrize(
    ("call", "match"),
    [
        (lambda: incident_split_loss([0], [1, 2]), "equal length"),
        (lambda: incident_merge_loss([True], [1]), "integer label"),
        (
            lambda: operator_review_burden(
                [0],
                [math.nan],
                ReviewPolicy("p", 1, 0.0),
            ),
            r"in \[0, 1\]",
        ),
        (
            lambda: evaluate_output_burden(
                [0],
                [1],
                [0.5],
                (ReviewPolicy("same", 1, 0.0), ReviewPolicy("same", 2, 0.5)),
            ),
            "unique",
        ),
    ],
)
def test_strict_api_rejects_misaligned_or_ambiguous_inputs(call, match: str) -> None:
    with pytest.raises(MetricInputError, match=match):
        call()


@pytest.mark.parametrize(
    "policy",
    [
        lambda: ReviewPolicy("", 1, 0.5),
        lambda: ReviewPolicy("bad-count", 0, 0.5),
        lambda: ReviewPolicy("bad-threshold", 1, 1.01),
        lambda: ReviewPolicy("bad-bool-count", True, 0.5),
    ],
)
def test_review_policy_validation_is_strict(policy) -> None:
    with pytest.raises(MetricInputError):
        policy()


def test_legacy_cluster_quality_no_longer_silently_truncates() -> None:
    with pytest.raises(MetricInputError, match="equal length"):
        cluster_quality([0], [0, 1])
