# BÁO CÁO PHẢN BIỆN KHOA HỌC — VÒNG 3 (CRITICAL REVIEW)

> Vai trò: Giáo sư chủ tịch hội đồng phản biện.
> Phạm vi: `paper/main.tex`, `resource/BaiBao_NoiDung.md`, mã + JSON trong `demo/`.
> Ngày: 2026-07-24.
> Nguyên tắc: chỉ nêu lỗi **thực sự tồn tại**, mỗi lỗi kèm bằng chứng chạy được. Vòng 1 dọn lỗi bề mặt; vòng 2 dọn lỗi logic/nhất quán. Vòng 3 soi tầng **cấu trúc ground-truth** và các tuyên bố định lượng còn sót.

---

## F. LỖI NGHIÊM TRỌNG — SAI CẤU TRÚC GROUND-TRUTH & QUY KẾT SAI NGUYÊN NHÂN ARI

### F1. "6 ốc đảo" và "264 điểm gom thành 6 nhóm" là SAI; nguyên nhân ARon = 0,892 bị quy kết nhầm

- **Hiện trạng (paper EN dòng 224, 234; BaiBao §5.1 dòng 282, §5.2 (1A) dòng 305):**
  - Mô tả bộ dữ liệu: "240 core events around **6 flood islands**".
  - Giải thích (1A) — chính là phần vòng 2 vừa thêm vào: *"both forms partition the **264** ground-truth-labeled events **identically into the 6 island groups**; they differ only in how they treat the 21 unlabeled noise/fake points... this difference is invisible to [ARI/NMI]."* Ngụ ý: nếu không vì 21 điểm nhiễu thì ARI sẽ là 1,0.

- **Bằng chứng (chạy trực tiếp trên `demo/data/generate.py` + `pipeline`):**
  - Nhãn ground-truth phân biệt (bỏ −1): `[0,1,2,3,4,5, 100,101,102,103,104,105]` → **12 nhãn**, KHÔNG phải 6.
  - Kích thước: `{0..5: 40 mỗi cụm}` (240 lõi) + `{100:1, 101:1, 102:5, 103:4, 104:10, 105:3}` (24 điểm narrative) + `{-1: 21}` (nhiễu). Tổng nhãn hợp lệ = **264 = 240 + 24** trải trên **12 nhãn**.
  - 24 điểm narrative (nhãn 100–105) nằm ĐÚNG tại tâm 6 ốc đảo: đo haversine tới tâm gần nhất = **0,0 m** cho cả 6 nhóm (S1_A ≡ tâm đảo 0 Huế; S1_B ≡ tâm đảo 2 Hội An; S2 ≡ đảo 1; S3 ≡ đảo 3; S4A ≡ đảo 4; S4B ≡ đảo 5).
  - Phân rã ARI (cả additive lẫn gating cho kết quả như nhau):
    - **ARI chỉ-lõi (240 điểm, nhãn 0–5) = 1,0**
    - **ARI chỉ-narrative (24 điểm, nhãn 100–105) = 1,0**
    - **ARI toàn-bộ-có-nhãn (264 điểm, 12 nhãn) = 0,892**

- **Chất vấn (gay gắt):**
  1. *Bộ dữ liệu có 6 hay 12 nhóm ground-truth?* Văn bản khẳng định "6 island groups" và "264 gom thành 6 nhóm" — SAI trên hai mặt: có 12 nhãn, và 264 điểm KHÔNG gom về 6 nhóm.
  2. *Tại sao ARI = 0,892 mà không phải 1,0?* Vòng 2 quy cho "21 điểm nhiễu bị mask" — **SAI**. Nhiễu (gt = −1) bị `metrics.py` mask *trước* khi tính ARI nên **không hề ảnh hưởng ARI**. Con số 0,892 (thay vì 1,0) sinh ra HOÀN TOÀN vì 24 điểm narrative đặt chồng lên tâm ốc đảo nhưng mang nhãn khác: mọi thuật toán phân cụm không gian buộc phải gộp một điểm ở 0 m vào ốc đảo chủ, và ground-truth gán nhãn khác nên bị tính là "bất đồng". Bằng chứng đóng đinh: ARI chỉ-lõi = 1,0.
  3. Hệ quả: tuyên bố "gating không hy sinh độ chính xác" vẫn ĐÚNG, nhưng **lời giải thích cơ chế đang sai** — một hội đồng đọc kỹ sẽ phát hiện mâu thuẫn giữa "264 → 6 nhóm" và bảng nhãn thật. Đây là lỗi định lượng + phương pháp luận, nặng ngang nhóm A của vòng 1.

- **Điểm tích cực bị bỏ lỡ:** ARI lõi = 1,0 là kết quả MẠNH HƠN cho phương pháp, hiện đang bị con số tổng 0,892 che mất. Sửa đúng vừa chính xác hơn vừa có lợi cho bài.

---

## G. LỖI TUYÊN BỐ ĐỊNH LƯỢNG (nhất quán số liệu)

### G1. Abstract & Kết luận: "Kendall's τ ≥ 0,94" MẠNH HƠN dữ liệu cho phép

- **Hiện trạng:** Abstract (EN dòng 43) và Conclusion (dòng 394) viết *"Kendall's $\tau \ge 0.94$ under $\pm0.10$"*. BaiBao dòng 9 & 421 tương tự ("τ ≥ 0,94 ở ±0,10").
- **Bằng chứng (`exp5_ranking_stability.json`):** ở mức ±0,10, `mean_kendall_tau = 0,9857` nhưng `min_kendall_tau = 0,9373`. Chính bảng 5 và caption Fig. 7 trong bài lại ghi "τ stays above 0.93" và min = 0,937.
- **Chất vấn:** τ ≥ 0,94 là **sai** như một chặn cứng (min = 0,937 < 0,94). Abstract đang phát biểu chặn mạnh hơn số liệu. Phải nói rõ *"mean"* (τ trung bình ≥ 0,94 — đúng ở mọi mức: 0,994/0,986/0,957) hoặc hạ về "τ ≥ 0,93".

### G2. "~40% tin giả" lệch so với tỉ lệ thực hiện

- **Hiện trạng:** BaiBao §5.1 dòng 283 & Paper.md dòng 283: "20 sự kiện nhiễu... khoảng **40%** là tin giả".
- **Bằng chứng:** trong 20 điểm nhiễu `NZ*`, số `is_fake=True` thực tế = **5** (`NZ011, NZ012, NZ015, NZ017, NZ019`) = **25%**, không phải 40%. Con số 40% chỉ là *tham số xác suất* `rng.random() < 0.4` khi sinh, không phải tỉ lệ hiện thực. (Tổng tin giả toàn tập = 6 do thêm `S3_FAKE`, khớp `exp8` `n_fake=6`.)
- **Chất vấn:** Mô tả bộ dữ liệu phải phản ánh tập ĐÃ SINH (tất định, seed=42), không phải kỳ vọng tham số. Sửa "~40%" → "sinh với xác suất 40% (thực tế 5/20 = 25%)" hoặc nêu thẳng "6 tin giả trên toàn tập".

---

## TÓM TẮT MỨC ĐỘ — VÒNG 3

| Mã | Lỗi | Mức độ |
|----|-----|--------|
| F1 | Sai số nhóm GT (6 vs 12); quy kết sai nguyên nhân ARI 0,892 | **Nghiêm trọng** (định lượng + phương pháp) |
| G1 | Abstract/Kết luận "τ ≥ 0,94" > dữ liệu (min 0,937) | Trung bình |
| G2 | "~40% tin giả" ≠ thực hiện (25%) | Nhẹ |

**Ghi chú tái lập:** mọi con số F1/G1/G2 được xác minh bằng cách chạy lại `data/generate.py` + `pipeline` và đọc `exp5_ranking_stability.json`, `exp8_confidence_detector.json`. Không suy diễn.
