from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

import pytest

from demo.v2.protocol import (
    CANONICAL_ID_PATTERN,
    ProtocolV2Error,
    build_freeze_record,
    load_protocol,
    protocol_bundle_sha256,
    protocol_member_hashes,
    write_freeze_record,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_DIR = REPOSITORY_ROOT / "revision" / "v2"


def _json(name: str, directory: Path = PROTOCOL_DIR) -> dict[str, object]:
    return json.loads((directory / name).read_text(encoding="utf-8"))


def _protocol_copy(tmp_path: Path) -> Path:
    destination = tmp_path / "v2"
    # Result artifacts can appear after calibration, but they are explicitly
    # outside the frozen protocol bundle.  Keep fixtures independent of the
    # repository's execution state and copy protocol inputs only.
    shutil.copytree(PROTOCOL_DIR, destination, ignore=shutil.ignore_patterns("results"))
    return destination


def test_seed_partitions_are_exact_and_disjoint() -> None:
    protocol = load_protocol()
    assert protocol.development_seeds == tuple(range(4100, 4120))
    assert protocol.calibration_seeds == tuple(range(4200, 4220))
    assert protocol.confirmation_seeds == tuple(range(4400, 4440))
    assert protocol.retired_confirmation_seeds == tuple(range(4300, 4340))
    sets = [
        set(protocol.development_seeds),
        set(protocol.calibration_seeds),
        set(protocol.confirmation_seeds),
        set(protocol.retired_confirmation_seeds),
    ]
    assert all(sets[left].isdisjoint(sets[right]) for left in range(4) for right in range(left))
    manifest = _json("seed_partitions.json")
    assert manifest["retired_confirmation"]["reason"] == "opened_during_pre_freeze_code_audit"
    assert manifest["retired_confirmation"]["eligible_for_selection_or_confirmation"] is False


def test_product_additive_grid_has_128_controlled_nuisance_pairs() -> None:
    protocol = load_protocol()
    members_by_pair: dict[str, list[object]] = defaultdict(list)
    for member in protocol.paired_configurations:
        assert member.pair_id is not None
        members_by_pair[member.pair_id].append(member)

    assert len(protocol.paired_configurations) == 256
    assert len(members_by_pair) == 128
    assert all(re.fullmatch(CANONICAL_ID_PATTERN, pair_id) for pair_id in members_by_pair)

    configuration_ids: set[str] = set()
    for pair_id, members in members_by_pair.items():
        assert len(members) == 2, pair_id
        assert {member.operator for member in members} == {"product", "additive"}
        first, second = (member.execution_payload() for member in members)
        keys = set(first) | set(second)
        assert {key for key in keys if first.get(key) != second.get(key)} == {"operator"}
        for member in members:
            assert re.fullmatch(CANONICAL_ID_PATTERN, member.configuration_id)
            configuration_ids.add(member.configuration_id)
    assert len(configuration_ids) == 256

    registry = _json("method_registry.json")
    comparison = registry["paired_comparisons"][0]
    assert comparison["role"] == "matched_search_space_for_symmetric_independent_selection"
    assert comparison["confirmation_estimand"] == (
        "independently_selected_product_pipeline_vs_independently_selected_additive_pipeline"
    )
    assert comparison["axis_order"] == [
        "sigma_geo_m",
        "tau_t_min",
        "threshold_quantile",
        "k",
        "resolution",
    ]
    assert comparison["axes"] == {
        "sigma_geo_m": [500, 700, 900, 1200],
        "tau_t_min": [30, 60],
        "threshold_quantile": [0.85, 0.90, 0.95, 0.98],
        "k": [8, 16],
        "resolution": [0.8, 1.2],
    }
    fixed = comparison["shared_fixed_parameters"]
    assert {key: fixed[key] for key in ("tau_F", "tau_E", "alpha", "beta", "gamma")} == {
        "tau_F": 0.25,
        "tau_E": 0.35,
        "alpha": 0.5,
        "beta": 0.5,
        "gamma": 0.5,
    }
    assert fixed["candidate_pool_min_neighbors"] == 64
    assert fixed["candidate_pool_k_multiplier"] == 4
    assert fixed["threshold_population"] == "shared_geographically_pregated_candidate_pairs"


def test_independent_grids_have_locked_sizes_and_canonical_ids() -> None:
    protocol = load_protocol()
    st_dbscan = protocol.independent_configurations["grid.st_dbscan"]
    hdbscan = protocol.independent_configurations["grid.hdbscan"]
    assert len(st_dbscan) == 64
    assert len(hdbscan) == 96
    identifiers = [member.configuration_id for member in (*st_dbscan, *hdbscan)]
    assert len(identifiers) == len(set(identifiers))
    assert all(re.fullmatch(CANONICAL_ID_PATTERN, identifier) for identifier in identifiers)

    registry = _json("method_registry.json")
    grids = {grid["id"]: grid["axes"] for grid in registry["independent_grids"]}
    assert grids["grid.st_dbscan"] == {
        "spatial_eps_m": [250, 500, 750, 1000],
        "temporal_eps_min": [15, 30, 60, 120],
        "min_samples": [3, 5, 8, 12],
    }
    assert grids["grid.hdbscan"] == {
        "min_cluster_size": [3, 5, 10, 20],
        "min_samples": [1, 3, 5, 10],
        "spatial_scale_m": [250, 500, 1000],
        "temporal_scale_min": [30, 60],
    }
    hdbscan = next(
        grid for grid in registry["independent_grids"] if grid["id"] == "grid.hdbscan"
    )
    assert hdbscan["method_id"] == "method.hdbscan_geo_time"
    assert hdbscan["fixed_parameters"]["feature_view"] == "observable_geo_time"


def test_common_one_se_rule_selects_each_method_independently() -> None:
    contract = _json("analysis_contract.json")
    assert contract["observation_snapshot"] == {
        "base_time": "2026-10-15T00:00:00Z",
        "cutoff_min_after_base_time": 150,
        "report_inclusion_rule": "received_at_at_or_before_cutoff",
        "missing_event_time_action": "retain_as_observed_then_route_to_manual_review",
        "incident_evaluation_rule": "evaluator_incident_start_at_or_before_cutoff",
        "batch_job_ready_rule": "all_predicted_jobs_ready_at_declared_cutoff",
        "late_report_action": "exclude_from_this_snapshot_without_imputation",
    }
    rules = contract["selection_rules"]
    assert isinstance(rules, list)
    assert len(rules) == 1
    rule = rules[0]
    assert rule["id"] == "selection.common.one_se"
    assert rule["selection_scope"] == "within_each_method_independently"
    assert rule["applies_to_method_ids"] == [
        "method.additive_louvain",
        "method.hdbscan_geo_time",
        "method.product_louvain",
        "method.st_dbscan",
    ]
    assert rule["selection_split"] == "calibration"
    assert rule["required_calibration_seed_count"] == 20
    assert rule["candidate_unit"] == "configuration_id"
    assert rule["one_configuration_per_method"] is True
    assert [(step["order"], step["endpoint_id"], step.get("direction")) for step in rule["steps"]] == [
        (1, "endpoint.clustering.ari_labeled_reports", "higher"),
        (2, "endpoint.clustering.ari_labeled_reports", None),
        (3, "endpoint.operational.false_destinations_per_100_reports", "lower"),
        (4, "endpoint.secondary.noise_rejection_rate", "higher"),
        (5, "endpoint.operational.review_burden", "lower"),
    ]
    one_se = rule["steps"][1]
    assert one_se == {
        "order": 2,
        "action": "retain_one_standard_error_set",
        "endpoint_id": "endpoint.clustering.ari_labeled_reports",
        "formula": "mean_ari_candidate >= mean_ari_best - standard_error_ari_best",
        "standard_error_definition": "sample_standard_deviation_of_best_candidate_ari_over_sqrt_20",
        "inclusive": True,
    }
    assert rule["final_tie_breaker"] == "canonical_configuration_id_ascending"
    assert rule["missing_metric_action"] == "mark_candidate_ineligible"
    assert rule["no_eligible_action"] == "return_no_selection_without_relaxation"
    assert rule["post_hoc_rule_changes"] == "forbidden"


def test_confirmatory_endpoints_have_exactly_one_holm_family() -> None:
    contract = _json("analysis_contract.json")
    endpoints = {endpoint["id"]: endpoint for endpoint in contract["endpoints"]}
    memberships: dict[str, int] = defaultdict(int)
    for family in contract["holm_families"]:
        assert family["procedure"] == "holm"
        assert family["alpha"] == 0.05
        for endpoint_id in family["endpoint_ids"]:
            memberships[endpoint_id] += 1
    assert len(contract["holm_families"]) == 5
    for endpoint_id, endpoint in endpoints.items():
        assert memberships[endpoint_id] == (1 if endpoint["confirmatory"] else 0)
    assert contract["clustering_endpoint_roles"] == {
        "co_primary_family_ids": [
            "family.clustering.synthetic",
        ],
        "key_secondary_endpoint_ids": [
            "endpoint.clustering.incident_split_loss",
            "endpoint.clustering.incident_merge_loss",
            "endpoint.operational.review_burden",
            "endpoint.secondary.destination_geographic_diameter_m",
            "endpoint.secondary.noise_rejection_rate",
        ],
    }
    assert memberships["endpoint.secondary.destination_geographic_diameter_m"] == 0
    assert memberships["endpoint.secondary.noise_rejection_rate"] == 0
    families = {row["id"]: set(row["endpoint_ids"]) for row in contract["holm_families"]}
    assert families["family.priority_dispatch.synthetic"] == {
        "endpoint.priority.ndcg_at_5",
        "endpoint.priority.normalized_drift",
        "endpoint.priority.top_k_churn",
        "endpoint.priority.false_priority_lift",
        "endpoint.dispatch.latent_harm",
        "endpoint.dispatch.deadline_miss_rate",
    }


def test_public_source_manifest_records_rights_coverage_and_unhashed_state() -> None:
    manifest = _json("public_sources.json")
    assert manifest["metadata_snapshot_date"] == "2026-08-11"
    sources = {source["id"]: source for source in manifest["sources"]}
    assert set(sources) == {
        "source.trec_is",
        "source.crisisfacts",
        "source.idrisi_re",
        "source.noaa_storm_events",
        "source.noaa_flash",
        "source.uk_water_rescue",
    }
    assert sources["source.trec_is"]["license"]["status"] == "restricted_terms_no_standard_open_license"
    assert sources["source.crisisfacts"]["license"]["status"] == "mixed_source_terms"
    assert sources["source.idrisi_re"]["license"]["identifier"] == "CC-BY-4.0"
    assert sources["source.noaa_storm_events"]["license"]["identifier"] == "US-PUBLIC-DOMAIN"
    assert sources["source.noaa_flash"]["license"]["status"] == "archival_product_license_unresolved"
    assert sources["source.uk_water_rescue"]["license"]["identifier"] == "OGL-3.0"

    for source in sources.values():
        artifact = source["local_artifact"]
        assert artifact["downloaded"] is False
        assert artifact["path"] is None
        assert artifact["sha256"] is None
        assert source["access_gate"]["status"] == "blocked"
        assert source["coverage"]["vietnamese"] is False
        assert all(url.startswith("https://") for url in source["official_urls"].values())

    incident_gate_statuses = {
        gate["status"]
        for source in sources.values()
        for gate in source["coverage_gates"]
        if gate["role"] == "physical_incident_clustering"
    }
    assert incident_gate_statuses == {"fail"}


def test_public_anchor_is_frozen_descriptive_evidence_only() -> None:
    protocol = load_protocol()
    anchor = _json("public_anchor.json")
    assert "public_anchor.json" in protocol.member_sha256
    assert set(anchor["audited_sources"]) == {
        "source.idrisi_re",
        "source.noaa_storm_events",
        "source.uk_water_rescue",
    }
    assert {
        row["source_id"] for row in anchor["blocked_sources"]
    } == {"source.trec_is", "source.crisisfacts"}
    assert anchor["anchor_mapping"]["generator_fit"] == {
        "claim": "No audited public source was used to fit the generator.",
        "parameters_estimated_from_public_sources": [],
        "performed": False,
    }
    assert anchor["seed_safety"]["generator_invoked"] is False


def test_public_anchor_rejects_a_post_hoc_generator_fit(tmp_path: Path) -> None:
    protocol_dir = _protocol_copy(tmp_path)
    anchor = _json("public_anchor.json", protocol_dir)
    anchor["anchor_mapping"]["generator_fit"]["performed"] = True
    (protocol_dir / "public_anchor.json").write_text(
        json.dumps(anchor, indent=2) + "\n", encoding="utf-8"
    )
    with pytest.raises(ProtocolV2Error, match="overstates generator fitting"):
        load_protocol(protocol_dir)


def test_external_and_real_world_claims_start_blocked() -> None:
    contract = _json("analysis_contract.json")
    claims = {claim["id"]: claim for claim in contract["claim_gates"]}
    required_blocked = {
        "claim.external_priority_sanity",
        "claim.external_consolidation_sanity",
        "claim.external_location_sanity",
        "claim.external_flood_context_descriptive",
        "claim.real_incident_clustering_accuracy",
        "claim.real_dispatch_benefit",
        "claim.vietnamese_transfer",
    }
    assert all(claims[claim_id]["default_status"] == "blocked" for claim_id in required_blocked)
    assert claims["claim.synthetic_controlled_clustering"]["permitted_scope"] == "within_frozen_synthetic_generator_family"
    assert claims["claim.synthetic_duplicate_invariance"]["permitted_scope"] == "algebraic_and_synthetic_stress_behavior"


def test_protocol_hash_ignores_results_lock_and_unlisted_files(tmp_path: Path) -> None:
    protocol_dir = _protocol_copy(tmp_path)
    initial_hash = protocol_bundle_sha256(protocol_dir)
    initial_members = protocol_member_hashes(protocol_dir)

    results = protocol_dir / "results"
    results.mkdir()
    (results / "tempting-result.json").write_text('{"winner":"post_hoc"}\n', encoding="utf-8")
    (protocol_dir / "protocol-lock.json").write_text('{"stale":true}\n', encoding="utf-8")
    (protocol_dir / "unlisted-notes.txt").write_text("not frozen\n", encoding="utf-8")
    assert protocol_bundle_sha256(protocol_dir) == initial_hash
    assert protocol_member_hashes(protocol_dir) == initial_members

    member = protocol_dir / "seed_partitions.json"
    member.write_text(member.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert protocol_bundle_sha256(protocol_dir) != initial_hash


def test_freeze_record_is_stable_and_never_hashes_results(tmp_path: Path) -> None:
    protocol_dir = _protocol_copy(tmp_path)
    fixed_time = "2026-08-11T00:00:00Z"
    first = build_freeze_record(protocol_dir, frozen_at=fixed_time)
    (protocol_dir / "results").mkdir()
    (protocol_dir / "results" / "after-freeze.csv").write_text("outcome\n1\n", encoding="utf-8")
    second = build_freeze_record(protocol_dir, frozen_at=fixed_time)
    assert first == second
    assert first["results_excluded"] is True
    assert first["external_data_downloaded_by_freeze"] is False
    assert {row["path"] for row in first["members"]} == {
        "bundle.json",
        "analysis_contract.json",
        "method_registry.json",
        "public_anchor.json",
        "public_sources.json",
        "seed_partitions.json",
    }

    output = tmp_path / "lock" / "protocol-lock.json"
    assert write_freeze_record(output, protocol_dir, frozen_at=fixed_time) == first
    assert json.loads(output.read_text(encoding="utf-8")) == first
    with pytest.raises(ProtocolV2Error, match="may not overwrite"):
        write_freeze_record(protocol_dir / "bundle.json", protocol_dir, frozen_at=fixed_time)


def test_checked_in_protocol_lock_matches_current_frozen_members() -> None:
    lock = _json("protocol-lock.json")
    assert lock == build_freeze_record(frozen_at=lock["frozen_at"])
    assert all(not row["path"].startswith("results/") for row in lock["members"])


def test_manifest_rejects_fabricated_checksum_before_download(tmp_path: Path) -> None:
    protocol_dir = _protocol_copy(tmp_path)
    manifest = _json("public_sources.json", protocol_dir)
    manifest["sources"][0]["local_artifact"]["sha256"] = "0" * 64
    (protocol_dir / "public_sources.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    with pytest.raises(ProtocolV2Error, match="may not declare path/SHA-256 before download"):
        load_protocol(protocol_dir)


def test_json_loader_rejects_duplicate_keys(tmp_path: Path) -> None:
    protocol_dir = _protocol_copy(tmp_path)
    contract_path = protocol_dir / "analysis_contract.json"
    contract = contract_path.read_text(encoding="utf-8")
    needle = (
        '"id": "endpoint.external.idrisi_location_span_f1",\n'
        '      "direction": "higher",'
    )
    replacement = needle + '\n      "direction": "lower",'
    assert contract.count(needle) == 1
    contract_path.write_text(contract.replace(needle, replacement), encoding="utf-8")
    with pytest.raises(ProtocolV2Error, match="duplicate JSON key 'direction'"):
        load_protocol(protocol_dir)
