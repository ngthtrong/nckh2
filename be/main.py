import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import HOST, PORT, PROBE_SIZE_BYTES, TEMPLATES_DIR, UPLOADS_DIR
from canonical import compute_bytes_sha256
import storage

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("rescue_mock_server")

app = FastAPI(
    title="Flood Rescue Mock Server",
    description="Server giả lập tiếp nhận báo cáo cứu hộ từ Frontend Flutter",
    version="1.0.0",
)

# Khởi tạo SQLite DB & Tables
storage.init_db()

# Kích hoạt CORS cho mọi origin (cho phép Flutter Web, Emulator, LAN)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phục vụ file ảnh tĩnh
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Khởi tạo template engine cho Dashboard
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Buffer 64KB cho endpoint /probe
_PROBE_DATA = b"X" * PROBE_SIZE_BYTES


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


@app.post("/api/reports", summary="Tiếp nhận báo cáo cứu hộ kèm ảnh (Multipart)")
async def receive_report(
    meta: str = Form(..., description="Chuỗi JSON của RescueRecord"),
    image: Optional[UploadFile] = File(None, description="File ảnh JPEG chụp hiện trường (tùy chọn)"),
    x_message_contract_version: Optional[str] = Header(None, alias="X-Message-Contract-Version"),
):
    """
    Transport chuyên biệt cho CREATE_RESCUE_RECORD có đính kèm file ảnh JPEG.
    Hỗ trợ kiểm tra imageSha256 và cập nhật ảnh cho cùng meta.id.
    """
    if x_message_contract_version is not None and x_message_contract_version != "1":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UNSUPPORTED_CONTRACT_VERSION",
        )

    logger.info("=" * 60)
    logger.info("==> [POST /api/reports] TIẾP NHẬN BÁO CÁO CÓ ẢNH (MULTIPART)")

    try:
        meta_dict = json.loads(meta)
    except Exception as e:
        logger.error(f"Lỗi cú pháp JSON meta: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trường 'meta' không hợp lệ: {e}",
        )

    rec_id = str(meta_dict.get("id") or f"rec_{int(uvicorn.config.time.time() * 1000)}")
    logger.info(f"    - ID: {rec_id}")
    logger.info(f"    - Vị trí: lat={meta_dict.get('lat')}, lng={meta_dict.get('lng')}")

    # Xử lý lưu ảnh nếu có
    image_filename = None
    image_local_path = None
    image_url = None
    computed_image_sha = None
    image_size = None

    if image is not None:
        try:
            image_content = await image.read()
            image_size = len(image_content)
            computed_image_sha = compute_bytes_sha256(image_content)

            # Kiểm tra imageSha256 nếu client gửi trong meta
            expected_sha = meta_dict.get("imageSha256")
            if expected_sha and expected_sha.lower() != computed_image_sha.lower():
                logger.error(f"Image SHA-256 không khớp! Client: {expected_sha}, Thực tế: {computed_image_sha}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="IMAGE_HASH_MISMATCH",
                )

            filename = f"{rec_id}_{image.filename or 'photo.jpg'}"
            image_filename, image_local_path, image_url = storage.save_image(filename, image_content)
            logger.info(f"    - Đã lưu ảnh cục bộ: {filename} ({image_size} bytes)")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"    - Lỗi khi lưu ảnh: {e}")
    else:
        logger.info("    - Không có ảnh đính kèm (text-only)")

    saved_record = storage.save_report(
        meta=meta_dict,
        image_filename=image_filename,
        image_local_path=image_local_path,
        image_url=image_url,
        image_sha256=computed_image_sha,
        image_size_bytes=image_size,
    )
    logger.info(f"==> [THÀNH CÔNG] Đã lưu báo cáo {rec_id} vào SQLite database.")
    logger.info("=" * 60)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "status": "ok",
            "message": "Báo cáo cứu hộ đã được tiếp nhận thành công",
            "id": rec_id,
            "imageUrl": image_url,
            "imageLocalPath": image_local_path,
            "receivedAt": saved_record["serverReceivedAt"],
        },
    )


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
    """
    if x_message_contract_version != "1":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UNSUPPORTED_CONTRACT_VERSION",
        )

    raw_body = await request.body()
    if len(raw_body) > 256 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Tổng request vượt quá giới hạn 256 KiB",
        )

    try:
        body = json.loads(raw_body)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"JSON không hợp lệ: {e}",
        )

    messages = body.get("messages")
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
    results = storage.process_sync_messages(messages)
    return JSONResponse(content={"results": results})


@app.get("/api/reports", summary="Lấy danh sách tất cả các báo cáo đã nhận")
async def list_reports():
    reports = storage.get_reports()
    return JSONResponse(content={"total": len(reports), "reports": reports})


@app.get("/api/reports/{report_id}", summary="Xem chi tiết một báo cáo theo ID")
async def get_report(report_id: str):
    rep = storage.get_report_by_id(report_id)
    if not rep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy báo cáo")
    return JSONResponse(content=rep)


@app.delete("/api/reports", summary="Xóa tất cả báo cáo và lịch sử dedup")
async def clear_all_reports():
    count = storage.clear_reports()
    logger.info(f"Đã xóa toàn bộ {count} báo cáo.")
    return JSONResponse(content={"status": "ok", "message": f"Đã xóa {count} báo cáo"})


@app.get("/", response_class=HTMLResponse, summary="Web Dashboard trực quan")
async def dashboard(request: Request):
    reports = storage.get_reports()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"reports": reports},
    )


if __name__ == "__main__":
    logger.info(f"Khởi động Flood Rescue Mock Server tại http://{HOST}:{PORT}")
    logger.info(f"Dashboard: http://localhost:{PORT}/")
    logger.info(f"Swagger: http://localhost:{PORT}/docs")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
