"""Portable coordinator. This file never edits the source repository or reports.

The notebook extracts hash-bound inputs to a NEW project and invokes this module
in a separate interpreter. Historical test sets remain development evidence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

VERSION = "nckh2-notebook-bundle-1"
SILVER = "docs/revision-plan/outputs/vi-nlp-fusion-silver-20261108"
PUBLIC = "docs/revision-plan/outputs/multimodal-20261108"
IMAGE = "products/fe/model/Edge Ai/seed1024"
SPLIT = "products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv"
DATA = "products/fe/model/Dataset_Flood"
TOOLS = "products/fe/tools"
DEFAULT = {
    "pruning_ratios": [0.05, 0.10, 0.20], "pruning_epochs": 35,
    "pruning_batch_size": 8, "qat_epochs": 10, "qat_batch_size": 8,
    "timeout_seconds": 21600, "run_qat": False, "run_baseline": False,
    "run_pruning": True, "run_ptq": True, "run_quant_debug": True,
    "run_public": True, "run_silver": True, "run_silver_t2": True,
    "run_synthetic": True, "run_synthetic_t2": False,
    "run_pte": False, "pte_python": None, "cpu_threads": 4, "bootstrap_draws": 2000,
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def csv_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def file_manifest(folder):
    return {str(p.relative_to(folder)): digest(p) for p in sorted(Path(folder).rglob("*"))
            if p.is_file() and p.name not in {"stage.json", "stage.json.tmp"}}


def verify_files(root, manifest):
    for relative, expected in manifest.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file() or digest(path) != expected:
            raise ValueError("Missing/changed artifact: " + relative)


def preflight(root, *, torch_check=False):
    """Read files only: count/hash checks are not a validation of scientific labels."""
    inventory = read(root / "bundle-inputs.json")
    for item in inventory["packages"]:
        verify_files(root, item["files"])
    images = csv_rows(root / SPLIT)
    if len(images) != 1702:
        raise ValueError("Unexpected image split length")
    by_group = {}
    for row in images:
        p = root / DATA / row["relative_path"]
        if hashlib.md5(p.read_bytes()).hexdigest() != row["md5"]:
            raise ValueError("Image MD5 mismatch: " + row["relative_path"])
        group = row["split_group"]
        if group in by_group and by_group[group] != row["split"]:
            raise ValueError("Image split_group crosses splits")
        by_group[group] = row["split"]
    source = read(root / IMAGE / "export/baseline/model_manifest.json")
    if source["checkpoint_sha256"] != digest(root / IMAGE / "flood_mobilenetv3_large_best.pth"):
        raise ValueError("Checkpoint/manifest mismatch")
    report = {
        "status": "INPUT_FILES_VERIFIED", "version": VERSION,
        "image_split": dict(Counter(x["split"] for x in images)),
        "image_source_groups_empty": sum(not r["source_group"].strip() for r in images),
        "native_gold": "DATA_NOT_READY", "independent_camera_test": "DATA_NOT_READY",
        "limits": ["Historical train-split lineage/source/IAA unresolved",
                   "Existing test sets have already been viewed; this is a development replay",
                   "No Android, SMS, real-network or field-effectiveness evidence"],
    }
    for name, dataset in [("public", "thucnghiem/multimodal/data/dataset.json"),
                          ("silver", "thucnghiem/vi_rescue/data/dataset.json")]:
        data = read(root / dataset)
        rows = data["records"] if isinstance(data, dict) else data
        if len({r["image_id"] for r in rows}) != len(rows):
            raise ValueError("Duplicate pair IDs: " + name)
        seen = {}
        for row in rows:
            p = root / row["image_path"] if "image_path" in row else root / "thucnghiem/multimodal/data" / row["image"]
            if digest(p) != row["image_sha256"]:
                raise ValueError("Pair image mismatch: " + row["image_id"])
            for key in ["image_id", "tweet_id", "image_sha256", "group_id", "event_name"]:
                identity = (key, row[key])
                if identity in seen and seen[identity] != row["split"]:
                    raise ValueError("Cross-split overlap: " + name + "/" + key)
                seen[identity] = row["split"]
        report[name] = {"n": len(rows), "split": dict(Counter(r["split"] for r in rows))}
    from synthetic_data import BASE as SYN_BASE, validate_payload
    report["synthetic_vi"] = validate_payload(read(root / SYN_BASE / "data/dataset.json"), root=root)
    report["environment"] = {"python": sys.version, "platform": platform.platform()}
    if torch_check:
        import torch
        import torchvision
        report["environment"].update(torch=torch.__version__, torchvision=torchvision.__version__,
                                     cuda_available=torch.cuda.is_available(), cuda_build=torch.version.cuda)
        if torch.cuda.is_available():
            # This tiny kernel verifies executable CUDA support, not research performance.
            x = torch.ones(4, device="cuda")
            if float((x * x).sum().cpu()) != 4:
                raise RuntimeError("CUDA arithmetic preflight failed")
            report["environment"].update(gpu=torch.cuda.get_device_name(0),
                                        capability=list(torch.cuda.get_device_capability(0)),
                                        vram_bytes=torch.cuda.get_device_properties(0).total_memory)
        report["environment"]["packages"] = {
            name: importlib.metadata.version(name) for name in
            ["numpy", "scipy", "scikit-learn", "transformers", "onnx", "onnxruntime", "torch-pruning"]}
    return report


class Run:
    def __init__(self, root, config):
        self.root = Path(root).resolve()
        self.config = {**DEFAULT, **config}
        self.out = self.root / "bundle-results"
        self.out.mkdir(exist_ok=True)
        self.config_path = self.out / "locked-config.json"
        if self.config_path.exists() and read(self.config_path) != self.config:
            raise ValueError("Config changed within this run; choose a NEW RUN_ID")
        write(self.config_path, self.config)
        self.binding = {"config": digest(self.config_path), "inputs": digest(self.root / "bundle-inputs.json")}

    def call(self, script, args, folder, *, cwd=None, python=None):
        command = [python or sys.executable, str(self.root / script), *[str(x) for x in args]]
        folder.mkdir(parents=True, exist_ok=True)
        log = folder / (Path(script).stem + ".log")
        write(folder / (Path(script).stem + "-command.json"), {
            "command": command, "cwd": str(cwd or self.root), "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source_sha256": digest(self.root / script), "bindings": self.binding})
        print("RUN", " ".join(command), flush=True)
        # Stream output to notebook and log. A watchdog bounds the entire child.
        import threading
        process = subprocess.Popen(command, cwd=cwd or self.root, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, bufsize=1)
        timed_out = threading.Event()
        def timeout():
            timed_out.set()
            process.kill()
        timer = threading.Timer(self.config["timeout_seconds"], timeout)
        timer.start()
        started = time.monotonic()
        try:
            with log.open("w", encoding="utf-8") as stream:
                for line in process.stdout:
                    stream.write(line); stream.flush(); print(line, end="", flush=True)
            code = process.wait()
        finally:
            timer.cancel()
            if process.poll() is None:
                process.kill(); process.wait()
        write(folder / (Path(script).stem + "-exit.json"), {
            "exit_code": code, "timeout": timed_out.is_set(), "seconds": time.monotonic() - started,
            "log_sha256": digest(log)})
        if timed_out.is_set() or code:
            raise RuntimeError(f"Child failed ({code}, timeout={timed_out.is_set()}): {script}; see {log}")

    def image_args(self):
        return ["--checkpoint", self.root / IMAGE / "flood_mobilenetv3_large_best.pth",
                "--config", self.root / IMAGE / "config_mobilenetv3_large.json",
                "--split-csv", self.root / SPLIT, "--dataset-dir", self.root / DATA]

    def stage(self, name):
        folder = self.out / name
        folder.mkdir(exist_ok=True)
        receipt = folder / "stage.json"
        if receipt.exists():
            old = read(receipt)
            if old["bindings"] != self.binding:
                raise ValueError("Stage belongs to different inputs/config")
            if old["status"] in {"COMPLETED", "DATA_READY", "DATA_NOT_READY", "NOT_REQUESTED", "REQUIRES_DEVICE"}:
                verify_files(folder, old.get("outputs", {}))
                verify_files(self.root, old.get("external_outputs", {}))
                print("SKIP verified stage", name, old["status"], flush=True)
                return old
            raise RuntimeError(f"Stage {name} was {old['status']}. Preserved; use a new RUN_ID, no automatic retry.")
        started = time.monotonic()
        write(receipt, {"status": "RUNNING", "bindings": self.binding})
        status, details = "COMPLETED", {}
        try:
            method = getattr(self, "do_" + name)
            result = method(folder)
            if result:
                status = result.pop("status", status)
                details = result
        except BaseException as exc:
            write(receipt, {"status": "FAILED", "bindings": self.binding, "error": str(exc),
                            "traceback": traceback.format_exc(), "seconds": time.monotonic() - started,
                            "outputs": file_manifest(folder)})
            raise
        result = {"status": status, "bindings": self.binding, "seconds": time.monotonic() - started,
                  "details": details, "outputs": file_manifest(folder), "external_outputs": self.external_outputs(name)}
        write(receipt, result)
        return result

    def external_outputs(self, name):
        prefixes = []
        if name == "public_fusion":
            prefixes = [PUBLIC, "thucnghiem/multimodal/models", "thucnghiem/multimodal/features"]
        elif name in {"silver_fusion", "silver_t2", "silver_evaluation"}:
            prefixes = [SILVER, "thucnghiem/vi_rescue/models", "thucnghiem/vi_rescue/cache/embeddings.npz"]
        elif name in {"synthetic_fusion", "synthetic_t2", "synthetic_evaluation"}:
            from synthetic_data import BASE as SYN_BASE, OUT as SYN_OUT
            prefixes = [SYN_OUT, SYN_BASE + "/models", SYN_BASE + "/cache/embeddings.npz"]
        result = {}
        for relative in prefixes:
            base = self.root / relative
            for p in sorted(base.rglob("*")) if base.is_dir() else [base]:
                if p.is_file():
                    result[str(p.relative_to(self.root))] = digest(p)
        return result

    def do_preflight(self, folder):
        write(folder / "preflight.json", preflight(self.root, torch_check=True))

    def do_image_baseline(self, folder):
        if not self.config["run_baseline"]:
            return {"status": "NOT_REQUESTED", "reason": "Existing baseline checkpoint is supplied; retraining is conditional"}
        self.call("toolkit/image_baseline.py", self.image_args() + ["--output-dir", folder / "model"], folder)

    def do_image_pruning(self, folder):
        if not self.config["run_pruning"]:
            return {"status": "NOT_REQUESTED"}
        candidates = []
        for ratio in self.config["pruning_ratios"]:
            target = folder / f"ratio-{ratio:.3f}"
            self.call(TOOLS + "/structured_pruning.py", self.image_args() + [
                "--prune-ratio", ratio, "--epochs", self.config["pruning_epochs"],
                "--batch-size", self.config["pruning_batch_size"], "--output-dir", target,
                "--defer-test"], target)
            report = read(target / "metrics.json")
            if report["final_test"] is not None:
                raise ValueError("Pruning selection must not inspect test")
            candidates.append({"ratio": ratio, "macro_f1": report["best_validation"]["macro_f1"],
                               "accuracy": report["best_validation"]["accuracy"],
                               "checkpoint": str((target / "flood_mobilenetv3_large_structured_best.pt").relative_to(self.root))})
        selected = max(candidates, key=lambda r: (r["macro_f1"], r["accuracy"], -r["ratio"]))
        write(folder / "selection.json", {"selection": "validation macro-F1, then accuracy, then lower ratio",
                                          "candidates": candidates, "selected": selected,
                                          "limits": "Development selection on existing split, not new independent confirmation"})

    def do_image_export_compare(self, folder):
        if not self.config["run_pruning"]:
            return {"status": "NOT_REQUESTED"}
        selection = read(self.out / "image_pruning/selection.json")
        selected = self.root / selection["selected"]["checkpoint"]
        self.call(TOOLS + "/export_structured_model.py", [
            "--checkpoint", selected, "--source-checkpoint", self.root / IMAGE / "flood_mobilenetv3_large_best.pth",
            "--config", self.root / IMAGE / "config_mobilenetv3_large.json", "--format", "onnx",
            "--output-dir", folder / "onnx"], folder)
        self.call(TOOLS + "/compare_structured_pruning.py", self.image_args() + [
            "--pruned", selected, "--report-dir", folder / "comparison", "--no-plots"], folder)
        from analysis import analyze_predictions
        analyze_predictions(folder / "comparison/all_predictions.csv", self.root / SPLIT,
                            folder / "paired-statistics.json", self.config["bootstrap_draws"])
        write(folder / "selected-model.json", {"checkpoint": str(selected), "checkpoint_sha256": digest(selected),
            "selection_sha256": digest(self.out / "image_pruning/selection.json"),
            "test_scope": "Historical test viewed before this session; development evidence only"})

    def do_image_ptq(self, folder):
        if not self.config["run_ptq"]:
            return {"status": "NOT_REQUESTED"}
        self.call(TOOLS + "/quantize_model.py", [
            "--onnx", self.root / IMAGE / "export/baseline/flood_mobilenetv3_large.onnx",
            "--source-manifest", self.root / IMAGE / "export/baseline/model_manifest.json",
            "--config", self.root / IMAGE / "config_mobilenetv3_large.json",
            "--split-csv", self.root / SPLIT, "--dataset-dir", self.root / DATA,
            "--out-dir", folder / "model", "--report-dir", folder / "report"], folder)

    def do_image_qat(self, folder):
        if not self.config["run_qat"]:
            return {"status": "NOT_REQUESTED", "reason": "Diagnose historical PTQ/QAT first; QAT retraining is conditional"}
        self.call(TOOLS + "/qat_finetune.py", self.image_args() + [
            "--fp32-onnx", self.root / IMAGE / "export/baseline/flood_mobilenetv3_large.onnx",
            "--source-manifest", self.root / IMAGE / "export/baseline/model_manifest.json",
            "--epochs", self.config["qat_epochs"], "--batch-size", self.config["qat_batch_size"],
            "--out-onnx", folder / "model/flood_mobilenetv3_large.qat.int8.onnx",
            "--out-checkpoint", folder / "model/flood_mobilenetv3_large_qat_best.pth"], folder)

    def do_quantization_analysis(self, folder):
        ptq = self.out / "image_ptq/model" if self.config["run_ptq"] else self.root / IMAGE / "Quantize"
        qat = self.out / "image_qat/model" if self.config["run_qat"] else self.root / IMAGE / "QAT"
        self.call(TOOLS + "/compare_fp32_ptq_qat.py", [
            "--fp32", self.root / IMAGE / "export/baseline/flood_mobilenetv3_large.onnx",
            "--ptq", ptq / "flood_mobilenetv3_large.int8.onnx",
            "--qat", qat / "flood_mobilenetv3_large.qat.int8.onnx",
            "--qat-checkpoint", qat / "flood_mobilenetv3_large_qat_best.pth",
            "--manifest", self.root / IMAGE / "export/baseline/model_manifest.json",
            "--ptq-manifest", ptq / "model_manifest_int8.json", "--qat-manifest", qat / "model_manifest_qat.json",
            "--config", self.root / IMAGE / "config_mobilenetv3_large.json",
            "--split-csv", self.root / SPLIT, "--dataset-dir", self.root / DATA,
            "--report-dir", folder / "comparison", "--no-plots"], folder)
        from analysis import analyze_predictions, activation_debug
        analyze_predictions(folder / "comparison/all_predictions.csv", self.root / SPLIT,
                            folder / "paired-statistics.json", self.config["bootstrap_draws"])
        if self.config["run_quant_debug"]:
            activation_debug(self.root, ptq, qat, folder / "validation-debug")
        return {"scope": "Per-class errors and validation tensor diagnostics; not a causal diagnosis or Android benchmark"}

    def pipeline(self, kind, script, folder):
        self.call(f"thucnghiem/{kind}/{script}.py", [], folder)

    def do_public_fusion(self, folder):
        if not self.config["run_public"]:
            return {"status": "NOT_REQUESTED"}
        for step in ["features", "train", "evaluate", "verify"]:
            self.pipeline("multimodal", step, folder / step)
        # Copy new receipts/predictions into the stage manifest for resume checking.
        self.snapshot(self.root / PUBLIC, folder / "outputs")
        return {"scope": "English CrisisMMD informativeness development replay"}

    def do_silver_fusion(self, folder):
        if not self.config["run_silver"]:
            return {"status": "NOT_REQUESTED"}
        for step in ["features", "train"]:
            self.pipeline("vi_rescue", step, folder / step)
        self.snapshot(self.root / SILVER, folder / "outputs")
        return {"scope": "AI-translated Vietnamese with AI text-only labels; no independent gold"}

    def do_silver_t2(self, folder):
        if not self.config["run_silver"] or not self.config["run_silver_t2"]:
            return {"status": "NOT_REQUESTED"}
        self.pipeline("vi_rescue", "fine_tune", folder)
        self.pipeline("vi_rescue", "verify_encoder_update", folder / "encoder-check")
        self.snapshot(self.root / SILVER, folder / "outputs")
        return {"scope": "Six GPU fine-tuning candidates, validation selection; same historical silver test"}

    def do_silver_evaluation(self, folder):
        if not self.config["run_silver"]:
            return {"status": "NOT_REQUESTED"}
        for step in ["evaluate", "verify"]:
            self.pipeline("vi_rescue", step, folder / step)
        self.snapshot(self.root / SILVER, folder / "outputs")

    @staticmethod
    def snapshot(source, destination):
        import shutil
        destination.mkdir(parents=True, exist_ok=True)
        for p in sorted(source.iterdir()):
            if p.is_file() and p.suffix in {".json", ".csv"}:
                shutil.copy2(p, destination / p.name)

    def do_historical_analysis(self, folder):
        from analysis import analyze_predictions
        source = self.root / "historical_evidence"
        for name in ["pruning", "quantization"]:
            analyze_predictions(source / name / "all_predictions.csv", self.root / SPLIT,
                                folder / (name + "-paired-statistics.json"), self.config["bootstrap_draws"])
        return {"scope": "Retrospective McNemar/paired CI from saved predictions; no fresh inference"}

    def do_native_gold(self, folder):
        write(folder / "readiness.json", {"status": "DATA_NOT_READY",
              "missing": ["Native Vietnamese paired corpus", "Independent human labels/adjudication",
                          "Agreed target and source/event-group split", "Locked task-specific protocol"],
              "not_substitutes": ["AI silver translations", "Image flood classes", "Structured OR labels"]})
        return {"status": "DATA_NOT_READY", "reason": "No fabricated corpus or human approval"}

    def do_synthetic_data(self, folder):
        from synthetic_data import BASE as SYN_BASE, validate_payload
        report = validate_payload(read(self.root / SYN_BASE / "data/dataset.json"), root=self.root)
        write(folder / "readiness.json", report)
        return report

    def do_synthetic_fusion(self, folder):
        if not self.config["run_synthetic"]:
            return {"status": "NOT_REQUESTED"}
        from synthetic_data import BASE as SYN_BASE, OUT as SYN_OUT, validate_payload
        validate_payload(read(self.root / SYN_BASE / "data/dataset.json"), root=self.root)
        for step in ["features", "train"]:
            self.pipeline("vi_synthetic", step, folder / step)
        self.snapshot(self.root / SYN_OUT, folder / "outputs")
        return {"evidence_class": "SYNTHETIC_UNPAIRED", "purpose": "TECHNICAL_PIPELINE_TEST_ONLY", "native_gold": False}

    def do_synthetic_t2(self, folder):
        if not self.config["run_synthetic"] or not self.config["run_synthetic_t2"]:
            return {"status": "NOT_REQUESTED", "reason": "Optional six additional CUDA candidates on synthetic sentences"}
        from synthetic_data import OUT as SYN_OUT
        self.pipeline("vi_synthetic", "fine_tune", folder)
        self.pipeline("vi_synthetic", "verify_encoder_update", folder / "encoder-check")
        self.snapshot(self.root / SYN_OUT, folder / "outputs")
        return {"evidence_class": "SYNTHETIC_UNPAIRED", "native_gold": False}

    def do_synthetic_evaluation(self, folder):
        if not self.config["run_synthetic"]:
            return {"status": "NOT_REQUESTED"}
        from synthetic_data import OUT as SYN_OUT
        for step in ["evaluate", "verify"]:
            self.pipeline("vi_synthetic", step, folder / step)
        self.snapshot(self.root / SYN_OUT, folder / "outputs")
        return {"evidence_class": "SYNTHETIC_UNPAIRED", "purpose": "TECHNICAL_PIPELINE_TEST_ONLY", "native_gold": False}

    def do_device_tests(self, folder):
        return {"status": "REQUIRES_DEVICE", "scope": "Android crash/E2E, SMS, cellular network, latency/pin/RAM require real devices"}

    def do_pte_export(self, folder):
        if not self.config["run_pte"]:
            return {"status": "NOT_REQUESTED", "reason": "Optional separate ExecuTorch 1.4.1-compatible environment; ONNX export is included"}
        if not self.config["run_pruning"]:
            return {"status": "NOT_REQUESTED", "reason": "No new pruned model selected"}
        if not self.config["pte_python"] or not Path(self.config["pte_python"]).is_file():
            raise ValueError("Set pte_python to a separate ExecuTorch 1.4.1-compatible Python; do not replace the GPU environment")
        self.call(TOOLS + "/export_structured_model.py", [
            "--checkpoint", self.root / read(self.out / "image_pruning/selection.json")["selected"]["checkpoint"],
            "--source-checkpoint", self.root / IMAGE / "flood_mobilenetv3_large_best.pth",
            "--config", self.root / IMAGE / "config_mobilenetv3_large.json",
            "--format", "pte", "--output-dir", folder / "model"], folder, python=self.config["pte_python"])


STAGES = ["preflight", "synthetic_data", "historical_analysis", "image_baseline", "image_pruning", "image_export_compare",
          "image_ptq", "image_qat", "quantization_analysis", "public_fusion", "silver_fusion",
          "silver_t2", "silver_evaluation", "synthetic_fusion", "synthetic_t2", "synthetic_evaluation", "native_gold", "device_tests", "pte_export"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--stage", choices=STAGES + ["plan"], required=True)
    args = parser.parse_args()
    run = Run(args.root, read(args.config))
    if args.stage == "plan":
        result = {"status": "PLAN_ONLY", "config": run.config, "stages": STAGES}
    else:
        result = run.stage(args.stage)
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
