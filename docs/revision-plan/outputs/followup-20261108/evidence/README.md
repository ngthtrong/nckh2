# Bổ sung bằng chứng P02/P05/P07 — 08/11/2026, Asia/Taipei

## Material Passport

- Scope: bounded evidence recovery and provenance audit, no new participant data or device/system measurements.
- Verification status: **ANALYZED**. No scientific campaign was reproduced.
- Inputs: existing image split/records/checkpoint/notebook, local refs and historical E2E narrative, official ISDS program PDF and publisher pages.
- Outputs: `local-evidence-audit.json`, `source-hashes.json`, `drive-receipt.json`, official program PDF/text/page22 render, and the dispositions below.
- Reproduce local audit: `python3 docs/revision-plan/outputs/followup-20261108/evidence/audit_local.py`.

## P02 — Có thêm truy vết, chưa có hồ sơ để đóng khoảng trống

Đã đối chiếu 1.702 dòng của split hiện tại với `seed1024/records_after_clean`: trùng đầy đủ trên tám trường relative_path, label, label_idx, MD5, source_group, dHash, perceptual_group và split_group. Split vẫn 1.189/257/256. **Cả 1.702 source_group đều trống**; đây không phải xác nhận độc lập theo sự kiện/nguồn.

Đã đọc metadata checkpoint best seed1024 bằng `zipfile` và `pickletools.genops`, **không thực thi unpickle**. Metadata chứa config seed1024 và khóa `split_csv_path` trỏ tới:

`/content/drive/MyDrive/Colab Notebooks/NCKH/models/mobilenetv3_large_dataset_v4/split_train_val_test_mobilenetv3_large.csv`.

Không tìm được checksum split lịch sử trong các chuỗi khóa metadata. Đường dẫn dùng chung chỉ liên kết ý định đọc split; không chứng minh bytes của split tại thời điểm train. Notebook hiện lưu output seed599 và thông báo thiếu `source_groups.csv`, không được dùng output này như training receipt của seed1024.

Không tìm được hồ sơ URL/license từng ảnh, người gán nhãn/IAA hoặc xác nhận chuyên gia dispatch trong nguồn đã kiểm. Không suy bản quyền/nguồn từ tên ảnh. Các trường này vẫn UNKNOWN/OPEN. Drive raw-name search Dataset_Flood_v4/source_groups/split_train_val_test/annotation/source_manifest không có hit phù hợp trong phạm vi quyền truy cập.

## P05 — Chưa khôi phục raw E2E

Mở rộng kiểm tra trước đây từ heads/remotes sang **31 ref local hiện có**, gồm tags/stash/Codex captures. Không có file raw phù hợp dưới results/logs/checkpoints/attempts của ba vùng experiment. Working tree, kể cả ignored, chỉ còn hai `.gitkeep` trong các vị trí output. Tìm tên file dưới `/home/ngthtrong` chỉ phát hiện gold mô phỏng và fixture app mang tên run_001/run_002; chúng không phải kết quả E2E ngày 24/10.

Drive search tên run_001/run_002/e2e/logcat/20261024 không có raw phù hợp. Search bổ sung RQ2 và candidate_v4_locked cũng không khôi phục dữ liệu chưa làm tròn; receipt lưu đúng query và response. Không khẳng định mọi máy/tài khoản khác đều không còn backup.

Giữ **SKIP_RERUN** cho benchmark ảnh 32 JSON có nguồn, **NOT_RUN** cho E2E mới. Không đo trên app/device/DB hoặc tạo raw giả. Historical Case8 run_001 vẫn FAIL được báo cáo; xác nhận giữ/gửi lại là thông tin bổ sung, không thay thế log gốc. C6 vẫn PARTIAL.

## P07/A1 — Xác minh được danh tính bài trong chương trình chính thức

Nguồn mới là [Program & Publications của ISDS](https://isds.ctu.edu.vn/2026/author/program), liên kết tới [program booklet chính thức](https://drive.google.com/file/d/1WPCC9q-Lm_ypgA1kMSmU3YqRyv0WZcKE/view). Đã đọc metadata, tải đủ **1.607.103 byte**, xác nhận PDF 23 trang, trích text và **xem ảnh trang22**. Trang22 ghi paper **6444**, đúng tiêu đề và đủ tám tác giả khớp `paper/main.tex`:

*Stress-Testing Product-Gated Clustering and Bounded Priority Ranking for Flood-Rescue Reports: A Synthetic Study* — Thanh-Trong Nguyen; Ngoc-Anh Le; Nhu-Quynh Nguyen; Tuong-Hung Cao; Hung-Thinh Ngo; Xuan-Phuong Chau; Lan Phuong Phan; Thanh-Khoa Nguyen.

Program ghi bài ở Room2103, Day2, phiên 10:00–10:20, nhóm Intelligent Systems & Recommender Systems. Bằng chứng này xác minh **danh tính bài và lịch trong chương trình**; không chứng minh bài đã được trình bày hoặc chapter đã online.

[Trang Springer Part II](https://link.springer.com/book/9789819274079) vẫn là nguồn cấp quyển CCIS3253, copyright2027 và thông tin forthcoming, không có chapter list/DOI nối trực tiếp bài6444 trong nội dung đã đọc. Lượt open ghi due23/12/2026 nhưng search cache khác ghi28/12/2026; không chọn một ngày dự kiến làm ngày công bố bài. [ISDS Authors](https://isds.ctu.edu.vn/2026/author) chỉ nêu các tuyến xuất bản chung.

Tìm exact title trên web phát hiện danh mục nhà sách có tên bài trong TOC PartII, nhưng đó là **lead thứ cấp chưa đủ**; không dùng để điền volume/DOI/pages/year vào bảng báo cáo. Truy cập book DOI và frontmatter PDF chính thức không thành công trong lượt kiểm này. Chưa khôi phục chapter DOI, online date, pages, volume hoặc year ở cấp bài.

**A1 vẫn OPEN / UNVERIFIED_AT_ARTICLE_LEVEL** đối với công bố chapter. Giữ trạng thái “đã công bố” theo xác nhận người dùng trong RULES; không tự nâng/hạ. Có thể bổ sung provenance chương trình chính thức vào ghi chú báo cáo, nhưng không điền metadata cấp bài chưa có căn cứ. A3 DEFERRED_BY_USER, không truy cập ảnh.

## Phạm vi kiểm chứng

Không sửa report/raw/model/app/server hoặc artifact cũ. Không fetch/checkout/reset, không tải LFS archive, không nhắn ai, không commit/push. Hash nguồn trong `source-hashes.json`; đây là checkpoint follow-up mới, không thay freeze cũ của P08.
