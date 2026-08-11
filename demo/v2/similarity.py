"""Missingness-aware product similarity for the version-2 pipeline."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from .contracts import LocationV2, ReportV2


EARTH_RADIUS_M = 6_371_000.0
BoundStatusV2 = Literal["finite", "unbounded", "empty"]


def _positive_finite(value: object, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite and > 0") from exc
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")
    return result


def _nonnegative_finite(value: object, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite and non-negative") from exc
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return result


@dataclass(frozen=True, slots=True)
class SimilarityParamsV2:
    """Locked product-similarity parameters.

    Positive finite ``tau_t``, ``tau_F`` and ``tau_E`` are enforced at the
    contract boundary, rather than relying on NumPy warnings or division by
    zero during graph construction.
    """

    sigma_geo_m: float = 700.0
    tau_t: float = 45.0
    tau_F: float = 0.25
    tau_E: float = 0.25
    beta: float = 0.5
    gamma: float = 0.5
    theta: float = 0.1

    def __post_init__(self) -> None:
        for name in ("sigma_geo_m", "tau_t", "tau_F", "tau_E"):
            object.__setattr__(
                self, name, _positive_finite(getattr(self, name), name)
            )
        for name in ("beta", "gamma", "theta"):
            object.__setattr__(
                self, name, _nonnegative_finite(getattr(self, name), name)
            )


@dataclass(frozen=True, slots=True)
class ProductBoundV2:
    status: BoundStatusV2
    radius_m: float | None
    theta: float
    maximum_weight: float


def haversine_m(first: LocationV2, second: LocationV2) -> float:
    """Haversine distance between two validated locations."""

    lat_first, lng_first = map(math.radians, first)
    lat_second, lng_second = map(math.radians, second)
    delta_lat = lat_second - lat_first
    delta_lng = lng_second - lng_first
    haversine = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat_first)
        * math.cos(lat_second)
        * math.sin(delta_lng / 2.0) ** 2
    )
    haversine = min(1.0, max(0.0, haversine))
    return 2.0 * EARTH_RADIUS_M * math.asin(math.sqrt(haversine))


def geographic_similarity(
    first: ReportV2,
    second: ReportV2,
    params: SimilarityParamsV2,
) -> float:
    if first.L is None or second.L is None:
        return 0.0
    distance = haversine_m(first.L, second.L)
    return math.exp(-(distance**2) / (2.0 * params.sigma_geo_m**2))


def temporal_similarity(
    first: ReportV2,
    second: ReportV2,
    params: SimilarityParamsV2,
) -> float:
    if first.T is None or second.T is None:
        return 0.0
    delta_min = abs((first.T - second.T).total_seconds()) / 60.0
    return math.exp(-delta_min / params.tau_t)


def context_similarity(
    first: ReportV2,
    second: ReportV2,
    params: SimilarityParamsV2,
) -> float:
    """Context agreement with zero contribution from unshared observations.

    The original fully observed context is recovered when both F and E are
    shared.  For partial context, the exponential uses only shared differences
    and is multiplied by ``shared_dimensions / 2``.  Thus an absent dimension
    contributes exactly zero instead of acting like an imputed perfect match:
    no shared context gives 0, one identical shared field gives at most 0.5,
    and two identical shared fields give 1.
    """

    scaled_difference = 0.0
    shared = 0
    if first.F is not None and second.F is not None:
        scaled_difference += abs(first.F - second.F) / params.tau_F
        shared += 1
    if first.E is not None and second.E is not None:
        scaled_difference += abs(first.E - second.E) / params.tau_E
        shared += 1
    if shared == 0:
        return 0.0
    coverage = shared / 2.0
    return coverage * math.exp(-scaled_difference)


def product_similarity(
    first: ReportV2,
    second: ReportV2,
    params: SimilarityParamsV2,
) -> float:
    """Compute ``G * (beta*T + gamma*C)`` for graph-eligible reports.

    Missing L or T is an operational review condition.  Returning zero here is
    a fail-closed guard for direct callers; graph construction additionally
    exposes those report identifiers in its review queue.
    """

    if not first.graph_eligible or not second.graph_eligible:
        return 0.0
    geographic = geographic_similarity(first, second, params)
    temporal = temporal_similarity(first, second, params)
    context = context_similarity(first, second, params)
    return geographic * (params.beta * temporal + params.gamma * context)


def product_distance_bound(params: SimilarityParamsV2) -> ProductBoundV2:
    """Classify the strict-threshold geographic bound for product edges."""

    maximum = params.beta + params.gamma
    if maximum == 0.0 or params.theta >= maximum:
        return ProductBoundV2("empty", None, params.theta, maximum)
    if params.theta == 0.0:
        return ProductBoundV2("unbounded", None, params.theta, maximum)
    log_ratio = math.log(maximum) - math.log(params.theta)
    radius = params.sigma_geo_m * math.sqrt(2.0 * log_ratio)
    return ProductBoundV2("finite", radius, params.theta, maximum)

