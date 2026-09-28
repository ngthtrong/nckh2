import '../entities/rescue_record.dart';

abstract class RescueRepository {
  Future<void> init();
  List<RescueRecord> getAllRecords();
  List<RescueRecord> getRecordsPage({required int offset, required int limit});
  int get recordCount;
  int getPendingCount();
  Future<void> saveRecord(RescueRecord record);
  Future<void> syncPendingRecords();
  Future<bool> sendRecord(RescueRecord record);

  /// Gửi SMS dự phòng tới tổng đài; false nếu nền tảng/cấu hình không cho phép.
  Future<bool> sendSmsFallback(RescueRecord record);

  /// Lấy trạng thái điều phối mới từ server cho các báo cáo đã đồng bộ và chưa
  /// hoàn thành; trả về các bản ghi vừa đổi trạng thái.
  Future<List<RescueRecord>> refreshStatuses();
}
