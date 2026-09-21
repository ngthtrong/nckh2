import 'package:hive_ce_flutter/hive_ce_flutter.dart';

import '../domain/report.dart';
import 'report_store.dart';

class OfflineReportStore implements ReportStore {
  OfflineReportStore._(this._box);

  static const boxName = 'rescue_reports_v1';

  final Box<dynamic> _box;

  static Future<OfflineReportStore> initialize() async {
    await Hive.initFlutter();
    final box = await Hive.openBox<dynamic>(boxName);
    return OfflineReportStore._(box);
  }

  @override
  Future<void> save(RescueReport report) => _box.put(report.id, report.toMap());

  @override
  Future<RescueReport?> get(String id) async {
    final value = _box.get(id);
    return value is Map ? RescueReport.fromMap(value) : null;
  }

  @override
  Future<List<RescueReport>> listAll() async {
    final reports = _box.values
        .whereType<Map>()
        .map(RescueReport.fromMap)
        .toList(growable: false);
    reports.sort((left, right) => right.createdAt.compareTo(left.createdAt));
    return reports;
  }

  @override
  Future<List<RescueReport>> pending() async {
    final reports = await listAll();
    return reports
        .where((report) => report.syncState == SyncState.pending)
        .toList(growable: false);
  }
}
