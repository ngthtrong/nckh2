import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:app/domain/entities/ai_model_type.dart';
import 'package:app/domain/repositories/inference_repository.dart';
import 'package:app/data/datasources/inference_local_datasource.dart';
import 'package:app/data/repositories/inference_repository_impl.dart';

void main() {
  group('InferenceRepository & AI Model Settings Test', () {
    late InferenceLocalDataSource dataSource;
    late InferenceRepository repository;

    setUp(() {
      dataSource = InferenceLocalDataSource();
      repository = InferenceRepositoryImpl(dataSource);
    });

    test('Default model is PTE and comparison requires admin access', () async {
      expect(repository.currentModel, equals(AiModelType.pte));
      expect(repository.currentModel.extension, equals('.pte'));
      repository.setModel(AiModelType.onnx);
      repository.setDualComparison(true);
      expect(repository.currentModel, AiModelType.pte);
      expect(repository.isDualComparison, isFalse);
      expect(repository.onnxReady, isFalse);
      await expectLater(repository.loadComparisonModel('untrusted.onnx'), throwsStateError);
    });

    test('Invalid image does not fabricate an inference result', () async {
      final dummyBytes = Uint8List(100);
      final result = await repository.classifyImage(dummyBytes);
      expect(result, isNull);
    });

    test('Generate AI tags translates correctly', () {
      final tags = repository.generateAiTags('low', 0.95);
      expect(tags.length, equals(1));
      expect(tags.first.label, contains('Ngập nhẹ'));
      expect(tags.first.confidence, equals(0.95));
    });
  });
}
