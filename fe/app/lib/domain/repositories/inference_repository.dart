import 'dart:typed_data';
import '../entities/ai_model_type.dart';
import '../entities/ai_tag.dart';

typedef InferenceResult = ({
  String label,
  double confidence,
  int durationMs,
  AiModelType modelType,
});

abstract class InferenceRepository {
  bool get ready;
  AiModelType get currentModel;
  bool get isDualComparison;
  ModelBenchmarkComparison? get latestComparison;

  void setModel(AiModelType model);
  void setDualComparison(bool enabled);

  Future<void> loadModel();
  Future<InferenceResult?> classifyImage(Uint8List imageBytes);
  List<AiTag> generateAiTags(String? label, double? confidence);
}
