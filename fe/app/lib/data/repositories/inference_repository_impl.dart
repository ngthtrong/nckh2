import 'dart:typed_data';

import '../../domain/entities/ai_model_type.dart';
import '../../domain/entities/ai_tag.dart';
import '../../domain/repositories/inference_repository.dart';
import '../datasources/inference/inference_data_source.dart';

class InferenceRepositoryImpl implements InferenceRepository {
  final InferenceDataSource dataSource;

  InferenceRepositoryImpl(this.dataSource);

  @override
  bool get ready => dataSource.ready;

  @override
  bool get pteReady => dataSource.pteReady;

  @override
  AiModelType get currentModel => dataSource.currentModel;

  @override
  bool get isDualComparison => dataSource.isDualComparison;

  @override
  ModelBenchmarkComparison? get latestComparison => dataSource.latestComparison;

  @override
  void setModel(AiModelType model) => dataSource.setModel(model);

  @override
  void setDualComparison(bool enabled) => dataSource.setDualComparison(enabled);

  @override
  Future<void> loadModel() async {
    await dataSource.loadModel();
  }

  @override
  Future<InferenceResult?> classifyImage(Uint8List imageBytes) async {
    return dataSource.classifyImage(imageBytes);
  }

  @override
  List<AiTag> generateAiTags(String? label, double? confidence) {
    return dataSource.generateAiTags(label, confidence);
  }
}
