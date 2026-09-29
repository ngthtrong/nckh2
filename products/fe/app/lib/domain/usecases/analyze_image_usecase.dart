import 'dart:typed_data';
import '../entities/ai_tag.dart';
import '../repositories/inference_repository.dart';

class AnalyzeImageUseCase {
  final InferenceRepository repository;

  AnalyzeImageUseCase(this.repository);

  Future<List<AiTag>> call(Uint8List imageBytes) async {
    final result = await repository.classifyImage(imageBytes);
    if (result != null) {
      return repository.generateAiTags(result.label, result.confidence);
    }
    return repository.generateAiTags(null, null);
  }
}
