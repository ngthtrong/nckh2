import '../entities/record_id.dart';
import '../entities/rescue_record.dart';
import '../entities/send_mode.dart';
import '../entities/sms_delivery.dart';
import '../repositories/rescue_repository.dart';
import 'deliver_record.dart';

class SendSosUseCase {
  final RescueRepository repository;
  final DateTime Function() now;
  static const repeatWindow = Duration(seconds: 30);

  SendSosUseCase(this.repository, {DateTime Function()? now})
    : now = now ?? DateTime.now;

  Future<RescueRecord> call({
    required double? lat,
    required double? lng,
    required SendMode sendMode,
    String? contactPhone,
    Future<({double? lat, double? lng})> Function()? locate,
    Future<SendMode> Function()? chooseMode,
  }) async {
    final createdAt = now();
    for (final previous in repository.getAllRecords()) {
      final age = createdAt.difference(previous.createdAt);
      if (previous.id.startsWith('sos-') &&
          !age.isNegative &&
          age < repeatWindow) {
        if (previous.awaitingSync &&
            !previous.metadataSynced &&
            previous.smsStatus == SmsStatus.notAttempted) {
          return deliverRecord(
            repository,
            previous,
            chooseMode == null ? sendMode : await chooseMode(),
          );
        }
        return previous;
      }
    }
    var record = RescueRecord(
      id: newRecordId('sos'),
      createdAt: createdAt,
      lat: lat,
      lng: lng,
      contactPhone: contactPhone,
      description: 'CỨU HỘ KHẨN CẤP (Nút SOS 1 chạm)',
      sendMode: SendMode.queuedOffline.name,
      synced: false,
      status: 'processing',
    );
    // Preserve the request even if the app closes during GPS or discovery.
    await repository.saveRecord(record, preparing: true);
    try {
      if (locate != null) {
        final position = await locate();
        record = record.copyWith(lat: position.lat, lng: position.lng);
        await repository.saveRecord(record);
      }
      return await deliverRecord(
        repository,
        record,
        chooseMode == null ? sendMode : await chooseMode(),
      );
    } catch (_) {
      await repository.queueRecord(record);
      rethrow;
    }
  }
}
