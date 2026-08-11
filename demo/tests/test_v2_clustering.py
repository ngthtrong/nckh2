from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random

import pytest
from sklearn.metrics import adjusted_rand_score

from demo.v2.clustering import (
    CANDIDATE_POOL_RULE_V2,
    ClusterRunV2,
    GraphConfigV2,
    _spatial_candidate_pairs,
    candidate_pool_neighbor_count_v2,
    clustering_endpoints,
    run_graph_clustering,
    run_hdbscan_v2,
    run_st_dbscan_v2,
)
from demo.v2.contracts import ReportV2, TruthV2
from demo.v2.generator import generate_dataset, observation_snapshot


def _data() -> tuple[list[ReportV2], list[TruthV2]]:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    reports = [
        ReportV2("a1", (16.0, 108.0), base, 0.9, 0.9, 10, 2),
        ReportV2("a2", (16.0001, 108.0001), base + timedelta(minutes=2), 0.9, 0.8, 9, 2),
        ReportV2("b1", (16.1, 108.1), base, 0.2, 0.2, 3, 0),
        ReportV2("b2", (16.1001, 108.1001), base + timedelta(minutes=2), 0.2, 0.3, 4, 0),
        ReportV2("noise", (16.5, 108.5), base + timedelta(hours=6), 0.5, 0.5, 1, 0),
        ReportV2("review", None, base, 0.5, 0.5, 1, 0),
    ]
    truth = [
        TruthV2("a1", "a", 0), TruthV2("a2", "a", 0),
        TruthV2("b1", "b", 1), TruthV2("b2", "b", 1),
        TruthV2("noise", is_noise=True), TruthV2("review", "a", 0),
    ]
    return reports, truth


def test_graph_run_keeps_missing_lt_in_review_queue() -> None:
    reports, truth = _data()
    config = GraphConfigV2("product", 700, 60, 0.85, 8, 1.2)
    run = run_graph_clustering(reports, config)
    assert "review" in run.review_report_ids
    assert run.labels[-1] == -1
    metrics = clustering_endpoints(reports, truth, run)
    assert metrics["n_reports"] == len(reports)
    assert metrics["n_linked_reports"] == 5


def test_product_and_additive_share_candidate_universe() -> None:
    reports, _ = _data()
    product = run_graph_clustering(reports, GraphConfigV2("product", 700, 60, 0.85, 8, 1.2))
    additive = run_graph_clustering(reports, GraphConfigV2("additive", 700, 60, 0.85, 8, 1.2))
    assert product.candidate_pairs == additive.candidate_pairs


def test_graph_partition_is_invariant_to_report_input_order() -> None:
    reports, _ = _data()
    config = GraphConfigV2("product", 700, 60, 0.85, 8, 1.2)
    forward = run_graph_clustering(reports, config, random_state=77)
    reversed_reports = list(reversed(reports))
    backward = run_graph_clustering(reversed_reports, config, random_state=77)
    forward_map = {report.report_id: label for report, label in zip(reports, forward.labels, strict=True)}
    backward_map = {
        report.report_id: label
        for report, label in zip(reversed_reports, backward.labels, strict=True)
    }
    assert forward_map == backward_map


def test_candidate_pool_rule_is_frozen_and_machine_disclosed() -> None:
    assert CANDIDATE_POOL_RULE_V2 == (
        "per eligible report retain min(n-1,max(64,4*k)) spatial neighbors; "
        "query every BallTree distance tie at the boundary, canonical-sort by "
        "(distance_rad,report_id), truncate to the declared count, then union "
        "the directed neighborhoods into undirected candidate pairs"
    )
    assert candidate_pool_neighbor_count_v2(n_eligible=80, graph_k=8) == 64
    assert candidate_pool_neighbor_count_v2(n_eligible=20, graph_k=8) == 19


def test_eighty_colocated_reports_have_permutation_invariant_candidate_pool() -> None:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    reports = [
        ReportV2(
            f"co-{index:03d}",
            L=(16.0, 108.0),
            T=base + timedelta(minutes=3 * (index % 7)),
            F=0.15 + 0.70 * ((index // 20) % 2),
            E=0.20 + 0.60 * ((index // 10) % 2),
            N=5 + index,
            V=index % 9,
        )
        for index in range(80)
    ]
    neighbor_count = candidate_pool_neighbor_count_v2(
        n_eligible=len(reports),
        graph_k=8,
    )

    def candidate_ids(rows: list[ReportV2]) -> frozenset[tuple[str, str]]:
        pairs = _spatial_candidate_pairs(
            rows,
            list(range(len(rows))),
            neighbor_count,
        )
        return frozenset(
            tuple(sorted((rows[left].report_id, rows[right].report_id)))
            for left, right in pairs
        )

    identifiers = sorted(report.report_id for report in reports)
    expected: set[tuple[str, str]] = set()
    for identifier in identifiers:
        nearest = [other for other in identifiers if other != identifier][
            :neighbor_count
        ]
        expected.update(tuple(sorted((identifier, other))) for other in nearest)

    reference_pool = candidate_ids(reports)
    assert reference_pool == frozenset(expected)
    config = GraphConfigV2("product", 700, 60, 0.60, 8, 1.2)
    reference_run = run_graph_clustering(reports, config, random_state=77)
    reference_labels = {
        report.report_id: label
        for report, label in zip(reports, reference_run.labels, strict=True)
    }
    permutations = [list(reversed(reports))]
    for seed in (5, 17, 91):
        shuffled = list(reports)
        random.Random(seed).shuffle(shuffled)
        permutations.append(shuffled)

    for permuted in permutations:
        assert candidate_ids(permuted) == reference_pool
        run = run_graph_clustering(permuted, config, random_state=77)
        labels = {
            report.report_id: label
            for report, label in zip(permuted, run.labels, strict=True)
        }
        assert labels == reference_labels
        assert run.candidate_pairs == reference_run.candidate_pairs
        assert run.retained_edges == reference_run.retained_edges


def test_development_ood_snapshot_candidate_search_is_complete() -> None:
    """Regression for a BallTree radius-rounding failure found pre-freeze."""

    dataset = observation_snapshot(generate_dataset(4100, "ood"))
    run = run_graph_clustering(
        dataset.reports,
        GraphConfigV2("product", 500, 30, 0.85, 8, 0.8),
        random_state=4100,
    )
    assert len(run.labels) == len(dataset.reports)
    assert run.candidate_pairs > 0


def test_direct_baselines_return_complete_label_vectors() -> None:
    reports, _ = _data()
    st = run_st_dbscan_v2(reports, spatial_eps_m=500, temporal_eps_min=30, min_samples=3)
    hdb = run_hdbscan_v2(reports, min_cluster_size=3, min_samples=1, spatial_scale_m=500, temporal_scale_min=30)
    assert len(st.labels) == len(reports)
    assert len(hdb.labels) == len(reports)
    assert st.labels[-1] == hdb.labels[-1] == -1


def test_unresolved_linked_reports_are_distinct_ari_units() -> None:
    reports, truth = _data()
    run = ClusterRunV2(
        "test",
        (0, 0, -1, -1, -1, -1),
        ("b1", "b2", "noise", "review"),
        None,
        0,
        0,
    )
    metrics = clustering_endpoints(reports, truth, run)
    expected = adjusted_rand_score(
        [0, 0, 1, 1, 0],
        [0, 0, -(1_000_000 + 2), -(1_000_000 + 3), -(1_000_000 + 5)],
    )
    assert metrics["ari_linked"] == pytest.approx(expected)
