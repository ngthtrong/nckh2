/// Cấu hình tập trung — sửa tại đây khi deploy thật.
library;

/// Base URL server. `10.0.2.2` = loopback của máy tính khi chạy emulator Android.
/// Đổi thành IP LAN/VPN thật khi test trên máy vật lý hoặc deploy.
const String kServerBaseUrl = 'http://localhost:8000';

/// Số tổng đài nhận SMS fallback — BẮT BUỘC thay bằng số thật.
const String kEmergencyPhone = '+840000000000';

/// Probe throughput: server cần phục vụ 1 file tĩnh ~64KB tại đường dẫn này.
const String kProbeUrl = '$kServerBaseUrl/probe';

/// Ngưỡng mạng (kbps).
const int kStrongKbps = 1000; // >= ~1 Mbps coi là mạnh
const int kMinUsefulKbps = 50; // còn gửi nổi ảnh nén

/// Ngưỡng tin model on-device.
const double kHighConfidence = 0.90;

/// true: confident cao + mạng mạnh → chỉ gửi text (tiết kiệm băng thông).
/// false: luôn gửi ảnh gốc khi mạng mạnh để server đối chiếu.
const bool kPreferTextWhenConfident = true;

/// Tham số nén thích ứng cho chế độ mạng trung bình / yếu.
const int kCompressQualityMedium = 60;
const int kCompressMaxSideMedium = 1024;
