"""Thực nghiệm GIẢ LẬP mạng yếu cho ba chế độ gửi của app.

Mỗi hồ sơ mạng (2G/3G/4G) là một proxy TCP chạy cục bộ, giới hạn băng thông và thêm
độ trễ một chiều RTT/2 trên cả hai hướng. Client Python gửi đúng dạng request của app:

- metadata : POST /sync/messages, một message CREATE_RESCUE_RECORD (JSON, không ảnh)
- compressed: POST /api/reports, ảnh nén như flutter_image_compress (cạnh ngắn 1024 px, q60)
- original : POST /api/reports, ảnh gốc

Proxy cắt kết nối khi vượt timeout của app (Dio: sync 30 s, upload 60 s) nên request đó
được tính là thất bại, giống app sẽ bỏ cuộc và để lại trong outbox.

Đây là giả lập phía máy tính (loopback), không phải đo trên thiết bị và mạng di động thật.

Chạy (server phải đang chạy, nên dùng DB riêng):
    RESCUE_DB_FILE=data/experiment.db RESCUE_UPLOADS_DIR=uploads_experiment \
        .venv/bin/python -m uvicorn main:app --port 8001
    .venv/bin/python experiments/weak_network.py --server 127.0.0.1:8001 --runs 20 [--resume]
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import io
import json
import os
import statistics
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image

BE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE_DIR))
from canonical import compute_payload_hash  # noqa: E402

DATASET_DIR = BE_DIR.parent / "fe" / "model" / "Dataset_Flood"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

# Tham số chế độ gửi và timeout lấy từ fe/app (config.dart, *_remote_datasource.dart).
COMPRESS_QUALITY = 60
COMPRESS_MIN_SIDE = 1024
TIMEOUT_S = {"metadata": 30.0, "compressed": 60.0, "original": 60.0}


@dataclass(frozen=True)
class Profile:
    name: str
    kbps: float
    rtt_ms: float


PROFILES = (
    Profile("2G (EDGE)", kbps=50, rtt_ms=600),
    Profile("3G", kbps=400, rtt_ms=200),
    Profile("4G", kbps=5000, rtt_ms=50),
)
MODES = ("metadata", "compressed", "original")


class ThrottledProxy:
    """Proxy TCP: băng thông kbps mỗi hướng, trễ một chiều RTT/2, cắt kết nối quá hạn."""

    def __init__(self, profile: Profile, upstream: tuple[str, int]) -> None:
        self.profile = profile
        self.upstream = upstream
        self.deadline_s = 60.0
        self.last_bytes_up = 0
        self.connection_closed = threading.Event()
        self.port = 0
        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()
        self._ready.wait()

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        server = self._loop.run_until_complete(
            asyncio.start_server(self._handle, "127.0.0.1", 0)
        )
        self.port = server.sockets[0].getsockname()[1]
        self._ready.set()
        self._loop.run_forever()

    async def _pump(self, reader, writer, counter: list[int]) -> None:
        bytes_per_s = self.profile.kbps * 1000 / 8
        one_way = self.profile.rtt_ms / 2000
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        async def deliver() -> None:
            while True:
                due, chunk = await queue.get()
                if chunk is None:
                    break
                await asyncio.sleep(max(0.0, due - loop.time()))
                writer.write(chunk)
                await writer.drain()

        sender = asyncio.create_task(deliver())
        link_free_at = loop.time()
        try:
            while chunk := await reader.read(4096):
                counter[0] += len(chunk)
                start = max(loop.time(), link_free_at)
                link_free_at = start + len(chunk) / bytes_per_s
                await asyncio.sleep(max(0.0, link_free_at - loop.time()))
                await queue.put((link_free_at + one_way, chunk))
            await queue.put((0.0, None))
            await sender
        except (asyncio.CancelledError, ConnectionError):
            sender.cancel()
            raise

    async def _handle(self, client_reader, client_writer) -> None:
        up = [0]
        down = [0]
        server_writer = None
        try:
            # Bắt tay TCP tốn khoảng một RTT.
            await asyncio.sleep(self.profile.rtt_ms / 1000)
            server_reader, server_writer = await asyncio.open_connection(*self.upstream)
            await asyncio.wait_for(
                asyncio.gather(
                    self._pump(client_reader, server_writer, up),
                    self._pump(server_reader, client_writer, down),
                ),
                timeout=self.deadline_s,
            )
        except (asyncio.TimeoutError, ConnectionError):
            pass
        finally:
            self.last_bytes_up = up[0]
            for w in (client_writer, server_writer):
                if w is not None:
                    w.close()
            self.connection_closed.set()


def pick_images(count: int) -> list[Path]:
    """Chọn đều ``count`` ảnh JPEG cạnh dài >= 1600 px (gần ảnh chụp điện thoại)."""
    candidates = []
    for path in sorted(DATASET_DIR.glob("*/*")):
        try:
            with Image.open(path) as image:
                if image.format == "JPEG" and max(image.size) >= 1600:
                    candidates.append(path)
        except OSError:
            continue
    if len(candidates) < count:
        raise SystemExit(f"Chỉ có {len(candidates)} ảnh phù hợp, cần {count}")
    step = len(candidates) / count
    return [candidates[int(i * step)] for i in range(count)]


def compress_like_app(data: bytes) -> bytes:
    with Image.open(io.BytesIO(data)) as image:
        image = image.convert("RGB")
        width, height = image.size
        scale = min(1.0, max(COMPRESS_MIN_SIDE / width, COMPRESS_MIN_SIDE / height))
        if scale < 1.0:
            image = image.resize((round(width * scale), round(height * scale)), Image.BILINEAR)
        out = io.BytesIO()
        image.save(out, format="JPEG", quality=COMPRESS_QUALITY)
        return out.getvalue()


def app_payload(report_id: str) -> dict:
    # Cùng khóa với RescueRepositoryImpl._payload trong fe/app.
    return {
        "id": report_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "lat": 16.0544,
        "lng": 108.2022,
        "trappedCount": 3,
        "injuredCount": 1,
        "vulnerableGroups": ["elderly", "children"],
        "description": "Nước ngập tới mái nhà, có 3 người mắc kẹt cần cứu gấp",
        "aiTags": [{"label": "Ngập sâu (High)", "confidence": 0.93}],
        "sendMode": "text",
        "status": "processing",
    }


def send(base: str, mode: str, image_bytes: bytes | None, client_id: str, seq: int) -> int:
    report_id = f"exp-{uuid.uuid4().hex[:12]}"
    payload = app_payload(report_id)
    headers = {"X-Message-Contract-Version": "1", "Connection": "close"}
    timeout = (15, TIMEOUT_S[mode] + 5)
    if mode == "metadata":
        body = {"messages": [{
            "message_id": str(uuid.uuid4()),
            "client_id": client_id,
            "sequence_number": seq,
            "operation_type": "CREATE_RESCUE_RECORD",
            "created_at": payload["createdAt"],
            "payload_hash": compute_payload_hash(payload),
            "payload": payload,
        }]}
        response = requests.post(f"{base}/sync/messages", json=body, headers=headers, timeout=timeout)
        return response.status_code
    payload["sendMode"] = mode
    payload["imageSha256"] = "sha256:" + hashlib.sha256(image_bytes).hexdigest()
    payload["imageSizeBytes"] = len(image_bytes)
    payload["clientId"] = client_id  # như app: chủ báo cáo (docs/contact_connect.md)
    response = requests.post(
        f"{base}/api/reports",
        data={"meta": json.dumps(payload, ensure_ascii=False)},
        files={"image": (f"{report_id}.jpg", image_bytes, "image/jpeg")},
        headers=headers,
        timeout=timeout,
    )
    return response.status_code


FIELDS = [
    "profile", "kbps", "rtt_ms", "mode", "run", "image", "image_bytes", "wire_bytes_up",
    "http_status", "success", "elapsed_s", "load1", "measured_at",
]
OVERLOAD_LOAD1 = os.cpu_count() or 1


def run_pair(profile: Profile, mode: str, upstream: tuple[str, int],
             images: list[tuple[Path, bytes, bytes]], runs: list[int], csv_path: Path,
             lock: threading.Lock) -> None:
    """Một cặp mạng × chế độ, proxy riêng (như một điện thoại trên một đường truyền riêng)."""
    proxy = ThrottledProxy(profile, upstream)
    proxy.deadline_s = TIMEOUT_S[mode]
    base = f"http://127.0.0.1:{proxy.port}"
    client_id = f"exp-{uuid.uuid4().hex[:8]}"
    for seq, run in enumerate(runs, start=1):
        path, original, compressed = images[(run - 1) % len(images)]
        data = {"metadata": None, "compressed": compressed, "original": original}[mode]
        proxy.connection_closed.clear()
        started = time.perf_counter()
        try:
            status = send(base, mode, data, client_id, seq)
        except requests.RequestException:
            status = 0
        elapsed = time.perf_counter() - started
        proxy.connection_closed.wait(timeout=10)
        ok = 200 <= status < 300 and elapsed <= TIMEOUT_S[mode]
        row = {
            "profile": profile.name, "kbps": profile.kbps, "rtt_ms": profile.rtt_ms,
            "mode": mode, "run": run, "image": path.name if data else "",
            "image_bytes": len(data) if data else 0, "wire_bytes_up": proxy.last_bytes_up,
            "http_status": status, "success": ok, "elapsed_s": round(elapsed, 3),
            "load1": round(os.getloadavg()[0], 2), "measured_at": datetime.now().isoformat(timespec="seconds"),
        }
        with lock:
            new_file = not csv_path.exists()
            with open(csv_path, "a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                if new_file:
                    writer.writeheader()
                writer.writerow(row)
        print(f"[{profile.name:9}] {mode:10} #{run:02d} {'OK ' if ok else 'FAIL'} "
              f"{row['wire_bytes_up']:>9} B {elapsed:7.2f} s load {row['load1']}", flush=True)


def load_rows(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []
    with open(csv_path, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for r in rows:
        r["run"] = int(r["run"])
        r["image_bytes"] = int(r["image_bytes"])
        r["wire_bytes_up"] = int(r["wire_bytes_up"])
        r["elapsed_s"] = float(r["elapsed_s"])
        r["load1"] = float(r["load1"])
        r["success"] = r["success"] == "True"
    return rows


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
    return ordered[index]


def summarize(rows: list[dict]) -> tuple[str, int]:
    """Bảng tổng hợp; loại các lượt đo khi máy quá tải (load1 > số nhân CPU)."""
    valid = [r for r in rows if r["load1"] <= OVERLOAD_LOAD1]
    lines = [
        "| Mạng | Chế độ gửi | Dung lượng cần gửi (trung vị, B) | Thành công | Độ trễ trung vị (s) | Độ trễ p95 (s) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for profile in PROFILES:
        for mode in MODES:
            group = [r for r in valid if r["profile"] == profile.name and r["mode"] == mode]
            if not group:
                continue
            ok = [r["elapsed_s"] for r in group if r["success"]]
            # Lần thất bại chỉ gửi được một phần; dùng kích thước ảnh để không đánh giá thấp dung lượng.
            wire = statistics.median(max(r["wire_bytes_up"], r["image_bytes"]) for r in group)
            median = f"{statistics.median(ok):.2f}" if ok else "–"
            p95 = f"{percentile(ok, 0.95):.2f}" if ok else "–"
            lines.append(
                f"| {profile.name} ({profile.kbps:g} kbps, RTT {profile.rtt_ms:g} ms) | {mode} | "
                f"{wire:,.0f} | {len(ok)}/{len(group)} | {median} | {p95} |"
            )
    return "\n".join(lines), len(rows) - len(valid)


def write_report(rows: list[dict], images: list[tuple[Path, bytes, bytes]], runs: int, out: Path) -> str:
    table, excluded = summarize(rows)
    original_median = statistics.median(len(o) for _, o, _ in images)
    compressed_median = statistics.median(len(c) for _, _, c in images)
    report = (
        "# Kết quả giả lập mạng yếu\n\n"
        f"Cập nhật {datetime.now().strftime('%d/%m/%Y %H:%M')}; {runs} lượt cho mỗi cặp mạng × chế độ, "
        f"mỗi cặp chạy qua một proxy riêng. Ảnh gốc: {len(images)} ảnh JPEG cạnh dài ≥ 1600 px từ "
        f"`fe/model/Dataset_Flood` (trung vị {original_median:,.0f} B); ảnh nén theo tham số app "
        f"(cạnh ngắn {COMPRESS_MIN_SIDE} px, chất lượng {COMPRESS_QUALITY}; trung vị {compressed_median:,.0f} B). "
        "Metadata là một message `CREATE_RESCUE_RECORD` qua `/sync/messages`.\n\n"
        "Giả lập bằng proxy TCP cục bộ (băng thông đối xứng, trễ một chiều RTT/2, bắt tay 1 RTT); "
        "request vượt timeout của app (sync 30 s, upload 60 s) bị tính là thất bại. **Không phải đo "
        "trên thiết bị và mạng di động thật.** Độ trễ chỉ tính trên các lượt thành công.\n\n"
        f"Loại {excluded} lượt đo khi máy quá tải (load average 1 phút > {OVERLOAD_LOAD1}); "
        "dữ liệu thô đầy đủ trong `weak_network.csv`.\n\n"
        f"{table}\n"
    )
    (out / "weak_network.md").write_text(report, encoding="utf-8")
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--server", default="127.0.0.1:8000", help="host:port của server đang chạy")
    parser.add_argument("--runs", type=int, default=20, help="số lượt cho mỗi cặp mạng × chế độ")
    parser.add_argument("--out", type=Path, default=RESULTS_DIR)
    parser.add_argument("--resume", action="store_true",
                        help="giữ CSV hiện có, chỉ chạy các lượt còn thiếu hoặc đo khi máy quá tải")
    parser.add_argument("--summarize-only", action="store_true", help="chỉ tạo lại bảng từ CSV")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "weak_network.csv"
    images = []
    for path in pick_images(args.runs):
        original = path.read_bytes()
        images.append((path, original, compress_like_app(original)))

    if not args.summarize_only:
        host, port = args.server.split(":")
        requests.get(f"http://{args.server}/probe", timeout=5).raise_for_status()
        rows = load_rows(csv_path) if args.resume else []
        if not args.resume and csv_path.exists():
            csv_path.unlink()
        if args.resume and rows:
            # Bỏ các lượt đo khi quá tải để đo lại.
            kept = [r for r in rows if r["load1"] <= OVERLOAD_LOAD1]
            with open(csv_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows({k: r[k] for k in FIELDS} for r in kept)
            rows = kept
        done = {(r["profile"], r["mode"], r["run"]) for r in rows}
        lock = threading.Lock()
        threads = []
        for profile in PROFILES:
            for mode in MODES:
                todo = [run for run in range(1, args.runs + 1) if (profile.name, mode, run) not in done]
                if todo:
                    threads.append(threading.Thread(
                        target=run_pair,
                        args=(profile, mode, (host, int(port)), images, todo, csv_path, lock),
                    ))
        print(f"Chạy {len(threads)} cặp song song; ảnh gốc trung vị "
              f"{statistics.median(len(o) for _, o, _ in images):,.0f} B", flush=True)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    table = write_report(load_rows(csv_path), images, args.runs, args.out)
    print("\n" + table)
    print(f"\nĐã ghi {csv_path} và weak_network.md")


if __name__ == "__main__":
    main()
