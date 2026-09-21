from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@dataclass(frozen=True)
class FakeProviderResult:
    message_id: str = "SM-test-001"
    status: str = "queued"


class FakeSmsGateway:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, str]] = []

    def send(self, to: str, body: str) -> FakeProviderResult:
        self.calls.append((to, body))
        if self.error is not None:
            raise self.error
        return FakeProviderResult()


def sms_settings(settings, **overrides):
    values = {
        "sms_enabled": True,
        "twilio_account_sid": "AC-test",
        "twilio_auth_token": "secret-test",
        "twilio_from_number": "+15005550006",
        "sms_alert_recipient": "+84901234567",
        **overrides,
    }
    return settings.model_copy(update=values)


def app_client(settings, gateway: FakeSmsGateway) -> TestClient:
    application = create_app(settings)
    application.state.sms_gateway = gateway
    return TestClient(application)


def save_report(client: TestClient, report_id: str) -> None:
    response = client.post(
        "/api/reports",
        data={
            "report_id": report_id,
            "created_at": "2026-09-21T10:00:00Z",
            "description": "Có người cần cứu hộ tại khu vực ngập sâu",
            "trapped_count": "2",
            "injured_count": "1",
            "vulnerable_groups": "[]",
            "ai_label": "high",
            "ai_confidence": "0.93",
            "latitude": "10.762622",
            "longitude": "106.660172",
        },
    )
    assert response.status_code == 201


def sms_payload(key: str, confirmed: bool = True) -> dict[str, object]:
    return {
        "recipient": "+84901234567",
        "idempotency_key": key,
        "confirmed": confirmed,
    }


def test_sms_disabled_never_calls_gateway(settings):
    gateway = FakeSmsGateway()
    client = app_client(settings, gateway)
    save_report(client, "disabled-report")

    response = client.post(
        "/api/reports/disabled-report/sms",
        json=sms_payload("sms-disabled"),
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "sms_not_configured"
    assert gateway.calls == []


def test_confirmation_is_required(settings):
    gateway = FakeSmsGateway()
    client = app_client(sms_settings(settings), gateway)
    save_report(client, "confirm-report")

    response = client.post(
        "/api/reports/confirm-report/sms",
        json=sms_payload("sms-confirm", confirmed=False),
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "sms_confirmation_required"
    assert gateway.calls == []


def test_same_idempotency_key_sends_once(settings):
    gateway = FakeSmsGateway()
    client = app_client(sms_settings(settings), gateway)
    save_report(client, "once-report")
    payload = sms_payload("sms-once")

    first = client.post("/api/reports/once-report/sms", json=payload)
    second = client.post("/api/reports/once-report/sms", json=payload)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["status"] == "queued"
    assert len(gateway.calls) == 1
    assert "once-report" in gateway.calls[0][1]
    assert "0.93" in gateway.calls[0][1]


def test_missing_report_never_calls_gateway(settings):
    gateway = FakeSmsGateway()
    client = app_client(sms_settings(settings), gateway)

    response = client.post(
        "/api/reports/missing/sms",
        json=sms_payload("sms-missing"),
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "report_not_found"
    assert gateway.calls == []


def test_hourly_rate_limit_blocks_provider_call(settings):
    gateway = FakeSmsGateway()
    client = app_client(sms_settings(settings, sms_max_per_hour=1), gateway)
    save_report(client, "rate-one")
    save_report(client, "rate-two")

    first = client.post("/api/reports/rate-one/sms", json=sms_payload("rate-key-one"))
    second = client.post("/api/reports/rate-two/sms", json=sms_payload("rate-key-two"))

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["detail"]["code"] == "sms_rate_limit"
    assert len(gateway.calls) == 1


def test_provider_failure_is_stored_without_automatic_retry(settings):
    gateway = FakeSmsGateway(RuntimeError("provider unavailable"))
    client = app_client(sms_settings(settings), gateway)
    save_report(client, "failed-report")

    response = client.post(
        "/api/reports/failed-report/sms",
        json=sms_payload("sms-failed"),
    )

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["code"] == "sms_provider_failed"
    assert "provider unavailable" not in detail["message"]
    status = client.get(f"/api/sms/status/{detail['message_id']}")
    assert status.status_code == 200
    assert status.json()["status"] == "failed"
    assert len(gateway.calls) == 1


@pytest.mark.parametrize("recipient", ["114", "0901234567", "+1", "+abc"])
def test_rejects_invalid_recipient_before_provider_call(settings, recipient):
    gateway = FakeSmsGateway()
    client = app_client(sms_settings(settings), gateway)
    save_report(client, f"recipient-{recipient.replace('+', 'plus')}")
    payload = sms_payload(f"key-{recipient}")
    payload["recipient"] = recipient

    response = client.post(
        f"/api/reports/recipient-{recipient.replace('+', 'plus')}/sms",
        json=payload,
    )

    assert response.status_code == 422
    assert gateway.calls == []
