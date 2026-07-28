"""Schema and method-agnostic quality gates for candidate synthetic data."""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from pipeline.attributes import haversine_m

SCHEMA_VERSION = "flood-rescue-synthetic-v4"
GENERATOR_VERSION = "4.1.0"
DEFAULT_SEED_MANIFEST = Path(__file__).resolve().parents[1] / "protocol" / "seed_manifest.json"

OBSERVABLE_FIELDS = (
    "event_id",
    "lat",
    "lng",
    "created_at",
    "flood",
    "urgency",
    "n_trapped",
    "vulnerability",
    "has_image",
    "source_type",
    "province",
    "note",
    "missing_fields",
)

FORBIDDEN_INFERENCE_FIELDS = {
    "incident_id",
    "gt_cluster",
    "n_true",
    "v_true",
    "deadline_min",
    "service_demand_min",
    "harm_curve",
    "duplicate_family_id",
    "duplicate_kind",
    "coverage_n",
    "coverage_v",
    "population_member_indices",
    "vulnerable_member_indices",
    "adversary",
    "scenario_family",
    "evaluation_only",
    "is_fake",
}

REQUIRED_SCENARIO_FAMILIES = {
    "ordinary",
    "spatial_overlap_context_supportive",
    "spatial_overlap_context_adversarial",
    "same_location_temporal",
    "distant_context_similar",
    "multimodal",
    "unequal_density",
    "independent_stress",
}

ALLOWED_SOURCE_TYPES = {
    "anonymous",
    "citizen_app",
    "field_team",
    "hotline",
    "social_media",
}
ALLOWED_HARM_CURVES = {"piecewise_linear_lateness"}
MISSINGNESS_FIELDS = {"flood", "urgency", "n_trapped", "vulnerability"}
OPAQUE_EVENT_ID = re.compile(r"^EV-[0-9a-f]{20}$")


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON used by dataset checksums."""
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def registered_seed_splits(
    seed_manifest: str | Path = DEFAULT_SEED_MANIFEST,
) -> dict[str, tuple[int, ...]]:
    payload = json.loads(Path(seed_manifest).read_text(encoding="utf-8"))
    raw = payload.get("splits")
    if not isinstance(raw, dict):
        raise ValueError("locked seed manifest has no splits object")
    result: dict[str, tuple[int, ...]] = {}
    seen: set[int] = set()
    expected = {"development": 20, "calibration": 20, "test": 40}
    for split, count in expected.items():
        seeds = raw.get(split)
        if not isinstance(seeds, list) or any(
            isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds
        ):
            raise ValueError(f"invalid locked seed list: {split}")
        parsed = tuple(seeds)
        if len(parsed) != count or len(set(parsed)) != count:
            raise ValueError(f"locked seed count/uniqueness failed: {split}")
        if seen.intersection(parsed):
            raise ValueError("locked seed splits overlap")
        seen.update(parsed)
        result[split] = parsed
    return result


def registered_split_for_seed(
    seed: int,
    seed_manifest: str | Path = DEFAULT_SEED_MANIFEST,
) -> str | None:
    for split, seeds in registered_seed_splits(seed_manifest).items():
        if int(seed) in seeds:
            return split
    return None


def observable_report(report: dict[str, Any]) -> dict[str, Any]:
    """Return the report view allowed to reach inference code."""
    return {field: report[field] for field in OBSERVABLE_FIELDS if field in report}


def report_fingerprint(report: dict[str, Any]) -> str:
    """Fingerprint exact duplicates from observable payload, excluding identity.

    `event_id` and free-form `note` are transport/narrative fields and do not
    determine whether the measured payload is identical.
    """
    fields = (
        "lat",
        "lng",
        "created_at",
        "flood",
        "urgency",
        "n_trapped",
        "vulnerability",
        "has_image",
        "source_type",
        "province",
        "missing_fields",
    )
    payload = {
        field: ([] if field == "missing_fields" else None)
        if field not in report
        else report[field]
        for field in fields
    }
    return sha256_bytes(canonical_json_bytes(payload))


def _near_duplicate_ok(a: dict[str, Any], b: dict[str, Any]) -> bool:
    dist = haversine_m(float(a["lat"]), float(a["lng"]), float(b["lat"]), float(b["lng"]))
    ta = datetime.fromisoformat(str(a["created_at"]))
    tb = datetime.fromisoformat(str(b["created_at"]))
    dt_min = abs((ta - tb).total_seconds()) / 60.0
    n_tol = max(5.0, 0.25 * max(float(a["n_trapped"]), 1.0))
    return (
        dist <= 100.0
        and dt_min <= 10.0
        and abs(float(a["flood"]) - float(b["flood"])) <= 0.10
        and abs(float(a["urgency"]) - float(b["urgency"])) <= 0.10
        and abs(float(a["n_trapped"]) - float(b["n_trapped"])) <= n_tol
        and abs(float(a["vulnerability"]) - float(b["vulnerability"])) <= 2.0
    )


def _aware_datetime(value: object, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must include a timezone offset")
    return parsed


def _validate_method_blind_family_properties(
    incidents: list[dict[str, Any]],
) -> list[str]:
    """Check preregistered scenario geometry without running a clustering method."""
    errors: list[str] = []
    by_family: dict[str, list[dict[str, Any]]] = {}
    for incident in incidents:
        by_family.setdefault(str(incident.get("scenario_family")), []).append(incident)

    def pair(family: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        rows = by_family.get(family, [])
        if len(rows) != 2:
            errors.append(f"{family}: expected exactly two incidents")
            return None
        return rows[0], rows[1]

    def properties(
        rows: tuple[dict[str, Any], dict[str, Any]],
    ) -> tuple[float, float, float]:
        first, second = rows
        distance = haversine_m(
            float(first["center_lat"]),
            float(first["center_lng"]),
            float(second["center_lat"]),
            float(second["center_lng"]),
        )
        time_delta = abs(
            (
                _aware_datetime(first["start_at"], "incident.start_at")
                - _aware_datetime(second["start_at"], "incident.start_at")
            ).total_seconds()
        ) / 60.0
        context_delta = abs(
            float(first["generator_profile"]["flood_latent"])
            - float(second["generator_profile"]["flood_latent"])
        ) + abs(
            float(first["generator_profile"]["urgency_latent"])
            - float(second["generator_profile"]["urgency_latent"])
        )
        return distance, time_delta, context_delta

    supportive = pair("spatial_overlap_context_supportive")
    if supportive is not None:
        distance, time_delta, context_delta = properties(supportive)
        if not (distance <= 900 and time_delta <= 30 and context_delta >= 0.90):
            errors.append("supportive family property gate failed")

    adversarial = pair("spatial_overlap_context_adversarial")
    if adversarial is not None:
        distance, time_delta, context_delta = properties(adversarial)
        if not (distance <= 800 and time_delta <= 30 and context_delta <= 0.25):
            errors.append("context-adversarial family property gate failed")

    temporal = pair("same_location_temporal")
    if temporal is not None:
        distance, time_delta, context_delta = properties(temporal)
        if not (distance <= 300 and time_delta >= 180 and context_delta <= 0.30):
            errors.append("temporal family property gate failed")

    distant = pair("distant_context_similar")
    if distant is not None:
        distance, time_delta, context_delta = properties(distant)
        if not (distance >= 60_000 and time_delta <= 30 and context_delta <= 0.25):
            errors.append("distant-context family property gate failed")

    unequal = pair("unequal_density")
    if unequal is not None:
        report_counts = [
            float(row["generator_profile"]["n_reports"]) for row in unequal
        ]
        spreads = [float(row["generator_profile"]["spread_m"]) for row in unequal]
        if max(report_counts) / min(report_counts) < 3.5:
            errors.append("unequal-density count-ratio gate failed")
        if max(spreads) / min(spreads) < 5.0:
            errors.append("unequal-density spread-ratio gate failed")

    multimodal = by_family.get("multimodal", [])
    if len(multimodal) != 1 or not multimodal[0].get("generator_profile", {}).get(
        "multimodal"
    ):
        errors.append("multimodal family property gate failed")
    if len(by_family.get("independent_stress", [])) != 3:
        errors.append("independent_stress must contain exactly three incidents")
    return errors


def validate_candidate_dataset(
    data: dict[str, Any],
    *,
    expected_seed: int | None = None,
    expected_split: str | None = None,
) -> dict[str, Any]:
    """Validate schema, integrity, duplicate semantics, and inference isolation.

    No clustering, priority, or preferred-method metric is part of this gate.
    A failing check raises `ValueError`; the returned profile is safe to store
    in a candidate manifest.
    """
    errors: list[str] = []
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if data.get("generator_version") != GENERATOR_VERSION:
        errors.append(f"generator_version must be {GENERATOR_VERSION!r}")
    if expected_seed is not None and data.get("seed") != expected_seed:
        errors.append("seed does not match requested seed")
    if expected_split is not None and data.get("split") != expected_split:
        errors.append("split does not match seed manifest")
    try:
        raw_seed = data.get("seed")
        if isinstance(raw_seed, bool) or not isinstance(raw_seed, int):
            raise ValueError("seed must be an integer")
        seed_value = raw_seed
        registered_split = registered_split_for_seed(seed_value)
        if registered_split is None:
            if data.get("split") != "unregistered":
                errors.append("unregistered seed must use split='unregistered'")
        elif data.get("split") != registered_split:
            errors.append(
                f"seed {seed_value} belongs to {registered_split}, not {data.get('split')}"
            )
    except (TypeError, ValueError) as exc:
        errors.append(f"invalid seed: {exc}")

    incidents = list(data.get("incidents", []))
    reports = list(data.get("reports", []))
    if not incidents:
        errors.append("incidents must not be empty")
    if not reports:
        errors.append("reports must not be empty")

    incident_ids = [row.get("incident_id") for row in incidents]
    report_ids = [row.get("event_id") for row in reports]
    if any(not isinstance(value, str) or not value for value in incident_ids):
        errors.append("incident_id must be a non-empty string")
    if any(not isinstance(value, str) or not value for value in report_ids):
        errors.append("event_id must be a non-empty string")
    if any(
        isinstance(value, str) and not OPAQUE_EVENT_ID.fullmatch(value)
        for value in report_ids
    ):
        errors.append("event_id must use the opaque uniform candidate format")
    if len(set(incident_ids)) != len(incident_ids):
        errors.append("incident_id must be unique")
    if len(set(report_ids)) != len(report_ids):
        errors.append("event_id must be unique")

    known_incidents = set(incident_ids)
    incident_by_id: dict[str, dict[str, Any]] = {
        str(row["incident_id"]): row
        for row in incidents
        if isinstance(row.get("incident_id"), str) and row.get("incident_id")
    }
    gt_labels: list[int] = []
    families: set[str] = set()
    for incident in incidents:
        try:
            if (
                isinstance(incident["gt_cluster"], bool)
                or not isinstance(incident["gt_cluster"], int)
                or isinstance(incident["n_true"], bool)
                or not isinstance(incident["n_true"], int)
                or isinstance(incident["v_true"], bool)
                or not isinstance(incident["v_true"], int)
            ):
                raise ValueError("gt_cluster/n_true/v_true must be integers")
            gt = int(incident["gt_cluster"])
            n_true = int(incident["n_true"])
            v_true = int(incident["v_true"])
            deadline = float(incident["deadline_min"])
            service = float(incident["service_demand_min"])
            center_lat = float(incident["center_lat"])
            center_lng = float(incident["center_lng"])
            _aware_datetime(incident["start_at"], "incident.start_at")
            if gt < 0:
                errors.append(f"{incident.get('incident_id')}: gt_cluster must be non-negative")
            if incident.get("scenario_family") not in REQUIRED_SCENARIO_FAMILIES:
                errors.append(f"{incident.get('incident_id')}: invalid scenario_family")
            if n_true <= 0 or not 0.0 <= v_true <= n_true:
                errors.append(f"{incident.get('incident_id')}: latent population invalid")
            if deadline <= 0 or service <= 0:
                errors.append(f"{incident.get('incident_id')}: outcome parameters invalid")
            if not (
                math.isfinite(deadline + service + center_lat + center_lng)
                and -90 <= center_lat <= 90
                and -180 <= center_lng <= 180
            ):
                errors.append(f"{incident.get('incident_id')}: latent numeric domain invalid")
            harm_curve = incident.get("harm_curve")
            if not isinstance(harm_curve, dict):
                errors.append(f"{incident.get('incident_id')}: harm_curve missing")
            elif harm_curve.get("type") not in ALLOWED_HARM_CURVES:
                errors.append(f"{incident.get('incident_id')}: invalid harm_curve type")
            else:
                try:
                    harm_values = [
                        float(harm_curve["grace_min"]),
                        float(harm_curve["slope"]),
                        float(harm_curve["capacity_penalty"]),
                    ]
                    if not all(math.isfinite(value) and value >= 0 for value in harm_values):
                        errors.append(
                            f"{incident.get('incident_id')}: invalid harm_curve parameters"
                        )
                except (KeyError, TypeError, ValueError):
                    errors.append(
                        f"{incident.get('incident_id')}: invalid harm_curve parameters"
                    )
            vulnerable_members = incident.get("vulnerable_member_indices")
            if (
                not isinstance(vulnerable_members, list)
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or not 0 <= value < n_true
                    for value in vulnerable_members
                )
                or len(set(vulnerable_members)) != len(vulnerable_members)
                or len(vulnerable_members) != v_true
            ):
                errors.append(
                    f"{incident.get('incident_id')}: vulnerable membership invalid"
                )
            gt_labels.append(gt)
            families.add(str(incident["scenario_family"]))
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"invalid incident record: {exc}")
    if len(set(gt_labels)) != len(gt_labels):
        errors.append("gt_cluster must be one-to-one with incident_id")
    missing_families = REQUIRED_SCENARIO_FAMILIES - families
    if missing_families:
        errors.append(f"missing scenario families: {sorted(missing_families)}")
    try:
        errors.extend(_validate_method_blind_family_properties(incidents))
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"invalid family-property record: {exc}")

    exact_groups: dict[str, list[dict[str, Any]]] = {}
    near_groups: dict[str, list[dict[str, Any]]] = {}
    fingerprint_groups: dict[str, list[dict[str, Any]]] = {}
    n_linked = n_fake = n_exact = n_near = 0
    total_membership_occurrences = 0
    unique_memberships: set[tuple[str, int]] = set()
    adversaries: set[str] = set()
    for report in reports:
        missing = [field for field in OBSERVABLE_FIELDS if field not in report]
        if missing:
            errors.append(f"{report.get('event_id')}: missing observable fields {missing}")
            continue
        try:
            if (
                isinstance(report["n_trapped"], bool)
                or not isinstance(report["n_trapped"], int)
            ):
                raise ValueError("n_trapped must be an integer")
            lat = float(report["lat"])
            lng = float(report["lng"])
            flood = float(report["flood"])
            urgency = float(report["urgency"])
            n_reported = int(report["n_trapped"])
            vulnerability = float(report["vulnerability"])
            _aware_datetime(report["created_at"], "report.created_at")
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                errors.append(f"{report['event_id']}: invalid coordinate")
            if not (0 <= flood <= 1 and 0 <= urgency <= 1):
                errors.append(f"{report['event_id']}: F/E outside [0,1]")
            if n_reported < 0 or vulnerability < 0:
                errors.append(f"{report['event_id']}: N/V must be non-negative")
            if not isinstance(report["has_image"], bool):
                errors.append(f"{report['event_id']}: has_image must be boolean")
            if report["source_type"] not in ALLOWED_SOURCE_TYPES:
                errors.append(f"{report['event_id']}: invalid source_type")
            if not isinstance(report["province"], str) or not report["province"]:
                errors.append(f"{report['event_id']}: province must be non-empty")
            if report["note"] != "synthetic_report":
                errors.append(
                    f"{report['event_id']}: observable note must use the neutral token"
                )
            missing_fields = report["missing_fields"]
            if (
                not isinstance(missing_fields, list)
                or any(field not in MISSINGNESS_FIELDS for field in missing_fields)
                or len(set(missing_fields)) != len(missing_fields)
                or missing_fields != sorted(missing_fields)
            ):
                errors.append(f"{report['event_id']}: invalid missing_fields mask")
            else:
                for field in missing_fields:
                    if float(report[field]) != 0.0:
                        errors.append(
                            f"{report['event_id']}: missing {field} must use locked zero imputation"
                        )
            if not math.isfinite(lat + lng + flood + urgency + vulnerability):
                errors.append(f"{report['event_id']}: non-finite numeric value")
        except (TypeError, ValueError) as exc:
            errors.append(f"{report.get('event_id')}: invalid observable value: {exc}")

        evaluation = report.get("evaluation_only")
        if not isinstance(evaluation, dict):
            errors.append(f"{report.get('event_id')}: evaluation_only missing")
            continue
        if "is_fake" in report:
            errors.append(f"{report.get('event_id')}: is_fake must be evaluation_only")
        if not isinstance(evaluation.get("is_fake"), bool):
            errors.append(f"{report.get('event_id')}: evaluation is_fake missing")
        incident_id = evaluation.get("incident_id")
        if incident_id is not None:
            n_linked += 1
            if str(incident_id) not in known_incidents:
                errors.append(f"{report['event_id']}: orphan incident_id")
            else:
                incident = incident_by_id[str(incident_id)]
                if evaluation.get("gt_cluster") != incident.get("gt_cluster"):
                    errors.append(f"{report['event_id']}: incident/gt mismatch")
                if evaluation.get("scenario_family") != incident.get("scenario_family"):
                    errors.append(f"{report['event_id']}: incident/family mismatch")
                members = evaluation.get("population_member_indices")
                vulnerable = evaluation.get("vulnerable_member_indices")
                if (
                    not isinstance(members, list)
                    or any(
                        isinstance(value, bool)
                        or not isinstance(value, int)
                        or not 0 <= value < int(incident["n_true"])
                        for value in members
                    )
                    or len(set(members)) != len(members)
                ):
                    errors.append(f"{report['event_id']}: population membership invalid")
                    members = []
                allowed_vulnerable = set(incident["vulnerable_member_indices"])
                if (
                    not isinstance(vulnerable, list)
                    or any(value not in set(members) for value in vulnerable)
                    or any(value not in allowed_vulnerable for value in vulnerable)
                    or len(set(vulnerable)) != len(vulnerable)
                ):
                    errors.append(f"{report['event_id']}: vulnerable membership invalid")
                    vulnerable = []
                expected_coverage_n = len(members) / int(incident["n_true"])
                expected_coverage_v = (
                    len(vulnerable) / int(incident["v_true"])
                    if int(incident["v_true"]) > 0
                    else 0.0
                )
                try:
                    if not math.isclose(
                        float(evaluation["coverage_n"]),
                        expected_coverage_n,
                        abs_tol=1e-6,
                    ):
                        errors.append(f"{report['event_id']}: coverage_n mismatch")
                    if not math.isclose(
                        float(evaluation["coverage_v"]),
                        expected_coverage_v,
                        abs_tol=1e-6,
                    ):
                        errors.append(f"{report['event_id']}: coverage_v mismatch")
                except (KeyError, TypeError, ValueError):
                    errors.append(f"{report['event_id']}: coverage fields invalid")
                total_membership_occurrences += len(members)
                unique_memberships.update((str(incident_id), value) for value in members)
        else:
            if evaluation.get("gt_cluster") is not None:
                errors.append(f"{report['event_id']}: unlinked report has gt_cluster")
            if evaluation.get("scenario_family") != "unlinked":
                errors.append(f"{report['event_id']}: unlinked family mismatch")
            if evaluation.get("population_member_indices") not in (None, []):
                errors.append(f"{report['event_id']}: unlinked report has population members")
            if evaluation.get("vulnerable_member_indices") not in (None, []):
                errors.append(f"{report['event_id']}: unlinked report has vulnerable members")
            if evaluation.get("coverage_n") is not None:
                errors.append(f"{report['event_id']}: unlinked report has coverage_n")
            if evaluation.get("coverage_v") is not None:
                errors.append(f"{report['event_id']}: unlinked report has coverage_v")
        kind = evaluation.get("duplicate_kind", "none")
        family_id = evaluation.get("duplicate_family_id")
        if kind not in {"none", "exact", "near"}:
            errors.append(f"{report['event_id']}: invalid duplicate_kind")
        if kind != "none" and not family_id:
            errors.append(f"{report['event_id']}: duplicate family missing")
        if kind == "none" and family_id is not None:
            errors.append(f"{report['event_id']}: non-duplicate has duplicate family")
        if kind == "exact":
            n_exact += 1
            exact_groups.setdefault(str(family_id), []).append(report)
        elif kind == "near":
            n_near += 1
            near_groups.setdefault(str(family_id), []).append(report)
        n_fake += int(bool(evaluation.get("is_fake", False)))
        adversary = evaluation.get("adversary")
        if adversary is not None:
            adversaries.add(str(adversary))

        leaked = FORBIDDEN_INFERENCE_FIELDS.intersection(observable_report(report))
        if leaked:
            errors.append(f"{report['event_id']}: inference leak {sorted(leaked)}")
        fingerprint_groups.setdefault(report_fingerprint(report), []).append(report)

    for family_id, rows in exact_groups.items():
        fingerprints = {report_fingerprint(row) for row in rows}
        if len(rows) < 2 or len(fingerprints) != 1:
            errors.append(f"exact duplicate family {family_id!r} is not identical")
        lineages = {
            (
                row["evaluation_only"].get("incident_id"),
                row["evaluation_only"].get("scenario_family"),
            )
            for row in rows
        }
        if len(lineages) != 1:
            errors.append(f"exact duplicate family {family_id!r} crosses lineage")
    for family_id, rows in near_groups.items():
        if len(rows) < 2 or any(not _near_duplicate_ok(rows[0], row) for row in rows[1:]):
            errors.append(f"near duplicate family {family_id!r} exceeds tolerance")
        if len({report_fingerprint(row) for row in rows}) != len(rows):
            errors.append(f"near duplicate family {family_id!r} contains exact payloads")
        lineages = {
            (
                row["evaluation_only"].get("incident_id"),
                row["evaluation_only"].get("scenario_family"),
            )
            for row in rows
        }
        if len(lineages) != 1:
            errors.append(f"near duplicate family {family_id!r} crosses lineage")
    shared_family_ids = set(exact_groups).intersection(near_groups)
    if shared_family_ids:
        errors.append(
            f"duplicate family IDs reused across kinds: {sorted(shared_family_ids)}"
        )

    for fingerprint, rows in fingerprint_groups.items():
        if len(rows) <= 1:
            continue
        declarations = {
            (
                row["evaluation_only"].get("duplicate_kind"),
                row["evaluation_only"].get("duplicate_family_id"),
            )
            for row in rows
        }
        if len(declarations) != 1 or next(iter(declarations))[0] != "exact":
            errors.append(
                f"observable exact duplicate {fingerprint[:12]} is not declared exact"
            )

    required_adversaries = {
        "low_conf_inflate_N",
        "low_conf_inflate_V",
        "low_conf_inflate_F",
        "low_conf_inflate_E",
        "coordinated_high_conf_campaign",
    }
    if n_linked == 0 or n_linked == len(reports):
        errors.append("dataset must contain linked and unlinked reports")
    if n_fake == 0:
        errors.append("dataset must contain evaluation fake cases")
    if n_exact == 0 or n_near == 0:
        errors.append("dataset must contain exact and near duplicate cases")
    if not required_adversaries.issubset(adversaries):
        errors.append(
            f"missing required adversaries: {sorted(required_adversaries - adversaries)}"
        )

    if errors:
        raise ValueError("candidate dataset failed quality gates:\n- " + "\n- ".join(errors))

    profile = {
        "status": "pass",
        "n_incidents": len(incidents),
        "n_reports": len(reports),
        "n_linked_reports": n_linked,
        "n_unlinked_reports": len(reports) - n_linked,
        "n_fake_reports": n_fake,
        "n_exact_duplicate_reports": n_exact,
        "n_near_duplicate_reports": n_near,
        "exact_duplicate_rate": round(n_exact / len(reports), 6),
        "near_duplicate_rate": round(n_near / len(reports), 6),
        "scenario_family_counts": {
            family: sum(1 for row in incidents if row["scenario_family"] == family)
            for family in sorted(families)
        },
        "latent_n_total": sum(int(row["n_true"]) for row in incidents),
        "latent_v_total": round(sum(float(row["v_true"]) for row in incidents), 6),
        "population_membership_occurrences": total_membership_occurrences,
        "unique_population_members_observed": len(unique_memberships),
        "population_overlap_rate": round(
            1.0 - len(unique_memberships) / total_membership_occurrences,
            6,
        )
        if total_membership_occurrences
        else 0.0,
        "adversary_cases": sorted(adversaries),
    }
    embedded_quality = data.get("quality")
    if embedded_quality not in ({}, None) and embedded_quality != profile:
        raise ValueError("candidate dataset failed quality gates:\n- embedded quality is stale")
    return profile
