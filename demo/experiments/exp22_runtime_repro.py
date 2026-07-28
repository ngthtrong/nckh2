"""Experiment 22: reproducible runtime, memory, packet, and spatial audit.

The benchmark uses development seeds only.  Each measured repeat runs in a
fresh child process so Linux ``ru_maxrss`` has an unambiguous per-repeat scope.
Thread pools are limited to one and CPU affinity is attempted and recorded.
If affinity cannot be pinned, the output explicitly makes no one-core claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import statistics
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

import numpy as np
from threadpoolctl import threadpool_info, threadpool_limits

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from demo.data.generate import candidate_inference_events
from demo.experiments.protocol import load_tuning_protocol
from demo.pipeline.attributes import Event, compute_confidence
from demo.pipeline.clustering import run_louvain
from demo.pipeline.config import DEFAULT_CONFIG
from demo.pipeline.spatial_weighting import (
    build_product_graph_spatial,
    partitions_equivalent,
)
from demo.pipeline.weighting import build_weight_matrix_vec, sparsify


SCHEMA_VERSION = "runtime-repro-v1"
WARMUP_REPEATS = 1
MEASURED_REPEATS = 5
DEVELOPMENT_BATCH_COUNTS = (1, 2, 4)
DEFAULT_GATE1_LOCK = REPOSITORY_ROOT / "revision" / "gate1-lock.json"
THREAD_ENVIRONMENT_KEYS = (
    "BLIS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


def _compressed_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def packet_payload(event: Event) -> dict[str, Any]:
    """Return the declared application payload using computed confidence."""

    timestamp = event.created_at
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("packet timestamp must be timezone-aware")
    if not 0.0 <= event.confidence <= 1.0:
        raise ValueError("computed confidence must lie in [0,1]")
    return {
        "C": round(float(event.confidence), 6),
        "E": float(event.urgency),
        "F": float(event.flood),
        "M": sorted(event.missing_fields),
        "N": int(event.n_trapped),
        "V": float(event.vulnerability),
        "id": event.event_id,
        "img": bool(event.has_image),
        "lat": round(float(event.lat), 7),
        "lng": round(float(event.lng), 7),
        "province": event.province,
        "source": event.source_type,
        "t": int(timestamp.astimezone(timezone.utc).timestamp()),
    }


def packet_size_summary(events: Sequence[Event]) -> dict[str, Any]:
    """Measure exact UTF-8 bytes and state deliberately excluded overhead."""

    if not events:
        raise ValueError("packet summary requires at least one event")
    sizes = sorted(len(_compressed_json_bytes(packet_payload(event))) for event in events)
    return {
        "schema": {
            "encoding": "UTF-8 JSON",
            "json": "sorted keys, compact separators, no NaN",
            "fields": [
                "id",
                "lat",
                "lng",
                "t",
                "F",
                "E",
                "N",
                "V",
                "C",
                "img",
                "source",
                "province",
                "M",
            ],
            "confidence": "computed by demo.pipeline.attributes.compute_confidence",
        },
        "n_packets": len(sizes),
        "min_bytes": sizes[0],
        "median_bytes": float(statistics.median(sizes)),
        "max_bytes": sizes[-1],
        "excluded_protocol_overhead": [
            "transport framing",
            "HTTP or MQTT headers",
            "TLS records",
            "authentication tokens",
            "retransmission and link-layer overhead",
        ],
        "scope": "application payload only; not an end-to-end network packet claim",
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_frozen_root(
    dataset_root: Path,
    gate1_lock_path: Path,
) -> dict[str, Any]:
    try:
        lock = json.loads(gate1_lock_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ValueError("a valid Gate-1 lock is required") from exc
    if (
        not isinstance(lock, dict)
        or lock.get("gate") != "Gate 1"
        or lock.get("status") != "locked"
    ):
        raise ValueError("Gate-1 lock is not in locked state")
    manifest_path = dataset_root / "manifest.json"
    expected = lock.get("data_contract", {}).get("dataset_manifest_sha256")
    actual = _sha256(manifest_path)
    if not isinstance(expected, str) or actual != expected:
        raise ValueError("frozen dataset manifest does not match Gate-1 lock")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("frozen dataset manifest is invalid JSON") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("entries"), list):
        raise ValueError("frozen dataset manifest has no entries")
    return manifest


def _verified_dataset_path(
    dataset_root: Path,
    manifest: dict[str, Any],
    *,
    stage: str,
    seed: int,
) -> Path:
    matches = [
        entry
        for entry in manifest["entries"]
        if isinstance(entry, dict)
        and entry.get("split") == stage
        and entry.get("seed") == seed
    ]
    if len(matches) != 1:
        raise ValueError(f"frozen manifest identity mismatch for {stage}/{seed}")
    relative = matches[0].get("path")
    expected = matches[0].get("sha256")
    required_relative = f"{stage}/seed_{seed}.json"
    if relative != required_relative or not isinstance(expected, str):
        raise ValueError(f"frozen manifest path mismatch for {stage}/{seed}")
    path = dataset_root / required_relative
    if _sha256(path) != expected:
        raise ValueError(f"frozen dataset checksum mismatch for {stage}/{seed}")
    return path


def _development_events(
    batch_count: int,
    *,
    dataset_root: Path,
    gate1_lock_path: Path,
) -> tuple[list[Event], list[int]]:
    protocol = load_tuning_protocol()
    if isinstance(batch_count, bool) or not 1 <= batch_count <= len(
        protocol.development_seeds
    ):
        raise ValueError("invalid development batch count")
    manifest = _validate_frozen_root(dataset_root, gate1_lock_path)
    selected = list(protocol.development_seeds[:batch_count])
    events: list[Event] = []
    for seed in selected:
        events.extend(
            candidate_inference_events(
                _verified_dataset_path(
                    dataset_root,
                    manifest,
                    stage="development",
                    seed=seed,
                )
            )
        )
    return events, selected


@contextmanager
def _runtime_limits() -> Iterator[dict[str, Any]]:
    """Limit native thread pools and attempt one-logical-CPU affinity."""

    original_affinity: set[int] | None = None
    pinned_cpu: int | None = None
    affinity_error: str | None = None
    try:
        if hasattr(os, "sched_getaffinity") and hasattr(os, "sched_setaffinity"):
            original_affinity = set(os.sched_getaffinity(0))
            if original_affinity:
                pinned_cpu = min(original_affinity)
                os.sched_setaffinity(0, {pinned_cpu})
    except OSError as exc:
        affinity_error = f"{type(exc).__name__}: {exc}"
        pinned_cpu = None

    try:
        with threadpool_limits(limits=1):
            pools = threadpool_info()
            yield {
                "thread_limit": 1,
                "threadpools": pools,
                "cpu_affinity_pinned": pinned_cpu is not None,
                "pinned_logical_cpu": pinned_cpu,
                "affinity_error": affinity_error,
                "one_core_claim_eligible": (
                    pinned_cpu is not None
                    and all(int(pool.get("num_threads", 0)) == 1 for pool in pools)
                ),
            }
    finally:
        if original_affinity is not None:
            try:
                os.sched_setaffinity(0, original_affinity)
            except OSError:
                pass


def _timed(function):
    started = time.perf_counter()
    value = function()
    return value, time.perf_counter() - started


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Linux reports KiB; macOS reports bytes.
    return value if sys.platform == "darwin" else value * 1024


def benchmark_once(
    batch_count: int,
    *,
    dataset_root: Path,
    gate1_lock_path: Path = DEFAULT_GATE1_LOCK,
) -> dict[str, Any]:
    """Run one isolated dense/spatial comparison."""

    events, seeds = _development_events(
        batch_count,
        dataset_root=dataset_root,
        gate1_lock_path=gate1_lock_path,
    )
    params = DEFAULT_CONFIG.weight
    with _runtime_limits() as runtime:
        dense_raw, dense_build_s = _timed(
            lambda: build_weight_matrix_vec(events, params, mode="gating")
        )
        dense_graph, dense_sparsify_s = _timed(lambda: sparsify(dense_raw, params))
        dense_labels, dense_cluster_s = _timed(
            lambda: run_louvain(
                dense_graph,
                DEFAULT_CONFIG.cluster.resolution,
                DEFAULT_CONFIG.cluster.random_state,
            )
        )
        spatial, spatial_build_s = _timed(
            lambda: build_product_graph_spatial(events, params)
        )
        spatial_labels, spatial_cluster_s = _timed(
            lambda: run_louvain(
                spatial.matrix,
                DEFAULT_CONFIG.cluster.resolution,
                DEFAULT_CONFIG.cluster.random_state,
            )
        )
        max_abs_difference = (
            float(np.max(np.abs(dense_graph - spatial.matrix)))
            if dense_graph.size
            else 0.0
        )

    return {
        "development_seeds": seeds,
        "n_events": len(events),
        "runtime_limits": runtime,
        "dense": {
            "build_s": dense_build_s,
            "sparsify_s": dense_sparsify_s,
            "cluster_s": dense_cluster_s,
            "total_s": dense_build_s + dense_sparsify_s + dense_cluster_s,
            "retained_edges": int(np.count_nonzero(np.triu(dense_graph, 1))),
        },
        "spatial": {
            "build_and_sparsify_s": spatial_build_s,
            "cluster_s": spatial_cluster_s,
            "total_s": spatial_build_s + spatial_cluster_s,
            "total_pairs": spatial.total_pairs,
            "candidate_pairs": spatial.candidate_pairs,
            "candidate_fraction": spatial.candidate_fraction,
            "retained_edges": spatial.retained_edges,
            "matrix_storage": "dense O(n^2) compatibility matrix",
        },
        "equivalence": {
            "max_abs_matrix_difference": max_abs_difference,
            "matrix_tolerance": 1e-9,
            "matrix_within_tolerance": max_abs_difference <= 1e-9,
            "labels_equal_up_to_permutation": partitions_equivalent(
                dense_labels,
                spatial_labels,
            ),
        },
        "peak_rss_bytes": _peak_rss_bytes(),
        "peak_rss_scope": "whole isolated worker, including imports and both matrices",
    }


def _distribution(values: Sequence[float | int]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "min": float(np.min(array)),
        "median": float(np.median(array)),
        "iqr": float(np.percentile(array, 75) - np.percentile(array, 25)),
        "max": float(np.max(array)),
    }


def summarize_repeats(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) != MEASURED_REPEATS:
        raise ValueError(f"expected {MEASURED_REPEATS} measured repeats")
    reference = rows[0]
    for row in rows[1:]:
        if (
            row["development_seeds"] != reference["development_seeds"]
            or row["n_events"] != reference["n_events"]
        ):
            raise ValueError("repeat inputs changed")
    matrices_within_tolerance = all(
        row["equivalence"]["matrix_within_tolerance"] for row in rows
    )
    edge_counts_equal = all(
        row["dense"]["retained_edges"] == row["spatial"]["retained_edges"]
        for row in rows
    )
    labels_equal = all(
        row["equivalence"]["labels_equal_up_to_permutation"] for row in rows
    )
    return {
        "development_seeds": reference["development_seeds"],
        "n_events": reference["n_events"],
        "measured_repeats": len(rows),
        "dense_total_s": _distribution([row["dense"]["total_s"] for row in rows]),
        "spatial_total_s": _distribution(
            [row["spatial"]["total_s"] for row in rows]
        ),
        "peak_rss_bytes": _distribution([row["peak_rss_bytes"] for row in rows]),
        "retained_edges": {
            "dense": sorted({row["dense"]["retained_edges"] for row in rows}),
            "spatial": sorted({row["spatial"]["retained_edges"] for row in rows}),
        },
        "candidate_pairs": sorted({row["spatial"]["candidate_pairs"] for row in rows}),
        "equivalence": {
            "max_abs_matrix_difference": max(
                row["equivalence"]["max_abs_matrix_difference"] for row in rows
            ),
            "all_matrices_within_1e_9": matrices_within_tolerance,
            "all_edge_counts_equal": edge_counts_equal,
            "all_labels_equal_up_to_permutation": labels_equal,
            "exact_equivalence_pass": (
                matrices_within_tolerance and edge_counts_equal and labels_equal
            ),
        },
        "runtime_limits": [row["runtime_limits"] for row in rows],
        "raw_repeats": list(rows),
    }


def _worker_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in THREAD_ENVIRONMENT_KEYS:
        environment[key] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _invoke_worker(
    batch_count: int,
    *,
    dataset_root: Path,
    gate1_lock_path: Path,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            "--development-batches",
            str(batch_count),
            "--dataset-root",
            str(dataset_root),
            "--gate1-lock",
            str(gate1_lock_path),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_worker_environment(),
    )
    return json.loads(completed.stdout)


def _exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(_compressed_json_bytes(value))
        stream.write(b"\n")


def run_benchmark(
    dataset_root: Path,
    *,
    gate1_lock_path: Path = DEFAULT_GATE1_LOCK,
) -> dict[str, Any]:
    protocol = load_tuning_protocol()
    manifest = _validate_frozen_root(dataset_root, gate1_lock_path)
    packet_seed = protocol.development_seeds[0]
    packet_events = candidate_inference_events(
        _verified_dataset_path(
            dataset_root,
            manifest,
            stage="development",
            seed=packet_seed,
        )
    )
    compute_confidence(packet_events, DEFAULT_CONFIG.confidence)

    sizes: list[dict[str, Any]] = []
    for batch_count in DEVELOPMENT_BATCH_COUNTS:
        for _ in range(WARMUP_REPEATS):
            _invoke_worker(
                batch_count,
                dataset_root=dataset_root,
                gate1_lock_path=gate1_lock_path,
            )
        measured = [
            _invoke_worker(
                batch_count,
                dataset_root=dataset_root,
                gate1_lock_path=gate1_lock_path,
            )
            for _ in range(MEASURED_REPEATS)
        ]
        sizes.append(summarize_repeats(measured))

    all_equivalent = all(
        row["equivalence"]["exact_equivalence_pass"] for row in sizes
    )
    all_one_core = all(
        limit["one_core_claim_eligible"]
        for row in sizes
        for limit in row["runtime_limits"]
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "purpose": "development-only runtime and representation-equivalence audit",
        "seed_stage": "development",
        "test_seed_access": False,
        "inputs": {
            "gate1_lock_sha256": _sha256(gate1_lock_path),
            "dataset_manifest_sha256": _sha256(dataset_root / "manifest.json"),
            "protocol_sha256": protocol.protocol_sha256,
            "seed_manifest_sha256": protocol.seed_manifest_sha256,
            "metric_contract_sha256": protocol.metric_contract_sha256,
        },
        "benchmark_contract": {
            "warmup_repeats": WARMUP_REPEATS,
            "measured_repeats": MEASURED_REPEATS,
            "thread_limit": 1,
            "cpu_affinity_attempted": True,
            "one_core_claim_eligible": all_one_core,
            "timing_summary": "median and IQR over isolated measured workers",
        },
        "spatial_conclusion": {
            "exact_equivalence_pass": all_equivalent,
            "candidate_pruning_implemented": True,
            "fully_sparse_memory_implemented": False,
            "allowed_claim": (
                "exact geographic candidate pruning with dense compatibility storage"
                if all_equivalent
                else "spatial implementation failed equivalence; scalability is future work"
            ),
        },
        "sizes": sizes,
        "packet": packet_size_summary(packet_events),
    }


def _parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--development-batches", type=int)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--gate1-lock", type=Path, default=DEFAULT_GATE1_LOCK)
    parser.add_argument("--output", type=Path)
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parse_args(arguments)
    if args.worker:
        if args.development_batches is None:
            raise SystemExit("--worker requires --development-batches")
        print(_compressed_json_bytes(benchmark_once(
            args.development_batches,
            dataset_root=args.dataset_root,
            gate1_lock_path=args.gate1_lock,
        )).decode())
        return 0

    result = run_benchmark(
        args.dataset_root,
        gate1_lock_path=args.gate1_lock,
    )
    output = args.output
    if output is None:
        tables_directory = os.environ.get("DEMO_TABLES_DIR")
        if not tables_directory:
            raise SystemExit(
                "DEMO_TABLES_DIR is required; run through the immutable candidate runner"
            )
        output = Path(tables_directory) / "exp22_runtime_repro.json"
    _exclusive_write(output, result)
    print(json.dumps({
        "output": str(output),
        "n_sizes": len(result["sizes"]),
        "equivalence": result["spatial_conclusion"]["exact_equivalence_pass"],
        "one_core_claim_eligible": result["benchmark_contract"][
            "one_core_claim_eligible"
        ],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
