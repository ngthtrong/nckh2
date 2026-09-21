# Flood Rescue Web Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng backend FastAPI độc lập để nhận báo cáo cứu hộ, lưu ảnh/SQLite và gửi SMS Twilio có kiểm soát.

**Architecture:** Ứng dụng dùng application factory, repository SQLite đồng bộ chạy qua threadpool của FastAPI, storage ảnh trên filesystem và cổng `SmsGateway` có implementation Twilio. Endpoint SMS chỉ được gọi theo thao tác rõ ràng, có idempotency và hạn mức theo giờ/ngày.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic Settings, SQLite (`sqlite3`), Twilio SDK, pytest, HTTPX.

**Spec:** `web_fullstack/DESIGN.md`

## Global Constraints

- Mọi file mới thuộc `web_fullstack/`; không sửa `fe/app`.
- `.env` thật không được commit; `backend/.env.example` chỉ chứa tên biến và giá trị không bí mật.
- `SMS_ENABLED=false` mặc định; không dùng sẵn số `114` hay số khẩn cấp làm người nhận.
- Ảnh chấp nhận: JPEG, PNG hoặc WebP; tối đa 10 MiB.
- `POST /api/reports` idempotent theo report ID do client cấp.
- CORS chỉ cho các origin trong `ALLOWED_ORIGINS`.

---

### Task 1: Backend skeleton, settings and health endpoints

**Files:**
- Create: `web_fullstack/backend/pyproject.toml`
- Create: `web_fullstack/backend/.gitignore`
- Create: `web_fullstack/backend/.env.example`
- Create: `web_fullstack/backend/app/__init__.py`
- Create: `web_fullstack/backend/app/config.py`
- Create: `web_fullstack/backend/app/main.py`
- Create: `web_fullstack/backend/tests/conftest.py`
- Create: `web_fullstack/backend/tests/test_health.py`

**Interfaces:**
- Produces: `Settings`, `get_settings()`, `create_app(settings: Settings | None = None) -> FastAPI`.
- Produces: `GET /health`, `GET /api/capabilities`, `GET /probe`.

- [ ] **Step 1: Write failing health and CORS tests**

```python
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_sms_disabled_by_default(client):
    body = client.get("/api/capabilities").json()
    assert body["storage"] is True
    assert body["sms"] is False

def test_configured_origin_is_allowed(client):
    response = client.options(
        "/health",
        headers={"Origin": "http://localhost:8080", "Access-Control-Request-Method": "GET"},
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:8080"
```

- [ ] **Step 2: Run tests and verify collection/import fails**

Run: `cd web_fullstack/backend && python -m pytest tests/test_health.py -v`

Expected: FAIL because `app.config` and `app.main` do not exist.

- [ ] **Step 3: Implement settings and application factory**

`Settings` must expose exact fields `app_env`, `app_host`, `app_port`, `database_url`, `upload_dir`, `allowed_origins`, `max_image_bytes`, `sms_enabled`, `sms_provider`, `twilio_account_sid`, `twilio_auth_token`, `twilio_from_number`, `sms_alert_recipient`, `sms_max_per_hour`, and `sms_max_per_day`. `create_app` creates data directories, configures CORS from `allowed_origins`, returns 64 KiB from `/probe`, and never includes secret values in capability responses.

- [ ] **Step 4: Run focused tests**

Run: `cd web_fullstack/backend && python -m pytest tests/test_health.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add web_fullstack/backend
git commit -m "feat(web): scaffold flood rescue backend"
```

### Task 2: Report validation, image storage and idempotent persistence

**Files:**
- Create: `web_fullstack/backend/app/domain.py`
- Create: `web_fullstack/backend/app/database.py`
- Create: `web_fullstack/backend/app/report_service.py`
- Create: `web_fullstack/backend/app/routes/reports.py`
- Create: `web_fullstack/backend/app/routes/__init__.py`
- Create: `web_fullstack/backend/tests/test_reports.py`
- Modify: `web_fullstack/backend/app/main.py`

**Interfaces:**
- Produces: `ReportCreate`, `ReportRead`, `ReportStatus` (`pending`, `synced`, `failed`).
- Produces: `ReportRepository.initialize()`, `create_or_get(report, image_path)`, `list_reports()`, `get_report(report_id)`.
- Produces: `POST /api/reports`, `GET /api/reports`, `GET /api/reports/{report_id}`.

- [ ] **Step 1: Write failing API tests**

```python
def test_create_report_with_image(client, jpeg_bytes):
    response = client.post(
        "/api/reports",
        data={
            "report_id": "report-001",
            "created_at": "2026-09-21T10:00:00Z",
            "description": "Nước ngập ngang đầu gối",
            "trapped_count": "2",
            "injured_count": "1",
            "vulnerable_groups": '["trẻ em"]',
            "ai_label": "medium",
            "ai_confidence": "0.87",
            "latitude": "10.762622",
            "longitude": "106.660172",
        },
        files={"image": ("scene.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert response.status_code == 201
    assert response.json()["id"] == "report-001"
    assert response.json()["has_image"] is True

def test_duplicate_report_id_returns_existing_record(client, jpeg_bytes):
    first = create_report(client, "same-id", jpeg_bytes)
    second = create_report(client, "same-id", jpeg_bytes)
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]

def test_rejects_non_image(client):
    response = client.post("/api/reports", data=valid_form("bad-file"), files={
        "image": ("notes.txt", b"not an image", "text/plain")
    })
    assert response.status_code == 415
```

- [ ] **Step 2: Run tests and verify endpoint is missing**

Run: `cd web_fullstack/backend && python -m pytest tests/test_reports.py -v`

Expected: FAIL with 404 responses.

- [ ] **Step 3: Implement database schema and report service**

Create tables `reports` and `sms_messages` in a transaction. Store only generated safe filenames such as `<report_id>.<ext>`. Validate declared MIME and magic bytes (`FFD8FF`, PNG signature, RIFF/WEBP), stream at most `max_image_bytes + 1`, delete a just-written image if the database transaction fails, and return the existing row without rewriting files when `report_id` already exists.

- [ ] **Step 4: Implement report routes**

Accept multipart fields with explicit FastAPI `Form`/`File` declarations. Parse `vulnerable_groups` as a JSON string array. Enforce nonnegative counts, confidence in `[0, 1]`, latitude in `[-90, 90]`, longitude in `[-180, 180]`, and AI labels `low|medium|high|non_flood`. Use status 201 for a new record and 200 for an idempotent replay.

- [ ] **Step 5: Run focused tests**

Run: `cd web_fullstack/backend && python -m pytest tests/test_reports.py -v`

Expected: PASS for create, replay, list, detail, validation, size and MIME cases.

- [ ] **Step 6: Commit**

```powershell
git add web_fullstack/backend
git commit -m "feat(web): persist rescue reports and images"
```

### Task 3: SMS gateway, explicit dispatch, idempotency and rate limits

**Files:**
- Create: `web_fullstack/backend/app/sms.py`
- Create: `web_fullstack/backend/app/routes/sms.py`
- Create: `web_fullstack/backend/tests/test_sms.py`
- Modify: `web_fullstack/backend/app/database.py`
- Modify: `web_fullstack/backend/app/main.py`

**Interfaces:**
- Consumes: `ReportRepository.get_report(report_id)`.
- Produces: `SmsGateway.send(to: str, body: str) -> SmsProviderResult`.
- Produces: `SmsService.send_report(report_id, recipient, idempotency_key) -> SmsMessageRead`.
- Produces: `POST /api/reports/{report_id}/sms`, `GET /api/sms/status/{message_id}`.

- [ ] **Step 1: Write failing SMS safety tests**

```python
def test_sms_disabled_never_calls_gateway(client, fake_sms_gateway, saved_report):
    response = client.post(
        f"/api/reports/{saved_report['id']}/sms",
        json={"recipient": "+84901234567", "idempotency_key": "sms-1", "confirmed": True},
    )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "sms_not_configured"
    assert fake_sms_gateway.calls == []

def test_confirmation_is_required(sms_enabled_client, saved_report):
    response = sms_enabled_client.post(
        f"/api/reports/{saved_report['id']}/sms",
        json={"recipient": "+84901234567", "idempotency_key": "sms-2", "confirmed": False},
    )
    assert response.status_code == 400

def test_same_idempotency_key_sends_once(sms_enabled_client, fake_sms_gateway, saved_report):
    payload = {"recipient": "+84901234567", "idempotency_key": "sms-once", "confirmed": True}
    first = sms_enabled_client.post(f"/api/reports/{saved_report['id']}/sms", json=payload)
    second = sms_enabled_client.post(f"/api/reports/{saved_report['id']}/sms", json=payload)
    assert first.status_code == second.status_code == 200
    assert len(fake_sms_gateway.calls) == 1
```

- [ ] **Step 2: Run tests and verify missing SMS routes**

Run: `cd web_fullstack/backend && python -m pytest tests/test_sms.py -v`

Expected: FAIL with 404 responses.

- [ ] **Step 3: Implement gateway and message formatter**

`TwilioSmsGateway` lazily imports/constructs the Twilio client only after configuration validation. The Vietnamese body contains report ID, trapped/injured counts, AI label/confidence, coordinates when present and description truncated so the complete body is at most 480 characters. Never log account SID, auth token or full recipient.

- [ ] **Step 4: Implement protected SMS service and routes**

Reject when disabled/missing keys, when `confirmed` is false, or recipient is absent. Before provider call, count messages with status `queued|sent|delivered` within one hour/day and compare to settings. Reserve the idempotency key transactionally; a replay returns the existing record. Provider failures are stored as `failed` and are not retried automatically.

- [ ] **Step 5: Run SMS and full backend tests**

Run: `cd web_fullstack/backend && python -m pytest -v`

Expected: PASS; fake gateway proves disabled, duplicate and over-limit requests never invoke Twilio.

- [ ] **Step 6: Commit**

```powershell
git add web_fullstack/backend
git commit -m "feat(web): add guarded Twilio SMS dispatch"
```

### Task 4: Local run scripts and backend documentation

**Files:**
- Create: `web_fullstack/scripts/run_backend.ps1`
- Create: `web_fullstack/scripts/test_backend.ps1`
- Create: `web_fullstack/backend/README.md`
- Create: `web_fullstack/backend/.env.test`

**Interfaces:**
- Produces: one-command setup/run at `http://127.0.0.1:8000`.

- [ ] **Step 1: Write the smoke test script**

The test script creates `.venv` if absent, installs `.[dev]`, runs `python -m pytest -v`, and exits with pytest's status. The run script performs the same environment setup, copies `.env.example` to `.env` only when `.env` is absent, then runs `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.

- [ ] **Step 2: Document environment keys and cost boundary**

Explain that only an explicit successful call to `/sms` can invoke Twilio; report creation, image upload and AI inference do not. List exact required keys: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `SMS_ALERT_RECIPIENT`; instruct enabling with `SMS_ENABLED=true` only after adding them.

- [ ] **Step 3: Execute backend test script**

Run: `powershell -ExecutionPolicy Bypass -File web_fullstack/scripts/test_backend.ps1`

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```powershell
git add web_fullstack/backend web_fullstack/scripts
git commit -m "docs(web): add backend setup and run guide"
```

