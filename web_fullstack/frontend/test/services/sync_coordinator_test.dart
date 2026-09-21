import 'package:flutter_test/flutter_test.dart';
import 'package:flood_rescue_web/domain/report.dart';
import 'package:flood_rescue_web/services/report_store.dart';
import 'package:flood_rescue_web/services/sync_coordinator.dart';

class MemoryReportStore implements ReportStore {
  MemoryReportStore(List<RescueReport> reports)
    : values = {for (final report in reports) report.id: report};

  final Map<String, RescueReport> values;

  @override
  Future<RescueReport?> get(String id) async => values[id];

  @override
  Future<List<RescueReport>> listAll() async => values.values.toList();

  @override
  Future<List<RescueReport>> pending() async => values.values
      .where((report) => report.syncState == SyncState.pending)
      .toList();

  @override
  Future<void> save(RescueReport report) async => values[report.id] = report;
}

class RecordingUploader implements ReportUploader {
  RecordingUploader({this.error});

  final Object? error;
  final List<String> uploadedIds = [];

  @override
  Future<void> upload(RescueReport report) async {
    uploadedIds.add(report.id);
    if (error != null) throw error!;
  }
}

RescueReport pendingReport(String id) => RescueReport(
  id: id,
  createdAt: DateTime.utc(2026, 9, 21),
  description: 'Cần cứu hộ',
);

void main() {
  test('successful upload marks a pending report synced', () async {
    final store = MemoryReportStore([pendingReport('r1')]);
    final uploader = RecordingUploader();
    final coordinator = SyncCoordinator(store: store, uploader: uploader);

    await coordinator.syncPending();

    expect(uploader.uploadedIds, ['r1']);
    expect((await store.get('r1'))!.syncState, SyncState.synced);
    expect((await store.get('r1'))!.syncError, isNull);
  });

  test('failed upload stays pending and records an error', () async {
    final store = MemoryReportStore([pendingReport('r1')]);
    final uploader = RecordingUploader(error: Exception('offline'));
    final coordinator = SyncCoordinator(store: store, uploader: uploader);

    await coordinator.syncPending();

    expect((await store.get('r1'))!.syncState, SyncState.pending);
    expect((await store.get('r1'))!.syncError, contains('offline'));
  });

  test('concurrent sync requests share one upload run', () async {
    final store = MemoryReportStore([pendingReport('r1')]);
    final uploader = RecordingUploader();
    final coordinator = SyncCoordinator(store: store, uploader: uploader);

    await Future.wait([coordinator.syncPending(), coordinator.syncPending()]);

    expect(uploader.uploadedIds, ['r1']);
  });
}
