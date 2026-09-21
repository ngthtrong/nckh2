# NCKH Flood Rescue — Web Full-stack

Đây là phiên bản web/backend được tách riêng hoàn toàn. Source Android chính vẫn nằm tại `fe/app` và không được import hoặc chỉnh sửa bởi phần mới.

## Cấu trúc

- `backend/`: FastAPI, SQLite, lưu ảnh và tích hợp Twilio có kiểm soát.
- `frontend/`: Flutter Web/PWA chạy trên Chrome (được xây dựng ở giai đoạn frontend).
- `model_tools/`: công cụ xuất checkpoint PyTorch sang ONNX cho trình duyệt.
- `scripts/`: lệnh kiểm thử và chạy từng thành phần.
- `DESIGN.md`: kiến trúc, giới hạn nền tảng và tiêu chí hoàn thành.

## Trạng thái hiện tại

Backend báo cáo và SMS đã có kiểm thử tự động. Frontend Flutter Web và công cụ model được triển khai theo kế hoạch tại `docs/superpowers/plans/2026-09-21-web-fullstack-frontend-ai.md`.

Xem [backend/README.md](backend/README.md) để chạy API và biết tên các biến môi trường cần điền sau.

