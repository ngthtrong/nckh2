from datetime import datetime, timezone
import math

import pytest

from demo.v2.contracts import ReportV2
from demo.v2.similarity import (
    SimilarityParamsV2,
    context_similarity,
    product_distance_bound,
    product_similarity,
)


NOW = datetime(2026, 8, 11, tzinfo=timezone.utc)


def _report(report_id: str, **overrides: object) -> ReportV2:
    values: dict[str, object] = {
        "report_id": report_id,
        "L": (16.0, 108.0),
        "T": NOW,
        "F": 0.4,
        "E": 0.8,
        "N": 10,
        "V": 2,
        "source_family": "citizen",
    }
    values.update(overrides)
    return ReportV2(**values)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("tau_t", 0),
        ("tau_t", -1),
        ("tau_F", 0),
        ("tau_F", float("nan")),
        ("tau_E", -0.1),
        ("tau_E", float("inf")),
    ],
)
def test_similarity_requires_positive_finite_taus(name: str, value: float) -> None:
    with pytest.raises(ValueError, match=name):
        SimilarityParamsV2(**{name: value})


def test_unshared_context_contributes_zero_without_zero_imputation() -> None:
    params = SimilarityParamsV2()
    no_context_a = _report("a", F=None, E=None)
    no_context_b = _report("b", F=None, E=None)
    one_shared_a = _report("c", F=0.4, E=None)
    one_shared_b = _report("d", F=0.4, E=None)
    full_a = _report("e", F=0.4, E=0.8)
    full_b = _report("f", F=0.4, E=0.8)

    assert context_similarity(no_context_a, no_context_b, params) == 0.0
    assert context_similarity(one_shared_a, one_shared_b, params) == 0.5
    assert context_similarity(full_a, full_b, params) == 1.0


def test_partial_context_preserves_only_shared_difference_and_coverage() -> None:
    params = SimilarityParamsV2(tau_F=0.2)
    first = _report("a", F=0.2, E=None)
    second = _report("b", F=0.4, E=None)
    assert context_similarity(first, second, params) == pytest.approx(
        0.5 * math.exp(-1.0)
    )


def test_missing_location_or_time_fails_closed_for_product_similarity() -> None:
    params = SimilarityParamsV2()
    complete = _report("complete")
    assert product_similarity(complete, _report("no-l", L=None), params) == 0.0
    assert product_similarity(complete, _report("no-t", T=None), params) == 0.0


def test_product_bound_classifies_finite_empty_and_unbounded_domains() -> None:
    finite = product_distance_bound(SimilarityParamsV2(theta=0.2))
    assert finite.status == "finite"
    assert finite.radius_m is not None and finite.radius_m > 0

    empty = product_distance_bound(SimilarityParamsV2(theta=1.0))
    assert empty.status == "empty"
    assert empty.radius_m is None

    unbounded = product_distance_bound(SimilarityParamsV2(theta=0.0))
    assert unbounded.status == "unbounded"
    assert unbounded.radius_m is None

