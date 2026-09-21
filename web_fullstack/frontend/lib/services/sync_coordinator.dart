import '../domain/report.dart';
import 'report_store.dart';

abstract interface class ReportUploader {
  Future<void> upload(RescueReport report);
}

class SyncCoordinator {
  SyncCoordinator({required this.store, required this.uploader});

  final ReportStore store;
  final ReportUploader uploader;
  Future<void>? _running;

  Future<void> syncPending() {
    final active = _running;
    if (active != null) return active;
    final run = _run();
    _running = run;
    return run.whenComplete(() {
      if (identical(_running, run)) _running = null;
    });
  }

  Future<void> _run() async {
    final reports = await store.pending();
    reports.sort((left, right) => left.createdAt.compareTo(right.createdAt));
    for (final report in reports) {
      try {
        await uploader.upload(report);
        await store.save(
          report.copyWith(syncState: SyncState.synced, clearSyncError: true),
        );
      } catch (error) {
        await store.save(
          report.copyWith(syncState: SyncState.pending, syncError: error.toString()),
        );
      }
    }
  }
}

