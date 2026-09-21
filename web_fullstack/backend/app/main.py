from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.config import Settings, get_settings
from app.database import ReportRepository
from app.report_service import ReportService
from app.routes.reports import router as reports_router


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_settings.upload_dir.mkdir(parents=True, exist_ok=True)

    application = FastAPI(title="Flood Rescue Web API")
    application.state.settings = resolved_settings
    repository = ReportRepository(resolved_settings.database_url)
    repository.initialize()
    application.state.report_repository = repository
    application.state.report_service = ReportService(
        repository,
        resolved_settings.upload_dir,
        resolved_settings.max_image_bytes,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/api/capabilities")
    def capabilities() -> dict[str, object]:
        required_sms_values = {
            "TWILIO_ACCOUNT_SID": resolved_settings.twilio_account_sid,
            "TWILIO_AUTH_TOKEN": resolved_settings.twilio_auth_token,
            "TWILIO_FROM_NUMBER": resolved_settings.twilio_from_number,
            "SMS_ALERT_RECIPIENT": resolved_settings.sms_alert_recipient,
        }
        missing = [name for name, value in required_sms_values.items() if not value]
        return {
            "storage": resolved_settings.upload_dir.is_dir(),
            "sms": resolved_settings.sms_enabled and not missing,
            "sms_provider": resolved_settings.sms_provider,
            "missing_sms_settings": missing,
        }

    @application.get("/probe", response_class=Response)
    def probe() -> Response:
        return Response(content=b"\0" * (64 * 1024), media_type="application/octet-stream")

    application.include_router(reports_router)

    return application


app = create_app()
