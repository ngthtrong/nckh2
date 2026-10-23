import 'package:hive_ce_flutter/hive_flutter.dart';
import '../../domain/entities/ai_tag.dart';
import '../../domain/entities/rescue_record.dart';
import '../../domain/entities/rescue_status.dart';
import '../../domain/entities/sms_delivery.dart';

class RecordLocalDataSource {
  static const String boxName = 'records';
  Box<Map>? _box;
  List<String>? _orderedIds;

  /// [hivePath] chỉ dùng trong test (thư mục tạm, không cần plugin path_provider).
  Future<void> init({String? hivePath}) async {
    hivePath == null ? await Hive.initFlutter() : Hive.init(hivePath);
    _box = await Hive.openBox<Map>(boxName);
    _orderedIds = null;
  }

  bool get ready => _box != null;

  Future<void> saveRecord(RescueRecord record) async {
    final previous = _box?.get(record.id);
    if (previous != null) {
      final saved = _recordFromMap(previous);
      // A foreground SMS result may arrive after the worker has saved an ACK.
      record = record.copyWith(
        metadataSynced: record.metadataSynced || saved.metadataSynced,
        synced: record.synced || saved.synced,
        status: advancedStatus(saved.status, record.status) ?? saved.status,
        syncError: record.syncError ?? saved.syncError,
      );
      final incomingSmsAt = record.smsAttemptedAt?.millisecondsSinceEpoch ?? -1;
      final savedSmsAt = saved.smsAttemptedAt?.millisecondsSinceEpoch ?? -1;
      if (incomingSmsAt < savedSmsAt ||
          (incomingSmsAt == savedSmsAt &&
              ((record.smsStatus == SmsStatus.notAttempted &&
                      saved.smsStatus != SmsStatus.notAttempted) ||
                  (record.smsStatus == SmsStatus.sending &&
                      saved.smsStatus != SmsStatus.notAttempted &&
                      saved.smsStatus != SmsStatus.sending) ||
                  saved.smsStatus == SmsStatus.sent))) {
        record = record.copyWith(
          smsStatus: saved.smsStatus,
          smsError: saved.smsError,
          smsAttemptedAt: saved.smsAttemptedAt,
          clearSmsError: saved.smsError == null,
        );
      }
    }
    final map = {
      'id': record.id,
      'createdAtMs': record.createdAt.millisecondsSinceEpoch,
      'lat': record.lat,
      'lng': record.lng,
      'locationAccuracyMeters': record.locationAccuracyMeters,
      'imagePath': record.imagePath,
      'images': record.images,
      'aiLabel': record.aiLabel,
      'aiConfidence': record.aiConfidence,
      'aiTags': record.aiTags.map((e) => e.toJson()).toList(),
      'trappedCount': record.trappedCount,
      'injuredCount': record.injuredCount,
      'vulnerableGroups': record.vulnerableGroups,
      'cannotMove': record.cannotMove,
      'severeSigns': record.severeSigns,
      'urgencyScore': record.urgencyScore,
      'description': record.description,
      'contactPhone': record.contactPhone,
      'sendMode': record.sendMode,
      'synced': record.synced,
      'metadataSynced': record.metadataSynced,
      'smsStatus': record.smsStatus.name,
      'smsError': record.smsError,
      'smsAttemptedAtMs': record.smsAttemptedAt?.millisecondsSinceEpoch,
      'attachmentError': record.attachmentError,
      'status': record.status,
      'syncError': record.syncError,
    };
    await _box?.put(record.id, map);
    if (previous == null ||
        _createdAtMs(previous) != record.createdAt.millisecondsSinceEpoch) {
      _orderedIds = null;
    }
  }

  List<RescueRecord> getAllRecords() {
    return getRecordsPage(offset: 0, limit: recordCount);
  }

  RescueRecord? getRecord(String id) {
    final raw = _box?.get(id);
    return raw == null ? null : _recordFromMap(raw);
  }

  int get recordCount =>
      _orderedIds?.length ?? _box?.keys.whereType<String>().length ?? 0;

  List<RescueRecord> getRecordsPage({required int offset, required int limit}) {
    final box = _box;
    if (box == null || limit <= 0) return [];

    final ids = _orderedIds ??= (box.keys.whereType<String>().toList()
      ..sort((a, b) {
        final byDate = _createdAtMs(
          box.get(b),
        ).compareTo(_createdAtMs(box.get(a)));
        return byDate != 0 ? byDate : a.compareTo(b);
      }));
    final start = offset < 0 ? 0 : offset;
    if (start >= ids.length) return [];
    final end = start + limit < ids.length ? start + limit : ids.length;
    return ids
        .sublist(start, end)
        .map((id) => _recordFromMap(box.get(id)!))
        .toList();
  }

  static int _createdAtMs(Map? raw) {
    final value = raw?['createdAtMs'];
    if (value is num) return value.toInt();
    final legacyValue = raw?['createdAt'];
    if (legacyValue is DateTime) return legacyValue.millisecondsSinceEpoch;
    if (legacyValue is String) {
      return DateTime.tryParse(legacyValue)?.millisecondsSinceEpoch ?? 0;
    }
    return 0;
  }

  static RescueRecord _recordFromMap(Map raw) {
    final m = Map<String, dynamic>.from(raw);
    final rawTags = m['aiTags'] as List?;
    final tags =
        rawTags
            ?.map((e) => AiTag.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList() ??
        [];
    final vulnerable =
        (m['vulnerableGroups'] as List?)?.map((e) => e.toString()).toList() ??
        [];
    final images =
        (m['images'] as List?)?.map((e) => e.toString()).toList() ?? [];
    final severeSigns =
        (m['severeSigns'] as List?)
            ?.map((value) => canonicalSevereSign(value.toString()))
            .toList() ??
        [];
    final createdAtMs = _createdAtMs(m);
    final smsAttemptedAtMs = m['smsAttemptedAtMs'];

    return RescueRecord(
      id: m['id'] as String? ?? 'id-${DateTime.now().millisecondsSinceEpoch}',
      createdAt: DateTime.fromMillisecondsSinceEpoch(
        createdAtMs == 0 ? DateTime.now().millisecondsSinceEpoch : createdAtMs,
      ),
      lat: (m['lat'] as num?)?.toDouble(),
      lng: (m['lng'] as num?)?.toDouble(),
      locationAccuracyMeters: (m['locationAccuracyMeters'] as num?)?.toDouble(),
      imagePath: m['imagePath'] as String?,
      images: images,
      aiLabel: m['aiLabel'] as String?,
      aiConfidence: (m['aiConfidence'] as num?)?.toDouble(),
      aiTags: tags,
      trappedCount: (m['trappedCount'] as num?)?.toInt() ?? 0,
      injuredCount: (m['injuredCount'] as num?)?.toInt() ?? 0,
      vulnerableGroups: vulnerable,
      cannotMove: m['cannotMove'] as bool? ?? false,
      severeSigns: severeSigns,
      urgencyScore: (m['urgencyScore'] as num?)?.toDouble(),
      description: m['description'] as String? ?? m['note'] as String? ?? '',
      contactPhone: m['contactPhone'] as String?,
      sendMode: m['sendMode'] as String? ?? m['mode'] as String? ?? 'direct',
      synced: m['synced'] as bool? ?? (m['status'] == 'sent'),
      metadataSynced: m['metadataSynced'] as bool? ?? m['synced'] == true,
      smsStatus: SmsStatus.values.firstWhere(
        (status) => status.name == m['smsStatus'],
        orElse: () => m['sendMode'] == 'smsFallback'
            ? SmsStatus.unknown
            : SmsStatus.notAttempted,
      ),
      smsError: m['smsError'] as String?,
      smsAttemptedAt: smsAttemptedAtMs is num
          ? DateTime.fromMillisecondsSinceEpoch(
              smsAttemptedAtMs.toInt(),
              isUtc: true,
            )
          : null,
      attachmentError: m['attachmentError'] as String?,
      status: m['status'] as String? ?? 'processing',
      syncError: m['syncError'] as String?,
    );
  }

  int getPendingCount() {
    return getAllRecords().where((r) => r.awaitingSync).length;
  }
}
