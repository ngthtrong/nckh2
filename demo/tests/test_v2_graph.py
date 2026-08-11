from datetime import datetime, timezone

import numpy as np

from demo.v2.contracts import ReportV2
from demo.v2.graph import (
    build_dense_product_oracle,
    build_sparse_product_graph,
    sparse_dense_equivalent,
)
from demo.v2.similarity import SimilarityParamsV2, product_similarity


NOW = datetime(2026, 8, 11, tzinfo=timezone.utc)


def _report(report_id: str, **overrides: object) -> ReportV2:
    values: dict[str, object] = {
        "report_id": report_id,
        "L": (16.0, 108.0),
        "T": NOW,
        "F": 0.4,
        "E": 0.8,
        "N": 20,
        "V": 3,
        "source_family": "citizen",
    }
    values.update(overrides)
    return ReportV2(**values)


def test_sparse_spatial_edges_match_dense_oracle_and_route_missing_lt_to_review() -> None:
    reports = [
        _report("near-a"),
        _report("near-b", L=(16.0004, 108.0)),
        _report("far", L=(16.03, 108.0)),
        _report("missing-location", L=None),
        _report("missing-time", T=None),
    ]
    params = SimilarityParamsV2(sigma_geo_m=300, theta=0.5)
    graph = build_sparse_product_graph(reports, params)
    dense = build_dense_product_oracle(reports, params)

    assert graph.review_queue == ("missing-location", "missing-time")
    assert graph.eligible_report_ids == ("near-a", "near-b", "far")
    assert graph.retained_edges == 1
    assert graph.candidate_pairs < graph.total_eligible_pairs
    assert np.allclose(graph.to_dense(), dense, rtol=0.0, atol=1e-12)
    assert sparse_dense_equivalent(reports, params)
    assert not hasattr(graph, "matrix")
    assert np.count_nonzero(dense[3:, :]) == 0
    assert np.count_nonzero(dense[:, 3:]) == 0


def test_strict_threshold_does_not_retain_equal_weight() -> None:
    reports = [_report("a"), _report("b", L=(16.0004, 108.0))]
    base = SimilarityParamsV2(theta=0.0)
    exact_weight = product_similarity(reports[0], reports[1], base)
    graph = build_sparse_product_graph(
        reports,
        SimilarityParamsV2(theta=exact_weight),
    )
    assert graph.retained_edges == 0


def test_zero_threshold_falls_back_to_all_pairs_but_remains_equivalent() -> None:
    reports = [
        _report("a"),
        _report("b", L=(16.01, 108.0)),
        _report("c", L=(16.02, 108.0), F=None, E=None),
    ]
    params = SimilarityParamsV2(theta=0.0)
    graph = build_sparse_product_graph(reports, params)
    assert graph.bound.status == "unbounded"
    assert graph.candidate_pairs == graph.total_eligible_pairs == 3
    assert sparse_dense_equivalent(reports, params)


def test_empty_weight_domain_short_circuits_candidates() -> None:
    reports = [_report("a"), _report("b")]
    params = SimilarityParamsV2(beta=0.0, gamma=0.0, theta=0.0)
    graph = build_sparse_product_graph(reports, params)
    assert graph.bound.status == "empty"
    assert graph.candidate_pairs == 0
    assert graph.edges == ()

