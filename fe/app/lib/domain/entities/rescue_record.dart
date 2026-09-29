import 'ai_tag.dart';

String canonicalSevereSign(String sign) => switch (sign) {
  'respiratory_distress' => 'respiratory_distress_or_cyanosis',
  'seizure' => 'active_convulsions',
  'major_trauma' => 'high_risk_trauma',
  _ => sign,
};

class RescueRecord {
  final String id;
  final DateTime createdAt;

  /// Null khi không lấy được GPS: server đưa báo cáo vào hàng cần xem xét thủ công.
  final double? lat;
  final double? lng;
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
  final String sendMode;
  final bool synced;
  final String status;

  const RescueRecord({
    required this.id,
    required this.createdAt,
    required this.lat,
    required this.lng,
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
    required this.sendMode,
    this.synced = false,
    this.status = 'processing',
  });

  /// Độ tin cậy cao nhất của AI on-device; 0 khi không có nhãn AI.
  double get maxAiConfidence => aiTags.fold(
    aiConfidence ?? 0,
    (best, tag) => tag.confidence > best ? tag.confidence : best,
  );

  /// Vị trí dạng hiển thị, hoặc thông báo khi báo cáo không có GPS.
  String get locationText => lat != null && lng != null
      ? '${lat!.toStringAsFixed(4)}, ${lng!.toStringAsFixed(4)}'
      : 'Chưa có GPS · trung tâm sẽ xác minh';

  RescueRecord copyWith({
    String? id,
    DateTime? createdAt,
    double? lat,
    double? lng,
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
    String? sendMode,
    bool? synced,
    String? status,
  }) {
    return RescueRecord(
      id: id ?? this.id,
      createdAt: createdAt ?? this.createdAt,
      lat: lat ?? this.lat,
      lng: lng ?? this.lng,
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
      sendMode: sendMode ?? this.sendMode,
      synced: synced ?? this.synced,
      status: status ?? this.status,
    );
  }

  bool get severeCondition => severeSigns.isNotEmpty;
}
