"""Freeze all registered candidate datasets with method-agnostic quality gates.

This is a data-production entry point, not tuning code. It reads the complete
locked seed manifest only to materialize the three disjoint data splits. It
does not run clustering, priority, or any test-set scientific metric.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from data.generate import write_candidate_bundle  # noqa: E402
from data.schema import canonical_json_bytes  # noqa: E402
from experiments.data_quality_report import (  # noqa: E402
    REPORT_SCHEMA_VERSION,
    write_distribution_report,
)

DEFAULT_SEED_MANIFEST = DEMO_ROOT / "protocol" / "seed_manifest.json"


def _load_splits(path: Path) -> dict[str, list[int]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    splits = payload.get("splits")
    if not isinstance(splits, dict):
        raise ValueError("seed manifest has no splits object")
    required = ("development", "calibration", "test")
    result: dict[str, list[int]] = {}
    seen: set[int] = set()
    for split in required:
        seeds = splits.get(split)
        if not isinstance(seeds, list) or any(
            isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds
        ):
            raise ValueError(f"invalid seed list: {split}")
        if seen.intersection(seeds):
            raise ValueError(f"seed overlap detected at split: {split}")
        seen.update(seeds)
        result[split] = seeds
    if [len(result[name]) for name in required] != [20, 20, 40]:
        raise ValueError("expected locked 20/20/40 split sizes")
    return result


def run(
    output_dir: Path,
    summary_path: Path,
    seed_manifest: Path = DEFAULT_SEED_MANIFEST,
) -> dict:
    seeds = _load_splits(seed_manifest)
    manifest = write_candidate_bundle(
        output_dir,
        seeds,
        seed_manifest=seed_manifest,
    )
    distribution_report_path = summary_path.parent / "data_distribution_report.json"
    _, distribution_report_sha256 = write_distribution_report(
        output_dir,
        distribution_report_path,
        manifest,
    )
    summary = {
        "schema_version": "candidate-data-quality-summary-v1",
        "purpose": "method-agnostic data freeze; no scientific test metrics",
        "dataset_manifest": str(output_dir / "manifest.json"),
        "distribution_report": str(distribution_report_path),
        "distribution_report_schema_version": REPORT_SCHEMA_VERSION,
        "distribution_report_sha256": distribution_report_sha256,
        "dataset_schema_version": manifest["dataset_schema_version"],
        "generator_version": manifest["generator_version"],
        "generator_sha256": manifest["generator_sha256"],
        "schema_sha256": manifest["schema_sha256"],
        "seed_manifest_sha256": manifest["seed_manifest_sha256"],
        "data_spec_sha256": manifest["data_spec_sha256"],
        "n_datasets": len(manifest["entries"]),
        "seed_counts": {split: len(values) for split, values in seeds.items()},
        "split_summaries": manifest["split_summaries"],
        "all_quality_gates_pass": all(
            row["quality_status"] == "pass" for row in manifest["entries"]
        ),
        "method_performance_gate_count": 0,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("xb") as stream:
        stream.write(canonical_json_bytes(summary))
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=(
            Path(os.environ["DEMO_WORK_DIR"]) / "datasets"
            if "DEMO_WORK_DIR" in os.environ
            else None
        ),
        required="DEMO_WORK_DIR" not in os.environ,
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=(
            Path(os.environ["DEMO_TABLES_DIR"]) / "data_quality_summary.json"
            if "DEMO_TABLES_DIR" in os.environ
            else None
        ),
        required="DEMO_TABLES_DIR" not in os.environ,
    )
    parser.add_argument(
        "--seed-manifest",
        type=Path,
        default=DEFAULT_SEED_MANIFEST,
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    summary = run(args.output_dir, args.summary, args.seed_manifest)
    print(
        f"frozen {summary['n_datasets']} datasets; "
        f"quality pass={summary['all_quality_gates_pass']}"
    )
    print(f"manifest: {summary['dataset_manifest']}")
    print(f"distribution report: {summary['distribution_report']}")
    print(f"summary: {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
