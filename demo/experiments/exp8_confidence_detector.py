"""Thí nghiệm 8 — C_i như bộ phát hiện tin giả + kịch bản đối kháng (phản biện 4.1).

Phản biện: toàn bộ bằng chứng đến từ một dataset tự sinh, trong đó tin giả được
thiết kế để *đúng là* cô lập + không ảnh — nên heuristic C_i tất nhiên gán điểm
thấp. Câu hỏi reviewer: (i) C_i tách tin giả tốt đến đâu (định lượng)? (ii) một
adversary tinh vi (có ảnh giả, hoặc phối hợp nhiều tin để tạo corroboration giả)
có đánh lừa được heuristic không?

Hai phần:
  (A) Bộ phát hiện yếu: đo AUC/precision của (1 - C_i) so với nhãn is_fake trên
      TOÀN dataset chính (không đụng dataset — chỉ đọc + tính C_i như mọi exp).
  (B) Đối kháng: dựng thêm 3 tin giả tinh vi (TỰ CHỨA trong exp này, KHÔNG sửa
      data/generate.py) và đo C_i của chúng:
        - ADV_IMG   : tin giả CÓ ảnh (qua được cờ has_image) nhưng vẫn cô lập.
        - ADV_CORR  : một CỤM 4 tin giả phối hợp cùng vùng/cửa sổ -> tự củng cố
                      lẫn nhau (corroboration giả), không ảnh.
        - ADV_BOTH  : cụm 4 tin giả CÓ ảnh + tự củng cố (kịch bản xấu nhất).
      So C_i của chúng với tin giả ngây thơ (S3_FAKE) và với báo cáo thật.

Trung thực: kỳ vọng heuristic MẠNH với tin giả ngây thơ, YẾU với adversary phối
hợp — ta báo cáo đúng giới hạn này, không tô hồng.
"""
from __future__ import annotations

from datetime import timedelta

from sklearn.metrics import roc_auc_score, average_precision_score

from common import prepared_events, print_table, save_table
from pipeline.config import DEFAULT_CONFIG as C
from pipeline.attributes import Event, compute_confidence
from data.generate import BASE_TIME


def _detector_scores(events):
    """(A) C_i như bộ phát hiện tin giả yếu: AUC & AP của (1 - C_i) vs is_fake."""
    y_true = [1 if e.is_fake else 0 for e in events]
    y_score = [1.0 - e.confidence for e in events]  # càng ít tin cậy -> càng nghi giả
    n_fake = sum(y_true)
    if n_fake == 0 or n_fake == len(y_true):
        return {"auc": None, "ap": None, "n_fake": n_fake, "n_total": len(y_true)}
    return {
        "auc": round(float(roc_auc_score(y_true, y_score)), 4),
        "ap": round(float(average_precision_score(y_true, y_score)), 4),
        "n_fake": n_fake,
        "n_total": len(y_true),
        "mean_Ci_fake": round(sum(e.confidence for e in events if e.is_fake) / n_fake, 4),
        "mean_Ci_real": round(
            sum(e.confidence for e in events if not e.is_fake)
            / (len(events) - n_fake), 4),
    }


def _make_adversarial():
    """(B) Dựng tin giả đối kháng — tự chứa, không đụng dataset chính.

    Đặt ở một vùng biển/đồng trống cô lập (16.20N, 108.00E) để KHÔNG vô tình được
    báo cáo thật lân cận củng cố; mọi 'corroboration' phải do chính các tin giả
    tạo ra thì mới là corroboration GIẢ đúng nghĩa.
    """
    t0 = BASE_TIME + timedelta(minutes=30)
    lat0, lng0 = 16.20, 108.00
    adv: list[Event] = []

    # ADV_IMG: tin giả đơn lẻ nhưng CÓ ảnh (giả mạo bằng chứng thị giác)
    adv.append(Event("ADV_IMG", lat0, lng0, t0, 0.98, 0.98, 180, 0.0,
                     has_image=True, province="ADV",
                     note="đối kháng: tin giả có ảnh", gt_cluster=-1, is_fake=True))

    # ADV_CORR: 4 tin giả phối hợp SÁT NHAU (trong 400m/60ph) -> tự củng cố, KHÔNG ảnh
    for k in range(4):
        adv.append(Event(f"ADV_CORR_{k}", lat0 + 0.10 + k * 0.0005,
                         lng0 + 0.10 + k * 0.0005, t0 + timedelta(minutes=k * 5),
                         0.97, 0.95, 150, 0.0, has_image=False, province="ADV",
                         note="đối kháng: corroboration giả (phối hợp)",
                         gt_cluster=-1, is_fake=True))

    # ADV_BOTH: 4 tin giả phối hợp SÁT NHAU + CÓ ảnh (kịch bản xấu nhất)
    for k in range(4):
        adv.append(Event(f"ADV_BOTH_{k}", lat0 + 0.20 + k * 0.0005,
                         lng0 + 0.20 + k * 0.0005, t0 + timedelta(minutes=k * 5),
                         0.99, 0.97, 160, 0.0, has_image=True, province="ADV",
                         note="đối kháng: có ảnh + corroboration giả",
                         gt_cluster=-1, is_fake=True))
    return adv


def _adversarial_confidence(base_events):
    """Nhét tin giả đối kháng vào tập sự kiện rồi TÍNH LẠI C_i cho toàn bộ.

    Quan trọng: C_i phụ thuộc corroboration lân cận nên phải tính trên tập hợp
    nhất (tin giả đối kháng + toàn bộ dataset thật) để corroboration giả có cơ hội
    'ăn' — nhưng vì đặt ở vùng cô lập, chỉ các tin giả đối kháng củng cố lẫn nhau.
    """
    adv = _make_adversarial()
    combined = base_events + adv
    compute_confidence(combined, C.confidence)   # tính lại C_i trên tập gộp
    ci = {e.event_id: e.confidence for e in combined}

    # tham chiếu: tin giả ngây thơ S3_FAKE và trung bình báo cáo thật
    s3 = ci.get("S3_FAKE")
    real_mean = (sum(e.confidence for e in combined if not e.is_fake)
                 / sum(1 for e in combined if not e.is_fake))

    rows = [
        {"report": "S3_FAKE (giả ngây thơ: cô lập, ko ảnh)", "Ci": round(s3, 4)
         if s3 else None, "note": "tham chiếu baseline"},
        {"report": "ADV_IMG (giả + có ảnh)", "Ci": round(ci["ADV_IMG"], 4),
         "note": "ảnh đẩy C_i lên"},
        {"report": "ADV_CORR_0 (giả + corroboration giả)",
         "Ci": round(ci["ADV_CORR_0"], 4), "note": "phối hợp đẩy C_i lên"},
        {"report": "ADV_BOTH_0 (giả + ảnh + corroboration)",
         "Ci": round(ci["ADV_BOTH_0"], 4), "note": "xấu nhất"},
        {"report": "TB báo cáo THẬT", "Ci": round(real_mean, 4),
         "note": "mốc để so"},
    ]
    return rows, {
        "Ci_S3_naive_fake": round(s3, 4) if s3 else None,
        "Ci_ADV_IMG": round(ci["ADV_IMG"], 4),
        "Ci_ADV_CORR": round(ci["ADV_CORR_0"], 4),
        "Ci_ADV_BOTH": round(ci["ADV_BOTH_0"], 4),
        "Ci_real_mean": round(real_mean, 4),
    }


def main():
    events = prepared_events()

    det = _detector_scores(events)
    print_table("A. C_i như bộ phát hiện tin giả yếu (trên dataset chính)", [det])

    adv_rows, adv_summary = _adversarial_confidence(prepared_events())
    print_table("B. C_i dưới tin giả ĐỐI KHÁNG (có ảnh / corroboration giả)", adv_rows)
    print("\nDiễn giải: heuristic C_i MẠNH với tin giả ngây thơ (S3 thấp), nhưng "
          "adversary tạo ảnh giả hoặc phối hợp nhiều tin sẽ NÂNG được C_i — "
          "đây là giới hạn thật của heuristic nhẹ, cần mô hình tin cậy học từ "
          "lịch sử/định danh người dùng để chống (hướng mở rộng).")

    out = {
        "detector": det,
        "adversarial": adv_summary,
        "adversarial_detail": adv_rows,
    }
    save_table("exp8_confidence_detector.json", [out])
    print("\n[saved] exp8_confidence_detector.json -> results/tables/")


if __name__ == "__main__":
    main()
