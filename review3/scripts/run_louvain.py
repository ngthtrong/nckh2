from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import datetime

import networkx as nx
from community import community_louvain
from sqlalchemy import create_engine, text


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(ROOT, 'data', 'review3.sqlite')}")


@dataclass(frozen=True)
class Report:
    report_id: str
    created_at: datetime
    lat: float
    lng: float
    image_label: str
    text_label: str
    urgency_score: float


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def normalize_time_delta_hours(created_a: datetime, created_b: datetime) -> float:
    return abs((created_a - created_b).total_seconds()) / 3600.0


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
    time_hours = normalize_time_delta_hours(left.created_at, right.created_at)

    if distance_km > 1.0 or time_hours > 2.0:
        return 0.0

    spatial = math.exp(-distance_km / 1.0)
    temporal = math.exp(-time_hours / 2.0)
    similarity = label_similarity(left, right)
    urgency = min(left.urgency_score, right.urgency_score)

    return round(0.35 * spatial + 0.25 * temporal + 0.20 * similarity + 0.20 * urgency, 6)


def load_reports(engine) -> list[Report]:
    query = text(
        """
        SELECT report_id, created_at, lat, lng, image_label, text_label, urgency_score
        FROM rescue_reports
        ORDER BY created_at ASC
        """
    )
    with engine.begin() as conn:
        rows = conn.execute(query).mappings().all()

    def parse_timestamp(value):
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    return [
        Report(
            report_id=str(row["report_id"]),
            created_at=parse_timestamp(row["created_at"]),
            lat=float(row["lat"]),
            lng=float(row["lng"]),
            image_label=row["image_label"],
            text_label=row["text_label"],
            urgency_score=float(row["urgency_score"]),
        )
        for row in rows
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
        )

    for index, left in enumerate(reports):
        for right in reports[index + 1 :]:
            weight = edge_weight(left, right)
            if weight > 0:
                graph.add_edge(left.report_id, right.report_id, weight=weight)

    return graph


def ensure_output_tables(engine) -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS rescue_communities (
        community_id INTEGER PRIMARY KEY,
        report_count INTEGER NOT NULL,
        center_lat DOUBLE PRECISION NOT NULL,
        center_lng DOUBLE PRECISION NOT NULL,
        max_urgency_score DOUBLE PRECISION NOT NULL,
        time_window_start TIMESTAMPTZ NOT NULL,
        time_window_end TIMESTAMPTZ NOT NULL
    );

    CREATE TABLE IF NOT EXISTS rescue_report_communities (
        report_id UUID PRIMARY KEY,
        community_id INTEGER NOT NULL REFERENCES rescue_communities(community_id),
        weight DOUBLE PRECISION NOT NULL,
        created_at TIMESTAMPTZ NOT NULL
    );
    """

    with engine.begin() as conn:
        for statement in ddl.strip().split(";"):
            if statement.strip():
                conn.execute(text(statement))


def save_partition(engine, reports: list[Report], partition: dict[str, int]) -> None:
    communities = {}
    for report in reports:
        community_id = partition.get(report.report_id, 0)
        communities.setdefault(community_id, []).append(report)

    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text("TRUNCATE TABLE rescue_report_communities, rescue_communities;"))
        else:
            conn.execute(text("DELETE FROM rescue_report_communities;"))
            conn.execute(text("DELETE FROM rescue_communities;"))

        for community_id, members in communities.items():
            report_count = len(members)
            center_lat = sum(item.lat for item in members) / report_count
            center_lng = sum(item.lng for item in members) / report_count
            max_urgency = max(item.urgency_score for item in members)
            time_window_start = min(item.created_at for item in members)
            time_window_end = max(item.created_at for item in members)

            conn.execute(
                text(
                    """
                    INSERT INTO rescue_communities (
                        community_id, report_count, center_lat, center_lng, max_urgency_score, time_window_start, time_window_end
                    ) VALUES (
                        :community_id, :report_count, :center_lat, :center_lng, :max_urgency_score, :time_window_start, :time_window_end
                    )
                    """
                ),
                {
                    "community_id": int(community_id),
                    "report_count": report_count,
                    "center_lat": center_lat,
                    "center_lng": center_lng,
                    "max_urgency_score": max_urgency,
                    "time_window_start": time_window_start,
                    "time_window_end": time_window_end,
                },
            )

            for report in members:
                conn.execute(
                    text(
                        """
                        INSERT INTO rescue_report_communities (report_id, community_id, weight, created_at)
                        VALUES (:report_id, :community_id, :weight, :created_at)
                        """
                    ),
                    {
                        "report_id": report.report_id,
                        "community_id": int(community_id),
                        "weight": report.urgency_score,
                        "created_at": report.created_at,
                    },
                )


def main() -> None:
    engine = create_engine(DATABASE_URL)
    ensure_output_tables(engine)
    reports = load_reports(engine)
    if not reports:
        raise RuntimeError("No reports found. Run import_sample_data.py first.")

    graph = build_graph(reports)
    if graph.number_of_edges() == 0:
        raise RuntimeError("Graph has no edges. Check the spatial/time thresholds or the sample dataset.")

    partition = community_louvain.best_partition(graph, weight="weight", random_state=42)
    modularity = community_louvain.modularity(partition, graph, weight="weight")
    save_partition(engine, reports, partition)

    print(f"Nodes: {graph.number_of_nodes()}")
    print(f"Edges: {graph.number_of_edges()}")
    print(f"Communities: {len(set(partition.values()))}")
    print(f"Modularity: {modularity:.4f}")


if __name__ == "__main__":
    main()
