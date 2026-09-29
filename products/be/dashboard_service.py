"""Truy vấn, thống kê và xuất dữ liệu cho dashboard điều phối.

Tối đa vài nghìn báo cáo nên lọc/sắp xếp làm bằng Python trên kết quả của
``storage.get_reports`` (định dạng thời gian của báo cáo không đồng nhất: ISO có/không
múi giờ hoặc epoch ms). Giờ không kèm múi giờ được hiểu là UTC, giống rescue_core.
"""
from __future__ import annotations

import csv
import io
import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

import storage

MAX_PAGE_SIZE = 5000
SORT_FIELDS = ("createdAt", "firstReceivedAt", "people", "status")
STATUS_ORDER = {"processing": 0, "dispatched": 1, "resolved": 2, "cancelled": 3}


def to_utc(value: Any) -> Optional[datetime]:
    if value is None or value == "":
        return None
    try:
        if isinstance(value, (int, float)) or str(value).isdigit():
            return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc)
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
    except (ValueError, OverflowError, OSError):
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def event_time(report: Dict[str, Any]) -> Optional[datetime]:
    return to_utc(report.get("createdAt")) or to_utc(report.get("firstReceivedAt")) or to_utc(report.get("serverReceivedAt"))


def people(report: Dict[str, Any]) -> float:
    payload = report.get("payload") or {}
    if payload.get("n_trapped") is not None:
        try:
            return float(payload["n_trapped"])
        except (TypeError, ValueError):
            pass
    return float((report.get("trappedCount") or 0) + (report.get("injuredCount") or 0))


def top_label(report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    tags = report.get("aiTags") or []
    return max(tags, key=lambda t: float(t.get("confidence") or 0.0), default=None)


def _csv_set(value: Optional[str]) -> Optional[set]:
    if not value:
        return None
    items = {part.strip() for part in value.split(",") if part.strip()}
    return items or None


def filter_reports(reports: Iterable[Dict[str, Any]], params: Dict[str, Optional[str]]) -> List[Dict[str, Any]]:
    """Lọc theo tham số query (chuỗi); tham số rỗng bị bỏ qua."""
    statuses = _csv_set(params.get("status"))
    ids = _csv_set(params.get("ids"))
    q = (params.get("q") or "").strip().lower()
    since = to_utc(params.get("since"))
    until = to_utc(params.get("until"))
    has_location = params.get("hasLocation")
    team = params.get("teamId")
    send_modes = _csv_set(params.get("sendMode"))
    labels = _csv_set(params.get("label"))
    vulnerable = params.get("vulnerable")
    source = params.get("source")

    out = []
    for r in reports:
        if statuses and r.get("status") not in statuses:
            continue
        if ids and r.get("id") not in ids:
            continue
        if q and q not in str(r.get("id") or "").lower() and q not in str(r.get("description") or "").lower():
            continue
        if since or until:
            t = event_time(r)
            if t is None or (since and t < since) or (until and t > until):
                continue
        located = r.get("lat") is not None and r.get("lng") is not None
        if has_location == "true" and not located or has_location == "false" and located:
            continue
        if team:
            if team == "none" and r.get("assignedTeamId") is not None:
                continue
            if team != "none" and str(r.get("assignedTeamId")) != team:
                continue
        if send_modes and r.get("sendMode") not in send_modes:
            continue
        if labels:
            tag = top_label(r)
            if not tag or tag.get("label") not in labels:
                continue
        if vulnerable:
            groups = r.get("vulnerableGroups") or []
            if not groups or (vulnerable != "any" and vulnerable not in groups):
                continue
        if source and ((r.get("payload") or {}).get("source") or "app") != source:
            continue
        out.append(r)
    return out


def sort_reports(reports: List[Dict[str, Any]], sort: Optional[str]) -> List[Dict[str, Any]]:
    sort = sort or "-createdAt"
    descending = sort.startswith("-")
    field = sort.lstrip("-")
    if field not in SORT_FIELDS:
        raise ValueError(f"sort phải là một trong {', '.join(SORT_FIELDS)} (thêm '-' để giảm dần)")
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    keys = {
        "createdAt": lambda r: event_time(r) or epoch,
        "firstReceivedAt": lambda r: to_utc(r.get("firstReceivedAt")) or epoch,
        "people": people,
        "status": lambda r: STATUS_ORDER.get(r.get("status"), 9),
    }
    return sorted(reports, key=keys[field], reverse=descending)


def paginate(reports: List[Dict[str, Any]], page: int, page_size: int) -> Dict[str, Any]:
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    pages = max(1, math.ceil(len(reports) / page_size))
    page = max(1, min(page, pages))
    start = (page - 1) * page_size
    return {
        "total": len(reports),
        "page": page,
        "pageSize": page_size,
        "pages": pages,
        "reports": reports[start:start + page_size],
    }


# ---------------------------------------------------------------- Thống kê

def _summary(minutes: List[float]) -> Dict[str, Any]:
    if not minutes:
        return {"count": 0, "medianMin": None, "p90Min": None}
    values = sorted(minutes)

    def quantile(q: float) -> float:
        pos = (len(values) - 1) * q
        low, high = math.floor(pos), math.ceil(pos)
        return values[low] + (values[high] - values[low]) * (pos - low)

    return {"count": len(values), "medianMin": round(quantile(0.5), 1), "p90Min": round(quantile(0.9), 1)}


def compute_stats(
    reports: Sequence[Dict[str, Any]],
    events: Sequence[Dict[str, Any]],
    teams: Sequence[Dict[str, Any]],
    now: Optional[datetime] = None,
    hours: int = 24,
) -> Dict[str, Any]:
    """Chỉ số vận hành: số lượng theo trạng thái, thời gian phản ứng, lưu lượng theo giờ."""
    now = now or datetime.now(timezone.utc)
    counts = {status: 0 for status in STATUS_ORDER}
    send_modes: Dict[str, int] = {}
    close_reasons: Dict[str, int] = {}
    no_location = 0
    for r in reports:
        counts[r.get("status")] = counts.get(r.get("status"), 0) + 1
        mode = r.get("sendMode") or "unknown"
        send_modes[mode] = send_modes.get(mode, 0) + 1
        if r.get("closeReason"):
            close_reasons[r["closeReason"]] = close_reasons.get(r["closeReason"], 0) + 1
        if r.get("lat") is None or r.get("lng") is None:
            no_location += 1

    first_dispatch: Dict[str, datetime] = {}
    first_resolve: Dict[str, datetime] = {}
    resolved_times: List[datetime] = []
    resolved_by_team: Dict[str, int] = {}
    actors: Dict[str, int] = {}
    for e in events:
        if e["kind"] != "status":
            continue
        at = to_utc(e["at"])
        if at is None:
            continue
        if e.get("actor") and e.get("source") == "dashboard":
            actors[e["actor"]] = actors.get(e["actor"], 0) + 1
        if e["to"] == "dispatched":
            first_dispatch.setdefault(e["reportId"], at)
        elif e["to"] == "resolved":
            if e["reportId"] not in first_resolve:
                first_resolve[e["reportId"]] = at
                resolved_times.append(at)

    by_id = {r["id"]: r for r in reports}
    to_dispatch, dispatch_to_resolve, to_resolve = [], [], []
    for rid, r in by_id.items():
        received = to_utc(r.get("firstReceivedAt"))
        dispatched, resolved = first_dispatch.get(rid), first_resolve.get(rid)
        if received and dispatched and dispatched >= received:
            to_dispatch.append((dispatched - received).total_seconds() / 60)
        if dispatched and resolved and resolved >= dispatched:
            dispatch_to_resolve.append((resolved - dispatched).total_seconds() / 60)
        if received and resolved and resolved >= received:
            to_resolve.append((resolved - received).total_seconds() / 60)
        if resolved and r.get("assignedTeamId") is not None:
            key = str(r["assignedTeamId"])
            resolved_by_team[key] = resolved_by_team.get(key, 0) + 1

    start = (now - timedelta(hours=hours - 1)).replace(minute=0, second=0, microsecond=0)
    buckets = [{"hour": (start + timedelta(hours=i)).isoformat().replace("+00:00", "Z"), "received": 0, "resolved": 0}
               for i in range(hours)]

    def bucket(at: Optional[datetime]) -> Optional[Dict[str, Any]]:
        if at is None or at < start:
            return None
        index = int((at - start).total_seconds() // 3600)
        return buckets[index] if 0 <= index < hours else None

    for r in reports:
        b = bucket(to_utc(r.get("firstReceivedAt")))
        if b:
            b["received"] += 1
    for at in resolved_times:
        b = bucket(at)
        if b:
            b["resolved"] += 1

    return {
        "generatedAt": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "counts": {"total": len(reports), "noLocation": no_location, **counts},
        "response": {
            "receivedToDispatch": _summary(to_dispatch),
            "dispatchToResolve": _summary(dispatch_to_resolve),
            "receivedToResolve": _summary(to_resolve),
        },
        "hourly": buckets,
        "sendModes": send_modes,
        "closeReasons": close_reasons,
        "teams": [
            {"id": t["id"], "name": t["name"], "active": t["active"],
             "activeAssignments": t["activeAssignments"], "resolved": resolved_by_team.get(str(t["id"]), 0)}
            for t in teams
        ],
        "operators": sorted(({"actor": a, "actions": n} for a, n in actors.items()), key=lambda x: -x["actions"]),
    }


# ---------------------------------------------------------------- Xuất dữ liệu

CSV_COLUMNS = (
    "id", "createdAt", "firstReceivedAt", "status", "statusVersion", "closeReason",
    "lat", "lng", "locationSource", "people", "trappedCount", "injuredCount",
    "vulnerableGroups", "description", "aiLabel", "aiConfidence", "sendMode",
    "team", "clusterRank", "clusterPriority", "imageUrl", "source",
)


def _export_row(r: Dict[str, Any], teams: Dict[int, str], clusters: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    tag = top_label(r) or {}
    cluster = clusters.get(r["id"]) or {}
    return {
        "id": r["id"],
        "createdAt": r.get("createdAt"),
        "firstReceivedAt": r.get("firstReceivedAt"),
        "status": r.get("status"),
        "statusVersion": r.get("statusVersion"),
        "closeReason": storage.CLOSE_REASONS.get(r.get("closeReason") or "", r.get("closeReason")),
        "lat": r.get("lat"),
        "lng": r.get("lng"),
        "locationSource": r.get("locationSource"),
        "people": people(r),
        "trappedCount": r.get("trappedCount"),
        "injuredCount": r.get("injuredCount"),
        "vulnerableGroups": ", ".join(r.get("vulnerableGroups") or []),
        "description": r.get("description"),
        "aiLabel": tag.get("label"),
        "aiConfidence": tag.get("confidence"),
        "sendMode": r.get("sendMode"),
        "team": teams.get(r.get("assignedTeamId")),
        "clusterRank": cluster.get("rank"),
        "clusterPriority": round(cluster["priority"], 4) if cluster.get("priority") is not None else None,
        "imageUrl": r.get("imageUrl"),
        "source": (r.get("payload") or {}).get("source") or "app",
    }


def cluster_index(cluster_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {rid: c for c in cluster_data.get("clusters", []) for rid in c["reportIds"]}


def to_csv(reports: Sequence[Dict[str, Any]], teams: Dict[int, str], clusters: Dict[str, Dict[str, Any]]) -> str:
    buffer = io.StringIO()
    buffer.write("﻿")  # BOM để Excel đọc đúng tiếng Việt
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for r in reports:
        writer.writerow(_export_row(r, teams, clusters))
    return buffer.getvalue()


def to_geojson(reports: Sequence[Dict[str, Any]], teams: Dict[int, str], clusters: Dict[str, Dict[str, Any]]) -> str:
    features = []
    for r in reports:
        if r.get("lat") is None or r.get("lng") is None:
            continue
        props = _export_row(r, teams, clusters)
        props.pop("lat"), props.pop("lng")
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lng"], r["lat"]]},
            "properties": props,
        })
    return json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False)
