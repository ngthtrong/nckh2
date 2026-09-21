from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_url: str = "sqlite:///./data/flood_rescue.db"
    upload_dir: Path = Path("./data/uploads")
    allowed_origins: list[str] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    max_image_bytes: int = 10 * 1024 * 1024

    sms_enabled: bool = False
    sms_provider: str = "twilio"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    sms_alert_recipient: str = ""
    sms_max_per_hour: int = 3
    sms_max_per_day: int = 10

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

