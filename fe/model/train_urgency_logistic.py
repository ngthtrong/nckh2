"""Huấn luyện hai baseline Logistic Regression để tính urgency evidence E_i."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


SIGN_FEATURES = (
    "unresponsive",
    "respiratory_distress",
    "heavy_bleeding",
    "seizure",
    "major_trauma",
)
COMPACT_FEATURES = ("injured_count", "cannot_move", "severe_condition")
DETAILED_FEATURES = ("injured_count", "cannot_move", *SIGN_FEATURES)
TARGET = "urgency_label"
AUDIT_COLUMNS = ("labeled_by", "labeled_at", "label_note")
REQUIRED_COLUMNS = (
    "scenario_id",
    "injured_count",
    "cannot_move",
    *SIGN_FEATURES,
    "severe_condition",
    TARGET,
    *AUDIT_COLUMNS,
)
ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET = ROOT / "data" / "urgency_dataset.csv"
DEFAULT_OUTPUT = ROOT.parent / "app" / "assets" / "models" / "urgency_logistic.json"


def _binary(value: str, *, field: str, row_number: int) -> int:
    if value not in {"0", "1"}:
        raise ValueError(f"Dòng {row_number}: {field} phải là 0 hoặc 1.")
    return int(value)


def load_dataset(path: Path) -> list[dict[str, int | str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Dataset thiếu cột: {', '.join(missing)}")

        rows: list[dict[str, int | str]] = []
        labels_by_scenario: dict[str, int] = {}
        for row_number, source in enumerate(reader, start=2):
            scenario_id = source["scenario_id"].strip()
            if not scenario_id:
                raise ValueError(f"Dòng {row_number}: scenario_id không được để trống.")

            try:
                injured_count = int(source["injured_count"])
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Dòng {row_number}: injured_count phải là số nguyên không âm."
                ) from error
            if injured_count < 0:
                raise ValueError(f"Dòng {row_number}: injured_count không được âm.")

            row: dict[str, int | str] = {
                "scenario_id": scenario_id,
                "injured_count": injured_count,
                "cannot_move": _binary(
                    source["cannot_move"], field="cannot_move", row_number=row_number
                ),
            }
            for feature in SIGN_FEATURES:
                row[feature] = _binary(source[feature], field=feature, row_number=row_number)

            row["severe_condition"] = _binary(
                source["severe_condition"], field="severe_condition", row_number=row_number
            )
            derived_severe = int(any(int(row[feature]) for feature in SIGN_FEATURES))
            if row["severe_condition"] != derived_severe:
                raise ValueError(
                    f"Dòng {row_number}: severe_condition phải bằng OR của năm dấu hiệu."
                )

            label = _binary(source[TARGET], field=TARGET, row_number=row_number)
            previous_label = labels_by_scenario.setdefault(scenario_id, label)
            if previous_label != label:
                raise ValueError(
                    f"Dòng {row_number}: các bản ghi của {scenario_id} có urgency_label khác nhau."
                )
            row[TARGET] = label

            if not source["labeled_by"].strip():
                raise ValueError(f"Dòng {row_number}: labeled_by không được để trống.")
            if not source["labeled_at"].strip():
                raise ValueError(f"Dòng {row_number}: labeled_at không được để trống.")
            try:
                datetime.fromisoformat(source["labeled_at"].strip().replace("Z", "+00:00"))
            except ValueError as error:
                raise ValueError(
                    f"Dòng {row_number}: labeled_at phải theo ISO 8601."
                ) from error
            rows.append(row)

    scenario_labels = list(labels_by_scenario.values())
    class_counts = np.bincount(scenario_labels, minlength=2)
    if len(labels_by_scenario) < 6 or min(class_counts) < 3:
        raise ValueError(
            "Dataset cần ít nhất 6 scenario và mỗi urgency_label phải có ít nhất "
            "3 scenario để chia train/validation/test."
        )
    return rows


def split_by_scenario(
    rows: list[dict[str, int | str]], *, validation_ratio: float, test_ratio: float, seed: int
) -> tuple[list[dict[str, int | str]], list[dict[str, int | str]], list[dict[str, int | str]]]:
    labels_by_scenario: dict[str, int] = {}
    for row in rows:
        labels_by_scenario[str(row["scenario_id"])] = int(row[TARGET])

    scenario_ids = np.asarray(list(labels_by_scenario))
    scenario_labels = np.asarray([labels_by_scenario[item] for item in scenario_ids])
    test_count = min(len(scenario_ids) - 4, max(2, round(len(scenario_ids) * test_ratio)))
    train_val_ids, test_ids = train_test_split(
        scenario_ids,
        test_size=test_count,
        random_state=seed,
        stratify=scenario_labels,
    )
    train_val_labels = np.asarray([labels_by_scenario[item] for item in train_val_ids])
    relative_validation_ratio = validation_ratio / (1.0 - test_ratio)
    validation_count = min(
        len(train_val_ids) - 2,
        max(2, round(len(train_val_ids) * relative_validation_ratio)),
    )
    train_ids, validation_ids = train_test_split(
        train_val_ids,
        test_size=validation_count,
        random_state=seed,
        stratify=train_val_labels,
    )

    groups = {
        "train": set(train_ids),
        "validation": set(validation_ids),
        "test": set(test_ids),
    }
    split_rows = {
        name: [row for row in rows if row["scenario_id"] in scenario_group]
        for name, scenario_group in groups.items()
    }
    return split_rows["train"], split_rows["validation"], split_rows["test"]


def _matrix(
    rows: list[dict[str, int | str]], features: tuple[str, ...]
) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray([[float(row[feature]) for feature in features] for row in rows])
    y = np.asarray([int(row[TARGET]) for row in rows], dtype=np.int64)
    return x, y


def _metrics(labels: np.ndarray, probability: np.ndarray, threshold: float) -> dict[str, float]:
    prediction = (probability >= threshold).astype(np.int64)
    return {
        "accuracy": float(accuracy_score(labels, prediction)),
        "precision": float(precision_score(labels, prediction, zero_division=0)),
        "recall": float(recall_score(labels, prediction, zero_division=0)),
        "f1": float(f1_score(labels, prediction, zero_division=0)),
        "roc_auc": float(roc_auc_score(labels, probability)),
        "brier_score": float(brier_score_loss(labels, probability)),
    }


def _select_f1_threshold(labels: np.ndarray, probability: np.ndarray) -> float:
    candidates = sorted({0.5, *(float(value) for value in probability)})
    return max(
        candidates,
        key=lambda threshold: (
            f1_score(labels, probability >= threshold, zero_division=0),
            recall_score(labels, probability >= threshold, zero_division=0),
            -threshold,
        ),
    )


def _inference_latency_us(model: LogisticRegression, sample: np.ndarray) -> float:
    repetitions = 1_000
    started = time.perf_counter()
    for _ in range(repetitions):
        model.predict_proba(sample)
    return (time.perf_counter() - started) * 1_000_000 / repetitions


def _train_model(
    name: str,
    features: tuple[str, ...],
    train_rows: list[dict[str, int | str]],
    validation_rows: list[dict[str, int | str]],
    test_rows: list[dict[str, int | str]],
    *,
    seed: int,
    balanced: bool,
) -> dict:
    x_train, y_train = _matrix(train_rows, features)
    x_validation, y_validation = _matrix(validation_rows, features)
    x_test, y_test = _matrix(test_rows, features)
    model = LogisticRegression(
        solver="liblinear",
        max_iter=1000,
        random_state=seed,
        class_weight="balanced" if balanced else None,
    )
    model.fit(x_train, y_train)

    validation_probability = model.predict_proba(x_validation)[:, 1]
    selected_threshold = _select_f1_threshold(y_validation, validation_probability)
    test_probability = model.predict_proba(x_test)[:, 1]
    core = {
        "name": name,
        "feature_order": list(features),
        "intercept": float(model.intercept_[0]),
        "coefficients": {
            feature: float(coefficient)
            for feature, coefficient in zip(features, model.coef_[0], strict=True)
        },
        "development_threshold": 0.5,
        "selected_threshold": selected_threshold,
        "threshold_objective": "maximum_f1_on_validation",
    }
    core["evaluation"] = {
        "validation_at_0_5": _metrics(y_validation, validation_probability, 0.5),
        "validation_at_selected_threshold": _metrics(
            y_validation, validation_probability, selected_threshold
        ),
        "test_at_selected_threshold": _metrics(y_test, test_probability, selected_threshold),
        "serialized_size_bytes": len(
            json.dumps(core, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ),
        "host_python_inference_mean_us": _inference_latency_us(model, x_test[:1]),
    }
    return core


def train(
    dataset: Path,
    output: Path,
    *,
    validation_ratio: float,
    test_ratio: float,
    seed: int,
    balanced: bool,
) -> dict:
    rows = load_dataset(dataset)
    train_rows, validation_rows, test_rows = split_by_scenario(
        rows,
        validation_ratio=validation_ratio,
        test_ratio=test_ratio,
        seed=seed,
    )
    models = [
        _train_model(
            "compact",
            COMPACT_FEATURES,
            train_rows,
            validation_rows,
            test_rows,
            seed=seed,
            balanced=balanced,
        ),
        _train_model(
            "detailed",
            DETAILED_FEATURES,
            train_rows,
            validation_rows,
            test_rows,
            seed=seed,
            balanced=balanced,
        ),
    ]
    artifact = {
        "schema_version": 2,
        "model_type": "logistic_regression",
        "score_semantics": "urgency_evidence",
        "target": TARGET,
        "models": models,
        "training": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
            "row_count": len(rows),
            "scenario_count": len({str(row["scenario_id"]) for row in rows}),
            "split_row_counts": {
                "train": len(train_rows),
                "validation": len(validation_rows),
                "test": len(test_rows),
            },
            "random_seed": seed,
            "class_weight": "balanced" if balanced else None,
            "injured_count_transform": "raw",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return artifact


def self_test() -> None:
    samples = [
        ("safe-1", 0, 0, 0, 0, 0, 0, 0, 0, 0),
        ("safe-2", 1, 0, 0, 0, 0, 0, 0, 0, 0),
        ("safe-3", 0, 1, 0, 0, 0, 0, 0, 0, 0),
        ("safe-4", 1, 0, 0, 0, 0, 0, 0, 0, 0),
        ("safe-5", 1, 0, 0, 0, 0, 0, 0, 0, 0),
        ("safe-6", 0, 0, 0, 0, 0, 0, 0, 0, 0),
        ("urgent-1", 2, 1, 0, 0, 1, 0, 0, 1, 1),
        ("urgent-2", 3, 0, 1, 0, 0, 0, 0, 1, 1),
        ("urgent-3", 1, 1, 0, 1, 0, 0, 0, 1, 1),
        ("urgent-4", 5, 1, 1, 1, 0, 0, 0, 1, 1),
        ("urgent-5", 2, 0, 0, 0, 0, 1, 0, 1, 1),
        ("urgent-6", 4, 0, 0, 0, 0, 0, 1, 1, 1),
    ]
    with tempfile.TemporaryDirectory() as directory:
        dataset = Path(directory) / "dataset.csv"
        output = Path(directory) / "model.json"
        with dataset.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(REQUIRED_COLUMNS)
            for sample in samples:
                writer.writerow((*sample[:-1], sample[-1], "self-test", "2026-09-27T00:00:00Z", ""))
        artifact = train(
            dataset,
            output,
            validation_ratio=0.2,
            test_ratio=0.2,
            seed=42,
            balanced=False,
        )
        assert output.is_file()
        assert [model["name"] for model in artifact["models"]] == ["compact", "detailed"]
        assert artifact["training"]["scenario_count"] == len(samples)
        assert sum(artifact["training"]["split_row_counts"].values()) == len(samples)
    print("Self-test thành công.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--validation-ratio", type=float, default=0.2)
    parser.add_argument("--test-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--balanced", action="store_true", help="Cân bằng trọng số hai lớp.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return
    if not 0.1 <= args.validation_ratio <= 0.4:
        parser.error("--validation-ratio phải nằm trong khoảng 0.1 đến 0.4")
    if not 0.1 <= args.test_ratio <= 0.4:
        parser.error("--test-ratio phải nằm trong khoảng 0.1 đến 0.4")
    if args.validation_ratio + args.test_ratio > 0.6:
        parser.error("Tổng validation-ratio và test-ratio không được vượt quá 0.6")
    if not args.dataset.is_file():
        parser.error(f"Không tìm thấy dataset: {args.dataset}")

    artifact = train(
        args.dataset,
        args.output,
        validation_ratio=args.validation_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
        balanced=args.balanced,
    )
    print(f"Đã xuất model: {args.output}")
    for model in artifact["models"]:
        metrics = model["evaluation"]["test_at_selected_threshold"]
        print(f"{model['name']}: {json.dumps(metrics, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
