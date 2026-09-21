import 'dart:typed_data';

enum SyncState { pending, synced, failed }

class RescueReport {
  const RescueReport({
    required this.id,
    required this.createdAt,
    this.description = '',
    this.trappedCount = 0,
    this.injuredCount = 0,
    this.vulnerableGroups = const [],
    this.aiLabel,
    this.aiConfidence,
    this.latitude,
    this.longitude,
    this.imageBytes,
    this.imageName,
    this.imageMimeType,
    this.syncState = SyncState.pending,
    this.syncError,
    this.smsStatus,
  });

  factory RescueReport.draft({
    required String id,
    Uint8List? imageBytes,
    String? imageName,
    String? imageMimeType,
  }) {
    return RescueReport(
      id: id,
      createdAt: DateTime.now().toUtc(),
      imageBytes: imageBytes,
      imageName: imageName,
      imageMimeType: imageMimeType,
    );
  }

  factory RescueReport.fromMap(Map<dynamic, dynamic> map) {
    final rawImage = map['imageBytes'];
    return RescueReport(
      id: map['id'] as String,
      createdAt: DateTime.parse(map['createdAt'] as String).toUtc(),
      description: map['description'] as String? ?? '',
      trappedCount: map['trappedCount'] as int? ?? 0,
      injuredCount: map['injuredCount'] as int? ?? 0,
      vulnerableGroups: List<String>.from(
        map['vulnerableGroups'] as List<dynamic>? ?? const [],
      ),
      aiLabel: map['aiLabel'] as String?,
      aiConfidence: (map['aiConfidence'] as num?)?.toDouble(),
      latitude: (map['latitude'] as num?)?.toDouble(),
      longitude: (map['longitude'] as num?)?.toDouble(),
      imageBytes: rawImage == null
          ? null
          : rawImage is Uint8List
          ? rawImage
          : Uint8List.fromList(List<int>.from(rawImage as List<dynamic>)),
      imageName: map['imageName'] as String?,
      imageMimeType: map['imageMimeType'] as String?,
      syncState: SyncState.values.byName(
        map['syncState'] as String? ?? SyncState.pending.name,
      ),
      syncError: map['syncError'] as String?,
      smsStatus: map['smsStatus'] as String?,
    );
  }

  final String id;
  final DateTime createdAt;
  final String description;
  final int trappedCount;
  final int injuredCount;
  final List<String> vulnerableGroups;
  final String? aiLabel;
  final double? aiConfidence;
  final double? latitude;
  final double? longitude;
  final Uint8List? imageBytes;
  final String? imageName;
  final String? imageMimeType;
  final SyncState syncState;
  final String? syncError;
  final String? smsStatus;

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'createdAt': createdAt.toUtc().toIso8601String(),
      'description': description,
      'trappedCount': trappedCount,
      'injuredCount': injuredCount,
      'vulnerableGroups': vulnerableGroups,
      'aiLabel': aiLabel,
      'aiConfidence': aiConfidence,
      'latitude': latitude,
      'longitude': longitude,
      'imageBytes': imageBytes,
      'imageName': imageName,
      'imageMimeType': imageMimeType,
      'syncState': syncState.name,
      'syncError': syncError,
      'smsStatus': smsStatus,
    };
  }

  RescueReport copyWith({
    String? description,
    int? trappedCount,
    int? injuredCount,
    List<String>? vulnerableGroups,
    String? aiLabel,
    double? aiConfidence,
    double? latitude,
    double? longitude,
    Uint8List? imageBytes,
    String? imageName,
    String? imageMimeType,
    SyncState? syncState,
    String? syncError,
    bool clearSyncError = false,
    String? smsStatus,
  }) {
    return RescueReport(
      id: id,
      createdAt: createdAt,
      description: description ?? this.description,
      trappedCount: trappedCount ?? this.trappedCount,
      injuredCount: injuredCount ?? this.injuredCount,
      vulnerableGroups: vulnerableGroups ?? this.vulnerableGroups,
      aiLabel: aiLabel ?? this.aiLabel,
      aiConfidence: aiConfidence ?? this.aiConfidence,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      imageBytes: imageBytes ?? this.imageBytes,
      imageName: imageName ?? this.imageName,
      imageMimeType: imageMimeType ?? this.imageMimeType,
      syncState: syncState ?? this.syncState,
      syncError: clearSyncError ? null : syncError ?? this.syncError,
      smsStatus: smsStatus ?? this.smsStatus,
    );
  }
}

