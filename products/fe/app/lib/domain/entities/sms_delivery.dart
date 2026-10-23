enum SmsStatus { notAttempted, sending, sent, failed, unknown }

class SmsResult {
  final SmsStatus status;
  final String? errorCode;

  const SmsResult(this.status, [this.errorCode]);

  factory SmsResult.fromNative(Object? value) {
    if (value is! Map) {
      return const SmsResult(SmsStatus.unknown, 'UNCONFIRMED_RESULT');
    }
    final status = switch (value['status']) {
      'sent' => SmsStatus.sent,
      'failed' => SmsStatus.failed,
      _ => SmsStatus.unknown,
    };
    return SmsResult(status, value['errorCode'] as String?);
  }
}

String smsStatusMessage(SmsStatus status) => switch (status) {
  SmsStatus.notAttempted => '',
  SmsStatus.sending || SmsStatus.unknown =>
    'Chưa xác nhận kết quả SMS. Không tự gửi SMS lặp; báo cáo vẫn chờ đồng bộ.',
  SmsStatus.sent =>
    'Điện thoại đã gửi SMS tóm tắt; chưa xác nhận máy nhận hoặc trung tâm tiếp nhận. Mô tả đầy đủ và ảnh chờ đồng bộ qua mạng.',
  SmsStatus.failed =>
    'Không gửi được SMS. Báo cáo vẫn được lưu; hãy gọi 112 nếu cần trợ giúp ngay.',
};
