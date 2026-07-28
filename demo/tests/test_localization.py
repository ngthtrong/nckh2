from __future__ import annotations

import json
import math
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from demo.data.generate import event_to_dict
from demo.experiments.exp14_localization_bounds import analyze_candidate, run
from demo.pipeline.attributes import Event, haversine_m
from demo.pipeline.config import WeightParams
from demo.pipeline.weighting import (
    additive_distance_bound,
    edge_weight_additive,
    edge_weight_gating,
    implied_distance_cutoff,
    product_distance_bound,
    sparsify,
)


def _event(
    event_id: str,
    *,
    lat: float = 16.0,
    lng: float = 108.0,
    minute: float = 0.0,
    flood: float = 0.5,
    urgency: float = 0.5,
) -> Event:
    return Event(
        event_id=event_id,
        lat=lat,
        lng=lng,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
        + timedelta(minutes=minute),
        flood=flood,
        urgency=urgency,
        n_trapped=1,
        vulnerability=0.0,
        has_image=True,
        gt_cluster=0,
    )


def _write_candidate(tmp_path, events: list[Event], seed: int = 7):
    path = tmp_path / "candidate.json"
    path.write_text(
        json.dumps({
            "meta": {"seed": seed},
            "events": [event_to_dict(event) for event in events],
        }),
        encoding="utf-8",
    )
    return path


def test_product_bound_uses_general_beta_gamma_sum() -> None:
    params = WeightParams(
        sigma_geo_m=700.0, beta=0.2, gamma=0.3, knn=0
    )
    bound = product_distance_bound(params, theta=0.1)

    assert bound.status == "finite"
    assert bound.domain_eligible
    assert bound.beta_gamma_sum == pytest.approx(0.5)
    assert bound.radius_m == pytest.approx(
        700.0 * math.sqrt(2.0 * math.log(0.5 / 0.1))
    )
    assert implied_distance_cutoff(params, 0.1) == pytest.approx(bound.radius_m)


@pytest.mark.parametrize(
    ("theta", "expected"),
    [
        (-0.1, "unbounded"),
        (0.0, "unbounded"),
        (0.49, "finite"),
        (0.5, "empty"),
        (0.8, "empty"),
    ],
)
def test_product_bound_classifies_threshold_boundaries(
    theta: float, expected: str
) -> None:
    params = WeightParams(beta=0.2, gamma=0.3)
    assert product_distance_bound(params, theta).status == expected


def test_product_zero_sum_and_legacy_wrapper_do_not_conflate_domains() -> None:
    zero = WeightParams(beta=0.0, gamma=0.0)
    assert product_distance_bound(zero, -0.1).status == "unbounded"
    assert product_distance_bound(zero, 0.0).status == "empty"
    assert product_distance_bound(zero, 1.0).status == "empty"

    params = WeightParams(beta=0.2, gamma=0.3)
    with pytest.raises(ValueError, match="miền product hữu hạn"):
        implied_distance_cutoff(params, 0.0)
    with pytest.raises(ValueError, match="miền product hữu hạn"):
        implied_distance_cutoff(params, 0.5)


@pytest.mark.parametrize(
    ("theta", "expected"),
    [
        (-0.1, "unbounded"),
        (0.0, "unbounded"),
        (0.49, "unbounded"),
        (0.5, "unbounded"),
        (0.6, "finite"),
        (0.9, "empty"),
        (1.2, "empty"),
    ],
)
def test_additive_bound_classifies_threshold_regions(
    theta: float, expected: str
) -> None:
    params = WeightParams(beta=0.2, gamma=0.3, alpha=0.4)
    assert additive_distance_bound(params, theta).status == expected


def test_additive_bound_handles_degenerate_boundaries() -> None:
    no_geo = WeightParams(beta=0.2, gamma=0.3, alpha=0.0)
    assert additive_distance_bound(no_geo, 0.49).status == "unbounded"
    assert additive_distance_bound(no_geo, 0.5).status == "empty"

    identically_zero = WeightParams(beta=0.0, gamma=0.0, alpha=0.0)
    assert additive_distance_bound(identically_zero, 0.0).status == "empty"


def test_additive_finite_radius_uses_theta_minus_non_geographic_max() -> None:
    params = WeightParams(
        sigma_geo_m=600.0, beta=0.2, gamma=0.3, alpha=0.4
    )
    bound = additive_distance_bound(params, theta=0.6)
    assert bound.status == "finite"
    assert bound.radius_m == pytest.approx(
        600.0 * math.sqrt(2.0 * math.log(0.4 / (0.6 - 0.5)))
    )


@pytest.mark.parametrize(
    "params",
    [
        WeightParams(sigma_geo_m=0.0),
        WeightParams(tau_temp_min=0.0),
        WeightParams(tau_temp_min=-10.0),
        WeightParams(tau_f=0.0),
        WeightParams(tau_e=float("inf")),
        WeightParams(beta=-0.1),
        WeightParams(gamma=-0.1),
    ],
)
def test_bound_api_rejects_parameters_outside_assumptions(
    params: WeightParams,
) -> None:
    with pytest.raises(ValueError):
        product_distance_bound(params, 0.1)

    with pytest.raises(ValueError):
        additive_distance_bound(replace(params, alpha=0.5), 0.6)


def test_additive_bound_rejects_negative_alpha() -> None:
    with pytest.raises(ValueError, match="alpha"):
        additive_distance_bound(WeightParams(), 0.5, alpha=-0.1)


def test_bound_api_rejects_non_finite_inputs_and_float_sum_overflow() -> None:
    with pytest.raises(ValueError, match="theta"):
        product_distance_bound(WeightParams(), float("nan"))
    with pytest.raises(ValueError, match=r"beta \+ gamma"):
        product_distance_bound(
            WeightParams(beta=1e308, gamma=1e308), theta=0.1
        )


def test_sparsify_removes_weight_equal_to_threshold() -> None:
    params = WeightParams(edge_threshold=0.5, knn=0)
    weights = np.array([
        [0.0, 0.5, 0.5000001],
        [0.5, 0.0, 0.9],
        [0.5000001, 0.9, 0.0],
    ])

    sparse = sparsify(weights, params)

    assert sparse[0, 1] == 0.0
    assert sparse[1, 0] == 0.0
    assert sparse[0, 2] == pytest.approx(0.5000001)
    assert sparse[1, 2] == pytest.approx(0.9)


def test_sparsify_refuses_negative_threshold_zero_edge_ambiguity() -> None:
    with pytest.raises(ValueError, match="edge_threshold"):
        sparsify(np.zeros((2, 2)), WeightParams(edge_threshold=-0.1, knn=0))


def test_product_bound_is_stable_near_upper_and_extreme_ratio() -> None:
    b_sum = 1e10
    near = math.nextafter(b_sum, 0.0)
    near_bound = product_distance_bound(
        WeightParams(sigma_geo_m=1000.0, beta=b_sum, gamma=0.0),
        near,
    )
    assert near_bound.status == "finite"
    assert near_bound.radius_m is not None
    assert near_bound.radius_m > 0.0

    extreme_bound = product_distance_bound(
        WeightParams(sigma_geo_m=700.0, beta=1e308, gamma=0.0),
        math.ulp(0.0),
    )
    assert extreme_bound.status == "finite"
    assert extreme_bound.radius_m is not None
    assert math.isfinite(extreme_bound.radius_m)


def test_additive_bound_is_stable_next_to_upper_boundary() -> None:
    scale = 1e100
    total = scale + scale
    theta = math.nextafter(total, scale)
    bound = additive_distance_bound(
        WeightParams(
            sigma_geo_m=1000.0,
            beta=scale,
            gamma=0.0,
            alpha=scale,
        ),
        theta,
    )
    assert bound.status == "finite"
    assert bound.radius_m is not None
    assert bound.radius_m > 0.0


def test_random_bounded_attributes_obey_product_edge_bound() -> None:
    rng = np.random.default_rng(20260728)
    n_retained = 0
    for index in range(300):
        beta = float(rng.uniform(0.01, 1.2))
        gamma = float(rng.uniform(0.01, 1.2))
        b_sum = beta + gamma
        theta = float(b_sum * rng.uniform(0.05, 0.8))
        params = WeightParams(
            sigma_geo_m=float(rng.uniform(300.0, 1500.0)),
            tau_temp_min=float(rng.uniform(10.0, 180.0)),
            tau_f=float(rng.uniform(0.1, 1.0)),
            tau_e=float(rng.uniform(0.1, 1.0)),
            beta=beta,
            gamma=gamma,
            edge_threshold=theta,
            knn=0,
        )
        a = _event(
            f"a{index}",
            flood=float(rng.uniform(0.0, 1.0)),
            urgency=float(rng.uniform(0.0, 1.0)),
        )
        b = _event(
            f"b{index}",
            lat=16.0 + float(rng.normal(0.0, 0.006)),
            lng=108.0 + float(rng.normal(0.0, 0.006)),
            minute=float(rng.uniform(-20.0, 20.0)),
            flood=float(np.clip(a.flood + rng.normal(0.0, 0.08), 0.0, 1.0)),
            urgency=float(
                np.clip(a.urgency + rng.normal(0.0, 0.08), 0.0, 1.0)
            ),
        )
        weight = edge_weight_gating(a, b, params)
        if weight > theta:
            n_retained += 1
            bound = product_distance_bound(params, theta)
            distance = haversine_m(a.lat, a.lng, b.lat, b.lng)
            assert bound.radius_m is not None
            assert distance < bound.radius_m

    assert n_retained > 50


def test_random_bounded_attributes_obey_additive_high_threshold_bound() -> None:
    rng = np.random.default_rng(1402)
    n_retained = 0
    for index in range(200):
        beta = float(rng.uniform(0.0, 0.8))
        gamma = float(rng.uniform(0.0, 0.8))
        alpha = float(rng.uniform(0.1, 1.5))
        b_sum = beta + gamma
        theta = float(b_sum + alpha * rng.uniform(0.05, 0.9))
        params = WeightParams(
            sigma_geo_m=float(rng.uniform(300.0, 1200.0)),
            beta=beta,
            gamma=gamma,
            alpha=alpha,
            edge_threshold=theta,
            knn=0,
        )
        a = _event(f"a{index}")
        b = _event(
            f"b{index}",
            lat=16.0 + float(rng.normal(0.0, 0.005)),
            lng=108.0 + float(rng.normal(0.0, 0.005)),
        )
        weight = edge_weight_additive(a, b, params)
        if weight > theta:
            n_retained += 1
            bound = additive_distance_bound(params, theta)
            distance = haversine_m(a.lat, a.lng, b.lat, b.lng)
            assert bound.radius_m is not None
            assert distance < bound.radius_m

    assert n_retained > 25


def test_exp14_reports_connectivity_and_finite_domain_bounds(tmp_path) -> None:
    events = [
        _event("a", lat=16.0000),
        _event("b", lat=16.0005),
        _event("c", lat=16.0010),
    ]
    candidate = _write_candidate(tmp_path, events)
    params = WeightParams(edge_threshold=0.05, knn=0)

    summary, clusters = analyze_candidate(candidate, params)

    assert summary["domain_eligible"] is True
    assert summary["n_edge_bound_violations"] == 0
    assert summary["n_cluster_bound_violations"] == 0
    assert summary["n_outside_domain_rows_counted"] == 0
    assert len(clusters) == summary["n_clusters"]
    assert all(row["connectivity_status"] in {
        "singleton", "connected", "disconnected"
    } for row in clusters)
    assert any(row["bound_counted"] for row in clusters)
    assert all(
        row["tightness_actual_over_h_r"] < 1.0
        for row in clusters if row["bound_counted"]
    )


def test_exp14_never_counts_empty_or_unbounded_domain_rows(tmp_path) -> None:
    events = [_event("a"), _event("b", lat=16.001)]
    candidate = _write_candidate(tmp_path, events)

    for params, expected_status in [
        (WeightParams(edge_threshold=1.0, knn=0), "empty"),
        (WeightParams(edge_threshold=0.0, knn=0), "unbounded"),
    ]:
        summary, clusters = analyze_candidate(candidate, params)
        assert summary["bound"]["status"] == expected_status
        assert summary["domain_eligible"] is False
        assert summary["n_edge_bound_rows_counted"] == 0
        assert summary["n_cluster_bound_rows_counted"] == 0
        assert summary["n_outside_domain_rows_counted"] == 0
        assert all(row["bound_counted"] is False for row in clusters)


def test_exp14_writes_isolated_result_and_selector_json(tmp_path) -> None:
    candidate = _write_candidate(
        tmp_path,
        [_event("a"), _event("b", lat=16.0005)],
        seed=14,
    )
    output_dir = tmp_path / "artifacts"

    result_path, selector_path = run([candidate], output_dir)

    result = json.loads(result_path.read_text(encoding="utf-8"))
    selectors = json.loads(selector_path.read_text(encoding="utf-8"))
    assert result["experiment"] == "exp14_localization_bounds"
    assert result["candidates"][0]["seed"] == 14
    assert result["candidates"][0]["n_outside_domain_rows_counted"] == 0
    assert selectors["source"] == result_path.name
    assert "cluster_connectivity" in selectors["selectors"]
