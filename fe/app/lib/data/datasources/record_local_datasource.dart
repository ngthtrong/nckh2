import 'package:hive_ce_flutter/hive_flutter.dart';
import '../../domain/entities/ai_tag.dart';
import '../../domain/entities/rescue_image.dart';
import '../../domain/entities/rescue_record.dart';

class RecordLocalDataSource {
  static const String boxName = 'records';
  Box<Map>? _box;

  RecordLocalDataSource();

  RecordLocalDataSource.withBox(Box<Map> box) : _box = box;

  Future<void> init() async {
    await Hive.initFlutter();
    _box = await Hive.openBox<Map>(boxName);
  }

  bool get ready => _box != null;

  Future<void> saveRecord(RescueRecord record) async {
    final map = {
      'id': record.id,
      'createdAtMs': record.createdAt.millisecondsSinceEpoch,
      'lat': record.lat,
      'lng': record.lng,
      'image': record.image?.toMap(),
      'aiLabel': record.aiLabel,
      'aiConfidence': record.aiConfidence,
      'aiTags': record.aiTags.map((e) => e.toJson()).toList(),
      'trappedCount': record.trappedCount,
      'injuredCount': record.injuredCount,
      'vulnerableGroups': record.vulnerableGroups,
      'description': record.description,
      'sendMode': record.sendMode,
      'synced': record.synced,
      'status': record.status,
      'lastError': record.lastError,
    };
    await _box?.put(record.id, map);
  }

  List<RescueRecord> getAllRecords() {
    if (_box == null) return [];
    final list = _box!.values.map((raw) {
      final m = Map<String, dynamic>.from(raw);
      final rawTags = m['aiTags'] as List?;
      List<AiTag> tags = [];
      if (rawTags != null) {
        tags = rawTags
            .map((e) => AiTag.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList();
      }

      final rawVulnerable = m['vulnerableGroups'] as List?;
      List<String> vulnerable = [];
      if (rawVulnerable != null) {
        vulnerable = rawVulnerable.map((e) => e.toString()).toList();
      }

      final rawImage = m['image'];
      final image = rawImage is Map ? RescueImage.fromMap(rawImage) : null;

      final createdAtMs =
          (m['createdAtMs'] as num?)?.toInt() ??
          DateTime.now().millisecondsSinceEpoch;

      return RescueRecord(
        id: m['id'] as String? ?? 'id-${DateTime.now().millisecondsSinceEpoch}',
        createdAt: DateTime.fromMillisecondsSinceEpoch(createdAtMs),
        lat: (m['lat'] as num?)?.toDouble() ?? 10.7769,
        lng: (m['lng'] as num?)?.toDouble() ?? 106.7009,
        image: image,
        aiLabel: m['aiLabel'] as String?,
        aiConfidence: (m['aiConfidence'] as num?)?.toDouble(),
        aiTags: tags,
        trappedCount: (m['trappedCount'] as num?)?.toInt() ?? 0,
        injuredCount: (m['injuredCount'] as num?)?.toInt() ?? 0,
        vulnerableGroups: vulnerable,
        description: m['description'] as String? ?? m['note'] as String? ?? '',
        sendMode: m['sendMode'] as String? ?? m['mode'] as String? ?? 'direct',
        synced: m['synced'] as bool? ?? (m['status'] == 'sent'),
        status: m['status'] as String? ?? 'processing',
        lastError: m['lastError'] as String?,
      );
    }).toList();

    list.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return list;
  }

  int getPendingCount() {
    return getAllRecords().where((r) => !r.synced).length;
  }
}
