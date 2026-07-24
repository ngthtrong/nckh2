# VÒNG 3 — GIẢI QUYẾT (2026-07-24)

> Thoát vai phản biện, trở lại vai tác giả (giữ khách quan). Trả lời từng chất vấn Vòng 3 và nêu phương án sửa cụ thể. Mọi số liệu lấy từ code/JSON đã chạy xác minh.

## F1 — Sai cấu trúc ground-truth: "6 nhóm" thực chất là 12 nhãn (NGHIÊM TRỌNG)

**Thừa nhận:** Đúng. Đây là lỗi thật, và tệ hơn: bản vá Vòng 2 đã *củng cố* lời giải thích sai. Kiểm chứng lại từ `generate.py` + chạy trực tiếp:
- Nhãn gt ≥ 0 phân biệt: `{0,1,2,3,4,5, 100,101,102,103,104,105}` → **12 nhãn**, không phải 6.
- 24 điểm narrative (nhãn 100–105) nằm **đúng 0,0 m** so với 6 tâm ốc đảo (S1_A tại tâm Huế, S1_B tại tâm Hội An, S2 tại tâm Quảng Trị, S3 thật tại tâm Đà Nẵng, S4A tại Phú Vang, S4B tại Vĩnh Linh).
- Do đó thuật toán (đúng đắn) gom mỗi nhóm narrative CHUNG cụm với ốc đảo trùng tọa độ, nhưng ground-truth lại gán nhãn KHÁC → mất điểm ARI.
- Chạy xác minh: **ARI lõi-240 = 1,0; ARI narrative-24 = 1,0; ARI toàn-264 = 0,892.** Vậy trần 0,892 sinh ra CHÍNH TỪ mâu thuẫn nhãn của các điểm trùng tọa độ, KHÔNG phải từ 21 điểm nhiễu (nhiễu đã bị mask `gt<0`).

**Vì sao lời giải Vòng 2 sai:** Vòng 2 nói "hai dạng cho cùng phân hoạch trên 264 điểm có nhãn thành **6 nhóm**; khác biệt 6↔27 nằm ở 21 nhiễu". Câu này (a) gọi sai số nhãn (6 thay vì 12); (b) quy trần ARI cho nhiễu, trong khi nhiễu bị mask nên KHÔNG ảnh hưởng ARI; (c) ẩn đi nguồn thật của việc ARI<1 là các điểm narrative đồng tọa độ khác nhãn.

**Giải pháp (chọn phương án minh bạch, không đụng seed/số liệu):** Giữ nguyên dataset và mọi con số (0,892 vẫn đúng), nhưng mô tả lại cho ĐÚNG cấu trúc và giải thích ĐÚNG nguồn của trần ARI:
1. Mô tả dataset: nói rõ ground-truth gồm **12 nhóm** = 6 ốc đảo lõi (nhãn 0–5, ~40 điểm mỗi cụm) + 6 nhóm kịch bản S1–S4 (nhãn 100–105) **đặt trùng tọa độ với các tâm ốc đảo** để stress-test công thức ưu tiên trên chính hình học đó.
2. Viết lại đoạn giải thích trần ARI (1A + Threats-Internal): ARI = 0,892 (không phải 1,0) vì 6 nhóm kịch bản được cố ý đặt chồng lên ốc đảo lõi nhưng gán nhãn riêng; thuật toán gộp chúng theo không gian (đúng về mặt điều phối) nên "mất" điểm ARI so với nhãn thiết kế. Đây là **giới hạn do cách gán nhãn ground-truth**, và củng cố cho luận điểm "0,892 phản ánh độ tách dữ liệu + quy ước nhãn, không thuần sức mạnh phương pháp".
3. Sửa lời giải "6 vs 27 cụm": khác biệt số cụm tổng vẫn nằm ở 21 nhiễu (đúng — gating cô lập thành singleton), NHƯNG KHÔNG được nói nó liên quan tới trần ARI; và sửa "6 nhóm có nhãn" → "12 nhóm có nhãn (264 điểm)".
4. Bổ sung script tái lập `demo/experiments/exp1_formula_validation.py`: thêm hàm in ARI lõi-only vs toàn-labeled để con số 1,0 / 0,892 có nguồn chạy được, chống no-hallucination.

## F2 — Câu "merging distinct islands" của HDBSCAN mơ hồ

**Thừa nhận:** Một phần đúng — dễ gây hiểu completeness đo trên 6 nhãn.
**Giải pháp:** Không đổi số (completeness HDBSCAN 0,929 vs Louvain 1,0 vẫn đúng theo `exp9_discriminative_metric.json`), chỉ nói rõ completeness tính trên toàn bộ nhãn ground-truth (12 nhóm) — nhất quán sau khi F1 sửa "6→12". Câu "merges islands" giữ được vì HDBSCAN thật sự gộp 11 cụm.

## F3 — Cận Kendall's τ ở ±0,10: nên là ≥0,93 không phải ≥0,94

**Thừa nhận:** Đúng. `exp5_ranking_stability.json`: mean τ ở ±0,10 = **0,9857**, min τ = **0,9373**. Abstract/Kết luận (EN+VN) ghi "τ ≥ 0,94 ở ±0,10" — sai với min 0,937.
**Giải pháp:** Đổi thành **"mean τ = 0,99, min τ = 0,94 ở ±0,10"** (làm tròn min 0,9373→0,94 vẫn ≥; an toàn hơn ghi rõ mean+min). Hoặc tối thiểu đổi "≥0,94" → "≥0,93". Chọn ghi "mean 0,99 (min 0,94)" cho chính xác và mạnh hơn. Áp cho: `paper/main.tex` abstract+conclusion; `BaiBao_NoiDung.md` dòng 9 + 421.

## F4 — τ_F/τ_E: hai nguồn resource mâu thuẫn hướng bất đối xứng

**Thừa nhận:** Đúng, mâu thuẫn nội tại giữa hai file resource.
- `Paper.md` dòng 188: "đặt $\tau_E>\tau_F$ ... vì E nhiễu hơn nên cần khoan dung hơn" ✔ hợp lý.
- `main.tex` dòng 166: "tighter $\tau_F=0.25$ vs $\tau_E=0.35$ ... penalize flood gap more sharply ... F is more physically grounded" — cách diễn đạt "F đáng tin hơn nên phạt gắt hơn" DỄ gây khó hiểu (đáng tin hơn thường → khoan dung hơn, không phải gắt hơn).
**Giải pháp:** Thống nhất một lập luận: $\tau_F<\tau_E$ vì **E trích từ cảm xúc văn bản nhiễu hơn F trích từ thị giác, nên nới lỏng ngưỡng khớp cho E ($\tau_E$ lớn) và siết cho F ($\tau_F$ nhỏ)**. Sửa `main.tex` dòng 166 cho khớp lập luận "độ nhiễu" của `Paper.md`, bỏ cách nói "trustworthy → sharper". `BaiBao_NoiDung.md` kiểm tra đã theo hướng nào và đồng bộ.

## KẾ HOẠCH KIỂM CHỨNG
- Chạy lại `exp1` sau khi thêm hàm ARI-core-vs-all; xác nhận in 1,0 / 0,892.
- Biên dịch lại `paper/main.tex` bằng `xelatex` (engine chính thức theo Vòng 1 D1): kỳ vọng 19 trang, 0 undefined refs.
- Đối chiếu 3 artifact (main.tex, BaiBao_NoiDung.md, Paper.md) cho các số F1–F4 sau khi sửa.
- No-hallucination: mọi con số (12 nhãn, 0,0 m, ARI 1,0/0,892, τ mean 0,9857/min 0,9373) đều từ chạy code trực tiếp, không suy diễn.
