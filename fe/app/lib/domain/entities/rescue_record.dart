import 'ai_tag.dart';

class RescueRecord {
  final String id;
  final DateTime createdAt;
  final double lat;
  final double lng;
  final String? imagePath;
  final List<String> images;
  final String? aiLabel;
  final double? aiConfidence;
  final List<AiTag> aiTags;
  final int trappedCount;
  final int injuredCount;
  final List<String> vulnerableGroups;
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
    this.description = '',
    required this.sendMode,
    this.synced = false,
    this.status = 'processing',
  });

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
      description: description ?? this.description,
      sendMode: sendMode ?? this.sendMode,
      synced: synced ?? this.synced,
      status: status ?? this.status,
    );
  }
}
