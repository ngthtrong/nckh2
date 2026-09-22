import 'dart:typed_data';

import 'package:app/data/datasources/inference/inference_data_source.dart';
import 'package:app/data/repositories/inference_repository_impl.dart';
import 'package:app/domain/entities/ai_model_type.dart';
import 'package:app/domain/entities/ai_tag.dart';
import 'package:app/domain/repositories/inference_repository.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeInferenceDataSource implements InferenceDataSource {
  Uint8List? receivedBytes;

  @override
  bool get ready => true;

  @override
  bool get pteReady => false;

  @override
  AiModelType currentModel = AiModelType.onnx;

  @override
  bool isDualComparison = false;

  @override
  ModelBenchmarkComparison? get latestComparison => null;

  @override
  Future<void> loadModel() async {}

  @override
  Future<InferenceResult?> classifyImage(Uint8List imageBytes) async {
    receivedBytes = imageBytes;
    return (
      label: 'high',
      confidence: 0.91,
      durationMs: 18,
      modelType: AiModelType.onnx,
    );
  }

  @override
  List<AiTag> generateAiTags(String? label, double? confidence) => [
    AiTag(label: label ?? '', confidence: confidence ?? 0),
  ];

  @override
  void setDualComparison(bool enabled) {
    isDualComparison = enabled;
  }

  @override
  void setModel(AiModelType model) {
    currentModel = model;
  }
}

void main() {
  test(
    'repository forwards bytes and exposes data source model state',
    () async {
      final dataSource = FakeInferenceDataSource();
      final repository = InferenceRepositoryImpl(dataSource);
      final imageBytes = Uint8List.fromList([1, 2, 3]);

      final result = await repository.classifyImage(imageBytes);
      repository.setDualComparison(true);
      repository.setModel(AiModelType.pte);

      expect(dataSource.receivedBytes, same(imageBytes));
      expect(result?.label, 'high');
      expect(result?.confidence, 0.91);
      expect(repository.isDualComparison, isTrue);
      expect(repository.currentModel, AiModelType.pte);
    },
  );
}
