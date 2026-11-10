"""Validate archive contents and notebook bootstrap without ML execution."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build import safe_name
from runtime import digest, preflight, write


def extract_and_verify(bundle, destination):
    index = json.loads((bundle / "bundle-index.json").read_text())
    manifests, archive_bindings = [], {}
    for entry in index["archives"]:
        path = bundle / entry["name"]
        if path.stat().st_size != entry["bytes"] or digest(path) != entry["sha256"]:
            raise ValueError("Archive hash mismatch: " + entry["name"])
        archive_bindings[entry["name"]] = entry["sha256"]
        with zipfile.ZipFile(path) as package:
            names = package.namelist()
            manifest = json.loads(package.read(entry["manifest"]))
            if len(names) != len(set(names)) or set(names) != set(manifest["files"]) | {entry["manifest"]}:
                raise ValueError("Undeclared/duplicate members")
            if manifest["package"] != entry["package"]:
                raise ValueError("Wrong package identity")
            for info in package.infolist():
                safe_name(info.filename)
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError("Symlink in archive")
                target = destination / info.filename
                expected = manifest["files"].get(info.filename)
                if target.exists():
                    if expected is None or digest(target) != expected:
                        raise ValueError("Conflicting duplicate input")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with package.open(info) as source, target.open("xb") as out:
                    import shutil
                    shutil.copyfileobj(source, out)
                if expected is not None and digest(target) != expected:
                    raise ValueError("Member hash mismatch")
            manifests.append(manifest)
    write(destination / "bundle-inputs.json", {"packages": manifests, "archive_bindings": {"archives": archive_bindings}})
    return manifests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-dir", type=Path, default=HERE / "dist")
    parser.add_argument("--test-python", type=Path, help="Optional numeric environment for fixture-only unit tests")
    args = parser.parse_args()
    bundle = args.bundle_dir.resolve()
    notebook = json.loads((bundle / "NCKH2_All_In_One.ipynb").read_text())
    if notebook["nbformat"] != 4:
        raise ValueError("Unexpected notebook format")
    ids = []
    for i, cell in enumerate(notebook["cells"]):
        ids.append(cell["id"])
        if cell["cell_type"] == "code":
            if cell["outputs"] or cell["execution_count"] is not None:
                raise ValueError("Notebook carries precomputed output")
            compile("".join(cell["source"]), f"cell-{i}", "exec")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate cell ids")
    with tempfile.TemporaryDirectory(prefix="nckh2-bundle-validation-") as tmp:
        project = Path(tmp) / "project"
        project.mkdir()
        manifests = extract_and_verify(bundle, project)
        for p in project.rglob("*.py"):
            ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        report = preflight(project, torch_check=False)
        synthetic_loader = subprocess.run([sys.executable, "-c",
            "import sys,json; sys.path.insert(0,sys.argv[1]); from common import load_data,TASK; "
            "rows=load_data(); print(json.dumps({'task':TASK,'n':len(rows)}))",
            str(project / "thucnghiem/vi_synthetic")], check=True, capture_output=True, text=True)
        loaded_synthetic = json.loads(synthetic_loader.stdout)
        if loaded_synthetic != {"task": "vi_synthetic_unpaired_request_v1", "n": 1702}:
            raise ValueError("Packaged synthetic pipeline loader mismatch")
        numeric_profile = None
        if args.test_python:
            check = r'''
import csv,inspect,json,sys,importlib
from collections import Counter
from pathlib import Path
import numpy,scipy,sklearn,onnx,onnxruntime
from PIL import Image,features
from onnxruntime.quantization.qdq_loss_debug import collect_activations,create_activation_matching
importlib.import_module('numpy._core.multiarray')
base=Path(sys.argv[1]); counts=Counter(); decoded=set()
with (base/'products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv').open(encoding='utf-8-sig') as f:
 for row in csv.DictReader(f):
  path=base/'products/fe/model/Dataset_Flood'/row['relative_path']
  with Image.open(path) as image:
   fmt=image.format; counts[fmt]+=1; image.verify()
  if fmt not in decoded:
   with Image.open(path) as image: image.load()
   decoded.add(fmt)
if not features.check('avif'): raise ValueError('AVIF decoding unavailable')
print(json.dumps({'numpy':numpy.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__,
 'onnx':onnx.__version__,'onnxruntime':onnxruntime.__version__,'Pillow':Image.__version__,
 'formats_verified':dict(counts),'one_image_per_format_decoded':sorted(decoded),
 'qdq_debug_signature':str(inspect.signature(collect_activations))}))
'''
            # Keep the venv executable path: resolve() follows its symlink to the
            # system interpreter and silently discards the selected environment.
            result = subprocess.run([str(args.test_python.absolute()), "-c", check, str(project)],
                                    capture_output=True, text=True, check=True)
            numeric_profile = json.loads(result.stdout)
        config = project / "validation-config.json"
        write(config, {})
        result = subprocess.run([sys.executable, str(project / "toolkit/runtime.py"), "--root", str(project),
                                 "--config", str(config), "--stage", "plan"], check=True, capture_output=True, text=True)
        if json.loads(result.stdout)["status"] != "PLAN_ONLY":
            raise ValueError("Plan unexpectedly executed experiments")
        readiness = {}
        for stage, expected in [("synthetic_data", "DATA_READY"), ("native_gold", "DATA_NOT_READY")]:
            result = subprocess.run([sys.executable, str(project / "toolkit/runtime.py"), "--root", str(project),
                                     "--config", str(config), "--stage", stage], check=True, capture_output=True, text=True)
            receipt = json.loads(result.stdout)
            if receipt["status"] != expected:
                raise ValueError("Wrong scoped readiness state: " + stage)
            readiness[stage] = {"status": receipt["status"], "details": receipt["details"]}
        # Execute the EXACT shipped bootstrap from a fresh project and once more
        # for the resume/input-binding path. Never install or execute ML here.
        first = "".join(notebook["cells"][1]["source"])
        setup = "".join(notebook["cells"][2]["source"])
        space = {"__name__": "__validation__"}
        exec(compile(first, "notebook-configuration", "exec"), space)
        space.update(ARCHIVE_DIR=bundle, WORK_ROOT=Path(tmp), RUN_ID="notebook-project", INSTALL_DEPENDENCIES=False,
                     EXISTING_PYTHON=sys.executable)
        exec(compile(setup, "notebook-bootstrap", "exec"), space)
        exec(compile(setup, "notebook-bootstrap-resume", "exec"), space)
        zipped = space["export_results"]()
        if not zipped.is_file():
            raise ValueError("Notebook result ZIP was not created")
        with zipfile.ZipFile(zipped) as archive:
            for name in archive.namelist():
                if any(part in name for part in ["/data_image/", "/Dataset_Flood/", "/huggingface/", "/label-batches/"]):
                    raise ValueError("Result ZIP accidentally includes raw inputs/caches")
        summary = {"status": "PACKAGING_VERIFIED_NO_TRAINING", "archive_count": len(manifests),
                   "file_entries": {m["package"]: len(m["files"]) for m in manifests},
                   "preflight": report, "notebook_cells": len(notebook["cells"]),
                   "scoped_readiness": readiness,
                   "synthetic_pipeline_loader": loaded_synthetic,
                   "checked": ["all ZIP SHA256 and entry SHA256", "declared-only safe paths and duplicate handling",
                               "image MD5 and split-group checks", "paired image SHA256 and identity/event leakage checks",
                               "source Python AST and notebook code compile", "CLI plan without model execution",
                               "exact notebook fresh extraction and resume with install disabled", "result ZIP excludes raw data/caches"],
                   "not_run": ["pip/CUDA environment installation", "GPU forward/training/export", "actual model inference",
                               "PTQ/QAT layer instrumentation", "public/silver training or statistical replay on study data",
                               "Android/SMS/real network", "report edits/build", "native-gold study"]}
        if numeric_profile:
            summary["numeric_profile_and_image_codecs"] = numeric_profile
    if args.test_python:
        command = [str(args.test_python.absolute()), "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_*.py", "-v"]
        result = subprocess.run(command, capture_output=True, text=True)
        log = bundle / "unit-tests.log"
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        summary["unit_tests"] = {"command": command, "exit_code": result.returncode, "log_sha256": digest(log),
                                 "scope": "Synthetic fixtures only; no research training or inference"}
        if result.returncode:
            raise RuntimeError("Fixture tests failed; see " + str(log))
    write(bundle / "validation.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
