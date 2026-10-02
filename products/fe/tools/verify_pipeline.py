"""Xác minh kỹ thuật PTH/ONNX FP32 trên ảnh test thật, không train/export.

Từ tools/: python verify_pipeline.py (mặc định 3 ảnh).
Chẩn đoán không có ONNX Runtime: python verify_pipeline.py --onnx-engine reference
Full test: python verify_pipeline.py --full-test
Báo cáo: products/fe/reports/verification/. Exit: 0=pass_local, 1=fail, 2=incomplete.
Không chứng nhận Flutter, partition hay latency mobile. PTE/INT8 dùng script compare riêng.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.metadata
import json
from pathlib import Path

import numpy as np

from compare_models import (CONFIG_JSON, DATASET_DIR, EDGE_DIR, EXPORT_DIR, REPORTS_DIR,
                            ROOT, SPLIT_CSV, check_hash, check_manifest, evaluate_models,
                            pairwise_metrics, prepare_test, preprocess, pth_runner, sha256)
from quantize_model import MEAN, STD, session, validate_input_shape

CHECKS = ("preprocessing", "precision", "execution_provider", "graph_parity", "label_mapping")


def inspect_graph(path: Path, config: dict):
    import onnx

    graph = onnx.load(str(path))
    onnx.checker.check_model(graph, full_check=True)
    if len(graph.graph.input) != 1 or len(graph.graph.output) != 1:
        raise ValueError("Cần graph có một input và một output.")
    input_info, output_info = graph.graph.input[0], graph.graph.output[0]
    input_shape = [dim.dim_param or dim.dim_value or None
                   for dim in input_info.type.tensor_type.shape.dim]
    output_shape = [dim.dim_param or dim.dim_value or None
                    for dim in output_info.type.tensor_type.shape.dim]
    validate_input_shape(input_shape, config["image_size"])
    if len(output_shape) != 2 or output_shape[1] != len(config["class_order"]):
        raise ValueError(f"Output shape không khớp class_order: {output_shape}")
    if (input_info.type.tensor_type.elem_type != onnx.TensorProto.FLOAT
            or output_info.type.tensor_type.elem_type != onnx.TensorProto.FLOAT):
        raise ValueError("Input/output phải là float32.")
    operators = Counter(node.op_type for node in graph.graph.node)
    quantized = {name: count for name, count in operators.items() if "Quant" in name or "Integer" in name}
    initializer_types = Counter(onnx.TensorProto.DataType.Name(value.data_type)
                                for value in graph.graph.initializer)
    if quantized or any(name in initializer_types for name in ("FLOAT16", "BFLOAT16", "DOUBLE", "INT8", "UINT8")):
        raise ValueError("Graph không phải FP32 thuần; INT8 dùng compare_fp32_int8.py.")
    return graph, {"input_shape": input_shape, "output_shape": output_shape,
                   "input_dtype": "float32", "output_dtype": "float32",
                   "initializer_types": dict(initializer_types), "quantized_nodes": quantized,
                   "node_count": len(graph.graph.node), "operators": dict(operators)}


def check_softmax(graph) -> dict:
    output = graph.graph.output[0].name
    producer = next((node for node in graph.graph.node if output in node.output), None)
    if producer is None or producer.op_type != "Softmax":
        raise ValueError("Graph output không được tạo trực tiếp bởi Softmax.")
    opset = next(item.version for item in graph.opset_import if item.domain in ("", "ai.onnx"))
    axis = next((attribute.i for attribute in producer.attribute if attribute.name == "axis"),
                -1 if opset >= 13 else 1)
    if axis not in (1, -1):  # Output [batch, classes], softmax phải theo classes.
        raise ValueError(f"Softmax axis không theo classes: {axis}")
    return {"softmax_axis": axis, "opset": opset}


def finalize(result: dict) -> dict:
    statuses = [value["status"] for value in result["checks"].values()]
    result["passed_checks"] = statuses.count("pass")
    result["failed_checks"] = statuses.count("fail")
    result["not_tested_checks"] = statuses.count("not_tested")
    if result["preflight"]["status"] == "fail" or "fail" in statuses:
        result["status"], result["exit_code"] = "fail", 1
    elif "not_tested" in statuses:
        result["status"], result["exit_code"] = "incomplete", 2
    else:
        result["status"], result["exit_code"] = "pass_local", 0
    return result


def run_verification(args) -> dict:
    result = {
        "scope": "local_PTH_ONNX_FP32",
        "metadata": {"checkpoint": str(args.checkpoint.resolve()), "onnx": str(args.onnx.resolve()),
                     "onnx_engine": args.onnx_engine, "atol": args.atol, "rtol": args.rtol},
        "preflight": {"status": "not_tested"},
        "checks": {name: {"status": "not_tested", "reason": "Chưa chạy."} for name in CHECKS},
        "mobile": {"status": "not_tested",
                   "reason": "Không chạy Flutter/device; chưa kiểm tra pixel preprocessing, partition hoặc latency mobile."},
    }
    try:
        if not np.isfinite([args.atol, args.rtol]).all() or min(args.atol, args.rtol) < 0:
            raise ValueError("Tolerance phải hữu hạn và >= 0.")
        config, items, metadata = prepare_test(
            args.config, args.split_csv, args.dataset_dir, None if args.full_test else args.limit)
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        check_manifest(manifest, config)
        check_hash(args.checkpoint, manifest.get("checkpoint_sha256"))
        check_hash(args.onnx, manifest.get("onnx_sha256"))
        result["metadata"].update(metadata, n_images=len(items), class_order=config["class_order"],
                                  input_size=config["image_size"], manifest=str(args.manifest.resolve()),
                                  manifest_sha256=sha256(args.manifest),
                                  checkpoint_sha256=manifest["checkpoint_sha256"], onnx_sha256=manifest["onnx_sha256"])
        result["preflight"] = {"status": "pass", "reason": "Config/hash/split độc lập khớp; không tự chia lại dataset."}
    except Exception as error:
        result["preflight"] = {"status": "fail", "error": str(error)}
        return finalize(result)

    state = {}

    def check(name, function):
        try:
            result["checks"][name] = {"status": "pass", **function()}
        except Exception as error:
            result["checks"][name] = {"status": "fail", "error": str(error)}

    def preprocessing_check():
        for path, _ in items:
            tensor = preprocess(path, config["image_size"], config["letterbox_fill"])
            if (tensor.shape != (1, 3, config["image_size"], config["image_size"])
                    or tensor.dtype != np.float32 or not np.isfinite(tensor).all()):
                raise ValueError(f"Tensor ảnh không đúng NCHW/FP32: {path}")
        return {"n_images": len(items), "pipeline": "EXIF -> RGB -> letterbox BILINEAR -> ImageNet NCHW",
                "mean": MEAN.tolist(), "std": STD.tolist(), "flutter_pixel_parity": "not_tested"}

    def precision_check():
        graph, details = inspect_graph(args.onnx, config)
        state["graph"] = graph
        return details

    def runtime_check():
        if "graph" not in state:
            return {"status": "not_tested", "reason": "Graph chưa qua kiểm tra precision/shape."}
        if args.onnx_engine == "reference":
            from onnx.reference import ReferenceEvaluator
            state["runtime"] = ReferenceEvaluator(state["graph"])
            return {"status": "not_tested", "engine": "onnx.reference.ReferenceEvaluator",
                    "reason": "Chỉ kiểm tra số học; không xác nhận ONNX Runtime hay execution provider mobile."}
        runtime = session(args.onnx)
        state["runtime"] = runtime
        return {"engine": "onnxruntime", "version": importlib.metadata.version("onnxruntime"),
                "providers": runtime.get_providers(), "scope": "CPU desktop, 1 luồng",
                "mobile_partition": "not_tested"}

    def graph_parity_check():
        if "runtime" not in state:
            return {"status": "not_tested", "reason": "Không có runtime để chạy graph."}
        details = check_softmax(state["graph"])
        input_name = state["graph"].graph.input[0].name
        runners = {"pth": pth_runner(args.checkpoint, config),
                   "onnx": lambda tensor: state["runtime"].run(None, {input_name: tensor})[0]}
        probabilities, _, rows = evaluate_models(runners, items, config)
        state["probabilities"] = probabilities
        state["predictions"] = [{"image_path": row["image_path"], "ground_truth": row["ground_truth"],
                                 "pred_pth": row["pred_pth"], "pred_onnx": row["pred_onnx"]}
                                for row in rows]
        pair = pairwise_metrics(probabilities["pth"], probabilities["onnx"], args.atol, args.rtol)
        return {"status": "pass" if pair["probabilities_close"] else "fail",
                **details, **pair, "checkpoint_loading": "strict=True",
                "reason": "Sai số đo thực tế trên test, không phải accuracy hay chứng nhận toàn bộ dữ liệu."}

    def labels_check():
        labels = json.loads(args.labels.read_text(encoding="utf-8"))
        if labels != config["class_order"] or labels != manifest["class_order"]:
            raise ValueError(f"Thứ tự nhãn app/config/manifest không khớp: {labels}")
        if "probabilities" not in state:
            return {"status": "not_tested", "class_order": labels,
                    "reason": "Nhãn khớp nhưng chưa chạy output để xác minh argmax."}
        probabilities = state["probabilities"]
        agreement = float((probabilities["pth"].argmax(axis=1) == probabilities["onnx"].argmax(axis=1)).mean())
        return {"status": "pass" if agreement == 1 else "fail",
                "class_order": labels, "top1_agreement": agreement,
                "reason": "Đồng thuận trên ảnh đã kiểm tra; không đồng nghĩa accuracy 100%."}

    check("preprocessing", preprocessing_check)
    check("precision", precision_check)
    check("execution_provider", runtime_check)
    if result["checks"]["preprocessing"]["status"] == "pass":
        check("graph_parity", graph_parity_check)
    check("label_mapping", labels_check)
    if "predictions" in state:
        result["predictions"] = state["predictions"]
    return finalize(result)


def write_report(result: dict, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "verification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    lines = ["# Xác minh pipeline PTH/ONNX FP32", "", f"Local status: {result['status']} (exit {result['exit_code']}).",
             f"PASS: {result['passed_checks']}; FAIL: {result['failed_checks']}; NOT TESTED: {result['not_tested_checks']}.",
             f"Scope: {result['metadata'].get('evaluation_scope', 'preflight_only')}; "
             f"ảnh: {result['metadata'].get('n_images', 0)}; engine: {result['metadata']['onnx_engine']}.", "",
             f"Preflight: {result['preflight']['status']}.",
             result["preflight"].get("error", result["preflight"].get("reason", "")), "",
             "| Check | Status | Chi tiết |", "|---|---|---|"]
    for name, value in result["checks"].items():
        detail = value.get("error", value.get("reason", "Xem thông số trong verification.json."))
        lines.append(f"| {name} | {value['status']} | {detail.replace('|', '/').replace(chr(10), ' ')} |")
    lines += ["", "Mobile: NOT TESTED. " + result["mobile"]["reason"],
              "Đây là kiểm tra kỹ thuật cục bộ, không phải full-test accuracy hay nghiệm thu trên điện thoại."]
    report = "\n".join(lines) + "\n"
    (report_dir / "verification.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"Reports: {report_dir.resolve()}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint", type=Path, default=EDGE_DIR / "flood_mobilenetv3_large_best.pth")
    parser.add_argument("--onnx", type=Path, default=EXPORT_DIR / "flood_mobilenetv3_large.onnx")
    parser.add_argument("--manifest", type=Path, default=EXPORT_DIR / "model_manifest.json")
    parser.add_argument("--config", type=Path, default=CONFIG_JSON)
    parser.add_argument("--split-csv", type=Path, default=SPLIT_CSV)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--labels", type=Path, default=ROOT / "app" / "assets" / "labels.json")
    parser.add_argument("--report-dir", type=Path, default=REPORTS_DIR / "verification")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--limit", type=int, default=3)
    scope.add_argument("--full-test", action="store_true")
    parser.add_argument("--onnx-engine", choices=("ort", "reference"), default="ort")
    parser.add_argument("--atol", type=float, default=1e-5)
    parser.add_argument("--rtol", type=float, default=1e-4)
    args = parser.parse_args(argv)
    if not np.isfinite([args.atol, args.rtol]).all() or min(args.atol, args.rtol) < 0:
        parser.error("--atol/--rtol phải hữu hạn và >= 0.")
    result = run_verification(args)
    write_report(result, args.report_dir)
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
