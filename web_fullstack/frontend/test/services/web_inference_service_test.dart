import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:flood_rescue_web/services/inference_contract.dart';
import 'package:flood_rescue_web/services/web_inference_service.dart';

class FakeInferenceBridge implements InferenceBridge {
  FakeInferenceBridge(this.response);

  final Map<String, dynamic> response;

  @override
  Future<Map<String, dynamic>> initialize(String modelUrl, String manifestUrl) async {
    return {'executionProvider': 'webgpu'};
  }

  @override
  Future<Map<String, dynamic>> predict(Uint8List imageBytes) async => response;
}

void main() {
  test('maps the complete bridge response to an inference result', () async {
    final service = WebInferenceService.withBridge(
      FakeInferenceBridge({
        'label': 'high',
        'confidence': 0.91,
        'probabilities': [0.01, 0.03, 0.91, 0.05],
        'durationMs': 18.0,
        'executionProvider': 'webgpu',
      }),
    );

    final result = await service.analyze(Uint8List.fromList([1, 2, 3]));

    expect(result.label, 'high');
    expect(result.confidence, 0.91);
    expect(result.probabilities, [0.01, 0.03, 0.91, 0.05]);
    expect(result.durationMs, 18);
    expect(result.executionProvider, 'webgpu');
  });

  test('rejects a bridge response with the wrong probability count', () async {
    final service = WebInferenceService.withBridge(
      FakeInferenceBridge({
        'label': 'high',
        'confidence': 0.91,
        'probabilities': [0.09, 0.91],
        'durationMs': 18.0,
        'executionProvider': 'wasm',
      }),
    );

    expect(
      () => service.analyze(Uint8List.fromList([1])),
      throwsA(isA<InferenceException>()),
    );
  });

  test('rejects non-finite or out-of-range probabilities', () async {
    final service = WebInferenceService.withBridge(
      FakeInferenceBridge({
        'label': 'medium',
        'confidence': double.nan,
        'probabilities': [0.1, double.nan, 0.2, 0.7],
        'durationMs': 1.0,
        'executionProvider': 'wasm',
      }),
    );

    expect(
      () => service.analyze(Uint8List.fromList([1])),
      throwsA(isA<InferenceException>()),
    );
  });
}
