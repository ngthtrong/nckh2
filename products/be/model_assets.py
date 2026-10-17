"""Model artifacts served only by the authenticated admin endpoints."""
import hashlib
import json
import os
from pathlib import Path

from fastapi import HTTPException

EXPORT_DIR = Path(os.environ.get(
    "RESCUE_MODEL_EXPORT_DIR",
    Path(__file__).resolve().parents[1] / "fe" / "model" / "Edge Ai" / "Export",
))
FILENAMES = {
    "onnx": "flood_mobilenetv3_large.onnx",
    "pte": "flood_mobilenetv3_large.pte",
}


def catalog():
    try:
        manifest = json.loads((EXPORT_DIR / "model_manifest.json").read_text(encoding="utf-8"))
        artifacts = {}
        for runtime, filename in FILENAMES.items():
            path = EXPORT_DIR / filename
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != manifest[f"{runtime}_sha256"]:
                raise ValueError(f"{runtime} does not match manifest")
            artifacts[runtime] = {"sha256": digest, "bytes": path.stat().st_size}
        return {"manifest": manifest, "artifacts": artifacts}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(503, detail="Tài nguyên model chưa sẵn sàng hoặc không khớp manifest") from exc


def artifact(runtime):
    if runtime not in FILENAMES:
        raise HTTPException(404, detail="Runtime không hợp lệ")
    catalog()
    return EXPORT_DIR / FILENAMES[runtime]
