from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        upload_dir=tmp_path / "uploads",
        allowed_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
        _env_file=None,
    )


@pytest.fixture
def client(settings: Settings):
    return TestClient(create_app(settings))
