# KẾ HOẠCH GIẢI QUYẾT (RESOLUTION PLAN)

> Vai trò: tác giả (giữ tính khách quan), trả lời từng chất vấn ở `review_report.md`.
> Nguyên tắc chủ đạo: **mọi con số sửa đổi phải dẫn xuất từ việc chạy chính code của demo**, không tự nghĩ ra.
> Trạng thái: TẤT CẢ đã thực thi (Bước 3). File này ghi lại lập luận + diff.

---

## A1 — Khoảng cách S1

**Thừa nhận:** Đúng. Ba nhãn mâu thuẫn; tọa độ là nguồn sự thật duy nhất.
**Giải pháp:** Chạy hàm `haversine` của demo trên đúng tọa độ → 102,84 km → chuẩn hóa **tất cả** thành "~103 km".

```diff
# paper/main.tex (dòng 224)
- S1: two rooftop-flood points $\sim$90\,km apart
+ S1: two rooftop-flood points $\sim$103\,km apart

# resource/BaiBao_NoiDung.md
- S1 ... ~90 km
+ S1 ... ~103 km

# demo/data/generate.py (docstring + 2 comment): 40km / 90km → 103km
# Tọa độ GIỮ NGUYÊN — chỉ sửa nhãn mô tả.
```

## A2 — Kích thước gói

**Thừa nhận:** Đúng. Con số 112–137 vô căn cứ, phải đo lại bằng script tái lập.
**Giải pháp:** Viết `demo/experiments/exp10_packet_size.py` đo gói JSON tối thiểu xác định (id, tọa độ, epoch, các trường L,T,F,E,N,V,C) trên cả 285 sự kiện → **100–111 byte** (min/median/max, đã strip whitespace). Đăng ký vào `run_all.py`.

```diff
# paper/main.tex (dòng 382)
- measures only \emph{112--137 bytes}
+ measures a deterministic \emph{100--111 bytes} across all 285 events
+   (min/median/max, whitespace-stripped)

# resource/BaiBao_NoiDung.md
- 112 byte (137 byte...)
+ dải đo được xác định 100–111 byte
```
Output exp10: `{n_events: 285, min: 100, median: 110, max: 111}`.

## B1 — Trích dẫn baseline

**Thừa nhận:** Đúng, khe hở trích dẫn.
**Giải pháp:** Thêm `\cite` tại lần đề cập đầu của mỗi baseline.

```diff
# paper/main.tex (dòng 312)
- Spectral clustering, HDBSCAN, Agglomerative
+ Spectral clustering~\cite{vonluxburg2007spectral}, HDBSCAN~\cite{campello2013hdbscan}, Agglomerative
```

## C1 — Số hình (VN)

**Thừa nhận:** Đúng. Thực tế có 7 hình.
**Giải pháp:**
```diff
# resource/BaiBao_NoiDung.md (dòng 482)
- nhúng 6 hình từ demo/v2/results/figures/
+ nhúng 7 hình từ demo/results/figures/
```

## C2 — Làm tròn ARI (VN)

**Thừa nhận:** Đúng.
**Giải pháp:** Chuẩn hóa abstract về "0,892" khớp thân bài và bản tiếng Anh (0.892 xuyên suốt).

## C3 — Banner run_all.py

**Thừa nhận:** Đúng.
**Giải pháp:** Đăng ký exp10 làm bước 11; chuẩn hóa mọi banner về `/13` (generate → exp1..exp10 → make_figures → dashboard = 13 bước).

## D1 — Engine biên dịch

**Thừa nhận:** Đúng, ghi nhớ "pdflatex build" đã lỗi thời.
**Giải pháp:** Xác nhận `xelatex` là engine chính thức. Kết quả: 19 trang, 0 undefined refs, 0 bibtex warnings.

---

## KIỂM CHỨNG CUỐI CÙNG

- `xelatex`: 19 trang, **0 undefined refs, 0 bibtex warnings**.
- Đối chiếu số học paper ↔ demo JSON: **toàn bộ headline khớp** — ARI 0,892; đường kính 100,07 → 0,30 km; Spectral 0,339 / HDBSCAN 0,890@25km / K-Means 0,688 / DBSCAN 0,730; Kendall's τ 0,994–0,957; exp6 τ 0,9829; exp7 10,43%; exp8 AUC 0,9651.
- Grep nhất quán VN cuối: không còn nhãn cũ, đường dẫn `demo/v2/`, hay làm tròn lỏng.
- **Ràng buộc no-hallucination:** mọi con số sửa đều từ chạy code demo (haversine → 103 km; exp10 → 100–111 byte).
