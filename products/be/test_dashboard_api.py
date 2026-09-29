"""Kiểm thử API dashboard điều phối: đăng nhập, trạng thái cancelled, thao tác hàng loạt,
nhật ký, đội cứu hộ, vị trí thủ công, luồng thay đổi, thống kê và xuất dữ liệu.

Chạy trên DB tạm (không đụng be/data/rescue_reports.db):
    .venv/bin/python -m unittest test_dashboard_api -v
"""
import csv
import hashlib
import io
import json
import os
import tempfile
import unittest
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

_TMP = tempfile.TemporaryDirectory()
os.environ["RESCUE_DB_FILE"] = str(Path(_TMP.name) / "dashboard.db")
os.environ["RESCUE_UPLOADS_DIR"] = str(Path(_TMP.name) / "uploads")
os.environ.pop("RESCUE_ALLOW_WIPE", None)

from fastapi.testclient import TestClient  # noqa: E402

import accounts  # noqa: E402
import auth  # noqa: E402
import dashboard_service  # noqa: E402
import main  # noqa: E402
import storage  # noqa: E402
from canonical import compute_payload_hash  # noqa: E402


JPEG = b"\xff\xd8\xff\xe0" + b"\0" * 64
V1 = {"X-Message-Contract-Version": "1"}


def _with_image(meta, image, client_id="device-1"):
    """meta của app khi upload ảnh: kèm clientId (chủ báo cáo), imageSha256, imageSizeBytes."""
    meta = {**meta, "clientId": client_id} if client_id else dict(meta)
    if image is not None:
        meta.update(imageSha256="sha256:" + hashlib.sha256(image).hexdigest(), imageSizeBytes=len(image))
    return meta


def _message(seq, operation, payload, message_id=None):
    return {
        "message_id": message_id or f"m{seq}", "client_id": "device-1", "sequence_number": seq,
        "operation_type": operation, "created_at": "2026-09-27T00:00:00Z",
        "payload_hash": compute_payload_hash(payload), "payload": payload,
    }


def _report(rid, lat=16.05, lng=108.2, minutes_ago=5, **extra):
    created = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    meta = {
        "id": rid, "createdAt": created.isoformat().replace("+00:00", "Z"),
        "lat": lat, "lng": lng, "trappedCount": 2, "injuredCount": 1,
        "description": "Nước dâng, 3 người mắc kẹt", "sendMode": "fullImage",
    }
    meta.update(extra)
    return meta


PASSWORD = "test-pass-123"
accounts.PBKDF2_ITERATIONS = 1000  # băm nhanh cho kiểm thử; mã thật dùng 200 000 vòng


def _username(name):
    return "u" + hashlib.sha256(name.encode("utf-8")).hexdigest()[:10]


class DashboardApiTest(unittest.TestCase):
    def setUp(self):
        main.SMS_GATEWAY_TOKEN = ""
        auth._failures.clear()
        auth.TRUSTED_PROXIES = []
        storage.init_db()
        storage.clear_reports()
        with storage.get_db_connection() as conn:
            conn.execute("DELETE FROM teams")
            conn.execute("DELETE FROM sessions")
            conn.execute("DELETE FROM operators")
        self.client = TestClient(main.app)

    def account(self, name="Điều phối A", role="admin"):
        """Tài khoản có tên hiển thị ``name`` (tạo nếu chưa có); trả về tên đăng nhập."""
        username = _username(name)
        if not any(o["username"] == username for o in accounts.list_operators()):
            accounts.create_operator({"username": username, "displayName": name, "password": PASSWORD, "role": role})
        return username

    def login(self, name="Điều phối A", role="admin", client=None):
        res = (client or self.client).post(
            "/api/auth/login", json={"username": self.account(name, role), "password": PASSWORD})
        self.assertEqual(res.status_code, 200, res.text)
        return res.json()

    # ------------------------------------------------------------ xác thực
    def test_dashboard_endpoints_require_login_but_app_endpoints_do_not(self):
        storage.save_report(_report("r1"))
        for method, path in (("get", "/api/reports"), ("get", "/api/clusters"), ("get", "/api/stats"),
                             ("get", "/api/teams"), ("get", "/api/reports/r1"), ("get", "/api/export"),
                             ("get", "/api/reports/changes"), ("delete", "/api/reports")):
            self.assertEqual(getattr(self.client, method)(path).status_code, 401, path)
        self.assertEqual(self.client.patch("/api/reports/r1/status", json={"status": "dispatched", "statusVersion": 2}).status_code, 401)
        # Endpoint của app giữ nguyên, không cần đăng nhập.
        self.assertEqual(self.client.get("/api/reports/status?ids=r1").json()["reports"][0]["status"], "processing")
        self.assertEqual(self.client.get("/probe").status_code, 200)
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_login_logout_and_bearer_token(self):
        bad = self.client.post("/api/auth/login", json={"username": self.account(), "password": "sai"})
        self.assertEqual(bad.status_code, 401)
        session = self.login()
        self.assertEqual(session["operator"], "Điều phối A")
        self.assertIn("closeReasons", session["config"])
        self.assertEqual(self.client.get("/api/auth/me").json()["operator"], "Điều phối A")
        self.assertTrue(self.client.get("/api/auth/me").json()["authenticated"])

        # Script/kiểm thử dùng Bearer token thay cookie.
        other = TestClient(main.app)
        self.assertEqual(other.get("/api/teams", headers={"Authorization": f"Bearer {session['token']}"}).status_code, 200)

        self.client.post("/api/auth/logout")
        self.assertEqual(self.client.get("/api/auth/me").json(), {"authenticated": False})
        self.assertEqual(other.get("/api/teams", headers={"Authorization": f"Bearer {session['token']}"}).status_code, 401)

    def test_login_rate_limited_after_repeated_failures(self):
        username = self.account()
        for _ in range(auth.MAX_FAILURES_PER_USER):
            self.client.post("/api/auth/login", json={"username": username, "password": "sai"})
        res = self.client.post("/api/auth/login", json={"username": username, "password": PASSWORD})
        self.assertEqual(res.status_code, 429)

    def test_uploads_require_login(self):
        (storage.UPLOADS_DIR / "x.jpg").write_bytes(b"jpeg")
        self.assertEqual(self.client.get("/uploads/x.jpg").status_code, 401)
        self.login()
        self.assertEqual(self.client.get("/uploads/x.jpg").content, b"jpeg")

    def test_uploaded_image_name_is_chosen_by_server(self):
        res = self.client.post(
            "/api/reports",
            data={"meta": json.dumps(_with_image({"id": "sos-1", "lat": 16.0, "lng": 108.0}, JPEG))},
            files={"image": ("../../x.html", JPEG, "text/html")}, headers=V1,
        )
        self.assertEqual(res.status_code, 201, res.text)
        url = res.json()["imageUrl"]
        self.assertRegex(url, r"^/uploads/sos-1_[0-9a-f]{12}\.jpg$")
        self.assertNotIn("imageLocalPath", res.json())
        self.assertTrue((storage.UPLOADS_DIR / url.rsplit("/", 1)[1]).exists())
        self.login()
        served = self.client.get(url)
        self.assertEqual(served.headers["x-content-type-options"], "nosniff")
        self.assertIn("sandbox", served.headers["content-security-policy"])

    def test_unknown_status_on_create_becomes_processing(self):
        storage.save_report(_report("r1", status="bogus"))
        self.assertEqual(storage.get_report_by_id("r1")["status"], "processing")

    def test_wipe_disabled_by_default(self):
        self.login()
        res = self.client.delete("/api/reports")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["detail"]["code"], "WIPE_DISABLED")

    # ------------------------------------------------------------ tài khoản, phân quyền
    def test_operator_accounts_and_roles(self):
        self.login("Quản trị")
        res = self.client.post("/api/operators", json={
            "username": "dieuphoi1", "displayName": "Điều phối 1", "password": "matkhau-tam", "role": "operator"})
        self.assertEqual(res.status_code, 201, res.text)
        op = res.json()
        self.assertTrue(op["mustChangePassword"])
        self.assertEqual(self.client.post("/api/operators", json={
            "username": "DieuPhoi1", "displayName": "Khác", "password": "12345678"}).json()["detail"]["code"], "OPERATOR_TAKEN")
        self.assertEqual(self.client.post("/api/operators", json={
            "username": "ab", "displayName": "X", "password": "12345678"}).status_code, 400)
        self.assertEqual(self.client.post("/api/operators", json={
            "username": "abc", "displayName": "X", "password": "ngan"}).status_code, 400)

        other = TestClient(main.app)
        session = other.post("/api/auth/login", json={"username": "dieuphoi1", "password": "matkhau-tam"}).json()
        self.assertEqual((session["operator"], session["role"], session["mustChangePassword"]), ("Điều phối 1", "operator", True))
        # Điều phối viên không quản lý tài khoản, không tải sao lưu, không xóa dữ liệu.
        for method, path in (("get", "/api/operators"), ("get", "/api/admin/backup"), ("delete", "/api/reports")):
            self.assertEqual(getattr(other, method)(path).json()["detail"]["code"], "FORBIDDEN", path)
        self.assertEqual(other.get("/api/teams").status_code, 200)
        # Tự đổi mật khẩu: cần mật khẩu cũ đúng, hết cờ buộc đổi.
        self.assertEqual(other.post("/api/auth/password", json={"currentPassword": "sai", "newPassword": "moi-12345"}).status_code, 400)
        self.assertEqual(other.post("/api/auth/password", json={"currentPassword": "matkhau-tam", "newPassword": "moi-12345"}).status_code, 200)
        self.assertFalse(other.get("/api/auth/me").json()["mustChangePassword"])
        # Khóa tài khoản: phiên đang mở mất hiệu lực, không đăng nhập lại được.
        self.assertFalse(self.client.patch(f"/api/operators/{op['id']}", json={"active": False}).json()["active"])
        self.assertEqual(other.get("/api/teams").status_code, 401)
        self.assertEqual(other.post("/api/auth/login", json={"username": "dieuphoi1", "password": "moi-12345"}).status_code, 401)

    def test_last_admin_cannot_be_removed(self):
        me = self.login("Quản trị")
        self.assertEqual(self.client.patch(f"/api/operators/{me['operatorId']}", json={"role": "operator"}).json()["detail"]["code"], "LAST_ADMIN")
        self.assertEqual(self.client.patch(f"/api/operators/{me['operatorId']}", json={"active": False}).json()["detail"]["code"], "LAST_ADMIN")
        self.assertEqual(self.client.patch("/api/operators/9999", json={"active": False}).status_code, 404)

    def test_admin_reset_password_logs_user_out(self):
        self.login("Quản trị")
        other = TestClient(main.app)
        session = self.login("Người B", role="operator", client=other)
        res = self.client.patch(f"/api/operators/{session['operatorId']}", json={"password": "dat-lai-123"})
        self.assertTrue(res.json()["mustChangePassword"])
        self.assertEqual(other.get("/api/teams").status_code, 401)

    def test_bootstrap_admin_from_environment(self):
        with storage.get_db_connection() as conn:
            conn.execute("DELETE FROM operators")
        os.environ.update(RESCUE_ADMIN_USERNAME="Chief", RESCUE_ADMIN_PASSWORD="bootstrap-pass")
        try:
            accounts.ensure_admin()
            accounts.ensure_admin()  # lần hai không tạo thêm
        finally:
            os.environ.pop("RESCUE_ADMIN_USERNAME"), os.environ.pop("RESCUE_ADMIN_PASSWORD")
        self.assertEqual([(o["username"], o["role"]) for o in accounts.list_operators()], [("chief", "admin")])
        self.assertEqual(self.client.post("/api/auth/login", json={"username": "chief", "password": "bootstrap-pass"}).status_code, 200)
        self.assertFalse(accounts.uses_default_password())

    def test_forwarded_for_only_trusted_from_proxies(self):
        from starlette.requests import Request

        def ip(peer, forwarded=None):
            headers = [(b"x-forwarded-for", forwarded.encode())] if forwarded else []
            return auth.client_ip(Request({"type": "http", "client": (peer, 1234), "headers": headers}))

        auth.TRUSTED_PROXIES = []
        self.assertEqual(ip("203.0.113.9", "1.2.3.4"), "203.0.113.9")  # không có proxy tin cậy: bỏ qua header
        auth.TRUSTED_PROXIES = ["10.0.0.0/8"]
        auth._proxy_cache = (0.0, [])
        self.assertEqual(ip("203.0.113.9", "1.2.3.4"), "203.0.113.9")  # client gọi thẳng, tự giả header
        self.assertEqual(ip("10.0.0.2", "1.2.3.4, 198.51.100.7"), "198.51.100.7")  # phần bên trái do client tự gửi
        self.assertEqual(ip("10.0.0.2", "198.51.100.7, 10.0.0.3"), "198.51.100.7")
        self.assertEqual(ip("10.0.0.2"), "10.0.0.2")

    def test_ip_limit_applies_across_usernames(self):
        for i in range(auth.MAX_FAILURES_PER_IP):
            self.client.post("/api/auth/login", json={"username": f"doan{i}", "password": "sai"})
        res = self.client.post("/api/auth/login", json={"username": self.account(), "password": PASSWORD})
        self.assertEqual(res.status_code, 429)

    # ------------------------------------------------------------ vận hành
    def test_cleanup_removes_expired_sessions_and_old_dedup(self):
        old = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
        future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat().replace("+00:00", "Z")
        with storage.get_db_connection() as conn:
            conn.execute("INSERT INTO sessions (token_hash, operator, operator_id, created_at, expires_at) "
                         "VALUES ('x', 'A', 1, '2026-01-01T00:00:00Z', '2026-01-02T00:00:00Z')")
            for mid, seq, processed, expires in (("old", 1, old, None), ("old-unexpired", 2, old, future),
                                                 ("fresh", 3, datetime.now(timezone.utc).isoformat(), None)):
                conn.execute("INSERT INTO messages_dedup (message_id, client_id, sequence_number, operation_type, "
                             "payload_hash, status, created_at, expires_at, processed_at) "
                             "VALUES (?, 'c', ?, 'CREATE_RESCUE_RECORD', 'h', 'accepted', 'x', ?, ?)",
                             (mid, seq, expires, processed))
            conn.commit()
        self.assertEqual(storage.cleanup(30), {"sessions": 1, "messagesDedup": 1})
        with storage.get_db_connection() as conn:
            left = [r[0] for r in conn.execute("SELECT message_id FROM messages_dedup ORDER BY message_id")]
        self.assertEqual(left, ["fresh", "old-unexpired"])

    def test_healthz(self):
        res = self.client.get("/healthz")
        self.assertEqual((res.status_code, res.json()), (200, {"status": "ok"}))

    def test_backup_includes_images(self):
        (storage.UPLOADS_DIR / "r1_abc.jpg").write_bytes(JPEG)
        self.login()
        res = self.client.get("/api/admin/backup?images=1")
        self.assertEqual(res.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(res.content)) as archive:
            names = archive.namelist()
            self.assertIn("uploads/r1_abc.jpg", names)
            db_name = next(n for n in names if n.startswith("data/") and n.endswith(".db"))
            self.assertTrue(archive.read(db_name).startswith(b"SQLite format 3"))
        with tempfile.TemporaryDirectory() as mirror:
            self.assertGreaterEqual(storage.mirror_uploads(Path(mirror)), 1)
            self.assertEqual(storage.mirror_uploads(Path(mirror)), 0)  # lần sau chỉ chép ảnh mới
            self.assertEqual((Path(mirror) / "r1_abc.jpg").read_bytes(), JPEG)

    # ------------------------------------------------------------ tiếp nhận từ app
    def sync(self, *messages, token=None):
        headers = {"X-Message-Contract-Version": "1"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        res = self.client.post("/sync/messages", headers=headers, json={"messages": list(messages)})
        self.assertEqual(res.status_code, 200, res.text)
        return res.json()["results"]

    def test_status_update_via_sync_requires_dashboard_session(self):
        storage.save_report(_report("r1"))
        update = {"id": "r1", "status": "cancelled", "statusVersion": 9, "reason": "false_alarm"}
        anonymous = self.sync(_message(1, "UPDATE_RESCUE_STATUS", update))[0]
        self.assertEqual((anonymous["status"], anonymous["code"]), ("rejected", "UNAUTHENTICATED"))
        self.assertEqual(storage.get_report_by_id("r1")["status"], "processing")
        token = self.login("Điều phối C")["token"]
        accepted = self.sync(_message(2, "UPDATE_RESCUE_STATUS", update), token=token)[0]
        self.assertEqual(accepted["status"], "accepted")
        self.assertEqual(self.client.get("/api/reports/r1/history").json()["events"][-1]["actor"], "Điều phối C")

    def test_invalid_message_is_rejected_without_failing_batch(self):
        results = self.sync(
            _message(1, "CREATE_RESCUE_RECORD", {"id": "bad", "lat": "abc", "lng": 108.0}),
            _message(2, "CREATE_RESCUE_RECORD", [1, 2]),
            "not-an-object",
            _message(3, "CREATE_RESCUE_RECORD", {"id": "far", "lat": 16.0, "lng": 999}),
            _message(4, "CREATE_RESCUE_RECORD", {"id": "half", "lat": 16.0}),
            _message(5, "CREATE_RESCUE_RECORD", _report("good")),
        )
        self.assertEqual([r["status"] for r in results], ["rejected"] * 5 + ["accepted"])
        self.assertTrue(all(r["code"] == "INVALID_PAYLOAD" and not r["retryable"] for r in results[:5]))
        self.assertIsNotNone(storage.get_report_by_id("good"))
        body_list = self.client.post("/sync/messages", headers={"X-Message-Contract-Version": "1"}, json=[1])
        self.assertEqual(body_list.status_code, 400)

    def test_create_ignores_client_status(self):
        self.sync(_message(1, "CREATE_RESCUE_RECORD", _report("r1", status="resolved")))
        self.assertEqual(storage.get_report_by_id("r1")["status"], "processing")

    def test_same_id_fills_blanks_but_never_overwrites(self):
        self.sync(_message(1, "CREATE_RESCUE_RECORD", _report("r1", lat=None, lng=None, description="")))
        first = storage.get_report_by_id("r1")
        # Upload ảnh sau metadata: bổ sung vị trí, mô tả còn trống và gắn ảnh.
        res = self.client.post("/api/reports", data={"meta": json.dumps(_with_image(_report("r1", description="Nhà ngập"), JPEG))},
                               files={"image": ("r1.jpg", JPEG, "image/jpeg")}, headers=V1)
        self.assertEqual(res.status_code, 201, res.text)
        merged = storage.get_report_by_id("r1")
        self.assertEqual((merged["lat"], merged["description"]), (16.05, "Nhà ngập"))
        self.assertEqual(merged["serverReceivedAt"], first["serverReceivedAt"])
        # Request sau với cùng id không đổi được nội dung hay ảnh đã có.
        res = self.client.post("/api/reports", data={"meta": json.dumps(_with_image(_report("r1", lat=0.0, lng=0.0, description="sửa"), JPEG + b"khac"))},
                               files={"image": ("r1.jpg", JPEG + b"khac", "image/jpeg")}, headers=V1)
        self.assertEqual(res.json()["imageUrl"], merged["imageUrl"])
        again = storage.get_report_by_id("r1")
        self.assertEqual((again["lat"], again["description"], again["imageUrl"]), (16.05, "Nhà ngập", merged["imageUrl"]))
        kinds = [e["kind"] for e in storage.get_report_events("r1")]
        self.assertEqual(kinds, ["received", "image"])

    def test_only_report_owner_can_fill_blanks(self):
        # Báo cáo thiếu GPS, 0 người mắc kẹt, tạo từ thiết bị device-1.
        self.sync(_message(1, "CREATE_RESCUE_RECORD", _report("r1", lat=None, lng=None, trappedCount=0, description="")))
        # Người ngoài biết id (không clientId / clientId khác) không bổ sung được vị trí, số người, SĐT.
        forged = {**_report("r1", lat=21.0, lng=105.8, trappedCount=50, description="bịa"), "contactPhone": "+84999"}
        for client_id in (None, "attacker"):
            res = self.client.post("/api/reports", data={"meta": json.dumps(_with_image(forged, None, client_id))}, headers=V1)
            self.assertEqual((res.status_code, res.json()["detail"]["code"]), (409, "REPORT_ID_CONFLICT"))
        other = _message(2, "CREATE_RESCUE_RECORD", forged, message_id="m-attacker")
        other["client_id"] = "attacker"
        result = self.sync(other)[0]
        self.assertEqual((result["status"], result["code"], result["retryable"]), ("rejected", "REPORT_ID_CONFLICT", False))
        report = storage.get_report_by_id("r1")
        self.assertEqual((report["lat"], report["trappedCount"], report["description"], report["contactPhone"]),
                         (None, 0, "", None))
        self.assertNotIn("clientId", report["payload"])
        # Chủ báo cáo gửi ảnh: được gắn ảnh và điền mô tả trống, nhưng 0 người là giá trị thật, không bị thay.
        res = self.client.post("/api/reports", headers=V1, files={"image": ("r1.jpg", JPEG, "image/jpeg")},
                               data={"meta": json.dumps(_with_image(_report("r1", trappedCount=7, description="Nhà ngập"), JPEG))})
        self.assertEqual(res.status_code, 201, res.text)
        report = storage.get_report_by_id("r1")
        self.assertEqual((report["trappedCount"], report["description"]), (0, "Nhà ngập"))
        self.assertIsNotNone(report["imageUrl"])

    def test_sms_report_is_claimed_by_first_app_client_only(self):
        main.SMS_GATEWAY_TOKEN = "gw-secret"
        rid = "sos-1790000000002-00000000000a"
        self.sms({"from": "0900", "text": f"SOS|id:{rid}|pos:unknown|trapped:2|injured:1"})
        self.sync(_message(1, "CREATE_RESCUE_RECORD", _report(rid)))  # device-1 nhận làm chủ
        self.assertEqual(storage.report_owner(rid), (True, "device-1"))
        res = self.client.post("/api/reports", data={"meta": json.dumps(_with_image(_report(rid), None, "attacker"))}, headers=V1)
        self.assertEqual(res.status_code, 409)
        # Báo cáo tổng đài và tin SMS tự do không thiết bị nào nhận làm chủ được.
        self.login()
        hotline = self.client.post("/api/reports/manual", json={"description": "Gọi 114", "lat": 16.0, "lng": 108.0}).json()
        free = self.sms({"from": "0911", "text": "cuu voi"}).json()["id"]
        for report_id in (hotline["id"], free):
            res = self.client.post("/api/reports", headers=V1,
                                   data={"meta": json.dumps(_with_image(_report(report_id, lat=1.0, lng=1.0), None))})
            self.assertEqual(res.status_code, 409, report_id)
        self.assertEqual(storage.get_report_by_id(hotline["id"])["locationSource"], "manual")

    def test_sync_rejects_duplicate_keys_and_uses_error_codes(self):
        body = ('{"messages": [], "messages": []}').encode()
        res = self.client.post("/sync/messages", headers={**V1, "content-type": "application/json"}, content=body)
        self.assertEqual((res.status_code, res.json()["detail"]["code"]), (400, "INVALID_JSON"))
        res = self.client.post("/sync/messages", json={"messages": []})
        self.assertEqual(res.json()["detail"]["code"], "UNSUPPORTED_CONTRACT_VERSION")
        res = self.client.post("/sync/messages", headers=V1, json={"messages": [{}] * 51})
        self.assertEqual(res.json()["detail"]["code"], "TOO_MANY_MESSAGES")

    def test_upload_rejects_bad_meta_and_non_images(self):
        def post(meta, image=None, headers=V1):
            files = {"image": ("a.jpg", image, "image/jpeg")} if image is not None else None
            return self.client.post("/api/reports", data={"meta": json.dumps(meta) if not isinstance(meta, str) else meta},
                                    files=files, headers=headers)

        def code(res):
            return res.json()["detail"]["code"]

        self.assertEqual(code(post({"lat": 1, "lng": 1})), "INVALID_PAYLOAD")
        self.assertEqual(post({"id": "../../evil"}).status_code, 400)
        self.assertEqual(post("{không phải json").status_code, 400)
        self.assertEqual(code(post('{"id": "d1", "id": "d2"}')), "INVALID_PAYLOAD")  # key trùng (RFC 8785)
        self.assertEqual(code(post({"id": "big", "x": "a" * 70_000})), "INVALID_PAYLOAD")  # meta > 64 KiB
        self.assertEqual(post(_with_image({"id": "x1"}, b"<script>alert(1)</script>"), b"<script>alert(1)</script>").status_code, 415)
        # Dạng lỗi thống nhất {code, error}; app dựa vào mã này để gửi lại ảnh.
        mismatch = post({"id": "x2", "imageSha256": "sha256:00"}, JPEG)
        self.assertEqual((mismatch.status_code, code(mismatch)), (400, "IMAGE_HASH_MISMATCH"))
        short = post({**_with_image({"id": "x3"}, JPEG), "imageSizeBytes": len(JPEG) + 1}, JPEG)
        self.assertEqual(code(short), "IMAGE_HASH_MISMATCH")
        self.assertEqual(code(post({"id": "x4"}, JPEG)), "INVALID_PAYLOAD")  # ảnh thiếu imageSha256
        self.assertEqual(code(post({"id": "x5"}, headers={})), "UNSUPPORTED_CONTRACT_VERSION")
        self.assertIsNone(storage.get_report_by_id("x1"))
        self.assertIsNone(storage.get_report_by_id("x5"))

    # ------------------------------------------------------------ SMS và tổng đài
    def sms(self, body, token="gw-secret", **kwargs):
        return self.client.post("/api/sms/inbound", headers={"X-Gateway-Token": token}, json=body, **kwargs)

    def test_sms_gateway_requires_configured_token(self):
        main.SMS_GATEWAY_TOKEN = ""
        self.assertEqual(self.sms({"from": "0900", "text": "cứu"}).json()["detail"]["code"], "SMS_GATEWAY_DISABLED")
        main.SMS_GATEWAY_TOKEN = "gw-secret"
        self.assertEqual(self.sms({"from": "0900", "text": "cứu"}, token="sai").status_code, 401)

    def test_app_sos_sms_merges_with_later_sync(self):
        main.SMS_GATEWAY_TOKEN = "gw-secret"
        text = "SOS|id:sos-1790000000000-a1b2c3d4e5f6|pos:16.05000,108.20000|trapped:3|injured:1|vuln:elderly,children|note:Nước tới mái | cần xuồng"
        res = self.sms({"event": "sms:received", "payload": {"phoneNumber": "+84900000001", "message": text}})
        self.assertEqual((res.status_code, res.json()["created"]), (201, True))
        rid = res.json()["id"]
        self.assertEqual(rid, "sos-1790000000000-a1b2c3d4e5f6")
        report = storage.get_report_by_id(rid)
        self.assertEqual((report["lat"], report["trappedCount"], report["description"]), (16.05, 3, "Nước tới mái | cần xuồng"))
        self.assertEqual((report["sendMode"], report["contactPhone"]), ("smsFallback", "+84900000001"))
        self.assertEqual(report["vulnerableGroups"], ["elderly", "children"])
        # Gateway gửi lại: không tạo báo cáo mới.
        self.assertEqual(self.sms({"from": "+84900000001", "text": text}).json()["created"], False)
        # App có mạng, đồng bộ bản đầy đủ: điền createdAt và nhãn AI, giữ dữ liệu SMS.
        self.sync(_message(1, "CREATE_RESCUE_RECORD", _report(rid, aiTags=[{"label": "high", "confidence": 0.9}])))
        merged = storage.get_report_by_id(rid)
        self.assertEqual(merged["aiTags"][0]["label"], "high")
        self.assertTrue(merged["createdAt"])
        self.assertEqual((merged["contactPhone"], merged["description"]), ("+84900000001", "Nước tới mái | cần xuồng"))
        self.assertEqual([e["kind"] for e in storage.get_report_events(rid)], ["received"])

    def test_free_text_sms_goes_to_review(self):
        main.SMS_GATEWAY_TOKEN = "gw-secret"
        res = self.client.post("/api/sms/inbound?token=gw-secret",
                               data={"From": "0911222333", "Body": "Nha toi o thon 3 bi ngap, co ba gia"})
        self.assertEqual(res.status_code, 201, res.text)
        report = storage.get_report_by_id(res.json()["id"])
        self.assertIsNone(report["lat"])
        self.assertEqual((report["description"], report["payload"]["source"]), ("Nha toi o thon 3 bi ngap, co ba gia", "sms"))
        self.login()
        self.assertIn(report["id"], self.client.get("/api/clusters").json()["review"])
        self.assertEqual([r["id"] for r in self.client.get("/api/reports?source=sms").json()["reports"]], [report["id"]])
        self.assertEqual(self.sms({"from": "0911", "text": "   "}).status_code, 400)

    def test_sms_after_app_sync_logs_contact(self):
        main.SMS_GATEWAY_TOKEN = "gw-secret"
        rid = "sos-1790000000001-000000000001"
        self.sync(_message(1, "CREATE_RESCUE_RECORD", _report(rid)))
        self.sms({"from": "0900", "text": f"SOS|id:{rid}|pos:unknown|trapped:2|injured:1"})
        self.assertEqual(storage.get_report_by_id(rid)["contactPhone"], "0900")
        self.assertEqual([e["kind"] for e in storage.get_report_events(rid)], ["received", "sms"])

    def test_operator_creates_hotline_report(self):
        self.assertEqual(self.client.post("/api/reports/manual", json={"description": "x"}).status_code, 401)
        self.login("Tổng đài 1")
        self.assertEqual(self.client.post("/api/reports/manual", json={"description": "  "}).status_code, 400)
        self.assertEqual(self.client.post("/api/reports/manual", json={"description": "x", "lat": 16.0}).status_code, 400)
        res = self.client.post("/api/reports/manual", json={
            "description": "Gọi 114: 2 người trên mái nhà", "contactPhone": "0912345678",
            "lat": 16.06, "lng": 108.21, "trappedCount": 2, "vulnerableGroups": ["elderly"],
        })
        self.assertEqual(res.status_code, 201, res.text)
        report = res.json()
        self.assertRegex(report["id"], r"^hotline-\d+-[0-9a-f]{6}$")
        self.assertEqual((report["sendMode"], report["locationSource"], report["contactPhone"]), ("hotline", "manual", "0912345678"))
        event = self.client.get(f"/api/reports/{report['id']}/history").json()["events"][0]
        self.assertEqual((event["kind"], event["actor"], event["source"]), ("received", "Tổng đài 1", "dashboard"))

    # ------------------------------------------------------------ trạng thái
    def test_cancel_requires_reason_and_is_terminal(self):
        storage.save_report(_report("r1"))
        self.login()
        res = self.client.patch("/api/reports/r1/status", json={"status": "cancelled", "statusVersion": 2})
        self.assertEqual(res.status_code, 400)
        res = self.client.patch("/api/reports/r1/status", json={
            "status": "cancelled", "statusVersion": 2, "reason": "duplicate", "note": "trùng sos-1",
        })
        self.assertEqual(res.status_code, 200, res.text)
        report = self.client.get("/api/reports/r1").json()
        self.assertEqual((report["status"], report["closeReason"]), ("cancelled", "duplicate"))
        for status in ("resolved", "dispatched", "processing"):
            res = self.client.patch("/api/reports/r1/status", json={"status": status, "statusVersion": 3})
            self.assertEqual(res.json()["detail"]["code"], "INVALID_STATUS_TRANSITION")
        # Báo cáo đã đóng không còn tham gia phân cụm.
        clusters = self.client.get("/api/clusters").json()
        self.assertNotIn("r1", [rid for c in clusters["clusters"] for rid in c["reportIds"]])

    def test_resolved_cannot_become_cancelled_via_sync(self):
        storage.save_report(_report("r1"))
        storage.update_report_status("r1", "resolved", 2)
        payload = {"id": "r1", "status": "cancelled", "statusVersion": 3, "reason": "other"}
        result = storage.process_sync_messages([{
            "message_id": "m1", "client_id": "c1", "sequence_number": 1,
            "operation_type": "UPDATE_RESCUE_STATUS", "created_at": "2026-09-27T00:00:00Z",
            "payload_hash": compute_payload_hash(payload), "payload": payload,
        }], operator="Điều phối A")
        self.assertEqual(result[0]["code"], "INVALID_STATUS_TRANSITION")

    def test_status_change_is_logged_with_operator_and_team(self):
        storage.save_report(_report("r1"))
        self.login("Nguyễn Văn B")
        team = self.client.post("/api/teams", json={"name": "Đội 1", "phone": "0900", "members": 6}).json()
        res = self.client.patch("/api/reports/r1/status", json={
            "status": "dispatched", "statusVersion": 2, "teamId": team["id"], "note": "xuồng máy",
        })
        self.assertEqual(res.status_code, 200, res.text)
        events = self.client.get("/api/reports/r1/history").json()["events"]
        self.assertEqual([e["kind"] for e in events], ["received", "status", "assign"])
        status_event = events[1]
        self.assertEqual((status_event["from"], status_event["to"], status_event["actor"], status_event["note"]),
                         ("processing", "dispatched", "Nguyễn Văn B", "xuồng máy"))
        self.assertEqual(self.client.get("/api/reports/r1").json()["assignedTeamId"], team["id"])
        self.assertEqual(self.client.get("/api/teams").json()["teams"][0]["activeAssignments"], 1)

    def test_bulk_status_reports_each_failure(self):
        for rid in ("a", "b", "c"):
            storage.save_report(_report(rid))
        storage.update_report_status("b", "dispatched", 2)
        self.login()
        res = self.client.post("/api/reports/bulk-status", json={
            "status": "dispatched",
            "items": [{"id": "a", "statusVersion": 2}, {"id": "b", "statusVersion": 2}, {"id": "zzz", "statusVersion": 2}],
        }).json()
        self.assertEqual((res["ok"], res["failed"]), (1, 2))
        codes = {r["id"]: r.get("code") for r in res["results"]}
        self.assertEqual(codes, {"a": None, "b": "INVALID_STATUS_VERSION", "zzz": "REPORT_NOT_FOUND"})
        self.assertEqual(storage.get_report_by_id("c")["status"], "processing")

    # ------------------------------------------------------------ đội, ghi chú, vị trí
    def test_team_management_and_assignment(self):
        storage.save_report(_report("r1"))
        self.login()
        team = self.client.post("/api/teams", json={"name": "Đội A"}).json()
        self.assertEqual(self.client.post("/api/teams", json={"name": "Đội A"}).status_code, 409)
        self.assertEqual(self.client.post("/api/teams", json={"name": " "}).status_code, 400)
        self.assertEqual(self.client.put("/api/reports/r1/team", json={"teamId": team["id"]}).json()["assignedTeamId"], team["id"])
        self.client.patch(f"/api/teams/{team['id']}", json={"active": False})
        storage.save_report(_report("r2"))
        res = self.client.put("/api/reports/r2/team", json={"teamId": team["id"]})
        self.assertEqual(res.json()["detail"]["code"], "TEAM_INACTIVE")
        self.assertIsNone(self.client.put("/api/reports/r1/team", json={"teamId": None}).json()["assignedTeamId"])

    def test_note_and_manual_location_for_review_report(self):
        storage.save_report(_report("nogps", lat=None, lng=None), client_id="device-1")
        self.login()
        self.assertIn("nogps", self.client.get("/api/clusters").json()["review"])
        self.assertEqual(self.client.post("/api/reports/nogps/notes", json={"text": "  "}).status_code, 400)
        self.assertEqual(self.client.post("/api/reports/nogps/notes", json={"text": "Gọi lại được, ở tổ 5"}).status_code, 201)
        self.assertEqual(self.client.put("/api/reports/nogps/location", json={"lat": 123, "lng": 0}).status_code, 400)
        res = self.client.put("/api/reports/nogps/location", json={"lat": 16.06, "lng": 108.21, "note": "xác minh qua điện thoại"})
        self.assertEqual(res.json()["locationSource"], "manual")
        clusters = self.client.get("/api/clusters").json()
        self.assertNotIn("nogps", clusters["review"])
        kinds = [e["kind"] for e in self.client.get("/api/reports/nogps/history").json()["events"]]
        self.assertEqual(kinds, ["received", "note", "location"])
        # App gửi lại cùng id không có GPS: giữ vị trí điều phối viên đã nhập.
        storage.save_report(_report("nogps", lat=None, lng=None), image_url="/uploads/nogps.jpg", client_id="device-1")
        report = storage.get_report_by_id("nogps")
        self.assertEqual((report["lat"], report["locationSource"]), (16.06, "manual"))

    # ------------------------------------------------------------ đồng bộ dashboard
    def test_changes_feed_is_incremental_and_resets_on_wipe(self):
        storage.save_report(_report("r1"))
        self.login()
        first = self.client.get("/api/reports/changes?since=0").json()
        self.assertTrue(first["reset"])
        self.assertEqual([r["id"] for r in first["reports"]], ["r1"])
        cursor, epoch = first["cursor"], first["epoch"]

        empty = self.client.get(f"/api/reports/changes?since={cursor}&epoch={epoch}").json()
        self.assertEqual((empty["reports"], empty["reset"]), ([], False))

        storage.save_report(_report("r2"))
        storage.add_note("r1", "đã gọi", actor="A")
        changed = self.client.get(f"/api/reports/changes?since={cursor}&epoch={epoch}").json()
        self.assertEqual(sorted(r["id"] for r in changed["reports"]), ["r1", "r2"])
        self.assertGreater(changed["cursor"], cursor)

        storage.clear_reports()
        storage.save_report(_report("r3"))
        after_wipe = self.client.get(f"/api/reports/changes?since={changed['cursor']}&epoch={epoch}").json()
        self.assertTrue(after_wipe["reset"])
        self.assertEqual([r["id"] for r in after_wipe["reports"]], ["r3"])

    def test_clusters_have_stable_key_and_etag(self):
        for i in range(4):
            storage.save_report(_report(f"k{i}", lat=16.05 + i * 0.0005, lng=108.2, minutes_ago=5 + i))
        self.login()
        res = self.client.get("/api/clusters")
        data, etag = res.json(), res.headers["etag"]
        for cluster in data["clusters"]:
            self.assertEqual(cluster["clusterKey"], min(cluster["reportIds"]))
        self.assertEqual(self.client.get("/api/clusters", headers={"If-None-Match": etag}).status_code, 304)
        storage.add_note("k0", "ghi chú không đổi phân cụm", actor="A")
        self.assertEqual(self.client.get("/api/clusters", headers={"If-None-Match": etag}).status_code, 304)
        storage.save_report(_report("k9"))
        self.assertEqual(self.client.get("/api/clusters", headers={"If-None-Match": etag}).status_code, 200)

    # ------------------------------------------------------------ truy vấn, thống kê, xuất
    def test_list_filters_sort_and_pagination(self):
        storage.save_report(_report("sos-1", minutes_ago=30, vulnerableGroups=["elderly"]))
        storage.save_report(_report("post-2", minutes_ago=10, description="Cần cứu gấp", trappedCount=9))
        storage.save_report(_report("sos-3", lat=None, lng=None, minutes_ago=1, sendMode="textOnly"))
        storage.update_report_status("post-2", "dispatched", 2)
        self.login()

        def ids(query):
            res = self.client.get("/api/reports?" + query)
            self.assertEqual(res.status_code, 200, res.text)
            return [r["id"] for r in res.json()["reports"]]

        self.assertEqual(ids("status=dispatched"), ["post-2"])
        self.assertEqual(ids("q=gấp"), ["post-2"])
        self.assertEqual(ids("q=SOS&sort=createdAt"), ["sos-1", "sos-3"])
        self.assertEqual(ids("hasLocation=false"), ["sos-3"])
        self.assertEqual(ids("vulnerable=any"), ["sos-1"])
        self.assertEqual(ids("sendMode=textOnly"), ["sos-3"])
        self.assertEqual(ids("sort=-people")[0], "post-2")
        since = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        self.assertEqual(set(ids("since=" + since.replace("+", "%2B"))), {"post-2", "sos-3"})
        page = self.client.get("/api/reports?pageSize=2&page=2&sort=createdAt").json()
        self.assertEqual((page["total"], page["pages"], [r["id"] for r in page["reports"]]), (3, 2, ["sos-3"]))
        self.assertEqual(self.client.get("/api/reports?sort=bogus").status_code, 400)
        # Tên tham số cũ `limit` vẫn dùng được.
        self.assertEqual(len(self.client.get("/api/reports?limit=5000").json()["reports"]), 3)

    def test_stats_response_times(self):
        storage.save_report(_report("r1"))
        storage.update_report_status("r1", "dispatched", 2)
        storage.update_report_status("r1", "resolved", 3)
        storage.save_report(_report("r2", lat=None, lng=None))
        self.login()
        stats = self.client.get("/api/stats").json()
        self.assertEqual((stats["counts"]["total"], stats["counts"]["resolved"], stats["counts"]["noLocation"]), (2, 1, 1))
        self.assertEqual(stats["response"]["receivedToDispatch"]["count"], 1)
        self.assertEqual(stats["response"]["receivedToResolve"]["count"], 1)
        self.assertEqual(len(stats["hourly"]), 24)
        self.assertEqual(sum(b["received"] for b in stats["hourly"]), 2)
        self.assertEqual(sum(b["resolved"] for b in stats["hourly"]), 1)

    def test_summary_quantiles(self):
        summary = dashboard_service._summary([1, 2, 3, 4, 10])
        self.assertEqual((summary["medianMin"], summary["p90Min"]), (3, 7.6))

    def test_export_csv_and_geojson(self):
        storage.save_report(_report("r1", description='Có dấu phẩy, và "ngoặc"'))
        storage.save_report(_report("r2", lat=None, lng=None))
        self.login()
        res = self.client.get("/api/export?format=csv")
        self.assertIn("attachment", res.headers["content-disposition"])
        rows = list(csv.DictReader(io.StringIO(res.content.decode("utf-8-sig"))))
        self.assertEqual({r["id"] for r in rows}, {"r1", "r2"})
        self.assertEqual(next(r for r in rows if r["id"] == "r1")["description"], 'Có dấu phẩy, và "ngoặc"')
        geo = json.loads(self.client.get("/api/export?format=geojson&status=processing").content)
        self.assertEqual([f["properties"]["id"] for f in geo["features"]], ["r1"])
        self.assertEqual(geo["features"][0]["geometry"]["coordinates"], [108.2, 16.05])
        self.assertEqual(self.client.get("/api/export?format=xml").status_code, 400)

    def test_backup_download_is_valid_sqlite(self):
        storage.save_report(_report("r1"))
        self.login()
        res = self.client.get("/api/admin/backup")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.content.startswith(b"SQLite format 3"))


if __name__ == "__main__":
    unittest.main()
