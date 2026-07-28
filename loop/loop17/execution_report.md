# Loop 17 — Báo cáo thực thi `plan.md`

Ngày chốt: 28/07/2026.

## Kết luận

Đường găng P0–P6 và toàn bộ hạng mục có thể thực hiện từ workspace đã hoàn tất.
Hai đầu vào bên ngoài còn thiếu là ORCID thật của sáu tác giả và tập dữ liệu lũ
thật cho sanity check P1.5; không giá trị nào được tự suy đoán.

## Kết quả theo pha

| Pha | Kết quả |
|---|---|
| P0 | Thay đóng góp “cửa sổ ngưỡng” bằng Bổ đề định vị: cạnh dạng nhân sau ngưỡng có `d < σ√(2 ln(1/θ))`; bổ sung cận đường kính theo số cạnh đường đi và nêu đúng giới hạn của dạng cộng. |
| P1 | Sinh dataset v3 gồm 485 báo cáo, 421 báo cáo lõi có nhãn, 60 nhiễu và chiến dịch giả 4 báo cáo; 13 sự kiện vật lý; 39 báo cáo giả, 26/39 nằm trong vùng sự kiện. |
| P1 gates | K-Means tọa độ ARI 0.6304; Agglomerative Haversine 0.4120; bỏ context giảm ARI 0.1740; sweep context có range 0.0706; AUC đặc trưng đơn tối đa 0.6903; tỷ lệ fake trong vùng sự kiện 0.667. Tất cả đạt ngưỡng đăng ký trước. |
| P2 | Sửa quy ước đường kính theo cụm chứa nhãn; thêm kiểm tra có điều kiện cho confidence; dùng `N_ref=500` tĩnh và chặn chuẩn hóa dân số ở 1; thống kê dùng bootstrap CI ghép cặp và Wilcoxon. |
| P3 | Chạy lại toàn bộ generator, Exp0–Exp13, tạo 8 hình và dashboard; 17/17 bước thành công. |
| P4 | Bổ sung và định vị với bilateral/product kernels, ClustGeo/regionalization và equity trong humanitarian logistics; dạng cộng được ghi là controlled ablation tự dựng. |
| P5 | Viết lại `paper/main.tex`, rút Edge AI khỏi tiêu đề/abstract/đóng góp, đưa đủ 8 hình vào bài, chuẩn hóa giọng văn và giới hạn kết luận. |
| P6 | `verify_figures.py` đạt; XeLaTeX–BibTeX–XeLaTeX×2 đạt; PDF 12 trang; 0 lỗi, 0 float-too-large, 0 overfull >5 pt và 0 tham chiếu thiếu. |

## Các lệnh xác minh cuối

```text
env MPLCONFIGDIR=/tmp/nckh2-mpl demo/.venv/bin/python demo/run_all.py
env MPLCONFIGDIR=/tmp/nckh2-mpl demo/.venv/bin/python demo/verify_figures.py
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

`run_all.py` hoàn tất 17/17 bước. Bản biên dịch cuối tạo `paper/main.pdf` 12
trang. Log còn một overfull 0.44897 pt và một underfull vbox; cả hai dưới cửa
chặn của kế hoạch, không có float quá khổ hay tham chiếu chưa giải quyết.

## Hạng mục cần tác giả cung cấp

1. ORCID thật của sáu tác giả. Không có ORCID nào trong workspace ngoài chuỗi
   ví dụ của template LNCS.
2. Dữ liệu lũ thực có tọa độ và thời gian nếu muốn hoàn thành sanity check P1.5.
3. Nếu hệ thống nộp bắt buộc pdfLaTeX, cài gói mã hóa/font tiếng Việt `T5`.
   Workspace hiện tại biên dịch đúng Unicode bằng XeLaTeX.
