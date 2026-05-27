from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

import networkx as nx
from community import community_louvain


@dataclass(frozen=True)
class Report:
    report_id: str
    created_at: datetime
    lat: float
    lng: float
    image_label: str
    text_label: str
    urgency_score: float
    province: str
    name: str
    phone: str
    network_mode: str
    sync_status: str


def parse_timestamp(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def label_similarity(left: Report, right: Report) -> float:
    if left.text_label == "irrelevant" or right.text_label == "irrelevant":
        return 0.0
    if left.text_label == right.text_label and left.image_label == right.image_label:
        return 1.0
    if {left.text_label, right.text_label} <= {"urgent_rescue", "need_supplies"}:
        return 0.75
    if {left.text_label, right.text_label} <= {"need_supplies", "safe_update"}:
        return 0.40
    if "high" in {left.image_label, right.image_label}:
        return 0.80
    return 0.25


def edge_weight(left: Report, right: Report) -> float:
    distance_km = haversine_km(left.lat, left.lng, right.lat, right.lng)
    time_hours = abs((left.created_at - right.created_at).total_seconds()) / 3600.0

    if distance_km > 1.0 or time_hours > 2.0:
        return 0.0

    spatial = math.exp(-distance_km / 1.0)
    temporal = math.exp(-time_hours / 2.0)
    similarity = label_similarity(left, right)
    urgency = min(left.urgency_score, right.urgency_score)

    return round(0.35 * spatial + 0.25 * temporal + 0.20 * similarity + 0.20 * urgency, 6)


def build_reports(raw_rows: list[dict]) -> list[Report]:
    return [
        Report(
            report_id=str(row["report_id"]),
            created_at=parse_timestamp(row["created_at"]),
            lat=float(row["lat"]),
            lng=float(row["lng"]),
            image_label=row["image_label"],
            text_label=row["text_label"],
            urgency_score=float(row["urgency_score"]),
            province=row["province"],
            name=row["name"],
            phone=row["phone"],
            network_mode=row["network_mode"],
            sync_status=row["sync_status"],
        )
        for row in raw_rows
    ]


def build_graph(reports: list[Report]) -> nx.Graph:
    graph = nx.Graph()
    for report in reports:
        graph.add_node(
            report.report_id,
            created_at=report.created_at.isoformat(),
            lat=report.lat,
            lng=report.lng,
            image_label=report.image_label,
            text_label=report.text_label,
            urgency_score=report.urgency_score,
            province=report.province,
            name=report.name,
            phone=report.phone,
            network_mode=report.network_mode,
            sync_status=report.sync_status,
        )

    for index, left in enumerate(reports):
        for right in reports[index + 1 :]:
            weight = edge_weight(left, right)
            if weight > 0:
                graph.add_edge(left.report_id, right.report_id, weight=weight)

    return graph


def run_louvain(raw_rows: list[dict]) -> dict:
    reports = build_reports(raw_rows)
    graph = build_graph(reports)
    if graph.number_of_nodes() == 0:
        return {
            "nodes": 0,
            "edges": 0,
            "communities": [],
            "modularity": 0.0,
            "partition": {},
            "graph": {"nodes": [], "edges": []},
        }

    partition = community_louvain.best_partition(graph, weight="weight", random_state=42)
    modularity = community_louvain.modularity(partition, graph, weight="weight") if graph.number_of_edges() > 0 else 0.0

    communities: dict[int, list[dict]] = {}
    for report in reports:
        community_id = int(partition.get(report.report_id, 0))
        communities.setdefault(community_id, []).append(
            {
                "report_id": report.report_id,
                "created_at": report.created_at.isoformat(),
                "province": report.province,
                "name": report.name,
                "phone": report.phone,
                "lat": report.lat,
                "lng": report.lng,
                "image_label": report.image_label,
                "text_label": report.text_label,
                "urgency_score": report.urgency_score,
                "network_mode": report.network_mode,
                "sync_status": report.sync_status,
            }
        )

    community_payload = []
    for community_id, members in sorted(communities.items(), key=lambda item: item[0]):
        report_count = len(members)
        center_lat = sum(item["lat"] for item in members) / report_count
        center_lng = sum(item["lng"] for item in members) / report_count
        time_window_start = min(item["created_at"] for item in members)
        time_window_end = max(item["created_at"] for item in members)
        max_urgency = max(item["urgency_score"] for item in members)

        community_payload.append(
            {
                "community_id": community_id,
                "report_count": report_count,
                "center_lat": round(center_lat, 6),
                "center_lng": round(center_lng, 6),
                "time_window_start": time_window_start,
                "time_window_end": time_window_end,
                "max_urgency_score": max_urgency,
                "members": members,
            }
        )

    graph_payload = {
        "nodes": [
            {
                "report_id": node_id,
                **data,
            }
            for node_id, data in graph.nodes(data=True)
        ],
        "edges": [
            {
                "source": source,
                "target": target,
                "weight": data.get("weight", 0.0),
            }
            for source, target, data in graph.edges(data=True)
        ],
    }

    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "communities": community_payload,
        "modularity": round(modularity, 6),
        "partition": partition,
        "graph": graph_payload,
    }
