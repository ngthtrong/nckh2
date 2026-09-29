import '../entities/rescue_record.dart';
import '../entities/send_mode.dart';
import '../repositories/rescue_repository.dart';

/// Lưu bản ghi rồi gửi theo [mode] đã chọn bởi AdaptiveSendPolicy.
///
/// Không có data ([SendMode.smsFallback]): gửi SMS tới tổng đài trước, rồi vẫn
/// xếp bản ghi vào outbox để đồng bộ đầy đủ khi có mạng (store-and-forward).
/// `sendMode` ghi lại cách gửi thực tế: `smsFallback` nếu SMS đi được, không thì
/// `queuedOffline`.
Future<RescueRecord> deliverRecord(
  RescueRepository repository,
  RescueRecord record,
  SendMode mode,
) async {
  var current = record.copyWith(sendMode: mode.name);
  if (mode == SendMode.smsFallback) {
    final smsOk = await repository.sendSmsFallback(current);
    current = current.copyWith(sendMode: resolveOfflineMode(mode, smsOk).name);
  }
  await repository.saveRecord(current);
  if (await repository.sendRecord(current)) {
    current = current.copyWith(synced: true);
    await repository.saveRecord(current);
  }
  return current;
}
