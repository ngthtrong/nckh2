import json
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.domain import ReportCreate
from app.report_service import ReportServiceError


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("")
async def create_report(
    request: Request,
    report_id: Annotated[str, Form()],
    created_at: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    trapped_count: Annotated[int, Form()] = 0,
    injured_count: Annotated[int, Form()] = 0,
    vulnerable_groups: Annotated[str, Form()] = "[]",
    ai_label: Annotated[str | None, Form()] = None,
    ai_confidence: Annotated[float | None, Form()] = None,
    latitude: Annotated[float | None, Form()] = None,
    longitude: Annotated[float | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
):
    try:
        groups = json.loads(vulnerable_groups)
        if not isinstance(groups, list) or not all(isinstance(item, str) for item in groups):
            raise ValueError("vulnerable_groups must be a string array")
        report = ReportCreate(
            report_id=report_id,
            created_at=created_at,
            description=description,
            trapped_count=trapped_count,
            injured_count=injured_count,
            vulnerable_groups=groups,
            ai_label=ai_label,
            ai_confidence=ai_confidence,
            latitude=latitude,
            longitude=longitude,
        )
    except (json.JSONDecodeError, ValueError, ValidationError) as error:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_report", "message": str(error)},
        ) from error

    try:
        stored, created = await request.app.state.report_service.create_report(report, image)
    except ReportServiceError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": error.code, "message": error.message},
        ) from error

    return JSONResponse(
        status_code=201 if created else 200,
        content=stored.model_dump(mode="json"),
    )


@router.get("")
def list_reports(request: Request):
    return request.app.state.report_repository.list_reports()


@router.get("/{report_id}")
def get_report(report_id: str, request: Request):
    report = request.app.state.report_repository.get_report(report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "report_not_found", "message": "Report was not found."},
        )
    return report

