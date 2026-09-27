"""Kiểm thử end-to-end hệ thống demo chạy bằng Docker (docker-compose.yml).

App Flutter bản web (container fe) → backend (be) → dashboard điều phối (dashboard),
điều khiển bằng Chromium headless như một người dùng ở Đà Nẵng (múi giờ UTC+7).

    python -m venv .venv && .venv/bin/pip install -r scripts/demo/e2e/requirements.txt
    .venv/bin/playwright install chromium          # hoặc truyền --chrome <đường dẫn chrome>
    docker compose up -d --build
    .venv/bin/python scripts/demo/e2e/e2e_system.py

Test ghi báo cáo thật vào DB của container be (volume be-data). Mục "CHƯA CÓ" là tính
năng còn thiếu, được liệt kê riêng và không làm test thất bại; mục FAIL là lỗi.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
LAT, LNG = 16.0544, 108.2022  # Đà Nẵng, gần vùng dữ liệu mô phỏng EMSR848

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("--app", default="http://localhost:8081")
parser.add_argument("--api", default="http://localhost:8000")
parser.add_argument("--dashboard", default="http://localhost:8080")
parser.add_argument("--chrome", default=os.environ.get("CHROME_PATH"), help="Chromium dùng thay bản của Playwright")
parser.add_argument("--screenshots", default=None, help="thư mục lưu ảnh chụp màn hình")
args = parser.parse_args()

results: list[tuple[str, str]] = []


def check(cond: object, label: str, *, gap: bool = False) -> bool:
    status = "PASS" if cond else ("CHƯA CÓ" if gap else "FAIL")
    results.append((status, label))
    print(f"{status:8} {label}", flush=True)
    return bool(cond)


def api(path: str, method: str = "GET", body: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(args.api + path, method=method, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def report_ids() -> set[str]:
    return {r["id"] for r in api("/api/reports?limit=5000")["reports"]}


def wait_new(prefix: str, known: set[str], timeout: float = 30) -> list[dict]:
    end = time.time() + timeout
    while time.time() < end:
        new = [r for r in api("/api/reports?limit=5000")["reports"] if r["id"].startswith(prefix) and r["id"] not in known]
        if new:
            return new
        time.sleep(1)
    return []


def age_seconds(report: dict) -> float:
    created = datetime.fromisoformat(report["createdAt"].replace("Z", "+00:00"))
    if created.tzinfo is None:  # server và rescue_core hiểu giờ không múi là UTC
        created = created.replace(tzinfo=timezone.utc)
    return abs((datetime.now(timezone.utc) - created).total_seconds())


def enable_semantics(page) -> None:
    page.evaluate("document.querySelector('flt-semantics-placeholder')?.click()")
    page.wait_for_timeout(800)


def screen_text(page) -> str:
    return page.evaluate(
        "[...document.querySelectorAll('flt-semantics [aria-label], flt-semantics [role], flt-semantics span')]"
        ".map(e => (e.getAttribute('aria-label') || e.textContent || '').trim().replace(/\\s+/g, ' ')).join(' | ')"
    )


def tap(page, name: str) -> None:
    # Nút của app có animation (SOS nhấp nháy) nên bỏ qua kiểm tra "stable".
    page.get_by_role("button", name=name).first.click(force=True)


def open_app(browser, **context_args):
    ctx = browser.new_context(viewport={"width": 420, "height": 900}, timezone_id="Asia/Ho_Chi_Minh", **context_args)
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
    end = time.time() + timeout
    report = api(f"/api/reports/{rid}")
    while time.time() < end and not predicate(report):
        time.sleep(1)
        report = api(f"/api/reports/{rid}")
    return report


def image_size(url: str) -> int:
    return len(urllib.request.urlopen(args.api + url, timeout=15).read())


IMAGE = sorted(glob.glob(str(ROOT / "fe/model/Dataset_Flood/high/*.jp*g")))[0]
full_image_bytes: list[int] = []


def shot(page, name: str) -> None:
    if args.screenshots:
        Path(args.screenshots).mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(Path(args.screenshots) / name), full_page=True)


def test_dashboard(browser) -> None:
    print("\n== Dashboard (container dashboard)")
    page = browser.new_page(viewport={"width": 1400, "height": 1000})
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.goto(args.dashboard + "/", wait_until="networkidle")
    page.wait_for_function("document.querySelectorAll('#cluster-list > *').length > 0", timeout=20000)
    dispatched = int(page.inner_text("#stat-dispatched"))
    check(int(page.inner_text("#stat-clusters")) > 0, "hiển thị cụm sự kiện và xếp hạng ưu tiên")
    check(page.locator(".leaflet-interactive").count() > 0, "bản đồ Leaflet có điểm báo cáo")
    if "sim-" in json.dumps(api("/api/reports?limit=5000")):
        check(page.is_visible("#synthetic-banner"), "banner 'Dữ liệu mô phỏng' khi có dữ liệu bán tổng hợp")
    # Chọn cụm ưu tiên cao nhất còn báo cáo chưa điều phối (test chạy lại nhiều lần).
    rank = page.evaluate(
        "clusterData.clusters.find(c => c.reportIds.some(id => reports.find(r => r.id === id)?.status === 'processing'))?.rank"
    )
    page.locator("#cluster-list > *").nth((rank or 1) - 1).click()
    page.wait_for_selector("#dispatch-cluster:not(.hidden)")
    check(page.locator("#report-rows tr").count() > 0, "chọn cụm → lọc bảng báo cáo theo cụm")
    page.click("#dispatch-cluster")
    try:
        page.wait_for_function(f"Number(document.getElementById('stat-dispatched').textContent) > {dispatched}", timeout=20000)
        check(True, "điều phối cả cụm cập nhật trạng thái")
    except Exception:
        check(False, "điều phối cả cụm cập nhật trạng thái")
    page.locator("#report-rows button", has_text="Chi tiết").first.click()
    page.wait_for_selector("#json-modal:not(.hidden)")
    check('"id"' in page.inner_text("#modal-content"), "xem chi tiết báo cáo")
    page.click("#json-modal button")
    shot(page, "dashboard.png")
    page.goto(args.dashboard + "/docs", wait_until="networkidle")
    check(page.locator(".opblock").count() >= 8, "Swagger UI qua proxy dashboard")
    check(not errors, f"dashboard không có lỗi JS/console {errors[:2]}")
    page.close()


def test_app(browser) -> None:
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
            data = urllib.request.urlopen(args.app + r["imageUrl"], timeout=15).read()
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


def test_adaptive_send(browser) -> None:
    print("\n== Gửi thích ứng theo mạng (Chrome giới hạn băng thông)")
    for kbps, expected, want_image in ((300, "compressedImage", True), (20, "textOnly", False)):
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
            else:
                page.wait_for_timeout(5000)
                check(not api(f"/api/reports/{r['id']}").get("imageUrl"), f"{kbps} kbit/s: không upload ảnh")
        check(not errors, f"{kbps} kbit/s: không có lỗi JS {errors[:2]}")
        ctx.close()


def test_without_gps(browser) -> None:
    print("\n== App web khi người dùng từ chối quyền vị trí")
    known = report_ids()
    ctx, page, errors = open_app(browser)
    tap(page, "SOS")
    new = wait_new("sos-", known)
    if check(len(new) == 1, "SOS vẫn gửi được khi không có GPS"):
        r = new[0]
        check(r["lat"] is None and r["lng"] is None, "không gửi tọa độ giả khi thiếu GPS")
        check(r["id"] in api("/api/clusters")["review"], "server đưa báo cáo thiếu vị trí vào hàng cần xem xét")
    check(not errors, f"không có lỗi JS chưa bắt {errors[:2]}")
    ctx.close()


with sync_playwright() as p:
    launch = {"args": ["--use-gl=swiftshader"]}
    if args.chrome:
        launch["executable_path"] = args.chrome
    browser = p.chromium.launch(**launch)
    test_dashboard(browser)
    test_app(browser)
    test_adaptive_send(browser)
    test_without_gps(browser)
    browser.close()

counts = {s: sum(1 for status, _ in results if status == s) for s in ("PASS", "FAIL", "CHƯA CÓ")}
print(f"\nTổng: {counts['PASS']} PASS · {counts['FAIL']} FAIL · {counts['CHƯA CÓ']} CHƯA CÓ")
for status, label in results:
    if status != "PASS":
        print(f"  {status}: {label}")
sys.exit(1 if counts["FAIL"] else 0)
