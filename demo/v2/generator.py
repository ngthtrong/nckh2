"""Procedural ID/OOD generator for the version-2 confirmation protocol.

The generator emits three physically separate tables: observable reports,
report-to-incident evaluation links, and incident-level outcome truth.  Only
the first table is accepted by inference functions.  OOD datasets change the
data-generating mechanism (counts, tails, missingness, bias, contradictions,
and coordinated campaigns), rather than merely changing a random seed.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

import numpy as np

from demo.v2.contracts import IncidentTruthV2, ReportV2, TruthV2, validate_unique_report_ids


Regime = Literal["id", "ood"]
GENERATOR_VERSION = "flood-rescue-v2.1.0"
PUBLIC_ANCHOR_AUDIT_ID = "audit.public_external_anchor.v2"
SNAPSHOT_CUTOFF_MIN_V2 = 150.0
ACTIVE_CONFIRMATION_SEEDS_V2 = frozenset(range(4400, 4440))
RETIRED_CONFIRMATION_SEEDS_V2 = frozenset(range(4300, 4340))
BASE_TIME = datetime(2026, 10, 15, 0, 0, tzinfo=timezone.utc)
SOURCE_QUALITY = {
    "field_team": 0.88,
    "hotline": 0.74,
    "citizen_app": 0.61,
    "social_media": 0.42,
    "anonymous": 0.27,
}


@dataclass(frozen=True, slots=True)
class StressAnnotationV2:
    """Evaluator-only perturbation annotation, never an inference feature."""

    report_id: str
    family: str


@dataclass(frozen=True, slots=True)
class GeneratedDatasetV2:
    regime: Regime
    master_seed: int
    reports: tuple[ReportV2, ...]
    report_truth: tuple[TruthV2, ...]
    incident_truth: tuple[IncidentTruthV2, ...]
    stress_annotations: tuple[StressAnnotationV2, ...]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        validate_unique_report_ids(self.reports)
        report_ids = {report.report_id for report in self.reports}
        truth_ids = {row.report_id for row in self.report_truth}
        annotation_ids = {row.report_id for row in self.stress_annotations}
        if (
            len(self.report_truth) != len(self.reports)
            or len(truth_ids) != len(self.report_truth)
            or report_ids != truth_ids
        ):
            raise ValueError("observable and evaluator report tables do not align")
        if not annotation_ids.issubset(report_ids):
            raise ValueError("stress annotation refers to an unknown report")
        incident_ids = {row.incident_id for row in self.incident_truth}
        if len(incident_ids) != len(self.incident_truth):
            raise ValueError("incident truth identifiers must be unique")
        linked_ids = {
            row.incident_id for row in self.report_truth if row.incident_id is not None
        }
        if not linked_ids.issubset(incident_ids):
            raise ValueError("report truth refers to an unknown incident")


def _offset(latitude: float, longitude: float, north_m: float, east_m: float) -> tuple[float, float]:
    return (
        latitude + north_m / 111_000.0,
        longitude + east_m / (111_000.0 * math.cos(math.radians(latitude))),
    )


def _clip(value: float, low: float, high: float) -> float:
    return min(high, max(low, float(value)))


def _canonical(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items())}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_canonical(item) for item in value]
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            _canonical(value),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _report_payload(report: ReportV2) -> dict[str, Any]:
    return {
        "report_id": report.report_id,
        "source_id": report.source_id,
        "source_family": report.source_family,
        "L": report.L,
        "T": report.T,
        "received_at": report.received_at,
        "F": report.F,
        "E": report.E,
        "N": report.N,
        "V": report.V,
        "mask": asdict(report.mask) if report.mask is not None else None,
        "provenance_quality": report.provenance_quality,
        "has_image": report.has_image,
    }


def dataset_hashes(dataset: GeneratedDatasetV2) -> dict[str, str]:
    """Return independent hashes so observable data can be shared without truth."""

    tables = {
        "reports": [_report_payload(row) for row in dataset.reports],
        "report_truth": [asdict(row) for row in dataset.report_truth],
        "incident_truth": [asdict(row) for row in dataset.incident_truth],
        "stress_annotations": [asdict(row) for row in dataset.stress_annotations],
    }
    return {
        name: hashlib.sha256(canonical_json_bytes(rows)).hexdigest()
        for name, rows in tables.items()
    }


def _source(rng: np.random.Generator, *, ood: bool) -> tuple[str, str, float, bool]:
    families = tuple(SOURCE_QUALITY)
    probabilities = (
        np.asarray([0.10, 0.20, 0.27, 0.31, 0.12])
        if not ood
        else np.asarray([0.06, 0.16, 0.20, 0.40, 0.18])
    )
    family = str(rng.choice(families, p=probabilities))
    source_id = f"{family}-{int(rng.integers(0, 48 if ood else 80)):03d}"
    quality = _clip(SOURCE_QUALITY[family] + rng.normal(0.0, 0.08), 0.05, 0.98)
    has_image = bool(rng.random() < (0.68 * quality + 0.08))
    return family, source_id, quality, has_image


def _independent_outcome(
    rng: np.random.Generator,
    *,
    flood: float,
    n_true: int,
    v_true: int,
    access_delay: float,
) -> tuple[float, float, float, float, float, float]:
    """Locked nonlinear stochastic target that does not reuse the priority score."""

    vulnerable_share = v_true / max(1, n_true)
    nonlinear = (
        math.log1p(n_true) ** 1.18
        * (0.22 + flood**2.15)
        * (1.0 + 1.35 * vulnerable_share**1.4)
        + 0.018 * n_true * flood * vulnerable_share
        + rng.normal(0.0, 0.35)
    )
    latent_need = max(0.01, nonlinear)
    deadline_min = _clip(
        175.0 - 31.0 * math.log1p(latent_need) - 0.35 * access_delay + rng.normal(0, 9),
        18.0,
        180.0,
    )
    service_demand = _clip(8.0 + 0.34 * n_true + 0.75 * v_true + rng.gamma(2.0, 2.0), 8, 120)
    harm_grace = float(rng.uniform(0.0, 18.0))
    harm_slope = 0.08 + 0.035 * latent_need**1.25
    max_harm = latent_need * (20.0 + 0.45 * n_true)
    return latent_need, deadline_min, service_demand, harm_grace, harm_slope, max_harm


def _missing(
    rng: np.random.Generator,
    field: str,
    *,
    regime: Regime,
    source_quality: float,
    severity: float,
) -> bool:
    if regime == "id":
        rates = {"L": 0.025, "T": 0.012, "F": 0.055, "E": 0.045, "N": 0.08, "V": 0.10}
        probability = rates[field]
    else:
        base = {"L": 0.07, "T": 0.04, "F": 0.11, "E": 0.12, "N": 0.19, "V": 0.24}[field]
        # MNAR: low-quality sources lose more fields; high severity also raises
        # N/V missingness because reports are assumed hurried and incomplete.
        probability = base + 0.18 * (1.0 - source_quality)
        if field in {"N", "V"}:
            probability += 0.12 * severity
    return bool(rng.random() < min(0.75, probability))


def _make_report(
    *,
    report_id: str,
    family: str,
    source_id: str,
    quality: float,
    has_image: bool,
    location: tuple[float, float] | None,
    timestamp: datetime | None,
    received_at: datetime | None,
    flood: float | None,
    urgency: float | None,
    n_claim: float | None,
    vulnerability: float | None,
) -> ReportV2:
    return ReportV2(
        report_id=report_id,
        source_id=source_id,
        source_family=family,
        L=location,
        T=timestamp,
        received_at=received_at,
        F=flood,
        E=urgency,
        N=n_claim,
        V=vulnerability,
        provenance_quality=quality,
        has_image=has_image,
    )


def _noise_report(
    rng: np.random.Generator,
    *,
    report_id: str,
    regime: Regime,
    campaign_center: tuple[float, float] | None = None,
    campaign_time: datetime | None = None,
    campaign_index: int | None = None,
) -> ReportV2:
    if campaign_center is None:
        location = (float(rng.uniform(15.70, 17.10)), float(rng.uniform(107.00, 108.60)))
        timestamp = BASE_TIME + timedelta(minutes=float(rng.uniform(-60, 720)))
        family, source_id, quality, has_image = _source(rng, ood=regime == "ood")
        flood, urgency = float(rng.beta(2, 2)), float(rng.beta(2, 2))
        n_claim, vulnerability = float(rng.integers(0, 120)), float(rng.integers(0, 25))
    else:
        angle = float(rng.uniform(0.0, 2.0 * math.pi))
        radius = float(rng.uniform(0.0, 35.0))
        location = _offset(campaign_center[0], campaign_center[1], radius * math.sin(angle), radius * math.cos(angle))
        timestamp = campaign_time + timedelta(seconds=int(rng.integers(-90, 91)))  # type: ignore[operator]
        families = tuple(SOURCE_QUALITY)
        family = families[int(campaign_index or 0) % len(families)]
        source_id = f"campaign-{family}-{int(campaign_index or 0):02d}"
        quality, has_image = 0.96, True
        flood, urgency, n_claim, vulnerability = 0.96, 0.98, 220.0, 45.0
    return _make_report(
        report_id=report_id,
        family=family,
        source_id=source_id,
        quality=quality,
        has_image=has_image,
        location=location,
        timestamp=timestamp,
        received_at=timestamp,
        flood=flood,
        urgency=urgency,
        n_claim=n_claim,
        vulnerability=vulnerability,
    )


def generate_dataset(
    master_seed: int,
    regime: Regime,
    *,
    confirmation_release: bool = False,
) -> GeneratedDatasetV2:
    """Generate one deterministic ID or mechanism-shift OOD dataset."""

    if isinstance(master_seed, bool) or not isinstance(master_seed, int):
        raise ValueError("master_seed must be an integer")
    if type(confirmation_release) is not bool:
        raise ValueError("confirmation_release must be boolean")
    if master_seed in RETIRED_CONFIRMATION_SEEDS_V2:
        raise ValueError("retired confirmation seeds are permanently unavailable")
    if master_seed in ACTIVE_CONFIRMATION_SEEDS_V2 and not confirmation_release:
        raise ValueError(
            "active confirmation seeds require the managed single-release entrypoint"
        )
    if confirmation_release and master_seed not in ACTIVE_CONFIRMATION_SEEDS_V2:
        raise ValueError("confirmation release capability is valid only for active seeds")
    if regime not in {"id", "ood"}:
        raise ValueError("regime must be 'id' or 'ood'")
    rng = np.random.default_rng(np.random.SeedSequence([master_seed, 0 if regime == "id" else 1]))
    ood = regime == "ood"
    n_incidents = int(rng.integers(8, 31)) if ood else 16
    reports: list[ReportV2] = []
    links: list[TruthV2] = []
    incidents: list[IncidentTruthV2] = []
    stresses: list[StressAnnotationV2] = []
    counter = 0

    for incident_index in range(n_incidents):
        incident_id = f"{regime.upper()}-{master_seed}-{incident_index:02d}"
        gt_cluster = incident_index
        # A quarter of incidents are deliberately near another incident.  The
        # context sometimes supports separation and sometimes contradicts it.
        if incident_index > 0 and incident_index % 4 == 1:
            previous = incidents[-1]
            angle = float(rng.uniform(0.0, 2.0 * math.pi))
            separation = float(rng.uniform(180.0, 700.0))
            center = _offset(previous.L[0], previous.L[1], separation * math.sin(angle), separation * math.cos(angle))
        else:
            center = (float(rng.uniform(15.75, 17.05)), float(rng.uniform(107.05, 108.50)))
        start_min = float(rng.uniform(0.0, 420.0 if ood else 300.0))
        flood_true = float(rng.beta(1.6 if ood else 2.2, 1.8 if ood else 2.3))
        urgency_true = _clip(0.20 + 0.58 * flood_true + rng.normal(0, 0.18), 0.02, 0.99)
        n_true = int(np.clip(rng.lognormal(2.4 if ood else 2.2, 1.0 if ood else 0.65), 1, 240))
        v_true = int(rng.binomial(n_true, _clip(rng.beta(1.8, 5.0), 0.02, 0.75)))
        access_delay = float(rng.gamma(2.4, 10.0 if ood else 6.0))
        latent_need, deadline, service, grace, slope, max_harm = _independent_outcome(
            rng,
            flood=flood_true,
            n_true=n_true,
            v_true=v_true,
            access_delay=access_delay,
        )
        incident = IncidentTruthV2(
            incident_id=incident_id,
            L=center,
            start_min=start_min,
            deadline_min=deadline,
            latent_need=latent_need,
            latent_benefit=latent_need,
            service_demand_min=service,
            harm_grace_min=grace,
            harm_slope=slope,
            max_harm=max_harm,
            n_true=n_true,
            v_true=v_true,
        )
        incidents.append(incident)
        if ood:
            report_count = int(np.clip(round(rng.lognormal(2.0, 0.95)), 2, 48))
            if rng.random() < 0.12:
                report_count = int(rng.integers(35, 65))
            systematic_north, systematic_east = rng.normal(0, 520, size=2)
        else:
            report_count = int(np.clip(rng.poisson(7) + 3, 3, 19))
            systematic_north, systematic_east = rng.normal(0, 80, size=2)

        incident_report_ids: list[str] = []
        for report_index in range(report_count):
            report_id = f"R-{master_seed}-{regime}-{counter:05d}"
            counter += 1
            incident_report_ids.append(report_id)
            family, source_id, quality, has_image = _source(rng, ood=ood)
            if ood and rng.random() < 0.18:
                gps_sd = float(rng.uniform(700.0, 2200.0))
            else:
                gps_sd = 320.0 if ood else 190.0
            north, east = rng.normal(0.0, gps_sd, size=2)
            location = _offset(
                center[0],
                center[1],
                float(north + systematic_north),
                float(east + systematic_east),
            )
            if ood and rng.random() < 0.16:
                delay = float(rng.lognormal(4.8, 0.75))
            else:
                delay = float(max(0.0, rng.normal(34.0 if ood else 18.0, 23.0)))
            timestamp = BASE_TIME + timedelta(minutes=start_min + delay)
            flood = _clip(flood_true + rng.normal(0, 0.13 if ood else 0.08), 0, 1)
            urgency = _clip(urgency_true + rng.normal(0, 0.15 if ood else 0.09), 0, 1)
            n_claim = float(max(0, round(n_true * rng.lognormal(-0.35, 0.42 if ood else 0.25))))
            vulnerability = float(max(0, round(v_true * rng.lognormal(-0.25, 0.40 if ood else 0.22))))
            severity = max(flood, urgency)
            values: dict[str, Any] = {
                "L": location,
                "T": timestamp,
                "F": flood,
                "E": urgency,
                "N": n_claim,
                "V": vulnerability,
            }
            for field in tuple(values):
                if _missing(rng, field, regime=regime, source_quality=quality, severity=severity):
                    values[field] = None
            report = _make_report(
                report_id=report_id,
                family=family,
                source_id=source_id,
                quality=quality,
                has_image=has_image,
                location=values["L"],
                timestamp=values["T"],
                received_at=timestamp,
                flood=values["F"],
                urgency=values["E"],
                n_claim=values["N"],
                vulnerability=values["V"],
            )
            reports.append(report)
            links.append(
                TruthV2(
                    report_id=report_id,
                    incident_id=incident_id,
                    gt_cluster=gt_cluster,
                )
            )

        # Exact and near duplicates are injected after the base family exists.
        base_candidates = [row for row in reports if row.report_id in incident_report_ids]
        if base_candidates and rng.random() < (0.70 if ood else 0.35):
            original = base_candidates[int(rng.integers(0, len(base_candidates)))]
            exact_id = f"R-{master_seed}-{regime}-{counter:05d}"
            counter += 1
            exact = replace(original, report_id=exact_id)
            reports.append(exact)
            original_truth = next(
                row for row in links if row.report_id == original.report_id
            )
            links.append(replace(original_truth, report_id=exact_id))
            stresses.append(StressAnnotationV2(exact_id, "exact_duplicate"))
        located = [row for row in base_candidates if row.L is not None and row.T is not None]
        if located and rng.random() < (0.75 if ood else 0.40):
            original = located[int(rng.integers(0, len(located)))]
            near_id = f"R-{master_seed}-{regime}-{counter:05d}"
            counter += 1
            near_location = _offset(original.L[0], original.L[1], float(rng.uniform(-30, 30)), float(rng.uniform(-30, 30)))
            near = replace(
                original,
                report_id=near_id,
                L=near_location,
                T=original.T + timedelta(minutes=float(rng.uniform(-2, 2))),
                F=None if original.F is None else _clip(original.F + rng.normal(0, 0.015), 0, 1),
                E=None if original.E is None else _clip(original.E + rng.normal(0, 0.015), 0, 1),
            )
            reports.append(near)
            original_truth = next(row for row in links if row.report_id == original.report_id)
            links.append(replace(original_truth, report_id=near_id))
            stresses.append(StressAnnotationV2(near_id, "near_duplicate"))

        if ood and located and incident_index % 5 == 0:
            anchor = located[0]
            # Adjacent steps fit a 100 m envelope but endpoints do not; a
            # complete-link family must therefore refuse transitive chaining.
            for chain_index in range(1, 5):
                chain_id = f"R-{master_seed}-{regime}-{counter:05d}"
                counter += 1
                chain = replace(
                    anchor,
                    report_id=chain_id,
                    L=_offset(anchor.L[0], anchor.L[1], 0.0, 65.0 * chain_index),
                    T=anchor.T + timedelta(minutes=1.5 * chain_index),
                )
                reports.append(chain)
                original_truth = next(row for row in links if row.report_id == anchor.report_id)
                links.append(replace(original_truth, report_id=chain_id))
                stresses.append(StressAnnotationV2(chain_id, "gradual_chain_duplicate"))

        if ood and base_candidates and incident_index % 6 == 2:
            original = base_candidates[0]
            contradiction_id = f"R-{master_seed}-{regime}-{counter:05d}"
            counter += 1
            contradiction = replace(
                original,
                report_id=contradiction_id,
                F=None if original.F is None else 1.0 - original.F,
                E=None if original.E is None else 1.0 - original.E,
            )
            reports.append(contradiction)
            original_truth = next(row for row in links if row.report_id == original.report_id)
            links.append(replace(original_truth, report_id=contradiction_id))
            stresses.append(StressAnnotationV2(contradiction_id, "contradictory_report"))

    n_noise = int(round(len(reports) * float(rng.uniform(0.08, 0.24) if ood else 0.08)))
    for _ in range(n_noise):
        report_id = f"R-{master_seed}-{regime}-{counter:05d}"
        counter += 1
        report = _noise_report(rng, report_id=report_id, regime=regime)
        reports.append(report)
        links.append(TruthV2(report_id=report_id, is_noise=True, is_fake=True))
        stresses.append(StressAnnotationV2(report_id, "background_noise"))

    if ood:
        campaign_center = (float(rng.uniform(15.9, 16.8)), float(rng.uniform(107.2, 108.3)))
        campaign_time = BASE_TIME + timedelta(minutes=float(rng.uniform(30, 330)))
        for campaign_index in range(int(rng.integers(5, 11))):
            report_id = f"R-{master_seed}-{regime}-{counter:05d}"
            counter += 1
            report = _noise_report(
                rng,
                report_id=report_id,
                regime=regime,
                campaign_center=campaign_center,
                campaign_time=campaign_time,
                campaign_index=campaign_index,
            )
            reports.append(report)
            links.append(TruthV2(report_id=report_id, is_noise=True, is_fake=True))
            stresses.append(StressAnnotationV2(report_id, "coordinated_high_confidence_campaign"))

    permutation = rng.permutation(len(reports))
    reports = [reports[int(index)] for index in permutation]
    # Truth tables are independently ordered to discourage accidental zip joins.
    truth_permutation = rng.permutation(len(links))
    links = [links[int(index)] for index in truth_permutation]
    metadata = {
        "generator_version": GENERATOR_VERSION,
        "mechanism": regime,
        "master_seed": master_seed,
        "n_incidents": n_incidents,
        "n_reports": len(reports),
        "public_anchor_audit_id": PUBLIC_ANCHOR_AUDIT_ID,
        "public_anchor_role": "descriptive_plausibility_check_only",
        "public_parameters_fitted": [],
        "public_marginal_anchor": (
            "no_parameters_fitted; the predeclared 300-minute ID start window "
            "is compared only with the pinned NOAA flood-duration p75"
        ),
        "truth_join_key": "report_id",
        "report_order_independent_of_truth_order": True,
        "ood_mechanism_changes": (
            [
                "variable_incident_count",
                "heavy_tailed_report_count",
                "mixture_and_systematic_gps_error",
                "late_reports",
                "source_and_severity_correlated_mnar",
                "variable_noise",
                "contradictions",
                "gradual_chain_duplicates",
                "coordinated_high_confidence_campaign",
            ]
            if ood
            else []
        ),
    }
    return GeneratedDatasetV2(
        regime=regime,
        master_seed=master_seed,
        reports=tuple(reports),
        report_truth=tuple(links),
        incident_truth=tuple(incidents),
        stress_annotations=tuple(stresses),
        metadata=metadata,
    )


def observation_snapshot(
    dataset: GeneratedDatasetV2,
    *,
    cutoff_min: float = SNAPSHOT_CUTOFF_MIN_V2,
) -> GeneratedDatasetV2:
    """Return the predeclared observable batch available by ``cutoff_min``.

    Inclusion uses the inference-visible receipt timestamp, never event truth.
    Missing event time ``T`` is therefore still observable at receipt and is
    retained for the manual-review queue.  Evaluator incidents are restricted
    to those whose authored onset has occurred by the same wall-clock cutoff;
    that truth-side restriction is applied only after the observable report
    set is fixed.
    """

    if isinstance(cutoff_min, bool) or not isinstance(cutoff_min, (int, float)):
        raise ValueError("snapshot cutoff must be finite and non-negative")
    cutoff = float(cutoff_min)
    if not math.isfinite(cutoff) or cutoff < 0.0:
        raise ValueError("snapshot cutoff must be finite and non-negative")
    missing_receipt = [
        report.report_id for report in dataset.reports if report.received_at is None
    ]
    if missing_receipt:
        raise ValueError(
            "generated reports require receipt timestamps for snapshotting: "
            f"{sorted(missing_receipt)[:5]}"
        )
    cutoff_time = BASE_TIME + timedelta(minutes=cutoff)
    observed_reports = tuple(
        report
        for report in dataset.reports
        if report.received_at is not None and report.received_at <= cutoff_time
    )
    observed_ids = {report.report_id for report in observed_reports}
    observed_truth = tuple(
        row for row in dataset.report_truth if row.report_id in observed_ids
    )
    eligible_incidents = tuple(
        row for row in dataset.incident_truth if row.start_min <= cutoff
    )
    eligible_incident_ids = {row.incident_id for row in eligible_incidents}
    early_future_links = sorted(
        {
            row.incident_id
            for row in observed_truth
            if row.incident_id is not None
            and row.incident_id not in eligible_incident_ids
        }
    )
    if early_future_links:
        raise ValueError(
            "observable reports precede their incident onset: "
            f"{early_future_links[:5]}"
        )
    observed_stress = tuple(
        row for row in dataset.stress_annotations if row.report_id in observed_ids
    )
    metadata = {
        **dict(dataset.metadata),
        "snapshot_cutoff_min": cutoff,
        "snapshot_rule": "received_at_at_or_before_cutoff",
        "n_full_stream_reports": len(dataset.reports),
        "n_snapshot_reports": len(observed_reports),
        "n_snapshot_incidents_started": len(eligible_incidents),
        "late_reports_excluded_from_snapshot": len(dataset.reports)
        - len(observed_reports),
    }
    return GeneratedDatasetV2(
        regime=dataset.regime,
        master_seed=dataset.master_seed,
        reports=observed_reports,
        report_truth=observed_truth,
        incident_truth=eligible_incidents,
        stress_annotations=observed_stress,
        metadata=metadata,
    )


def write_dataset(dataset: GeneratedDatasetV2, output_directory: str | Path) -> dict[str, str]:
    """Write separate observable/evaluator JSON files and return their hashes."""

    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    payloads = {
        "reports.json": [_report_payload(row) for row in dataset.reports],
        "report_truth.json": [asdict(row) for row in dataset.report_truth],
        "incident_truth.json": [asdict(row) for row in dataset.incident_truth],
        "stress_annotations.json": [asdict(row) for row in dataset.stress_annotations],
        "metadata.json": dict(dataset.metadata),
    }
    hashes: dict[str, str] = {}
    for filename, payload in payloads.items():
        encoded = canonical_json_bytes(payload)
        (directory / filename).write_bytes(encoded)
        hashes[filename] = hashlib.sha256(encoded).hexdigest()
    manifest = {
        "generator_version": GENERATOR_VERSION,
        "regime": dataset.regime,
        "master_seed": dataset.master_seed,
        "files": hashes,
    }
    manifest_bytes = canonical_json_bytes(manifest)
    (directory / "manifest.json").write_bytes(manifest_bytes)
    hashes["manifest.json"] = hashlib.sha256(manifest_bytes).hexdigest()
    return hashes


__all__ = [
    "GENERATOR_VERSION",
    "ACTIVE_CONFIRMATION_SEEDS_V2",
    "PUBLIC_ANCHOR_AUDIT_ID",
    "RETIRED_CONFIRMATION_SEEDS_V2",
    "SNAPSHOT_CUTOFF_MIN_V2",
    "GeneratedDatasetV2",
    "StressAnnotationV2",
    "canonical_json_bytes",
    "dataset_hashes",
    "generate_dataset",
    "observation_snapshot",
    "write_dataset",
]
