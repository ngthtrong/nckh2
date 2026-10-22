import '../entities/ai_tag.dart';
import '../entities/record_id.dart';
import '../entities/rescue_record.dart';
import '../entities/send_mode.dart';
import '../repositories/rescue_repository.dart';
import 'deliver_record.dart';
import '../../core/platform/local_file.dart';
import '../../config.dart';

class SubmitRescuePostUseCase {
  final RescueRepository repository;

  SubmitRescuePostUseCase(this.repository);

  static int descriptionWordCount(String text) =>
      RegExp(r'\S+').allMatches(text).length;

  static String? validateInput({
    required int trappedCount,
    required int injuredCount,
    required String description,
  }) {
    if (trappedCount < 0 ||
        trappedCount > kMaxReportPeople ||
        injuredCount < 0 ||
        injuredCount > kMaxReportPeople) {
      return 'Số người phải từ 0 đến $kMaxReportPeople.';
    }
    if (description.runes.length > kMaxDescriptionCharacters) {
      return 'Mô tả tối đa $kMaxDescriptionCharacters ký tự.';
    }
    if (descriptionWordCount(description) > kMaxDescriptionWords) {
      return 'Mô tả tối đa $kMaxDescriptionWords từ.';
    }
    return null;
  }

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
    String? contactPhone,
    required SendMode sendMode,
    Future<SendMode> Function()? chooseMode,
  }) async {
    description = description.trim();
    final error = validateInput(
      trappedCount: trappedCount,
      injuredCount: injuredCount,
      description: description,
    );
    if (error != null) throw FormatException(error);
    final id = newRecordId('post');
    final savedImages = <String, String>{};
    for (final path in {?imagePath, ...images}) {
      try {
        savedImages[path] = await preserveLocalFile(
          path,
          '$id-${savedImages.length}',
        );
      } catch (_) {
        throw const FormatException(
          'Không lưu được ảnh đính kèm. Hãy bỏ ảnh hoặc chọn lại ảnh rồi gửi lại.',
        );
      }
    }
    final record = RescueRecord(
      id: id,
      createdAt: DateTime.now(),
      lat: lat,
      lng: lng,
      imagePath: savedImages[imagePath],
      images: images.map((path) => savedImages[path]!).toList(),
      aiTags: aiTags,
      trappedCount: trappedCount,
      injuredCount: injuredCount,
      vulnerableGroups: vulnerableGroups,
      cannotMove: cannotMove,
      severeSigns: severeSigns,
      urgencyScore: urgencyScore,
      description: description,
      contactPhone: contactPhone,
      sendMode: sendMode.name,
      synced: false,
      status: 'processing',
    );

    await repository.saveRecord(record);
    return deliverRecord(
      repository,
      record,
      chooseMode == null ? sendMode : await chooseMode(),
    );
  }
}
