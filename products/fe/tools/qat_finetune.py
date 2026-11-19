"""Fine-tune a trained MobileNetV3 with QAT and export an ONNX QDQ model.

Run from tools/: python qat_finetune.py
The saved train/val split is used for fitting and checkpoint selection; test is
not used for fitting or observer calibration. Export compatibility is checked
before fine-tuning; non-fused PyTorch fake quantization exports as ONNX Q/DQ.
Reference graph parity and optimized INT8 runtime drift are checked separately.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from compare_models import (CONFIG_JSON, DATASET_DIR, EDGE_DIR, EXPORT_DIR as FP32_EXPORT_DIR,
                            SPLIT_CSV, check_manifest)
from convert_model import build_model, load_checkpoint, remove_module_prefix
from quantize_model import (load_splits, preprocess, quantized_probability_sum_atol, session, sha256,
                            validate_input_shape, validate_probabilities)

CHECKPOINT = EDGE_DIR / "flood_mobilenetv3_large_best.pth"
QAT_DIR = EDGE_DIR / "QAT"
DEFAULT_QAT_ONNX = QAT_DIR / "flood_mobilenetv3_large.qat.int8.onnx"
DEFAULT_QAT_CHECKPOINT = QAT_DIR / "flood_mobilenetv3_large_qat_best.pth"
IMAGE_MEAN = (0.485, 0.456, 0.406)
IMAGE_STD = (0.229, 0.224, 0.225)
SEVERITY_RANK = {"non_flood": 0, "low": 1, "medium": 2, "high": 3}
LOGGER = logging.getLogger(__name__)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    import torch

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def make_dataset(items, config: dict, *, training: bool):
    import torch
    from torch.utils.data import Dataset
    from torchvision import transforms

    class FloodDataset(Dataset):
        def __init__(self):
            self.items = items
            ops = []
            if training:
                ops.extend([
                    transforms.RandomHorizontalFlip(p=0.5),
                    transforms.RandomAffine(degrees=4, translate=(0.03, 0.03),
                                            scale=(0.95, 1.05), fill=tuple(config["letterbox_fill"])),
                    transforms.ColorJitter(brightness=0.12, contrast=0.12,
                                           saturation=0.08, hue=0.02),
                ])
            ops.extend([transforms.ToTensor(), transforms.Normalize(IMAGE_MEAN, IMAGE_STD)])
            self.transform = transforms.Compose(ops)

        def __len__(self):
            return len(self.items)

        def __getitem__(self, index):
            path, label = self.items[index]
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                image = ImageOps.pad(
                    image,
                    (config["image_size"], config["image_size"]),
                    method=Image.Resampling.BILINEAR,
                    color=tuple(config["letterbox_fill"]),
                    centering=(0.5, 0.5),
                )
            return self.transform(image), label

    return FloodDataset()


def evaluate(model, loader, device, config: dict, *, log_every: int = 10) -> dict:
    import torch
    from torch.ao.quantization import disable_observer
    from sklearn.metrics import accuracy_score, f1_score

    model.eval()
    model.apply(disable_observer)  # Validation must not update quantization statistics.
    started = time.perf_counter()
    LOGGER.info("Validation started: %d images, %d batches; observers frozen", len(loader.dataset), len(loader))
    labels, predictions = [], []
    with torch.inference_mode():
        for batch, (images, targets) in enumerate(loader, 1):
            logits = model(images.to(device))
            labels.extend(targets.tolist())
            predictions.extend(logits.argmax(dim=1).cpu().tolist())
            if batch == 1 or batch % log_every == 0 or batch == len(loader) or LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.info("Validation batch %d/%d | images=%d/%d | elapsed=%.1fs",
                            batch, len(loader), len(labels), len(loader.dataset), time.perf_counter() - started)
    ranks = np.asarray([SEVERITY_RANK[name] for name in config["class_order"]])
    distances = np.abs(ranks[np.asarray(labels)] - ranks[np.asarray(predictions)])
    metrics = {
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "critical_error_count": int((distances >= config.get("critical_distance", 2)).sum()),
        "critical_error_rate": float(np.mean(distances >= config.get("critical_distance", 2))),
    }
    LOGGER.info("Validation completed in %.1fs | accuracy=%.4f | macro_f1=%.4f | critical=%d",
                time.perf_counter() - started, metrics["accuracy"], metrics["macro_f1"], metrics["critical_error_count"])
    return metrics


def prepare_qat_model(model, image_size: int, backend: str):
    import torch
    from torch.ao.quantization import get_default_qat_qconfig_mapping
    from torch.ao.quantization.quantize_fx import prepare_qat_fx

    # Version 0 uses exportable FakeQuantize, not fused_moving_avg_obs_fake_quant.
    LOGGER.info("Preparing QAT graph: backend=%s, input=1x3x%dx%d, exportable fake quantization",
                backend, image_size, image_size)
    # Sharing input/output qparams across average pooling makes integer half-way
    # means sensitive to FP32 reduction order. Native mapping inserts a separate
    # observer after FP32 pooling; all Conv/Linear weight quantizers stay enabled.
    mapping = get_default_qat_qconfig_mapping(backend, version=0)
    mapping.set_object_type(torch.nn.AdaptiveAvgPool2d, None)
    LOGGER.info("QAT policy: AdaptiveAvgPool2d excluded; separate pooling boundary observers; Conv/Linear still QAT")
    return prepare_qat_fx(
        model.train(), mapping,
        (torch.zeros(1, 3, image_size, image_size),),
    )


def frozen_weight_codes(model, sample):
    """Preserve PyTorch's rounding at half-integer weight quantization boundaries."""
    import torch

    codes, hooks = {}, []

    def capture(module, inputs, output, *, name):
        if not int(module.fake_quant_enabled[0]):
            raise RuntimeError(f"Weight fake quantization is disabled: {name}")
        shape = [1] * output.ndim
        if module.scale.numel() > 1:
            shape[module.ch_axis] = -1
        integer = torch.round(output.detach() / module.scale.reshape(shape)) + module.zero_point.reshape(shape)
        if not torch.isfinite(integer).all() or (integer < module.quant_min).any() or (integer > module.quant_max).any():
            raise RuntimeError(f"Invalid quantized weights: {name}")
        dtype = torch.int8 if module.quant_min < 0 else torch.uint8
        codes[f"model.{name}.scale"] = integer.to(dtype).cpu().numpy()

    try:
        from functools import partial
        for name, module in model.named_modules():
            if name.endswith("weight_fake_quant"):
                hooks.append(module.register_forward_hook(partial(capture, name=name)))
        with torch.no_grad():
            model(sample)
    finally:
        for hook in hooks:
            hook.remove()
    return codes


def protect_int32_bias(graph) -> int:
    """Raise scales only where decoded weights are zero; never change their values."""
    from onnx import numpy_helper

    initializers = {value.name: value for value in graph.graph.initializer}
    producers = {output: node for node in graph.graph.node for output in node.output}

    def array(name):
        while name in producers and producers[name].op_type == "Identity":
            name = producers[name].input[0]
        if name in producers and producers[name].op_type == "Constant":
            return numpy_helper.to_array(next(attribute.t for attribute in producers[name].attribute if attribute.name == "value"))
        return numpy_helper.to_array(initializers[name])

    protected = 0
    for node in graph.graph.node:
        if node.op_type not in ("Conv", "Gemm") or len(node.input) < 3:
            continue
        activation = producers.get(node.input[0])
        weight = producers.get(node.input[1])
        if activation is None or weight is None or activation.op_type != "DequantizeLinear" or weight.op_type != "DequantizeLinear":
            continue
        integer, scale, zero = (array(name) for name in weight.input[:3])
        bias = array(node.input[2]).reshape(-1)
        scale = np.broadcast_to(scale, bias.shape).copy()
        zero = np.broadcast_to(zero, bias.shape)
        if integer.shape[0] != len(bias):
            raise RuntimeError(f"Unsupported bias/weight channel layout: {node.name}")
        input_scale = float(array(activation.input[1]).reshape(()))
        if not np.isfinite(input_scale) or input_scale <= 0 or not np.isfinite(bias).all() or not np.isfinite(scale).all() or (scale <= 0).any():
            raise RuntimeError(f"Invalid bias/quantization scale: {node.name}")
        # Half the INT32 limit leaves room for FP32 rounding in runtime bias conversion.
        required = np.abs(bias.astype(np.float64)) / (input_scale * (np.iinfo(np.int32).max // 2))
        unsafe = required > scale
        if not unsafe.any():
            continue
        zero_channels = np.all(integer.reshape(len(bias), -1) == zero[:, None], axis=1)
        if (unsafe & ~zero_channels).any():
            raise RuntimeError(f"INT32 bias overflow in nonzero weight channels: {node.name}; refusing to change learned weights.")
        scale = np.maximum(scale, required).astype(np.float32)
        if not any(attribute.name == "axis" for attribute in weight.attribute):
            if not zero_channels.all():
                raise RuntimeError(f"Cannot change a shared per-tensor scale of nonzero weights: {node.name}")
            scale = np.array(scale.max(), dtype=np.float32)
        name = weight.output[0] + "__bias_safe_scale"
        while name in initializers:
            name += "_"
        value = numpy_helper.from_array(scale, name)
        graph.graph.initializer.append(value)
        initializers[name] = value
        weight.input[1] = name
        protected += int(unsafe.sum())
    return protected


def export_qdq(model, onnx_path: Path, image_size: int, *, check_samples=None) -> dict:
    import onnx
    import onnxruntime as ort
    from onnx import numpy_helper
    import torch
    from torch.ao.quantization import disable_observer
    from convert_model import ProbabilityModel

    started = time.perf_counter()
    LOGGER.info("Exporting QAT ONNX Q/DQ: %s", onnx_path)
    onnx_path.parent.mkdir(parents=True, exist_ok=True)
    model = model.to("cpu").eval()
    model.apply(disable_observer)  # Freeze every child before tracing/export.
    sample = torch.zeros(1, 3, image_size, image_size)
    check_samples = [sample] if check_samples is None else list(check_samples)
    if not check_samples:
        raise ValueError("Export smoke samples must not be empty.")
    check_samples = [torch.as_tensor(value).detach().cpu() for value in check_samples]
    for value in check_samples:
        if value.dtype != torch.float32 or value.shape != sample.shape or not torch.isfinite(value).all():
            raise ValueError("Export smoke samples must be finite FP32 tensors [1,3,H,W].")
    weight_codes = frozen_weight_codes(model, sample)
    with tempfile.NamedTemporaryFile(suffix=".onnx", dir=onnx_path.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        torch.onnx.export(
            ProbabilityModel(model).eval(), sample, temporary,
            input_names=["image"], output_names=["probabilities"],
            dynamic_axes={"image": {0: "batch"}, "probabilities": {0: "batch"}},
            opset_version=17, dynamo=False,
        )
        LOGGER.info("ONNX tracing completed in %.1fs; checking graph and residual qparams",
                    time.perf_counter() - started)
        graph = onnx.load(str(temporary))
        frozen = set()
        for node in list(graph.graph.node):
            if node.op_type == "QuantizeLinear" and "weight_fake_quant" in node.name:
                key = node.input[1]
                if key not in weight_codes:
                    raise RuntimeError(f"Cannot map quantized weight to PyTorch observer: {node.name}")
                graph.graph.initializer.append(numpy_helper.from_array(weight_codes[key], node.output[0]))
                graph.graph.node.remove(node)
                frozen.add(key)
        if frozen != set(weight_codes):
            raise RuntimeError("ONNX export omitted a weight fake-quant module.")
        protected = protect_int32_bias(graph)
        LOGGER.info("Preserved %d INT8 weight tensors; protected %d zero-weight channels against INT32 bias overflow",
                    len(frozen), protected)
        # Per-tensor qparams must be scalars for ORT's QLinearAdd residual fusion.
        # Reshape only singleton qparams, never change values or per-channel axes.
        initializers = {value.name: value for value in graph.graph.initializer}
        aliases = {node.output[0]: node.input[0] for node in graph.graph.node if node.op_type == "Identity"}
        scalar_names = {}
        for node in graph.graph.node:
            if node.op_type not in ("QuantizeLinear", "DequantizeLinear") or any(
                attribute.name == "axis" for attribute in node.attribute
            ):
                continue
            for index in (1, 2):
                name = node.input[index]
                while name in aliases:
                    name = aliases[name]
                value = initializers.get(name)
                if value is None or list(value.dims) != [1]:
                    continue
                if name not in scalar_names:
                    scalar_name = name + "__scalar"
                    while scalar_name in initializers:
                        scalar_name += "_"
                    scalar = numpy_helper.from_array(numpy_helper.to_array(value).reshape(()), scalar_name)
                    graph.graph.initializer.append(scalar)
                    initializers[scalar_name] = scalar
                    scalar_names[name] = scalar_name
                node.input[index] = scalar_names[name]
        used = {name for node in graph.graph.node for name in node.input}
        used.update(value.name for value in (*graph.graph.input, *graph.graph.output))
        for name in scalar_names:
            if name not in used:
                graph.graph.initializer.remove(initializers[name])
        from onnx.utils import Extractor
        graph = Extractor(graph).extract_model([value.name for value in graph.graph.input],
                                               [value.name for value in graph.graph.output])
        onnx.checker.check_model(graph)
        operations = {node.op_type for node in graph.graph.node}
        if not {"QuantizeLinear", "DequantizeLinear"}.issubset(operations):
            raise RuntimeError("ONNX exporter did not preserve QAT as Q/DQ nodes; refusing FP32 export.")
        onnx.save(graph, str(temporary))
        LOGGER.info("Q/DQ graph checked: %d quantizers, %d dequantizers; validating ONNX Runtime",
                    sum(node.op_type == "QuantizeLinear" for node in graph.graph.node),
                    sum(node.op_type == "DequantizeLinear" for node in graph.graph.node))
        runtime = session(temporary)
        # This is ONLY an export-reference check. The deployment session above
        # retains its default optimizations and must still run real INT8 kernels.
        reference_options = ort.SessionOptions()
        reference_options.intra_op_num_threads = reference_options.inter_op_num_threads = 1
        reference_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
        reference = ort.InferenceSession(str(temporary), reference_options, providers=["CPUExecutionProvider"])
        input_info = runtime.get_inputs()[0]
        validate_input_shape(input_info.shape, image_size)
        max_difference, agreement, close = 0.0, 0, True
        reference_difference, reference_close = 0.0, True
        for value in check_samples:
            with torch.inference_mode():
                expected = torch.softmax(model(value), dim=1).numpy()
            validate_probabilities(expected, expected.shape[1])
            reference_output = reference.run(None, {input_info.name: value.numpy()})[0]
            validate_probabilities(reference_output, expected.shape[1])
            reference_difference = max(reference_difference, float(np.max(np.abs(reference_output - expected))))
            reference_close = reference_close and bool(np.allclose(reference_output, expected, atol=1e-5, rtol=1e-4))
            actual = runtime.run(None, {input_info.name: value.numpy()})[0]
            validate_probabilities(actual, expected.shape[1])
            difference = float(np.max(np.abs(actual - expected)))
            max_difference = max(max_difference, difference)
            agreement += int(actual.argmax() == expected.argmax())
            close = close and bool(np.allclose(actual, expected, atol=1e-5, rtol=1e-4))
        checks = {"samples": len(check_samples), "weight_tensors_int8": len(frozen),
                  "bias_channels_protected": protected, "max_abs_diff": max_difference,
                  "top1_agreement": agreement / len(check_samples), "probabilities_close": close,
                  "reference_max_abs_diff": reference_difference, "reference_probabilities_close": reference_close,
                  "reference_optimization": "ORT_DISABLE_ALL", "runtime_optimization": "ORT_ENABLE_ALL",
                  "atol": 1e-5, "rtol": 1e-4}
        del reference, runtime
        LOGGER.info("Export reference (no INT8 fusion): max_abs_diff=%.8g, probabilities_close=%s",
                    reference_difference, reference_close)
        if not reference_close:
            # Fake quantization rounds after FP32 arithmetic: a tiny reduction
            # or reciprocal/division difference can cross an INT8 half-way bin.
            # Do not label this a parity PASS or mistake it for a malformed graph.
            LOGGER.warning("Reference probabilities differ from PyTorch fake quantization; "
                           "strict graph parity NOT proven. FP32 rounding boundaries can propagate "
                           "through Q/DQ; evaluate the saved independent test split before deployment.")
        LOGGER.info("Optimized INT8 runtime smoke: top1 agreement=%d/%d, max_abs_diff=%.8g, probabilities_close=%s",
                    agreement, len(check_samples), max_difference, close)
        if not close:
            LOGGER.warning("Optimized INT8 runtime differs from PyTorch fake quantization; "
                           "NOT a strict runtime parity PASS. "
                           "Run full independent-test comparison before deployment.")
        os.replace(temporary, onnx_path)
        LOGGER.info("QAT ONNX execution/schema checks passed (strict parity=%s); saved %s (%.2f MiB) in %.1fs",
                    close, onnx_path, onnx_path.stat().st_size / 1024**2, time.perf_counter() - started)
        return checks
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    parser.add_argument("--config", type=Path, default=CONFIG_JSON)
    parser.add_argument("--split-csv", type=Path, default=SPLIT_CSV)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--fp32-onnx", type=Path, default=FP32_EXPORT_DIR / "flood_mobilenetv3_large.onnx")
    parser.add_argument("--source-manifest", type=Path, default=EDGE_DIR / "Export" / "model_manifest.json")
    parser.add_argument("--out-onnx", type=Path, default=DEFAULT_QAT_ONNX)
    parser.add_argument("--out-checkpoint", type=Path, default=DEFAULT_QAT_CHECKPOINT)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--patience", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--backbone-lr", type=float, default=1e-6)
    parser.add_argument("--head-lr", type=float, default=1e-5)
    parser.add_argument("--freeze-observers-after", type=int, default=2)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--log-file", type=Path, help="default: <out-onnx folder>/qat_finetune.log; append across runs")
    parser.add_argument("--log-every", type=int, default=10, help="log progress every N batches (default: 10)")
    parser.add_argument("--verbose", action="store_true", help="log every train/validation batch")
    parser.add_argument("--check-export-only", action="store_true", help="check export on 3 train images; no fitting or model artifact output")
    args = parser.parse_args()
    log_path = args.log_file or args.out_onnx.parent / "qat_finetune.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S", force=True,
                        handlers=[logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8")])
    LOGGER.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    started = time.perf_counter()
    LOGGER.info("Starting QAT fine-tuning; log=%s", log_path.resolve())
    LOGGER.info("Options: epochs=%d, batch_size=%d, backbone_lr=%g, head_lr=%g, freeze_after=%d, num_workers=%d",
                args.epochs, args.batch_size, args.backbone_lr, args.head_lr, args.freeze_observers_after, args.num_workers)
    if args.log_every <= 0:
        raise ValueError("--log-every phải > 0.")
    if min(args.epochs, args.patience, args.batch_size) <= 0 or args.num_workers < 0:
        raise ValueError("epochs, patience, batch-size phải > 0; num-workers không âm.")
    if not 1 <= args.freeze_observers_after <= args.epochs:
        raise ValueError("freeze-observers-after phải từ 1 đến epochs.")

    LOGGER.info("Loading PyTorch and training dependencies...")
    import torch
    from torch import nn
    from torch.ao.quantization import disable_observer, enable_observer
    from torch.utils.data import DataLoader

    seed_everything(42)
    LOGGER.info("Loading config: %s; source manifest: %s", args.config, args.source_manifest)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    source_manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    LOGGER.info("Checking source checkpoint/FP32 ONNX hashes and preprocessing contract...")
    if (source_manifest.get("checkpoint_sha256") != sha256(args.checkpoint)
            or source_manifest.get("onnx_sha256") != sha256(args.fp32_onnx)):
        raise ValueError("FP32 ONNX manifest không thuộc checkpoint được chỉ định.")
    if (source_manifest.get("input_size") != config["image_size"]
            or source_manifest.get("letterbox_fill") != config["letterbox_fill"]
            or source_manifest.get("class_order") != config["class_order"]):
        raise ValueError("Config và manifest FP32 không khớp preprocessing/class_order.")
    check_manifest(source_manifest, config)
    LOGGER.info("Source contract passed; auditing saved split (paths/hashes/leakage): %s", args.split_csv)
    split = load_splits(args.split_csv, args.dataset_dir, config["class_order"])
    LOGGER.info("Split audit passed: train=%d, val=%d, test=%d; test excluded from fitting/calibration",
                len(split["train"]), len(split["val"]), len(split["test"]))
    if not split["val"]:
        raise ValueError("QAT cần validation split để chọn checkpoint.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    LOGGER.info("Runtime: PyTorch=%s, device=%s%s", torch.__version__, device,
                f" ({torch.cuda.get_device_name(device)})" if device.type == "cuda" else "")
    seed_everything(config.get("seed", 42))
    LOGGER.info("Loading FP32 checkpoint: %s", args.checkpoint)
    state, checkpoint = load_checkpoint(args.checkpoint)
    state = remove_module_prefix(state)
    if checkpoint.get("class_names") and list(checkpoint["class_names"]) != config["class_order"]:
        raise ValueError("Checkpoint class_names không khớp config.")
    model = build_model(len(config["class_order"]), float(config.get("dropout", 0.25)),
                        nested_classifier="classifier.3.1.weight" in state)
    model.load_state_dict(state, strict=True)
    LOGGER.info("Checkpoint loaded strictly; classes=%s, image_size=%d", config["class_order"], config["image_size"])

    backend = "x86" if "x86" in torch.backends.quantized.supported_engines else "fbgemm"
    model = prepare_qat_model(model, config["image_size"], backend)
    # Check this architecture/exporter now, not after a long fine-tuning run.
    # Temporary observer statistics are discarded; no output artifact is replaced.
    initial_state = {key: value.clone() for key, value in model.state_dict().items()}
    LOGGER.info("Checking QAT ONNX Q/DQ export before fine-tuning...")
    smoke_samples = [preprocess(path, config["image_size"], config["letterbox_fill"])
                     for path, _ in split["train"][:3]]
    with tempfile.TemporaryDirectory(prefix="qat-export-check-") as directory:
        with torch.no_grad():
            model.eval()
            for value in smoke_samples:
                model(torch.from_numpy(value))  # Temporary calibration uses train only, never test.
        export_qdq(model, Path(directory) / "preflight.onnx", config["image_size"], check_samples=smoke_samples)
    model.load_state_dict(initial_state, strict=True)
    del initial_state
    if args.check_export_only:
        LOGGER.info("Export-only checks completed in %.1fs; reference/runtime drift reported separately; "
                    "no fitting, no model artifacts saved, NOT deployment verification", time.perf_counter() - started)
        return
    model = model.to(device)
    LOGGER.info("QAT export preflight executed; parity results logged separately; observer state restored; creating data loaders")
    train_loader = DataLoader(make_dataset(split["train"], config, training=True),
                              batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers,
                              pin_memory=device.type == "cuda")
    val_loader = DataLoader(make_dataset(split["val"], config, training=False),
                            batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers,
                            pin_memory=device.type == "cuda")
    LOGGER.info("Data loaders ready: train=%d batches, val=%d batches; outputs=%s",
                len(train_loader), len(val_loader), args.out_onnx.parent)
    backbone, head = [], []
    for name, parameter in model.named_parameters():
        (head if name.startswith("classifier") else backbone).append(parameter)
    optimizer = torch.optim.AdamW(
        [{"params": backbone, "lr": args.backbone_lr}, {"params": head, "lr": args.head_lr}],
        weight_decay=float(config.get("weight_decay", 5e-4)),
    )
    criterion = nn.CrossEntropyLoss(label_smoothing=float(config.get("label_smoothing", 0.05)))
    ranks = torch.tensor([SEVERITY_RANK[name] for name in config["class_order"]],
                         dtype=torch.float32, device=device)
    qat_loss_weight = float(config.get("severity_loss_weight", 0.0))
    tie_tolerance = float(config.get("accuracy_tie_tolerance", 0.005))
    args.out_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    args.out_onnx.parent.mkdir(parents=True, exist_ok=True)
    history = []
    best_accuracy, best_critical, best_state, stale = -1.0, float("inf"), None, 0
    best_epoch, best_metrics = 0, None

    for epoch in range(args.epochs):
        epoch_started = time.perf_counter()
        LOGGER.info("Epoch %d/%d started; observers=%s", epoch + 1, args.epochs,
                    "collecting" if epoch < args.freeze_observers_after else "frozen")
        model.train()
        running_loss, seen = 0.0, 0
        for batch, (images, labels) in enumerate(train_loader, 1):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            ce_loss = criterion(logits, labels)
            probs = torch.softmax(logits, dim=1)
            distances = (ranks.unsqueeze(0) - ranks[labels].unsqueeze(1)).abs()
            severity_loss = (probs * distances).sum(dim=1).mean()
            loss = ce_loss + qat_loss_weight * severity_loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=3.0)
            optimizer.step()
            running_loss += float(loss.detach()) * len(labels)
            seen += len(labels)
            if batch == 1 or batch % args.log_every == 0 or batch == len(train_loader) or args.verbose:
                elapsed = time.perf_counter() - epoch_started
                LOGGER.info("Epoch %d/%d | train batch %d/%d | images=%d/%d | loss=%.5f | elapsed=%.1fs | ETA=%.1fs",
                            epoch + 1, args.epochs, batch, len(train_loader), seen, len(train_loader.dataset),
                            running_loss / seen, elapsed, elapsed / batch * (len(train_loader) - batch))

        permanently_frozen = epoch + 1 >= args.freeze_observers_after
        val_metrics = evaluate(model, val_loader, device, config, log_every=args.log_every)
        train_loss = running_loss / len(train_loader.dataset)
        record = {"epoch": epoch + 1, "train_loss": train_loss, **val_metrics}
        history.append(record)
        LOGGER.info("Epoch {epoch}/{total} | train_loss={train_loss:.5f} | val_acc={accuracy:.4f} "
              "val_macro_f1={macro_f1:.4f} | critical={critical_error_count}/{n} ({critical_error_rate:.4f}) "
              "| observers={observer}".format(
                  total=args.epochs, n=len(val_loader.dataset), observer="frozen" if permanently_frozen else "collecting",
                  **record))

        improved = val_metrics["accuracy"] > best_accuracy + tie_tolerance
        tied_better = (best_state is not None
                       and val_metrics["accuracy"] >= best_accuracy - tie_tolerance
                       and val_metrics["critical_error_rate"] < best_critical)
        if improved or tied_better:
            best_accuracy = max(best_accuracy, val_metrics["accuracy"])
            best_critical = val_metrics["critical_error_rate"]
            best_epoch, best_metrics = epoch + 1, val_metrics
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            stale = 0
            torch.save({
                "qat_state_dict": best_state,
                "source_checkpoint_sha256": sha256(args.checkpoint),
                "source_onnx_sha256": source_manifest["onnx_sha256"],
                "split_csv_sha256": sha256(args.split_csv),
                "config_sha256": sha256(args.config),
                "epoch": epoch + 1,
                "validation_metrics": val_metrics,
                "backend": backend,
                "qat_qconfig_exclusions": ["AdaptiveAvgPool2d"],
            }, args.out_checkpoint)
            LOGGER.info("Saved best QAT checkpoint: %s; epoch=%d", args.out_checkpoint, epoch + 1)
        else:
            stale += 1
            LOGGER.info("No validation improvement: patience %d/%d", stale, args.patience)
            if stale >= args.patience:
                LOGGER.info("Early stopping: no validation improvement for %d epochs", args.patience)
                break
        if not permanently_frozen:
            model.apply(enable_observer)
        LOGGER.info("Epoch %d completed in %.1fs", epoch + 1, time.perf_counter() - epoch_started)

    if best_state is None:
        raise RuntimeError("QAT không tạo được checkpoint tốt nhất.")
    LOGGER.info("Fine-tuning finished; best epoch=%d; exporting frozen QAT model", best_epoch)
    model.load_state_dict(best_state, strict=True)
    model.apply(disable_observer)
    model.eval()
    export_checks = export_qdq(model, args.out_onnx, config["image_size"], check_samples=smoke_samples)
    runtime = session(args.out_onnx)
    input_info = runtime.get_inputs()[0]
    validate_input_shape(input_info.shape, config["image_size"])
    validate_probabilities(runtime.run(None, {input_info.name: np.zeros(
        (1, 3, config["image_size"], config["image_size"]), dtype=np.float32)})[0],
        len(config["class_order"]),
        sum_atol=quantized_probability_sum_atol(len(config["class_order"])))
    manifest = {
        "checkpoint_sha256": source_manifest["checkpoint_sha256"],
        "qat_checkpoint_sha256": sha256(args.out_checkpoint),
        "source_onnx_sha256": source_manifest["onnx_sha256"],
        "onnx_sha256": sha256(args.out_onnx),
        "split_csv_sha256": sha256(args.split_csv),
        "config_sha256": sha256(args.config),
        "input_size": config["image_size"],
        "preprocess": source_manifest["preprocess"],
        "letterbox_fill": config["letterbox_fill"],
        "class_order": config["class_order"],
        "precision": "int8_qat",
        "quantization": f"QDQ_QAT_{backend}",
        "qat_qconfig_exclusions": ["AdaptiveAvgPool2d"],
        "qat_epochs_requested": args.epochs,
        "qat_epochs_completed": len(history),
        "qat_best_epoch": best_epoch,
        "validation_metrics": best_metrics,
        "artifacts_complete": True,
        "export_smoke": {"scope": "train_subset_not_accuracy", **export_checks},
    }
    manifest_path = args.out_onnx.parent / "model_manifest_qat.json"
    LOGGER.info("Saving manifest and training history: %s", args.out_onnx.parent)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (args.out_onnx.parent / "qat_history.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=history[0].keys())
        writer.writeheader()
        writer.writerows(history)
    LOGGER.info("QAT completed in %.1fs | ONNX=%s | manifest=%s | device=%s | backend=%s",
                time.perf_counter() - started, args.out_onnx, manifest_path, device, backend)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        LOGGER.warning("QAT interrupted by user")
        raise
    except Exception:
        LOGGER.exception("QAT failed; see the last logged stage and traceback")
        raise
