# Loop 5 — Báo cáo Phản biện (Step 1)

**Vai trò:** Chủ tịch hội đồng phản biện — Toán / Công nghệ / Kỹ thuật.
**Phạm vi:** `@paper` (main.tex, references.bib), `@resource` (BaiBao_NoiDung.md, Paper.md), đối chiếu `@demo` (code + results).
**Nguyên tắc:** No hallucination — mọi con số phải truy về output demo hoặc tính trực tiếp. Công thức dùng LaTeX.

Sau 4 vòng lặp trước, các lỗi vĩ mô (miền giá trị công thức, citation bịa, xref, faithfulness code) đã được xử lý. Vòng 5 đào sâu vào **tính nhất quán của độ đo (metric)** và **các phát biểu định lượng vi mô** — nơi dễ có lỗi tinh vi mà 4 vòng trước bỏ sót.

---

## PHÁT HIỆN 5.1 — [ĐÃ XÁC NHẬN, NGHIÊM TRỌNG] Sai số liệu trong Paper.md: "Spectral chỉ cách 0,003"

**Vị trí:** `resource/Paper.md` dòng 211 (mục tóm tắt Thí nghiệm 9).

**Câu sai (nguyên văn trước sửa):**
> "Spectral, dù ARI **chỉ cách nhóm gần-hòa 0,003**, bị phơi bày với completeness chỉ 0,595…"

**Chất vấn:** ARI của Spectral là bao nhiêu, và cách nhóm dẫn đầu (ARI ~0,892) bao xa?

**Bằng chứng (demo `exp9_discriminative_metric.json`):**
- Spectral (gating): ARI = **0,3392**
- Nhóm dẫn đầu: Louvain/Leiden/Agglomerative = 0,892; HDBSCAN = 0,8903
- Khoảng cách thực: $0{,}892 - 0{,}339 = 0{,}553$ — **KHÔNG phải 0,003**.

Con số "0,003" hoàn toàn sai (lệch ~180 lần). Nó mâu thuẫn nội bộ ngay trong cùng câu, vì câu này dùng Spectral làm ví dụ "đầu THẤP" của bảng. main.tex (dòng 382) và BaiBao (dòng 390) đều mô tả đúng (Spectral 0,339, ở đầu thấp). Chỉ Paper.md — bản Việt cũ — mang lỗi này.

**Mức độ:** Nghiêm trọng (sai dữ kiện định lượng, tự mâu thuẫn). → Sửa ngay.

---

## PHÁT HIỆN 5.2 — [ĐÃ XÁC NHẬN, VỪA] NMI và V-measure là CÙNG một đại lượng — trình bày như hai độ đo độc lập

**Vị trí:**
- `paper/main.tex` dòng 381 (tiêu đề mục 9: *"A Discriminative Metric Beyond ARI"*), dòng 382 (*"We add the homogeneity/completeness/V-measure triad … We therefore report V-measure alongside ARI throughout"*).
- Bảng `tab:gating` (dòng 243–246) và `tab:baselines` (dòng 323–329) báo cáo cột **NMI** = 0,927.
- exp9 báo cáo **V-measure** = 0,927 cho Louvain.
- BaiBao dòng 390 & 423; Paper.md dòng 211.

**Chất vấn:** Thí nghiệm 9 tuyên bố "bổ sung một độ đo phân biệt HƠN ARI" và "báo cáo V-measure kèm ARI xuyên suốt". Nhưng NMI đã được báo cáo ở mọi bảng. **V-measure có phải là một độ đo MỚI, hay chỉ là NMI đội tên khác?**

**Bằng chứng (chứng minh trực tiếp trong `.venv` sklearn):**
```
n=173  NMI(arith)=0.043131  Vmeasure=0.043131  hcv_v=0.043131  equal=True
n= 52  NMI(arith)=0.159980  Vmeasure=0.159980  equal=True
... (5/5 test đều bằng nhau tuyệt đối)
import: sklearn.metrics.cluster._supervised (cùng một module cho cả hai)
```
Về mặt toán học, với `average_method='arithmetic'` (mặc định của sklearn):
$$\text{NMI}_{\text{arith}}(U,V)=\frac{2\,I(U;V)}{H(U)+H(V)}=\text{V-measure}(U,V)$$
Đây là **định nghĩa đồng nhất**, không phải trùng hợp số. Kiểm tra `metrics.py` dòng 22: dùng `normalized_mutual_info_score(...)` không truyền `average_method` → mặc định arithmetic. Vậy **NMI mà cả paper báo cáo (0,927) CHÍNH LÀ V-measure (0,927)**. HDBSCAN xác nhận: NMI 0,922 = V-measure 0,9219.

**Hệ quả:** Câu chữ của mục 9 phóng đại đóng góp. V-measure **không** là "độ đo vượt trên ARI" mới — nó bằng NMI đã in ở mọi bảng. Sức phân biệt thực sự mà exp9 chứng minh đến từ việc **phân rã** NMI/V-measure thành hai trục **homogeneity** và **completeness** riêng lẻ (đặc biệt completeness: Louvain 1,0 vs HDBSCAN 0,929 — tách được nhóm mà ARI gộp). Chính docstring và phần print của `exp9_discriminative_metric.py` (dòng 91–99) đã trung thực nói điều này (độ trải completeness 0,405 mới là cái tách mạnh); chỉ phần văn xuôi trong paper là diễn đạt lệch.

**Mức độ:** Vừa (không sai số, nhưng overclaim về tính mới của độ đo — một phản biện sắc sẽ chỉ ra ngay "V-measure = NMI của anh"). → Sửa câu chữ để (a) nói rõ V-measure ≡ NMI đã báo cáo, (b) quy công lao phân biệt cho completeness/homogeneity.

---

## CÁC KIỂM TRA ĐÃ QUA (không phát hiện lỗi — ghi để minh bạch)

| Phát biểu trong paper | Giá trị demo | Kết luận |
|---|---|---|
| Phantom population −55% | `exp1_E`: reduction_pct = 55.0 | ✔ khớp |
| exp7 vulnerability +10,4% | `exp7`: 10.43% | ✔ khớp (làm tròn) |
| exp7 additive nhanh hơn (133,3 vs 146,5) | 133,27 vs 146,5 | ✔ đã tự công bố trong main.tex dòng 376 |
| ROC-AUC bộ phát hiện 0,9651 | `exp8`: auc 0.9651 | ✔ khớp |
| Kendall τ ±0,10: mean 0,99 / min 0,94 | `exp5`: 0,9857 / 0,9373 | ✔ khớp (làm tròn) |
| completeness gap 0,07 (Louvain 1,0 vs HDBSCAN 0,929) | 1,0 vs 0,9285 → 0,0715 | ✔ khớp |
| "within 0,002 ARI" nhóm dẫn đầu | max−min = 0,892−0,8903 = 0,0017 | ✔ làm tròn thành 0,002 |
| Packet size 100–111 bytes | (đã xác minh vòng trước) | ✔ |

Không tìm thấy thêm lỗi số học hay dữ liệu ở các thí nghiệm còn lại.

---

## TỔNG KẾT STEP 1

- **5.1** — lỗi số liệu thực (Spectral "0,003") trong Paper.md → **sửa ngay**.
- **5.2** — overclaim độ đo (V-measure trình bày như mới, thực chất ≡ NMI đã báo cáo) → **sửa câu chữ ở main.tex, BaiBao, Paper.md**; quy tính phân biệt cho completeness/homogeneity.

Các con số headline khác đều đã kiểm và nhất quán với demo. Vòng 5 hội tụ về hai vấn đề trên.
