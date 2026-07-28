"""Experiment 14: executable product-localization diagnostics.

The experiment writes only below the caller-provided ``--output-dir``. It does
not use ``common.save_table`` and therefore cannot overwrite the historical
``demo/results`` source of truth.

For every candidate dataset it reports:

* the structured threshold-domain state;
* retained-edge violations only when the product bound is finite;
* connectivity for every output community;
* measured hop diameter ``h``, ``h * r_theta``, actual geographic diameter,
  and tightness for each connected non-singleton community.

An empty or unbounded threshold region is reported but never counted as a
theorem check. See ``revision/math-spec.md``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import Sequence

import networkx as nx
import numpy as np

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from data.generate import candidate_inference_events, load_events  # noqa: E402
from pipeline.attributes import Event, haversine_m  # noqa: E402
from pipeline.clustering import matrix_to_graph, run_louvain  # noqa: E402
from pipeline.config import DEFAULT_CONFIG, WeightParams  # noqa: E402
from pipeline.weighting import (  # noqa: E402
    build_weight_matrix,
    product_distance_bound,
    sparsify,
)

DEFAULT_CANDIDATE = DEMO_ROOT / "data" / "dataset.json"
RESULT_NAME = "exp14_localization_bounds.json"
SELECTOR_NAME = "exp14_localization_selectors.json"
NUMERIC_TOLERANCE_M = 1e-6


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dataset_meta(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"candidate không phải JSON object: {path}")
    if isinstance(payload.get("events"), list):
        meta = payload.get("meta", {})
        return meta if isinstance(meta, dict) else {}
    if isinstance(payload.get("reports"), list) and isinstance(
        payload.get("incidents"), list
    ):
        return {
            "seed": payload.get("seed"),
            "split": payload.get("split"),
            "schema_version": payload.get("schema_version"),
        }
    raise ValueError(f"candidate không có events hoặc reports/incidents: {path}")


def resolve_candidates(candidate_paths: Sequence[str | Path] | None) -> list[Path]:
    """Resolve explicit dataset files or directories into a stable file list.

    An explicit file must be a valid dataset. For a directory, JSON files that
    do not contain an ``events`` array are ignored so run manifests can coexist
    with candidate datasets.
    """
    raw_paths = [Path(p) for p in candidate_paths] if candidate_paths else [
        DEFAULT_CANDIDATE
    ]
    resolved: list[Path] = []
    for raw in raw_paths:
        path = raw.expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"candidate không tồn tại: {path}")
        if path.is_file():
            _dataset_meta(path)
            resolved.append(path)
            continue
        if not path.is_dir():
            raise ValueError(f"candidate không phải file/thư mục: {path}")
        for child in sorted(path.rglob("*.json")):
            try:
                _dataset_meta(child)
            except (json.JSONDecodeError, OSError, ValueError):
                continue
            resolved.append(child.resolve())
    unique = list(dict.fromkeys(resolved))
    if not unique:
        raise ValueError("không tìm thấy candidate dataset JSON nào")
    return unique


def _geographic_diameter_m(events: list[Event], members: list[int]) -> float:
    diameter = 0.0
    for offset, i in enumerate(members):
        a = events[i]
        for j in members[offset + 1:]:
            b = events[j]
            diameter = max(diameter, haversine_m(a.lat, a.lng, b.lat, b.lng))
    return float(diameter)


def _retained_edge_diagnostics(
    events: list[Event], sparse_weights: np.ndarray, radius_m: float | None
) -> dict:
    rows = []
    for i, j in zip(*np.triu_indices(len(events), k=1)):
        if sparse_weights[i, j] <= 0.0:
            continue
        distance_m = haversine_m(
            events[i].lat, events[i].lng, events[j].lat, events[j].lng
        )
        rows.append(distance_m)

    if radius_m is None:
        return {
            "n_retained_edges": len(rows),
            "n_edge_bound_rows_counted": 0,
            "n_edge_bound_violations": None,
            "max_retained_edge_m": round(max(rows), 6) if rows else 0.0,
            "max_edge_tightness_ratio": None,
        }

    violations = [
        distance for distance in rows
        if distance >= radius_m + NUMERIC_TOLERANCE_M
    ]
    return {
        "n_retained_edges": len(rows),
        "n_edge_bound_rows_counted": len(rows),
        "n_edge_bound_violations": len(violations),
        "max_retained_edge_m": round(max(rows), 6) if rows else 0.0,
        "max_edge_tightness_ratio": (
            round(max(rows) / radius_m, 10) if rows and radius_m > 0.0 else None
        ),
    }


def analyze_candidate(
    candidate: str | Path,
    weight_params: WeightParams | None = None,
    resolution: float | None = None,
    random_state: int | None = None,
) -> tuple[dict, list[dict]]:
    """Analyze one candidate and return its per-seed summary and cluster rows."""
    path = Path(candidate).expanduser().resolve()
    meta = _dataset_meta(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    events = (
        candidate_inference_events(payload)
        if isinstance(payload.get("reports"), list)
        else load_events(path)
    )
    params = weight_params or DEFAULT_CONFIG.weight
    cluster_resolution = (
        DEFAULT_CONFIG.cluster.resolution if resolution is None else resolution
    )
    cluster_seed = (
        DEFAULT_CONFIG.cluster.random_state if random_state is None else random_state
    )

    bound = product_distance_bound(params, params.edge_threshold)
    weights = build_weight_matrix(events, params, mode="gating")
    sparse = sparsify(weights, params)
    labels = run_louvain(sparse, cluster_resolution, cluster_seed)
    graph = matrix_to_graph(sparse)

    groups: dict[int, list[int]] = {}
    for node, label in enumerate(labels):
        groups.setdefault(int(label), []).append(node)

    cluster_rows: list[dict] = []
    for cluster_id, members in sorted(groups.items()):
        subgraph = graph.subgraph(members)
        singleton = len(members) == 1
        connected = singleton or nx.is_connected(subgraph)
        if singleton:
            connectivity_status = "singleton"
            hop_diameter = 0
        elif connected:
            connectivity_status = "connected"
            hop_diameter = int(nx.diameter(subgraph))
        else:
            connectivity_status = "disconnected"
            hop_diameter = None

        actual_diameter_m = _geographic_diameter_m(events, members)
        bound_counted = bool(
            bound.domain_eligible and connected and not singleton
        )
        hop_bound_m = (
            float(hop_diameter * bound.radius_m)
            if bound_counted
            and hop_diameter is not None
            and bound.radius_m is not None
            else None
        )
        if hop_bound_m is not None and hop_bound_m > 0.0:
            tightness = actual_diameter_m / hop_bound_m
            bound_holds = actual_diameter_m < hop_bound_m + NUMERIC_TOLERANCE_M
        else:
            tightness = None
            bound_holds = None

        cluster_rows.append({
            "candidate": str(path),
            "seed": meta.get("seed"),
            "cluster_id": cluster_id,
            "n_members": len(members),
            "connectivity_status": connectivity_status,
            "connected": connected,
            "hop_diameter_h": hop_diameter,
            "r_theta_m": (
                round(bound.radius_m, 6) if bound.radius_m is not None else None
            ),
            "hop_bound_h_times_r_m": (
                round(hop_bound_m, 6) if hop_bound_m is not None else None
            ),
            "actual_geographic_diameter_m": round(actual_diameter_m, 6),
            "tightness_actual_over_h_r": (
                round(tightness, 10) if tightness is not None else None
            ),
            "bound_counted": bound_counted,
            "bound_holds": bound_holds,
        })

    radius = bound.radius_m if bound.domain_eligible else None
    edge_summary = _retained_edge_diagnostics(events, sparse, radius)
    counted_clusters = [row for row in cluster_rows if row["bound_counted"]]
    cluster_violations = [
        row for row in counted_clusters if row["bound_holds"] is False
    ]
    connected_non_singletons = [
        row for row in cluster_rows
        if row["connectivity_status"] == "connected"
    ]

    summary = {
        "candidate": str(path),
        "candidate_sha256": _sha256(path),
        "seed": meta.get("seed"),
        "n_events": len(events),
        "threshold_relation": "weight > theta",
        "theta": params.edge_threshold,
        "beta": params.beta,
        "gamma": params.gamma,
        "beta_gamma_sum_B": params.beta + params.gamma,
        "sigma_geo_m": params.sigma_geo_m,
        "knn": params.knn,
        "bound": asdict(bound),
        "domain_eligible": bound.domain_eligible,
        **edge_summary,
        "n_clusters": len(cluster_rows),
        "n_singletons": sum(
            row["connectivity_status"] == "singleton" for row in cluster_rows
        ),
        "n_connected_non_singleton_clusters": len(connected_non_singletons),
        "n_disconnected_clusters": sum(
            row["connectivity_status"] == "disconnected" for row in cluster_rows
        ),
        "n_cluster_bound_rows_counted": len(counted_clusters),
        "n_cluster_bound_violations": (
            len(cluster_violations) if bound.domain_eligible else None
        ),
        # This stays zero by construction and makes invalid-domain leakage
        # mechanically auditable in the artifact.
        "n_outside_domain_rows_counted": sum(
            row["bound_counted"] for row in cluster_rows
            if not bound.domain_eligible
        ) + (edge_summary["n_edge_bound_rows_counted"] if not bound.domain_eligible else 0),
        "max_hop_diameter_h": (
            max(row["hop_diameter_h"] for row in connected_non_singletons)
            if connected_non_singletons else 0
        ),
        "max_h_times_r_m": (
            round(max(row["hop_bound_h_times_r_m"] for row in counted_clusters), 6)
            if counted_clusters else None
        ),
        "max_actual_cluster_diameter_m": (
            round(
                max(row["actual_geographic_diameter_m"] for row in cluster_rows),
                6,
            )
            if cluster_rows else 0.0
        ),
        "max_cluster_tightness_ratio": (
            round(
                max(
                    row["tightness_actual_over_h_r"]
                    for row in counted_clusters
                    if row["tightness_actual_over_h_r"] is not None
                ),
                10,
            )
            if counted_clusters else None
        ),
    }
    return summary, cluster_rows


def run(
    candidates: Sequence[str | Path] | None,
    output_dir: str | Path,
    theta: float | None = None,
) -> tuple[Path, Path]:
    """Run diagnostics and write the result plus a stable selector contract."""
    candidate_files = resolve_candidates(candidates)
    params = DEFAULT_CONFIG.weight
    if theta is not None:
        params = replace(params, edge_threshold=float(theta))

    summaries: list[dict] = []
    clusters: list[dict] = []
    for candidate in candidate_files:
        summary, rows = analyze_candidate(candidate, weight_params=params)
        summaries.append(summary)
        clusters.extend(rows)

    payload = {
        "schema_version": 1,
        "experiment": "exp14_localization_bounds",
        "math_spec": "revision/math-spec.md",
        "numeric_tolerance_m": NUMERIC_TOLERANCE_M,
        "candidates": summaries,
        "clusters": clusters,
    }
    selectors = {
        "schema_version": 1,
        "source": RESULT_NAME,
        "selectors": {
            "per_seed_bound_state": "$.candidates[*].bound.status",
            "per_seed_r_theta_m": "$.candidates[*].bound.radius_m",
            "per_seed_edge_violations": "$.candidates[*].n_edge_bound_violations",
            "per_seed_outside_domain_rows_counted": (
                "$.candidates[*].n_outside_domain_rows_counted"
            ),
            "cluster_connectivity": "$.clusters[*].connectivity_status",
            "cluster_hop_diameter_h": "$.clusters[*].hop_diameter_h",
            "cluster_h_times_r_m": "$.clusters[*].hop_bound_h_times_r_m",
            "cluster_actual_diameter_m": (
                "$.clusters[*].actual_geographic_diameter_m"
            ),
            "cluster_tightness": "$.clusters[*].tightness_actual_over_h_r",
        },
    }

    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    result_path = destination / RESULT_NAME
    selector_path = destination / SELECTOR_NAME
    result_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    selector_path.write_text(
        json.dumps(selectors, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    return result_path, selector_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        "--candidate-path",
        dest="candidates",
        action="append",
        help=(
            "Dataset JSON hoặc thư mục candidate; có thể lặp lại. "
            f"Mặc định: {DEFAULT_CANDIDATE}"
        ),
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Thư mục artifact cô lập; không được là demo/results.",
    )
    parser.add_argument(
        "--theta",
        type=float,
        default=None,
        help="Ghi đè edge threshold để audit miền; mặc định dùng config hiện hành.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir).expanduser().resolve()
    historical_results = (DEMO_ROOT / "results").resolve()
    if output_dir == historical_results or historical_results in output_dir.parents:
        raise ValueError(
            "--output-dir không được nằm dưới demo/results; dùng candidate run directory"
        )
    result_path, selector_path = run(args.candidates, output_dir, theta=args.theta)
    print(f"[saved] {result_path}")
    print(f"[saved] {selector_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
