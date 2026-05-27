from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Dashboard Louvain" in response.text


def test_reports_and_louvain():
    reports = client.get("/reports")
    assert reports.status_code == 200
    assert reports.json()["count"] > 0

    summary = client.get("/louvain/summary")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["nodes"] > 0
    assert payload["community_count"] > 0
