# Lỗi wrapper và trạng thái artifact

Lần assemble đầu hoàn tất child artifact và in `Frozen: 296 retained; 4 uncertain excluded`, nhưng wrapper lỗi `FileExistsError` khi ghi đè receipt RUNNING bằng helper chỉ cho tạo tệp mới. Không chạy lại hoặc ghi đè corpus. Receipt `commands/assemble.json` được giữ; exit code child chưa được chốt bền trong receipt đó. Bước `commands/verify_dataset.json` sau đó đạt exit 0, kiểm corpus và hash bằng `load_data()`.

Lần features cũng đã khởi động bằng wrapper cũ và gặp cùng lỗi chốt receipt sau khi child hoàn thành extraction. Giữ nguyên `commands/features.json`, `features.log`, cache và `features.json`; không chạy lại extraction. `commands/verify_features.json` đạt exit 0, xác minh 296 hàng, ID, chiều, tính hữu hạn, L2 và hash. Đây là lỗi ghi receipt của wrapper, không phải bằng chứng rằng extraction đã thất bại hoặc rằng receipt RUNNING là receipt thành công.

Runner đã được sửa để ghi start receipt và final receipt ở hai tệp riêng, cùng log/hash/exit. Lệnh launch T2 đầu đặt `--timeout` sau positional name nên argparse REMAINDER hiểu đó là executable; Popen trả `FileNotFoundError` trước khi tạo child. Chưa có training trong lần launch đó. Lệnh đúng đặt cờ trước tên bước và dùng receipt `fine_tune_cpu` riêng; bước này đã hoàn tất exit 0.

Trong kiểm PDF, `check_citation_regression` chủ ý kiểm bản chưa sửa và trả lỗi cho hai tài liệu DistilBERT chưa được gán số do thiếu keyword phân nhóm. Receipt lỗi được giữ để chứng minh bộ kiểm mới phát hiện đúng vấn đề. Bản cuối bổ sung keyword và làm mới auxiliary cache đánh số; build.py tự làm mới cache nếu còn khóa trích dẫn chưa có số dương. Bản cuối được kiểm lại bằng các receipt final; không thay receipt cũ thành PASS.
