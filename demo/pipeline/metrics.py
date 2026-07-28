"""Clustering and operational-output metrics.

The operational metrics in this module deliberately keep the predicted noise
label out of the destination set.  A rejected report is one unresolved report,
not a member of a synthetic ``-1`` cluster.  Every public burden metric returns
an explicit numerator, denominator, rate, and a point-coverage record so a
caller cannot silently lose reports through ``zip`` truncation or filtering.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Any, Iterable, Sequence

import numpy as np
from sklearn.metrics import (
    adjusted_rand_score,
    normalized_mutual_info_score,
)

from .attributes import Event, haversine_m


class MetricInputError(ValueError):
    """Raised when metric inputs cannot support a complete, aligned audit."""


Label = int | str


@dataclass(frozen=True)
class ReviewPolicy:
    """Observable policy defining which operational units enter manual review.

    A destination is queued when it has too few supporting reports or its mean
    report confidence is below ``min_mean_confidence``.  Predicted-noise reports
    are never collapsed into a destination; when ``review_unclustered`` is true
    each is one queue item.
    """

    id: str
    min_destination_reports: int
    min_mean_confidence: float
    review_unclustered: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise MetricInputError("review policy id must be a non-empty string")
        if (
            isinstance(self.min_destination_reports, bool)
            or not isinstance(self.min_destination_reports, Integral)
            or self.min_destination_reports < 1
        ):
            raise MetricInputError(
                "min_destination_reports must be a positive integer"
            )
        threshold = self.min_mean_confidence
        if (
            isinstance(threshold, bool)
            or not isinstance(threshold, Real)
            or not math.isfinite(float(threshold))
            or not 0.0 <= float(threshold) <= 1.0
        ):
            raise MetricInputError(
                "min_mean_confidence must be finite and in [0, 1]"
            )
        if not isinstance(self.review_unclustered, bool):
            raise MetricInputError("review_unclustered must be boolean")


def _is_label(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        or isinstance(value, Integral)
        and not isinstance(value, bool)
    )


def _label_sequence(values: Sequence[Label] | Iterable[Label], name: str) -> list[Label]:
    if isinstance(values, (str, bytes)):
        raise MetricInputError(f"{name} must be a sequence of labels")
    try:
        result = list(values)
    except TypeError as exc:
        raise MetricInputError(f"{name} must be iterable") from exc
    for index, value in enumerate(result):
        if not _is_label(value):
            raise MetricInputError(
                f"{name}[{index}] must be a non-empty string or integer label"
            )
    return result


def _aligned_labels(
    predicted_labels: Sequence[Label] | Iterable[Label],
    incident_labels: Sequence[Label] | Iterable[Label],
) -> tuple[list[Label], list[Label]]:
    predicted = _label_sequence(predicted_labels, "predicted_labels")
    incidents = _label_sequence(incident_labels, "incident_labels")
    if len(predicted) != len(incidents):
        raise MetricInputError(
            "predicted_labels and incident_labels must have exactly equal length: "
            f"{len(predicted)} != {len(incidents)}"
        )
    return predicted, incidents


def _validate_sentinel(value: Label | None, name: str) -> None:
    if value is not None and not _is_label(value):
        raise MetricInputError(
            f"{name} must be None, a non-empty string, or an integer label"
        )


def _label_key(value: Label) -> str:
    """Encode label type as well as value for collision-free JSON detail keys."""

    if isinstance(value, str):
        return f"string:{value}"
    return f"integer:{int(value)}"


def _coverage(total: int, *, population_total: int | None = None) -> dict[str, Any]:
    population = total if population_total is None else population_total
    return {
        "points_total": total,
        "points_accounted": total,
        "point_coverage_rate": 1.0,
        "population_points_total": population,
        "population_points_accounted": population,
        "population_coverage_rate": 1.0,
        "complete": True,
    }


def _ratio_metric(
    metric: str,
    numerator: int | float,
    denominator: int,
    *,
    direction: str,
    coverage: dict[str, Any],
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(denominator, bool) or not isinstance(denominator, Integral):
        raise MetricInputError("metric denominator must be an integer")
    if denominator < 0:
        raise MetricInputError("metric denominator cannot be negative")
    numeric_numerator = float(numerator)
    if not math.isfinite(numeric_numerator) or numeric_numerator < 0.0:
        raise MetricInputError("metric numerator must be finite and non-negative")
    if numeric_numerator > denominator:
        raise MetricInputError(
            f"metric numerator exceeds denominator: {numerator} > {denominator}"
        )
    if direction not in {"higher", "lower"}:
        raise MetricInputError(f"unsupported metric direction: {direction!r}")
    return {
        "metric": metric,
        "direction": direction,
        "numerator": numerator,
        "denominator": int(denominator),
        "rate": (
            float(numeric_numerator / denominator) if denominator > 0 else None
        ),
        "coverage": coverage,
        "details": details or {},
    }


def _is_predicted_noise(label: Label, noise_label: Label | None) -> bool:
    return noise_label is not None and label == noise_label


def _is_ground_truth_noise(
    label: Label, ground_truth_noise_label: Label | None
) -> bool:
    return ground_truth_noise_label is not None and label == ground_truth_noise_label


def _operational_groups(
    predicted: Sequence[Label], noise_label: Label | None
) -> tuple[dict[Label, list[int]], list[int]]:
    groups: dict[Label, list[int]] = {}
    unclustered: list[int] = []
    for index, label in enumerate(predicted):
        if _is_predicted_noise(label, noise_label):
            unclustered.append(index)
        else:
            groups.setdefault(label, []).append(index)
    if noise_label is not None and noise_label in groups:
        raise AssertionError("predicted noise label entered destination groups")
    return groups, unclustered


def incident_split_loss(
    predicted_labels: Sequence[Label] | Iterable[Label],
    incident_labels: Sequence[Label] | Iterable[Label],
    *,
    noise_label: Label | None = -1,
    ground_truth_noise_label: Label | None = -1,
) -> dict[str, Any]:
    """Return the fraction of represented incidents split across output units.

    Operational destinations are predicted labels other than ``noise_label``.
    Each predicted-noise report is a distinct unresolved output unit; rejected
    reports are therefore never treated as one cluster.  An incident is split
    when its reports occupy more than one destination/unresolved unit.
    """

    _validate_sentinel(noise_label, "noise_label")
    _validate_sentinel(ground_truth_noise_label, "ground_truth_noise_label")
    predicted, incidents = _aligned_labels(predicted_labels, incident_labels)
    by_incident: dict[Label, list[int]] = {}
    n_truth_noise = 0
    for index, incident in enumerate(incidents):
        if _is_ground_truth_noise(incident, ground_truth_noise_label):
            n_truth_noise += 1
        else:
            by_incident.setdefault(incident, []).append(index)

    split_count = 0
    incident_unit_counts: dict[str, int] = {}
    all_unclustered = 0
    excess_units = 0
    for incident, indices in by_incident.items():
        units: set[tuple[str, object]] = set()
        for index in indices:
            label = predicted[index]
            if _is_predicted_noise(label, noise_label):
                units.add(("unclustered_report", index))
            else:
                units.add(("destination", label))
        unit_count = len(units)
        incident_unit_counts[_label_key(incident)] = unit_count
        split_count += int(unit_count > 1)
        excess_units += max(0, unit_count - 1)
        all_unclustered += int(
            bool(indices)
            and all(
                _is_predicted_noise(predicted[index], noise_label)
                for index in indices
            )
        )

    return _ratio_metric(
        "incident_split_loss",
        split_count,
        len(by_incident),
        direction="lower",
        coverage=_coverage(len(predicted), population_total=len(predicted) - n_truth_noise),
        details={
            "definition": "binary incident split across operational/unresolved units",
            "n_incident_reports": len(predicted) - n_truth_noise,
            "n_ground_truth_noise_reports_excluded": n_truth_noise,
            "n_incidents_all_reports_unclustered": all_unclustered,
            "excess_output_units": excess_units,
            "output_units_per_incident": incident_unit_counts,
        },
    )


def incident_merge_loss(
    predicted_labels: Sequence[Label] | Iterable[Label],
    incident_labels: Sequence[Label] | Iterable[Label],
    *,
    noise_label: Label | None = -1,
    ground_truth_noise_label: Label | None = -1,
) -> dict[str, Any]:
    """Return the fraction of emitted destinations containing >=2 incidents."""

    _validate_sentinel(noise_label, "noise_label")
    _validate_sentinel(ground_truth_noise_label, "ground_truth_noise_label")
    predicted, incidents = _aligned_labels(predicted_labels, incident_labels)
    groups, unclustered = _operational_groups(predicted, noise_label)
    merged = 0
    noise_only = 0
    incident_counts: dict[str, int] = {}
    for destination, indices in groups.items():
        present = {
            incidents[index]
            for index in indices
            if not _is_ground_truth_noise(
                incidents[index], ground_truth_noise_label
            )
        }
        incident_counts[_label_key(destination)] = len(present)
        merged += int(len(present) >= 2)
        noise_only += int(not present)

    return _ratio_metric(
        "incident_merge_loss",
        merged,
        len(groups),
        direction="lower",
        coverage=_coverage(len(predicted)),
        details={
            "definition": "destination contains reports from at least two incidents",
            "n_operational_destinations": len(groups),
            "n_noise_only_destinations": noise_only,
            "n_unclustered_reports": len(unclustered),
            "incident_count_per_destination": incident_counts,
        },
    )


def _noise_partition(
    predicted: Sequence[Label],
    incidents: Sequence[Label],
    *,
    noise_label: Label | None,
    ground_truth_noise_label: Label | None,
) -> dict[str, int]:
    groups, _ = _operational_groups(predicted, noise_label)
    destination_has_incident = {
        destination: any(
            not _is_ground_truth_noise(
                incidents[index], ground_truth_noise_label
            )
            for index in indices
        )
        for destination, indices in groups.items()
    }
    rejected = 0
    absorbed = 0
    assigned_to_noise_only_destination = 0
    total = 0
    for label, incident in zip(predicted, incidents, strict=True):
        if not _is_ground_truth_noise(incident, ground_truth_noise_label):
            continue
        total += 1
        if _is_predicted_noise(label, noise_label):
            rejected += 1
        elif destination_has_incident[label]:
            absorbed += 1
        else:
            assigned_to_noise_only_destination += 1
    if rejected + absorbed + assigned_to_noise_only_destination != total:
        raise AssertionError("noise outcome partition is incomplete")
    return {
        "total": total,
        "rejected": rejected,
        "absorbed": absorbed,
        "assigned_to_noise_only_destination": assigned_to_noise_only_destination,
    }


def noise_rejection_rate(
    predicted_labels: Sequence[Label] | Iterable[Label],
    incident_labels: Sequence[Label] | Iterable[Label],
    *,
    noise_label: Label | None = -1,
    ground_truth_noise_label: Label | None = -1,
) -> dict[str, Any]:
    """Return the fraction of ground-truth noise reports explicitly rejected."""

    _validate_sentinel(noise_label, "noise_label")
    _validate_sentinel(ground_truth_noise_label, "ground_truth_noise_label")
    predicted, incidents = _aligned_labels(predicted_labels, incident_labels)
    partition = _noise_partition(
        predicted,
        incidents,
        noise_label=noise_label,
        ground_truth_noise_label=ground_truth_noise_label,
    )
    return _ratio_metric(
        "noise_rejection_rate",
        partition["rejected"],
        partition["total"],
        direction="higher",
        coverage=_coverage(len(predicted), population_total=partition["total"]),
        details={
            **partition,
            "partition_complete": True,
            "noise_label_is_destination": False,
        },
    )


def noise_absorption_rate(
    predicted_labels: Sequence[Label] | Iterable[Label],
    incident_labels: Sequence[Label] | Iterable[Label],
    *,
    noise_label: Label | None = -1,
    ground_truth_noise_label: Label | None = -1,
) -> dict[str, Any]:
    """Return noise assigned to destinations that contain a true incident."""

    _validate_sentinel(noise_label, "noise_label")
    _validate_sentinel(ground_truth_noise_label, "ground_truth_noise_label")
    predicted, incidents = _aligned_labels(predicted_labels, incident_labels)
    partition = _noise_partition(
        predicted,
        incidents,
        noise_label=noise_label,
        ground_truth_noise_label=ground_truth_noise_label,
    )
    return _ratio_metric(
        "noise_absorption_rate",
        partition["absorbed"],
        partition["total"],
        direction="lower",
        coverage=_coverage(len(predicted), population_total=partition["total"]),
        details={
            **partition,
            "partition_complete": True,
            "noise_label_is_destination": False,
        },
    )


def false_operational_destinations(
    predicted_labels: Sequence[Label] | Iterable[Label],
    incident_labels: Sequence[Label] | Iterable[Label],
    *,
    noise_label: Label | None = -1,
    ground_truth_noise_label: Label | None = -1,
) -> dict[str, Any]:
    """Count emitted destinations containing only ground-truth noise reports."""

    _validate_sentinel(noise_label, "noise_label")
    _validate_sentinel(ground_truth_noise_label, "ground_truth_noise_label")
    predicted, incidents = _aligned_labels(predicted_labels, incident_labels)
    groups, unclustered = _operational_groups(predicted, noise_label)
    false_destinations = 0
    false_destination_reports = 0
    for indices in groups.values():
        if all(
            _is_ground_truth_noise(incidents[index], ground_truth_noise_label)
            for index in indices
        ):
            false_destinations += 1
            false_destination_reports += len(indices)
    result = _ratio_metric(
        "false_operational_destinations",
        false_destinations,
        len(groups),
        direction="lower",
        coverage=_coverage(len(predicted)),
        details={
            "unit": "destination_count",
            "n_operational_destinations": len(groups),
            "n_false_destination_reports": false_destination_reports,
            "n_unclustered_reports": len(unclustered),
            "noise_label_is_destination": False,
        },
    )
    result["count"] = false_destinations
    return result


def operator_review_burden(
    predicted_labels: Sequence[Label] | Iterable[Label],
    review_scores: Sequence[float] | Iterable[float],
    policy: ReviewPolicy,
    *,
    noise_label: Label | None = -1,
) -> dict[str, Any]:
    """Return manual-review queue size under one observable review policy."""

    if not isinstance(policy, ReviewPolicy):
        raise MetricInputError("policy must be a ReviewPolicy")
    _validate_sentinel(noise_label, "noise_label")
    predicted = _label_sequence(predicted_labels, "predicted_labels")
    if isinstance(review_scores, (str, bytes)):
        raise MetricInputError("review_scores must be a numeric sequence")
    try:
        scores = list(review_scores)
    except TypeError as exc:
        raise MetricInputError("review_scores must be iterable") from exc
    if len(scores) != len(predicted):
        raise MetricInputError(
            "review_scores and predicted_labels must have exactly equal length: "
            f"{len(scores)} != {len(predicted)}"
        )
    normalized_scores: list[float] = []
    for index, value in enumerate(scores):
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not math.isfinite(float(value))
            or not 0.0 <= float(value) <= 1.0
        ):
            raise MetricInputError(
                f"review_scores[{index}] must be finite and in [0, 1]"
            )
        normalized_scores.append(float(value))

    groups, unclustered = _operational_groups(predicted, noise_label)
    reviewed_destinations = 0
    reports_in_reviewed_destinations = 0
    destination_rows: list[dict[str, Any]] = []
    for destination, indices in groups.items():
        mean_score = float(np.mean([normalized_scores[index] for index in indices]))
        reasons: list[str] = []
        if len(indices) < policy.min_destination_reports:
            reasons.append("below_min_destination_reports")
        if mean_score < policy.min_mean_confidence:
            reasons.append("below_min_mean_confidence")
        queued = bool(reasons)
        reviewed_destinations += int(queued)
        if queued:
            reports_in_reviewed_destinations += len(indices)
        destination_rows.append(
            {
                "destination": str(destination),
                "n_reports": len(indices),
                "mean_review_score": mean_score,
                "queued": queued,
                "reasons": reasons,
            }
        )

    unclustered_reviews = len(unclustered) if policy.review_unclustered else 0
    queue_size = reviewed_destinations + unclustered_reviews
    decision_units = len(groups) + len(unclustered)
    reports_in_queue = reports_in_reviewed_destinations + unclustered_reviews
    result = _ratio_metric(
        "operator_review_burden",
        queue_size,
        decision_units,
        direction="lower",
        coverage=_coverage(len(predicted)),
        details={
            "unit": "review_queue_items",
            "policy": {
                "id": policy.id,
                "min_destination_reports": int(policy.min_destination_reports),
                "min_mean_confidence": float(policy.min_mean_confidence),
                "review_unclustered": policy.review_unclustered,
            },
            "n_operational_destinations": len(groups),
            "n_unclustered_reports": len(unclustered),
            "n_reviewed_destinations": reviewed_destinations,
            "n_unclustered_report_reviews": unclustered_reviews,
            "n_reports_represented_in_review_queue": reports_in_queue,
            "report_denominator": len(predicted),
            "report_rate": (
                float(reports_in_queue / len(predicted)) if predicted else None
            ),
            "destinations": destination_rows,
            "noise_label_is_destination": False,
        },
    )
    result["queue_size"] = queue_size
    return result


def evaluate_output_burden(
    predicted_labels: Sequence[Label] | Iterable[Label],
    incident_labels: Sequence[Label] | Iterable[Label],
    review_scores: Sequence[float] | Iterable[float],
    policies: Sequence[ReviewPolicy] | Iterable[ReviewPolicy],
    *,
    noise_label: Label | None = -1,
    ground_truth_noise_label: Label | None = -1,
) -> dict[str, Any]:
    """Evaluate every preregistered E3 endpoint with one aligned point audit."""

    predicted, incidents = _aligned_labels(predicted_labels, incident_labels)
    policy_list = list(policies)
    if not policy_list:
        raise MetricInputError("at least one review policy is required")
    if any(not isinstance(policy, ReviewPolicy) for policy in policy_list):
        raise MetricInputError("every policy must be a ReviewPolicy")
    policy_ids = [policy.id for policy in policy_list]
    if len(policy_ids) != len(set(policy_ids)):
        raise MetricInputError("review policy ids must be unique")
    if isinstance(review_scores, (str, bytes)):
        raise MetricInputError("review_scores must be a numeric sequence")
    try:
        reusable_review_scores = list(review_scores)
    except TypeError as exc:
        raise MetricInputError("review_scores must be iterable") from exc

    split = incident_split_loss(
        predicted,
        incidents,
        noise_label=noise_label,
        ground_truth_noise_label=ground_truth_noise_label,
    )
    merge = incident_merge_loss(
        predicted,
        incidents,
        noise_label=noise_label,
        ground_truth_noise_label=ground_truth_noise_label,
    )
    rejection = noise_rejection_rate(
        predicted,
        incidents,
        noise_label=noise_label,
        ground_truth_noise_label=ground_truth_noise_label,
    )
    absorption = noise_absorption_rate(
        predicted,
        incidents,
        noise_label=noise_label,
        ground_truth_noise_label=ground_truth_noise_label,
    )
    false_destinations = false_operational_destinations(
        predicted,
        incidents,
        noise_label=noise_label,
        ground_truth_noise_label=ground_truth_noise_label,
    )
    reviews = {
        policy.id: operator_review_burden(
            predicted,
            reusable_review_scores,
            policy,
            noise_label=noise_label,
        )
        for policy in policy_list
    }
    all_results = [
        split,
        merge,
        rejection,
        absorption,
        false_destinations,
        *reviews.values(),
    ]
    if any(
        metric["coverage"]["points_accounted"] != len(predicted)
        or metric["coverage"]["point_coverage_rate"] != 1.0
        for metric in all_results
    ):
        raise AssertionError("E3 metric coverage fell below 100%")
    return {
        "schema_version": "output-burden-metrics-v1",
        "n_points": len(predicted),
        "noise_label": noise_label,
        "ground_truth_noise_label": ground_truth_noise_label,
        "incident_split_loss": split,
        "incident_merge_loss": merge,
        "noise_rejection_rate": rejection,
        "noise_absorption_rate": absorption,
        "false_operational_destinations": false_destinations,
        "operator_review_burden": reviews,
        "coverage": _coverage(len(predicted)),
        "all_metrics_complete": True,
        "noise_label_is_destination": False,
    }


def cluster_quality(labels: list[int], gt: list[int]) -> dict[str, float]:
    """ARI và NMI so với nhãn ground-truth (bỏ qua các điểm nhiễu gt = -1)."""
    if len(labels) != len(gt):
        raise MetricInputError(
            f"labels and gt must have equal length: {len(labels)} != {len(gt)}"
        )
    pred = np.array(labels)
    truth = np.array(gt)
    mask = truth >= 0
    if mask.sum() == 0:
        return {"ari": 0.0, "nmi": 0.0, "n_eval": 0}
    return {
        "ari": round(float(adjusted_rand_score(truth[mask], pred[mask])), 4),
        "nmi": round(float(normalized_mutual_info_score(truth[mask], pred[mask])), 4),
        "n_eval": int(mask.sum()),
    }


def noise_handling(
    labels: list[int], gt: list[int], noise_label: int | None = -1
) -> dict[str, float]:
    """Cách phương pháp XỬ LÝ nhiễu — thông tin mà ARI/NMI che mất.

    `cluster_quality` chỉ chấm trên các điểm có nhãn (gt >= 0), nên một phương
    pháp hút hết điểm nhiễu (gt = -1) vào các cụm thật vẫn có thể đạt ARI = 1,0.
    Đó là ưu thế giả: về vận hành, nhiễu bị hút vào cụm sẽ kéo giãn cụm và làm
    sai lệch toạ độ điều phối.

    THÙNG NHIỄU (`noise_label`, mặc định -1): DBSCAN/HDBSCAN gán nhãn -1 cho
    "KHÔNG thuộc cụm nào". Nhóm đó KHÔNG phải một cụm, nên không được tính là
    nơi nhiễu "bị hấp thụ" — nếu tính, một phương pháp ném cả nhiễu lẫn vài
    điểm thật vào thùng -1 sẽ bị báo cáo sai thành "hấp thụ 100% nhiễu" trong
    khi thực tế nó không hấp thụ điểm nào. Đặt `noise_label=None` cho các thuật
    toán không sinh nhãn nhiễu (Louvain, Leiden, K-Means, Spectral,
    Agglomerative) — với chúng mọi nhãn đều là cụm thật.

    Trả về:
      - `noise_absorbed_pct`: % điểm nhiễu bị đặt vào một CỤM THẬT có ít nhất
        một điểm có nhãn (càng thấp càng tốt).
      - `contaminated_clusters`: số cụm thật chứa lẫn cả điểm thật và điểm nhiễu.
      - `purity_labeled`: tỉ lệ điểm trong các cụm "thật" thực sự có nhãn.
      - `n_unclustered`: số điểm nằm trong thùng nhiễu (chưa được gán cụm nào).
      - `labeled_dropped_to_noise`: số điểm CÓ NHÃN bị đẩy vào thùng nhiễu — lỗi
        đối ngẫu của hấp thụ. Một phương pháp có thể đạt hấp-thụ-nhiễu 0% bằng
        cách từ chối phân cụm phần lớn dữ liệu; cột này phơi bày cái giá đó.
    """
    if len(labels) != len(gt):
        raise MetricInputError(
            f"labels and gt must have equal length: {len(labels)} != {len(gt)}"
        )
    groups: dict[int, list[int]] = {}
    for lab, g in zip(labels, gt):
        groups.setdefault(lab, []).append(g)

    noise_bin = groups.pop(noise_label, []) if noise_label is not None else []

    n_noise = sum(1 for g in gt if g < 0)
    absorbed = 0
    contaminated = 0
    n_in_real = 0
    n_labeled_in_real = 0
    for members in groups.values():
        n_lab = sum(1 for g in members if g >= 0)
        n_noi = len(members) - n_lab
        if n_lab > 0:
            n_in_real += len(members)
            n_labeled_in_real += n_lab
            if n_noi > 0:
                absorbed += n_noi
                contaminated += 1
    return {
        "n_noise_points": n_noise,
        "noise_absorbed": absorbed,
        "noise_absorbed_pct": round(100.0 * absorbed / n_noise, 2) if n_noise else 0.0,
        "contaminated_clusters": contaminated,
        "purity_labeled": round(n_labeled_in_real / n_in_real, 4) if n_in_real else 0.0,
        "n_unclustered": len(noise_bin),
        "labeled_dropped_to_noise": sum(1 for g in noise_bin if g >= 0),
    }


def geographic_spread(
    events: list[Event],
    labels: list[int],
    noise_label: int | None = -1,
    gt_labels: list[int] | None = None,
) -> dict[str, float]:
    """Đường kính địa lý của cụm (km) — cụm gắn kết thì nhỏ.

    QUY ƯỚC BÁO CÁO CHÍNH (áp dụng NHƯ NHAU cho mọi phương pháp, xem Mục 5 của
    bài): chỉ số hình học chính là các cột `*_labeled`, tính TRÊN CÁC CỤM CHỨA ÍT
    NHẤT MỘT ĐIỂM CÓ NHÃN GROUND-TRUTH (gt >= 0). Lý do: các cụm gồm TOÀN điểm
    nhiễu không phải là nhóm mà phương pháp được yêu cầu phục hồi, nhưng chúng
    trải rộng khắp vùng (hàng trăm km) nên chi phối trung bình và làm một phương
    pháp bị đọc sai thành "trải cả tỉnh". Ví dụ đo được: HDBSCAN 20 cụm = 14 cụm
    có nhãn (TB 6,46 km) + 6 cụm toàn nhiễu (TB 147,22 km) => trung bình gộp
    48,69 km. Con số 48,69 km là artifact của quy ước đo, không phải chất lượng
    hình học. Chỉ số gộp và các cụm-toàn-nhiễu được báo cáo RIÊNG ở cột phụ.

    Cần truyền `gt_labels` (cùng thứ tự với `events`) để có các cột `*_labeled`;
    nếu không truyền, các cột đó bằng None và chỉ còn quy ước gộp cũ.

    Các cột gộp (giữ để tương thích ngược, đọc như tham khảo):
      - `mean_diameter_km`         : mọi cụm, singleton tính là 0 — THIÊN VỊ phân
        hoạch nhiều singleton, không dùng để so sánh.
      - `max_diameter_km`          : trường hợp xấu nhất.
      - `mean_diameter_km_multi`   : chỉ cụm có >= 2 thành viên.
      - `mean_diameter_km_weighted`: trung bình có trọng số theo số điểm.

    THÙNG NHIỄU (`noise_label`, mặc định -1): nhãn -1 của DBSCAN/HDBSCAN nghĩa là
    "không thuộc cụm nào", nên KHÔNG được tính như một cụm. Nếu tính, thùng nhiễu
    gom các điểm rải khắp vùng sẽ tạo ra một "cụm" đường kính hàng trăm km và
    chi phối cả `max_diameter_km` lẫn `mean_diameter_km_multi` — một artifact đo
    lường, không phải nhược điểm thật của thuật toán. Số điểm trong thùng được
    báo cáo riêng qua `n_unclustered`. Lưu ý: thùng nhiễu (nhãn -1 do thuật toán
    gán) khác với cụm-toàn-nhiễu (một cụm THẬT nhưng mọi thành viên có gt < 0).
    """
    if len(events) != len(labels):
        raise MetricInputError(
            f"events and labels must have equal length: {len(events)} != {len(labels)}"
        )
    if gt_labels is not None and len(events) != len(gt_labels):
        raise MetricInputError(
            "events and gt_labels must have equal length: "
            f"{len(events)} != {len(gt_labels)}"
        )
    groups: dict[int, list[Event]] = {}
    gt_groups: dict[int, list[int]] = {}
    gt_seq = list(gt_labels) if gt_labels is not None else [None] * len(events)
    for ev, lab, g in zip(events, labels, gt_seq):
        groups.setdefault(lab, []).append(ev)
        gt_groups.setdefault(lab, []).append(g)

    noise_bin = groups.pop(noise_label, []) if noise_label is not None else []
    if noise_label is not None:
        gt_groups.pop(noise_label, None)

    def _diameter_km(members: list[Event]) -> float:
        max_d = 0.0
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                d = haversine_m(
                    members[i].lat, members[i].lng, members[j].lat, members[j].lng
                )
                max_d = max(max_d, d)
        return max_d / 1000.0

    diameters = []        # mọi cụm (singleton = 0.0)
    diam_multi = []       # chỉ cụm >= 2 thành viên
    sizes_multi = []      # số điểm tương ứng, cho bản có trọng số
    diam_labeled = []     # cụm chứa >= 1 điểm có nhãn GT
    diam_noise_only = []  # cụm gồm TOÀN điểm nhiễu
    n_singletons = 0
    for lab, members in groups.items():
        diam = 0.0 if len(members) < 2 else _diameter_km(members)
        diameters.append(diam)
        if len(members) < 2:
            n_singletons += 1
        else:
            diam_multi.append(diam)
            sizes_multi.append(len(members))
        if gt_labels is not None:
            has_label = any(g is not None and g >= 0 for g in gt_groups[lab])
            (diam_labeled if has_label else diam_noise_only).append(diam)

    if diam_multi:
        w = np.array(sizes_multi, dtype=float)
        mean_multi = float(np.mean(diam_multi))
        mean_weighted = float(np.average(diam_multi, weights=w))
    else:
        mean_multi = 0.0
        mean_weighted = 0.0

    out: dict[str, float] = {
        "mean_diameter_km": round(float(np.mean(diameters)), 4) if diameters else 0.0,
        "mean_diameter_km_multi": round(mean_multi, 4),
        "mean_diameter_km_weighted": round(mean_weighted, 4),
        "max_diameter_km": round(float(np.max(diameters)), 4) if diameters else 0.0,
        "n_clusters": len(groups),
        "n_singletons": n_singletons,
        "n_clusters_multi": len(diam_multi),
        "n_unclustered": len(noise_bin),
    }
    if gt_labels is None:
        out.update({
            "n_clusters_labeled": None,
            "n_clusters_noise_only": None,
            "mean_diameter_km_labeled": None,
            "max_diameter_km_labeled": None,
            "mean_diameter_km_noise_only": None,
            "frac_labeled_clusters_under_1p5km": None,
        })
        return out

    n_lab_cl = len(diam_labeled)
    out.update({
        "n_clusters_labeled": n_lab_cl,
        "n_clusters_noise_only": len(diam_noise_only),
        "mean_diameter_km_labeled": (
            round(float(np.mean(diam_labeled)), 4) if diam_labeled else 0.0),
        "max_diameter_km_labeled": (
            round(float(np.max(diam_labeled)), 4) if diam_labeled else 0.0),
        "mean_diameter_km_noise_only": (
            round(float(np.mean(diam_noise_only)), 4) if diam_noise_only else 0.0),
        "frac_labeled_clusters_under_1p5km": (
            round(sum(1 for d in diam_labeled if d < 1.5) / n_lab_cl, 4)
            if n_lab_cl else 0.0),
    })
    return out


__all__ = [
    "MetricInputError",
    "ReviewPolicy",
    "cluster_quality",
    "evaluate_output_burden",
    "false_operational_destinations",
    "geographic_spread",
    "incident_merge_loss",
    "incident_split_loss",
    "noise_absorption_rate",
    "noise_handling",
    "noise_rejection_rate",
    "operator_review_burden",
]
