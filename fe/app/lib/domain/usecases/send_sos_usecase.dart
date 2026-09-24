import '../entities/rescue_record.dart';
import '../repositories/rescue_repository.dart';

class SendSosUseCase {
  final RescueRepository repository;

  SendSosUseCase(this.repository);

  Future<RescueRecord> call({
    required double lat,
    required double lng,
    required String sendMode,
  }) async {
    final record = RescueRecord(
      id: 'sos-${DateTime.now().millisecondsSinceEpoch}',
      createdAt: DateTime.now(),
      lat: lat,
      lng: lng,
      description: 'CỨU HỘ KHẨN CẤP (Nút SOS 1 chạm)',
      sendMode: sendMode,
      synced: false,
      status: 'processing',
    );

    await repository.saveRecord(record);
    final success = await repository.sendRecord(record);
    if (success) {
      final updated = record.copyWith(synced: true);
      await repository.saveRecord(updated);
      return updated;
    }
    return record;
  }
}
