"""E2E riêng: app Flutter web → backend → dashboard, có log và checkpoint từng kịch bản.

Đây là bản sao của products/scripts/demo/e2e/e2e_system.py. Các hàm kiểm tra E2E
được giữ về nội dung; phần [CHỈNH SỬA]/[BỔ SUNG] ghi thay đổi cho thực nghiệm.
Xem README.md trước khi chạy. Mục CHƯA CÓ được tách khỏi FAIL.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# [CHỈNH SỬA] Chỉ sửa các đường dẫn mặc định ở đây nếu đổi vị trí repo.
EXPERIMENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
GOLD_DIR = REPO_ROOT / "thucnghiem/data/gold"  # 80 run giữ nguyên tại nguồn
CSV_PATH = EXPERIMENT_DIR.parent / "split_val_mobilenetv3_large.csv"
IMAGE_ROOT = REPO_ROOT / "products/fe/model/Dataset_Flood"
COMPOSE_FILE = EXPERIMENT_DIR / "docker-compose.yml"
LOGS_DIR = EXPERIMENT_DIR / "logs"
RESULTS_DIR = EXPERIMENT_DIR / "results"
CHECKPOINTS_DIR = EXPERIMENT_DIR / "checkpoints"
DATA_DIR = EXPERIMENT_DIR / "data"
UPLOADS_DIR = EXPERIMENT_DIR / "uploads"
SUPPORT_FILES = {
    "runner_requirements": EXPERIMENT_DIR / "requirements.txt",
    "backend_requirements": EXPERIMENT_DIR / "backend_requirements.txt",
    "seed_demo": EXPERIMENT_DIR / "seed_demo.py",
    "entrypoint": EXPERIMENT_DIR / "entrypoint.sh",
    "be_dockerfile": EXPERIMENT_DIR / "docker/be.Dockerfile",
    "dashboard_dockerfile": EXPERIMENT_DIR / "docker/dashboard.Dockerfile",
    "fe_dockerfile": EXPERIMENT_DIR / "docker/fe.Dockerfile",
}

LAT, LNG = 16.0544, 108.2022  # Đà Nẵng, gần vùng dữ liệu mô phỏng EMSR848

# [BỔ SUNG] Lệnh --seed-run chọn run_001..run_080; --resume dùng cấu hình đã khóa trong manifest.
def parse_args(argv=None):
    """Đọc lệnh chạy, kiểm tra đầu vào hoặc tiếp tục một lần chạy cũ."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check-inputs", action="store_true", help="kiểm tra dữ liệu, không mở Docker")
    actions.add_argument("--run", action="store_true", help="bắt đầu lần E2E mới")
    actions.add_argument("--resume", metavar="RUN_ID", help="tiếp tục từ checkpoint")
    parser.add_argument("--seed-run", type=int, default=1, help="run gold 1..80 (chỉ cho --run/--check-inputs)")
    parser.add_argument("--image-relative-path", help="chọn một ảnh high JPG trong CSV; mặc định ảnh hợp lệ đầu tiên")
    parser.add_argument("--be-port", type=int, default=18000)
    parser.add_argument("--dashboard-port", type=int, default=18080)
    parser.add_argument("--fe-port", type=int, default=18081)
    parser.add_argument("--chrome", default=os.environ.get("CHROME_PATH"))
    parser.add_argument("--headed", action="store_true", help="mở Chromium có giao diện để quan sát")
    parser.add_argument("--username", default=os.environ.get("RESCUE_ADMIN_USERNAME", "admin"))
    parser.add_argument("--password", default=os.environ.get("RESCUE_ADMIN_PASSWORD") or os.environ.get("RESCUE_DASHBOARD_PASSWORD", "cuuho2026"))
    return parser.parse_args(argv)


args = None  # [BỔ SUNG] Thiết lập trong main, để --check-inputs không cần Playwright.
IMAGE = ""  # [CHỈNH SỬA] Ảnh chỉ lấy từ relative_path thuộc CSV validation.

results: list[tuple[str, str]] = []


def check(cond: object, label: str, *, gap: bool = False) -> bool:
    """Ghi một tiêu chí PASS, FAIL hoặc CHƯA CÓ ra log và kết quả."""
    status = "PASS" if cond else ("CHƯA CÓ" if gap else "FAIL")
    results.append((status, label))
    print(f"{status:8} {label}", flush=True)
    return bool(cond)


_token: list[str] = []


def auth_headers() -> dict:
    """API dashboard (danh sách, phân cụm, đổi trạng thái, ảnh) cần đăng nhập; đăng nhập một lần."""
    if not _token:
        req = urllib.request.Request(
            args.api + "/api/auth/login", method="POST",
            data=json.dumps({"username": args.username, "password": args.password}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            _token.append(json.load(resp)["token"])
    return {"Authorization": f"Bearer {_token[0]}"}


def api(path: str, method: str = "GET", body: dict | None = None):
    """Gọi API backend có token dashboard."""
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(args.api + path, method=method, data=data,
                                 headers={"Content-Type": "application/json", **auth_headers()})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def fetch(url: str) -> bytes:
    """Tải ảnh qua API bằng token để đối chiếu nội dung."""
    req = urllib.request.Request(url, headers=auth_headers())
    return urllib.request.urlopen(req, timeout=15).read()


def status_without_login(url: str) -> int:
    """Lấy mã HTTP khi chưa đăng nhập để kiểm tra phân quyền."""
    try:
        return urllib.request.urlopen(url, timeout=15).status
    except urllib.error.HTTPError as err:
        return err.code


def report_ids() -> set[str]:
    """Chụp danh sách ID hiện có trước một thao tác để nhận ra báo cáo mới."""
    return {r["id"] for r in api("/api/reports?limit=5000")["reports"]}


def wait_new(prefix: str, known: set[str], timeout: float = 30) -> list[dict]:
    """Đợi báo cáo SOS/post mới xuất hiện trên server."""
    end = time.time() + timeout
    while time.time() < end:
        new = [r for r in api("/api/reports?limit=5000")["reports"] if r["id"].startswith(prefix) and r["id"] not in known]
        if new:
            return new
        time.sleep(1)
    return []


def age_seconds(report: dict) -> float:
    """Đo độ lệch giữa createdAt của báo cáo và giờ UTC hiện tại."""
    created = datetime.fromisoformat(report["createdAt"].replace("Z", "+00:00"))
    if created.tzinfo is None:  # server và rescue_core hiểu giờ không múi là UTC
        created = created.replace(tzinfo=timezone.utc)
    return abs((datetime.now(timezone.utc) - created).total_seconds())


def enable_semantics(page) -> None:
    """Bật nhãn truy cập của Flutter web để Playwright tìm nút."""
    page.evaluate("document.querySelector('flt-semantics-placeholder')?.click()")
    page.wait_for_timeout(800)


def screen_text(page) -> str:
    """Lấy chữ hiển thị từ cây semantics của Flutter."""
    return page.evaluate(
        "[...document.querySelectorAll('flt-semantics [aria-label], flt-semantics [role], flt-semantics span')]"
        ".map(e => (e.getAttribute('aria-label') || e.textContent || '').trim().replace(/\\s+/g, ' ')).join(' | ')"
    )


def tap(page, name: str) -> None:
    """Bấm nút app, kể cả nút SOS đang có animation."""
    # Nút của app có animation (SOS nhấp nháy) nên bỏ qua kiểm tra "stable".
    page.get_by_role("button", name=name).first.click(force=True)


def open_app(browser, *, deny_geolocation: bool = False, **context_args):
    """Mở app trong phiên trình duyệt mới và ghi lỗi JavaScript."""
    ctx = browser.new_context(viewport={"width": 420, "height": 900}, timezone_id="Asia/Ho_Chi_Minh", **context_args)
    if deny_geolocation:
        # [CHỈNH SỬA] Giả lập từ chối ngay trong Geolocation API; Chrome headed
        # có thể vẫn để quyền ở prompt dù gửi Browser.setPermission qua page CDP.
        ctx.add_init_script("""
            Object.defineProperty(navigator, 'geolocation', {
              configurable: true,
              value: {
                getCurrentPosition(_success, onError) {
                  setTimeout(() => onError?.({code: 1, message: 'User denied Geolocation'}), 0);
                },
                watchPosition(_success, onError) {
                  setTimeout(() => onError?.({code: 1, message: 'User denied Geolocation'}), 0);
                  return 0;
                },
                clearWatch() {}
              }
            });
        """)
    page = ctx.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(f"{e.name}: {e.message[:200]}"))
    page.goto(args.app, wait_until="networkidle")
    page.wait_for_timeout(3000)
    enable_semantics(page)
    tap(page, "Bỏ qua")
    page.wait_for_timeout(2500)
    return ctx, page, errors


def submit_post(page, text: str, image: str) -> None:
    """Nhập mô tả, gắn ảnh rồi gửi bài cứu hộ qua giao diện app."""
    tap(page, "Gửi bài cứu hộ")
    page.wait_for_timeout(1500)
    page.get_by_role("textbox").last.click(force=True)
    page.keyboard.type(text)
    with page.expect_file_chooser(timeout=10000) as chooser:
        tap(page, "Chọn từ máy")
    chooser.value.set_files(image)
    page.wait_for_timeout(2500)
    tap(page, "Gửi ngay")


def wait_report(rid: str, predicate, timeout: float = 30) -> dict:
    """Đợi một báo cáo đạt điều kiện, thường là upload xong ảnh."""
    end = time.time() + timeout
    report = api(f"/api/reports/{rid}")
    while time.time() < end and not predicate(report):
        time.sleep(1)
        report = api(f"/api/reports/{rid}")
    return report


def image_size(url: str) -> int:
    """Đọc số byte ảnh server đang lưu."""
    return len(fetch(args.api + url))


full_image_bytes: list[int] = []


def shot(page, name: str) -> None:
    """Lưu ảnh chụp màn hình của kịch bản vào results/RUN_ID."""
    if args.screenshots:
        Path(args.screenshots).mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(Path(args.screenshots) / name), full_page=True)


def test_dashboard(browser) -> None:
    """Kiểm tra đăng nhập, cụm, bản đồ, điều phối, thống kê và Swagger."""
    print("\n== Dashboard (container dashboard)")
    check(status_without_login(args.api + "/api/clusters") == 401, "API dashboard từ chối khi chưa đăng nhập")
    check(status_without_login(args.api + "/api/reports/status?ids=x") == 200, "API trạng thái cho app không cần đăng nhập")
    page = browser.new_page(viewport={"width": 1400, "height": 1000})
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.goto(args.dashboard + "/", wait_until="networkidle")
    check(page.is_visible("#login-view"), "dashboard yêu cầu đăng nhập")
    page.fill("#login-username", args.username)
    page.fill("#login-password", args.password)
    page.click("#login-form button[type=submit]")
    page.wait_for_function("document.querySelectorAll('#cluster-list .cluster-row').length > 0", timeout=20000)
    dispatched = int(page.inner_text("#kpi-dispatched"))
    check(int(page.inner_text("#kpi-clusters")) > 0, "hiển thị cụm sự kiện và xếp hạng ưu tiên")
    check(page.locator(".leaflet-interactive").count() > 0, "bản đồ Leaflet có điểm báo cáo")
    reports = {r["id"]: r for r in api("/api/reports?limit=5000")["reports"]}
    if any(i.startswith("sim-") for i in reports):
        check(page.is_visible("#synthetic-banner"), "banner 'Dữ liệu mô phỏng' khi có dữ liệu bán tổng hợp")
    # Chọn cụm ưu tiên cao nhất còn báo cáo chưa điều phối (test chạy lại nhiều lần).
    cluster = next((c for c in api("/api/clusters")["clusters"]
                    if any(reports.get(i, {}).get("status") == "processing" for i in c["reportIds"])), None)
    if check(cluster is not None, "còn cụm có báo cáo chờ xử lý"):
        page.click(f'#cluster-list .cluster-row[data-cluster-key="{cluster["clusterKey"]}"]')
        page.wait_for_selector("#cluster-actions:not([hidden])")
        check(page.locator("#report-rows tr").count() > 0, "chọn cụm → lọc bảng báo cáo theo cụm")
        page.click("[data-cluster-action=dispatched]")
        page.wait_for_selector("#dialog[open]")
        check(page.locator("#dialog .id-list").count() == 1, "điều phối cả cụm hiện đúng danh sách báo cáo trước khi xác nhận")
        page.click("#dialog-ok")
        try:
            page.wait_for_function(f"Number(document.getElementById('kpi-dispatched').textContent) > {dispatched}", timeout=20000)
            check(True, "điều phối cả cụm cập nhật trạng thái")
        except Exception:
            check(False, "điều phối cả cụm cập nhật trạng thái")
    page.locator("#report-rows [data-open]").first.click()
    page.wait_for_selector("#drawer:not([hidden])")
    check('"id"' in (page.text_content("#d-raw") or ""), "xem chi tiết báo cáo")
    try:
        page.wait_for_selector("#d-history .timeline li", timeout=10000)
        check(True, "chi tiết có nhật ký thao tác")
    except Exception:
        check(False, "chi tiết có nhật ký thao tác")
    page.click("#drawer-close")
    page.click("[role=tab][data-tab=stats]")
    page.wait_for_selector("#stats-panel .stat-tile", timeout=10000)
    check(True, "tab thống kê hiển thị thời gian phản ứng")
    shot(page, "dashboard.png")
    page.goto(args.dashboard + "/docs", wait_until="networkidle")
    check(page.locator(".opblock").count() >= 8, "Swagger UI qua proxy dashboard")
    check(not errors, f"dashboard không có lỗi JS/console {errors[:2]}")
    page.close()


def test_app(browser) -> None:
    """Kiểm tra SOS, bài kèm ảnh, hàng đợi offline và phản hồi trạng thái."""
    print("\n== App web (container fe) → backend → dashboard")
    ctx, page, errors = open_app(browser, locale="vi-VN", geolocation={"latitude": LAT, "longitude": LNG}, permissions=["geolocation"])
    check("Bản web không chạy AI on-device" in screen_text(page), "trạng thái AI trên web ghi rõ lý do không khả dụng")

    known = report_ids()
    tap(page, "SOS")
    sos = wait_new("sos-", known)
    if check(len(sos) == 1, "SOS khi có mạng tới server (/sync/messages)"):
        r = sos[0]
        check(r["lat"] is not None and abs(r["lat"] - LAT) < 1e-3 and abs(r["lng"] - LNG) < 1e-3, f"SOS mang GPS thật ({r['lat']}, {r['lng']})")
        check(age_seconds(r) < 120, f"SOS createdAt là UTC đúng thời điểm ({r['createdAt']})")
    page.wait_for_timeout(3500)

    known = report_ids()
    submit_post(page, "Nhà bị ngập tới mái, 3 người mắc kẹt, cần cứu gấp", IMAGE)
    post = wait_new("post-", known)
    if check(len(post) == 1, "bài cứu hộ kèm ảnh tới server"):
        rid = post[0]["id"]
        r = wait_report(rid, lambda x: x.get("imageUrl"), timeout=20)
        check(r.get("sendMode") == "fullImage", f"mạng mạnh, không có AI → gửi ảnh gốc (sendMode={r.get('sendMode')})")
        if r.get("imageUrl"):
            full_image_bytes.append(image_size(r["imageUrl"]))
        if check(bool(r.get("imageUrl")), "ảnh được upload qua /api/reports"):
            data = fetch(args.app + r["imageUrl"])
            # [BỔ SUNG] Giữ bản ảnh server nhận để đối chiếu kích thước/hash sau này.
            (Path(args.upload_dir) / "full.jpg").write_bytes(data)
            check(status_without_login(args.app + r["imageUrl"]) == 401, "ảnh hiện trường cần đăng nhập mới xem được")
            check(r.get("imageSha256") == "sha256:" + hashlib.sha256(data).hexdigest(), "SHA-256 ảnh trên server khớp")
        check("mắc kẹt" in (r.get("description") or ""), "mô tả tiếng Việt được lưu")
        check(age_seconds(r) < 120, f"createdAt không lệch múi giờ sau khi upload ảnh ({r['createdAt']})")
    shot(page, "app_submitted.png")

    tap(page, "Trang chủ")
    page.wait_for_timeout(1500)
    known = report_ids()
    ctx.set_offline(True)
    page.wait_for_timeout(2500)
    tap(page, "SOS")
    page.wait_for_timeout(4000)
    check("1 bản ghi" in screen_text(page), "mất mạng: SOS nằm trong hàng đợi của app")
    check(not wait_new("sos-", known, timeout=3), "mất mạng: server chưa nhận")
    ctx.set_offline(False)
    late = wait_new("sos-", known, timeout=40)
    if check(len(late) == 1, "có mạng lại: hàng đợi tự đồng bộ"):
        check(late[0]["sendMode"] == "queuedOffline", "báo cáo đồng bộ muộn ghi sendMode=queuedOffline")
    page.wait_for_timeout(3000)
    check("0 bản ghi" in screen_text(page), "hàng đợi về 0 sau khi đồng bộ")

    ids = [r["id"] for r in sos + post + late]
    members = {rid for c in api("/api/clusters")["clusters"] for rid in c["reportIds"]}
    check(ids and all(i in members for i in ids), "báo cáo từ app được phân cụm trên server")

    if sos:
        cur = api(f"/api/reports/{sos[0]['id']}")
        api(f"/api/reports/{sos[0]['id']}/status", "PATCH", {"status": "dispatched", "statusVersion": cur["statusVersion"] + 1})
        tap(page, "Lịch sử")
        end, seen = time.time() + 45, False  # app hỏi trạng thái mỗi 15 s
        while time.time() < end and not seen:
            page.wait_for_timeout(2000)
            seen = "Đang đến" in screen_text(page)
        shot(page, "app_history.png")
        check(seen, "dashboard điều phối → app hiện 'Đang đến' (không cần tải lại)")
    check(not errors, f"app không có lỗi JS chưa bắt {errors[:2]}")
    ctx.close()


def test_adaptive_send(browser, kbps: int) -> None:
    """Thử riêng mạng 300 hoặc 20 kbit/s để checkpoint được từng mức."""
    print(f"\n== Gửi thích ứng theo mạng {kbps} kbit/s")
    expected, want_image = ("compressedImage", True) if kbps == 300 else ("textOnly", False)
    if kbps not in (300, 20):
        raise ValueError("Chỉ hỗ trợ kịch bản 300 hoặc 20 kbit/s")
    # [CHỈNH SỬA] Nội dung kịch bản gốc giữ nguyên, tách vòng lặp thành 2 stage.
    ctx, page, errors = open_app(browser, geolocation={"latitude": LAT, "longitude": LNG}, permissions=["geolocation"])
    cdp = ctx.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send("Network.emulateNetworkConditions", {
        "offline": False, "latency": 150,
        "downloadThroughput": kbps * 1000 / 8, "uploadThroughput": kbps * 1000 / 8,
    })
    known = report_ids()
    submit_post(page, f"Thử mạng {kbps} kbit/s, nước ngập ngang ngực", IMAGE)
    new = wait_new("post-", known, timeout=60)
    if check(len(new) == 1, f"{kbps} kbit/s: bài tới server"):
        r = wait_report(new[0]["id"], lambda x: x.get("imageUrl") or not want_image, timeout=60)
        check(r.get("sendMode") == expected, f"{kbps} kbit/s: chọn {expected} (sendMode={r.get('sendMode')})")
        if want_image:
            size = image_size(r["imageUrl"]) if r.get("imageUrl") else 0
            full = (full_image_bytes or [0])[0]
            check(r.get("imageUrl") and 0 < size < full, f"{kbps} kbit/s: ảnh nén {size} B < ảnh gốc {full} B")
            if r.get("imageUrl"):
                (Path(args.upload_dir) / "compressed.jpg").write_bytes(fetch(args.api + r["imageUrl"]))
        else:
            page.wait_for_timeout(5000)
            check(not api(f"/api/reports/{r['id']}").get("imageUrl"), f"{kbps} kbit/s: không upload ảnh")
    check(not errors, f"{kbps} kbit/s: không có lỗi JS {errors[:2]}")
    ctx.close()


def test_without_gps(browser) -> None:
    """Kiểm tra SOS khi người dùng từ chối cấp vị trí."""
    print("\n== App web khi người dùng từ chối quyền vị trí")
    known = report_ids()
    ctx, page, errors = open_app(browser, deny_geolocation=True)
    tap(page, "SOS")
    new = wait_new("sos-", known)
    if check(len(new) == 1, "SOS vẫn gửi được khi không có GPS"):
        r = new[0]
        check(r["lat"] is None and r["lng"] is None, "không gửi tọa độ giả khi thiếu GPS")
        check(r["id"] in api("/api/clusters")["review"], "server đưa báo cáo thiếu vị trí vào hàng cần xem xét")
    check(not errors, f"không có lỗi JS chưa bắt {errors[:2]}")
    ctx.close()


# [CHỈNH SỬA] Khối chạy cũ chuyển vào main phía dưới để chọn run và resume.


def digest(path: Path, algorithm: str = "sha256") -> str:
    """Băm file nguồn để khi resume phát hiện dữ liệu hoặc code bị đổi."""
    h = hashlib.new(algorithm)
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    """Ghi checkpoint nguyên vẹn, tránh file JSON hỏng khi dừng giữa chừng."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def select_inputs(seed_run: int, csv_path: Path, requested_image: str | None) -> dict:
    """Kiểm tra gold và chọn đúng một ảnh high/JPEG trong split=val của CSV."""
    if not 1 <= seed_run <= 80:
        raise ValueError("--seed-run phải từ 1 đến 80")
    csv_path = csv_path.resolve(strict=True)
    gold = GOLD_DIR / f"run_{seed_run:03d}"
    algorithm = gold / "algorithm_input.json"
    gold_manifest = gold / "run_manifest.json"
    inputs = json.loads(algorithm.read_text(encoding="utf-8"))
    origin = json.loads(gold_manifest.read_text(encoding="utf-8"))
    expected_name = f"run_{seed_run:03d}"
    if inputs.get("dataset_id") != expected_name or origin.get("dataset_id") != expected_name:
        raise ValueError(f"dataset_id không khớp {expected_name}")
    reports = inputs.get("reports")
    if not isinstance(reports, list) or not reports:
        raise ValueError("algorithm_input.json không có reports")
    if len({r["event_id"] for r in reports}) != len(reports):
        raise ValueError("event_id bị trùng trong gold run")

    candidates = []
    val_count = 0
    with csv_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"relative_path", "split", "label", "md5"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV thiếu cột: {sorted(required - set(reader.fieldnames or []))}")
        for row in reader:
            if row["split"] != "val":
                continue
            val_count += 1
            rel = Path(row["relative_path"])
            if row["label"] == "high" and rel.suffix.lower() in {".jpg", ".jpeg"}:
                candidates.append(row)
    if not candidates:
        raise ValueError("CSV không có ảnh high JPG trong tập val")
    selected = next((r for r in candidates if r["relative_path"] == requested_image), None) if requested_image else candidates[0]
    if selected is None:
        raise ValueError("--image-relative-path phải là ảnh high JPG thuộc split=val trong CSV")
    rel = Path(selected["relative_path"])
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("relative_path của ảnh không an toàn")
    image = (IMAGE_ROOT / rel).resolve(strict=True)
    if not image.is_relative_to(IMAGE_ROOT.resolve(strict=True)):
        raise ValueError("Ảnh nằm ngoài IMAGE_ROOT")
    if selected["md5"] and digest(image, "md5") != selected["md5"].lower():
        raise ValueError(f"MD5 không khớp CSV: {rel}")
    hashes = {
        "csv": digest(csv_path), "image": digest(image),
        "gold_input": digest(algorithm), "gold_manifest": digest(gold_manifest),
        "runner": digest(Path(__file__)), "compose": digest(COMPOSE_FILE),
    }
    hashes.update({name: digest(path) for name, path in SUPPORT_FILES.items()})
    return {
        "seed_run": seed_run, "gold_name": expected_name,
        "report_count": len(reports), "report_ids": [f"sim-r{seed_run:03d}-{r['event_id']}" for r in reports],
        "csv": str(csv_path), "csv_val_count": val_count, "image_candidates": len(candidates),
        "image_relative_path": selected["relative_path"], "image": str(image),
        "image_bytes": image.stat().st_size,
        "gold_input": str(algorithm), "gold_manifest": str(gold_manifest),
        "sha256": hashes,
    }


class Tee:
    """Vừa in ra màn hình vừa lưu nguyên văn vào console.txt."""

    def __init__(self, screen, logfile):
        self.screen, self.logfile = screen, logfile

    def write(self, value):
        self.screen.write(value)
        self.logfile.write(value)
        self.logfile.flush()

    def flush(self):
        self.screen.flush()
        self.logfile.flush()


def compose(cmd: list[str], manifest: dict, log_file: Path, *, check: bool = True) -> int:
    """Chạy Compose của bản sao với project/volume riêng và lưu output."""
    config = manifest["config"]
    env = os.environ.copy()
    env.update({
        "E2E_PROJECT": config["project"], "E2E_RUN_ID": manifest["run_id"],
        "SEED_RUN": str(manifest["inputs"]["seed_run"]),
        "BE_PORT": str(config["be_port"]),
        "DASHBOARD_PORT": str(config["dashboard_port"]),
        "FE_PORT": str(config["fe_port"]),
        "RESCUE_ADMIN_USERNAME": config["username"],
        "RESCUE_ADMIN_PASSWORD": args.password,
    })
    command = ["docker", "compose", "-f", str(COMPOSE_FILE), "-p", config["project"], *cmd]
    with log_file.open("w", encoding="utf-8") as output:
        try:
            code = subprocess.run(command, cwd=EXPERIMENT_DIR, env=env, stdout=output, stderr=subprocess.STDOUT, text=True).returncode
        except OSError as error:
            output.write(str(error) + "\n")
            code = 127
    if check and code:
        raise RuntimeError(f"Docker Compose lỗi {code}; xem {log_file}")
    return code


def wait_services() -> None:
    """Đợi backend, dashboard và app sẵn sàng trước thao tác trình duyệt."""
    urls = [args.api + "/api/reports/status?ids=x", args.dashboard + "/", args.app + "/"]
    for url in urls:
        end = time.monotonic() + 120
        last_error = None
        while True:
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    if response.status == 200:
                        break
            except (urllib.error.URLError, http.client.HTTPException, OSError, TimeoutError) as error:
                # nginx/container có thể đóng socket trong lúc vừa khởi động; thử lại đến timeout.
                last_error = error
            if time.monotonic() >= end:
                raise RuntimeError(f"Dịch vụ không sẵn sàng sau 120 giây: {url}; lỗi cuối: {last_error}")
            time.sleep(2)


def verify_seed(inputs: dict) -> None:
    """Đảm bảo DB Docker có đủ ID của đúng gold run, kể cả khi resume."""
    actual = report_ids()
    missing = set(inputs["report_ids"]) - actual
    if missing:
        raise RuntimeError(f"DB thiếu {len(missing)} báo cáo seed của {inputs['gold_name']}; không resume trên DB khác")


def result_dir(manifest: dict) -> Path:
    """Thư mục kết quả ghi rõ gold run và RUN_ID để dễ nhận biết/tách lần chạy."""
    return artifact_dir(RESULTS_DIR, manifest)


def artifact_key(manifest: dict) -> str:
    """Tên chung cho đầu ra: gold run được chọn và RUN_ID duy nhất."""
    return f"{manifest['inputs']['gold_name']}__{manifest['run_id']}"


def artifact_dir(base: Path, manifest: dict) -> Path:
    return base / artifact_key(manifest)


def locate_log_dir(run_id: str) -> Path:
    """Tìm log định dạng mới, đồng thời vẫn resume được các run cũ."""
    legacy = LOGS_DIR / run_id
    if legacy.is_dir():
        return legacy
    matches = list(LOGS_DIR.glob(f"run_*__{run_id}"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Không tìm thấy duy nhất thư mục log cho RUN_ID={run_id}")
    return matches[0]


def write_summary(manifest: dict, state: dict) -> None:
    """Xuất từng tiêu chí CSV và tổng PASS/FAIL/CHƯA CÓ dạng JSON."""
    folder = result_dir(manifest)
    folder.mkdir(parents=True, exist_ok=True)
    checks = [dict(stage=stage, status=status, label=label)
              for stage in ("dashboard", "app", "adaptive_300", "adaptive_20", "no_gps")
              for status, label in state["completed"].get(stage, [])]
    with (folder / "checks.csv").open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=["stage", "status", "label"])
        writer.writeheader()
        writer.writerows(checks)
    counts = {status: sum(c["status"] == status for c in checks) for status in ("PASS", "FAIL", "CHƯA CÓ")}
    summary = {
        "run_id": manifest["run_id"], "gold_run": manifest["inputs"]["gold_name"],
        "seed_report_count": manifest["inputs"]["report_count"],
        "csv_val_count": manifest["inputs"]["csv_val_count"],
        "image_relative_path": manifest["inputs"]["image_relative_path"],
        "status": state["status"], "completed_stages": list(state["completed"]),
        "failed_stage": state.get("failed_stage"), "last_error": state.get("last_error"),
        "failed_attempt_checks": state.get("failed_checks", []),
        "stage_count": 5, "check_count": len(checks), "counts": counts,
        "interpretation": "PASS là tiêu chí đạt; FAIL là lỗi; CHƯA CÓ là khoảng trống chức năng. Một gold run là một kịch bản, không phải 80 lần lặp độc lập của ảnh.",
    }
    atomic_json(folder / "summary.json", summary)


def experiment(manifest: dict, state: dict) -> int:
    """Khởi động Docker, chạy phần còn thiếu và lưu checkpoint sau mỗi stage."""
    global results, IMAGE
    run_id = manifest["run_id"]
    logs = artifact_dir(LOGS_DIR, manifest)
    if not logs.is_dir():  # [TƯƠNG THÍCH] Resume log cũ chưa có tiền tố gold run.
        logs = LOGS_DIR / run_id
    checkpoint = CHECKPOINTS_DIR / f"{artifact_key(manifest)}.json"
    inputs = manifest["inputs"]
    IMAGE = inputs["image"]
    args.run_id = run_id
    args.api = f"http://localhost:{manifest['config']['be_port']}"
    args.dashboard = f"http://localhost:{manifest['config']['dashboard_port']}"
    args.app = f"http://localhost:{manifest['config']['fe_port']}"
    args.username = manifest["config"]["username"]
    args.chrome = manifest["config"]["chrome"]
    args.headed = manifest["config"]["headed"]
    output_dir = result_dir(manifest)
    args.screenshots = str(output_dir / "screenshots")
    args.upload_dir = str(artifact_dir(UPLOADS_DIR, manifest))
    Path(args.upload_dir).mkdir(parents=True, exist_ok=True)
    full_image_bytes.clear()
    if state.get("full_image_bytes"):
        full_image_bytes.append(state["full_image_bytes"])
    if state["status"] == "complete":
        print(f"{run_id} đã hoàn tất; xem {output_dir / 'summary.json'}")
        return 0

    attempt_no = state["attempt"] + 1
    results = []
    state["active_stage"] = None
    with (logs / "console.txt").open("a", encoding="utf-8") as log:
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = Tee(old_out, log), Tee(old_err, log)
        try:
            print(f"\nRUN_ID={run_id}; gold={inputs['gold_name']}; báo cáo seed={inputs['report_count']}")
            print(f"Ảnh CSV: {inputs['image_relative_path']}; {inputs['image_bytes']} byte")
            print(f"Tiếp tục bằng: python e2e_system.py --resume {run_id}")
            print(f"Đang chuẩn bị Docker; chi tiết lưu trong docker_up_attempt_{attempt_no}.txt", flush=True)
            # [BỔ SUNG] Resume không build lại image, không xóa volume/DB.
            state["attempt"] = attempt_no
            atomic_json(checkpoint, state)
            compose(["up", "-d"] if state.get("docker_started") else ["up", "-d", "--build"],
                    manifest, logs / f"docker_up_attempt_{attempt_no}.txt")
            state["docker_started"] = True
            atomic_json(checkpoint, state)
            wait_services()
            verify_seed(inputs)
            from playwright.sync_api import sync_playwright  # chỉ cần khi chạy E2E

            stages = [
                ("dashboard", test_dashboard), ("app", test_app),
                ("adaptive_300", lambda browser: test_adaptive_send(browser, 300)),
                ("adaptive_20", lambda browser: test_adaptive_send(browser, 20)),
                ("no_gps", test_without_gps),
            ]
            state["failed_stage"] = None
            state["last_error"] = None
            state["failed_checks"] = []
            with sync_playwright() as p:
                launch = {"args": ["--use-gl=swiftshader"], "headless": not args.headed}
                if args.chrome:
                    launch["executable_path"] = args.chrome
                browser = p.chromium.launch(**launch)
                try:
                    for name, function in stages:
                        if name in state["completed"]:
                            print(f"SKIP {name}: đã hoàn tất trong checkpoint")
                            continue
                        results = []
                        state["active_stage"] = name
                        print(f"\nSTAGE {name}", flush=True)
                        function(browser)
                        if not results or any(status == "FAIL" for status, _ in results):
                            raise RuntimeError(f"Stage {name} có tiêu chí FAIL; giữ checkpoint trước stage này")
                        if name == "app":
                            if not full_image_bytes:
                                raise RuntimeError("Stage app không lưu được kích thước ảnh gốc")
                            state["full_image_bytes"] = full_image_bytes[0]
                        state["completed"][name] = results.copy()
                        state["active_stage"] = None
                        state["status"] = "running"
                        atomic_json(checkpoint, state)
                        write_summary(manifest, state)
                finally:
                    browser.close()
            state["status"] = "complete"
            atomic_json(checkpoint, state)
            write_summary(manifest, state)
            print(f"Hoàn tất: {output_dir / 'summary.json'}")
            return 0
        except (Exception, KeyboardInterrupt):
            state["status"] = "interrupted"
            state["failed_stage"] = state.get("active_stage")
            state["last_error"] = str(sys.exc_info()[1])
            state["failed_checks"] = results.copy()
            atomic_json(checkpoint, state)
            write_summary(manifest, state)
            traceback.print_exc()
            print(f"Đã giữ tiến độ. Tiếp tục: python e2e_system.py --resume {run_id}")
            return 1
        finally:
            compose(["ps"], manifest, logs / f"docker_ps_attempt_{attempt_no}.txt", check=False)
            compose(["logs", "--no-color"], manifest, logs / f"docker_logs_attempt_{attempt_no}.txt", check=False)
            (logs / "exit_code.txt").write_text("0\n" if state["status"] == "complete" else "1\n", encoding="utf-8")
            if state["status"] == "complete":
                compose(["down"], manifest, logs / f"docker_down_attempt_{attempt_no}.txt", check=False)
            sys.stdout, sys.stderr = old_out, old_err


def main(argv=None) -> int:
    """Kiểm tra đầu vào, tạo lần chạy mới hoặc tiếp tục đúng checkpoint cũ."""
    global args
    args = parse_args(argv)
    if args.resume:
        run_id = args.resume
        if not run_id.startswith("e2e-") or not all(c.isalnum() or c in "-_" for c in run_id):
            raise ValueError("RUN_ID không hợp lệ")
        logs = locate_log_dir(run_id)
        manifest = json.loads((logs / "manifest.json").read_text(encoding="utf-8"))
        checkpoint = CHECKPOINTS_DIR / f"{artifact_key(manifest)}.json"
        legacy_checkpoint = CHECKPOINTS_DIR / f"{run_id}.json"
        if not checkpoint.is_file() and legacy_checkpoint.is_file():
            checkpoint = legacy_checkpoint
        state = json.loads(checkpoint.read_text(encoding="utf-8"))
        saved = manifest["inputs"]
        current = select_inputs(saved["seed_run"], Path(saved["csv"]), saved["image_relative_path"])
        if current != saved:
            raise ValueError("Đầu vào/code/Compose đã đổi so với manifest; tạo lần chạy mới")
        return experiment(manifest, state)

    inputs = select_inputs(args.seed_run, CSV_PATH, args.image_relative_path)
    if args.check_inputs:
        print(json.dumps({k: v for k, v in inputs.items() if k not in ("report_ids", "sha256")}, ensure_ascii=False, indent=2))
        print("Đầu vào hợp lệ; chưa chạy Docker hoặc Playwright.")
        return 0

    run_id = "e2e-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    config = {
        "project": run_id, "be_port": args.be_port,
        "dashboard_port": args.dashboard_port, "fe_port": args.fe_port,
        "username": args.username, "chrome": args.chrome, "headed": args.headed,
    }
    if len({args.be_port, args.dashboard_port, args.fe_port}) != 3 or not all(1 <= n <= 65535 for n in (args.be_port, args.dashboard_port, args.fe_port)):
        raise ValueError("Ba cổng phải khác nhau và nằm trong 1..65535")
    logs = LOGS_DIR / f"{inputs['gold_name']}__{run_id}"
    logs.mkdir(parents=True, exist_ok=False)
    manifest = {"run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(), "config": config, "inputs": inputs}
    atomic_json(logs / "manifest.json", manifest)
    # [BỔ SUNG] Ghi mã nguồn tại thời điểm chạy; không đưa mật khẩu vào manifest.
    for name, command in (("git_head.txt", ["git", "rev-parse", "HEAD"]),
                          ("git_status.txt", ["git", "status", "--short", "--untracked-files=no"])):
        with (logs / name).open("w", encoding="utf-8") as output:
            try:
                subprocess.run(command, cwd=REPO_ROOT, stdout=output, stderr=subprocess.STDOUT, check=False)
            except OSError as error:
                output.write(str(error) + "\n")
    # [BỔ SUNG] Snapshot dữ liệu đầu vào; gold gốc và CSV gốc không bị sửa.
    shutil.copy2(inputs["csv"], logs / "input_validation.csv")
    snapshot = DATA_DIR / f"{inputs['gold_name']}__{run_id}"
    snapshot.mkdir(parents=True, exist_ok=False)
    shutil.copy2(inputs["gold_input"], snapshot / "algorithm_input.json")
    shutil.copy2(inputs["gold_manifest"], snapshot / "run_manifest.json")
    shutil.copy2(inputs["image"], snapshot / Path(inputs["image"]).name)
    state = {"run_id": run_id, "status": "created", "attempt": 0, "docker_started": False,
             "completed": {}, "full_image_bytes": None}
    atomic_json(CHECKPOINTS_DIR / f"{inputs['gold_name']}__{run_id}.json", state)
    return experiment(manifest, state)


if __name__ == "__main__":
    # [BỔ SUNG] Windows terminal có thể dùng cp1252; log tiếng Việt cần UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Lỗi đầu vào: {error}", file=sys.stderr)
        sys.exit(2)
