
---

# VÒNG 2 — GIẢI QUYẾT (2026-07-24)

## E1 — Lập luận Exp9

**Thừa nhận:** Đúng, tự mâu thuẫn. So sánh tổng-spread sai hướng.
**Giải pháp:** Viết lại đoạn theo đúng số liệu JSON: tách 2 loại lỗi ARI làm mờ — (i) đầu thấp: Spectral completeness 0,595; (ii) nhóm đỉnh: 4 leader trong 0,002 ARI nhưng HDBSCAN completeness 0,929 vs Louvain 1,0 (gap 0,07). Đưa ARI spread 0,55 vào ngoặc, nói rõ nó "dồn ở đầu thấp nên không tách được nhóm đỉnh".

```diff
# paper/main.tex (Exp9) + BaiBao_NoiDung.md (§5.10)
- ...versus an ARI spread of only 0.55 concentrated at the low end, so the triad ranks the top methods...
+ It exposes two failures ARI blurs. First, at the low end, Spectral fragments events (completeness 0.595)...
+ Second, among the four leaders within 0.002 ARI, completeness still separates them: Louvain/Leiden/Agg 1.0
+ while HDBSCAN drops to 0.929... (The full-range ARI spread of 0.55 is real but sits entirely at the low end
+ —Spectral 0.339, K-Means 0.688—so it cannot rank the leaders.)
```
Số dùng: completeness Louvain/Leiden/Agg=1,0; HDBSCAN=0,9285; Spectral=0,5947; ari_spread=0,5528; completeness_spread=0,4053 (khớp `exp9_discriminative_metric.json`).

## E2 — Kích thước gói

**Thừa nhận:** Đúng, lệch một bậc. Đã đo 100–111 byte thì "few-KB" là phóng đại.
**Giải pháp:** Chuẩn hóa mọi mô tả gói *của hệ thống ta* về "sub-kilobyte" (EN) / "dưới 1 KB" (VN); Related-Work mô tả Edge AI nói chung giữ "few-KB". Thêm cross-ref từ Related Work tới Discussion (`\ref{sec:discussion}`) nơi có con số đo.

```diff
# paper/main.tex: abstract, contribution list, attribute-vector line
- a few-kilobyte metadata packet / (a few KB)
+ a sub-kilobyte metadata packet / (sub-kilobyte; quantified in Sect. Discussion)

# BaiBao_NoiDung.md dòng 9, 23, 113
- vài Kilobyte / vài KB   →  + dưới 1 Kilobyte / dưới 1 KB
```

## E3 — Làm tròn τ (VN)

**Thừa nhận:** Đúng.
**Giải pháp:** `BaiBao_NoiDung.md` dòng 258: "0,983" → "0,9829" cho khớp §5.8 và bản EN.

## E4 — Framing ARI 6 vs 27 cụm

**Thừa nhận:** Đúng, cần làm rõ để tránh hiểu nhầm. Đây là điểm subagent kiểm chứng: ARI bit-identical vì `metrics.py` mask noise (`gt<0`) trước khi tính.
**Giải pháp:** Thêm một câu giải thích vào mục 1A (cả EN & VN): khác biệt 6↔27 cụm nằm ở các điểm nhiễu xa mà gating cô lập thành singleton; các điểm này bị loại khỏi ARI/NMI theo ground-truth, nên hai chế độ trùng ARI *do thiết kế* — lợi ích của gating là đường kính & cô lập nhiễu, không phải ARI.

```diff
# paper/main.tex (1A) + BaiBao_NoiDung.md (§5.2, 1A)
+ The identical ARI is by construction: the two forms partition the 264 ground-truth-labeled
+ events identically; they differ only on the 21 far-flung noise points, which gating isolates
+ as singletons (6 vs 27 total clusters) and which the label-masked ARI/NMI ignore. Gating's
+ benefit is thus spatial tightness and noise isolation, not an ARI gain.
```

## KIỂM CHỨNG VÒNG 2
- `xelatex`: **19 trang, 0 undefined refs, 0 bibtex warnings** (cross-ref `sec:discussion` mới đã resolve).
- Mọi số thay thế lấy từ `exp9_discriminative_metric.json` + phân bố gt xác minh bằng chạy `generate.py` (264 nhãn + 21 nhiễu = 285).
- **No-hallucination:** E4 dựa trên kiểm chứng 0/34.716 cặp lệch giữa 2 phân hoạch (subagent + tự chạy lại), không suy diễn.
