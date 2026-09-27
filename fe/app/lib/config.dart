/// Cấu hình tập trung — sửa tại đây khi deploy thật.
library;

/// Base URL server. `10.0.2.2` = loopback của máy tính khi chạy emulator Android.
/// Đổi thành IP LAN/VPN thật khi test trên máy vật lý hoặc deploy.
/// Ghi đè lúc build/run: `flutter run --dart-define=SERVER_URL=http://10.0.2.2:8000`.
const String kServerBaseUrl = String.fromEnvironment(
  'SERVER_URL',
  defaultValue: 'http://localhost:8000',
);

/// Số tổng đài nhận SMS fallback. Đặt lúc build/run:
/// `--dart-define=EMERGENCY_PHONE=+84xxxxxxxxx`. Còn là số giả thì app không gửi SMS.
const String kEmergencyPhone = String.fromEnvironment(
  'EMERGENCY_PHONE',
  defaultValue: kPlaceholderEmergencyPhone,
);
const String kPlaceholderEmergencyPhone = '+840000000000';

/// Chu kỳ app hỏi server trạng thái điều phối của các báo cáo đã gửi.
const Duration kStatusPollInterval = Duration(seconds: 15);

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

/// Chuyển ảnh định dạng server không nhận (vd. HEIC) sang JPEG khi gửi ảnh gốc.
const int kConvertJpegQuality = 90;
const int kConvertMaxSide = 4096;
