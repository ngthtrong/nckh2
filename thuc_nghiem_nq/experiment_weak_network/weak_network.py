"""Runner riêng cho thực nghiệm mạng yếu trên tập validation.

Sao chép và phát triển từ products/be/experiments/weak_network.py.
Không sửa runner gốc. Không có tham số: chỉ hiện hướng dẫn, không gửi request.

    python weak_network.py --check-inputs
    python weak_network.py --run
    python weak_network.py --resume RUN_ID
    python weak_network.py --summarize-only RUN_ID

CSV mặc định: ../split_val_mobilenetv3_large.csv.
Ảnh: ../../products/fe/model/Dataset_Flood, tra bằng relative_path.
Đây là giả lập TCP trên máy tính, không đo Flutter, AI hay mạng di động thật.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import statistics
import subprocess
import sys
import threading
import time
import traceback
import uuid

# QUY ƯỚC CHÚ THÍCH SO VỚI products/be/experiments/weak_network.py:
# [BỔ SUNG]: hàm/lớp mới, chưa có trong runner gốc.
# [ĐIỀU CHỈNH]: đã có trong runner gốc, nhưng sửa giao diện hoặc cách xử lý.
# [KẾ THỪA]: giữ nhiệm vụ và logic chính của runner gốc.
# Luồng chính: main -> load_inputs -> run_experiment -> measure -> send.
# build_plan lập danh sách lượt; save_checkpoint lưu tiến độ; write_report tổng hợp.

# [ĐIỀU CHỈNH] Tính đường dẫn từ vị trí bản sao để có thể gọi từ thư mục khác.
# CSV mặc định nằm ở thuc_nghiem_nq; ảnh và backend vẫn lấy từ source hiện có.
EXPERIMENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
BE_DIR = REPO_ROOT / "products" / "be"
DEFAULT_CSV = EXPERIMENT_DIR.parent / "split_val_mobilenetv3_large.csv"
DATASET_DIR = REPO_ROOT / "products" / "fe" / "model" / "Dataset_Flood"
COMPRESS_QUALITY = 60
COMPRESS_MIN_SIDE = 1024
TIMEOUT_S = {"metadata": 30.0, "compressed": 60.0, "original": 60.0}
OVERLOAD_LOAD1 = os.cpu_count() or 1
MODES = ("metadata", "compressed", "original")
MIME_TYPES = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp", "AVIF": "image/avif"}
EXTENSIONS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp", "AVIF": ".avif"}
# [ĐIỀU CHỈNH] Giữ các cột đo của runner gốc và thêm thông tin truy vết,
# lần lặp/attempt, nguyên nhân lỗi và ACK để kiểm tra đủ lượt, phục vụ resume.
FIELDS = [
    "profile", "kbps", "rtt_ms", "mode", "run", "image", "image_bytes", "wire_bytes_up",
    "http_status", "success", "elapsed_s", "load1", "measured_at",
    "input_index", "relative_path", "label", "image_sha256", "original_format",
    "payload_format", "repeat", "attempt", "error_code", "error_detail", "backend_accepted",
]


# [KẾ THỪA] Lưu một cấu hình mạng: tên, băng thông kbps và RTT ms.
# Proxy dùng cấu hình này để giới hạn tốc độ và thêm độ trễ.
@dataclass(frozen=True)
class Profile:
    name: str
    kbps: float
    rtt_ms: float


PROFILES = (
    Profile("2G (EDGE)", 50, 600),
    Profile("3G", 400, 200),
    Profile("4G", 5000, 50),
)


# [BỔ SUNG] Gom dữ liệu của một ảnh val: đường dẫn, nhãn, byte gốc/nén và hash.
# Giữ riêng hai bản byte để gửi lại cùng một ảnh ở mọi cấu hình mạng,
# không ghi đè file ảnh nguồn khi tạo phiên bản compressed.
@dataclass(frozen=True)
class ImageInput:
    path: Path
    relative_path: str
    label: str
    original: bytes
    compressed: bytes
    original_format: str
    mime_type: str
    sha256: str


# [BỔ SUNG] Mô tả một lượt cần đo: mạng, chế độ, ảnh, lần lặp và số thứ tự.
# Đây là đầu vào của measure(), không phải kết quả của một request đã chạy.
@dataclass(frozen=True)
class Measurement:
    profile: Profile
    mode: str
    image: ImageInput
    input_index: int
    repeat: int
    run: int

    # [BỔ SUNG] Khóa ổn định để đối chiếu kế hoạch với CSV khi chạy tiếp.
    # Dùng đường dẫn tương đối, tránh nhầm các ảnh trùng tên ở lớp khác nhau.
    @property
    def key(self) -> tuple[str, str, str, int]:
        return self.profile.name, self.mode, self.image.relative_path, self.repeat


# [BỔ SUNG] Trả trạng thái HTTP, việc backend chấp nhận báo cáo và lý do lỗi.
# Tách accepted khỏi HTTP status vì HTTP 200 vẫn có thể chứa ACK từ chối.
@dataclass(frozen=True)
class SendResult:
    http_status: int
    accepted: bool
    error_code: str = ""
    error_detail: str = ""


# [ĐIỀU CHỈNH] Kế thừa proxy TCP để giả lập mạng giữa client Python và backend.
# Bổ sung xử lý lỗi khởi động/dọn tài nguyên, tính timeout cả bắt tay và
# chuyển vị trí đếm byte đến sau khi ghi vào socket đích.
class ThrottledProxy:
    """Proxy TCP của runner gốc: giới hạn kbps mỗi hướng và thêm RTT."""

    # [ĐIỀU CHỈNH] Khởi tạo proxy với backend đích và chạy event loop ở thread riêng.
    # Chờ cổng TCP sẵn sàng; báo lỗi nếu khởi động thất bại thay vì chờ vô hạn.
    def __init__(self, profile: Profile, upstream: tuple[str, int]) -> None:
        self.profile = profile
        self.upstream = upstream
        self.deadline_s = 60.0
        self.last_bytes_up = 0
        self.connection_closed = threading.Event()
        self.port = 0
        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        self._startup_error = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=10):
            raise RuntimeError("Không khởi động được proxy TCP")
        if self._startup_error is not None:
            raise RuntimeError("Không khởi động được proxy TCP") from self._startup_error

    # [ĐIỀU CHỈNH] Tạo TCP server ở một cổng loopback tự chọn và giữ loop hoạt động.
    # Báo cổng/lỗi về thread chính để client biết có thể gửi request hay chưa.
    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            self._server = self._loop.run_until_complete(
                asyncio.start_server(self._handle, "127.0.0.1", 0)
            )
            self.port = self._server.sockets[0].getsockname()[1]
        except Exception as error:
            self._startup_error = error
            self._loop.close()
            self._ready.set()
            return
        self._ready.set()
        self._loop.run_forever()
        self._loop.close()

    # [ĐIỀU CHỈNH] Chuyển dữ liệu theo một hướng của kết nối TCP.
    # Xếp lịch từng khối byte theo băng thông và trễ RTT/2, để request bị chậm
    # theo profile ngay cả khi client và backend cùng chạy trên máy này.
    async def _pump(self, reader, writer, counter: list[int]) -> None:
        bytes_per_s = self.profile.kbps * 1000 / 8
        one_way = self.profile.rtt_ms / 2000
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        # [ĐIỀU CHỈNH] Gửi các khối đã xếp lịch khi tới thời điểm cho phép.
        # Chỉ tăng counter sau khi ghi/drain vào socket, không đếm ngay lúc đọc.
        async def deliver() -> None:
            while True:
                due, chunk = await queue.get()
                if chunk is None:
                    return
                await asyncio.sleep(max(0.0, due - loop.time()))
                writer.write(chunk)
                await writer.drain()
                counter[0] += len(chunk)

        sender = asyncio.create_task(deliver())
        link_free_at = loop.time()
        try:
            while chunk := await reader.read(4096):
                start = max(loop.time(), link_free_at)
                link_free_at = start + len(chunk) / bytes_per_s
                await asyncio.sleep(max(0.0, link_free_at - loop.time()))
                await queue.put((link_free_at + one_way, chunk))
            await queue.put((0.0, None))
            await sender
        finally:
            sender.cancel()
            await asyncio.gather(sender, return_exceptions=True)

    # [ĐIỀU CHỈNH] Xử lý một kết nối client: nối backend, truyền hai chiều,
    # áp dụng thời hạn của chế độ gửi, đóng kết nối và chốt số byte upload.
    async def _handle(self, client_reader, client_writer) -> None:
        up, down = [0], [0]
        server_writer = None

        # [BỔ SUNG] Gộp thời gian bắt tay và truyền hai chiều vào một coroutine,
        # để wait_for áp dụng timeout cho toàn bộ kết nối giả lập.
        async def relay() -> None:
            nonlocal server_writer
            await asyncio.sleep(self.profile.rtt_ms / 1000)
            server_reader, server_writer = await asyncio.open_connection(*self.upstream)
            await asyncio.gather(
                self._pump(client_reader, server_writer, up),
                self._pump(server_reader, client_writer, down),
            )

        try:
            # Timeout bao gồm cả bắt tay, không cộng thêm RTT ngoài thời hạn.
            await asyncio.wait_for(relay(), timeout=self.deadline_s)
        except (asyncio.TimeoutError, OSError):
            pass
        finally:
            self.last_bytes_up = up[0]
            for writer in (client_writer, server_writer):
                if writer is not None:
                    writer.close()
            self.connection_closed.set()

    # [BỔ SUNG] Dừng proxy và thread khi đổi cặp mạng/chế độ hoặc kết thúc chạy.
    # Tránh để server và tác vụ nền của cặp trước còn tồn tại ở cặp tiếp theo.
    def close(self) -> None:
        # [BỔ SUNG] Ngừng nhận kết nối, hủy và chờ các tác vụ trong loop kết thúc.
        async def shutdown() -> None:
            self._server.close()
            await self._server.wait_closed()
            pending = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

        try:
            asyncio.run_coroutine_threadsafe(shutdown(), self._loop).result(timeout=10)
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=10)


# [KẾ THỪA] Tạo byte JPEG quality 60 bằng cách nén của runner gốc.
# Giảm kích thước theo cạnh ngắn 1024 px khi cần, không phóng to ảnh nhỏ.
# Chỉ xử lý trong bộ nhớ; không sửa byte gốc hoặc ghi đè file ảnh nguồn.
def compress_like_app(data: bytes) -> bytes:
    from PIL import Image

    with Image.open(io.BytesIO(data)) as source:
        image = source.convert("RGB")
        width, height = image.size
        scale = min(1.0, max(COMPRESS_MIN_SIDE / width, COMPRESS_MIN_SIDE / height))
        if scale < 1.0:
            image = image.resize((round(width * scale), round(height * scale)), Image.BILINEAR)
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=COMPRESS_QUALITY)
        return output.getvalue()


# [BỔ SUNG] Thay cách chọn JPEG lớn của pick_images() trong runner gốc.
# Đọc toàn bộ dòng val theo thứ tự CSV, kiểm tra đường dẫn/trùng ảnh/MD5,
# nhận diện định dạng thực tế và chuẩn bị byte gốc + nén cho mỗi ảnh.
# Mục đích: đo đúng tập validation đã chọn, không tự lọc bỏ ảnh nhỏ hoặc ảnh AVIF.
def load_inputs(csv_path: Path, dataset_root: Path) -> list[ImageInput]:
    """Đọc đúng toàn bộ dòng val; không sửa CSV hoặc ảnh nguồn."""
    from PIL import Image

    root = dataset_root.resolve()
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if not {"relative_path", "label", "split"}.issubset(reader.fieldnames or []):
            raise ValueError("CSV phải có relative_path, label và split")
        rows = list(reader)
    if not rows:
        raise ValueError("CSV không có ảnh validation")
    images, seen = [], set()
    for index, row in enumerate(rows, start=1):
        if row.get("split") != "val":
            raise ValueError(f"Dòng dữ liệu {index} không thuộc tập val")
        # Cột path trỏ tới Colab; dùng relative_path để tìm ảnh trên máy đang chạy.
        relative = row.get("relative_path", "")
        pure = PurePosixPath(relative.replace("\\", "/"))
        if not relative or pure.is_absolute() or ".." in pure.parts or ":" in relative:
            raise ValueError(f"Đường dẫn không hợp lệ ở dòng {index}: {relative!r}")
        path = root.joinpath(*pure.parts).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"Không tìm thấy ảnh trong dataset: {relative}")
        identity = path.as_posix().casefold()
        if identity in seen:
            raise ValueError(f"Ảnh bị lặp trong CSV: {relative}")
        seen.add(identity)
        original = path.read_bytes()
        expected_md5 = row.get("md5", "")
        if expected_md5 and hashlib.md5(original).hexdigest().lower() != expected_md5.lower():
            raise ValueError(f"Ảnh không khớp MD5 trong CSV: {relative}")
        try:
            with Image.open(io.BytesIO(original)) as image:
                image_format = image.format
                image.load()
            if image_format not in MIME_TYPES:
                raise ValueError(f"Định dạng chưa được hỗ trợ: {image_format}")
            compressed = compress_like_app(original)
        except (OSError, ValueError) as error:
            raise ValueError(f"Không đọc/nén được {relative}: {error}") from error
        images.append(ImageInput(
            path, relative, row["label"], original, compressed, image_format,
            MIME_TYPES[image_format], hashlib.sha256(original).hexdigest(),
        ))
    return images


# [BỔ SUNG] Lập đầy đủ tổ hợp mạng × chế độ × lần lặp × ảnh.
# Với 257 ảnh và repeats=1, trả 2.313 lượt; thứ tự ảnh theo CSV trong từng cặp.
# Chỉ lập kế hoạch trong bộ nhớ, chưa mở proxy hoặc gửi request.
def build_plan(images: list[ImageInput], repeats: int) -> list[Measurement]:
    if repeats < 1:
        raise ValueError("--repeats phải >= 1")
    return [
        Measurement(profile, mode, image, index, repeat, (repeat - 1) * len(images) + index)
        for profile in PROFILES for mode in MODES
        for repeat in range(1, repeats + 1) for index, image in enumerate(images, start=1)
    ]


# [KẾ THỪA] Tạo metadata báo cáo mẫu theo giao thức app, giữ nội dung runner gốc.
# ID/thời gian được tạo cho từng báo cáo; GPS/mô tả/aiTags là dữ liệu cố định
# để đo giao thức truyền, không phải dự đoán AI từ ảnh val.
def app_payload(report_id: str) -> dict:
    # Nhãn CSV chỉ phục vụ truy vết, không chạy AI; giữ metadata của runner gốc.
    return {
        "id": report_id, "createdAt": datetime.now(timezone.utc).isoformat(),
        "lat": 16.0544, "lng": 108.2022, "trappedCount": 3, "injuredCount": 1,
        "vulnerableGroups": ["elderly", "children"],
        "description": "Nước ngập tới mái nhà, có 3 người mắc kẹt cần cứu gấp",
        "aiTags": [{"label": "Ngập sâu (High)", "confidence": 0.93}],
        "sendMode": "text", "status": "processing",
    }


# [BỔ SUNG] Đọc phản hồi backend và xác định có thật sự chấp nhận báo cáo không.
# Metadata phải có ACK đúng message_id với accepted/duplicate; upload cần status=ok.
# Trả riêng mã lỗi như UNSUPPORTED_IMAGE, để không nhầm lỗi định dạng với lỗi mạng.
def interpret_response(http_status: int, body, mode: str, message_id: str | None = None) -> SendResult:
    body = body if isinstance(body, dict) else {}
    if not 200 <= http_status < 300:
        detail = body.get("detail", {})
        code = detail.get("code") if isinstance(detail, dict) else None
        message = detail.get("error", "") if isinstance(detail, dict) else str(detail)
        return SendResult(http_status, False, code or f"HTTP_{http_status}", message)
    if mode == "metadata":
        results = body.get("results", [])
        matches = [item for item in results if isinstance(item, dict) and item.get("message_id") == message_id] \
            if isinstance(results, list) else []
        if len(matches) != 1:
            return SendResult(http_status, False, "INVALID_ACK", "Không có ACK đúng message_id")
        ack = matches[0]
        if ack.get("status") in ("accepted", "duplicate"):
            return SendResult(http_status, True)
        return SendResult(http_status, False, ack.get("code") or "MESSAGE_REJECTED", str(ack.get("result") or ""))
    if body.get("status") == "ok" and body.get("id"):
        return SendResult(http_status, True)
    return SendResult(http_status, False, "INVALID_ACK", "Backend không xác nhận đã nhận báo cáo")


# [ĐIỀU CHỈNH] Giữ hai endpoint của runner gốc nhưng nhận cả lượt đo Measurement.
# Metadata gửi JSON có canonical hash; compressed/original gửi multipart kèm ảnh.
# Bổ sung MIME/đuôi file theo định dạng thực, giữ byte original và kiểm tra ACK/ID.
# Hàm này gửi request; measure() chịu trách nhiệm đo thời gian và tạo dòng kết quả.
def send(base: str, task: Measurement, client_id: str) -> SendResult:
    import requests

    if str(BE_DIR) not in sys.path:
        sys.path.insert(0, str(BE_DIR))
    from canonical import compute_payload_hash

    report_id = f"exp-{uuid.uuid4().hex[:12]}"
    payload = app_payload(report_id)
    headers = {"X-Message-Contract-Version": "1", "Connection": "close"}
    timeout = (15, TIMEOUT_S[task.mode] + 5)
    message_id = None
    if task.mode == "metadata":
        message_id = str(uuid.uuid4())
        response = requests.post(
            f"{base}/sync/messages", headers=headers, timeout=timeout,
            json={"messages": [{
                "message_id": message_id, "client_id": client_id, "sequence_number": task.run,
                "operation_type": "CREATE_RESCUE_RECORD", "created_at": payload["createdAt"],
                "payload_hash": compute_payload_hash(payload), "payload": payload,
            }]},
        )
    else:
        data = task.image.compressed if task.mode == "compressed" else task.image.original
        image_format = "JPEG" if task.mode == "compressed" else task.image.original_format
        payload.update({
            "sendMode": task.mode, "imageSha256": "sha256:" + hashlib.sha256(data).hexdigest(),
            "imageSizeBytes": len(data), "clientId": client_id,
        })
        response = requests.post(
            f"{base}/api/reports", headers=headers, timeout=timeout,
            data={"meta": json.dumps(payload, ensure_ascii=False)},
            files={"image": (report_id + EXTENSIONS[image_format], data, MIME_TYPES[image_format])},
        )
    try:
        try:
            body = response.json()
        except ValueError:
            body = None
        result = interpret_response(response.status_code, body, task.mode, message_id)
        if task.mode != "metadata" and result.accepted and body.get("id") != report_id:
            return SendResult(response.status_code, False, "INVALID_ACK", "id báo cáo trong ACK không khớp")
        return result
    finally:
        response.close()


# [BỔ SUNG] Đọc mức tải máy trung bình một phút để nhận diện lượt bị quá tải.
# Windows không hỗ trợ thì trả None (CSV để trống), không giả tải bằng 0.
def read_load_average() -> float | None:
    try:
        return round(os.getloadavg()[0], 2)
    except (AttributeError, OSError):
        return None


# [BỔ SUNG] Tách việc đo một request khỏi vòng lặp run_pair() của runner gốc.
# Gửi qua proxy, đo thời gian, kiểm tra ACK + timeout và thu số byte/tải máy/lỗi.
# Trả một dòng CSV có đủ ảnh, nhãn, repeat và attempt để truy vết hoặc resume;
# hàm không tự ghi CSV, việc ghi thuộc run_experiment().
def measure(task: Measurement, proxy: ThrottledProxy, client_id: str, attempt: int) -> dict:
    import requests

    proxy.connection_closed.clear()
    proxy.last_bytes_up = 0
    started = time.perf_counter()
    try:
        result = send(f"http://127.0.0.1:{proxy.port}", task, client_id)
    except requests.Timeout as error:
        result = SendResult(0, False, "TIMEOUT", str(error))
    except requests.RequestException as error:
        result = SendResult(0, False, "NETWORK_ERROR", str(error))
    elapsed = time.perf_counter() - started
    if not proxy.connection_closed.wait(timeout=10):
        raise RuntimeError("Proxy chưa đóng lượt trước; dừng để tránh trộn số byte giữa hai lượt")
    ok = result.accepted and elapsed <= TIMEOUT_S[task.mode]
    data = None if task.mode == "metadata" else (
        task.image.compressed if task.mode == "compressed" else task.image.original
    )
    return {
        "profile": task.profile.name, "kbps": task.profile.kbps, "rtt_ms": task.profile.rtt_ms,
        "mode": task.mode, "run": task.run, "image": task.image.path.name,
        "image_bytes": len(data) if data is not None else 0,
        "wire_bytes_up": proxy.last_bytes_up, "http_status": result.http_status, "success": ok,
        "elapsed_s": round(elapsed, 3), "load1": read_load_average(),
        "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_index": task.input_index, "relative_path": task.image.relative_path,
        "label": task.image.label, "image_sha256": task.image.sha256,
        "original_format": task.image.original_format,
        "payload_format": "" if data is None else (
            "JPEG" if task.mode == "compressed" else task.image.original_format
        ),
        "repeat": task.repeat, "attempt": attempt,
        "error_code": result.error_code if not result.accepted else ("" if ok else "APP_TIMEOUT"),
        "error_detail": result.error_detail, "backend_accepted": result.accepted,
    }


# [BỔ SUNG] Lấy khóa của một dòng kết quả theo cùng quy tắc Measurement.key.
# Dùng khóa này để so sánh lượt đã đo với kế hoạch, không dựa vào số dòng đơn thuần.
def row_key(row: dict) -> tuple[str, str, str, int]:
    return row["profile"], row["mode"], row["relative_path"], row["repeat"]


# [BỔ SUNG] Chọn lượt hợp lệ cuối cùng của mỗi khóa, bỏ lượt quá tải khỏi bảng.
# Một lần gửi thất bại vẫn là lượt đo hợp lệ nếu không bị quá tải: không đo lại
# chỉ để tăng tỷ lệ thành công. Danh sách dòng thô đầu vào vẫn được giữ nguyên.
def effective_rows(rows: list[dict], load_limit: float = OVERLOAD_LOAD1) -> dict:
    """CSV là nguồn chính để resume; giữ nguyên cả lượt quá tải trong dữ liệu thô."""
    selected = {}
    for row in rows:
        if row["load1"] is None or row["load1"] <= load_limit:
            selected[row_key(row)] = row
    return selected


# [ĐIỀU CHỈNH] Đọc CSV kết quả và chuyển các cột số/bool về đúng kiểu dữ liệu.
# Bổ sung kiểm tra header, dòng ghi dở và attempt trùng để resume không ghép sai.
# Chỉ đọc/chuyển kiểu trong bộ nhớ, không tự sửa hoặc xóa dòng trong file kết quả.
def load_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != FIELDS:
            raise ValueError("Header kết quả không thuộc runner này; không được resume file cũ")
        rows = list(reader)
    seen = set()
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("CSV kết quả có dòng ghi dở; giữ bản gốc và kiểm tra trước khi resume")
        for key in ("run", "image_bytes", "wire_bytes_up", "http_status", "input_index", "repeat", "attempt"):
            row[key] = int(row[key])
        row["elapsed_s"] = float(row["elapsed_s"])
        row["load1"] = float(row["load1"]) if row["load1"] else None
        for key in ("success", "backend_accepted"):
            if row[key] not in ("True", "False"):
                raise ValueError(f"Giá trị {key} không hợp lệ trong CSV kết quả")
            row[key] = row[key] == "True"
        identity = (row_key(row), row["attempt"])
        if identity in seen:
            raise ValueError("CSV có lượt/attempt bị trùng; không tự ý bỏ hoặc ghi đè")
        seen.add(identity)
    return rows


# [BỔ SUNG] Lưu JSON qua file tạm rồi thay thế file đích sau khi ghi xong.
# Dùng cho manifest/checkpoint để giảm nguy cơ file chính bị ghi dở khi gián đoạn.
def atomic_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


# [BỔ SUNG] Tạo bản mô tả cấu hình và checksum CSV, runner, backend, ảnh gốc/nén.
# Lưu trong manifest; khi resume, đối chiếu bản này để bảo đảm dữ liệu và cách
# tạo request/payload vẫn khớp lần chạy trước, tránh trộn hai cấu hình thực nghiệm.
def configuration(csv_path: Path, images: list[ImageInput], repeats: int, server: str) -> dict:
    return {
        "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "backend_sources": {
            name: hashlib.sha256((BE_DIR / name).read_bytes()).hexdigest()
            for name in ("canonical.py", "main.py", "storage.py")
        },
        "server": server, "profiles": [asdict(profile) for profile in PROFILES],
        "modes": list(MODES), "repeats": repeats, "timeouts_s": TIMEOUT_S,
        "compress_quality": COMPRESS_QUALITY, "compress_min_side": COMPRESS_MIN_SIDE,
        "load1_limit": OVERLOAD_LOAD1,
        "images": [{
            "relative_path": image.relative_path, "label": image.label,
            "sha256": image.sha256, "format": image.original_format,
            "original_bytes": len(image.original), "compressed_bytes": len(image.compressed),
            "compressed_sha256": hashlib.sha256(image.compressed).hexdigest(),
        } for image in images],
    }


# [BỔ SUNG] So sánh cấu hình đã lưu với cấu hình hiện tại trước khi chạy tiếp.
# Nếu có thay đổi thì dừng và yêu cầu RUN_ID mới, bảo vệ tính nhất quán của kết quả.
def validate_resume(saved: dict, current: dict) -> None:
    if saved != current:
        raise ValueError(
            "CSV, ảnh, source, server hoặc cấu hình đã thay đổi. "
            "Không ghép dữ liệu khác cấu hình; tạo RUN_ID mới."
        )


# [KẾ THỪA] Sắp xếp các giá trị và lấy phần tử ở vị trí phân vị q như runner gốc.
# write_report() gọi với q=0.95 để thống kê p95 của thời gian gửi thành công.
def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
    return ordered[index]


# [ĐIỀU CHỈNH] Tổng hợp CSV thành weak_network.md theo mạng/chế độ, thay cả phần
# summarize() của runner gốc: tỷ lệ thành công, dung lượng, median/p95 và lỗi.
# Dùng ngưỡng tải/cấu hình đã lưu; ghi đủ/thiếu lượt và tách lỗi định dạng.
# Chỉ tính độ trễ trên lượt thành công; không thay đổi CSV đo thô.
def write_report(rows: list[dict], manifest: dict, out: Path) -> None:
    config = manifest["configuration"]
    selected = effective_rows(rows, config["load1_limit"])
    valid = list(selected.values())
    expected = manifest["expected_measurements"]
    overload_count = sum(row["load1"] is not None and row["load1"] > config["load1_limit"] for row in rows)
    lines = [
        "# Kết quả giả lập mạng yếu", "",
        f"RUN_ID: {manifest['run_id']}. Đã có {len(valid)}/{expected} lượt hợp lệ duy nhất; "
        f"{len(rows)} dòng đo thô. " + ("**Đủ lượt.**" if len(valid) == expected else "**Chưa đủ lượt.**"),
        "",
        f"Đầu vào: {len(config['images'])} ảnh val × {len(config['profiles'])} mạng × "
        f"{len(config['modes'])} chế độ × {config['repeats']} lượt/ảnh. Chạy tuần tự.",
        f"CSV đầu vào SHA256: {config['csv_sha256']}.", "",
        "Metadata cố định như runner gốc; nhãn CSV chỉ dùng truy vết, không chạy MobileNetV3. "
        "Ảnh original giữ nguyên byte; compressed là JPEG quality 60, giảm cạnh ngắn về 1024 px "
        "khi ảnh đủ lớn, không phóng to ảnh nhỏ. Ảnh nhỏ có thể lớn hơn sau khi nén lại.",
        "",
        "Các mức 2G/3G/4G là cấu hình do nhóm đặt, không phải phép đo mạng di động thật. "
        "Timeout metadata 30 s, upload 60 s. Độ trễ dưới đây chỉ tính lượt thành công.",
        "wire_bytes_up là byte proxy chuyển vào socket backend (có header HTTP), "
        "không bao gồm overhead TCP/IP và không thay thế kích thước toàn bộ payload khi timeout.",
        "",
        f"Có {overload_count} dòng quá tải không đưa vào bảng; vẫn giữ trong CSV. "
        "Resume chạy phần chưa có lượt hợp lệ, không chạy lại thất bại mạng hợp lệ.",
        f"{sum(row['load1'] is None for row in rows)} dòng không có load average "
        "(ví dụ trên Windows); để trống, không giả thành 0 và không áp dụng bộ lọc tải cho các dòng đó.",
        "",
        "| Mạng | Chế độ | Thành công / lượt | Thành công (%) | Ảnh gửi trung vị (B) | "
        "Byte proxy trung vị (B) | Median thành công (s) | p95 thành công (s) | Lỗi định dạng |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profile in config["profiles"]:
        for mode in config["modes"]:
            group = [row for row in valid if row["profile"] == profile["name"] and row["mode"] == mode]
            if not group:
                continue
            successes = [row["elapsed_s"] for row in group if row["success"]]
            latency = f"{statistics.median(successes):.3f}" if successes else "–"
            p95 = f"{percentile(successes, 0.95):.3f}" if successes else "–"
            format_errors = sum(row["error_code"] == "UNSUPPORTED_IMAGE" for row in group)
            lines.append(
                f"| {profile['name']} | {mode} | {len(successes)}/{len(group)} | "
                f"{100 * len(successes) / len(group):.2f} | "
                f"{statistics.median(row['image_bytes'] for row in group):.0f} | "
                f"{statistics.median(row['wire_bytes_up'] for row in group):.0f} | "
                f"{latency} | {p95} | {format_errors} |"
            )
    errors = Counter(row["error_code"] for row in valid if not row["success"])
    lines.extend(["", "## Nguyên nhân thất bại", ""])
    lines.extend(f"- {code}: {count} lượt." for code, count in sorted(errors.items()))
    if not errors:
        lines.append("Chưa có lượt thất bại trong dữ liệu hiện có.")
    lines.extend([
        "",
        "Tỷ lệ thành công tính mọi nguyên nhân. UNSUPPORTED_IMAGE/HTTP 415 là lỗi định dạng, "
        "không kết luận là lỗi mạng. Backend hiện nhận JPEG, PNG, WebP và từ chối AVIF original; "
        "vẫn thử ảnh AVIF và giữ kết quả, không tự đổi hoặc bỏ ảnh.",
        "",
    ])
    (out / "weak_network.md").write_text("\n".join(lines), encoding="utf-8")


# [BỔ SUNG] Ghi cùng một output ra màn hình và console.txt.
# run_experiment() dùng lớp này để lưu cả thông báo tiến độ và lỗi của runner.
class Tee:
    # [BỔ SUNG] Nhận luồng màn hình và file log cần ghi song song.
    def __init__(self, stream, log) -> None:
        self.stream, self.log = stream, log

    # [BỔ SUNG] Ghi nội dung ra cả hai nơi và đẩy log ra file ngay.
    def write(self, text):
        self.log.write(text)
        self.log.flush()
        return self.stream.write(text)

    # [BỔ SUNG] Đẩy bộ đệm của hai luồng, để output/log cập nhật kịp tiến độ.
    def flush(self):
        self.stream.flush()
        self.log.flush()


# [BỔ SUNG] Lưu commit Git và danh sách thay đổi chưa commit tại lúc bắt đầu chạy.
# Giúp truy lại source tạo ra kết quả; chỉ đọc Git, không commit hoặc sửa repository.
# Nếu Git không có sẵn, vẫn dùng checksum source/input đã ghi trong manifest.
def git_snapshot(log_dir: Path) -> str | None:
    commit = None
    git_status = "git không có sẵn; runner/backend/input đã có SHA256 trong manifest.\n"
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
        )
        if result.returncode == 0:
            commit = result.stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "status", "--short"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
        )
        git_status = status.stdout + status.stderr
    except (OSError, subprocess.TimeoutExpired):
        pass
    (log_dir / "git_status.txt").write_text(git_status, encoding="utf-8")
    return commit


# [BỔ SUNG] Điều phối một lần chạy mới hoặc chạy tiếp; thay việc main()/run_pair()
# chạy chín nhóm song song của runner gốc bằng vòng đo tuần tự.
# Khóa cấu hình, kiểm tra backend, tạo log/result, đo từng lượt, ghi CSV trước
# checkpoint và xuất báo cáo khi hoàn tất/dừng/lỗi. Trả exit code cho terminal.
# Chỉ main() với --run/--resume mới gọi hàm này; --check-inputs không gọi.
def run_experiment(args, images: list[ImageInput]) -> int:
    # Chỉ nhánh --run/--resume mới import HTTP/JCS và kiểm tra backend.
    try:
        import requests
        if str(BE_DIR) not in sys.path:
            sys.path.insert(0, str(BE_DIR))
        import canonical  # noqa: F401
    except ImportError as error:
        raise ValueError("Thiếu dependency; cài requirements.txt trong thư mục thực nghiệm") from error
    try:
        host, port_text = args.server.rsplit(":", 1)
        port = int(port_text)
        if not host or not 1 <= port <= 65535:
            raise ValueError
    except ValueError as error:
        raise ValueError("--server phải có dạng host:port hợp lệ") from error

    run_id = args.resume or args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", run_id):
        raise ValueError("RUN_ID chỉ được có chữ, số, dấu gạch ngang và gạch dưới")
    log_dir = EXPERIMENT_DIR / "logs" / run_id
    out_dir = EXPERIMENT_DIR / "results" / run_id
    checkpoint = EXPERIMENT_DIR / "checkpoints" / (run_id + ".json")
    csv_path = out_dir / "weak_network.csv"
    manifest_path = log_dir / "manifest.json"
    plan = build_plan(images, args.repeats)
    current = configuration(args.images_csv, images, args.repeats, args.server)
    if args.resume:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_resume(manifest["configuration"], current)
        rows = load_rows(csv_path)
        expected_keys = {task.key for task in plan}
        if any(row_key(row) not in expected_keys for row in rows):
            raise ValueError("CSV kết quả chứa lượt không có trong cấu hình đã khóa")
    else:
        if log_dir.exists() or out_dir.exists() or checkpoint.exists():
            raise ValueError(f"RUN_ID {run_id} đã tồn tại; dùng --resume {run_id} hoặc RUN_ID mới")
        rows = []
        manifest = {
            "run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(),
            "input_csv": str(args.images_csv.resolve()), "dataset_root": str(args.dataset_root.resolve()),
            "python": sys.version, "os": platform.platform(),
            "expected_measurements": len(plan), "configuration": current,
            "copied_from": "products/be/experiments/weak_network.py",
            "original_runner_sha256": hashlib.sha256((BE_DIR / "experiments" / "weak_network.py").read_bytes()).hexdigest(),
        }

    # Probe trực tiếp để kiểm tra backend sẵn sàng; không tính vào 2.313 lượt đo.
    requests.get(f"http://{args.server}/probe", timeout=5).raise_for_status()
    if not args.resume:
        log_dir.mkdir(parents=True)
        out_dir.mkdir(parents=True)
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        (log_dir / "input_validation.csv").write_bytes(args.images_csv.read_bytes())
        manifest["git_commit"] = git_snapshot(log_dir)
        atomic_json(manifest_path, manifest)
        with csv_path.open("x", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=FIELDS).writeheader()

    # CSV là bằng chứng chính: suy ra phần còn thiếu từ các dòng đã ghi,
    # kể cả khi checkpoint chưa kịp cập nhật lúc chương trình bị gián đoạn.
    done = effective_rows(rows)
    attempts = Counter()
    for row in rows:
        attempts[row_key(row)] = max(attempts[row_key(row)], row["attempt"])
    todo = [task for task in plan if task.key not in done]

    # [BỔ SUNG] Lưu trạng thái, số lượt hợp lệ/còn thiếu và lượt cuối sau mỗi lần đo.
    # Checkpoint báo tiến độ; khi resume vẫn đọc CSV để xác định lượt đã hoàn tất.
    def save_checkpoint(status: str) -> None:
        selected = effective_rows(rows)
        atomic_json(checkpoint, {
            "run_id": run_id, "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "csv_sha256": current["csv_sha256"], "runner_sha256": current["runner_sha256"],
            "expected_measurements": len(plan), "completed_valid_measurements": len(selected),
            "raw_measurements": len(rows), "remaining_measurements": len(plan) - len(selected),
            "results_csv": str(csv_path),
            "last_measurement": {key: rows[-1][key] for key in (
                "profile", "mode", "relative_path", "repeat", "attempt"
            )} if rows else None,
            "resume_source_of_truth": "weak_network.csv",
        })

    exit_code, status = 0, "running"
    with (log_dir / "console.txt").open("a", encoding="utf-8") as log:
        with redirect_stdout(Tee(sys.stdout, log)), redirect_stderr(Tee(sys.stderr, log)):
            print(f"RUN_ID: {run_id}\nCSV: {args.images_csv.resolve()}\nKết quả: {out_dir}")
            print(f"{len(images)} ảnh; {len(plan)} lượt dự kiến; {len(todo)} lượt còn cần đo. Chạy tuần tự.")
            save_checkpoint("running")
            proxy = None
            active_pair = None
            try:
                with csv_path.open("a", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=FIELDS)
                    # Mỗi thời điểm chỉ có một request đo; đổi proxy khi đổi cặp.
                    for task in todo:
                        pair = (task.profile.name, task.mode)
                        if pair != active_pair:
                            if proxy is not None:
                                proxy.close()
                                proxy = None
                            proxy = ThrottledProxy(task.profile, (host, port))
                            proxy.deadline_s = TIMEOUT_S[task.mode]
                            active_pair = pair
                            client_id = f"exp-{uuid.uuid4().hex[:12]}"
                        attempt = attempts[task.key] + 1
                        row = measure(task, proxy, client_id, attempt)
                        # Ghi và đồng bộ CSV trước rồi mới ghi checkpoint: nếu dừng
                        # giữa hai bước, resume vẫn thấy dòng đo đã lưu trong CSV.
                        writer.writerow(row)
                        handle.flush()
                        os.fsync(handle.fileno())
                        rows.append(row)
                        attempts[task.key] = attempt
                        print(f"[{task.profile.name}] {task.mode} {task.input_index}/{len(images)} "
                              f"repeat={task.repeat} {'OK' if row['success'] else 'FAIL'} "
                              f"{row['elapsed_s']:.3f}s {row['error_code']} {task.image.relative_path}",
                              flush=True)
                        save_checkpoint("running")
                status = "complete" if len(effective_rows(rows)) == len(plan) else "needs_resume"
                if status != "complete":
                    exit_code = 2
                    print(f"Còn lượt quá tải/chưa hợp lệ. Tiếp tục: --resume {run_id}")
            except KeyboardInterrupt:
                exit_code, status = 130, "interrupted"
                print(f"\nĐã dừng; giữ dữ liệu hiện có. Tiếp tục: --resume {run_id}")
            except Exception:
                exit_code, status = 1, "error"
                traceback.print_exc()
            finally:
                if proxy is not None:
                    try:
                        proxy.close()
                    except Exception:
                        exit_code, status = 1, "error"
                        traceback.print_exc()
                save_checkpoint(status)
                write_report(rows, manifest, out_dir)
                (log_dir / "exit_code.txt").write_text(str(exit_code) + "\n", encoding="utf-8")
            print(f"Trạng thái: {status}. Đã ghi {csv_path} và {out_dir / 'weak_network.md'}")
    return exit_code


# [ĐIỀU CHỈNH] Điểm điều khiển CLI: đọc tham số và chọn đúng thao tác.
# --check-inputs chỉ chuẩn bị/kiểm tra; --run và --resume mới gửi request;
# --summarize-only chỉ đọc kết quả đã có. Không có thao tác thì chỉ in hướng dẫn.
# Bổ sung đường dẫn CSV/dataset và repeats; trả mã lỗi thay vì âm thầm báo hoàn tất.
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--check-inputs", action="store_true", help="chỉ kiểm tra CSV/ảnh; không gửi request hoặc tạo kết quả")
    actions.add_argument("--run", action="store_true", help="bắt đầu lần thực nghiệm mới")
    actions.add_argument("--resume", metavar="RUN_ID", help="tiếp tục lần chạy; CSV kết quả quyết định phần còn thiếu")
    actions.add_argument("--summarize-only", metavar="RUN_ID", help="tổng hợp lại kết quả đã có, không gửi request")
    parser.add_argument("--images-csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--dataset-root", type=Path, default=DATASET_DIR)
    parser.add_argument("--server", default="127.0.0.1:8001")
    parser.add_argument("--repeats", type=int, default=1, help="số lần đo mỗi ảnh ở mỗi cặp mạng/chế độ")
    parser.add_argument("--run-id", help="tên lần chạy mới; mặc định YYYYMMDD-HHmmss")
    args = parser.parse_args(argv)
    if not any((args.check_inputs, args.run, args.resume, args.summarize_only)):
        parser.print_help()
        return 0
    try:
        if args.repeats < 1:
            raise ValueError("--repeats phải >= 1")
        if args.run_id and not args.run:
            raise ValueError("--run-id chỉ dùng cùng --run")
        if args.summarize_only:
            run_id = args.summarize_only
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", run_id):
                raise ValueError("RUN_ID không hợp lệ")
            manifest = json.loads((EXPERIMENT_DIR / "logs" / run_id / "manifest.json").read_text(encoding="utf-8"))
            out_dir = EXPERIMENT_DIR / "results" / run_id
            rows = load_rows(out_dir / "weak_network.csv")
            write_report(rows, manifest, out_dir)
            print(f"Đã tổng hợp {out_dir / 'weak_network.md'}; không gửi request.")
            return 0
        images = load_inputs(args.images_csv, args.dataset_root)
        if args.check_inputs:
            print(f"CSV: {args.images_csv.resolve()}\nDataset: {args.dataset_root.resolve()}")
            print(f"Đọc được {len(images)} ảnh val, đúng thứ tự CSV; không sửa dữ liệu nguồn.")
            print("Định dạng: " + json.dumps(dict(Counter(image.original_format for image in images))))
            print(f"Dự kiến {len(build_plan(images, args.repeats))} lượt đo với --repeats {args.repeats}.")
            if any(image.original_format == "AVIF" for image in images):
                print("Lưu ý: backend hiện từ chối AVIF original (HTTP 415); sẽ ghi riêng lỗi định dạng.")
            print("CHỈ KIỂM TRA ĐẦU VÀO: không gọi backend, không tạo log/kết quả/checkpoint.")
            return 0
        return run_experiment(args, images)
    except (ValueError, OSError, csv.Error, ImportError) as error:
        print(f"Lỗi: {error}", file=sys.stderr)
        return 1


# [ĐIỀU CHỈNH] Khi chạy trực tiếp, hiển thị tiếng Việt UTF-8 và trả exit code từ main.
# Import file để kiểm tra helper không tự khởi động thực nghiệm.
if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
