def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sms_disabled_by_default(client):
    response = client.get("/api/capabilities")

    assert response.status_code == 200
    assert response.json() == {
        "storage": True,
        "sms": False,
        "sms_provider": "twilio",
        "missing_sms_settings": [
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "TWILIO_FROM_NUMBER",
            "SMS_ALERT_RECIPIENT",
        ],
    }


def test_configured_origin_is_allowed(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8080"


def test_unconfigured_origin_is_not_allowed(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_probe_returns_fixed_payload(client):
    response = client.get("/probe")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert len(response.content) == 64 * 1024
