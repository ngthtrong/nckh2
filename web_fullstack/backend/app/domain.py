from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ReportStatus(StrEnum):
    pending = "pending"
    synced = "synced"
    failed = "failed"


class ReportCreate(BaseModel):
    report_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
    created_at: str = Field(min_length=1, max_length=64)
    description: str = Field(default="", max_length=2000)
    trapped_count: int = Field(default=0, ge=0, le=10000)
    injured_count: int = Field(default=0, ge=0, le=10000)
    vulnerable_groups: list[str] = Field(default_factory=list, max_length=32)
    ai_label: Literal["low", "medium", "high", "non_flood"] | None = None
    ai_confidence: float | None = Field(default=None, ge=0, le=1)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class ReportRead(BaseModel):
    id: str
    created_at: str
    description: str
    trapped_count: int
    injured_count: int
    vulnerable_groups: list[str]
    ai_label: str | None
    ai_confidence: float | None
    latitude: float | None
    longitude: float | None
    has_image: bool
    image_name: str | None
    image_mime_type: str | None
    status: ReportStatus

