import asyncio
import hmac
import json
import logging
import shutil
import sys
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

from config import (
    ALLOW_WIPE, BACKUP_DIR, BACKUP_INTERVAL_MIN, BACKUP_KEEP, CLUSTER_MIN_INTERVAL_S, CLUSTER_SYNC_BUDGET_S,
    CORS_ORIGINS, DEDUP_RETENTION_DAYS, HOST, MAX_IMAGE_BYTES, PORT, PROBE_SIZE_BYTES, SMS_GATEWAY_TOKEN,
    STATIC_DIR, TEMPLATES_DIR, TILE_ATTRIBUTION, TILE_URL, UPLOADS_DIR,
)
from canonical import compute_bytes_sha256
from cluster_service import ClusterService
import accounts
import auth
import dashboard_service
import sms_intake
import storage

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("rescue_mock_server")


def run_backup() -> Path:
    """Chụp DB và đồng bộ thêm ảnh mới vào ``BACKUP_DIR/uploads`` (ảnh không bao giờ bị sửa,
    tên file chứa SHA-256, nên chỉ cần chép file chưa có). Giữ ``BACKUP_KEEP`` bản DB gần nhất;
    ảnh được giữ lại vì các bản DB cũ vẫn trỏ tới."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = storage.backup_to(BACKUP_DIR / f"rescue_reports_{stamp}.db")
    for old in sorted(BACKUP_DIR.glob("rescue_reports_*.db"))[:-BACKUP_KEEP]:
        old.unlink(missing_ok=True)
    copied = storage.mirror_uploads(BACKUP_DIR / "uploads")
    logger.info(f"[BACKUP] Đã sao lưu DB vào {dest}, thêm {copied} ảnh vào {BACKUP_DIR / 'uploads'}")
    return dest


async def _backup_loop() -> None:
    while True:
        await asyncio.sleep(BACKUP_INTERVAL_MIN * 60)
        try:
            await asyncio.to_thread(run_backup)
        except Exception as exc:  # sao lưu lỗi không được làm dừng server
            logger.error(f"[BACKUP] Lỗi sao lưu: {exc}")


async def _maintenance_loop() -> None:
    """Dọn phiên hết hạn, bản ghi chống trùng cũ và bộ đếm đăng nhập sai (mỗi giờ)."""
    while True:
        try:
            removed = await asyncio.to_thread(storage.cleanup, DEDUP_RETENTION_DAYS)
            auth.prune_failures()
            if any(removed.values()):
                logger.info(f"[MAINTENANCE] Đã dọn {removed}")
        except Exception as exc:
            logger.error(f"[MAINTENANCE] Lỗi khi dọn dữ liệu: {exc}")
        await asyncio.sleep(3600)


async def _warm_clusters() -> None:
    # Tính sẵn phân cụm để dashboard mở đầu tiên không phải chờ.
    try:
        await asyncio.to_thread(_clusters.get)
    except Exception:
        logger.exception("[CLUSTER] Lỗi khi tính sẵn phân cụm")


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_backup_loop()) if BACKUP_INTERVAL_MIN > 0 else None
    warmup = asyncio.create_task(_warm_clusters())
    maintenance = asyncio.create_task(_maintenance_loop())
    yield
    warmup.cancel()
    maintenance.cancel()
    if task:
        task.cancel()


app = FastAPI(
    title="Flood Rescue Mock Server",
    description="Server giả lập tiếp nhận báo cáo cứu hộ từ Frontend Flutter",
    version="1.1.0",
    lifespan=lifespan,
)

# Khởi tạo SQLite DB & Tables
storage.init_db()
accounts.ensure_admin()
auth.warn_if_default_password()

# CORS cho app Flutter web chạy khác origin (không cần cookie). Dashboard dùng cookie
# phiên nên phải chạy cùng origin với API (trực tiếp hoặc qua nginx của container dashboard).
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def protect_uploads(request: Request, call_next):
    # Ảnh hiện trường là dữ liệu nhạy cảm: chỉ điều phối viên đã đăng nhập mới xem được.
    if not request.url.path.startswith("/uploads/"):
        return await call_next(request)
    if not auth.session_for(request):
        return JSONResponse(status_code=401, content={"detail": {"code": "UNAUTHENTICATED"}})
    response = await call_next(request)
    # File do người dùng tải lên: không cho trình duyệt đoán kiểu hay chạy nội dung.
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'none'; img-src 'self'; sandbox"
    return response


# Phục vụ file ảnh tĩnh và tài nguyên của dashboard
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Khởi tạo template engine cho Dashboard
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Số báo cáo tối đa đưa vào phân cụm mỗi lần
# Số báo cáo tối đa mỗi trang của luồng thay đổi và mỗi lần đổi trạng thái hàng loạt
# (không còn giới hạn số báo cáo đưa vào phân cụm, thống kê hay xuất dữ liệu).
PAGE_LIMIT = 5000
_clusters = ClusterService(
    storage.get_cluster_version,
    lambda: storage.get_reports(active_only=True),
    sync_budget_s=CLUSTER_SYNC_BUDGET_S,
    min_interval_s=CLUSTER_MIN_INTERVAL_S,
)

Operator = Depends(auth.require_operator)

_ERROR_HTTP_STATUS = {
    "INVALID_PAYLOAD": status.HTTP_400_BAD_REQUEST,
    "REPORT_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "TEAM_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "OPERATOR_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "INVALID_CREDENTIALS": status.HTTP_400_BAD_REQUEST,
}


def _raise(err: storage.StatusUpdateError) -> None:
    http_status = _ERROR_HTTP_STATUS.get(err.code, status.HTTP_409_CONFLICT)
    raise HTTPException(status_code=http_status, detail={"code": err.code, "error": err.message})


# Buffer 64KB cho endpoint /probe
_PROBE_DATA = b"X" * PROBE_SIZE_BYTES
SYNC_MAX_BYTES = 256 * 1024


@app.get("/probe", summary="Đo throughput mạng (64KB payload)")
async def get_probe():
    """
    FE Flutter gọi endpoint này 1 lần duy nhất trước khi gửi báo cáo
    để tính throughput mạng (measureKbps).
    Trả về đúng 65,536 bytes (64 KB) nhị phân với HTTP 200.
    """
    logger.info(f"==> [PROBE] Đo throughput client (trả về {len(_PROBE_DATA)} bytes)")
    return Response(
        content=_PROBE_DATA,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": "inline; filename=probe.bin",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


# Định dạng ảnh nhận được (theo byte đầu file, không tin tên file/Content-Type của client).
_IMAGE_SIGNATURES = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
)


def _image_extension(content: bytes) -> Optional[str]:
    for signature, ext in _IMAGE_SIGNATURES:
        if content.startswith(signature):
            return ext
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


def _contract_error(code: str, message: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "error": message})


@app.post("/api/reports", status_code=201, summary="Tiếp nhận báo cáo cứu hộ kèm ảnh (Multipart)")
async def receive_report(
    request: Request,
    meta: str = Form(..., description="Chuỗi JSON của RescueRecord"),
    image: Optional[UploadFile] = File(None, description="Ảnh JPEG chụp hiện trường (tùy chọn)"),
    x_message_contract_version: Optional[str] = Header(None, alias="X-Message-Contract-Version"),
):
    """
    Transport chuyên biệt cho CREATE_RESCUE_RECORD có đính kèm ảnh.
    ``meta.id`` là khóa idempotency: báo cáo đã có chỉ được bổ sung trường còn trống và
    gắn ảnh nếu chưa có ảnh (ảnh đầu tiên được giữ), không bị ghi đè nội dung.
    """
    if x_message_contract_version is not None and x_message_contract_version != "1":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UNSUPPORTED_CONTRACT_VERSION")
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_IMAGE_BYTES + 512 * 1024:
        raise _contract_error("IMAGE_TOO_LARGE", f"Request vượt {MAX_IMAGE_BYTES // (1024 * 1024)} MB",
                              status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    try:
        meta_dict = json.loads(meta)
        storage.validate_report_payload(meta_dict)
    except ValueError as e:
        raise _contract_error("INVALID_PAYLOAD", f"Trường 'meta' không phải JSON hợp lệ: {e}")
    except storage.StatusUpdateError as err:
        raise _contract_error(err.code, err.message)
    rec_id = meta_dict["id"]
    logger.info(f"==> [POST /api/reports] {rec_id} | lat={meta_dict.get('lat')}, lng={meta_dict.get('lng')}")

    image_fields: Dict[str, Any] = {}
    if image is not None:
        content = await image.read()
        if len(content) > MAX_IMAGE_BYTES:
            raise _contract_error("IMAGE_TOO_LARGE", f"Ảnh vượt {MAX_IMAGE_BYTES // (1024 * 1024)} MB",
                                  status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        computed_sha = compute_bytes_sha256(content)
        expected_sha = meta_dict.get("imageSha256")
        if expected_sha and expected_sha.lower() != computed_sha.lower():
            logger.error(f"Image SHA-256 không khớp! Client: {expected_sha}, Thực tế: {computed_sha}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="IMAGE_HASH_MISMATCH")
        ext = _image_extension(content)
        if ext is None:
            raise _contract_error("UNSUPPORTED_IMAGE", "Ảnh phải là JPEG, PNG hoặc WebP",
                                  status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        existing = storage.get_report_by_id(rec_id)
        if existing and existing.get("imageUrl"):
            logger.info(f"    - {rec_id} đã có ảnh, giữ ảnh đầu tiên")
        else:
            # Tên file do server đặt (id đã kiểm tra + SHA): không ghi đè ảnh khác, không nhận đuôi lạ.
            filename, local_path, url = await asyncio.to_thread(
                storage.save_image, f"{rec_id}_{computed_sha[7:19]}.{ext}", content
            )
            image_fields = {
                "image_filename": filename, "image_local_path": local_path, "image_url": url,
                "image_sha256": computed_sha, "image_size_bytes": len(content),
            }

    saved = await asyncio.to_thread(storage.save_report, meta_dict, **image_fields)
    return {
        "status": "ok",
        "message": "Báo cáo cứu hộ đã được tiếp nhận thành công",
        "id": rec_id,
        "imageUrl": saved["imageUrl"],
        "receivedAt": saved["serverReceivedAt"],
    }


@app.post("/sync/messages", summary="Đồng bộ message store-and-forward batch (JSON)")
async def sync_messages(
    request: Request,
    x_message_contract_version: Optional[str] = Header(None, alias="X-Message-Contract-Version"),
):
    """
    Endpoint chuẩn theo docs/contact_connect.md:
    - Bắt buộc header: X-Message-Contract-Version: 1
    - Tối đa 50 messages, tổng request <= 256 KiB
    - Xử lý idempotency, payload canonical hash và deduplication
    - ``UPDATE_RESCUE_STATUS`` cần phiên đăng nhập dashboard (cookie hoặc Bearer)
    """
    if x_message_contract_version != "1":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UNSUPPORTED_CONTRACT_VERSION",
        )

    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > SYNC_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Tổng request vượt quá giới hạn 256 KiB")
    raw_body = bytearray()
    async for chunk in request.stream():
        raw_body += chunk
        if len(raw_body) > SYNC_MAX_BYTES:
            raise HTTPException(status_code=413, detail="Tổng request vượt quá giới hạn 256 KiB")

    try:
        body = json.loads(raw_body)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"JSON không hợp lệ: {e}",
        )

    messages = body.get("messages") if isinstance(body, dict) else None
    if not isinstance(messages, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trường 'messages' phải là một mảng",
        )

    if len(messages) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Số lượng message vượt quá giới hạn tối đa 50",
        )

    logger.info(f"==> [POST /sync/messages] Nhận batch {len(messages)} messages ({len(raw_body)} bytes)")
    session = await asyncio.to_thread(auth.session_for, request)
    results = await asyncio.to_thread(
        storage.process_sync_messages, messages, session["operator"] if session else None
    )
    return JSONResponse(content={"results": results})



# ---------------------------------------------------------------- SMS gateway

def _first(data: Dict[str, Any], *names: str) -> Any:
    lowered = {str(k).lower(): v for k, v in data.items()}
    return next((lowered[n.lower()] for n in names if lowered.get(n.lower()) not in (None, "")), None)


@app.post("/api/sms/inbound", summary="SMS gateway chuyển tiếp tin nhắn tới tổng đài")
async def sms_inbound(request: Request):
    """Nhận một SMS từ gateway (điện thoại Android chạy app SMS gateway, nhà mạng...).

    Xác thực bằng ``RESCUE_SMS_GATEWAY_TOKEN`` qua header ``X-Gateway-Token`` hoặc
    ``?token=``. Body JSON (``from``/``phoneNumber``, ``text``/``message``/``body``,
    ``receivedAt`` tùy chọn; chấp nhận cả dạng lồng ``{"payload": {...}}``) hoặc form
    (``From``, ``Body``). Tin ``SOS|id:...`` của app gộp vào báo cáo cùng id.
    """
    if not SMS_GATEWAY_TOKEN:
        raise _contract_error("SMS_GATEWAY_DISABLED", "Chưa cấu hình RESCUE_SMS_GATEWAY_TOKEN", 403)
    token = request.headers.get("x-gateway-token") or request.query_params.get("token") or ""
    if not hmac.compare_digest(token.encode("utf-8"), SMS_GATEWAY_TOKEN.encode("utf-8")):
        raise _contract_error("UNAUTHENTICATED", "Sai token SMS gateway", 401)
    try:
        if "json" in (request.headers.get("content-type") or ""):
            data = await request.json()
        else:
            data = dict(await request.form())
    except ValueError:
        raise _contract_error("INVALID_PAYLOAD", "Body phải là JSON hoặc form")
    if isinstance(data, dict) and isinstance(data.get("payload"), dict):
        data = data["payload"]
    if not isinstance(data, dict):
        raise _contract_error("INVALID_PAYLOAD", "Body phải là JSON object")
    try:
        report, created = await asyncio.to_thread(
            sms_intake.save_sms,
            _first(data, "from", "phoneNumber", "sender", "phone", "msisdn"),
            _first(data, "text", "message", "body", "content"),
            _first(data, "receivedAt", "timestamp", "date"),
        )
    except storage.StatusUpdateError as err:
        raise _contract_error(err.code, err.message)
    return JSONResponse(status_code=201 if created else 200,
                        content={"status": "ok", "id": report["id"], "created": created})


# ---------------------------------------------------------------- Đăng nhập dashboard

class LoginBody(BaseModel):
    username: str = Field(..., max_length=64, description="Tên đăng nhập của tài khoản điều phối viên")
    password: str = Field(..., max_length=200)


def _dashboard_config(session: Dict[str, Any]) -> Dict[str, Any]:
    admin = session.get("role") == "admin"
    return {
        # Nhắc quản trị viên đổi mật khẩu mặc định (chỉ tính cho admin: PBKDF2 tốn vài chục ms).
        "defaultAdminPassword": admin and accounts.uses_default_password(),
        "allowWipe": ALLOW_WIPE,
        "tileUrl": TILE_URL,
        "tileAttribution": TILE_ATTRIBUTION,
        "closeReasons": storage.CLOSE_REASONS,
        "backupIntervalMin": BACKUP_INTERVAL_MIN,
    }


@app.post("/api/auth/login", summary="Điều phối viên đăng nhập dashboard")
async def login(request: Request, body: LoginBody):
    session = await asyncio.to_thread(auth.login, request, body.username, body.password)
    response = JSONResponse(content={**session, "config": _dashboard_config(session)})
    response.set_cookie(
        auth.COOKIE_NAME, session["token"], max_age=int(auth.SESSION_HOURS * 3600),
        httponly=True, samesite="strict", secure=auth.COOKIE_SECURE, path="/",
    )
    return response


@app.post("/api/auth/logout", summary="Đăng xuất")
async def logout(request: Request):
    auth.logout(request)
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie(auth.COOKIE_NAME, path="/")
    return response


@app.get("/api/auth/me", summary="Phiên đăng nhập hiện tại và cấu hình dashboard")
async def me(request: Request):
    # Trả 200 cả khi chưa đăng nhập để trang không ghi lỗi 401 vào console lúc mở.
    session = await asyncio.to_thread(auth.session_for, request)
    if not session:
        return {"authenticated": False}
    config = await asyncio.to_thread(_dashboard_config, session)
    return {"authenticated": True, **session, "config": config}


class PasswordChange(BaseModel):
    currentPassword: str = Field(..., max_length=200)
    newPassword: str = Field(..., max_length=200)


@app.post("/api/auth/password", summary="Đổi mật khẩu của chính mình (đăng xuất các phiên khác)")
def change_password(request: Request, body: PasswordChange, session: Dict[str, Any] = Depends(auth.require_session)):
    try:
        accounts.change_own_password(session["operatorId"], body.currentPassword, body.newPassword,
                                     keep_token_hash=auth.token_hash(request))
    except storage.StatusUpdateError as err:
        _raise(err)
    logger.info(f"[AUTH] {session['username']} đổi mật khẩu")
    return {"status": "ok"}


# ---------------------------------------------------------------- Tài khoản (quản trị viên)

Admin = Depends(auth.require_admin)


class OperatorCreate(BaseModel):
    username: str = Field(..., max_length=32)
    displayName: str = Field(..., max_length=60)
    password: str = Field(..., max_length=200)
    role: str = "operator"


class OperatorUpdate(BaseModel):
    displayName: Optional[str] = Field(None, max_length=60)
    role: Optional[str] = None
    active: Optional[bool] = None
    password: Optional[str] = Field(None, max_length=200, description="Đặt lại mật khẩu (người dùng phải đổi khi đăng nhập)")


@app.get("/api/operators", summary="Danh sách tài khoản điều phối viên (quản trị viên)")
def get_operators(_: Dict[str, Any] = Admin):
    return {"operators": accounts.list_operators()}


@app.post("/api/operators", status_code=201, summary="Tạo tài khoản điều phối viên (quản trị viên)")
def post_operator(body: OperatorCreate, session: Dict[str, Any] = Admin):
    try:
        created = accounts.create_operator(body.model_dump())
    except storage.StatusUpdateError as err:
        _raise(err)
    logger.info(f"[AUTH] {session['username']} tạo tài khoản {created['username']} ({created['role']})")
    return created


@app.patch("/api/operators/{operator_id}", summary="Sửa, khóa hoặc đặt lại mật khẩu tài khoản (quản trị viên)")
def patch_operator(operator_id: int, body: OperatorUpdate, session: Dict[str, Any] = Admin):
    try:
        updated = accounts.update_operator(operator_id, body.model_dump(exclude_unset=True),
                                           acting_id=session["operatorId"])
    except storage.StatusUpdateError as err:
        _raise(err)
    logger.info(f"[AUTH] {session['username']} sửa tài khoản {updated['username']}: "
                f"{sorted(k for k in body.model_dump(exclude_unset=True) if k != 'password')}"
                f"{' + đặt lại mật khẩu' if body.password else ''}")
    return updated


# ---------------------------------------------------------------- Báo cáo (dashboard)

@app.get("/api/reports", summary="Danh sách báo cáo: lọc, sắp xếp, phân trang (cần đăng nhập)")
def list_reports(
    request: Request,
    _: str = Operator,
    page: int = 1,
    pageSize: Optional[int] = None,
    limit: int = 100,
    sort: str = "-firstReceivedAt",
):
    """Tham số lọc (tùy chọn): ``status`` (phân tách dấu phẩy), ``q`` (id/mô tả),
    ``since``/``until`` (ISO 8601, theo thời điểm sự kiện), ``hasLocation`` (true/false),
    ``teamId`` (số hoặc ``none``), ``sendMode``, ``label`` (nhãn AI), ``vulnerable``
    (``any`` hoặc tên nhóm), ``source`` (``app``/``sms``/``hotline``/``synthetic``), ``ids``.
    ``sort``: ``createdAt``, ``firstReceivedAt``, ``people``, ``status`` (thêm ``-`` để giảm dần).
    ``limit`` là tên cũ của ``pageSize``.
    """
    reports = dashboard_service.filter_reports(
        storage.get_reports(), dict(request.query_params)
    )
    try:
        reports = dashboard_service.sort_reports(reports, sort)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "INVALID_SORT", "error": str(exc)})
    return JSONResponse(content=dashboard_service.paginate(reports, page, pageSize or limit))


class ManualReport(BaseModel):
    description: str = Field(..., max_length=storage.DESCRIPTION_MAX_LENGTH)
    contactPhone: Optional[str] = Field(None, max_length=30)
    lat: Optional[float] = None
    lng: Optional[float] = None
    trappedCount: int = Field(0, ge=0, le=storage.PEOPLE_MAX)
    injuredCount: int = Field(0, ge=0, le=storage.PEOPLE_MAX)
    vulnerableGroups: List[str] = Field(default_factory=list, max_length=20)


@app.post("/api/reports/manual", status_code=201, summary="Điều phối viên nhập báo cáo (cuộc gọi tổng đài)")
def create_manual_report(body: ManualReport, operator: str = Operator):
    try:
        return sms_intake.create_manual_report(body.model_dump(), actor=operator)
    except storage.StatusUpdateError as err:
        _raise(err)


@app.get("/api/reports/changes", summary="Báo cáo thay đổi sau một mốc (dashboard hỏi định kỳ)")
def report_changes(since: int = 0, epoch: Optional[str] = None, _: str = Operator):
    """Lần đầu gọi ``since=0``; các lần sau gửi lại ``cursor`` và ``epoch`` đã nhận.
    Nếu ``epoch`` khác (dữ liệu đã bị xóa toàn bộ) server trả ``reset: true`` kèm toàn bộ dữ liệu.
    """
    changes = storage.get_changes_since(since, limit=PAGE_LIMIT)
    if epoch and epoch != changes["epoch"]:
        changes = storage.get_changes_since(0, limit=PAGE_LIMIT)
        changes["reset"] = True
    else:
        changes["reset"] = since == 0
    return JSONResponse(content=changes)


@app.get("/api/reports/status", summary="App lấy trạng thái điều phối của các báo cáo đã gửi")
async def report_statuses(ids: str = ""):
    """`ids` phân tách bằng dấu phẩy, tối đa 100; id server không biết không có trong kết quả.

    Khai báo trước `/api/reports/{report_id}` để "status" không bị hiểu là một id.
    """
    return JSONResponse(content={"reports": storage.get_report_statuses(ids.split(","))})


@app.get("/api/clusters", summary="Phân cụm sự kiện và xếp hạng ưu tiên (product C_ij + Louvain)")
def list_clusters(request: Request, _: str = Operator):
    """Chạy lõi thuật toán của bài báo trên các báo cáo chưa kết thúc.

    Chỉ tính lại khi có báo cáo mới/bổ sung, đổi trạng thái hoặc vị trí; hỗ trợ
    ``If-None-Match`` (304 khi không đổi). Khi dữ liệu lớn làm một lần tính chậm, trả kết
    quả gần nhất kèm ``stale: true`` và tính lại ở luồng nền (``computedAt`` cho biết lúc tính).
    Hàm đồng bộ (không async) để FastAPI chạy trong threadpool.
    """
    snapshot, stale = _clusters.get()
    if request.headers.get("if-none-match") == snapshot.etag:
        return Response(status_code=304, headers={"ETag": snapshot.etag})
    return JSONResponse(
        content={**snapshot.data, "computedAt": snapshot.computed_at, "stale": stale},
        headers={"ETag": snapshot.etag},
    )


class StatusUpdate(BaseModel):
    status: str
    statusVersion: int
    note: Optional[str] = None
    reason: Optional[str] = Field(None, description="Bắt buộc khi status = cancelled")
    teamId: Optional[int] = Field(None, description="Giao đội khi điều phối (tùy chọn)")


def _check_reason(new_status: str, reason: Optional[str]) -> None:
    if new_status == "cancelled" and not reason:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_PAYLOAD", "error": "Đóng báo cáo phải chọn lý do",
        })


@app.patch("/api/reports/{report_id}/status", summary="Điều phối viên cập nhật trạng thái cứu hộ")
async def patch_report_status(report_id: str, body: StatusUpdate, operator: str = Operator):
    _check_reason(body.status, body.reason)
    try:
        result = storage.update_report_status(
            report_id, body.status, body.statusVersion,
            actor=operator, note=body.note, reason=body.reason, team_id=body.teamId,
        )
    except storage.StatusUpdateError as err:
        _raise(err)
    return JSONResponse(content=result)


class BulkItem(BaseModel):
    id: str
    statusVersion: int


class BulkStatusUpdate(BaseModel):
    items: List[BulkItem] = Field(..., max_length=PAGE_LIMIT)
    status: str
    note: Optional[str] = None
    reason: Optional[str] = None
    teamId: Optional[int] = None


@app.post("/api/reports/bulk-status", summary="Đổi trạng thái nhiều báo cáo (đúng danh sách đã xác nhận)")
async def bulk_status(body: BulkStatusUpdate, operator: str = Operator):
    """Mỗi báo cáo xử lý độc lập với ``statusVersion`` dashboard đang thấy; kết quả trả
    theo từng báo cáo để hiển thị báo cáo nào thất bại và vì sao."""
    _check_reason(body.status, body.reason)
    results = storage.update_statuses_bulk(
        [item.model_dump() for item in body.items], body.status,
        actor=operator, note=body.note, reason=body.reason, team_id=body.teamId,
    )
    return JSONResponse(content={
        "ok": sum(1 for r in results if r["ok"]),
        "failed": sum(1 for r in results if not r["ok"]),
        "results": results,
    })


class TeamAssign(BaseModel):
    teamId: Optional[int] = None


@app.put("/api/reports/{report_id}/team", summary="Giao / bỏ giao đội cứu hộ cho báo cáo")
async def put_report_team(report_id: str, body: TeamAssign, operator: str = Operator):
    try:
        return JSONResponse(content=storage.assign_team(report_id, body.teamId, actor=operator))
    except storage.StatusUpdateError as err:
        _raise(err)


class NoteBody(BaseModel):
    text: str


@app.post("/api/reports/{report_id}/notes", summary="Thêm ghi chú nội bộ cho báo cáo")
async def post_report_note(report_id: str, body: NoteBody, operator: str = Operator):
    try:
        return JSONResponse(status_code=201, content=storage.add_note(report_id, body.text, actor=operator))
    except storage.StatusUpdateError as err:
        _raise(err)


class LocationBody(BaseModel):
    lat: float
    lng: float
    note: Optional[str] = None


@app.put("/api/reports/{report_id}/location", summary="Nhập vị trí thủ công (báo cáo thiếu GPS)")
async def put_report_location(report_id: str, body: LocationBody, operator: str = Operator):
    try:
        return JSONResponse(content=storage.set_manual_location(
            report_id, body.lat, body.lng, actor=operator, note=body.note,
        ))
    except storage.StatusUpdateError as err:
        _raise(err)


@app.get("/api/reports/{report_id}/history", summary="Nhật ký thao tác của một báo cáo")
async def get_report_history(report_id: str, _: str = Operator):
    if not storage.get_report_by_id(report_id):
        raise HTTPException(status_code=404, detail={"code": "REPORT_NOT_FOUND", "error": "Không tìm thấy báo cáo"})
    return JSONResponse(content={"events": storage.get_report_events(report_id)})


@app.get("/api/reports/{report_id}", summary="Xem chi tiết một báo cáo theo ID")
async def get_report(report_id: str, _: str = Operator):
    rep = storage.get_report_by_id(report_id)
    if not rep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy báo cáo")
    return JSONResponse(content=rep)


@app.delete("/api/reports", summary="Xóa tất cả báo cáo và lịch sử (chỉ khi RESCUE_ALLOW_WIPE=1)")
async def clear_all_reports(session: Dict[str, Any] = Admin):
    operator = session["operator"]
    if not ALLOW_WIPE:
        raise HTTPException(status_code=403, detail={
            "code": "WIPE_DISABLED", "error": "Xóa toàn bộ dữ liệu chỉ bật ở chế độ demo (RESCUE_ALLOW_WIPE=1)",
        })
    count = storage.clear_reports()
    logger.info(f"{operator} đã xóa toàn bộ {count} báo cáo.")
    return JSONResponse(content={"status": "ok", "message": f"Đã xóa {count} báo cáo"})


# ---------------------------------------------------------------- Đội cứu hộ

class TeamBody(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    members: Optional[int] = None
    note: Optional[str] = None
    active: Optional[bool] = None


@app.get("/api/teams", summary="Danh sách đội cứu hộ")
async def get_teams(_: str = Operator):
    return {"teams": storage.list_teams()}


@app.post("/api/teams", summary="Thêm đội cứu hộ")
async def post_team(body: TeamBody, operator: str = Operator):
    try:
        team = storage.create_team(body.model_dump(exclude_unset=True))
    except storage.StatusUpdateError as err:
        _raise(err)
    logger.info(f"[TEAM] {operator} thêm đội {team['name']}")
    return JSONResponse(status_code=201, content=team)


@app.patch("/api/teams/{team_id}", summary="Sửa / ngừng hoạt động đội cứu hộ")
async def patch_team(team_id: int, body: TeamBody, operator: str = Operator):
    try:
        team = storage.update_team(team_id, body.model_dump(exclude_unset=True))
    except storage.StatusUpdateError as err:
        _raise(err)
    logger.info(f"[TEAM] {operator} sửa đội {team['name']}")
    return team


# ---------------------------------------------------------------- Thống kê, xuất, sao lưu

@app.get("/api/stats", summary="Chỉ số vận hành: trạng thái, thời gian phản ứng, lưu lượng theo giờ")
def get_stats(hours: int = 24, _: str = Operator):
    return dashboard_service.compute_stats(
        storage.get_reports(),
        storage.get_all_events(("status",)),
        storage.list_teams(),
        hours=max(1, min(hours, 168)),
    )


@app.get("/api/export", summary="Xuất báo cáo (CSV hoặc GeoJSON) theo bộ lọc")
def export_reports(request: Request, format: str = "csv", sort: str = "-firstReceivedAt", _: str = Operator):
    """Nhận cùng tham số lọc như ``GET /api/reports``; kèm hạng/điểm ưu tiên cụm hiện tại."""
    if format not in ("csv", "geojson"):
        raise HTTPException(status_code=400, detail={"code": "INVALID_FORMAT", "error": "format: csv | geojson"})
    reports = dashboard_service.filter_reports(storage.get_reports(), dict(request.query_params))
    try:
        reports = dashboard_service.sort_reports(reports, sort)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "INVALID_SORT", "error": str(exc)})
    teams = {t["id"]: t["name"] for t in storage.list_teams()}
    clusters = dashboard_service.cluster_index(_clusters.get()[0].data)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    if format == "csv":
        body, media, ext = dashboard_service.to_csv(reports, teams, clusters), "text/csv; charset=utf-8", "csv"
    else:
        body, media, ext = dashboard_service.to_geojson(reports, teams, clusters), "application/geo+json", "geojson"
    return Response(content=body, media_type=media, headers={
        "Content-Disposition": f'attachment; filename="bao_cao_cuu_ho_{stamp}.{ext}"',
    })


@app.get("/api/admin/backup", summary="Tải bản sao lưu CSDL (kèm ảnh khi images=1) (quản trị viên)")
def download_backup(images: bool = False, session: Dict[str, Any] = Admin):
    """``images=0``: file SQLite nhất quán. ``images=1``: file ZIP gồm CSDL và thư mục ``uploads/``
    (giải nén vào ``be/`` để khôi phục cả ảnh hiện trường)."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="rescue_backup_"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    db_file = storage.backup_to(tmp_dir / f"rescue_reports_{stamp}.db")
    dest, media = db_file, "application/vnd.sqlite3"
    if images:
        dest, media = storage.zip_backup(db_file, tmp_dir / f"rescue_backup_{stamp}.zip"), "application/zip"
    logger.info(f"[BACKUP] {session['username']} tải bản sao lưu {dest.name}")

    def cleanup() -> None:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return FileResponse(dest, media_type=media, filename=dest.name, background=BackgroundTask(cleanup))


@app.get("/healthz", summary="Kiểm tra sống (cho Docker/giám sát): DB đọc được, thư mục ảnh tồn tại")
def healthz():
    try:
        storage.ping()
    except Exception as exc:
        logger.error(f"[HEALTH] Lỗi: {exc}")
        return JSONResponse(status_code=503, content={"status": "error", "error": str(exc)})
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse, summary="Web Dashboard điều phối")
async def dashboard(request: Request):
    # Trang tĩnh; tự đăng nhập và tải dữ liệu qua /api/* (xem be/static/js/).
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})


if __name__ == "__main__":
    logger.info(f"Khởi động Flood Rescue Mock Server tại http://{HOST}:{PORT}")
    logger.info(f"Dashboard: http://localhost:{PORT}/")
    logger.info(f"Swagger: http://localhost:{PORT}/docs")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
