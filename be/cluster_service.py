"""Ánh xạ báo cáo đã lưu sang ReportV2 và chạy phân cụm + xếp hạng ưu tiên.

Thuật toán (rescue_core) giữ nguyên như bài báo. Module này chỉ chuyển dữ liệu
thực tế của app sang ký hiệu L/T/F/E/N/V của thuật toán. Các quy tắc suy diễn
dưới đây là heuristic vận hành, không phải kết quả đã được kiểm định:

- F (mức ngập, [0,1]): từ nhãn AI trên thiết bị: low=0.33, medium=0.66,
  high=1.0, non_flood=0.0; nhãn lạ thì để trống.
- E (khẩn cấp, [0,1]): theo từ khóa trong mô tả; không có mô tả thì để trống.
- N: số người mắc kẹt + bị thương.
- V: số nhóm yếu thế được chọn (0-4), là đại lượng thay thế cho số người yếu thế.
- provenance_quality: độ tin cậy của mô hình AI. Chỉ là một trường của payload
  (vào dấu vân tay bản trùng); điểm tin cậy Q_i dùng để xếp hạng được tính theo
  Eq. (1) của bài báo từ việc có ảnh và số báo cáo củng cố lân cận.

Nếu payload đã có sẵn trường của thuật toán (flood, urgency, vulnerability,
confidence, n_trapped — như bộ dữ liệu mô phỏng) thì dùng trực tiếp.
"""
from __future__ import annotations

import logging
import math
import re
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from rescue_core import GraphConfigV2, ReportV2, run_graph_clustering, score_clusters

logger = logging.getLogger("rescue_mock_server")

# Cấu hình product_cij_louvain đã chọn trong bài báo
# (src/results/cij_baseline_benchmark_results/selected_configs.json).
DEFAULT_GRAPH_CONFIG = GraphConfigV2(
    composition_operator="product",
    sigma_geo_m=700.0,
    tau_t=60.0,
    threshold_quantile=0.9,
    k=8,
    resolution=1.2,
)
RANDOM_STATE = 42

_FLOOD_BY_LABEL = {"low": 0.33, "medium": 0.66, "high": 1.0, "non_flood": 0.0}

# Mức khẩn cấp theo từ khóa (lấy mức cao nhất khớp được).
_URGENCY_KEYWORDS: Tuple[Tuple[float, Tuple[str, ...]], ...] = (
    (0.9, ("cứu với", "cứu gấp", "khẩn cấp", "nguy kịch", "đuối nước", "sắp chìm", "ngập nóc", "lên mái", "trên mái", "bất tỉnh")),
    (0.75, ("mắc kẹt", "bị kẹt", "bị thương", "cấp cứu", "nước dâng", "không thoát", "trẻ em", "người già", "mang thai")),
    (0.6, ("cần cứu", "cần hỗ trợ", "thiếu nước", "thiếu lương thực", "mất điện", "cô lập")),
)
_DEFAULT_URGENCY_WITH_TEXT = 0.4


def _flood_from_label(label: Optional[str]) -> Optional[float]:
    if not label:
        return None
    text = label.lower()
    if "non_flood" in text or "không ngập" in text:
        return _FLOOD_BY_LABEL["non_flood"]
    for key in ("high", "medium", "low"):
        if re.search(rf"\b{key}\b", text):
            return _FLOOD_BY_LABEL[key]
    return None


def _urgency_from_text(text: Optional[str]) -> Optional[float]:
    if not text or not text.strip():
        return None
    lowered = text.lower()
    for level, keywords in _URGENCY_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return level
    return _DEFAULT_URGENCY_WITH_TEXT


def _parse_time(value: Any) -> Optional[datetime]:
    if value is None or value == "":
        return None
    try:
        if isinstance(value, (int, float)) or str(value).isdigit():
            return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc)
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except (ValueError, OverflowError, OSError):
        return None


def _unit_or_none(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return min(1.0, max(0.0, number))


def _nonnegative_or_none(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0.0:
        return None
    return number


def to_report_v2(report: Dict[str, Any]) -> ReportV2:
    """Chuyển một báo cáo (dạng storage._row_to_dict) sang ReportV2."""
    payload = report.get("payload") or {}
    lat, lng = report.get("lat"), report.get("lng")
    location = (float(lat), float(lng)) if lat is not None and lng is not None else None

    event_time = _parse_time(report.get("createdAt")) or _parse_time(report.get("serverReceivedAt"))

    ai_tags = report.get("aiTags") or []
    top_tag = max(ai_tags, key=lambda tag: float(tag.get("confidence") or 0.0), default=None)

    if "flood" in payload:
        flood = _unit_or_none(payload.get("flood"))
    else:
        flood = _flood_from_label(top_tag.get("label") if top_tag else None)

    if "urgency" in payload:
        urgency = _unit_or_none(payload.get("urgency"))
    else:
        urgency = _urgency_from_text(report.get("description"))

    if "n_trapped" in payload:
        people = _nonnegative_or_none(payload.get("n_trapped"))
    else:
        people = float((report.get("trappedCount") or 0) + (report.get("injuredCount") or 0))

    if "vulnerability" in payload:
        vulnerability = _nonnegative_or_none(payload.get("vulnerability"))
    else:
        vulnerability = float(len(report.get("vulnerableGroups") or []))

    if "confidence" in payload:
        provenance = _unit_or_none(payload.get("confidence"))
    else:
        provenance = _unit_or_none(top_tag.get("confidence")) if top_tag else None

    has_image = bool(report.get("imageUrl")) or bool(payload.get("has_image"))

    return ReportV2(
        report_id=str(report["id"]),
        L=location,
        T=event_time,
        F=flood,
        E=urgency,
        N=people,
        V=vulnerability,
        provenance_quality=provenance,
        has_image=has_image,
    )


def _centroid(reports: Sequence[ReportV2]) -> Optional[Dict[str, float]]:
    located = [r.L for r in reports if r.L is not None]
    if not located:
        return None
    return {
        "lat": sum(point[0] for point in located) / len(located),
        "lng": sum(point[1] for point in located) / len(located),
    }


def compute_clusters(reports: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Phân cụm và xếp hạng ưu tiên các báo cáo chưa được giải quyết.

    Trả về cụm đã sắp xếp theo điểm ưu tiên giảm dần. Báo cáo thiếu vị trí hoặc
    thời gian được đưa vào ``review`` (cần người xem xét), đúng như thiết kế
    fail-closed của thuật toán.
    """
    active = [r for r in reports if r.get("status") != "resolved"]
    converted: List[ReportV2] = []
    invalid: List[Dict[str, str]] = []
    for report in active:
        try:
            converted.append(to_report_v2(report))
        except (ValueError, KeyError, TypeError) as exc:
            invalid.append({"id": str(report.get("id")), "error": str(exc)})

    if not converted:
        return {
            "config": _config_dict(),
            "clusters": [],
            "review": [],
            "invalid": invalid,
            "totalReports": len(active),
        }

    run = run_graph_clustering(converted, DEFAULT_GRAPH_CONFIG, random_state=RANDOM_STATE)
    priorities = score_clusters(converted, run.labels)
    by_id = {r.report_id: r for r in converted}

    clusters = []
    for cluster_id, priority in priorities.items():
        members = [by_id[report_id] for report_id in priority.report_ids]
        clusters.append({
            "clusterId": cluster_id,
            "reportIds": list(priority.report_ids),
            "size": len(priority.report_ids),
            "centroid": _centroid(members),
            "priority": priority.revised,
            "components": {
                "E": priority.e_agg,
                "F": priority.f_max,
                "N": priority.n_norm,
                "V": priority.v_agg,
                "provenance": priority.provenance_mean,
            },
            "exactDuplicatesRemoved": priority.exact_duplicates_removed,
            "nearDuplicatesCoalesced": priority.near_units_coalesced,
        })
    clusters.sort(key=lambda row: (-row["priority"], row["clusterId"]))
    for rank, row in enumerate(clusters, start=1):
        row["rank"] = rank

    return {
        "config": _config_dict(),
        "clusters": clusters,
        "review": list(run.review_report_ids),
        "invalid": invalid,
        "totalReports": len(active),
        "candidatePairs": run.candidate_pairs,
        "retainedEdges": run.retained_edges,
    }


def _config_dict() -> Dict[str, Any]:
    c = DEFAULT_GRAPH_CONFIG
    return {
        "method": "product_cij_louvain",
        "sigmaGeoM": c.sigma_geo_m,
        "tauT": c.tau_t,
        "thresholdQuantile": c.threshold_quantile,
        "k": c.k,
        "resolution": c.resolution,
        "randomState": RANDOM_STATE,
    }


class ClusterCache:
    """Chỉ tính lại khi tập báo cáo (id, trạng thái, thời điểm nhận) thay đổi."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._key: Optional[Tuple[Any, ...]] = None
        self._value: Optional[Dict[str, Any]] = None

    @staticmethod
    def _key_for(reports: Sequence[Dict[str, Any]]) -> Tuple[Any, ...]:
        return tuple(sorted(
            (str(r.get("id")), r.get("status"), r.get("statusVersion"), r.get("serverReceivedAt"))
            for r in reports
        ))

    def get(self, reports: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        key = self._key_for(reports)
        with self._lock:
            if key == self._key and self._value is not None:
                return self._value
        value = compute_clusters(reports)
        with self._lock:
            self._key, self._value = key, value
        logger.info(f"[CLUSTER] Tính lại: {len(value['clusters'])} cụm từ {value['totalReports']} báo cáo")
        return value
