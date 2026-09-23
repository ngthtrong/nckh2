"""Script kiểm thử toàn diện Mock Server theo docs/contact_connect.md."""

import io
import json
import time
import requests

from canonical import compute_bytes_sha256, compute_payload_hash

BASE_URL = "http://localhost:8000"


def test_probe():
    print("\n--- [1] KIỂM TRA GET /probe ---")
    start = time.perf_counter()
    resp = requests.get(f"{BASE_URL}/probe", timeout=5)
    duration = time.perf_counter() - start
    
    assert resp.status_code == 200, f"Probe thất bại: {resp.status_code}"
    size_bytes = len(resp.content)
    throughput_kbps = ((size_bytes / 1024) / duration) if duration > 0 else 0
    
    print(f"✓ HTTP {resp.status_code} ({size_bytes} bytes)")
    print(f"✓ Throughput: {throughput_kbps:.1f} KB/s")


def test_api_reports_with_sha256():
    print("\n--- [2] KIỂM TRA POST /api/reports (KÈM ẢNH & SHA-256 CHECK) ---")
    rec_id = f"rescue_{int(time.time())}"
    fake_jpeg = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
        b"\xff\xc0\x00\x0b\x08\x00\x10\x00\x10\x01\x01\x11\x00\xff\xd9"
    )
    img_sha = compute_bytes_sha256(fake_jpeg)

    meta = {
        "id": rec_id,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lat": 16.4637,
        "lng": 107.5909,
        "trappedCount": 2,
        "injuredCount": 0,
        "vulnerableGroups": ["child"],
        "description": "Nước ngập đường, cần xuồng hỗ trợ",
        "sendMode": "compressedImage",
        "imageSha256": img_sha,
        "imageSizeBytes": len(fake_jpeg),
    }

    headers = {"X-Message-Contract-Version": "1"}
    data = {"meta": json.dumps(meta, ensure_ascii=False)}
    files = {"image": (f"{rec_id}.jpg", io.BytesIO(fake_jpeg), "image/jpeg")}

    resp = requests.post(f"{BASE_URL}/api/reports", data=data, files=files, headers=headers, timeout=10)
    assert resp.status_code == 201, f"Lỗi POST /api/reports: {resp.status_code} - {resp.text}"
    print(f"✓ HTTP {resp.status_code}: Đã lưu báo cáo kèm ảnh và kiểm tra SHA-256 thành công.")

    # Kiểm tra gửi SHA sai -> từ chối IMAGE_HASH_MISMATCH
    meta["imageSha256"] = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    data_bad = {"meta": json.dumps(meta, ensure_ascii=False)}
    files_bad = {"image": (f"{rec_id}.jpg", io.BytesIO(fake_jpeg), "image/jpeg")}
    resp_bad = requests.post(f"{BASE_URL}/api/reports", data=data_bad, files=files_bad, headers=headers, timeout=10)
    assert resp_bad.status_code == 400 and "IMAGE_HASH_MISMATCH" in resp_bad.text
    print("✓ HTTP 400 IMAGE_HASH_MISMATCH: Từ chối ảnh sai hash thành công.")


def test_sync_messages():
    print("\n--- [3] KIỂM TRA POST /sync/messages (DEDUP, HASH, STATUS TRANSITION) ---")
    headers = {
        "Content-Type": "application/json",
        "X-Message-Contract-Version": "1",
    }

    # 1. Test header version sai -> 400 UNSUPPORTED_CONTRACT_VERSION
    resp_v = requests.post(f"{BASE_URL}/sync/messages", json={"messages": []}, headers={"X-Message-Contract-Version": "99"})
    assert resp_v.status_code == 400 and "UNSUPPORTED_CONTRACT_VERSION" in resp_v.text
    print("✓ Kiểm tra phiên bản contract: Chặn phiên bản không hỗ trợ thành công.")

    client_id = f"device_{int(time.time())}"
    msg1_id = f"msg_{int(time.time())}_1"
    rescue_id = f"rescue_{int(time.time())}_sync"

    payload1 = {
        "id": rescue_id,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lat": 10.7626,
        "lng": 106.6601,
        "trappedCount": 3,
        "injuredCount": 1,
        "vulnerableGroups": ["elderly"],
        "description": "Nước lên tầng 2",
        "sendMode": "queuedOffline",
        "status": "processing",
    }
    hash1 = compute_payload_hash(payload1)

    msg1 = {
        "message_id": msg1_id,
        "client_id": client_id,
        "sequence_number": 1,
        "operation_type": "CREATE_RESCUE_RECORD",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload_hash": hash1,
        "payload": payload1,
    }

    # Batch 1: Gửi CREATE_RESCUE_RECORD mới
    resp1 = requests.post(f"{BASE_URL}/sync/messages", json={"messages": [msg1]}, headers=headers, timeout=10)
    assert resp1.status_code == 200
    res1 = resp1.json()["results"][0]
    assert res1["status"] == "accepted", f"Mong muốn accepted nhưng nhận: {res1}"
    print(f"✓ Message 1 (CREATE_RESCUE_RECORD): {res1['status']}")

    # Batch 2: Gửi lại cùng message1 -> phải trả duplicate + kết quả cũ
    resp2 = requests.post(f"{BASE_URL}/sync/messages", json={"messages": [msg1]}, headers=headers, timeout=10)
    res2 = resp2.json()["results"][0]
    assert res2["status"] == "duplicate", f"Mong muốn duplicate nhưng nhận: {res2}"
    print(f"✓ Gửi lại Message 1: {res2['status']} (Idempotency OK)")

    # Batch 3: Tái sử dụng message1_id nhưng payload khác -> rejected: ID_REUSED_WITH_DIFFERENT_PAYLOAD
    payload1_tampered = dict(payload1, trappedCount=99)
    msg1_tampered = dict(msg1, payload=payload1_tampered, payload_hash=compute_payload_hash(payload1_tampered))
    resp3 = requests.post(f"{BASE_URL}/sync/messages", json={"messages": [msg1_tampered]}, headers=headers, timeout=10)
    res3 = resp3.json()["results"][0]
    assert res3["status"] == "rejected" and res3["code"] == "ID_REUSED_WITH_DIFFERENT_PAYLOAD"
    print(f"✓ Tái sử dụng message_id với payload khác: {res3['code']}")

    # Batch 4: Tái sử dụng (client_id, sequence_number=1) với message_id khác -> rejected: SEQUENCE_REUSED
    msg_reused_seq = {
        "message_id": f"msg_{int(time.time())}_another",
        "client_id": client_id,
        "sequence_number": 1,  # Đã dùng ở msg1
        "operation_type": "CREATE_RESCUE_RECORD",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload_hash": hash1,
        "payload": payload1,
    }
    resp4 = requests.post(f"{BASE_URL}/sync/messages", json={"messages": [msg_reused_seq]}, headers=headers, timeout=10)
    res4 = resp4.json()["results"][0]
    assert res4["status"] == "rejected" and res4["code"] == "SEQUENCE_REUSED"
    print(f"✓ Tái sử dụng (client_id, sequence_number): {res4['code']}")

    # Batch 5: Cập nhật trạng thái UPDATE_RESCUE_STATUS (processing -> dispatched)
    payload_status = {
        "id": rescue_id,
        "status": "dispatched",
        "statusVersion": 2,
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    msg_status = {
        "message_id": f"msg_{int(time.time())}_status",
        "client_id": client_id,
        "sequence_number": 2,
        "operation_type": "UPDATE_RESCUE_STATUS",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload_hash": compute_payload_hash(payload_status),
        "payload": payload_status,
    }
    resp5 = requests.post(f"{BASE_URL}/sync/messages", json={"messages": [msg_status]}, headers=headers, timeout=10)
    res5 = resp5.json()["results"][0]
    assert res5["status"] == "accepted" and res5["result"]["status"] == "dispatched"
    print(f"✓ Cập nhật trạng thái UPDATE_RESCUE_STATUS (dispatched, v2): {res5['status']}")

    # Batch 6: Thử lùi trạng thái về processing -> rejected: INVALID_STATUS_TRANSITION
    payload_back = {
        "id": rescue_id,
        "status": "processing",
        "statusVersion": 3,
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    msg_back = {
        "message_id": f"msg_{int(time.time())}_back",
        "client_id": client_id,
        "sequence_number": 3,
        "operation_type": "UPDATE_RESCUE_STATUS",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload_hash": compute_payload_hash(payload_back),
        "payload": payload_back,
    }
    resp6 = requests.post(f"{BASE_URL}/sync/messages", json={"messages": [msg_back]}, headers=headers, timeout=10)
    res6 = resp6.json()["results"][0]
    assert res6["status"] == "rejected" and res6["code"] == "INVALID_STATUS_TRANSITION"
    print(f"✓ Thử lùi trạng thái về processing: {res6['code']}")


if __name__ == "__main__":
    print("Bắt đầu kiểm thử toàn diện Mock Server theo contact_connect.md...")
    try:
        test_probe()
        test_api_reports_with_sha256()
        test_sync_messages()
        print("\n==================================================================")
        print("✓ TẤT CẢ TEST CASES THEO CONTACT_CONNECT.MD ĐÃ ĐẠT 100%!")
        print("==================================================================")
    except Exception as err:
        print(f"\n❌ LỖI KIỂM THỬ: {err}")
