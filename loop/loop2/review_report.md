
---

# VÒNG 2 — SOI SÂU LỚP LOGIC / NHẤT QUÁN (2026-07-24)

> Vòng 1 dọn lỗi bề mặt (khoảng cách, kích thước gói, trích dẫn, đếm hình). Vòng 2 soi tầng lập luận & nhất quán liên-mục. Mọi lỗi kèm bằng chứng từ JSON/code demo (đã chạy xác minh).

## E. LỖI LOGIC / LẬP LUẬN (nghiêm trọng)

### E1. Mâu thuẫn nội tại trong lập luận Thí nghiệm 9
- **Hiện trạng (paper cũ):** "completeness far more discriminative... versus an ARI spread of **only** $0.55$".
- **Bằng chứng:** `exp9_discriminative_metric.json`: `ari_spread=0.5528`, `completeness_spread=0.4053`. Tức **ARI spread (0,55) LỚN HƠN completeness spread (0,405)**.
- **Chất vấn:** Không thể gọi 0,55 là "chỉ/only" để chứng minh completeness phân biệt tốt hơn, khi 0,55 > 0,405. So sánh tổng-spread là **sai hướng**. Lập luận đúng: ARI spread dồn hết ở đầu thấp (Spectral 0,339; K-Means 0,688), nên 4 phương pháp *đỉnh* gần như hòa (chênh ≤0,002 ARI); completeness mới tách được nhóm đỉnh đó (HDBSCAN 0,929 vs Louvain 1,0 = gap 0,07). Mệnh đề "near-tie candidates having ARI within 0.003" còn bị gắn nhầm ngữ pháp vào Spectral (ARI 0,339 — KHÔNG near-tie).

## E2. Lệch một bậc độ lớn: "few-kilobyte" vs "100–111 byte"
- **Hiện trạng:** Abstract + Intro nói gói metadata "few-kilobyte"; Discussion đo được **100–111 byte** (sub-KB). Chênh ~1 bậc.
- **Chất vấn:** Gói là vài KB hay ~100 byte? Cùng một đối tượng, hai con số vênh nhau. Phải thống nhất về "sub-kilobyte".

## E3. Làm tròn Kendall's τ không nhất quán (bản VN)
- **Hiện trạng:** `BaiBao_NoiDung.md` dòng 258 ghi exp6 "τ = 0,983", dòng 371 (và bản EN) ghi "0,9829".
- **Chất vấn:** Cùng con số, hai độ chính xác.

## E4. Framing gây hiểu nhầm: "6 cụm vs 27 cụm cùng ARI 0,892"
- **Hiện trạng:** Bảng 1A nêu additive=6 cụm, gating=27 cụm, ARI y hệt — nhưng KHÔNG giải thích tại sao thay đổi lớn về số cụm lại cho ARI bit-identical.
- **Bằng chứng (đã chạy):** `metrics.py` mask `gt<0` (21 điểm nhiễu) TRƯỚC khi tính ARI. Phân bố gt: 6 island×40 + narrative(24 điểm, gt 100–105 nhưng đặt trùng tọa độ 6 tâm cũ) + 21 noise. Cả hai chế độ cho **phân hoạch y hệt trên 264 điểm có nhãn** (0/34.716 cặp lệch). Khác biệt 6↔27 hoàn toàn nằm ở 21 điểm nhiễu (gating cô lập thành singleton) — vô hình với ARI vì đã bị mask.
- **Chất vấn:** Phải nói rõ ARI-bằng-nhau là *do thiết kế* (noise bị loại khỏi metric), tránh để người đọc tưởng đây là trùng hợp hoặc lỗi copy-paste. Lợi ích của gating là **đường kính & cô lập nhiễu**, KHÔNG phải cải thiện ARI.

## TÓM TẮT VÒNG 2
| Nhóm | Số lỗi | Mức độ |
|------|--------|--------|
| E1 logic Exp9 | 1 | Nghiêm trọng (tự mâu thuẫn) |
| E2 lệch bậc độ lớn | 1 | Trung bình (nhất quán số liệu) |
| E3 làm tròn τ (VN) | 1 | Nhẹ |
| E4 framing ARI | 1 | Trung bình (dễ gây hiểu nhầm) |
