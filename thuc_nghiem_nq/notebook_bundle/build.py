"""Build a whitelist-only, local notebook/data bundle. No training or uploading."""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from runtime import DEFAULT, PUBLIC, SILVER, IMAGE, SPLIT, DATA, TOOLS, digest
import synthetic_data as synthetic


def encode(data):
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def safe_name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or ".." in p.parts or "\\" in name or ":" in name:
        raise ValueError("Unsafe archive member: " + name)
    return str(p)


class Package:
    def __init__(self, name, metadata):
        self.name, self.metadata, self.entries = name, metadata, {}

    def add(self, source, name=None):
        source = Path(source)
        if not source.is_absolute():
            source = ROOT / source
        if not source.is_file():
            raise FileNotFoundError(source)
        key = safe_name(name or str(source.relative_to(ROOT)))
        value = (source, digest(source), source.stat().st_size)
        if key in self.entries and self.entries[key][1:] != value[1:]:
            raise ValueError("Conflicting package entry: " + key)
        self.entries[key] = value

    def text(self, name, value):
        value = value.encode() if isinstance(value, str) else value
        self.entries[safe_name(name)] = (value, hashlib.sha256(value).hexdigest(), len(value))

    def manifest(self):
        return {"package": self.name, "metadata": self.metadata,
                "files": {k: v[1] for k, v in sorted(self.entries.items())},
                "bytes": sum(v[2] for v in self.entries.values())}

    def save(self, destination):
        destination = Path(destination)
        with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
            for name, (value, _, _) in sorted(self.entries.items()):
                if isinstance(value, Path):
                    z.write(value, name)
                else:
                    z.writestr(name, value)
            z.writestr("_bundle/manifests/" + self.name + ".json", encode(self.manifest()))
        return {"name": destination.name, "package": self.name,
                "sha256": digest(destination), "bytes": destination.stat().st_size,
                "manifest": "_bundle/manifests/" + self.name + ".json"}


def replace_once(source, old, new, count=1):
    if source.count(old) != count:
        raise ValueError(f"Patch anchor mismatch: expected {count}, got {source.count(old)}: {old[:80]!r}")
    return source.replace(old, new)


def portable_source(name, text):
    """Patch package copies only; original model/pilot sources remain unchanged."""
    changes = []
    if Path(name).name == "structured_pruning.py":
        text = replace_once(text, '    parser.add_argument("--prune-ratio",',
            '    parser.add_argument("--defer-test", action="store_true", help="Select across ratios using validation before any test")\n'
            '    parser.add_argument("--prune-ratio",')
        text = replace_once(text, '    test_metrics = evaluate(best_model, loaders["test"], config, device)',
                            '    test_metrics = None if args.defer_test else evaluate(best_model, loaders["test"], config, device)')
        text = replace_once(text, '"evaluation_protocol": "train_and_select_on_saved_train_val; test evaluated once after best epoch",',
            '"evaluation_protocol": "validation-only candidate selection; test deferred" if args.defer_test else "single-config test after selection",')
        old = '    LOGGER.info("Final test: acc=%.4f macro_f1=%.4f critical=%s/%d",\n                test_metrics["accuracy"], test_metrics["macro_f1"],\n                test_metrics.get("critical_error_count", "n/a"), len(splits["test"]))'
        text = replace_once(text, old, '    if test_metrics is not None:\n' + "\n".join("    " + line for line in old.splitlines()))
        changes.append("Add --defer-test: candidate grid cannot inspect test before validation selection")
    if name.endswith("vi_rescue/features.py"):
        old = "    response = requests.get('https://huggingface.co/api/models/' + repo, timeout=60)\n    response.raise_for_status()\n    revision = response.json()['sha']\n    directory = snapshot_download(repo, revision=revision, cache_dir=BASE / 'cache/huggingface',\n        allow_patterns=['config.json', 'tokenizer.json', 'tokenizer_config.json',\n                        'vocab.txt', 'special_tokens_map.json', 'model.safetensors'])"
        new = "    revision = '45c032ab32cc946ad88a166f7cb282f58c753c2e'\n    directory = str(BASE / 'cache/huggingface' / ('models--' + repo.replace('/', '--')) / 'snapshots' / revision)\n    if not (Path(directory) / 'model.safetensors').is_file():\n        raise FileNotFoundError('Pinned local DistilBERT snapshot missing')"
        text = replace_once(text, old, new)
        changes.append("Use packaged, hash-bound DistilBERT revision offline; never resolve latest")
    if name.endswith("vi_rescue/train.py"):
        text = replace_once(text, "    joblib.dump(bundle, target, compress=3)",
                            "    target.parent.mkdir(parents=True, exist_ok=True)\n"
                            "    joblib.dump(bundle, target, compress=3)")
        changes.append("Create classifier output directory; ZIP archives do not preserve empty source directories")
    if name.endswith("vi_rescue/fine_tune.py"):
        anchor = "T2_PROTOCOL = OUT / 't2-protocol.json'"
        text = replace_once(text, anchor, anchor + "\nDEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')")
        text = replace_once(text, "str(snapshot), local_files_only=True, use_safetensors=True)",
                            "str(snapshot), local_files_only=True, use_safetensors=True, attn_implementation='eager')")
        text = replace_once(text, "    torch.manual_seed(seed)", "    torch.manual_seed(seed)\n    if torch.cuda.is_available():\n        torch.cuda.manual_seed_all(seed)")
        text = replace_once(text, "max_length=max_length, return_tensors='pt')",
                            "max_length=max_length, return_tensors='pt').to(DEVICE)")
        text = replace_once(text, "[:, 1].numpy()", "[:, 1].detach().cpu().numpy()")
        text = replace_once(text, "    rows = load_data()", "    if DEVICE.type != 'cuda':\n        raise RuntimeError('This notebook T2 profile requires real CUDA; CPU pilot already exists')\n    print('T2 device:', DEVICE, torch.cuda.get_device_name(0), flush=True)\n    rows = load_data()")
        text = replace_once(text, "train_labels = torch.tensor(labels['train'], dtype=torch.long)",
                            "train_labels = torch.tensor(labels['train'], dtype=torch.long, device=DEVICE)")
        text = replace_once(text, "    criterion = nn.CrossEntropyLoss(weight=class_weights, reduction='sum')",
                            "    class_weights = class_weights.to(DEVICE)\n    criterion = nn.CrossEntropyLoss(weight=class_weights, reduction='sum')")
        text = replace_once(text, "model = MeanPoolClassifier(snapshot, float(protocol['dropout']))",
                            "model = MeanPoolClassifier(snapshot, float(protocol['dropout'])).to(DEVICE)", count=2)
        text = replace_once(text, "'cpu_threads': int(protocol['cpu_threads']), 'torch': torch.__version__,",
                            "'cpu_threads': int(protocol['cpu_threads']), 'torch': torch.__version__,\n        'device': str(DEVICE), 'gpu': torch.cuda.get_device_name(0),")
        changes.append("Move model/tokens/targets/CE weights to CUDA; CPU copies for NumPy; eager attention for deterministic CUDA; record actual GPU")
    if name.endswith("qat_finetune.py"):
        text = replace_once(text, "    seed_everything(42)\n", "")
        text = replace_once(text, '    config = json.loads(args.config.read_text(encoding="utf-8"))',
                            '    config = json.loads(args.config.read_text(encoding="utf-8"))\n    seed_everything(int(config.get("seed", 42)))')
        changes.append("Bind new QAT RNG seed to supplied config instead of hard-coded 42")
    ast.parse(text, filename=name)
    return text, changes


def synthetic_source(name, text):
    """Reuse the portable pilot's mechanics under a separate synthetic task/root."""
    text = text.replace("vi_translated_silver_request_v1", synthetic.TASK)
    text = text.replace(SILVER, synthetic.OUT)
    text = text.replace("AI_SILVER_TEXT_ONLY", synthetic.ORIGIN)
    text = text.replace("AI_SILVER_LABELS", "SYNTHETIC_TEMPLATE_LABELS")
    text = text.replace("AI_SILVER_PILOT", "SYNTHETIC_PIPELINE")
    text = text.replace("task_and_ai_silver_scope", "task_and_synthetic_scope")
    text = text.replace("evaluation_counts_and_one_event_scope", "evaluation_counts_and_artificial_partition_scope")
    for old, new in [
        ("label_ai", "label_synthetic"), ("AI-translated", "AI-authored synthetic"),
        ("AI silver", "synthetic template"), ("AI-silver", "synthetic unpaired"),
        ("AI labels", "template labels"), ("AI label", "template label"),
        ("silver pilot", "synthetic pipeline test"),
        ("held-out event", "artificial test partition"), ("known event", "artificial partition"),
        ("source text", "authored template"),
    ]:
        text = text.replace(old, new)
    # Share packaged pretrained caches; feature/model OUTPUTS remain separate.
    text = text.replace("BASE / 'cache/huggingface'", "ROOT / 'thucnghiem/vi_rescue/cache/huggingface'")
    text = text.replace("BASE / 'cache/torch", "ROOT / 'thucnghiem/vi_rescue/cache/torch")
    if name == "features":
        text = replace_once(text, "    target = BASE / 'cache/embeddings.npz'",
                            "    target = BASE / 'cache/embeddings.npz'\n    target.parent.mkdir(parents=True, exist_ok=True)")
    if name == "common":
        text = replace_once(text, "def write_json(path, value):\n    path = Path(path)",
            "def write_json(path, value):\n"
            "    if isinstance(value, dict):\n"
            "        value = {**value, 'evidence_class': 'SYNTHETIC_UNPAIRED',\n"
            "                 'purpose': 'TECHNICAL_PIPELINE_TEST_ONLY', 'native_gold': False,\n"
            "                 'human_labels': 0, 'image_text_relation': 'ARBITRARY_UNPAIRED',\n"
            "                 'scope': 'Authored Vietnamese sentence templates arbitrarily paired with flood images; technical testing only',\n"
            "                 'limits': ['Not observed rescue reports or naturally paired inputs',\n"
            "                            'No independent human labels, IAA, expert approval or real-event holdout',\n"
            "                            'Template-task metrics do not validate native Vietnamese rescue NLP or fusion effectiveness']}\n"
            "    path = Path(path)")
        text = replace_once(text, "    rows = data['records']",
            "    if data.get('evidence_class') != 'SYNTHETIC_UNPAIRED' or data.get('native_gold') is not False:\n"
            "        raise ValueError('Synthetic data cannot be presented as native gold')\n"
            "    rows = data['records']")
    ast.parse(text)
    return text


def packages():
    code = Package("runtime", {"scope": "Portable source copies and input protocols; no results asserted",
                                "future_development": "CONTENT_ONLY", "native_gold": "DATA_NOT_READY"})
    changes = {}
    for name in ["runtime.py", "analysis.py", "image_baseline.py", "synthetic_data.py", "requirements-gpu.txt"]:
        code.add(HERE / name, "toolkit/" + name)
    legacy = ["structured_pruning.py", "compare_models.py", "compare_structured_pruning.py", "convert_model.py",
              "quantize_model.py", "qat_finetune.py", "compare_fp32_ptq_qat.py", "export_structured_model.py", "export_executorch.py"]
    for name in [TOOLS + "/" + n for n in legacy] + [
        "thucnghiem/" + kind + "/" + name + ".py"
        for kind, names in [("multimodal", ["common", "features", "train", "evaluate", "verify"]),
                            ("vi_rescue", ["common", "features", "train", "fine_tune", "evaluate", "verify", "verify_encoder_update"])]
        for name in names]:
        original = (ROOT / name).read_text(encoding="utf-8")
        patched, notes = portable_source(name, original)
        code.text(name, patched)
        changes[name] = {"source_sha256": digest(ROOT / name), "packaged_sha256": hashlib.sha256(patched.encode()).hexdigest(), "changes": notes}
    for module in ["common", "features", "train", "fine_tune", "evaluate", "verify", "verify_encoder_update"]:
        source = "thucnghiem/vi_rescue/" + module + ".py"
        portable, _ = portable_source(source, (ROOT / source).read_text())
        patched = synthetic_source(module, portable)
        target = synthetic.BASE + "/" + module + ".py"
        code.text(target, patched)
        changes[target] = {"source_sha256": digest(ROOT / source),
                           "packaged_sha256": hashlib.sha256(patched.encode()).hexdigest(),
                           "changes": ["Separate SYNTHETIC_UNPAIRED task/output root", "Reuse pinned pretrained caches only",
                                       "Template labels and arbitrary pairing explicitly disclosed in all JSON outputs"]}
    code.text("toolkit/source-adaptations.json", encode(changes))
    for folder, names in [(SILVER, ["protocol.json", "t2-protocol.json", "dataset-lock.json"]),
                          (PUBLIC, ["protocol.json", "selection-lock.json", "data-audit.json", "sources.json", "image-downloads.json", "split-manifest.csv"])]:
        for name in names:
            code.add(folder + "/" + name)
    for name, folder in [("pruning", "prunning_st"), ("quantization", "fp32_ptq_qat")]:
        for filename in ["all_predictions.csv", "summary.json"]:
            code.add(f"products/fe/reports/seed1024/{folder}/{filename}", f"historical_evidence/{name}/{filename}")
    code.text("native_templates/README.md", "# DATA_NOT_READY\nNo native Vietnamese corpus or human labels are included. Do not rename silver as gold.\nNative data require an agreed target, genuinely paired inputs, source/usage records, independent annotations/adjudication and an event/source-group split before a separate protocol and runner can be enabled.\nNo field-photo collection, travel-cost scheduler or field trial is executed: these are report Future Work.\n")
    code.text("native_templates/records.csv", "report_id,event_id,source_id,text_vi,image_path,image_sha256,usage_basis,split,group_id\n")
    code.text("native_templates/annotations.csv", "report_id,annotator_id,stage,label,label_origin,uncertainty,evidence_ref\n")
    flood = Package("flood_images", {"n": 1702, "splits": {"train": 1189, "val": 257, "test": 256},
                "label_origin": "GROUP_MANUAL_LABELS_IAA_UNKNOWN", "scope": "Historical development data",
                "source_event_independence": "UNVERIFIED", "image_licenses": "UNRESOLVED_PER_IMAGE"})
    flood.add(SPLIT)
    flood.add(IMAGE + "/config_mobilenetv3_large.json")
    with (ROOT / SPLIT).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 1702:
        raise ValueError("Unexpected flood dataset")
    for row in rows:
        source = ROOT / DATA / safe_name(row["relative_path"])
        if hashlib.md5(source.read_bytes()).hexdigest() != row["md5"]:
            raise ValueError("Image changed: " + str(source))
        flood.add(source)
    public = Package("crisis_public", {"n_pairs": 4261, "task": "public_crisis_informativeness",
                                      "splits": {"train": 2971, "dev": 589, "test": 701}, "not_native_vietnamese": True})
    public.add("thucnghiem/multimodal/data/dataset.json")
    for name in ["sources.json", "image-downloads.json"]:
        for row in json.loads((ROOT / PUBLIC / name).read_text()):
            p = ROOT / "thucnghiem/multimodal" / safe_name(row["path"])
            if digest(p) != row["sha256"]:
                raise ValueError("Public source changed: " + str(p))
            public.add(p)
    silver = Package("vi_silver", {"n_pairs": 296, "selected": 300, "uncertain_excluded": 4,
             "splits": {"train": 179, "dev": 58, "test": 59}, "label_origin": "AI_SILVER_TEXT_ONLY",
             "human_labels": 0, "scope": "Translated foreign-event development pilot; not native/human gold"})
    for name in ["dataset.json", "excluded.json", "selection.json"]:
        silver.add("thucnghiem/vi_rescue/data/" + name)
    for row in json.loads((ROOT / "thucnghiem/vi_rescue/data/selection.json").read_text()):
        p = ROOT / "thucnghiem/multimodal/data" / safe_name(row["image"])
        if digest(p) != row["image_sha256"]:
            raise ValueError("Silver image changed")
        silver.add(p)
    for name in ["input-1.json", "input-2.json", "input-3.json", "output-1.json", "output-2.json", "output-3.json"]:
        silver.add(SILVER + "/label-batches/" + name)
    models = Package("models", {"source_image_seed": 1024, "distilbert_revision": "45c032ab32cc946ad88a166f7cb282f58c753c2e",
                                 "scope": "Original baseline/quantized artifacts and pinned pretrained encoders; no new model trained"})
    for relative in ["flood_mobilenetv3_large_best.pth", "export/baseline/model_manifest.json", "export/baseline/flood_mobilenetv3_large.onnx",
                     "Quantize/flood_mobilenetv3_large.int8.onnx", "Quantize/model_manifest_int8.json",
                     "QAT/flood_mobilenetv3_large.qat.int8.onnx", "QAT/flood_mobilenetv3_large_qat_best.pth", "QAT/model_manifest_qat.json"]:
        models.add(IMAGE + "/" + relative)
    snapshot = ROOT / "thucnghiem/vi_rescue/cache/huggingface/models--distilbert--distilbert-base-multilingual-cased/snapshots/45c032ab32cc946ad88a166f7cb282f58c753c2e"
    feature_receipt = json.loads((ROOT / SILVER / "features.json").read_text())
    for name, expected in feature_receipt["text_files_sha256"].items():
        if digest(snapshot / name) != expected:
            raise ValueError("Pretrained text snapshot changed")
        models.add(snapshot / name)
    for name, expected in [("thucnghiem/vi_rescue/cache/torch/checkpoints/mobilenet_v3_large-5c1a4163.pth", feature_receipt["image_weights_sha256"]),
                           ("thucnghiem/multimodal/cache/torch/checkpoints/mobilenet_v3_small-047dcff4.pth", "047dcff4addef86ea5bc2eff13c9614dc11f47ab1160d0a71a25e7db994f4e1f")]:
        if digest(ROOT / name) != expected:
            raise ValueError("Pretrained image weights changed")
        models.add(name)
    files, readiness = synthetic.dataset_artifacts(ROOT, rows)
    composed = Package("vi_synthetic", readiness)
    for name, value in files.items():
        composed.text(name, value)
    composed.text(synthetic.BASE + "/data/README.md", "# DATA_READY — SYNTHETIC_UNPAIRED\nẢnh Dataset_Flood được ghép tùy ý với câu tiếng Việt tự soạn. Nhãn từ loại khuôn câu, không đọc ảnh. Chỉ dùng kiểm tra kỹ thuật; không phải báo cáo cứu hộ thực, native gold hoặc dữ liệu người gán độc lập. Ảnh được dùng lại từ 01_flood_images.zip.\n")
    return [code, flood, public, silver, models, composed]


def cell(kind, source):
    value = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        value.update(execution_count=None, outputs=[])
    return value


def notebook(index):
    configuration = '''from pathlib import Path
import json, sys, os, subprocess, time, hashlib, zipfile, shutil, stat

# Kaggle: attach all six ZIP files as PRIVATE input; enable Internet for pip.
# Colab: put ZIP files in /content or a Drive folder, then set ARCHIVE_DIR.
# Local/WSL: put notebook and ZIP files together. Python 3.10-3.12.
ARCHIVE_DIR = None                 # e.g. Path('/content/drive/MyDrive/nckh2-bundle')
WORK_ROOT = Path('/kaggle/working/nckh2-bundle') if Path('/kaggle').exists() else Path('/content/nckh2-bundle') if Path('/content').exists() else Path.cwd() / 'nckh2-work'
RUN_ID = time.strftime('run-%Y%m%d-%H%M%S')  # reuse this exact ID to skip VERIFIED completed stages
INSTALL_DEPENDENCIES = True
EXISTING_PYTHON = None              # optional compatible Python; INSTALL_DEPENDENCIES=False
CONFIG = __CONFIG__
'''.replace("__CONFIG__", repr(DEFAULT))
    bootstrap = (HERE / "notebook_bootstrap.py").read_text()
    bootstrap = bootstrap.replace("BUNDLE_INDEX = None  # replaced by builder", "BUNDLE_INDEX = " + repr(index))
    stages = [
        ("Kiểm dữ liệu và CUDA", ["preflight"]),
        ("Ảnh ghép tùy ý với câu tự soạn: DATA_READY / SYNTHETIC_UNPAIRED", ["synthetic_data"]),
        ("McNemar/CI từ dự đoán lịch sử", ["historical_analysis"]),
        ("Baseline tùy chọn, ba mức cắt tỉa, chọn bằng validation", ["image_baseline", "image_pruning"]),
        ("Xuất ONNX, so sánh mô hình đã chọn, McNemar/CI", ["image_export_compare"]),
        ("PTQ, QAT tùy chọn và chẩn đoán lượng tử hóa", ["image_ptq", "image_qat", "quantization_analysis"]),
        ("Pilot CrisisMMD informative", ["public_fusion"]),
        ("Pilot tiếng Việt dịch: frozen fusion, DistilBERT CUDA và kiểm độc lập", ["silver_fusion", "silver_t2", "silver_evaluation"]),
        ("Kiểm tra pipeline trên dữ liệu tự soạn, không phải native gold", ["synthetic_fusion", "synthetic_t2", "synthetic_evaluation"]),
        ("Ghi rõ nhánh thiếu dữ liệu/thiết bị; PTE tùy chọn", ["native_gold", "device_tests", "pte_export"]),
    ]
    cells = [cell("markdown", "# NCKH2 — một notebook chạy bộ thực nghiệm\n\n"
        "**Phạm vi:** cắt tỉa/PTQ/QAT ảnh; baseline tùy chọn; CrisisMMD; tiếng Việt dịch/nhãn AI; fine-tuning DistilBERT; paired statistics; ONNX. "
        "Không sửa báo cáo, không công bố dữ liệu. Bộ ảnh ghép với câu tự soạn có **DATA_READY / SYNTHETIC_UNPAIRED** để kiểm tra kỹ thuật. Tin tiếng Việt gốc/gold và tập camera xác nhận vẫn **DATA_NOT_READY**. "
        "Android/SMS/mạng thật cần thiết bị. Các kiến nghị phát triển chỉ là nội dung Hướng phát triển, không được thực thi.\n\n"
        "Mỗi Run all tạo RUN_ID mới. Kết quả dùng lại các test đã xem: **development replay**, không xác nhận độc lập. "
        "`run_baseline=False`, `run_qat=False`, `run_pte=False` là mặc định vì các nhánh có điều kiện. `run_synthetic=True` chạy frozen NLP/fusion tự soạn; chỉ bật `run_synthetic_t2=True` nếu muốn thêm sáu phiên DistilBERT trên dữ liệu này. Ba tỷ lệ 5/10/20% là cấu hình đề xuất, được khóa trước chạy và chọn bằng validation.\n"),
        cell("code", configuration), cell("code", bootstrap)]
    for title, tasks in stages:
        cells.append(cell("markdown", "## " + title + "\n"))
        cells.append(cell("code", "\n".join("run_stage(" + repr(name) + ")" for name in tasks) + "\n"))
    cells.append(cell("markdown", "## Xuất kết quả\nZIP tự động được cập nhật sau mỗi bước, kể cả khi bước lỗi. Không chứa raw datasets hoặc pretrained caches. Tải ZIP kết quả và notebook đã chạy; không coi trạng thái DATA_NOT_READY/REQUIRES_DEVICE là hoàn tất nghiên cứu.\n"))
    cells.append(cell("code", "result_zip = export_results()\nprint('Kết quả:', result_zip)\nfrom IPython.display import display, FileLink\ndisplay(FileLink(str(result_zip)))\n# Colab nếu cần: from google.colab import files; files.download(str(result_zip))\n"))
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"}, "accelerator": "GPU"}, "cells": cells}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "dist")
    parser.add_argument("--refresh-runtime", action="store_true", help="Refresh generated code/notebook only; verify unchanged data/model ZIPs")
    parser.add_argument("--refresh-synthetic", action="store_true", help="Explicitly regenerate the user-edited synthetic corpus; archive its prior ZIP")
    args = parser.parse_args()
    if args.refresh_synthetic:
        args.refresh_runtime = True
    output = args.output.resolve()
    if args.refresh_runtime:
        existing = json.loads((output / "bundle-index.json").read_text())
        if existing["version"] != "nckh2-notebook-bundle-1":
            raise ValueError("Wrong bundle identity")
        old_index = existing["archives"]
    else:
        output.mkdir(parents=True, exist_ok=False)
    built = packages()
    index = []
    for number, package in enumerate(built):
        target = output / f"{number:02d}_{package.name}.zip"
        if args.refresh_runtime and number and number < len(old_index):
            old = old_index[number]
            if old["name"] != target.name or digest(target) != old["sha256"]:
                raise ValueError("Existing archive changed")
            with zipfile.ZipFile(target) as archive:
                unchanged = json.loads(archive.read(old["manifest"])) == package.manifest()
                if not unchanged and not (args.refresh_synthetic and package.name == "vi_synthetic"):
                    raise ValueError("Input source changed; make a new bundle instead")
            if unchanged:
                index.append(old)
                continue
            history = output / "_history"
            history.mkdir(exist_ok=True)
            previous = history / (package.name + "-" + old["sha256"][:16] + ".zip")
            if not previous.exists():
                shutil.copy2(target, previous)
        print("PACK", target.name, len(package.entries), "files", flush=True)
        if args.refresh_runtime:
            if number >= len(old_index) and target.exists():
                raise ValueError("Unindexed ZIP already exists; refusing to replace it")
            temporary = target.with_suffix(".zip.new")
            updated = package.save(temporary)
            temporary.replace(target)
            updated["name"] = target.name
            index.append(updated)
        else:
            index.append(package.save(target))
    (output / "bundle-index.json").write_bytes(encode({"version": "nckh2-notebook-bundle-1", "archives": index}))
    nb = notebook(index)
    for i, item in enumerate(nb["cells"]):
        item["id"] = "cell-" + str(i).zfill(3)
        if item["cell_type"] == "code":
            compile("".join(item["source"]), f"notebook-cell-{i}", "exec")
    (output / "NCKH2_All_In_One.ipynb").write_bytes(encode(nb))
    shutil.copy2(HERE / "README.md", output / "README.md")
    (output / "synthetic-readiness.json").write_bytes(encode(built[-1].metadata))
    print(json.dumps(index, indent=2), flush=True)


if __name__ == "__main__":
    main()
