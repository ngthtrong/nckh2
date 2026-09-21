import os
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from app.database import ReportRepository
from app.domain import ReportCreate, ReportRead


IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@dataclass(frozen=True)
class ReportServiceError(Exception):
    status_code: int
    code: str
    message: str


class ReportService:
    def __init__(
        self,
        repository: ReportRepository,
        upload_dir: Path,
        max_image_bytes: int,
    ) -> None:
        self.repository = repository
        self.upload_dir = upload_dir
        self.max_image_bytes = max_image_bytes

    async def create_report(
        self,
        report: ReportCreate,
        image: UploadFile | None,
    ) -> tuple[ReportRead, bool]:
        existing = await run_in_threadpool(self.repository.get_report, report.report_id)
        if existing is not None:
            return existing, False

        image_bytes: bytes | None = None
        image_path: Path | None = None
        image_name: str | None = None
        image_mime_type: str | None = None

        if image is not None:
            image_mime_type = image.content_type or ""
            extension = IMAGE_EXTENSIONS.get(image_mime_type)
            if extension is None:
                raise ReportServiceError(
                    415, "unsupported_image_type", "Only JPEG, PNG and WebP images are accepted."
                )
            image_bytes = await image.read(self.max_image_bytes + 1)
            if len(image_bytes) > self.max_image_bytes:
                raise ReportServiceError(413, "image_too_large", "Image exceeds configured size limit.")
            if not _has_valid_signature(image_bytes, image_mime_type):
                raise ReportServiceError(
                    415, "invalid_image_signature", "Image bytes do not match the declared type."
                )
            image_path = self.upload_dir / f"{report.report_id}{extension}"
            image_name = Path(image.filename or image_path.name).name

        stored, created = await run_in_threadpool(
            self.repository.create_or_get,
            report,
            image_path=str(image_path) if image_path else None,
            image_name=image_name,
            image_mime_type=image_mime_type,
        )
        if not created or image_path is None or image_bytes is None:
            return stored, created

        try:
            await run_in_threadpool(_write_atomic, image_path, image_bytes)
        except Exception:
            await run_in_threadpool(self.repository.delete, report.report_id)
            raise
        return stored, True


def _has_valid_signature(data: bytes, content_type: str) -> bool:
    if content_type == "image/jpeg":
        return data.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/webp":
        return len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    return False


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_bytes(data)
    os.replace(temporary, path)

