from fastapi import APIRouter, HTTPException, Request

from app.domain import SmsRequest
from app.sms import SmsServiceError


router = APIRouter(tags=["sms"])


@router.post("/api/reports/{report_id}/sms")
async def send_sms(report_id: str, command: SmsRequest, request: Request):
    client_key = request.client.host if request.client is not None else "unknown"
    try:
        return await request.app.state.sms_service.send_report(
            report_id,
            command,
            client_key=client_key,
            gateway=request.app.state.sms_gateway,
        )
    except SmsServiceError as error:
        detail: dict[str, str] = {"code": error.code, "message": error.message}
        if error.message_id is not None:
            detail["message_id"] = error.message_id
        raise HTTPException(status_code=error.status_code, detail=detail) from error


@router.get("/api/sms/status/{message_id}")
def get_sms_status(message_id: str, request: Request):
    message = request.app.state.report_repository.get_sms(message_id)
    if message is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "sms_not_found", "message": "SMS message was not found."},
        )
    return message

