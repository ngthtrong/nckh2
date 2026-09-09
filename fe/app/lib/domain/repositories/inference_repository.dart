import 'dart:typed_data';
import '../entities/ai_tag.dart';

typedef InferenceResult = ({String label, double confidence, int durationMs});

abstract class InferenceRepository {
  bool get ready;
  Future<void> loadModel();
  Future<InferenceResult?> classifyImage(Uint8List imageBytes);
  List<AiTag> generateAiTags(String? label, double? confidence);
}
