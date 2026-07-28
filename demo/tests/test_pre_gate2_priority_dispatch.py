from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from demo.experiments.exp16_priority_robustness import (
    LEGACY_ESTIMATOR_NAME,
    REVISED_ESTIMATOR_NAME,
    run_seed as run_priority_seed,
)
from demo.experiments.exp17_dispatch_outcomes import (
    POLICY_IDS,
    run_seed as run_dispatch_seed,
)
from demo.experiments.pre_gate2 import (
    default_table_path,
    resolve_frozen_dataset_root,
    restricted_protocol_and_seeds,
    write_exclusive_json,
)
from demo.experiments.calibration import load_tuning_dataset
from demo.simulation.dispatch import (
    DispatchIncident,
    ResourceScenario,
    simulate_dispatch,
)


@pytest.fixture(scope="module")
def priority_rows() -> list[dict[str, object]]:
    return run_priority_seed(1000, "development")


@pytest.fixture(scope="module")
def dispatch_rows() -> list[dict[str, object]]:
    return run_dispatch_seed(1000, "development")


def _assert_finite_json_numbers(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _assert_finite_json_numbers(child)
    elif isinstance(value, list):
        for child in value:
            _assert_finite_json_numbers(child)
    elif isinstance(value, float):
        assert math.isfinite(value)


def test_restricted_protocol_exposes_only_pre_gate2_stages() -> None:
    protocol, selected = restricted_protocol_and_seeds(("development",))
    assert len(selected) == 20
    assert {stage for stage, _ in selected} == {"development"}
    assert not hasattr(protocol, "test_seeds")
    with pytest.raises(ValueError, match="development/calibration"):
        restricted_protocol_and_seeds(("evaluation",))


def test_experiment_sources_do_not_import_evaluation_release_module() -> None:
    experiments = Path(__file__).resolve().parents[1] / "experiments"
    for filename in (
        "exp16_priority_robustness.py",
        "exp17_dispatch_outcomes.py",
        "pre_gate2.py",
    ):
        source = (experiments / filename).read_text(encoding="utf-8")
        assert "evaluation_protocol" not in source
        if filename.startswith("exp"):
            assert "build_candidate_dataset" not in source


def test_frozen_loader_uses_exact_split_path_and_refuses_relabel(
    tmp_path: Path,
) -> None:
    protocol, _ = restricted_protocol_and_seeds(("development",))
    frozen_root, provenance = resolve_frozen_dataset_root()
    loaded = load_tuning_dataset(
        frozen_root,
        stage="development",
        seed=1000,
        tuning_protocol=protocol,
        calibration_labels=True,
    )
    assert loaded.stage == "development"
    assert loaded.seed == 1000
    assert len(loaded.source_sha256) == 64
    assert provenance["dataset_manifest_sha256"] == (
        "74b9e80a085651b70a9ee18f5e9c7cb9846d47197d89c0717c05ac6af2fd1f7a"
    )

    with pytest.raises(ValueError, match="not the bundle"):
        resolve_frozen_dataset_root(tmp_path)

    # Even if development bytes are placed under a calibration filename, the
    # payload identity check refuses to relabel them.
    wrong_root = tmp_path / "wrong-bundle"
    wrong_source = wrong_root / "calibration" / "seed_2000.json"
    wrong_source.parent.mkdir(parents=True)
    (wrong_root / "manifest.json").write_bytes(
        (frozen_root / "manifest.json").read_bytes()
    )
    wrong_source.write_bytes(
        (frozen_root / "development" / "seed_1000.json").read_bytes()
    )
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_tuning_dataset(
            wrong_root,
            stage="calibration",
            seed=2000,
            tuning_protocol=protocol,
            calibration_labels=True,
        )


def test_artifact_output_is_exclusive_and_never_defaults_to_current_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tables = tmp_path / "immutable-run" / "tables"
    monkeypatch.setenv("DEMO_TABLES_DIR", str(tables))
    output = default_table_path("result.json")
    assert output == tables / "result.json"
    payload = {"schema_version": "fixture-v1", "value": 1}
    write_exclusive_json(output, payload)
    assert json.loads(output.read_text(encoding="utf-8")) == payload
    with pytest.raises(FileExistsError):
        write_exclusive_json(output, payload)
    with pytest.raises(ValueError, match="DEMO_TABLES_DIR"):
        write_exclusive_json(tmp_path / "outside.json", payload)


def test_exp16_covers_all_threats_estimators_and_exact_invariance(
    priority_rows: list[dict[str, object]],
) -> None:
    scenarios = {str(row["scenario"]) for row in priority_rows}
    assert {
        "exact_duplicate_2x",
        "exact_duplicate_5x",
        "exact_duplicate_10x",
        "near_duplicate",
        "low_confidence_inflate_N",
        "low_confidence_inflate_V",
        "low_confidence_inflate_F",
        "low_confidence_inflate_E",
        "coordinated_high_confidence_campaign",
        "source_missingness_zero_imputation",
    }.issubset(scenarios)
    assert {row["estimator"] for row in priority_rows} == {
        REVISED_ESTIMATOR_NAME,
        LEGACY_ESTIMATOR_NAME,
    }

    revised_exact = [
        row
        for row in priority_rows
        if row["estimator"] == REVISED_ESTIMATOR_NAME
        and str(row["scenario"]).startswith("exact_duplicate_")
    ]
    assert revised_exact
    assert all(
        float(row["priority_drift_abs_normalized"]) == 0.0
        for row in revised_exact
    )
    assert all(
        int(row["exact_duplicates_removed_after"])
        == int(row["metadata"]["total_observable_multiplicity"]) - 1
        for row in revised_exact
    )
    _assert_finite_json_numbers(priority_rows)


def test_exp16_reports_confidence_rank_and_latent_truth_errors(
    priority_rows: list[dict[str, object]],
) -> None:
    low = [
        row
        for row in priority_rows
        if str(row["scenario"]).startswith("low_confidence_")
        and row["estimator"] == REVISED_ESTIMATOR_NAME
    ]
    high = [
        row
        for row in priority_rows
        if row["scenario"] == "coordinated_high_confidence_campaign"
        and row["estimator"] == REVISED_ESTIMATOR_NAME
    ]
    assert len(low) == 4
    assert len(high) == 1
    assert all(float(row["attack_confidence_max"]) < 0.5 for row in low)
    assert float(high[0]["attack_confidence_mean"]) > max(
        float(row["attack_confidence_mean"]) for row in low
    )
    for row in priority_rows:
        assert float(row["n_error_relative_after"]) >= 0.0
        assert float(row["v_error_relative_after"]) >= 0.0
        assert 0.0 <= float(row["top_k_churn"]) <= 1.0
        assert 0.0 <= float(row["mean_rank_drift_normalized"]) <= 1.0


def _dispatch_fixture() -> tuple[
    tuple[DispatchIncident, ...],
    ResourceScenario,
]:
    incidents = (
        DispatchIncident(
            incident_id="a",
            lat=16.0,
            lng=107.0,
            province="north",
            start_min=0.0,
            ready_min=0.0,
            deadline_min=20.0,
            service_demand_min=12.0,
            harm_grace_min=0.0,
            harm_slope=2.0,
            capacity_penalty=0.5,
            n_true=20,
            robust_priority=1.5,
            legacy_priority=0.2,
            workload_proxy=10.0,
        ),
        DispatchIncident(
            incident_id="b",
            lat=16.05,
            lng=107.05,
            province="south",
            start_min=0.0,
            ready_min=0.0,
            deadline_min=40.0,
            service_demand_min=10.0,
            harm_grace_min=5.0,
            harm_slope=1.0,
            capacity_penalty=0.2,
            n_true=10,
            robust_priority=0.4,
            legacy_priority=1.6,
            workload_proxy=5.0,
        ),
    )
    scenario = ResourceScenario(
        scenario_id="fixture",
        depot_coordinates=((16.0, 107.0),),
        n_boats=1,
        speed_kmh=30.0,
        service_rate=1.0,
        nominal_service_capacity_min=15.0,
    )
    return incidents, scenario


def test_dispatch_simulator_is_deterministic_and_outcomes_are_latent() -> None:
    incidents, scenario = _dispatch_fixture()
    first = simulate_dispatch(incidents, scenario, "revised_priority")
    second = simulate_dispatch(incidents, scenario, "revised_priority")
    assert first == second
    assert [row["incident_id"] for row in first["assignments"]] == ["a", "b"]
    metrics = first["metrics"]
    assert metrics["n_incidents"] == 2
    assert float(metrics["latent_harm"]) >= 0.0
    assert 0.0 <= float(metrics["deadline_miss_rate"]) <= 1.0
    assert "flood" not in DispatchIncident.__dataclass_fields__
    assert "vulnerability" not in DispatchIncident.__dataclass_fields__


def test_fifo_remains_strict_beyond_blended_policy_aging_horizon() -> None:
    incidents, scenario = _dispatch_fixture()
    much_older_but_farther = (
        DispatchIncident(
            **{
                **incidents[0].__dict__,
                "incident_id": "older",
                "lat": 16.10,
                "lng": 107.10,
                "ready_min": -400.0,
            }
        ),
        DispatchIncident(
            **{
                **incidents[1].__dict__,
                "incident_id": "newer",
                "lat": 16.0,
                "lng": 107.0,
                "ready_min": -200.0,
            }
        ),
    )
    result = simulate_dispatch(
        much_older_but_farther,
        scenario,
        "first_report_fifo",
    )
    assert result["assignments"][0]["incident_id"] == "older"


def test_exp17_retains_every_policy_resource_and_pareto_endpoint(
    dispatch_rows: list[dict[str, object]],
) -> None:
    resources = {str(row["resource_scenario"]) for row in dispatch_rows}
    assert len(resources) == 3
    assert len(dispatch_rows) == len(POLICY_IDS) * len(resources)
    for resource in resources:
        selected = [
            row for row in dispatch_rows if row["resource_scenario"] == resource
        ]
        assert {row["policy"] for row in selected} == set(POLICY_IDS)
        assert any(bool(row["pareto_nondominated"]) for row in selected)
    for row in dispatch_rows:
        assert float(row["latent_harm"]) >= 0.0
        assert 0.0 <= float(row["deadline_miss_rate"]) <= 1.0
        assert float(row["mean_arrival_min"]) >= 0.0
        assert float(row["arrival_equity_gap_min"]) >= 0.0
        assert float(row["total_fleet_workload_min"]) >= 0.0
        assert len(row["assignments"]) == int(row["n_incidents"])
    _assert_finite_json_numbers(dispatch_rows)
