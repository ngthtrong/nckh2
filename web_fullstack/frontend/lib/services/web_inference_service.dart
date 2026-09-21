import 'dart:typed_data';

import '../domain/inference_result.dart';
import 'inference_bridge_stub.dart'
    if (dart.library.js_interop) 'inference_bridge_web.dart';
import 'inference_contract.dart';

class WebInferenceService {
  WebInferenceService() : this.withBridge(createInferenceBridge());

  WebInferenceService.withBridge(this._bridge);

  static const _classes = ['low', 'medium', 'high', 'non_flood'];
  static const _modelUrl = 'models/flood_mobilenetv3_large.onnx';
  static const _manifestUrl = 'models/model_manifest.json';

  final InferenceBridge _bridge;
  Future<void>? _initialization;

  Future<void> initialize() {
    return _initialization ??= _initializeOnce();
  }

  Future<void> _initializeOnce() async {
    try {
      await _bridge.initialize(_modelUrl, _manifestUrl);
    } catch (error) {
      _initialization = null;
      if (error is InferenceException) rethrow;
      throw InferenceException('Không thể tải mô hình AI: $error');
    }
  }

  Future<InferenceResult> analyze(Uint8List imageBytes) async {
    if (imageBytes.isEmpty) {
      throw const InferenceException('Ảnh không có dữ liệu.');
    }
    await initialize();
    final Map<String, dynamic> response;
    try {
      response = await _bridge.predict(imageBytes);
    } catch (error) {
      if (error is InferenceException) rethrow;
      throw InferenceException('Không thể chạy nhận diện AI: $error');
    }

    final rawProbabilities = response['probabilities'];
    if (rawProbabilities is! List || rawProbabilities.length != _classes.length) {
      throw const InferenceException('Mô hình phải trả về đúng bốn xác suất.');
    }
    final probabilities = rawProbabilities.map((value) {
      if (value is! num) {
        throw const InferenceException('Xác suất AI không phải là số.');
      }
      final probability = value.toDouble();
      if (!probability.isFinite || probability < 0 || probability > 1) {
        throw const InferenceException('Xác suất AI nằm ngoài khoảng hợp lệ.');
      }
      return probability;
    }).toList(growable: false);

    final label = response['label'];
    final confidenceValue = response['confidence'];
    final durationValue = response['durationMs'];
    final provider = response['executionProvider'];
    if (label is! String || !_classes.contains(label)) {
      throw const InferenceException('Nhãn AI không hợp lệ.');
    }
    if (confidenceValue is! num ||
        !confidenceValue.toDouble().isFinite ||
        confidenceValue < 0 ||
        confidenceValue > 1) {
      throw const InferenceException('Độ tin cậy AI không hợp lệ.');
    }
    if (durationValue is! num || !durationValue.toDouble().isFinite) {
      throw const InferenceException('Thời gian nhận diện không hợp lệ.');
    }
    if (provider is! String || (provider != 'webgpu' && provider != 'wasm')) {
      throw const InferenceException('ONNX execution provider không hợp lệ.');
    }

    return InferenceResult(
      label: label,
      confidence: confidenceValue.toDouble(),
      probabilities: probabilities,
      durationMs: durationValue.toDouble(),
      executionProvider: provider,
    );
  }
}
