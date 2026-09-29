import '../entities/ai_tag.dart';
import '../entities/record_id.dart';
import '../entities/rescue_record.dart';
import '../entities/send_mode.dart';
import '../repositories/rescue_repository.dart';
import 'deliver_record.dart';

class SubmitRescuePostUseCase {
  final RescueRepository repository;

  SubmitRescuePostUseCase(this.repository);

  Future<RescueRecord> call({
    required double? lat,
    required double? lng,
    String? imagePath,
    List<String> images = const [],
    List<AiTag> aiTags = const [],
    int trappedCount = 0,
    int injuredCount = 0,
    List<String> vulnerableGroups = const [],
    bool cannotMove = false,
    List<String> severeSigns = const [],
    double? urgencyScore,
    String description = '',
    required SendMode sendMode,
  }) async {
    final record = RescueRecord(
      id: newRecordId('post'),
      createdAt: DateTime.now(),
      lat: lat,
      lng: lng,
      imagePath: imagePath,
      images: images,
      aiTags: aiTags,
      trappedCount: trappedCount,
      injuredCount: injuredCount,
      vulnerableGroups: vulnerableGroups,
      cannotMove: cannotMove,
      severeSigns: severeSigns,
      urgencyScore: urgencyScore,
      description: description,
      sendMode: sendMode.name,
      synced: false,
      status: 'processing',
    );

    return deliverRecord(repository, record, sendMode);
  }
}
