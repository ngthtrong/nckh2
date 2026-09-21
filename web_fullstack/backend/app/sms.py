from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import uuid4

from starlette.concurrency import run_in_threadpool

from app.config import Settings
from app.database import ReportRepository
from app.domain import ReportRead, SmsMessageRead, SmsRequest, SmsStatus


@dataclass(frozen=True)
class SmsProviderResult:
    message_id: str
    status: str


class SmsGateway(Protocol):
    def send(self, to: str, body: str) -> SmsProviderResult: ...


class TwilioSmsGateway:
    def __init__(self, account_sid: str, auth_token: str, from_number: str) -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    def send(self, to: str, body: str) -> SmsProviderResult:
        from twilio.rest import Client

        message = Client(self.account_sid, self.auth_token).messages.create(
            from_=self.from_number,
            to=to,
            body=body,
        )
        return SmsProviderResult(message_id=message.sid, status=message.status or "queued")


@dataclass(frozen=True)
class SmsServiceError(Exception):
    status_code: int
    code: str
    message: str
    message_id: str | None = None


class SmsService:
    def __init__(self, repository: ReportRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    async def send_report(
        self,
        report_id: str,
        command: SmsRequest,
        *,
        client_key: str,
        gateway: SmsGateway,
    ) -> SmsMessageRead:
        missing = _missing_sms_settings(self.settings)
        if not self.settings.sms_enabled or missing:
            raise SmsServiceError(
                503,
                "sms_not_configured",
                "SMS is disabled or required provider settings are missing.",
            )
        if not command.confirmed:
            raise SmsServiceError(
                400,
                "sms_confirmation_required",
                "Explicit confirmation is required before sending SMS.",
            )

        report = await run_in_threadpool(self.repository.get_report, report_id)
        if report is None:
            raise SmsServiceError(404, "report_not_found", "Report was not found.")

        existing = await run_in_threadpool(
            self.repository.get_sms_by_idempotency_key,
            command.idempotency_key,
        )
        if existing is not None:
            return existing

        now = datetime.now(UTC)
        hour_count = await run_in_threadpool(
            self.repository.count_recent_sms,
            recipient=command.recipient,
            report_id=report_id,
            client_key=client_key,
            since=(now - timedelta(hours=1)).isoformat(),
        )
        day_count = await run_in_threadpool(
            self.repository.count_recent_sms,
            recipient=command.recipient,
            report_id=report_id,
            client_key=client_key,
            since=(now - timedelta(days=1)).isoformat(),
        )
        if hour_count >= self.settings.sms_max_per_hour or day_count >= self.settings.sms_max_per_day:
            raise SmsServiceError(
                429,
                "sms_rate_limit",
                "SMS sending limit reached. Try again later.",
            )

        message, created = await run_in_threadpool(
            self.repository.reserve_sms,
            message_id=str(uuid4()),
            report_id=report_id,
            recipient=command.recipient,
            client_key=client_key,
            idempotency_key=command.idempotency_key,
            now=now.isoformat(),
        )
        if not created:
            return message

        try:
            provider_result = await run_in_threadpool(
                gateway.send,
                command.recipient,
                _format_sms(report),
            )
        except Exception as error:
            failed = await run_in_threadpool(
                self.repository.update_sms,
                message.id,
                status=SmsStatus.failed,
                updated_at=datetime.now(UTC).isoformat(),
                error_code=type(error).__name__,
            )
            raise SmsServiceError(
                502,
                "sms_provider_failed",
                "The SMS provider rejected or could not process the request.",
                failed.id,
            ) from error

        provider_status = _provider_status(provider_result.status)
        return await run_in_threadpool(
            self.repository.update_sms,
            message.id,
            status=provider_status,
            updated_at=datetime.now(UTC).isoformat(),
            provider_message_id=provider_result.message_id,
        )


def _missing_sms_settings(settings: Settings) -> list[str]:
    values = {
        "TWILIO_ACCOUNT_SID": settings.twilio_account_sid,
        "TWILIO_AUTH_TOKEN": settings.twilio_auth_token,
        "TWILIO_FROM_NUMBER": settings.twilio_from_number,
        "SMS_ALERT_RECIPIENT": settings.sms_alert_recipient,
    }
    return [name for name, value in values.items() if not value]


def _provider_status(status: str) -> SmsStatus:
    try:
        return SmsStatus(status)
    except ValueError:
        return SmsStatus.queued


def _format_sms(report: ReportRead) -> str:
    ai = "unknown"
    if report.ai_label is not None:
        confidence = f" {report.ai_confidence:.2f}" if report.ai_confidence is not None else ""
        ai = f"{report.ai_label}{confidence}"
    gps = "unknown"
    if report.latitude is not None and report.longitude is not None:
        gps = f"{report.latitude:.6f},{report.longitude:.6f}"
    prefix = (
        f"SOS Flood Rescue | report={report.id} | trapped={report.trapped_count} | "
        f"injured={report.injured_count} | AI={ai} | GPS={gps} | desc="
    )
    available = max(0, 480 - len(prefix))
    return prefix + report.description[:available]

