/// Quyết định chế độ gửi — hàm thuần, không phụ thuộc plugin, dễ unit test.
library;

enum SendMode {
  fullImage,
  compressedImage,
  textOnly,
  smsFallback,
  queuedOffline,
}

/// Logic:
/// - Không data → thử SMS fallback (thất bại sẽ rơi vào queue ở tầng gọi).
///   [hasData]=false nghĩa là mất data connection.
/// - Mạng mạnh:
///     * confidence cao (tin model on-device) → chỉ gửi TEXT nếu
///       [preferTextWhenConfident], ngược lại gửi ảnh gốc cho server đối chiếu.
///     * confidence thấp → gửi ảnh GỐC để server xác minh lại.
/// - Mạng trung bình (>= [minUsefulKbps]) → ảnh NÉN + text.
/// - Mạng yếu hơn nữa nhưng còn data → chỉ TEXT (vài trăm byte).
SendMode chooseMode({
  required bool hasData,
  required double confidence,
  required int throughputKbps,
  required int strongKbps,
  required int minUsefulKbps,
  required double highConfidence,
  bool preferTextWhenConfident = true,
}) {
  if (!hasData) return SendMode.smsFallback;
  if (throughputKbps >= strongKbps) {
    if (confidence >= highConfidence && preferTextWhenConfident) {
      return SendMode.textOnly;
    }
    return SendMode.fullImage;
  }
  if (throughputKbps >= minUsefulKbps) return SendMode.compressedImage;
  return SendMode.textOnly;
}

/// Nhãn hiển thị của queue khi không gửi được gì cả.
SendMode resolveOfflineMode(SendMode attempted, bool smsOk) =>
    (attempted == SendMode.smsFallback && smsOk)
    ? SendMode.smsFallback
    : SendMode.queuedOffline;

extension SendModeLabel on SendMode {
  /// Mô tả tiếng Việt để hiển thị cho người dùng.
  String get label => switch (this) {
    SendMode.fullImage => 'Ảnh gốc + thông tin',
    SendMode.compressedImage => 'Ảnh nén + thông tin',
    SendMode.textOnly => 'Chỉ thông tin (không gửi ảnh)',
    SendMode.smsFallback => 'SMS tới tổng đài, đồng bộ khi có mạng',
    SendMode.queuedOffline => 'Lưu hàng đợi, gửi khi có mạng',
  };
}

/// Chế độ gửi đọc từ `RescueRecord.sendMode`; null với giá trị cũ ('direct') hoặc lạ.
SendMode? sendModeFromName(String? name) => SendMode.values.asNameMap()[name];
