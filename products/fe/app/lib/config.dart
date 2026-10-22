/// Cấu hình tập trung — sửa tại đây khi deploy thật.
library;

const int kMaxReportPeople = 10000;
const int kMaxDescriptionWords = 300;
const int kMaxDescriptionCharacters = 2000;

// Flutter supplies the flavor to Dart and Gradle together.
const bool kAdminModelTools =
    String.fromEnvironment('FLUTTER_APP_FLAVOR') != 'user';

/// Bản thông thường chỉ kết nối HTTPS tại địa chỉ được cấu hình lúc build.
const String kConfiguredServerUrl = String.fromEnvironment(
  'SERVER_URL',
  defaultValue: '',
);
const bool kAllowInsecureLan = bool.fromEnvironment('ALLOW_INSECURE_LAN');

bool isAllowedServerUrl(
  String url, {
  bool allowInsecureLan = kAllowInsecureLan,
}) {
  final uri = Uri.tryParse(url);
  if (uri == null ||
      uri.host.isEmpty ||
      uri.userInfo.isNotEmpty ||
      uri.hasQuery ||
      uri.hasFragment ||
      (uri.path.isNotEmpty && uri.path != '/')) {
    return false;
  }
  if (uri.scheme == 'https') return true;
  if (!allowInsecureLan || uri.scheme != 'http') return false;
  if (uri.host == 'localhost' || uri.host == '::1') return true;
  final parts = uri.host.split('.').map(int.tryParse).toList();
  if (parts.length != 4 || parts.any((p) => p == null || p < 0 || p > 255)) {
    return false;
  }
  return parts[0] == 10 ||
      parts[0] == 127 ||
      (parts[0] == 192 && parts[1] == 168) ||
      (parts[0] == 172 && parts[1]! >= 16 && parts[1]! <= 31);
}

void requireAllowedServerUrl(String url) {
  if (!isAllowedServerUrl(url)) {
    throw StateError(
      'Cần SERVER_URL HTTPS. HTTP LAN chỉ dùng trong bản demo ALLOW_INSECURE_LAN=true.',
    );
  }
}

String _serverBaseUrl = kConfiguredServerUrl;
String get kServerBaseUrl => _serverBaseUrl;

/// Không gửi dữ liệu đến địa chỉ cũ khi chưa xác minh được server.
void setServerBaseUrl(String? url) => _serverBaseUrl =
    url != null && isAllowedServerUrl(url) ? url : 'http://127.0.0.1:1';

/// Số tổng đài nhận SMS fallback. Đặt lúc build/run:
/// `--dart-define-from-file=.env.local`. Tệp bị Git bỏ qua, không đóng gói như asset.
/// Cấu hình build vẫn có thể được trích từ APK; không dùng cho khóa bí mật.
const String kEmergencyPhone = String.fromEnvironment(
  'EMERGENCY_PHONE',
  defaultValue: kPlaceholderEmergencyPhone,
);
const String kPlaceholderEmergencyPhone = '+840000000000';

/// Chu kỳ app hỏi server trạng thái điều phối của các báo cáo đã gửi.
const Duration kStatusPollInterval = Duration(seconds: 15);

/// Probe throughput: server cần phục vụ 1 file tĩnh ~64KB tại đường dẫn này.
String get kProbeUrl => '$kServerBaseUrl/probe';

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
