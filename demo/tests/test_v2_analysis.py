from __future__ import annotations

import copy
import hashlib
from typing import Any

import pytest

from demo.v2.analysis import (
    ConfirmationAnalysisError,
    ConfirmationAnalysisSpec,
    analyze_confirmation_payload,
    validate_confirmation_payload,
)


SPEC = ConfirmationAnalysisSpec(seeds=(11, 4, 27), expected_seed_count=3)


def _payload(spec: ConfirmationAnalysisSpec = SPEC) -> dict[str, Any]:
    clustering_rows: list[dict[str, Any]] = []
    priority_rows: list[dict[str, Any]] = []
    priority_stress_rows: list[dict[str, Any]] = []
    predicted_dispatch_rows: list[dict[str, Any]] = []
    schedule_hashes: list[dict[str, Any]] = []

    method_ari = {
        "method.product_louvain": 0.90,
        "method.additive_louvain": 0.70,
        "method.st_dbscan": 0.60,
        "method.hdbscan_geo_time": 0.65,
    }
    method_false = {
        "method.product_louvain": 1,
        "method.additive_louvain": 3,
        "method.st_dbscan": 4,
        "method.hdbscan_geo_time": 5,
    }
    for method in spec.methods:
        for seed in spec.seeds:
            for regime in spec.regimes:
                ari = method_ari[method] + seed / 100_000
                # Deliberately retain an adverse OOD product result.
                if method == spec.product_method and regime == "ood":
                    ari = 0.50 + seed / 100_000
                n_false = method_false[method]
                clustering_rows.append(
                    {
                        "method": method,
                        "seed": seed,
                        "regime": regime,
                        "metrics": {
                            "ari_linked": ari,
                            "false_destinations_per_100_reports": float(n_false),
                            "split_loss": 0.1,
                            "merge_loss": 0.1,
                            "noise_rejection": 0.8,
                            "review_items_per_100_reports": 5.0,
                            "max_diameter_m": 800.0,
                            "singleton_rate": 0.1,
                            "n_reports": 100,
                            "n_false_destinations": n_false,
                            "n_review_items": 5,
                            "n_incidents_with_reports": 10,
                            "n_split_incidents": 1,
                            "n_linked_destinations": 10,
                            "n_merged_linked_destinations": 1,
                            "n_noise_reports": 10,
                            "n_noise_rejected": 8,
                        },
                    }
                )

    priority_base = {
        "revised": 0.90,
        "legacy": 0.70,
        "urgency_only": 0.60,
        "population_only": 0.58,
        "simple_linear": 0.75,
        "random": 0.35,
    }
    for policy in spec.priority_policies:
        for seed in spec.seeds:
            for regime in spec.regimes:
                priority_rows.append(
                    {
                        "policy": policy,
                        "seed": seed,
                        "regime": regime,
                        "evaluation_partition": "predicted_clusters_one_to_one_max_overlap",
                        "metrics": {
                            "ndcg_at_k": priority_base[policy] + seed / 1_000_000,
                            "kendall_tau_b": 0.5,
                            "top_k_recall": 0.8,
                            "rank_regret": 0.2,
                            "k": 5,
                            "n_ranking_units": 10,
                            "denominator": {
                                "ranking_units": "predicted clusters",
                                "n_ranking_units": 10,
                            },
                        },
                    }
                )

    campaign = "coordinated_high_confidence_campaign"
    for family in spec.stress_families:
        for policy in spec.priority_policies:
            for seed in spec.seeds:
                for regime in spec.regimes:
                    revised = policy == spec.revised_policy
                    base_drift = 0.0 if family == "exact_duplicate" and revised else (
                        0.04 if revised else 0.20
                    )
                    priority_stress_rows.append(
                        {
                            "family": family,
                            "policy": policy,
                            "seed": seed,
                            "regime": regime,
                            "target_selection": "observable_minimum_membership_hash",
                            "drift": {
                                "mean_normalized_rank_drift": base_drift,
                                "top_k_set_drift": base_drift,
                                "max_absolute_score_drift": base_drift,
                            },
                            "false_priority_lift": {
                                "applicable": family == campaign,
                                "normalized_score_change": (
                                    0.10 if revised else 0.40
                                )
                                if family == campaign
                                else 0.0,
                            },
                        }
                    )

    scenario_harm = {"lean": 5.0, "nominal": 10.0, "surge": 20.0}
    for seed in spec.seeds:
        for regime in spec.regimes:
            for scenario in spec.scenarios:
                for policy in spec.dispatch_policies:
                    revised = policy == spec.revised_policy
                    missed = 2 if revised else 4
                    predicted_dispatch_rows.append(
                        {
                            "seed": seed,
                            "regime": regime,
                            "scenario": scenario,
                            "policy": policy,
                            "partition": "predicted_product_clusters",
                            "metrics": {
                                "total_harm": (
                                    50.0 if revised else 80.0
                                )
                                + scenario_harm[scenario]
                                + seed / 1000,
                                "missed_deadlines": missed,
                                "deadline_miss_rate": missed / 20,
                                "n_incidents": 20,
                                "unreached_incidents": 1,
                                "false_trips": 2,
                                "duplicate_trips": 1,
                                "max_response_min": 120.0,
                                "cvar90_response_min": 110.0,
                                "workload_cv": 0.2,
                            },
                        }
                    )
                    key = f"{seed}|{regime}|{scenario}|{policy}".encode()
                    schedule_hashes.append(
                        {
                            "seed": seed,
                            "regime": regime,
                            "scenario": scenario,
                            "policy": policy,
                            "hash": hashlib.sha256(key).hexdigest(),
                        }
                    )
    return {
        "schema_version": "v2.confirmation-result.1",
        "confirmation_master_seeds": list(spec.seeds),
        "clustering_rows": clustering_rows,
        "priority_rows": priority_rows,
        "priority_stress_rows": priority_stress_rows,
        "predicted_dispatch_rows": predicted_dispatch_rows,
        "schedule_hashes": schedule_hashes,
        "adverse_results_retained": True,
        "priority_scoring_uses_truth": False,
        "truth_used_by_scheduler": False,
    }


@pytest.fixture(scope="module")
def confirmation_result() -> dict[str, Any]:
    return analyze_confirmation_payload(_payload(), SPEC)


def test_exact_coverage_and_complete_inferential_summary(
    confirmation_result: dict[str, Any],
) -> None:
    counts = confirmation_result["coverage"]["expected_and_observed_counts"]
    assert counts == {
        "clustering_rows": 4 * 3 * 2,
        "priority_rows": 6 * 3 * 2,
        "priority_stress_rows": 10 * 6 * 3 * 2,
        "predicted_dispatch_rows": 7 * 3 * 3 * 2,
        "schedule_hashes": 7 * 3 * 3 * 2,
    }
    comparisons = confirmation_result["comparisons"]
    assert len(comparisons["clustering"]) == 4
    assert len(comparisons["priority"]) == 10
    assert len(comparisons["dispatch"]) == 24
    assert len(comparisons["stress"]) == 210
    for section in comparisons.values():
        for row in section.values():
            assert row["n_seed_pairs"] == 3
            assert row["pairing_key"] == "master_seed"
            assert row["holm_adjusted_p_value"] is not None
            assert row["denominator"]["n_master_seeds"] == 3
    assert confirmation_result["analysis_contract"][
        "adverse_and_null_results_retained"
    ] is True


def test_adverse_ood_result_is_retained_and_blocks_superiority(
    confirmation_result: dict[str, Any],
) -> None:
    row = confirmation_result["comparisons"]["clustering"][
        "clustering.ood.ari_linked.product_vs_additive"
    ]
    assert row["mean_improvement"] < 0.0
    assert row["adverse_or_null"] is True
    gate = confirmation_result["claim_gates"]["claim.synthetic_controlled_clustering"]
    assert gate["status"] == "blocked"
    assert gate["conditions"]["ood_ari_not_reversed"] is False
    assert confirmation_result["claim_gates"]["claim.real_incident_clustering_accuracy"]["status"] == "blocked"
    assert confirmation_result["claim_gates"]["claim.real_dispatch_benefit"]["status"] == "blocked"
    assert set(confirmation_result["claim_gates"]) == {
        "claim.synthetic_controlled_clustering",
        "claim.synthetic_duplicate_invariance",
        "claim.synthetic_priority_alignment",
        "claim.external_priority_sanity",
        "claim.external_consolidation_sanity",
        "claim.external_location_sanity",
        "claim.external_flood_context_descriptive",
        "claim.real_incident_clustering_accuracy",
        "claim.real_dispatch_benefit",
        "claim.vietnamese_transfer",
    }


def test_dispatch_comparison_averages_scenarios_within_seed(
    confirmation_result: dict[str, Any],
) -> None:
    row = confirmation_result["comparisons"]["dispatch"][
        "dispatch.id.total_harm.revised_vs_legacy"
    ]
    assert row["mean_improvement"] == pytest.approx(30.0)
    assert row["denominator"]["scenario_aggregation"] == (
        "unweighted_mean_of_locked_scenarios"
    )
    assert row["denominator"]["n_scenarios_per_seed"] == 3


def test_row_order_cannot_change_seed_keyed_inference(
    confirmation_result: dict[str, Any],
) -> None:
    reversed_payload = _payload()
    for table in (
        "clustering_rows",
        "priority_rows",
        "priority_stress_rows",
        "predicted_dispatch_rows",
        "schedule_hashes",
    ):
        reversed_payload[table].reverse()
    reversed_result = analyze_confirmation_payload(reversed_payload, SPEC)
    assert reversed_result["comparisons"] == confirmation_result["comparisons"]


@pytest.mark.parametrize(
    ("table", "extra_field", "extra_value"),
    [
        ("clustering_rows", "method", "method.not_locked"),
        ("priority_rows", "policy", "not_locked"),
        ("priority_stress_rows", "family", "not_locked"),
        ("predicted_dispatch_rows", "scenario", "not_locked"),
        ("schedule_hashes", "scenario", "not_locked"),
    ],
)
@pytest.mark.parametrize("mutation", ["duplicate", "missing", "extra"])
def test_every_table_rejects_duplicate_missing_and_extra_composite_keys(
    table: str,
    extra_field: str,
    extra_value: str,
    mutation: str,
) -> None:
    payload = _payload()
    if mutation == "duplicate":
        payload[table].append(copy.deepcopy(payload[table][0]))
    elif mutation == "missing":
        payload[table].pop()
    else:
        extra = copy.deepcopy(payload[table][0])
        extra[extra_field] = extra_value
        payload[table].append(extra)
    with pytest.raises(ConfirmationAnalysisError):
        validate_confirmation_payload(payload, SPEC)


def test_oracle_priority_and_oracle_dispatch_are_rejected() -> None:
    priority_payload = _payload()
    priority_payload["priority_rows"][0]["evaluation_partition"] = (
        "oracle_incident_groups_for_construct_only"
    )
    with pytest.raises(ConfirmationAnalysisError, match="predicted-cluster"):
        validate_confirmation_payload(priority_payload, SPEC)

    dispatch_payload = _payload()
    dispatch_payload["predicted_dispatch_rows"][0]["partition"] = (
        "oracle_incident_grouping_upper_bound_only"
    )
    with pytest.raises(ConfirmationAnalysisError, match="oracle"):
        validate_confirmation_payload(dispatch_payload, SPEC)


def test_metric_denominator_and_nonfinite_values_fail_closed() -> None:
    clustering_payload = _payload()
    clustering_payload["clustering_rows"][0]["metrics"][
        "false_destinations_per_100_reports"
    ] = 99.0
    with pytest.raises(ConfirmationAnalysisError, match="denominator"):
        validate_confirmation_payload(clustering_payload, SPEC)

    priority_payload = _payload()
    priority_payload["priority_rows"][0]["metrics"]["ndcg_at_k"] = float("nan")
    with pytest.raises(ConfirmationAnalysisError, match="finite"):
        validate_confirmation_payload(priority_payload, SPEC)

    dispatch_payload = _payload()
    dispatch_payload["predicted_dispatch_rows"][0]["metrics"][
        "deadline_miss_rate"
    ] = 0.9
    with pytest.raises(ConfirmationAnalysisError, match="disagrees"):
        validate_confirmation_payload(dispatch_payload, SPEC)


def test_cross_row_denominators_cannot_mix_datasets() -> None:
    clustering_payload = _payload()
    clustering_payload["clustering_rows"][0]["metrics"]["n_reports"] = 200
    clustering_payload["clustering_rows"][0]["metrics"][
        "false_destinations_per_100_reports"
    ] = 0.5
    clustering_payload["clustering_rows"][0]["metrics"][
        "review_items_per_100_reports"
    ] = 2.5
    with pytest.raises(ConfirmationAnalysisError, match="report denominator"):
        validate_confirmation_payload(clustering_payload, SPEC)

    priority_payload = _payload()
    priority_payload["priority_rows"][0]["metrics"]["n_ranking_units"] = 9
    priority_payload["priority_rows"][0]["metrics"]["denominator"][
        "n_ranking_units"
    ] = 9
    with pytest.raises(ConfirmationAnalysisError, match="predicted-unit denominator"):
        validate_confirmation_payload(priority_payload, SPEC)

    dispatch_payload = _payload()
    dispatch_payload["predicted_dispatch_rows"][0]["metrics"]["n_incidents"] = 10
    dispatch_payload["predicted_dispatch_rows"][0]["metrics"]["missed_deadlines"] = 1
    with pytest.raises(ConfirmationAnalysisError, match="incident denominator"):
        validate_confirmation_payload(dispatch_payload, SPEC)


def test_stress_contract_is_observable_only_and_campaign_only() -> None:
    target_payload = _payload()
    target_payload["priority_stress_rows"][0]["target_selection"] = "truth_max_gain"
    with pytest.raises(ConfirmationAnalysisError, match="observable-only"):
        validate_confirmation_payload(target_payload, SPEC)

    applicability_payload = _payload()
    noncampaign = next(
        row
        for row in applicability_payload["priority_stress_rows"]
        if row["family"] != "coordinated_high_confidence_campaign"
    )
    noncampaign["false_priority_lift"]["applicable"] = True
    with pytest.raises(ConfirmationAnalysisError, match="campaign-only"):
        validate_confirmation_payload(applicability_payload, SPEC)


def test_schedule_hash_contract_rejects_invalid_or_ambiguous_digest() -> None:
    invalid_payload = _payload()
    invalid_payload["schedule_hashes"][0]["hash"] = "not-a-sha256"
    with pytest.raises(ConfirmationAnalysisError, match="SHA-256"):
        validate_confirmation_payload(invalid_payload, SPEC)

    ambiguous_payload = _payload()
    ambiguous_payload["schedule_hashes"][0]["schedule_hash"] = (
        ambiguous_payload["schedule_hashes"][0]["hash"]
    )
    with pytest.raises(ConfirmationAnalysisError, match="exactly one"):
        validate_confirmation_payload(ambiguous_payload, SPEC)


def test_spec_accepts_custom_expected_seed_ids_but_keeps_locked_axes() -> None:
    small = ConfirmationAnalysisSpec(seeds=(101, 202), expected_seed_count=2)
    validated = validate_confirmation_payload(_payload(small), small)
    assert validated.coverage["master_seed_count"] == 2
    with pytest.raises(ConfirmationAnalysisError, match="exactly 4"):
        ConfirmationAnalysisSpec(
            seeds=(1,), expected_seed_count=1, methods=("a", "b", "c")
        )
    with pytest.raises(ConfirmationAnalysisError, match="exactly 40"):
        ConfirmationAnalysisSpec(seeds=(1,))
