"""Calibration, freeze, and single-release confirmation orchestration for v2."""
from __future__ import annotations

import gzip
import hashlib
import importlib.metadata
import json
import math
import os
import sys
import tempfile
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from demo.v2.analysis import ConfirmationAnalysisSpec, analyze_confirmation_payload
from demo.v2.clustering import (
    ClusterRunV2,
    GraphConfigV2,
    clustering_endpoints,
    run_graph_clustering,
    run_hdbscan_v2,
    run_st_dbscan_v2,
)
from demo.v2.contracts import ReportV2
from demo.v2.dispatch import (
    POLICY_IDS,
    ResourceScenarioV2,
    build_jobs,
    evaluate_schedule,
    schedule_hash,
    schedule_jobs,
)
from demo.v2.evaluation import (
    STRESS_FAMILIES_V2,
    evaluate_predicted_priority,
    evaluate_priority_stress,
    score_predicted_priority,
)
from demo.v2.generator import (
    ACTIVE_CONFIRMATION_SEEDS_V2,
    BASE_TIME,
    SNAPSHOT_CUTOFF_MIN_V2,
    GeneratedDatasetV2,
    canonical_json_bytes,
    generate_dataset,
    observation_snapshot,
)
from demo.v2.priority import report_provenance_scores, score_clusters
from demo.v2.protocol import ExpandedConfiguration, ProtocolV2, file_sha256, load_protocol


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RESULT_DIRECTORY = REPOSITORY_ROOT / "revision" / "v2" / "results"
CALIBRATION_ROWS = RESULT_DIRECTORY / "calibration_rows.json.gz"
CALIBRATION_SELECTION = RESULT_DIRECTORY / "calibration_selection.json"
EXECUTION_FREEZE = RESULT_DIRECTORY / "execution_freeze.json"
CONFIRMATION_RESULT = RESULT_DIRECTORY / "confirmation_result.json.gz"
CONFIRMATION_ANALYSIS = RESULT_DIRECTORY / "confirmation_analysis.json"
CONFIRMATION_MANIFEST = RESULT_DIRECTORY / "confirmation_manifest.json"
ORACLE_DIAGNOSTIC = RESULT_DIRECTORY / "oracle_dispatch_diagnostic.json.gz"
IMPLEMENTATION_FILES = (
    "demo/v2/clustering.py",
    "demo/v2/analysis.py",
    "demo/v2/contracts.py",
    "demo/v2/dedup.py",
    "demo/v2/dispatch.py",
    "demo/v2/evaluation.py",
    "demo/v2/experiment.py",
    "demo/v2/generator.py",
    "demo/v2/graph.py",
    "demo/v2/priority.py",
    "demo/v2/protocol.py",
    "demo/v2/similarity.py",
    "demo/v2/statistics.py",
    "pyproject.toml",
    "requirements.lock",
)
RUNTIME_DISTRIBUTIONS = (
    "networkx",
    "numpy",
    "python-louvain",
    "scikit-learn",
    "scipy",
)
STRESS_FAMILIES = STRESS_FAMILIES_V2


class ExperimentV2Error(RuntimeError):
    """Raised when execution would violate a frozen experiment gate."""


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_json(path: Path, payload: Any) -> None:
    _atomic_write(path, canonical_json_bytes(payload))


def _exclusive_write_json(path: Path, payload: Any) -> None:
    """Create an immutable execution claim without an existence-check race."""

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ExperimentV2Error(
            f"immutable execution state already exists; overwrite/retry is forbidden: {path}"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json_bytes(payload))
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        # The claim is deliberately retained even if writing it fails.  Once
        # O_EXCL succeeds, fail closed instead of permitting another release.
        raise


def _transition_confirmation_state(path: Path, payload: Mapping[str, Any]) -> None:
    current = _read_json(path)
    if not isinstance(current, dict) or current.get("status") != "started":
        raise ExperimentV2Error("confirmation state is terminal and immutable")
    if payload.get("status") not in {"failed", "accepted"}:
        raise ExperimentV2Error("confirmation may transition only to failed or accepted")
    for field in (
        "protocol_sha256",
        "implementation_sha256",
        "execution_freeze_sha256",
        "selection_sha256",
        "confirmation_master_seeds",
        "confirmation_master_seeds_sha256",
        "result_file",
        "analysis_file",
        "oracle_diagnostic_file",
    ):
        if payload.get(field) != current.get(field):
            raise ExperimentV2Error(f"confirmation transition changed frozen field: {field}")
    if payload.get("status") == "accepted":
        for field in (
            "result_sha256",
            "analysis_sha256",
            "oracle_diagnostic_sha256",
        ):
            digest = payload.get(field)
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise ExperimentV2Error(
                    f"accepted confirmation lacks a valid artifact digest: {field}"
                )
    _write_json(path, payload)


def _write_json_gzip(path: Path, payload: Any) -> None:
    encoded = canonical_json_bytes(payload)
    _atomic_write(path, gzip.compress(encoded, compresslevel=9, mtime=0))


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_gzip(path: Path) -> Any:
    return json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))


def _payload_sha256(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _path_label(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPOSITORY_ROOT.resolve()))
    except ValueError:
        return str(resolved)


def implementation_sha256() -> str:
    rows: dict[str, str] = {}
    for relative in IMPLEMENTATION_FILES:
        path = REPOSITORY_ROOT / relative
        if not path.is_file():
            raise ExperimentV2Error(f"implementation file missing: {relative}")
        rows[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    runtime = {
        "python_implementation": sys.implementation.name,
        "python_version": ".".join(str(value) for value in sys.version_info[:3]),
        "python_cache_tag": sys.implementation.cache_tag,
        "distributions": {
            name: importlib.metadata.version(name)
            for name in RUNTIME_DISTRIBUTIONS
        },
    }
    return hashlib.sha256(
        canonical_json_bytes({"files": rows, "runtime": runtime})
    ).hexdigest()


def _configuration_payload(configuration: ExpandedConfiguration) -> dict[str, Any]:
    return {
        "configuration_id": configuration.configuration_id,
        "method_id": configuration.method_id,
        "pair_id": configuration.pair_id,
        "operator": configuration.operator,
        "parameters": dict(configuration.parameters),
    }


def all_configurations(protocol: ProtocolV2) -> tuple[ExpandedConfiguration, ...]:
    return (
        *protocol.paired_configurations,
        *protocol.independent_configurations["grid.st_dbscan"],
        *protocol.independent_configurations["grid.hdbscan"],
    )


def _graph_config(configuration: ExpandedConfiguration) -> GraphConfigV2:
    parameters = configuration.parameters
    return GraphConfigV2(
        composition_operator=str(configuration.operator),  # type: ignore[arg-type]
        sigma_geo_m=float(parameters["sigma_geo_m"]),
        tau_t=float(parameters["tau_t_min"]),
        threshold_quantile=float(parameters["threshold_quantile"]),
        k=int(parameters.get("k", parameters.get("knn"))),
        resolution=float(parameters["resolution"]),
        tau_F=float(parameters["tau_F"]),
        tau_E=float(parameters["tau_E"]),
        alpha=float(parameters["alpha"]),
        beta=float(parameters["beta"]),
        gamma=float(parameters["gamma"]),
    )


def execute_configuration(
    reports: Sequence[ReportV2],
    configuration: ExpandedConfiguration,
    *,
    seed: int,
) -> ClusterRunV2:
    parameters = configuration.parameters
    if configuration.method_id in {"method.product_louvain", "method.additive_louvain"}:
        return run_graph_clustering(reports, _graph_config(configuration), random_state=seed)
    if configuration.method_id == "method.st_dbscan":
        return run_st_dbscan_v2(
            reports,
            spatial_eps_m=float(parameters["spatial_eps_m"]),
            temporal_eps_min=float(parameters["temporal_eps_min"]),
            min_samples=int(parameters["min_samples"]),
        )
    if configuration.method_id == "method.hdbscan_geo_time":
        return run_hdbscan_v2(
            reports,
            min_cluster_size=int(parameters["min_cluster_size"]),
            min_samples=int(parameters["min_samples"]),
            spatial_scale_m=float(parameters["spatial_scale_m"]),
            temporal_scale_min=float(parameters["temporal_scale_min"]),
        )
    raise ExperimentV2Error(f"unimplemented method: {configuration.method_id}")


def run_calibration(
    protocol: ProtocolV2 | None = None,
    *,
    output_path: Path = CALIBRATION_ROWS,
) -> dict[str, Any]:
    """Execute every registered configuration on all 20 calibration seeds."""

    protocol = protocol or load_protocol()
    configurations = all_configurations(protocol)
    rows: list[dict[str, Any]] = []
    for seed in protocol.calibration_seeds:
        dataset = observation_snapshot(generate_dataset(seed, "id"))
        provenance = report_provenance_scores(dataset.reports)
        for configuration in configurations:
            base = {
                "configuration_id": configuration.configuration_id,
                "method": configuration.method_id,
                "operator": configuration.operator,
                "seed": seed,
                "regime": "id",
                "n_reports": len(dataset.reports),
            }
            try:
                run = execute_configuration(dataset.reports, configuration, seed=seed)
                metrics = clustering_endpoints(
                    dataset.reports,
                    dataset.report_truth,
                    run,
                    provenance_scores=provenance,
                )
                rows.append({**base, "status": "success", "metrics": metrics})
            except Exception as exc:  # failures are retained, never silently dropped
                rows.append(
                    {
                        **base,
                        "status": "failure",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
    expected = len(configurations) * len(protocol.calibration_seeds)
    if len(rows) != expected:
        raise ExperimentV2Error(f"calibration coverage error: {len(rows)} != {expected}")
    payload = {
        "schema_version": "v2.calibration-rows.1",
        "protocol_sha256": protocol.bundle_sha256,
        "implementation_sha256": implementation_sha256(),
        "n_configurations": len(configurations),
        "n_seeds": len(protocol.calibration_seeds),
        "n_rows": len(rows),
        "rows": rows,
    }
    _write_json_gzip(output_path, payload)
    return payload


def _mean(rows: Sequence[Mapping[str, Any]], endpoint: str) -> float:
    return float(np.mean([float(row["metrics"][endpoint]) for row in rows]))


def _assert_exact_composite_keys(
    name: str,
    rows: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
    expected: set[tuple[Any, ...]],
) -> None:
    observed: list[tuple[Any, ...]] = []
    for index, row in enumerate(rows):
        try:
            observed.append(tuple(row[field] for field in fields))
        except KeyError as exc:
            raise ExperimentV2Error(
                f"{name} row {index} lacks coverage field {exc.args[0]}"
            ) from exc
    observed_set = set(observed)
    if len(observed) != len(observed_set):
        raise ExperimentV2Error(f"{name} coverage contains duplicate composite keys")
    if observed_set != expected:
        missing = sorted(expected - observed_set, key=repr)
        extra = sorted(observed_set - expected, key=repr)
        raise ExperimentV2Error(
            f"{name} coverage mismatch: missing={missing[:3]}, extra={extra[:3]}"
        )


def _validate_calibration_payload(
    payload: Mapping[str, Any],
    protocol: ProtocolV2,
    *,
    current_implementation_sha256: str,
) -> tuple[dict[str, ExpandedConfiguration], dict[str, list[Mapping[str, Any]]]]:
    if payload.get("schema_version") != "v2.calibration-rows.1":
        raise ExperimentV2Error("unsupported calibration-row schema")
    if payload.get("protocol_sha256") != protocol.bundle_sha256:
        raise ExperimentV2Error("calibration rows do not match current protocol")
    if payload.get("implementation_sha256") != current_implementation_sha256:
        raise ExperimentV2Error("calibration rows do not match current implementation")

    configurations = all_configurations(protocol)
    configuration_map = {
        configuration.configuration_id: configuration
        for configuration in configurations
    }
    if len(configuration_map) != len(configurations):
        raise ExperimentV2Error("protocol contains duplicate configuration ids")
    seeds = tuple(protocol.calibration_seeds)
    expected_keys = {
        (configuration_id, seed)
        for configuration_id in configuration_map
        for seed in seeds
    }
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ExperimentV2Error("calibration rows must be a list")
    if (
        payload.get("n_configurations") != len(configurations)
        or payload.get("n_seeds") != len(seeds)
    ):
        raise ExperimentV2Error("calibration configuration/seed header is not exact")

    required_metrics = (
        "ari_linked",
        "false_destinations_per_100_reports",
        "noise_rejection",
        "review_items_per_100_reports",
    )
    by_configuration: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    observed_keys: set[tuple[str, int]] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ExperimentV2Error(f"calibration row {index} is not an object")
        configuration_id = row.get("configuration_id")
        seed = row.get("seed")
        if not isinstance(configuration_id, str) or isinstance(seed, bool) or not isinstance(seed, int):
            raise ExperimentV2Error(f"calibration row {index} has an invalid key")
        key = (configuration_id, seed)
        if key in observed_keys:
            raise ExperimentV2Error(
                f"duplicate calibration configuration×seed key: {configuration_id}×{seed}"
            )
        observed_keys.add(key)
        if key not in expected_keys:
            raise ExperimentV2Error(
                f"unexpected calibration configuration×seed key: {configuration_id}×{seed}"
            )
        configuration = configuration_map[configuration_id]
        if (
            row.get("method") != configuration.method_id
            or row.get("operator") != configuration.operator
            or row.get("regime") != "id"
        ):
            raise ExperimentV2Error(f"calibration row {index} contradicts its configuration")
        status = row.get("status")
        if status not in {"success", "failure"}:
            raise ExperimentV2Error(f"calibration row {index} has an invalid status")
        if status == "success":
            metrics = row.get("metrics")
            if not isinstance(metrics, Mapping):
                raise ExperimentV2Error(f"successful calibration row {index} lacks metrics")
            for endpoint in required_metrics:
                value = metrics.get(endpoint)
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                ):
                    raise ExperimentV2Error(
                        f"successful calibration row {index} has invalid {endpoint}"
                    )
            n_reports = metrics.get("n_reports")
            n_linked = metrics.get("n_linked_reports")
            n_noise = metrics.get("n_noise_reports")
            n_noise_rejected = metrics.get("n_noise_rejected")
            n_false = metrics.get("n_false_destinations")
            n_review = metrics.get("n_review_items")
            counts = (n_reports, n_linked, n_noise, n_noise_rejected, n_false, n_review)
            if any(isinstance(value, bool) or not isinstance(value, int) for value in counts):
                raise ExperimentV2Error(
                    f"successful calibration row {index} has non-integer denominators"
                )
            assert all(isinstance(value, int) for value in counts)
            if (
                n_reports <= 0
                or n_linked <= 0
                or n_noise <= 0
                or n_noise_rejected < 0
                or n_noise_rejected > n_noise
                or n_false < 0
                or n_review < 0
                or row.get("n_reports") != n_reports
            ):
                raise ExperimentV2Error(
                    f"successful calibration row {index} has invalid endpoint denominators"
                )
            expected_values = {
                "false_destinations_per_100_reports": 100.0 * n_false / n_reports,
                "noise_rejection": n_noise_rejected / n_noise,
                "review_items_per_100_reports": 100.0 * n_review / n_reports,
            }
            if not -1.0 <= float(metrics["ari_linked"]) <= 1.0:
                raise ExperimentV2Error(
                    f"successful calibration row {index} has out-of-range ARI"
                )
            for endpoint, expected_value in expected_values.items():
                if not math.isclose(
                    float(metrics[endpoint]),
                    expected_value,
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                ):
                    raise ExperimentV2Error(
                        f"successful calibration row {index} has inconsistent {endpoint} denominator"
                    )
        elif not isinstance(row.get("error_type"), str):
            raise ExperimentV2Error(f"failed calibration row {index} lacks error_type")
        by_configuration[configuration_id].append(row)

    if (
        payload.get("n_rows") != len(expected_keys)
        or len(rows) != len(expected_keys)
        or observed_keys != expected_keys
    ):
        missing = len(expected_keys - observed_keys)
        extra = len(observed_keys - expected_keys)
        raise ExperimentV2Error(
            f"calibration configuration×seed coverage mismatch: missing={missing}, extra={extra}"
        )
    return configuration_map, by_configuration


def select_calibration(
    calibration_payload: Mapping[str, Any] | None = None,
    protocol: ProtocolV2 | None = None,
    *,
    calibration_path: Path | None = None,
    output_path: Path = CALIBRATION_SELECTION,
) -> dict[str, Any]:
    """Apply the identical ARI/one-SE/operational selection rule to each method."""

    protocol = protocol or load_protocol()
    if calibration_payload is None:
        source_path = calibration_path or CALIBRATION_ROWS
        calibration_payload = _read_json_gzip(source_path)
        source: dict[str, Any] = {
            "kind": "gzip_file",
            "path": _path_label(source_path),
            "sha256": file_sha256(source_path),
        }
    elif calibration_path is not None:
        from_file = _read_json_gzip(calibration_path)
        if canonical_json_bytes(from_file) != canonical_json_bytes(calibration_payload):
            raise ExperimentV2Error("calibration payload does not match its declared source")
        source = {
            "kind": "gzip_file",
            "path": _path_label(calibration_path),
            "sha256": file_sha256(calibration_path),
        }
    else:
        source = {
            "kind": "inline_payload",
            "path": None,
            "sha256": None,
        }
    if not isinstance(calibration_payload, Mapping):
        raise ExperimentV2Error("calibration payload must be an object")
    payload_sha256 = _payload_sha256(calibration_payload)
    if source["kind"] == "inline_payload":
        source["sha256"] = payload_sha256
    current_implementation = implementation_sha256()
    configuration_map, by_configuration = _validate_calibration_payload(
        calibration_payload,
        protocol,
        current_implementation_sha256=current_implementation,
    )
    method_configurations: dict[str, list[str]] = defaultdict(list)
    for configuration in configuration_map.values():
        method_configurations[configuration.method_id].append(configuration.configuration_id)
    selections: dict[str, Any] = {}
    summaries: dict[str, Any] = {}
    n_seeds = len(protocol.calibration_seeds)
    for method_id, identifiers in sorted(method_configurations.items()):
        eligible: list[dict[str, Any]] = []
        method_summaries: list[dict[str, Any]] = []
        for identifier in sorted(identifiers):
            rows = by_configuration.get(identifier, [])
            success = [row for row in rows if row.get("status") == "success"]
            summary: dict[str, Any] = {
                "configuration_id": identifier,
                "n_expected": n_seeds,
                "n_success": len(success),
                "n_failures": len(rows) - len(success),
                "eligible": len(rows) == n_seeds and len(success) == n_seeds,
            }
            if summary["eligible"]:
                ari_values = np.asarray([float(row["metrics"]["ari_linked"]) for row in success])
                summary.update(
                    {
                        "mean_ari": float(ari_values.mean()),
                        "se_ari": float(ari_values.std(ddof=1) / math.sqrt(n_seeds)),
                        "mean_false_destinations_per_100_reports": _mean(success, "false_destinations_per_100_reports"),
                        "mean_noise_rejection": _mean(success, "noise_rejection"),
                        "mean_review_items_per_100_reports": _mean(success, "review_items_per_100_reports"),
                    }
                )
                eligible.append(summary)
            method_summaries.append(summary)
        summaries[method_id] = method_summaries
        if not eligible:
            selections[method_id] = {"status": "no_selection", "reason": "no_complete_configuration"}
            continue
        best_ari = max(row["mean_ari"] for row in eligible)
        best_rows = [row for row in eligible if row["mean_ari"] == best_ari]
        best = min(best_rows, key=lambda row: row["configuration_id"])
        one_se_floor = best_ari - best["se_ari"]
        one_se = [row for row in eligible if row["mean_ari"] >= one_se_floor - 1e-15]
        selected = min(
            one_se,
            key=lambda row: (
                row["mean_false_destinations_per_100_reports"],
                -row["mean_noise_rejection"],
                row["mean_review_items_per_100_reports"],
                row["configuration_id"],
            ),
        )
        configuration = configuration_map[selected["configuration_id"]]
        selections[method_id] = {
            "status": "selected",
            "configuration": _configuration_payload(configuration),
            "best_mean_ari": best_ari,
            "best_standard_error": best["se_ari"],
            "one_standard_error_floor": one_se_floor,
            "one_standard_error_set_size": len(one_se),
            "selected_metrics": selected,
            "selection_order": [
                "maximum_mean_calibration_ari",
                "one_standard_error_set",
                "minimum_false_destinations_per_100_reports",
                "maximum_noise_rejection",
                "minimum_review_items_per_100_reports",
                "canonical_configuration_id",
            ],
        }
    payload = {
        "schema_version": "v2.calibration-selection.1",
        "protocol_sha256": protocol.bundle_sha256,
        "implementation_sha256": current_implementation,
        "calibration_rows_sha256": payload_sha256,
        "calibration_rows_payload_sha256": payload_sha256,
        "calibration_rows_source": source,
        "selections": selections,
        "configuration_summaries": summaries,
    }
    _write_json(output_path, payload)
    return payload


def freeze_execution(
    protocol: ProtocolV2 | None = None,
    *,
    selection_path: Path = CALIBRATION_SELECTION,
    output_path: Path = EXECUTION_FREEZE,
) -> dict[str, Any]:
    """Freeze protocol, code, selection, and confirmation seeds before release."""

    protocol = protocol or load_protocol()
    if (
        CONFIRMATION_MANIFEST.exists()
        or CONFIRMATION_RESULT.exists()
        or CONFIRMATION_ANALYSIS.exists()
        or ORACLE_DIAGNOSTIC.exists()
    ):
        raise ExperimentV2Error(
            "confirmation state/output already exists; execution freeze is forbidden"
        )
    if output_path.exists():
        raise ExperimentV2Error("execution freeze already exists and is immutable")
    selection = _read_json(selection_path)
    if selection.get("protocol_sha256") != protocol.bundle_sha256:
        raise ExperimentV2Error("selection does not match current protocol")
    current_code = implementation_sha256()
    if selection.get("implementation_sha256") != current_code:
        raise ExperimentV2Error("implementation changed after calibration selection")
    _selected_configurations(protocol, selection)
    payload = {
        "schema_version": "v2.execution-freeze.1",
        "protocol_sha256": protocol.bundle_sha256,
        "implementation_sha256": current_code,
        "calibration_selection_sha256": file_sha256(selection_path),
        "confirmation_master_seeds": list(protocol.confirmation_seeds),
        "retired_confirmation_master_seeds": list(
            protocol.retired_confirmation_seeds
        ),
        "confirmation_master_seeds_sha256": _payload_sha256(
            list(protocol.confirmation_seeds)
        ),
        "regimes_per_master_seed": ["id", "ood"],
        "confirmation_datasets": len(protocol.confirmation_seeds) * 2,
        "confirmation_release_policy": "one accepted execution; no intermediate selection feedback",
        "accepted_execution_exists_at_freeze": False,
    }
    _exclusive_write_json(output_path, payload)
    return payload


def _selected_configurations(protocol: ProtocolV2, selection: Mapping[str, Any]) -> dict[str, ExpandedConfiguration]:
    configuration_map = {configuration.configuration_id: configuration for configuration in all_configurations(protocol)}
    expected_methods = {configuration.method_id for configuration in configuration_map.values()}
    selection_rows = selection.get("selections")
    if not isinstance(selection_rows, Mapping) or set(selection_rows) != expected_methods:
        raise ExperimentV2Error("selection must contain every registered method exactly once")
    result: dict[str, ExpandedConfiguration] = {}
    for method_id, row in selection_rows.items():
        if not isinstance(row, Mapping):
            raise ExperimentV2Error(f"selection row is not an object: {method_id}")
        if row.get("status") != "selected":
            raise ExperimentV2Error(f"method is not selected: {method_id}")
        configuration_payload = row.get("configuration")
        if not isinstance(configuration_payload, Mapping):
            raise ExperimentV2Error(f"selection lacks configuration payload: {method_id}")
        identifier = configuration_payload.get("configuration_id")
        if not isinstance(identifier, str) or identifier not in configuration_map:
            raise ExperimentV2Error(f"selection references unknown configuration: {identifier}")
        configuration = configuration_map[str(identifier)]
        if configuration.method_id != method_id:
            raise ExperimentV2Error(
                f"selection method/configuration mismatch: {method_id}/{identifier}"
            )
        if dict(configuration_payload) != _configuration_payload(configuration):
            raise ExperimentV2Error(f"selection payload was altered: {identifier}")
        result[str(method_id)] = configuration
    return result


def _resource_scenarios(seed: int) -> tuple[ResourceScenarioV2, ...]:
    rng = np.random.default_rng(np.random.SeedSequence([seed, 17]))
    jitter = lambda center: (
        center[0] + float(rng.normal(0.0, 0.025)),
        center[1] + float(rng.normal(0.0, 0.025)),
    )
    hue, danang, quangtri = (16.4637, 107.5909), (16.0678, 108.2208), (16.7500, 107.1900)
    return (
        ResourceScenarioV2("lean", (jitter(hue),), 2, 24.0, 0.8, 18.0),
        ResourceScenarioV2("nominal", (jitter(hue), jitter(danang)), 3, 30.0, 1.0, 12.0),
        ResourceScenarioV2("surge", (jitter(hue), jitter(danang), jitter(quangtri)), 5, 34.0, 1.3, 8.0),
    )


def _oracle_labels(dataset: GeneratedDatasetV2) -> tuple[int, ...]:
    truth = {row.report_id: row for row in dataset.report_truth}
    return tuple(
        -1 if truth[row.report_id].incident_id is None else int(truth[row.report_id].gt_cluster)
        for row in dataset.reports
    )


def run_confirmation(
    protocol: ProtocolV2 | None = None,
    *,
    result_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Claim and release the active paired confirmation partition once."""

    protocol = protocol or load_protocol()
    managed_result = CONFIRMATION_RESULT
    managed_state = CONFIRMATION_MANIFEST
    requested_result = managed_result if result_path is None else Path(result_path)
    requested_state = managed_state if manifest_path is None else Path(manifest_path)
    if requested_result.resolve() != managed_result.resolve():
        raise ExperimentV2Error("custom confirmation result paths are forbidden")
    if requested_state.resolve() != managed_state.resolve():
        raise ExperimentV2Error("custom confirmation state paths are forbidden")
    if managed_state.exists():
        raise ExperimentV2Error("confirmation was already started; retry is forbidden")
    if managed_result.exists() or CONFIRMATION_ANALYSIS.exists() or ORACLE_DIAGNOSTIC.exists():
        raise ExperimentV2Error("confirmation output exists without a clean start state")

    freeze = _read_json(EXECUTION_FREEZE)
    selection = _read_json(CALIBRATION_SELECTION)
    current_code = implementation_sha256()
    selection_sha256 = file_sha256(CALIBRATION_SELECTION)
    freeze_sha256 = file_sha256(EXECUTION_FREEZE)
    active_seeds = list(protocol.confirmation_seeds)
    retired_seeds = list(protocol.retired_confirmation_seeds)
    active_seed_sha256 = _payload_sha256(active_seeds)
    if len(active_seeds) != 40:
        raise ExperimentV2Error(
            "managed confirmation requires exactly 40 locked master seeds"
        )
    if freeze.get("schema_version") != "v2.execution-freeze.1":
        raise ExperimentV2Error("unsupported execution-freeze schema")
    if selection.get("schema_version") != "v2.calibration-selection.1":
        raise ExperimentV2Error("unsupported calibration-selection schema")
    if freeze.get("protocol_sha256") != protocol.bundle_sha256:
        raise ExperimentV2Error("protocol changed after execution freeze")
    if freeze.get("implementation_sha256") != current_code:
        raise ExperimentV2Error("implementation changed after execution freeze")
    if freeze.get("calibration_selection_sha256") != selection_sha256:
        raise ExperimentV2Error("calibration selection changed after execution freeze")
    if (
        freeze.get("confirmation_master_seeds") != active_seeds
        or freeze.get("retired_confirmation_master_seeds") != retired_seeds
        or freeze.get("confirmation_master_seeds_sha256") != active_seed_sha256
        or freeze.get("regimes_per_master_seed") != ["id", "ood"]
        or freeze.get("confirmation_datasets") != len(active_seeds) * 2
    ):
        raise ExperimentV2Error("execution freeze does not bind the active confirmation partition")
    if selection.get("protocol_sha256") != protocol.bundle_sha256:
        raise ExperimentV2Error("selection does not match current protocol")
    if selection.get("implementation_sha256") != current_code:
        raise ExperimentV2Error("selection does not match current implementation")
    selected = _selected_configurations(protocol, selection)
    start_state = {
        "schema_version": "v2.confirmation-state.1",
        "status": "started",
        "protocol_sha256": protocol.bundle_sha256,
        "implementation_sha256": current_code,
        "execution_freeze_sha256": freeze_sha256,
        "selection_sha256": selection_sha256,
        "confirmation_master_seeds": active_seeds,
        "confirmation_master_seeds_sha256": active_seed_sha256,
        "result_file": _path_label(managed_result),
        "analysis_file": _path_label(CONFIRMATION_ANALYSIS),
        "oracle_diagnostic_file": _path_label(ORACLE_DIAGNOSTIC),
    }
    _exclusive_write_json(managed_state, start_state)
    try:
        return _run_confirmation_core(
            protocol,
            result_path=managed_result,
            analysis_path=CONFIRMATION_ANALYSIS,
            state_path=managed_state,
            current_code=current_code,
            selected=selected,
            start_state=start_state,
        )
    except BaseException as exc:
        failed_state = {
            **start_state,
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "retry_permitted": False,
        }
        # Preserve hashes of any atomically completed orphan artifacts for a
        # forensic audit.  Their presence never permits retry or acceptance.
        for field, path in (
            ("result_sha256", managed_result),
            ("analysis_sha256", CONFIRMATION_ANALYSIS),
            ("oracle_diagnostic_sha256", ORACLE_DIAGNOSTIC),
        ):
            if path.is_file():
                failed_state[field] = file_sha256(path)
        try:
            _transition_confirmation_state(managed_state, failed_state)
        except BaseException:
            # A retained started/terminal claim is itself sufficient to block
            # another release; never mask the original scientific failure.
            pass
        raise


def _run_confirmation_core(
    protocol: ProtocolV2,
    *,
    result_path: Path,
    analysis_path: Path,
    state_path: Path,
    current_code: str,
    selected: Mapping[str, ExpandedConfiguration],
    start_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Execute the scientific loop after the single-release claim is held."""
    clustering_rows: list[dict[str, Any]] = []
    priority_rows: list[dict[str, Any]] = []
    stress_rows: list[dict[str, Any]] = []
    dispatch_rows: list[dict[str, Any]] = []
    oracle_rows: list[dict[str, Any]] = []
    schedule_hash_rows: list[dict[str, Any]] = []
    for seed in protocol.confirmation_seeds:
        for regime in ("id", "ood"):
            dataset = observation_snapshot(
                generate_dataset(
                    seed,
                    regime,
                    confirmation_release=seed in ACTIVE_CONFIRMATION_SEEDS_V2,
                )
            )
            provenance = report_provenance_scores(dataset.reports)
            runs: dict[str, ClusterRunV2] = {}
            for method_id, configuration in selected.items():
                run = execute_configuration(dataset.reports, configuration, seed=seed)
                runs[method_id] = run
                clustering_rows.append(
                    {
                        "method": method_id,
                        "configuration_id": configuration.configuration_id,
                        "seed": seed,
                        "regime": regime,
                        "metrics": clustering_endpoints(
                            dataset.reports,
                            dataset.report_truth,
                            run,
                            provenance_scores=provenance,
                        ),
                    }
                )
            product_method = "method.product_louvain"
            product_run = runs[product_method]
            # Observable scoring is completed before evaluator-only linkage.
            # The evaluator then assigns independent gains to predicted units;
            # it never repairs split/merge/noise before scoring.
            predicted_priority = score_predicted_priority(
                dataset.reports,
                product_run.labels,
            )
            evaluated_priority = evaluate_predicted_priority(
                predicted_priority,
                dataset.report_truth,
                dataset.incident_truth,
                k=5,
            )
            for row in evaluated_priority.alignment_rows:
                priority_rows.append(
                    {
                        "seed": seed,
                        "regime": regime,
                        **dict(row),
                        "matching_summary": evaluated_priority.summary,
                    }
                )
            for family in STRESS_FAMILIES:
                stress = evaluate_priority_stress(
                    dataset.reports,
                    product_run.labels,
                    dataset.report_truth,
                    dataset.incident_truth,
                    family,
                    k=5,
                    base_scored=predicted_priority,
                    base_evaluation=evaluated_priority,
                )
                for row in stress.stress_rows:
                    stress_rows.append({"seed": seed, "regime": regime, **dict(row)})

            predicted_jobs = build_jobs(
                dataset.reports,
                product_run.labels,
                predicted_priority.cluster_score_payload,
                base_time=BASE_TIME,
                snapshot_min=SNAPSHOT_CUTOFF_MIN_V2,
            )
            for scenario in _resource_scenarios(seed):
                for policy_id in POLICY_IDS:
                    schedule = schedule_jobs(predicted_jobs.jobs, scenario, policy_id)
                    schedule_hash_rows.append(
                        {
                            "seed": seed,
                            "regime": regime,
                            "scenario": scenario.scenario_id,
                            "policy": policy_id,
                            "hash": schedule_hash(schedule),
                        }
                    )
                    dispatch_rows.append(
                        {
                            "seed": seed,
                            "regime": regime,
                            "scenario": scenario.scenario_id,
                            "policy": policy_id,
                            "partition": "predicted_product_clusters",
                            "review_reports": len(predicted_jobs.review_report_ids),
                            "metrics": evaluate_schedule(
                                schedule,
                                dataset.report_truth,
                                dataset.incident_truth,
                            ),
                        }
                    )
                # Clearly separate oracle grouping as an artifact-only upper-bound diagnostic.
                oracle_labels = _oracle_labels(dataset)
                oracle_cluster_scores = score_clusters(dataset.reports, oracle_labels)
                oracle_jobs = build_jobs(
                    dataset.reports,
                    oracle_labels,
                    {cluster_id: row.dispatch_scores() for cluster_id, row in oracle_cluster_scores.items()},
                    base_time=BASE_TIME,
                    snapshot_min=SNAPSHOT_CUTOFF_MIN_V2,
                )
                for policy_id in ("revised", "nearest_first"):
                    oracle_schedule = schedule_jobs(oracle_jobs.jobs, scenario, policy_id)
                    oracle_rows.append(
                        {
                            "seed": seed,
                            "regime": regime,
                            "scenario": scenario.scenario_id,
                            "policy": policy_id,
                            "partition": "oracle_incident_grouping_upper_bound_only",
                            "metrics": evaluate_schedule(
                                oracle_schedule,
                                dataset.report_truth,
                                dataset.incident_truth,
                            ),
                        }
                    )
    seeds = tuple(protocol.confirmation_seeds)
    regimes = ("id", "ood")
    scenarios = ("lean", "nominal", "surge")
    priority_policies = tuple(
        sorted(set(POLICY_IDS).difference({"nearest_first"}))
    )
    _assert_exact_composite_keys(
        "clustering",
        clustering_rows,
        ("method", "seed", "regime"),
        {
            (method, seed, regime)
            for method in selected
            for seed in seeds
            for regime in regimes
        },
    )
    _assert_exact_composite_keys(
        "priority",
        priority_rows,
        ("policy", "seed", "regime"),
        {
            (policy, seed, regime)
            for policy in priority_policies
            for seed in seeds
            for regime in regimes
        },
    )
    _assert_exact_composite_keys(
        "priority stress",
        stress_rows,
        ("family", "policy", "seed", "regime"),
        {
            (family, policy, seed, regime)
            for family in STRESS_FAMILIES
            for policy in priority_policies
            for seed in seeds
            for regime in regimes
        },
    )
    dispatch_keys = {
        (scenario, policy, seed, regime)
        for scenario in scenarios
        for policy in POLICY_IDS
        for seed in seeds
        for regime in regimes
    }
    _assert_exact_composite_keys(
        "predicted dispatch",
        dispatch_rows,
        ("scenario", "policy", "seed", "regime"),
        dispatch_keys,
    )
    _assert_exact_composite_keys(
        "schedule hash",
        schedule_hash_rows,
        ("scenario", "policy", "seed", "regime"),
        dispatch_keys,
    )
    _assert_exact_composite_keys(
        "oracle diagnostic",
        oracle_rows,
        ("scenario", "policy", "seed", "regime"),
        {
            (scenario, policy, seed, regime)
            for scenario in scenarios
            for policy in ("revised", "nearest_first")
            for seed in seeds
            for regime in regimes
        },
    )
    if file_sha256(EXECUTION_FREEZE) != start_state["execution_freeze_sha256"]:
        raise ExperimentV2Error("execution freeze changed during confirmation")
    if file_sha256(CALIBRATION_SELECTION) != start_state["selection_sha256"]:
        raise ExperimentV2Error("calibration selection changed during confirmation")
    if implementation_sha256() != current_code:
        raise ExperimentV2Error("implementation changed during confirmation")
    payload = {
        "schema_version": "v2.confirmation-result.1",
        "protocol_sha256": protocol.bundle_sha256,
        "implementation_sha256": current_code,
        "execution_freeze_sha256": start_state["execution_freeze_sha256"],
        "selection_sha256": start_state["selection_sha256"],
        "confirmation_master_seeds": list(protocol.confirmation_seeds),
        "clustering_rows": clustering_rows,
        "priority_rows": priority_rows,
        "priority_stress_rows": stress_rows,
        "predicted_dispatch_rows": dispatch_rows,
        "schedule_hashes": schedule_hash_rows,
        "adverse_results_retained": True,
        "priority_scoring_uses_truth": False,
        "truth_used_by_scheduler": False,
    }
    # Analyze only the predicted-cluster confirmation payload.  Oracle rows
    # remain in their separate upper-bound diagnostic and cannot enter any
    # inferential family or claim gate.
    analysis = analyze_confirmation_payload(
        payload,
        ConfirmationAnalysisSpec(
            seeds=seeds,
            # The managed entrypoint enforces 40.  This explicit count keeps
            # the private core testable on development-only fixtures.
            expected_seed_count=len(seeds),
        ),
    )
    analysis_payload = {
        **analysis,
        "source_confirmation": {
            "schema_version": payload["schema_version"],
            "protocol_sha256": protocol.bundle_sha256,
            "implementation_sha256": current_code,
            "execution_freeze_sha256": start_state["execution_freeze_sha256"],
            "selection_sha256": start_state["selection_sha256"],
            "confirmation_payload_sha256": _payload_sha256(payload),
        },
    }
    # Analysis is intentionally computed before any result is accepted.  The
    # three artifacts may be written sequentially, but the immutable state is
    # not transitioned to accepted until all three digests are available.
    _write_json_gzip(result_path, payload)
    _write_json_gzip(ORACLE_DIAGNOSTIC, {"schema_version": "v2.oracle-dispatch-diagnostic.1", "rows": oracle_rows})
    _write_json(analysis_path, analysis_payload)
    if file_sha256(EXECUTION_FREEZE) != start_state["execution_freeze_sha256"]:
        raise ExperimentV2Error("execution freeze changed while writing confirmation artifacts")
    if file_sha256(CALIBRATION_SELECTION) != start_state["selection_sha256"]:
        raise ExperimentV2Error("calibration selection changed while writing confirmation artifacts")
    if implementation_sha256() != current_code:
        raise ExperimentV2Error("implementation changed while writing confirmation artifacts")
    manifest = {
        **dict(start_state),
        "status": "accepted",
        "result_file": _path_label(result_path),
        "result_sha256": file_sha256(result_path),
        "analysis_file": _path_label(analysis_path),
        "analysis_sha256": file_sha256(analysis_path),
        "oracle_diagnostic_file": _path_label(ORACLE_DIAGNOSTIC),
        "oracle_diagnostic_sha256": file_sha256(ORACLE_DIAGNOSTIC),
        "n_master_seeds": len(protocol.confirmation_seeds),
        "n_id_datasets": len(protocol.confirmation_seeds),
        "n_ood_datasets": len(protocol.confirmation_seeds),
        "n_clustering_rows": len(clustering_rows),
        "n_priority_rows": len(priority_rows),
        "n_stress_rows": len(stress_rows),
        "n_dispatch_rows": len(dispatch_rows),
        "coverage_complete": True,
    }
    _transition_confirmation_state(state_path, manifest)
    return manifest


__all__ = [
    "CALIBRATION_ROWS",
    "CALIBRATION_SELECTION",
    "CONFIRMATION_ANALYSIS",
    "CONFIRMATION_MANIFEST",
    "CONFIRMATION_RESULT",
    "EXECUTION_FREEZE",
    "ExperimentV2Error",
    "all_configurations",
    "execute_configuration",
    "freeze_execution",
    "implementation_sha256",
    "run_calibration",
    "run_confirmation",
    "select_calibration",
]
