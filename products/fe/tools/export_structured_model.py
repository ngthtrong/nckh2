"""Export the saved structured-pruned checkpoint to ONNX and/or ExecuTorch."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch

from compare_structured_pruning import load_structured_model
from convert_model import ProbabilityModel, inference_contract, update_manifest, sha256_file
from export_executorch import EXPECTED_EXECUTORCH_VERSION
from quantize_model import session, validate_probabilities


ROOT = Path(__file__).resolve().parents[1]
EDGE_DIR = ROOT / "model" / "Edge Ai"
DEFAULT_CHECKPOINT = EDGE_DIR / "flood_mobilenetv3_large_structured_best.pt"
DEFAULT_SOURCE_CHECKPOINT = EDGE_DIR / "flood_mobilenetv3_large_best.pth"
DEFAULT_CONFIG = EDGE_DIR / "config_mobilenetv3_large.json"
DEFAULT_OUTPUT_DIR = EDGE_DIR / "Export" / "pruning_st"
LOGGER = logging.getLogger("export_structured_model")


def temporary_path(output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{output.stem}.", suffix=output.suffix, dir=output.parent)
    os.close(fd)
    return Path(name)


def verify_probabilities(output, num_classes: int) -> np.ndarray:
    return validate_probabilities(output, num_classes)[None, :]


def smoke_onnx(path: Path, sample: torch.Tensor, expected: np.ndarray, num_classes: int) -> float:
    runtime = session(path)
    inputs = runtime.get_inputs()
    outputs = runtime.get_outputs()
    size = sample.shape[-1]
    if (len(inputs) != 1 or len(outputs) != 1 or inputs[0].type != "tensor(float)"
            or outputs[0].type != "tensor(float)" or inputs[0].shape[1:] != [3, size, size]):
        raise ValueError("Graph ONNX có I/O không khớp FP32 NCHW của config.")
    actual = verify_probabilities(
        runtime.run(None, {inputs[0].name: sample.numpy()})[0], num_classes,
    )
    difference = float(np.max(np.abs(actual - expected)))
    if not np.allclose(actual, expected, atol=1e-4, rtol=1e-4):
        raise RuntimeError(f"ONNX smoke parity thất bại; max_abs_diff={difference:.8g}.")
    return difference


def check_executorch_version() -> str:
    try:
        version = importlib.metadata.version("executorch")
    except importlib.metadata.PackageNotFoundError as error:
        raise RuntimeError("Thiếu ExecuTorch; cài đúng version hoặc chỉ export --format onnx.") from error
    if version != EXPECTED_EXECUTORCH_VERSION:
        raise RuntimeError(f"Cần ExecuTorch {EXPECTED_EXECUTORCH_VERSION}, hiện cài {version}.")
    return version


def export_onnx(model: torch.nn.Module, sample: torch.Tensor, output: Path, num_classes: int) -> float:
    temporary = temporary_path(output)
    try:
        torch.onnx.export(
            ProbabilityModel(model).eval(), sample, temporary,
            input_names=["image"], output_names=["probabilities"],
            dynamic_axes={"image": {0: "batch"}, "probabilities": {0: "batch"}},
            opset_version=17, dynamo=False,
        )
        with torch.inference_mode():
            expected = ProbabilityModel(model).eval()(sample).cpu().numpy()
        difference = smoke_onnx(temporary, sample, expected, num_classes)
        os.replace(temporary, output)
        return difference
    finally:
        temporary.unlink(missing_ok=True)


def export_pte(model: torch.nn.Module, sample: torch.Tensor, output: Path, num_classes: int) -> tuple[str, int, float]:
    from executorch.exir import to_edge_transform_and_lower
    from executorch.backends.xnnpack.partition.xnnpack_partitioner import XnnpackFloatingPointPartitioner
    from executorch.backends.xnnpack.utils.configs import get_transform_passes

    version = check_executorch_version()
    flatc = Path(sys.executable).with_name("flatc.exe")
    if os.name == "nt" and flatc.is_file():
        os.environ.setdefault("FLATC_EXECUTABLE", str(flatc))

    wrapper = ProbabilityModel(model).eval()
    exported = torch.export.export(wrapper, (sample,))
    edge_program = to_edge_transform_and_lower(
        exported,
        partitioner=[XnnpackFloatingPointPartitioner()],
        transform_passes=get_transform_passes(),
    )
    program = edge_program.to_executorch()
    delegates = sum(
        delegate.id == "XnnpackBackend"
        for plan in program.executorch_program.execution_plan
        for delegate in plan.delegates
    )
    if delegates == 0:
        raise RuntimeError("Không có XNNPACK partition; từ chối tạo PTE không tối ưu.")

    temporary = temporary_path(output)
    try:
        temporary.write_bytes(program.buffer)
        from executorch.runtime import Runtime

        runtime_program = Runtime.get().load_program(program.buffer)
        forward = runtime_program.load_method("forward")
        with torch.inference_mode():
            expected = wrapper(sample).cpu().numpy()
        outputs = forward.execute((sample,))
        if len(outputs) != 1 or not isinstance(outputs[0], torch.Tensor):
            raise ValueError("PTE cần trả một tensor probabilities.")
        actual = verify_probabilities(outputs[0].detach().cpu().numpy(), num_classes)
        difference = float(np.max(np.abs(actual - expected)))
        if not np.allclose(actual, expected, atol=1e-4, rtol=1e-4):
            raise RuntimeError(f"PTE smoke parity thất bại; max_abs_diff={difference:.8g}.")
        del forward, runtime_program
        os.replace(temporary, output)
        return version, delegates, difference
    finally:
        temporary.unlink(missing_ok=True)


def update_pruned_manifest(manifest_path: Path, checkpoint: Path, config: dict,
                           artifact_path: Path, artifact_type: str, source_sha256: str,
                           details: dict, executorch_version: str | None = None) -> dict:
    manifest = update_manifest(
        manifest_path, checkpoint, config, artifact_path,
        artifact_type=artifact_type, executorch_version=executorch_version,
    )
    manifest.update(
        model_type="structured_pruned",
        source_checkpoint_sha256=source_sha256,
        pruning=details["pruning"],
        best_epoch=details["best_epoch"],
        parameter_count=details["parameter_count"],
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest", type=Path, help="default: OUTPUT_DIR/model_manifest.json")
    parser.add_argument("--format", choices=("all", "onnx", "pte"), default="all")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = json.loads(args.config.read_text(encoding="utf-8"))
    contract = inference_contract(config)
    if args.format in ("all", "pte"):
        check_executorch_version()
    source_sha256 = sha256_file(args.source_checkpoint)
    model, details = load_structured_model(args.checkpoint, config, source_sha256)
    model = model.cpu().eval()
    torch.set_num_threads(1)
    size = contract["input_size"]
    sample = torch.zeros(1, 3, size, size)
    with torch.inference_mode():
        reference = ProbabilityModel(model).eval()(sample)
    if reference.shape != (1, len(contract["class_order"])) or not torch.isfinite(reference).all():
        raise ValueError("Output model structured không khớp class_order hoặc chứa giá trị non-finite.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.manifest or args.output_dir / "model_manifest.json"
    if args.format in ("all", "onnx"):
        onnx_path = args.output_dir / "flood_mobilenetv3_large_structured.onnx"
        LOGGER.info("Export ONNX: %s", onnx_path)
        error = export_onnx(model, sample, onnx_path, len(contract["class_order"]))
        manifest = update_pruned_manifest(
            manifest_path, args.checkpoint, config, onnx_path, "onnx", source_sha256, details,
        )
        LOGGER.info("ONNX smoke max_abs_diff=%.8g; manifest version=%s", error, manifest["version"])

    if args.format in ("all", "pte"):
        pte_path = args.output_dir / "flood_mobilenetv3_large_structured.pte"
        LOGGER.info("Export ExecuTorch/XNNPACK FP32: %s", pte_path)
        version, delegates, error = export_pte(model, sample, pte_path, len(contract["class_order"]))
        manifest = update_pruned_manifest(
            manifest_path, args.checkpoint, config, pte_path, "pte", source_sha256,
            details, executorch_version=version,
        )
        LOGGER.info("PTE smoke max_abs_diff=%.8g; XNNPACK partitions=%d; manifest version=%s",
                    error, delegates, manifest["version"])

    LOGGER.info("Checkpoint SHA256: %s", sha256_file(args.checkpoint))
    LOGGER.info("Source checkpoint SHA256: %s", source_sha256)
    LOGGER.info("Export completed; files saved under %s", args.output_dir.resolve())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        LOGGER.warning("Export interrupted")
        raise SystemExit(130)
    except Exception:
        LOGGER.exception("Structured model export failed")
        raise SystemExit(1)
