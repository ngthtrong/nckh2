import '../entities/rescue_record.dart';
import '../entities/send_mode.dart';
import '../repositories/rescue_repository.dart';
import 'deliver_record.dart';

class SendSosUseCase {
  final RescueRepository repository;

  SendSosUseCase(this.repository);

  Future<RescueRecord> call({
    required double? lat,
    required double? lng,
    required SendMode sendMode,
  }) async {
    final record = RescueRecord(
      id: 'sos-${DateTime.now().millisecondsSinceEpoch}',
      createdAt: DateTime.now(),
      lat: lat,
      lng: lng,
      description: 'CỨU HỘ KHẨN CẤP (Nút SOS 1 chạm)',
      sendMode: sendMode.name,
      synced: false,
      status: 'processing',
    );

    return deliverRecord(repository, record, sendMode);
  }
}
