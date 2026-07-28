"""Deterministic, method-agnostic distribution report for candidate data.

The report describes the frozen synthetic data only.  It deliberately contains
no clustering result, preferred-method comparison, ranking endpoint, or
acceptance threshold derived from method performance.  Test-split summaries
are descriptive provenance for the data freeze and are not exposed through
the tuning API.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from data.schema import (  # noqa: E402
    OBSERVABLE_FIELDS,
    canonical_json_bytes,
    observable_report,
    sha256_bytes,
    validate_candidate_dataset,
)
from pipeline.attributes import Event, compute_confidence, haversine_m  # noqa: E402
from pipeline.config import DEFAULT_CONFIG  # noqa: E402


REPORT_SCHEMA_VERSION = "candidate-data-distribution-report-v1"
CONFIDENCE_BAND_CUT = 0.5
CONFIDENCE_HISTOGRAM_EDGES = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
MEASUREMENT_FIELDS = ("flood", "urgency", "n_trapped", "vulnerability")
EVALUATION_FIELDS = (
    "incident_id",
    "gt_cluster",
    "scenario_family",
    "duplicate_kind",
    "duplicate_family_id",
    "coverage_n",
    "coverage_v",
    "population_member_indices",
    "vulnerable_member_indices",
    "is_fake",
    "adversary",
)
SPLIT_ORDER = {"development": 0, "calibration": 1, "test": 2}


def _rounded(value: float) -> float:
    result = round(float(value), 6)
    return 0.0 if result == 0 else result


def _rate(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return _rounded(float(numerator) / float(denominator))


def _quantile(sorted_values: Sequence[float], probability: float) -> float | None:
    """R-7/NumPy-linear quantile without a runtime dependency on NumPy."""
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return _rounded(sorted_values[0])
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return _rounded(sorted_values[lower])
    fraction = position - lower
    return _rounded(
        sorted_values[lower]
        + fraction * (sorted_values[upper] - sorted_values[lower])
    )


def _numeric_summary(values: Iterable[int | float]) -> dict[str, int | float | None]:
    clean = sorted(
        float(value)
        for value in values
        if math.isfinite(float(value))
    )
    if not clean:
        return {
            "n": 0,
            "min": None,
            "p05": None,
            "p25": None,
            "median": None,
            "p75": None,
            "p95": None,
            "max": None,
            "iqr": None,
            "mad": None,
            "mean": None,
        }
    median = _quantile(clean, 0.5)
    p25 = _quantile(clean, 0.25)
    p75 = _quantile(clean, 0.75)
    assert median is not None and p25 is not None and p75 is not None
    absolute_deviations = sorted(abs(value - median) for value in clean)
    return {
        "n": len(clean),
        "min": _rounded(clean[0]),
        "p05": _quantile(clean, 0.05),
        "p25": p25,
        "median": median,
        "p75": p75,
        "p95": _quantile(clean, 0.95),
        "max": _rounded(clean[-1]),
        "iqr": _rounded(p75 - p25),
        "mad": _quantile(absolute_deviations, 0.5),
        "mean": _rounded(sum(clean) / len(clean)),
    }


def _categorical(values: Iterable[object]) -> dict[str, Any]:
    counts = Counter("<null>" if value is None else str(value) for value in values)
    total = sum(counts.values())
    return {
        "n": total,
        "categories": {
            category: {
                "count": count,
                "rate": _rate(count, total),
            }
            for category, count in sorted(counts.items())
        },
    }


def _missingness(
    reports: Sequence[dict[str, Any]],
) -> dict[str, dict[str, int | float]]:
    """Summarize structural missingness and the locked measurement mask.

    Candidate v4 uses zero imputation for F/E/N/V and records the original
    missing measurement names in ``missing_fields``.  Treating the imputed zero
    itself as missing would conflate a valid boundary value with missingness.
    """
    total = len(reports)
    masked_counts = Counter()
    for report in reports:
        raw_mask = report.get("missing_fields", [])
        if isinstance(raw_mask, list):
            masked_counts.update(
                str(field) for field in raw_mask if field in MEASUREMENT_FIELDS
            )

    result: dict[str, dict[str, int | float]] = {}
    for field in OBSERVABLE_FIELDS:
        if field in MEASUREMENT_FIELDS:
            count = masked_counts[field]
        else:
            count = sum(
                field not in report or report.get(field) is None for report in reports
            )
        result[field] = {
            "missing_count": int(count),
            "missing_rate": _rate(count, total),
        }
    return result


def _evaluation_missingness(
    reports: Sequence[dict[str, Any]],
) -> dict[str, dict[str, int | float]]:
    total = len(reports)
    result: dict[str, dict[str, int | float]] = {}
    for field in EVALUATION_FIELDS:
        count = sum(
            not isinstance(report.get("evaluation_only"), dict)
            or field not in report["evaluation_only"]
            or report["evaluation_only"].get(field) is None
            for report in reports
        )
        result[field] = {
            "missing_count": count,
            "missing_rate": _rate(count, total),
        }
    return result


def _confidence_for_reports(
    reports: Sequence[dict[str, Any]],
) -> dict[str, dict[str, int | float]]:
    events: list[Event] = []
    for full_report in reports:
        report = observable_report(full_report)
        events.append(
            Event(
                event_id=str(report["event_id"]),
                lat=float(report["lat"]),
                lng=float(report["lng"]),
                created_at=datetime.fromisoformat(str(report["created_at"])),
                flood=float(report["flood"]),
                urgency=float(report["urgency"]),
                n_trapped=int(report["n_trapped"]),
                vulnerability=float(report["vulnerability"]),
                has_image=bool(report["has_image"]),
                source_type=str(report["source_type"]),
                province=str(report["province"]),
                note=str(report["note"]),
                missing_fields=tuple(str(field) for field in report["missing_fields"]),
            )
        )
    compute_confidence(events, DEFAULT_CONFIG.confidence)
    return {
        event.event_id: {
            "score": _rounded(event.confidence),
            "n_corroborating_payloads": event.n_corrob,
        }
        for event in events
    }


def _safe_dataset_path(bundle_dir: Path, relative_name: object) -> Path:
    relative = Path(str(relative_name))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"dataset path is not bundle-contained: {relative}")
    source = (bundle_dir / relative).resolve()
    resolved_bundle = bundle_dir.resolve()
    if resolved_bundle not in source.parents:
        raise ValueError(f"dataset path escapes bundle: {relative}")
    return source


def _load_records(
    bundle_dir: Path,
    manifest: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    manifest_path = bundle_dir / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    disk_manifest = json.loads(manifest_bytes)
    if manifest is not None and manifest != disk_manifest:
        raise ValueError("supplied dataset manifest differs from frozen manifest")
    manifest = disk_manifest
    raw_entries = manifest.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ValueError("dataset manifest has no entries")

    records: list[dict[str, Any]] = []
    for entry in raw_entries:
        if not isinstance(entry, dict):
            raise ValueError("dataset manifest entry must be an object")
        source = _safe_dataset_path(bundle_dir, entry.get("path"))
        payload = source.read_bytes()
        if sha256_bytes(payload) != entry.get("sha256"):
            raise ValueError(f"dataset checksum mismatch: {entry.get('path')}")
        data = json.loads(payload)
        seed = int(entry["seed"])
        split = str(entry["split"])
        validate_candidate_dataset(
            data,
            expected_seed=seed,
            expected_split=split,
        )
        if data.get("seed") != seed or data.get("split") != split:
            raise ValueError(f"dataset identity mismatch: {entry.get('path')}")
        records.append(
            {
                "seed": seed,
                "split": split,
                "data": data,
                "confidence": _confidence_for_reports(data["reports"]),
            }
        )

    records.sort(
        key=lambda row: (
            SPLIT_ORDER.get(str(row["split"]), 99),
            int(row["seed"]),
        )
    )
    return records, manifest, sha256_bytes(manifest_bytes)


def _selected(
    records: Sequence[dict[str, Any]],
    family: str | None,
) -> tuple[
    list[dict[str, Any]],
    list[tuple[dict[str, Any], dict[str, Any]]],
]:
    incidents: list[dict[str, Any]] = []
    reports: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for record in records:
        selected_incidents = [
            incident
            for incident in record["data"]["incidents"]
            if family is None or incident["scenario_family"] == family
        ]
        incident_ids = {
            str(incident["incident_id"]) for incident in selected_incidents
        }
        incidents.extend(selected_incidents)
        for report in record["data"]["reports"]:
            if family is None or str(
                report["evaluation_only"].get("incident_id")
            ) in incident_ids:
                reports.append((record, report))
    return incidents, reports


def _duplicate_summary(
    reports: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    total = len(reports)
    exact = [
        report
        for report in reports
        if report["evaluation_only"].get("duplicate_kind") == "exact"
    ]
    near = [
        report
        for report in reports
        if report["evaluation_only"].get("duplicate_kind") == "near"
    ]
    exact_groups = Counter(
        str(report["evaluation_only"]["duplicate_family_id"]) for report in exact
    )
    near_groups = Counter(
        str(report["evaluation_only"]["duplicate_family_id"]) for report in near
    )
    return {
        "exact": {
            "report_count": len(exact),
            "report_rate": _rate(len(exact), total),
            "family_count": len(exact_groups),
            "family_size": _numeric_summary(exact_groups.values()),
        },
        "near": {
            "report_count": len(near),
            "report_rate": _rate(len(near), total),
            "family_count": len(near_groups),
            "family_size": _numeric_summary(near_groups.values()),
        },
    }


def _membership_summary(
    incidents: Sequence[dict[str, Any]],
    reports: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    by_incident: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for report in reports:
        incident_id = report["evaluation_only"].get("incident_id")
        if incident_id is not None:
            by_incident[str(incident_id)].append(report)

    population_reuse: list[float] = []
    population_unique_coverage: list[float] = []
    vulnerable_reuse: list[float] = []
    vulnerable_unique_coverage: list[float] = []
    population_jaccard: list[float] = []
    population_overlap_coefficient: list[float] = []
    vulnerable_jaccard: list[float] = []
    vulnerable_overlap_coefficient: list[float] = []
    report_coverage_n: list[float] = []
    report_coverage_v: list[float] = []

    for incident in incidents:
        rows = by_incident.get(str(incident["incident_id"]), [])
        population_sets = [
            set(report["evaluation_only"]["population_member_indices"])
            for report in rows
        ]
        vulnerable_sets = [
            set(report["evaluation_only"]["vulnerable_member_indices"])
            for report in rows
        ]
        population_occurrences = sum(len(values) for values in population_sets)
        vulnerable_occurrences = sum(len(values) for values in vulnerable_sets)
        population_union = set().union(*population_sets) if population_sets else set()
        vulnerable_union = set().union(*vulnerable_sets) if vulnerable_sets else set()
        if population_occurrences:
            population_reuse.append(
                1.0 - len(population_union) / population_occurrences
            )
        population_unique_coverage.append(
            len(population_union) / int(incident["n_true"])
        )
        if vulnerable_occurrences:
            vulnerable_reuse.append(
                1.0 - len(vulnerable_union) / vulnerable_occurrences
            )
        if int(incident["v_true"]) > 0:
            vulnerable_unique_coverage.append(
                len(vulnerable_union) / int(incident["v_true"])
            )

        for report in rows:
            evaluation = report["evaluation_only"]
            report_coverage_n.append(float(evaluation["coverage_n"]))
            report_coverage_v.append(float(evaluation["coverage_v"]))

        for index, first in enumerate(population_sets):
            for second in population_sets[index + 1 :]:
                union = first | second
                if union:
                    population_jaccard.append(len(first & second) / len(union))
                smaller = min(len(first), len(second))
                if smaller:
                    population_overlap_coefficient.append(
                        len(first & second) / smaller
                    )
        for index, first in enumerate(vulnerable_sets):
            for second in vulnerable_sets[index + 1 :]:
                union = first | second
                if union:
                    vulnerable_jaccard.append(len(first & second) / len(union))
                smaller = min(len(first), len(second))
                if smaller:
                    vulnerable_overlap_coefficient.append(
                        len(first & second) / smaller
                    )

    return {
        "report_level_coverage_n": _numeric_summary(report_coverage_n),
        "report_level_coverage_v": _numeric_summary(report_coverage_v),
        "incident_population_reuse_rate": _numeric_summary(population_reuse),
        "incident_unique_population_coverage": _numeric_summary(
            population_unique_coverage
        ),
        "incident_vulnerable_reuse_rate": _numeric_summary(vulnerable_reuse),
        "incident_unique_vulnerable_coverage": _numeric_summary(
            vulnerable_unique_coverage
        ),
        "pairwise_population_jaccard": _numeric_summary(population_jaccard),
        "pairwise_population_overlap_coefficient": _numeric_summary(
            population_overlap_coefficient
        ),
        "pairwise_vulnerable_jaccard": _numeric_summary(vulnerable_jaccard),
        "pairwise_vulnerable_overlap_coefficient": _numeric_summary(
            vulnerable_overlap_coefficient
        ),
    }


def _dispersion_summary(
    incidents: Sequence[dict[str, Any]],
    reports: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    incident_by_id = {
        str(incident["incident_id"]): incident for incident in incidents
    }
    by_incident: dict[str, list[dict[str, Any]]] = defaultdict(list)
    center_distances: list[float] = []
    signed_time_offsets: list[float] = []
    absolute_time_offsets: list[float] = []

    for report in reports:
        incident_id = report["evaluation_only"].get("incident_id")
        if incident_id is None or str(incident_id) not in incident_by_id:
            continue
        incident = incident_by_id[str(incident_id)]
        by_incident[str(incident_id)].append(report)
        center_distances.append(
            haversine_m(
                float(report["lat"]),
                float(report["lng"]),
                float(incident["center_lat"]),
                float(incident["center_lng"]),
            )
        )
        offset = (
            datetime.fromisoformat(str(report["created_at"]))
            - datetime.fromisoformat(str(incident["start_at"]))
        ).total_seconds() / 60.0
        signed_time_offsets.append(offset)
        absolute_time_offsets.append(abs(offset))

    time_ranges: list[float] = []
    flood_deviations: list[float] = []
    urgency_deviations: list[float] = []
    context_l1_deviations: list[float] = []
    for rows in by_incident.values():
        timestamps = sorted(
            datetime.fromisoformat(str(report["created_at"])) for report in rows
        )
        if timestamps:
            time_ranges.append(
                (timestamps[-1] - timestamps[0]).total_seconds() / 60.0
            )
        flood_values = sorted(float(report["flood"]) for report in rows)
        urgency_values = sorted(float(report["urgency"]) for report in rows)
        flood_median = _quantile(flood_values, 0.5)
        urgency_median = _quantile(urgency_values, 0.5)
        assert flood_median is not None and urgency_median is not None
        for report in rows:
            flood_delta = abs(float(report["flood"]) - flood_median)
            urgency_delta = abs(float(report["urgency"]) - urgency_median)
            flood_deviations.append(flood_delta)
            urgency_deviations.append(urgency_delta)
            context_l1_deviations.append(flood_delta + urgency_delta)

    return {
        "coordinate_distance_to_latent_center_m": _numeric_summary(center_distances),
        "signed_time_offset_from_incident_start_min": _numeric_summary(
            signed_time_offsets
        ),
        "absolute_time_offset_from_incident_start_min": _numeric_summary(
            absolute_time_offsets
        ),
        "incident_report_time_range_min": _numeric_summary(time_ranges),
        "flood_abs_deviation_from_incident_median": _numeric_summary(
            flood_deviations
        ),
        "urgency_abs_deviation_from_incident_median": _numeric_summary(
            urgency_deviations
        ),
        "context_l1_abs_deviation_from_incident_medians": _numeric_summary(
            context_l1_deviations
        ),
    }


def _histogram(values: Sequence[float]) -> dict[str, int]:
    counts = {
        f"[{CONFIDENCE_HISTOGRAM_EDGES[index]:.1f},"
        f"{CONFIDENCE_HISTOGRAM_EDGES[index + 1]:.1f}"
        f"{']' if index == len(CONFIDENCE_HISTOGRAM_EDGES) - 2 else ')'}": 0
        for index in range(len(CONFIDENCE_HISTOGRAM_EDGES) - 1)
    }
    labels = list(counts)
    for value in values:
        index = len(CONFIDENCE_HISTOGRAM_EDGES) - 2
        for candidate in range(len(CONFIDENCE_HISTOGRAM_EDGES) - 1):
            if value < CONFIDENCE_HISTOGRAM_EDGES[candidate + 1]:
                index = candidate
                break
        counts[labels[index]] += 1
    return counts


def _confidence_truth_summary(
    selected_reports: Sequence[tuple[dict[str, Any], dict[str, Any]]],
) -> dict[str, Any]:
    by_truth: dict[str, list[float]] = {"real": [], "fake": []}
    cross_tab = {
        "real": {"low": 0, "high": 0},
        "fake": {"low": 0, "high": 0},
    }
    corroboration: dict[str, list[int]] = {"real": [], "fake": []}
    adversary_scores: dict[str, list[float]] = defaultdict(list)
    for record, report in selected_reports:
        truth = "fake" if report["evaluation_only"].get("is_fake") else "real"
        derived = record["confidence"][str(report["event_id"])]
        score = float(derived["score"])
        band = "high" if score >= CONFIDENCE_BAND_CUT else "low"
        by_truth[truth].append(score)
        cross_tab[truth][band] += 1
        corroboration[truth].append(int(derived["n_corroborating_payloads"]))
        adversary = report["evaluation_only"].get("adversary")
        if adversary is not None:
            adversary_scores[str(adversary)].append(score)

    histograms = {truth: _histogram(scores) for truth, scores in by_truth.items()}
    real_total = len(by_truth["real"])
    fake_total = len(by_truth["fake"])
    overlap = 0.0
    if real_total and fake_total:
        overlap = sum(
            min(
                histograms["real"][label] / real_total,
                histograms["fake"][label] / fake_total,
            )
            for label in histograms["real"]
        )

    total = real_total + fake_total
    return {
        "descriptive_band_cut": CONFIDENCE_BAND_CUT,
        "band_cut_role": "description_only_not_an_acceptance_or_tuning_threshold",
        "truth_counts": {
            "real": real_total,
            "fake": fake_total,
            "fake_rate": _rate(fake_total, total),
        },
        "truth_by_confidence_band": {
            truth: {
                "low_count": values["low"],
                "high_count": values["high"],
                "low_rate_within_truth": _rate(
                    values["low"], values["low"] + values["high"]
                ),
                "high_rate_within_truth": _rate(
                    values["high"], values["low"] + values["high"]
                ),
            }
            for truth, values in cross_tab.items()
        },
        "confidence_score_by_truth": {
            truth: _numeric_summary(values) for truth, values in by_truth.items()
        },
        "corroborating_payload_count_by_truth": {
            truth: _numeric_summary(values)
            for truth, values in corroboration.items()
        },
        "confidence_histogram_by_truth": histograms,
        "histogram_overlap_coefficient": _rounded(overlap),
        "confidence_by_adversary_case": {
            label: _numeric_summary(values)
            for label, values in sorted(adversary_scores.items())
        },
    }


def _group_summary(
    records: Sequence[dict[str, Any]],
    *,
    family: str | None = None,
) -> dict[str, Any]:
    incidents, selected_reports = _selected(records, family)
    reports = [report for _, report in selected_reports]
    linked_reports = [
        report
        for report in reports
        if report["evaluation_only"].get("incident_id") is not None
    ]
    unlinked_reports = [
        report
        for report in reports
        if report["evaluation_only"].get("incident_id") is None
    ]

    linked_counts = Counter(
        str(report["evaluation_only"]["incident_id"]) for report in linked_reports
    )
    latent_n = [int(incident["n_true"]) for incident in incidents]
    latent_v = [float(incident["v_true"]) for incident in incidents]
    report_partitions = {
        "all": reports,
        "linked": linked_reports,
        "unlinked": unlinked_reports,
    }

    return {
        "scope": {
            "n_datasets": len(records),
            "n_incidents": len(incidents),
            "n_reports": len(reports),
            "n_linked_reports": len(linked_reports),
            "n_unlinked_reports": len(unlinked_reports),
            "unlinked_report_rate": _rate(len(unlinked_reports), len(reports)),
        },
        "reports_per_incident": _numeric_summary(
            linked_counts.get(str(incident["incident_id"]), 0)
            for incident in incidents
        ),
        "duplicates": _duplicate_summary(reports),
        "missingness": {
            "observable": _missingness(reports),
            "evaluation_all_reports": _evaluation_missingness(reports),
            "evaluation_linked_reports": _evaluation_missingness(linked_reports),
        },
        "provenance": {
            "source_type": _categorical(
                report.get("source_type") for report in reports
            ),
            "has_image": _categorical(
                report.get("has_image") for report in reports
            ),
            "province": _categorical(report.get("province") for report in reports),
            "source_type_by_truth": {
                truth: _categorical(
                    report.get("source_type")
                    for report in reports
                    if bool(report["evaluation_only"].get("is_fake"))
                    == (truth == "fake")
                )
                for truth in ("real", "fake")
            },
        },
        "latent_incident_truth": {
            "n_true": _numeric_summary(latent_n),
            "v_true": _numeric_summary(latent_v),
            "vulnerable_share": _numeric_summary(
                float(incident["v_true"]) / int(incident["n_true"])
                for incident in incidents
            ),
        },
        "reported_measurements": {
            partition: {
                "n_trapped_after_locked_imputation": _numeric_summary(
                    int(report["n_trapped"]) for report in rows
                ),
                "n_trapped_observed_only": _numeric_summary(
                    int(report["n_trapped"])
                    for report in rows
                    if "n_trapped" not in report.get("missing_fields", [])
                ),
                "vulnerability_after_locked_imputation": _numeric_summary(
                    float(report["vulnerability"]) for report in rows
                ),
                "vulnerability_observed_only": _numeric_summary(
                    float(report["vulnerability"])
                    for report in rows
                    if "vulnerability" not in report.get("missing_fields", [])
                ),
            }
            for partition, rows in report_partitions.items()
        },
        "membership_overlap": _membership_summary(incidents, linked_reports),
        "coordinate_time_context_dispersion": _dispersion_summary(
            incidents, linked_reports
        ),
        "confidence_truth_overlap": _confidence_truth_summary(selected_reports),
        "latent_outcome_parameters": {
            "deadline_min": _numeric_summary(
                float(incident["deadline_min"]) for incident in incidents
            ),
            "service_demand_min": _numeric_summary(
                float(incident["service_demand_min"]) for incident in incidents
            ),
            "harm_curve_type": _categorical(
                incident["harm_curve"]["type"] for incident in incidents
            ),
            "harm_grace_min": _numeric_summary(
                float(incident["harm_curve"]["grace_min"])
                for incident in incidents
            ),
            "harm_slope": _numeric_summary(
                float(incident["harm_curve"]["slope"]) for incident in incidents
            ),
            "harm_capacity_penalty": _numeric_summary(
                float(incident["harm_curve"]["capacity_penalty"])
                for incident in incidents
            ),
        },
    }


def _seed_summary(record: dict[str, Any]) -> dict[str, Any]:
    summary = _group_summary([record])
    scope = summary["scope"]
    duplicate = summary["duplicates"]
    confidence = summary["confidence_truth_overlap"]
    reports = int(scope["n_reports"])
    missing = summary["missingness"]["observable"]
    return {
        "seed": int(record["seed"]),
        "split": str(record["split"]),
        "counts": {
            "incidents": int(scope["n_incidents"]),
            "reports": reports,
            "linked_reports": int(scope["n_linked_reports"]),
            "unlinked_reports": int(scope["n_unlinked_reports"]),
            "real_reports": int(confidence["truth_counts"]["real"]),
            "fake_reports": int(confidence["truth_counts"]["fake"]),
            "exact_duplicate_reports": int(duplicate["exact"]["report_count"]),
            "near_duplicate_reports": int(duplicate["near"]["report_count"]),
        },
        "rates": {
            "unlinked": float(scope["unlinked_report_rate"]),
            "fake": float(confidence["truth_counts"]["fake_rate"]),
            "exact_duplicate": float(duplicate["exact"]["report_rate"]),
            "near_duplicate": float(duplicate["near"]["report_rate"]),
            "low_confidence": _rate(
                confidence["truth_by_confidence_band"]["real"]["low_count"]
                + confidence["truth_by_confidence_band"]["fake"]["low_count"],
                reports,
            ),
            "has_image": _rate(
                sum(
                    1
                    for report in record["data"]["reports"]
                    if report["has_image"]
                ),
                reports,
            ),
            "measurement_missing": {
                field: float(missing[field]["missing_rate"])
                for field in MEASUREMENT_FIELDS
            },
        },
        "reports_per_incident": summary["reports_per_incident"],
        "population_overlap_rate": summary["membership_overlap"][
            "incident_population_reuse_rate"
        ],
    }


def build_distribution_report(
    bundle_dir: str | Path,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a complete deterministic report from a frozen candidate bundle."""
    bundle = Path(bundle_dir)
    records, manifest, manifest_sha256 = _load_records(bundle, manifest)
    splits = sorted(
        {str(record["split"]) for record in records},
        key=lambda value: (SPLIT_ORDER.get(value, 99), value),
    )
    families = sorted(
        {
            str(incident["scenario_family"])
            for record in records
            for incident in record["data"]["incidents"]
        }
    )

    confidence = DEFAULT_CONFIG.confidence
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "purpose": "method-agnostic descriptive profile of frozen candidate data",
        "analysis_unit": {
            "latent_truth": "physical_incident",
            "observation": "report",
            "seed_summary": "generated_dataset",
        },
        "scope_policy": {
            "method_agnostic": True,
            "contains_method_performance_metrics": False,
            "contains_scientific_endpoints": False,
            "test_split_use": "descriptive_data_freeze_only",
            "test_split_available_to_tuning": False,
            "acceptance_depends_on_preferred_method": False,
        },
        "source": {
            "dataset_manifest_schema_version": manifest.get("schema_version"),
            "dataset_schema_version": manifest.get("dataset_schema_version"),
            "generator_version": manifest.get("generator_version"),
            "dataset_manifest_sha256": manifest_sha256,
            "generator_sha256": manifest.get("generator_sha256"),
            "schema_sha256": manifest.get("schema_sha256"),
            "seed_manifest_sha256": manifest.get("seed_manifest_sha256"),
            "data_spec_sha256": manifest.get("data_spec_sha256"),
            "n_datasets": len(records),
        },
        "definitions": {
            "numeric_summary": (
                "finite observations; R-7 linear quantiles; MAD is median "
                "absolute deviation from the median"
            ),
            "measurement_missingness": (
                "membership in observable missing_fields before locked zero imputation"
            ),
            "reported_measurement_views": (
                "after_locked_imputation is the inference-visible distribution; "
                "observed_only excludes reports whose missing_fields mask names "
                "that measurement"
            ),
            "population_reuse_rate": (
                "1 - unique represented members / member occurrences, per incident"
            ),
            "pairwise_jaccard": "intersection / union for report membership sets",
            "pairwise_overlap_coefficient": (
                "intersection / smaller set size; empty smaller sets excluded"
            ),
            "context_dispersion": (
                "absolute report F/E deviation from its incident report median"
            ),
            "confidence": {
                "formula": "sigmoid(b0 + b1*has_image + b2*log1p(unique_corroborating_payloads))",
                "b0": confidence.b0,
                "b1": confidence.b1,
                "b2": confidence.b2,
                "corroboration_radius_m": confidence.corrob_radius_m,
                "corroboration_window_min": confidence.corrob_window_min,
                "exact_payload_multiplicity_counts_as_corroboration": False,
                "descriptive_low_high_cut": CONFIDENCE_BAND_CUT,
            },
        },
        "overall": _group_summary(records),
        "by_split": {
            split: _group_summary(
                [record for record in records if record["split"] == split]
            )
            for split in splits
        },
        "by_incident_family": {
            family: _group_summary(records, family=family) for family in families
        },
        "by_split_and_incident_family": {
            split: {
                family: _group_summary(
                    [record for record in records if record["split"] == split],
                    family=family,
                )
                for family in families
            }
            for split in splits
        },
        "per_seed_counts_and_rates": [
            _seed_summary(record) for record in records
        ],
    }
    return report


def write_distribution_report(
    bundle_dir: str | Path,
    output_path: str | Path,
    manifest: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    """Write the report exclusively and return it with its SHA-256."""
    report = build_distribution_report(bundle_dir, manifest)
    payload = canonical_json_bytes(report)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(payload)
    return report, sha256_bytes(payload)


__all__ = [
    "REPORT_SCHEMA_VERSION",
    "build_distribution_report",
    "write_distribution_report",
]
