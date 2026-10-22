import '../entities/rescue_record.dart';
import '../entities/sms_delivery.dart';

abstract class RescueRepository {
  Future<void> init();
  String? get connectedServerUrl;
  Future<bool> reconnectServer({bool force = true});
  List<RescueRecord> getAllRecords();
  RescueRecord? getRecord(String id);
  List<RescueRecord> getRecordsPage({required int offset, required int limit});
  int get recordCount;
  int getPendingCount();

  /// [preparing] keeps a durable draft out of foreground sync until finalized.
  Future<void> saveRecord(RescueRecord record, {bool preparing = false});

  /// Persist the outbox entry without probing or sending to the server.
  Future<void> queueRecord(RescueRecord record);

  /// Gửi các bản ghi còn chờ. [immediate] (có mạng trở lại, Workmanager, người dùng
  /// yêu cầu) gửi ngay cả message đang chờ backoff; false chỉ gửi message đã đến hạn.
  Future<void> syncPendingRecords({bool immediate = true});

  /// Thời điểm message sớm nhất đang chờ backoff đến hạn gửi lại; null nếu không có.
  DateTime? get nextRetryAt;

  /// Gửi [record] (qua outbox) và trả về bản ghi sau lần gửi, đã lưu cục bộ:
  /// `synced` khi xong, `syncError` khi server từ chối vĩnh viễn, nguyên trạng khi
  /// cần thử lại sau.
  Future<RescueRecord> sendRecord(RescueRecord record);

  /// Native send result; `sent` does not confirm delivery or rescue acceptance.
  Future<SmsResult> sendSmsFallback(RescueRecord record);

  /// Lấy trạng thái điều phối mới từ server cho các báo cáo đã đồng bộ và chưa
  /// hoàn thành; trả về các bản ghi vừa đổi trạng thái.
  Future<List<RescueRecord>> refreshStatuses();
}
