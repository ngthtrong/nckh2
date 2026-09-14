import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:app/domain/entities/ai_model_type.dart';
import 'package:app/domain/entities/ai_tag.dart';
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

    test('Default model should be ONNX Runtime', () {
      expect(repository.currentModel, equals(AiModelType.onnx));
      expect(repository.currentModel.extension, equals('.onnx'));
      expect(repository.currentModel.badgeText, equals('ONNX (.onnx)'));
    });

    test('Switch model to ExecuTorch (.pte) and back to ONNX', () {
      repository.setModel(AiModelType.pte);
      expect(repository.currentModel, equals(AiModelType.pte));
      expect(repository.currentModel.extension, equals('.pte'));
      expect(repository.currentModel.badgeText, equals('ExecuTorch (.pte)'));

      repository.setModel(AiModelType.onnx);
      expect(repository.currentModel, equals(AiModelType.onnx));
    });

    test('Toggle Dual Model Comparison', () {
      expect(repository.isDualComparison, isTrue);
      repository.setDualComparison(false);
      expect(repository.isDualComparison, isFalse);
      repository.setDualComparison(true);
      expect(repository.isDualComparison, isTrue);
    });

    test('Classify image returns valid result and records comparison', () async {
      // Empty/fallback test bytes
      final dummyBytes = Uint8List(100);
      final result = await repository.classifyImage(dummyBytes);

      expect(result, isNotNull);
      expect(result!.label, isNotEmpty);
      expect(result.confidence, greaterThan(0));
      expect(result.durationMs, greaterThan(0));

      final comparison = repository.latestComparison;
      expect(comparison, isNotNull);
      expect(comparison!.labelOnnx, isNotEmpty);
      expect(comparison.labelPte, isNotEmpty);
      expect(comparison.durationMsOnnx, greaterThan(0));
      expect(comparison.durationMsPte, greaterThan(0));
    });

    test('Generate AI tags translates correctly', () {
      final tags = repository.generateAiTags('low', 0.95);
      expect(tags.length, equals(1));
      expect(tags.first.label, contains('Ngập nhẹ'));
      expect(tags.first.confidence, equals(0.95));
    });
  });
}
