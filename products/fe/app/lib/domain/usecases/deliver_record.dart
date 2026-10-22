import '../entities/rescue_record.dart';
import '../entities/send_mode.dart';
import '../entities/sms_delivery.dart';
import '../repositories/rescue_repository.dart';

/// Lưu và xếp hàng trước mọi quyền/SMS. Worker chỉ đồng bộ data, không tự gửi SMS.
Future<RescueRecord> deliverRecord(
  RescueRepository repository,
  RescueRecord record,
  SendMode mode, {
  bool retrySms = false,
  DateTime Function()? now,
}) async {
  var current = record.copyWith(
    sendMode: mode == SendMode.smsFallback
        ? SendMode.queuedOffline.name
        : mode.name,
  );
  await repository.saveRecord(current);
  await repository.queueRecord(current);
  current = repository.getRecord(current.id) ?? current;
  if (mode != SendMode.smsFallback) {
    current = await repository.sendRecord(current);
  }
  final attemptedAt = (now ?? DateTime.now)();
  final previousAttempt = current.smsAttemptedAt;
  final mayRetry =
      retrySms &&
      current.smsStatus == SmsStatus.failed &&
      previousAttempt != null &&
      attemptedAt.difference(previousAttempt) >= const Duration(seconds: 30);
  if (current.metadataSynced ||
      current.synced ||
      current.syncError != null ||
      (current.smsStatus != SmsStatus.notAttempted && !mayRetry)) {
    return current;
  }
  current = current.copyWith(
    smsStatus: SmsStatus.sending,
    smsAttemptedAt: attemptedAt,
    clearSmsError: true,
  );
  await repository.saveRecord(current);
  SmsResult result;
  try {
    result = await repository.sendSmsFallback(current);
  } catch (_) {
    result = const SmsResult(SmsStatus.unknown, 'CALLBACK_UNAVAILABLE');
  }
  current = current.copyWith(
    smsStatus: result.status,
    smsError: result.errorCode,
    clearSmsError: result.errorCode == null,
    sendMode: result.status == SmsStatus.sent
        ? SendMode.smsFallback.name
        : SendMode.queuedOffline.name,
  );
  await repository.saveRecord(current);
  return repository.getRecord(current.id) ?? current;
}
