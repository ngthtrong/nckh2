import '../entities/ai_tag.dart';
import '../entities/rescue_image.dart';
import '../entities/rescue_record.dart';
import '../repositories/rescue_repository.dart';

class SubmitRescuePostUseCase {
  final RescueRepository repository;

  SubmitRescuePostUseCase(this.repository);

  Future<RescueRecord> call({
    required double lat,
    required double lng,
    RescueImage? image,
    List<AiTag> aiTags = const [],
    int trappedCount = 0,
    int injuredCount = 0,
    List<String> vulnerableGroups = const [],
    String description = '',
    required String sendMode,
  }) async {
    final record = RescueRecord(
      id: 'post-${DateTime.now().millisecondsSinceEpoch}',
      createdAt: DateTime.now(),
      lat: lat,
      lng: lng,
      image: image,
      aiTags: aiTags,
      trappedCount: trappedCount,
      injuredCount: injuredCount,
      vulnerableGroups: vulnerableGroups,
      description: description,
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
