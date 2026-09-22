import 'dart:typed_data';

import '../../../domain/entities/ai_model_type.dart';
import '../../../domain/entities/ai_tag.dart';
import '../../../domain/repositories/inference_repository.dart';

abstract interface class InferenceDataSource {
  bool get ready;
  bool get pteReady;
  AiModelType get currentModel;
  bool get isDualComparison;
  ModelBenchmarkComparison? get latestComparison;

  void setModel(AiModelType model);
  void setDualComparison(bool enabled);
  Future<void> loadModel();
  Future<InferenceResult?> classifyImage(Uint8List imageBytes);
  List<AiTag> generateAiTags(String? label, double? confidence);
}
