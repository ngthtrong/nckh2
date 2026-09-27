"""Lượng tử hóa INT8 mô hình ONNX MobileNetV3-Large và so sánh với FP32.

Lượng tử hóa tĩnh (QDQ, trọng số per-channel INT8, kích hoạt UINT8) bằng
onnxruntime.quantization, hiệu chỉnh trên một mẫu ảnh phân tầng theo lớp. Báo cáo:
kích thước file, độ trễ CPU (1 luồng), tỉ lệ trùng nhãn INT8 so với FP32 và độ chính
xác trên TOÀN BỘ Dataset_Flood.

Lưu ý: bộ dữ liệu gồm cả ảnh đã dùng để huấn luyện (file chia train/val/test không có
trong repo), nên độ chính xác ở đây chỉ để so sánh tương đối FP32 với INT8, không phải
độ chính xác trên tập test độc lập (xem notebook fe/model/1706.ipynb).

    python tools/quantize_model.py --onnx path/to/flood_mobilenetv3_large.onnx
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from onnxruntime.quantization import (
    CalibrationDataReader,
    QuantFormat,
    QuantType,
    quantize_static,
)
from onnxruntime.quantization.shape_inference import quant_pre_process
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "model" / "Dataset_Flood"
REPORT_DIR = ROOT / "reports" / "quantization"

CLASS_ORDER = ["low", "medium", "high", "non_flood"]
IMAGE_SIZE = 224
LETTERBOX_FILL = (124, 116, 104)
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
SEED = 42


def preprocess(path: Path) -> np.ndarray:
    """Letterbox 224×224 (bilinear, nền 124/116/104) + chuẩn hóa ImageNet, NCHW.

    Giống hệt notebook huấn luyện: không xoay ảnh theo EXIF.
    """
    with Image.open(path) as image:
        image = image.convert("RGB")
        image = ImageOps.pad(image, (IMAGE_SIZE, IMAGE_SIZE), method=Image.Resampling.BILINEAR,
                             color=LETTERBOX_FILL, centering=(0.5, 0.5))
        array = (np.asarray(image, dtype=np.float32) / 255.0 - MEAN) / STD
    return array.transpose(2, 0, 1)[None, ...].astype(np.float32)


def list_images() -> list[tuple[Path, int]]:
    items = []
    for label, name in enumerate(CLASS_ORDER):
        for path in sorted((DATASET_DIR / name).iterdir()):
            try:
                with Image.open(path):
                    items.append((path, label))
            except OSError:
                continue
    return items


class StratifiedReader(CalibrationDataReader):
    def __init__(self, items: list[tuple[Path, int]], input_name: str, per_class: int) -> None:
        rng = random.Random(SEED)
        chosen = []
        for label in range(len(CLASS_ORDER)):
            pool = [path for path, y in items if y == label]
            chosen += rng.sample(pool, min(per_class, len(pool)))
        self._batches = iter([{input_name: preprocess(path)} for path in chosen])
        self.count = len(chosen)

    def get_next(self):
        return next(self._batches, None)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def session(path: Path) -> ort.InferenceSession:
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    return ort.InferenceSession(str(path), options, providers=["CPUExecutionProvider"])


def evaluate(fp32: Path, int8: Path, items: list[tuple[Path, int]]) -> dict:
    s32, s8 = session(fp32), session(int8)
    name = s32.get_inputs()[0].name
    y_true, p32, p8, t32, t8 = [], [], [], [], []
    for path, label in items:
        x = preprocess(path)
        start = time.perf_counter()
        out32 = s32.run(None, {name: x})[0][0]
        t32.append((time.perf_counter() - start) * 1000)
        start = time.perf_counter()
        out8 = s8.run(None, {name: x})[0][0]
        t8.append((time.perf_counter() - start) * 1000)
        y_true.append(label)
        p32.append(int(np.argmax(out32)))
        p8.append(int(np.argmax(out8)))

    def metrics(pred: list[int]) -> dict:
        correct = sum(int(a == b) for a, b in zip(y_true, pred))
        f1s = []
        for c in range(len(CLASS_ORDER)):
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--onnx", type=Path, required=True, help="mô hình ONNX FP32")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "model" / "Edge Ai")
    parser.add_argument("--calib-per-class", type=int, default=50)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    prepared = args.out_dir / "flood_mobilenetv3_large.prep.onnx"
    int8 = args.out_dir / "flood_mobilenetv3_large.int8.onnx"

    items = list_images()
    input_name = session(args.onnx).get_inputs()[0].name
    quant_pre_process(str(args.onnx), str(prepared))
    reader = StratifiedReader(items, input_name, args.calib_per_class)
    quantize_static(
        str(prepared), str(int8), reader,
        quant_format=QuantFormat.QDQ,
        per_channel=True,
        weight_type=QuantType.QInt8,
        activation_type=QuantType.QUInt8,
    )
    prepared.unlink()

    result = {
        "fp32_onnx": {"file": args.onnx.name, "bytes": args.onnx.stat().st_size, "sha256": sha256(args.onnx)},
        "int8_onnx": {"file": int8.name, "bytes": int8.stat().st_size, "sha256": sha256(int8)},
        "calibration_images": reader.count,
        "onnxruntime": ort.__version__,
        **evaluate(args.onnx, int8, items),
    }
    (REPORT_DIR / "quantization.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    f, q = result["fp32"], result["int8"]
    mb = lambda n: n / 1024 / 1024  # noqa: E731
    report = f"""# Lượng tử hóa INT8 mô hình MobileNetV3-Large

Lượng tử hóa tĩnh QDQ (trọng số INT8 per-channel, kích hoạt UINT8), hiệu chỉnh trên
{result['calibration_images']} ảnh phân tầng theo lớp; onnxruntime {result['onnxruntime']},
CPU 1 luồng.

| Chỉ số | FP32 | INT8 |
|---|---:|---:|
| Kích thước file | {mb(result['fp32_onnx']['bytes']):.1f} MB | {mb(result['int8_onnx']['bytes']):.1f} MB |
| Độ trễ suy luận (trung vị, CPU máy tính) | {f['latency_ms_median']:.1f} ms | {q['latency_ms_median']:.1f} ms |
| Accuracy trên toàn bộ {result['n_images']} ảnh* | {f['accuracy']:.2%} | {q['accuracy']:.2%} |
| Macro-F1 trên toàn bộ {result['n_images']} ảnh* | {f['macro_f1']:.2%} | {q['macro_f1']:.2%} |
| Trùng nhãn INT8 so với FP32 | – | {result['top1_agreement']:.2%} |

\\* Toàn bộ `Dataset_Flood`, gồm cả ảnh đã dùng để huấn luyện, nên con số chỉ dùng để so
sánh FP32 với INT8. Độ chính xác trên tập test độc lập của mô hình FP32 là Accuracy 73,77%,
macro-F1 72,21% (244 ảnh, `fe/model/1706.ipynb`). Độ trễ đo trên CPU máy tính, không phải
trên điện thoại.

FP32: `{result['fp32_onnx']['file']}` sha256 `{result['fp32_onnx']['sha256'][:16]}…`;
INT8: `{result['int8_onnx']['file']}` sha256 `{result['int8_onnx']['sha256'][:16]}…`.
"""
    (REPORT_DIR / "quantization.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
