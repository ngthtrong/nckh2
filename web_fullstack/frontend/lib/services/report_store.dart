import '../domain/report.dart';

abstract interface class ReportStore {
  Future<void> save(RescueReport report);

  Future<RescueReport?> get(String id);

  Future<List<RescueReport>> listAll();

  Future<List<RescueReport>> pending();
}

