import '../entities/rescue_record.dart';

abstract class RescueRepository {
  Future<void> init();
  List<RescueRecord> getAllRecords();
  List<RescueRecord> getRecordsPage({required int offset, required int limit});
  int get recordCount;
  int getPendingCount();
  Future<void> saveRecord(RescueRecord record);

  /// Gửi các bản ghi còn chờ. [immediate] (có mạng trở lại, Workmanager, người dùng
  /// yêu cầu) gửi ngay cả message đang chờ backoff; false chỉ gửi message đã đến hạn.
  Future<void> syncPendingRecords({bool immediate = true});

  /// Thời điểm message sớm nhất đang chờ backoff đến hạn gửi lại; null nếu không có.
  DateTime? get nextRetryAt;

  /// Gửi [record] (qua outbox) và trả về bản ghi sau lần gửi, đã lưu cục bộ:
  /// `synced` khi xong, `syncError` khi server từ chối vĩnh viễn, nguyên trạng khi
  /// cần thử lại sau.
  Future<RescueRecord> sendRecord(RescueRecord record);

  /// Gửi SMS dự phòng tới tổng đài; false nếu nền tảng/cấu hình không cho phép.
  Future<bool> sendSmsFallback(RescueRecord record);

  /// Lấy trạng thái điều phối mới từ server cho các báo cáo đã đồng bộ và chưa
  /// hoàn thành; trả về các bản ghi vừa đổi trạng thái.
  Future<List<RescueRecord>> refreshStatuses();
}
