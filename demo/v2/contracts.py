"""Version-2 data contracts with a strict inference/evaluation boundary.

``ReportV2`` contains only deployment-visible observations.  ``TruthV2`` is a
separate evaluator-side record linked by ``report_id``; it must never be passed
to similarity, deduplication, graph construction, priority, or dispatch code.

The compact field names ``L/T/F/E/N/V`` follow the manuscript notation.  Every
observation is nullable and accompanied by an explicit mask.  The constructor
derives the mask when omitted and rejects a supplied mask that disagrees with
the nullable values, making missingness auditable without zero imputation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from typing import Iterable, Sequence


LocationV2 = tuple[float, float]


def _finite(value: object, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    return result


def _nonempty_identifier(value: object, name: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{name} must be a non-empty identifier")
    return result


def _normalise_time(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            value = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError("T must be an ISO-8601 timestamp or datetime") from exc
    if not isinstance(value, datetime):
        raise ValueError("T must be an ISO-8601 timestamp or datetime")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _normalise_location(value: Sequence[float] | None) -> LocationV2 | None:
    if value is None:
        return None
    if isinstance(value, (str, bytes)) or len(value) != 2:
        raise ValueError("L must be a (latitude, longitude) pair")
    latitude = _finite(value[0], "L.latitude")
    longitude = _finite(value[1], "L.longitude")
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("L.latitude must lie in [-90, 90]")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError("L.longitude must lie in [-180, 180]")
    # Canonicalise signed zero so equivalent observable payloads hash equally.
    return (
        0.0 if latitude == 0.0 else latitude,
        0.0 if longitude == 0.0 else longitude,
    )


@dataclass(frozen=True, slots=True)
class ObservationMaskV2:
    """Whether each manuscript observation is present in ``ReportV2``."""

    L: bool
    T: bool
    F: bool
    E: bool
    N: bool
    V: bool

    def __post_init__(self) -> None:
        for item in fields(self):
            if type(getattr(self, item.name)) is not bool:
                raise ValueError(f"mask {item.name} must be boolean")

    @classmethod
    def from_values(
        cls,
        *,
        L: object | None,
        T: object | None,
        F: object | None,
        E: object | None,
        N: object | None,
        V: object | None,
    ) -> "ObservationMaskV2":
        return cls(
            L=L is not None,
            T=T is not None,
            F=F is not None,
            E=E is not None,
            N=N is not None,
            V=V is not None,
        )

    @property
    def missing_fields(self) -> tuple[str, ...]:
        return tuple(
            item.name for item in fields(self) if not getattr(self, item.name)
        )


@dataclass(frozen=True, slots=True)
class ReportV2:
    """Inference-visible report with nullable, explicitly masked observations."""

    report_id: str
    L: LocationV2 | Sequence[float] | None = None
    T: datetime | str | None = None
    F: float | None = None
    E: float | None = None
    N: float | None = None
    V: float | None = None
    mask: ObservationMaskV2 | None = None
    source_id: str | None = None
    source_family: str | None = None
    provenance_quality: float | None = None
    has_image: bool = False
    received_at: datetime | str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "report_id", _nonempty_identifier(self.report_id, "report_id")
        )
        object.__setattr__(self, "L", _normalise_location(self.L))
        object.__setattr__(self, "T", _normalise_time(self.T))
        received_at = _normalise_time(self.received_at)
        # For ordinary fully timed records the event/report timestamp is also
        # a safe default receipt timestamp.  Synthetic generation always
        # supplies receipt time explicitly so a missing T can still enter a
        # predeclared observation snapshot and then route to manual review.
        if received_at is None and self.T is not None:
            received_at = self.T
        object.__setattr__(self, "received_at", received_at)

        for name in ("F", "E"):
            value = getattr(self, name)
            if value is None:
                continue
            number = _finite(value, name)
            if not 0.0 <= number <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
            object.__setattr__(self, name, 0.0 if number == 0.0 else number)

        for name in ("N", "V"):
            value = getattr(self, name)
            if value is None:
                continue
            number = _finite(value, name)
            if number < 0.0:
                raise ValueError(f"{name} must be non-negative")
            object.__setattr__(self, name, 0.0 if number == 0.0 else number)

        if type(self.has_image) is not bool:
            raise ValueError("has_image must be boolean")
        for name in ("source_id", "source_family"):
            value = getattr(self, name)
            if value is not None:
                normalised = str(value).strip()
                object.__setattr__(self, name, normalised or None)
        if self.provenance_quality is not None:
            provenance_quality = _finite(
                self.provenance_quality, "provenance_quality"
            )
            if not 0.0 <= provenance_quality <= 1.0:
                raise ValueError("provenance_quality must lie in [0, 1]")
            object.__setattr__(
                self, "provenance_quality", provenance_quality
            )

        derived = ObservationMaskV2.from_values(
            L=self.L,
            T=self.T,
            F=self.F,
            E=self.E,
            N=self.N,
            V=self.V,
        )
        if self.mask is None:
            object.__setattr__(self, "mask", derived)
        elif self.mask != derived:
            raise ValueError(
                "mask must agree exactly with nullable L/T/F/E/N/V values: "
                f"received {self.mask!r}, derived {derived!r}"
            )

    @property
    def latitude(self) -> float | None:
        return None if self.L is None else self.L[0]

    @property
    def longitude(self) -> float | None:
        return None if self.L is None else self.L[1]

    @property
    def missing_fields(self) -> tuple[str, ...]:
        # ``mask`` is always resolved in ``__post_init__``.
        assert self.mask is not None
        return self.mask.missing_fields

    @property
    def graph_eligible(self) -> bool:
        """Graph inference requires both observable location and time."""

        assert self.mask is not None
        return self.mask.L and self.mask.T


@dataclass(frozen=True, slots=True)
class TruthV2:
    """Evaluator-only report-to-incident linkage and report annotations."""

    report_id: str
    incident_id: str | None = None
    gt_cluster: int | None = None
    is_noise: bool = False
    is_fake: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "report_id", _nonempty_identifier(self.report_id, "report_id")
        )
        if self.incident_id is not None:
            object.__setattr__(
                self,
                "incident_id",
                _nonempty_identifier(self.incident_id, "incident_id"),
            )
        if self.gt_cluster is not None and type(self.gt_cluster) is not int:
            raise ValueError("gt_cluster must be an integer or None")
        if type(self.is_noise) is not bool or type(self.is_fake) is not bool:
            raise ValueError("is_noise and is_fake must be boolean")
        if self.incident_id is None:
            if self.gt_cluster is not None or not self.is_noise:
                raise ValueError(
                    "unlinked synthetic truth must be explicitly marked noise "
                    "and cannot have gt_cluster"
                )
        elif self.is_noise or self.gt_cluster is None:
            raise ValueError(
                "incident-linked truth requires gt_cluster and cannot be noise"
            )


@dataclass(frozen=True, slots=True)
class IncidentTruthV2:
    """Evaluator-only latent incident and outcome contract.

    This record is deliberately separate from both ``ReportV2`` and the
    report-level ``TruthV2`` linkage.  Inference code must not accept it; only
    an evaluator may join it through ``TruthV2.incident_id`` after scheduling.
    """

    incident_id: str
    L: LocationV2 | Sequence[float]
    start_min: float
    deadline_min: float
    latent_need: float
    service_demand_min: float
    harm_grace_min: float
    harm_slope: float
    max_harm: float
    n_true: int
    v_true: int
    latent_benefit: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "incident_id",
            _nonempty_identifier(self.incident_id, "incident_id"),
        )
        location = _normalise_location(self.L)
        if location is None:
            raise ValueError("IncidentTruthV2.L cannot be missing")
        object.__setattr__(self, "L", location)

        for name in (
            "start_min",
            "deadline_min",
            "latent_need",
            "service_demand_min",
            "harm_grace_min",
            "harm_slope",
            "max_harm",
        ):
            number = _finite(getattr(self, name), name)
            if number < 0.0:
                raise ValueError(f"{name} must be non-negative")
            object.__setattr__(self, name, number)
        if self.latent_benefit is not None:
            latent_benefit = _finite(self.latent_benefit, "latent_benefit")
            if latent_benefit < 0.0:
                raise ValueError("latent_benefit must be non-negative")
            object.__setattr__(self, "latent_benefit", latent_benefit)

        for name in ("n_true", "v_true"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.v_true > self.n_true:
            raise ValueError("v_true cannot exceed n_true")

    @property
    def latitude(self) -> float:
        return self.L[0]

    @property
    def longitude(self) -> float:
        return self.L[1]


def validate_unique_report_ids(reports: Iterable[ReportV2]) -> None:
    """Fail closed when report identifiers cannot form a one-to-one join key."""

    seen: set[str] = set()
    duplicates: set[str] = set()
    for report in reports:
        if report.report_id in seen:
            duplicates.add(report.report_id)
        seen.add(report.report_id)
    if duplicates:
        rendered = ", ".join(sorted(duplicates))
        raise ValueError(f"duplicate report_id values: {rendered}")


# Lower-case aliases keep the schema names in machine-readable contracts while
# the CamelCase classes remain the idiomatic Python API.
report_v2 = ReportV2
truth_v2 = TruthV2
incident_truth_v2 = IncidentTruthV2
