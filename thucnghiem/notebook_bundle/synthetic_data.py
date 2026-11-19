"""Compose Vietnamese sentences and arbitrarily pair existing images for code tests.

This is intentionally SYNTHETIC_UNPAIRED, never native reports or human gold.
Labels describe the selected sentence template only, without inspecting images.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import random
from collections import Counter
from pathlib import Path

TAG = "SYNTHETIC_UNPAIRED"
ORIGIN = "SYNTHETIC_TEMPLATE_TEXT_ONLY"
PURPOSE = "TECHNICAL_PIPELINE_TEST_ONLY"
TASK = "vi_synthetic_unpaired_request_v1"
BASE = "thucnghiem/vi_synthetic"
OUT = "docs/revision-plan/outputs/vi-synthetic-unpaired-20261109"
SEED = 20261109
REMOVED_PREFIX = "[MẪU TỰ SOẠN; KHÔNG PHẢI TIN CỨU HỘ THẬT] "
TEMPLATES = {
    "train": {
        "request": [
            "Gia đình trong kịch bản tại điểm giả lập {place} đang mắc kẹt, cần thuyền đưa đến nơi an toàn.",
            "Nhóm trong tình huống giả lập {place} thiếu nước uống, đề nghị hỗ trợ tiếp tế.",
            "Trong bài tập mô phỏng {place}, một người không tự di chuyển được; xin đội hỗ trợ đến đón.",
            "Tình huống huấn luyện tại điểm {place}: người dân đề nghị hỗ trợ sơ tán khỏi khu ngập.",
        ],
        "no_request": [
            "Bản tin giả lập {place} giới thiệu kiến thức phòng tránh lũ lụt.",
            "Thông báo mô phỏng {place} ghi lịch tập huấn kỹ năng ứng phó thiên tai.",
            "Tài liệu huấn luyện {place} giải thích các mức cảnh báo ngập và cách đọc bản đồ.",
            "Bài viết minh họa {place} tổng kết một buổi diễn tập đã kết thúc.",
        ],
    },
    "dev": {
        "request": [
            "Kịch bản kiểm thử {place} có người cần được đưa ra khỏi nơi ngập; mong bố trí phương tiện hỗ trợ.",
            "Trong ca mô phỏng {place}, nhóm đang chờ được cấp nước sạch và lương thực.",
            "Tại ô giả lập {place}, gia đình đề nghị lực lượng hỗ trợ đưa một người tới điểm an toàn.",
        ],
        "no_request": [
            "Nội dung giả lập {place} thông tin về buổi tuyên truyền phòng chống thiên tai.",
            "Mẫu văn bản {place} mô tả cách bảo quản vật dụng trước mùa mưa.",
            "Bản ghi minh họa {place} cập nhật lịch họp rút kinh nghiệm sau diễn tập.",
        ],
    },
    "test": {
        "request": [
            "Trong tình huống tự soạn {place}, người mắc kẹt đề nghị được hỗ trợ rời khu vực bằng thuyền.",
            "Ca kiểm tra giả lập {place}: nhóm không còn nước sạch, cần tiếp tế sớm.",
            "Bài tập tại vị trí giả định {place} yêu cầu hỗ trợ vận chuyển một người không thể đi bộ.",
        ],
        "no_request": [
            "Ví dụ tự soạn {place} giới thiệu tài liệu giáo dục về ứng phó mưa lũ.",
            "Thông tin minh họa {place} công bố lịch bảo trì hệ thống đo mực nước.",
            "Đoạn văn mô phỏng {place} tường thuật kết quả một chương trình tập huấn đã hoàn thành.",
        ],
    },
}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def create_payload(root, split_rows):
    records = []
    for split in ["train", "dev", "test"]:
        source_split = "val" if split == "dev" else split
        selected = sorted((r for r in split_rows if r["split"] == source_split), key=lambda r: r["relative_path"])
        random.Random(SEED + {"train": 1, "dev": 2, "test": 3}[split]).shuffle(selected)
        for index, row in enumerate(selected):
            label = "request" if index % 2 else "no_request"
            image_path = "products/fe/model/Dataset_Flood/" + row["relative_path"]
            identity = hashlib.sha256((str(SEED) + ":" + row["relative_path"]).encode()).hexdigest()
            template_index = (index // 2) % len(TEMPLATES[split][label])
            sentence = TEMPLATES[split][label][template_index].format(place=identity[:10].upper())
            records.append({
                "image_id": "synthetic-" + identity[:20], "tweet_id": "NOT_A_TWEET-" + identity[:20],
                "tweet_text": sentence, "text_vi": sentence, "label": label,
                "image_path": image_path, "image_sha256": sha_file(root / image_path),
                "split": split, "group_id": "flood-group-" + row["split_group"],
                "event_name": "SYNTHETIC_PARTITION_" + split.upper(),
                "event_name_semantics": "artificial partition ID, NOT a disaster event",
                "source_image_id": row["relative_path"], "source_image_label": row["label"],
                "template_id": f"{split}/{label}/{template_index}",
                "label_origin": ORIGIN, "evidence_class": TAG,
                "image_text_relation": "ARBITRARY_UNPAIRED", "human_annotators": 0,
                "rationale": "Label from the authored sentence template only; image not consulted.",
            })
    return {"task": TASK, "status": "DATA_READY", "display_status": "DATA-READY",
            "format_version": 2, "text_prefix": None,
            "evidence_class": TAG, "label_origin": ORIGIN, "language": "vi_synthetic_authored_templates",
            "purpose": PURPOSE, "native_gold": False, "human_labels": 0,
            "image_text_relation": "ARBITRARY_UNPAIRED", "seed": SEED,
            "templates_sha256": sha_bytes(encoded(TEMPLATES)), "records": records,
            "limits": ["Images and sentences were not observed together in any real report",
                       "Labels are template-derived; no human gold, no IAA, no expert approval",
                       "Scores measure a synthetic template task only; no native rescue or fusion effectiveness claims",
                       "Image split groups do not establish independence of real sources/events"]}


def validate_payload(payload, *, root=None):
    expected = {"task": TASK, "status": "DATA_READY", "evidence_class": TAG,
                "label_origin": ORIGIN, "purpose": PURPOSE, "native_gold": False,
                "human_labels": 0, "image_text_relation": "ARBITRARY_UNPAIRED"}
    if any(payload.get(k) != v for k, v in expected.items()):
        raise ValueError("Synthetic data scope/origin was changed; not native or human gold")
    records = payload["records"]
    ids, images, texts, groups = set(), {}, {}, {}
    for row in records:
        if row["image_id"] in ids:
            raise ValueError("Duplicate synthetic report ID")
        ids.add(row["image_id"])
        if row["label_origin"] != ORIGIN or row["evidence_class"] != TAG or row["human_annotators"] != 0:
            raise ValueError("Synthetic row mislabeled as observed or human-annotated data")
        if not row["text_vi"].strip() or REMOVED_PREFIX in row["text_vi"] or row["label"] not in {"request", "no_request"}:
            raise ValueError("Empty text, removed prefix present, or unsupported label")
        template_split, template_label, template_index = row["template_id"].split("/")
        if template_split != row["split"] or template_label != row["label"]:
            raise ValueError("Template provenance differs from the split/label")
        expected_text = TEMPLATES[template_split][template_label][int(template_index)].format(
            place=row["image_id"].removeprefix("synthetic-")[:10].upper())
        if row["text_vi"] != expected_text:
            raise ValueError("Sentence differs from the recorded authored template")
        if row["event_name"] != "SYNTHETIC_PARTITION_" + row["split"].upper():
            raise ValueError("Synthetic partition was reinterpreted as a real event")
        for registry, key in [(images, row["image_sha256"]), (texts, row["text_vi"].casefold()), (groups, row["group_id"])]:
            if key in registry and registry[key] != row["split"]:
                raise ValueError("Synthetic input/group overlaps across splits")
            registry[key] = row["split"]
        if root:
            image = (root / row["image_path"]).resolve()
            if not image.is_relative_to(root.resolve()) or sha_file(image) != row["image_sha256"]:
                raise ValueError("Missing/changed synthetic source image")
    counts = {}
    for split in ["train", "dev", "test"]:
        counts[split] = dict(Counter(r["label"] for r in records if r["split"] == split))
        if set(counts[split]) != {"request", "no_request"}:
            raise ValueError("Synthetic split must contain both template labels")
    return {"status": "DATA_READY", "display_status": "DATA-READY", "n": len(records), "counts": counts,
            "format_version": 2, "text_prefix": None,
            "evidence_class": TAG, "purpose": PURPOSE, "native_gold": False, "human_labels": 0,
            "model_training": "NOT_RUN", "image_text_relation": "ARBITRARY_UNPAIRED"}


def dataset_artifacts(root, split_rows):
    payload = create_payload(root, split_rows)
    readiness = validate_payload(payload, root=root)
    source = root / "docs/revision-plan/outputs/vi-nlp-fusion-silver-20261108"
    protocol = copy.deepcopy(json.loads((source / "protocol.json").read_text()))
    protocol.update(version=TASK, status="LOCKED_BEFORE_SYNTHETIC_FITTING", date="2026-11-09",
                    authorization="User requested arbitrary image pairing with authored Vietnamese sentences and DATA_READY status",
                    task=TASK, language="AI-authored Vietnamese sentence templates; synthetic, not observed reports",
                    label_origin=ORIGIN, evidence_class=TAG, purpose=PURPOSE, native_gold=False,
                    label_view="template ID only; image ignored", n_selected=len(payload["records"]),
                    selection="All existing flood split images; deterministic shuffle, alternating sentence-template labels",
                    split="Keep original image split/groups; artificial partition IDs are NOT real events",
                    source_label_use="Flood labels retained for provenance only, never used to assign request labels",
                    deployment="offline technical pipeline tests; no serving changes", limits=payload["limits"],
                    source_dataset_sha256=sha_file(root / "products/fe/model/Edge Ai/split_train_val_test_mobilenetv3_large.csv"),
                    selection_sha256=sha_bytes(encoded(TEMPLATES)))
    protocol["bootstrap"]["unit"] = "source image split groups within an artificial test partition; synthetic diagnostics only"
    protocol["classifier"]["seed"] = SEED
    protocol_bytes, data_bytes = encoded(protocol), encoded(payload)
    t2 = copy.deepcopy(json.loads((source / "t2-protocol.json").read_text()))
    t2.update(scope="Fine-tuning on SYNTHETIC_UNPAIRED templates only; not native/human-gold validation",
              dataset_sha256=sha_bytes(data_bytes), base_protocol_sha256=sha_bytes(protocol_bytes),
              evidence_class=TAG, purpose=PURPOSE, native_gold=False)
    lock = {"status": "SYNTHETIC_DATA_FROZEN_BEFORE_FITTING", "dataset_sha256": sha_bytes(data_bytes),
            "protocol_sha256": sha_bytes(protocol_bytes), "counts": readiness["counts"],
            "evidence_class": TAG, "human_labels": 0, "expert_approvals": 0, "native_gold": False}
    stream = io.StringIO(newline="")
    columns = ["report_id", "label", "label_origin", "template_id", "stage", "human_annotators"]
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    for row in payload["records"]:
        writer.writerow({"report_id": row["image_id"], "label": row["label"], "label_origin": ORIGIN,
                         "template_id": row["template_id"], "stage": "synthetic_generated", "human_annotators": 0})
    files = {
        BASE + "/data/dataset.json": data_bytes,
        BASE + "/data/templates.json": encoded(TEMPLATES),
        BASE + "/data/annotations.csv": stream.getvalue().encode(),
        OUT + "/protocol.json": protocol_bytes,
        OUT + "/t2-protocol.json": encoded(t2),
        OUT + "/dataset-lock.json": encoded(lock),
        OUT + "/readiness.json": encoded(readiness),
    }
    return files, readiness
