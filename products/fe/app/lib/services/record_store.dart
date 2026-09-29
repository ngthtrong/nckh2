import 'package:hive_ce_flutter/hive_flutter.dart';

import '../models/rescue_record.dart';

/// Lưu trữ cục bộ bằng Hive — nhẹ, nhanh, không cần SQL.
/// Một box duy nhất: vừa là queue (status=pending) vừa là log metrics.
class RecordStore {
  static const boxName = 'records';
  Box<Map>? _box;

  Future<void> init() async {
    await Hive.initFlutter();
    _box = await Hive.openBox<Map>(boxName);
  }

  bool get ready => _box != null;

  Future<void> upsert(RescueRecord r) async {
    await _box?.put(r.id, r.toMap());
  }

  List<RescueRecord> get all {
    final list = (_box?.values ?? const [])
        .map((m) => RescueRecord.fromMap(Map<dynamic, dynamic>.from(m)))
        .toList();
    list.sort((a, b) => b.createdAtMs.compareTo(a.createdAtMs));
    return list;
  }

  List<RescueRecord> pending() =>
      all.where((r) => r.status == 'pending').toList();

  int get pendingCount => all.where((r) => r.status == 'pending').length;
}
