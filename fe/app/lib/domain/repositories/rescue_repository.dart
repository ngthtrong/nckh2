import '../entities/rescue_record.dart';

abstract class RescueRepository {
  Future<void> init();
  List<RescueRecord> getAllRecords();
  int getPendingCount();
  Future<void> saveRecord(RescueRecord record);
  Future<void> syncPendingRecords();
  Future<bool> sendRecord(RescueRecord record);
}
