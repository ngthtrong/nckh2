import '../entities/rescue_record.dart';
import '../entities/rescue_status.dart';

bool hasSyncWork(Iterable<RescueRecord> records) => records.any(
  (record) =>
      record.syncError == null &&
      (record.awaitingSync || !isFinalStatus(record.status)),
);

bool hasTrackedReports(Iterable<RescueRecord> records) => records.any(
  (record) => record.syncError == null && !isFinalStatus(record.status),
);
