from __future__ import annotations

import copy
import gzip

import pytest

from demo.experiments.promote_results import (
    RAW_SECTION_PATHS,
    _render_number,
    _resolve_pointer,
    _walk_numeric,
    build_compact_summary,
    validate_compact_summary,
)


def _minimal_result() -> dict:
    return {
        "artifact_content_sha256": "a" * 64,
        "method_track_registry": {
            "selections": [{"method_id": "product_louvain"}],
            "exclusions": [{"method_id": "excluded"}],
        },
        "clustering": {
            "method_summaries": {
                "benchmark_label_aware": {
                    "product_louvain": {
                        "ari_labeled_reports": {
                            "mean": 0.923675,
                            "observations": [{"seed": 3000, "value": 0.9}],
                        }
                    }
                }
            },
            "per_seed_rows": [{"seed": 3000}],
        },
        "factorial_ablation": {
            "clustering": {"rows": [{"seed": 3000}]},
            "priority": {"rows": [{"seed": 3000}]},
        },
        "priority_robustness": {"scenario_rows": [{"seed": 3000}]},
        "dispatch_outcomes": {
            "per_seed_resource_policy_rows": [{"seed": 3000}]
        },
    }


def _minimal_selectors() -> dict:
    row = {
        "id": (
            "clustering.summary.benchmark_label_aware.product_louvain."
            "ari_labeled_reports"
        ),
        "kind": "method_endpoint_summary",
        "json_pointer": (
            "/clustering/method_summaries/benchmark_label_aware/"
            "product_louvain/ari_labeled_reports"
        ),
    }
    # The production validator requires the complete 448-row registry.  Reuse
    # a valid pointer while preserving unique ids for this projection fixture.
    rows = [{**row, "id": f"{row['id']}.{index}"} for index in range(448)]
    return {"selector_count": 448, "selectors": rows}


def test_compact_summary_removes_only_raw_blocks_and_keeps_selectors() -> None:
    result = _minimal_result()
    selectors = _minimal_selectors()
    compact = build_compact_summary(
        result,
        source_record={"result_sha256": "b" * 64},
        raw_archive_record={"sha256": "c" * 64},
        gate3_lock_sha256="d" * 64,
    )
    validation = validate_compact_summary(compact, selectors=selectors)
    assert validation["status"] == "pass"
    assert validation["base_selector_count"] == 448
    assert (
        _resolve_pointer(
            compact,
            selectors["selectors"][0]["json_pointer"],
        )["mean"]
        == 0.923675
    )
    for pointer in RAW_SECTION_PATHS:
        with pytest.raises(ValueError):
            _resolve_pointer(compact, pointer)
    assert result == _minimal_result()


def test_compact_content_hash_rejects_mutation() -> None:
    compact = build_compact_summary(
        _minimal_result(),
        source_record={"result_sha256": "b" * 64},
        raw_archive_record={"sha256": "c" * 64},
        gate3_lock_sha256="d" * 64,
    )
    compact["clustering"]["method_summaries"]["benchmark_label_aware"][
        "product_louvain"
    ]["ari_labeled_reports"]["mean"] = 0.1
    with pytest.raises(ValueError, match="checksum"):
        validate_compact_summary(compact, selectors=_minimal_selectors())


def test_numeric_walk_skips_raw_observations_and_boolean_values() -> None:
    value = {
        "mean": 0.5,
        "n": 40,
        "flag": True,
        "paired_confidence_interval": [0.4, 0.6],
        "observations": [{"seed": 3000, "value": 0.5}],
    }
    assert list(_walk_numeric(value)) == [
        ("/mean", 0.5),
        ("/n", 40),
        ("/paired_confidence_interval/0", 0.4),
        ("/paired_confidence_interval/1", 0.6),
    ]


@pytest.mark.parametrize(
    ("value", "rendered"),
    [
        (40, "40"),
        (0.0, "0"),
        (0.923675, "0.9237"),
        (-0.0315725, "-0.0316"),
        (34.85, "34.850"),
        (5.093e-11, "5.09e-11"),
    ],
)
def test_render_number_is_deterministic(value: int | float, rendered: str) -> None:
    assert _render_number(value)[0] == rendered


def test_complete_archive_is_lossless_and_deterministic() -> None:
    payload = b'{"locked":true}\n'
    first = gzip.compress(payload, compresslevel=9, mtime=0)
    second = gzip.compress(payload, compresslevel=9, mtime=0)
    assert first == second
    assert gzip.decompress(first) == payload
