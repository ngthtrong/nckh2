import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def jpeg_bytes() -> bytes:
    return b"\xff\xd8\xff\xe0" + b"flood-scene" * 8


def valid_form(report_id: str) -> dict[str, str]:
    return {
        "report_id": report_id,
        "created_at": "2026-09-21T10:00:00Z",
        "description": "Nước ngập ngang đầu gối",
        "trapped_count": "2",
        "injured_count": "1",
        "vulnerable_groups": json.dumps(["trẻ em"], ensure_ascii=False),
        "ai_label": "medium",
        "ai_confidence": "0.87",
        "latitude": "10.762622",
        "longitude": "106.660172",
    }


def create_report(client, report_id: str, image: bytes, description: str | None = None):
    form = valid_form(report_id)
    if description is not None:
        form["description"] = description
    return client.post(
        "/api/reports",
        data=form,
        files={"image": ("scene.jpg", image, "image/jpeg")},
    )


def test_create_report_with_image(client, jpeg_bytes):
    response = create_report(client, "report-001", jpeg_bytes)

    assert response.status_code == 201
    assert response.json() == {
        "id": "report-001",
        "created_at": "2026-09-21T10:00:00Z",
        "description": "Nước ngập ngang đầu gối",
        "trapped_count": 2,
        "injured_count": 1,
        "vulnerable_groups": ["trẻ em"],
        "ai_label": "medium",
        "ai_confidence": 0.87,
        "latitude": 10.762622,
        "longitude": 106.660172,
        "has_image": True,
        "image_name": "scene.jpg",
        "image_mime_type": "image/jpeg",
        "status": "synced",
    }


def test_duplicate_report_id_returns_original_without_rewriting(client, jpeg_bytes, settings):
    first = create_report(client, "same-id", jpeg_bytes, "Nội dung đầu tiên")
    stored_image = settings.upload_dir / "same-id.jpg"
    first_mtime = stored_image.stat().st_mtime_ns

    second = create_report(client, "same-id", b"\xff\xd8\xffchanged", "Nội dung mới")

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["description"] == "Nội dung đầu tiên"
    assert stored_image.read_bytes() == jpeg_bytes
    assert stored_image.stat().st_mtime_ns == first_mtime


def test_lists_and_gets_reports(client, jpeg_bytes):
    create_report(client, "report-list", jpeg_bytes)

    listed = client.get("/api/reports")
    detail = client.get("/api/reports/report-list")

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == ["report-list"]
    assert detail.status_code == 200
    assert detail.json()["id"] == "report-list"


def test_missing_report_returns_404(client):
    response = client.get("/api/reports/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "report_not_found"


def test_rejects_non_image_content_type(client):
    response = client.post(
        "/api/reports",
        data=valid_form("bad-file"),
        files={"image": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["detail"]["code"] == "unsupported_image_type"


def test_rejects_mismatched_image_signature(client):
    response = client.post(
        "/api/reports",
        data=valid_form("fake-jpeg"),
        files={"image": ("scene.jpg", b"not really jpeg", "image/jpeg")},
    )

    assert response.status_code == 415
    assert response.json()["detail"]["code"] == "invalid_image_signature"


def test_rejects_image_over_configured_limit(settings, jpeg_bytes):
    limited = settings.model_copy(update={"max_image_bytes": 16})
    limited_client = TestClient(create_app(limited))

    response = create_report(limited_client, "too-large", jpeg_bytes)

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "image_too_large"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("trapped_count", "-1"),
        ("ai_label", "unknown"),
        ("ai_confidence", "1.5"),
        ("latitude", "91"),
        ("longitude", "-181"),
    ],
)
def test_rejects_invalid_report_fields(client, field, value):
    form = valid_form(f"invalid-{field}")
    form[field] = value

    response = client.post("/api/reports", data=form)

    assert response.status_code == 422


def test_rejects_non_array_vulnerable_groups(client):
    form = valid_form("invalid-groups")
    form["vulnerable_groups"] = json.dumps({"group": "trẻ em"})

    response = client.post("/api/reports", data=form)

    assert response.status_code == 422
