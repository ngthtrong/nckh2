"""Lượng tử hóa INT8 mô hình ONNX MobileNetV3-Large và so sánh với FP32.

Lượng tử hóa tĩnh (QDQ, trọng số per-channel INT8, kích hoạt UINT8) bằng
onnxruntime.quantization, hiệu chỉnh trên một mẫu ảnh phân tầng theo lớp. Báo cáo:
kích thước file, độ trễ CPU (1 luồng), tỉ lệ trùng nhãn INT8 so với FP32 và độ chính
xác trên test độc lập. Calibration chỉ lấy train theo CSV đã lưu khi huấn luyện,
không tự chia lại dataset. INT8 có model_manifest_int8.json riêng, không ghi đè
manifest của cặp ONNX/PTE FP32. Mặc định lưu INT8 và manifest trong model/Edge Ai/Quantize.

    python quantize_model.py --onnx model.onnx --config config.json --split-csv split.csv --dataset-dir Dataset_Flood
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import statistics
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "model" / "Dataset_Flood"
REPORT_DIR = ROOT / "reports" / "quantization"

IMAGE_SIZE = 256
LETTERBOX_FILL = (124, 116, 104)
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
SEED = 42


def preprocess(path: Path, image_size: int = IMAGE_SIZE, fill=LETTERBOX_FILL) -> np.ndarray:
    """Letterbox 256×256 (bilinear, nền 124/116/104) + chuẩn hóa ImageNet, NCHW.

    EXIF transpose trước khi letterbox, giống notebook huấn luyện.
    """
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image = ImageOps.pad(image, (image_size, image_size), method=Image.Resampling.BILINEAR,
                             color=tuple(fill), centering=(0.5, 0.5))
        array = (np.asarray(image, dtype=np.float32) / 255.0 - MEAN) / STD
    return array.transpose(2, 0, 1)[None, ...].astype(np.float32)


def load_splits(csv_path: Path, dataset_dir: Path, class_order: list[str]) -> dict:
    """Dùng relative_path để remap CSV Colab; từ chối split bị trùng/leakage."""
    splits = {name: [] for name in ("train", "val", "test")}
    identities = {}
    root = dataset_dir.resolve()
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"split", "label"}.issubset(reader.fieldnames or []):
            raise ValueError("CSV thiếu cột split/label; cần CSV split của lần train, không phải records_after_clean.")
        for row in reader:
            split, label = row["split"], row["label"]
            if split not in splits or label not in class_order:
                raise ValueError(f"Split/label không hợp lệ: {split}/{label}")
            relative = row.get("relative_path", "").strip()
            path = (root / relative.replace("\\", "/")).resolve() if relative else Path(row["path"]).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError(f"Ảnh không có trong --dataset-dir: {path}")
            label_idx = class_order.index(label)
            if row.get("label_idx", "") and int(row["label_idx"]) != label_idx:
                raise ValueError(f"label_idx không khớp config: {path}")
            digest = hashlib.md5(path.read_bytes()).hexdigest()
            if row.get("md5", "") and row["md5"] != digest:
                raise ValueError(f"Ảnh đã thay đổi so với split train: {path}")
            keys = [("path", str(path)), ("md5", digest)]
            keys += [(field, row[field]) for field in ("split_group", "source_group") if row.get(field)]
            for key in keys:
                previous = identities.get(key)
                if previous is not None and (previous != split or key[0] == "path"):
                    raise ValueError(f"Split trùng/leakage: {key} ({previous}/{split})")
                identities[key] = split
            splits[split].append((path, label_idx))
    if not splits["train"] or not splits["test"]:
        raise ValueError("CSV cần có train và test không rỗng; không tự chia lại dataset.")
    return splits


class StratifiedReader:
    def __init__(self, items, input_name, per_class, config) -> None:
        if per_class <= 0:
            raise ValueError("--calib-per-class phải > 0")
        rng = random.Random(config.get("seed", SEED))
        chosen = []
        for label in range(len(config["class_order"])):
            pool = [path for path, y in items if y == label]
            if not pool:
                raise ValueError(f"Train thiếu lớp {config['class_order'][label]}")
            chosen += rng.sample(pool, min(per_class, len(pool)))
        self._batches = ({input_name: preprocess(path, config["image_size"], config["letterbox_fill"])}
                         for path in chosen)
        self.count = len(chosen)

    def get_next(self):
        return next(self._batches, None)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def session(path: Path):
    import onnxruntime as ort
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    return ort.InferenceSession(str(path), options, providers=["CPUExecutionProvider"])


def validate_input_shape(shape: list, image_size: int) -> None:
    if (len(shape) != 4 or shape[1:] != [3, image_size, image_size]
            or (isinstance(shape[0], int) and shape[0] != 1)):
        raise ValueError(f"ONNX input không khớp NCHW config: {shape}")


def quantized_probability_sum_atol(num_classes: int) -> float:
    """Sai số tổng lớn nhất do làm tròn từng probability UINT8 trong [0, 1]."""
    return num_classes / (2 * 255) + 1e-6


def validate_probabilities(output, num_classes: int, *, sum_atol: float = 1e-4) -> np.ndarray:
    array = np.asarray(output)
    if (array.shape != (1, num_classes) or array.dtype != np.float32
            or not np.isfinite(array).all() or (array < -1e-6).any()
            or (array > 1 + 1e-6).any()
            or not np.allclose(array.sum(axis=1), 1, atol=sum_atol, rtol=0)):
        raise ValueError(f"Output không phải FP32 probabilities [1,{num_classes}]: {array}")
    return array[0].copy()  # Một số runtime dùng lại buffer ở lần inference kế tiếp.


def evaluate(fp32: Path, int8: Path, items: list[tuple[Path, int]], config: dict) -> dict:
    if not items:
        raise ValueError("Test không được rỗng.")
    num_classes = len(config["class_order"])
    int8_sum_atol = quantized_probability_sum_atol(num_classes)
    s32, s8 = session(fp32), session(int8)
    name32, name8 = s32.get_inputs()[0].name, s8.get_inputs()[0].name
    x = preprocess(items[0][0], config["image_size"], config["letterbox_fill"])
    for _ in range(3):
        validate_probabilities(s32.run(None, {name32: x})[0], num_classes)
        validate_probabilities(s8.run(None, {name8: x})[0], num_classes, sum_atol=int8_sum_atol)
    y_true, p32, p8, t32, t8 = [], [], [], [], []
    for path, label in items:
        x = preprocess(path, config["image_size"], config["letterbox_fill"])
        start = time.perf_counter()
        out32 = s32.run(None, {name32: x})[0]
        t32.append((time.perf_counter() - start) * 1000)
        out32 = validate_probabilities(out32, num_classes)
        start = time.perf_counter()
        out8 = s8.run(None, {name8: x})[0]
        t8.append((time.perf_counter() - start) * 1000)
        out8 = validate_probabilities(out8, num_classes, sum_atol=int8_sum_atol)
        y_true.append(label)
        p32.append(int(np.argmax(out32)))
        p8.append(int(np.argmax(out8)))

    def metrics(pred: list[int]) -> dict:
        correct = sum(int(a == b) for a, b in zip(y_true, pred))
        f1s = []
        for c in range(len(config["class_order"])):
            tp = sum(1 for a, b in zip(y_true, pred) if a == c and b == c)
            fp = sum(1 for a, b in zip(y_true, pred) if a != c and b == c)
            fn = sum(1 for a, b in zip(y_true, pred) if a == c and b != c)
            f1s.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
        return {"accuracy": correct / len(y_true), "macro_f1": sum(f1s) / len(f1s)}

    return {
        "n_images": len(items),
        "fp32": {**metrics(p32), "latency_ms_median": statistics.median(t32)},
        "int8": {**metrics(p8), "latency_ms_median": statistics.median(t8)},
        "top1_agreement": sum(int(a == b) for a, b in zip(p32, p8)) / len(items),
    }


def int8_manifest(source: dict, int8: Path, split_csv: Path) -> dict:
    # Không kế thừa hash PTE FP32: đây là manifest của ONNX INT8 riêng.
    manifest = {key: source[key] for key in (
        "checkpoint_sha256", "input_size", "preprocess", "letterbox_fill", "class_order"
    )}
    digest = sha256(int8)
    manifest.update(
        onnx_sha256=digest, source_onnx_sha256=source["onnx_sha256"],
        version=f"mobilenetv3-int8-{digest[:12]}",
        precision="int8", quantization="QDQ_QInt8_weights_QUInt8_activations_per_channel",
        split_csv_sha256=sha256(split_csv), artifacts_complete=False,
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--onnx", type=Path, required=True, help="mô hình ONNX FP32")
    parser.add_argument("--config", type=Path, required=True, help="config đi kèm checkpoint")
    parser.add_argument("--split-csv", type=Path, required=True, help="CSV split đã dùng khi train checkpoint này")
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "model" / "Edge Ai" / "Quantize",
                        help="mặc định: model/Edge Ai/Quantize")
    parser.add_argument("--source-manifest", type=Path, help="mặc định: model_manifest.json cạnh ONNX FP32")
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--calib-per-class", type=int, default=50)
    args = parser.parse_args()

    source_path = args.source_manifest or args.onnx.parent / "model_manifest.json"
    manifest_path = args.out_dir / "model_manifest_int8.json"
    if manifest_path.resolve() == source_path.resolve():
        raise ValueError("Không được ghi đè source manifest bằng manifest INT8.")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    source = json.loads(source_path.read_text(encoding="utf-8"))
    if source["onnx_sha256"] != sha256(args.onnx):
        raise ValueError("ONNX không khớp hash trong source manifest.")
    expected_preprocess = "letterbox_rgb_" + "_".join(map(str, config["letterbox_fill"]))
    if (config.get("preprocess") != "letterbox" or source["preprocess"] != expected_preprocess
            or source["input_size"] != config["image_size"]
            or source["class_order"] != config["class_order"]
            or source["letterbox_fill"] != config["letterbox_fill"]):
        raise ValueError("Config preprocessing/class_order không khớp ONNX manifest.")
    splits = load_splits(args.split_csv, args.dataset_dir, config["class_order"])

    import onnxruntime as ort
    from onnxruntime.quantization import CalibrationDataReader, QuantFormat, QuantType, quantize_static
    from onnxruntime.quantization.shape_inference import quant_pre_process

    class Reader(StratifiedReader, CalibrationDataReader):
        pass

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    int8 = args.out_dir / "flood_mobilenetv3_large.int8.onnx"
    if int8.resolve() == args.onnx.resolve():
        raise ValueError("Input FP32 không được trùng output INT8.")

    input_info = session(args.onnx).get_inputs()[0]
    validate_input_shape(input_info.shape, config["image_size"])
    reader = Reader(splits["train"], input_info.name, args.calib_per_class, config)
    with tempfile.TemporaryDirectory(dir=args.out_dir) as temp:
        prepared = Path(temp) / "prepared.onnx"
        quant_pre_process(str(args.onnx), str(prepared))
        quantize_static(
            str(prepared), str(int8), reader,
            quant_format=QuantFormat.QDQ,
            per_channel=True,
            weight_type=QuantType.QInt8,
            activation_type=QuantType.QUInt8,
        )

    result = {
        "fp32_onnx": {"file": args.onnx.name, "bytes": args.onnx.stat().st_size, "sha256": sha256(args.onnx)},
        "int8_onnx": {"file": int8.name, "bytes": int8.stat().st_size, "sha256": sha256(int8)},
        "calibration_images": reader.count,
        "calibration_split": "train",
        "evaluation_split": "test",
        "split_csv": str(args.split_csv.resolve()),
        "split_csv_sha256": sha256(args.split_csv),
        "config_sha256": sha256(args.config),
        "seed": config.get("seed", SEED),
        "input_size": config["image_size"],
        "class_order": config["class_order"],
        "onnxruntime": ort.__version__,
        **evaluate(args.onnx, int8, splits["test"], config),
    }
    manifest_path.write_text(json.dumps(int8_manifest(source, int8, args.split_csv), indent=2), encoding="utf-8")
    (args.report_dir / "quantization.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    f, q = result["fp32"], result["int8"]
    mb = lambda n: n / 1024 / 1024  # noqa: E731
    report = f"""# Lượng tử hóa INT8 mô hình MobileNetV3-Large

Lượng tử hóa tĩnh QDQ (trọng số INT8 per-channel, kích hoạt UINT8), hiệu chỉnh trên
{result['calibration_images']} ảnh TRAIN phân tầng theo lớp; onnxruntime {result['onnxruntime']},
CPU 1 luồng.

| Chỉ số | FP32 | INT8 |
|---|---:|---:|
| Kích thước file | {mb(result['fp32_onnx']['bytes']):.1f} MB | {mb(result['int8_onnx']['bytes']):.1f} MB |
| Độ trễ suy luận (trung vị, CPU máy tính) | {f['latency_ms_median']:.1f} ms | {q['latency_ms_median']:.1f} ms |
| Accuracy trên {result['n_images']} ảnh TEST | {f['accuracy']:.2%} | {q['accuracy']:.2%} |
| Macro-F1 trên {result['n_images']} ảnh TEST | {f['macro_f1']:.2%} | {q['macro_f1']:.2%} |
| Trùng nhãn INT8 so với FP32 | – | {result['top1_agreement']:.2%} |

Metric chỉ lấy test trong `{args.split_csv}` (đúng CSV của checkpoint, không chia lại).
Seed calibration: {result['seed']}; input: {result['input_size']}×{result['input_size']}.
Độ trễ đo trên CPU máy tính sau 3 lượt warmup, không bao gồm preprocessing,
không phải trên điện thoại. Manifest INT8 riêng: `{manifest_path}`; không thay đổi FP32/PTE.

FP32: `{result['fp32_onnx']['file']}` sha256 `{result['fp32_onnx']['sha256'][:16]}…`;
INT8: `{result['int8_onnx']['file']}` sha256 `{result['int8_onnx']['sha256'][:16]}…`.
"""
    (args.report_dir / "quantization.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
