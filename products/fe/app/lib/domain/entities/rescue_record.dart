import 'ai_tag.dart';
import 'sms_delivery.dart';

String canonicalSevereSign(String sign) => switch (sign) {
  'respiratory_distress' => 'respiratory_distress_or_cyanosis',
  'seizure' => 'active_convulsions',
  'major_trauma' => 'high_risk_trauma',
  _ => sign,
};

String formatReportLocation(double? lat, double? lng, double? accuracyMeters) {
  if (lat == null || lng == null) return 'Chưa có GPS · trung tâm sẽ xác minh';
  final coordinates = '${lat.toStringAsFixed(4)}, ${lng.toStringAsFixed(4)}';
  if (accuracyMeters == null) return coordinates;
  return '$coordinates · sai số ±${accuracyMeters.ceil()} m'
      '${accuracyMeters > 100 ? ' · vị trí gần đúng' : ''}';
}

class RescueRecord {
  final String id;
  final DateTime createdAt;

  /// Null khi không lấy được GPS: server đưa báo cáo vào hàng cần xem xét thủ công.
  final double? lat;
  final double? lng;
  final double? locationAccuracyMeters;
  final String? imagePath;
  final List<String> images;
  final String? aiLabel;
  final double? aiConfidence;
  final List<AiTag> aiTags;
  final int trappedCount;
  final int injuredCount;
  final List<String> vulnerableGroups;
  final bool cannotMove;
  final List<String> severeSigns;
  final double? urgencyScore;
  final String description;
  final String? contactPhone;
  final String sendMode;
  final bool synced;
  final bool metadataSynced;
  final SmsStatus smsStatus;
  final String? smsError;
  final DateTime? smsAttemptedAt;

  /// Retryable local attachment failure; metadata may already be on the server.
  final String? attachmentError;
  final String status;

  /// Mã lỗi khi server từ chối vĩnh viễn báo cáo (vd. `INVALID_PAYLOAD`): báo cáo
  /// không còn chờ gửi, người dùng cần gọi tổng đài. Null khi chưa bị từ chối.
  final String? syncError;

  const RescueRecord({
    required this.id,
    required this.createdAt,
    required this.lat,
    required this.lng,
    this.locationAccuracyMeters,
    this.imagePath,
    this.images = const [],
    this.aiLabel,
    this.aiConfidence,
    this.aiTags = const [],
    this.trappedCount = 0,
    this.injuredCount = 0,
    this.vulnerableGroups = const [],
    this.cannotMove = false,
    this.severeSigns = const [],
    this.urgencyScore,
    this.description = '',
    this.contactPhone,
    required this.sendMode,
    this.synced = false,
    this.metadataSynced = false,
    this.smsStatus = SmsStatus.notAttempted,
    this.smsError,
    this.smsAttemptedAt,
    this.attachmentError,
    this.status = 'processing',
    this.syncError,
  });

  /// Còn chờ gửi lên server (chưa xong và chưa bị từ chối vĩnh viễn).
  bool get awaitingSync => !synced && syncError == null;

  /// Độ tin cậy cao nhất của AI on-device; 0 khi không có nhãn AI.
  double get maxAiConfidence => aiTags.fold(
    aiConfidence ?? 0,
    (best, tag) => tag.confidence > best ? tag.confidence : best,
  );

  /// Vị trí dạng hiển thị, hoặc thông báo khi báo cáo không có GPS.
  String get locationText =>
      formatReportLocation(lat, lng, locationAccuracyMeters);

  RescueRecord copyWith({
    String? id,
    DateTime? createdAt,
    double? lat,
    double? lng,
    double? locationAccuracyMeters,
    String? imagePath,
    List<String>? images,
    String? aiLabel,
    double? aiConfidence,
    List<AiTag>? aiTags,
    int? trappedCount,
    int? injuredCount,
    List<String>? vulnerableGroups,
    bool? cannotMove,
    List<String>? severeSigns,
    double? urgencyScore,
    String? description,
    String? contactPhone,
    String? sendMode,
    bool? synced,
    bool? metadataSynced,
    SmsStatus? smsStatus,
    String? smsError,
    bool clearSmsError = false,
    DateTime? smsAttemptedAt,
    String? attachmentError,
    bool clearAttachmentError = false,
    String? status,
    String? syncError,
  }) {
    return RescueRecord(
      id: id ?? this.id,
      createdAt: createdAt ?? this.createdAt,
      lat: lat ?? this.lat,
      lng: lng ?? this.lng,
      locationAccuracyMeters:
          locationAccuracyMeters ?? this.locationAccuracyMeters,
      imagePath: imagePath ?? this.imagePath,
      images: images ?? this.images,
      aiLabel: aiLabel ?? this.aiLabel,
      aiConfidence: aiConfidence ?? this.aiConfidence,
      aiTags: aiTags ?? this.aiTags,
      trappedCount: trappedCount ?? this.trappedCount,
      injuredCount: injuredCount ?? this.injuredCount,
      vulnerableGroups: vulnerableGroups ?? this.vulnerableGroups,
      cannotMove: cannotMove ?? this.cannotMove,
      severeSigns: severeSigns ?? this.severeSigns,
      urgencyScore: urgencyScore ?? this.urgencyScore,
      description: description ?? this.description,
      contactPhone: contactPhone ?? this.contactPhone,
      sendMode: sendMode ?? this.sendMode,
      synced: synced ?? this.synced,
      metadataSynced: metadataSynced ?? this.metadataSynced,
      smsStatus: smsStatus ?? this.smsStatus,
      smsError: clearSmsError ? null : smsError ?? this.smsError,
      smsAttemptedAt: smsAttemptedAt ?? this.smsAttemptedAt,
      attachmentError: clearAttachmentError
          ? null
          : attachmentError ?? this.attachmentError,
      status: status ?? this.status,
      syncError: syncError ?? this.syncError,
    );
  }

  bool get severeCondition => severeSigns.isNotEmpty;
}
