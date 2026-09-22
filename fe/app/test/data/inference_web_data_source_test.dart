import 'dart:typed_data';

import 'package:app/data/datasources/inference/inference_web_data_source.dart';
import 'package:app/data/datasources/inference/web_inference_bridge.dart';
import 'package:app/domain/entities/ai_model_type.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeInferenceBridge implements InferenceBridge {
  FakeInferenceBridge(this.response);

  final Map<String, dynamic> response;

  @override
  Future<Map<String, dynamic>> initialize(
    String modelUrl,
    String manifestUrl,
  ) async => {'executionProvider': 'webgpu'};

  @override
  Future<Map<String, dynamic>> predict(Uint8List imageBytes) async => response;
}

void main() {
  test('maps a valid browser result to the shared inference result', () async {
    final dataSource = InferenceWebDataSource.withBridge(
      FakeInferenceBridge({
        'label': 'high',
        'confidence': 0.91,
        'probabilities': [0.01, 0.03, 0.91, 0.05],
        'durationMs': 18.0,
        'executionProvider': 'webgpu',
      }),
    );

    await dataSource.loadModel();
    final result = await dataSource.classifyImage(
      Uint8List.fromList([1, 2, 3]),
    );

    expect(dataSource.ready, isTrue);
    expect(result?.label, 'high');
    expect(result?.confidence, 0.91);
    expect(result?.durationMs, 18);
    expect(result?.modelType, AiModelType.onnx);
  });

  test('rejects a browser result with the wrong probability count', () async {
    final dataSource = InferenceWebDataSource.withBridge(
      FakeInferenceBridge({
        'label': 'high',
        'confidence': 0.91,
        'probabilities': [0.09, 0.91],
        'durationMs': 18.0,
        'executionProvider': 'wasm',
      }),
    );

    expect(
      () => dataSource.classifyImage(Uint8List.fromList([1])),
      throwsA(isA<InferenceException>()),
    );
  });

  test('rejects non-finite browser probabilities', () async {
    final dataSource = InferenceWebDataSource.withBridge(
      FakeInferenceBridge({
        'label': 'medium',
        'confidence': double.nan,
        'probabilities': [0.1, double.nan, 0.2, 0.7],
        'durationMs': 1.0,
        'executionProvider': 'wasm',
      }),
    );

    expect(
      () => dataSource.classifyImage(Uint8List.fromList([1])),
      throwsA(isA<InferenceException>()),
    );
  });
}
