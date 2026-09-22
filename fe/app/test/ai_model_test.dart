import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:app/domain/entities/ai_model_type.dart';
import 'package:app/domain/repositories/inference_repository.dart';
import 'package:app/data/datasources/inference/inference_data_source.dart';
import 'package:app/data/datasources/inference/inference_data_source_factory.dart';
import 'package:app/data/repositories/inference_repository_impl.dart';

void main() {
  group('InferenceRepository & AI Model Settings Test', () {
    late InferenceDataSource dataSource;
    late InferenceRepository repository;

    setUp(() {
      dataSource = createInferenceDataSource();
      repository = InferenceRepositoryImpl(dataSource);
    });

    test('Default model should be ONNX Runtime', () {
      expect(repository.currentModel, equals(AiModelType.onnx));
      expect(repository.currentModel.extension, equals('.onnx'));
      expect(repository.currentModel.badgeText, equals('ONNX (.onnx)'));
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
