import 'package:flutter/foundation.dart';

import '../../../domain/entities/ai_model_type.dart';
import '../../../domain/entities/ai_tag.dart';
import '../../../domain/repositories/inference_repository.dart';
import 'inference_data_source.dart';
import 'web_inference_bridge.dart';
import 'web_inference_bridge_stub.dart'
    if (dart.library.js_interop) 'web_inference_bridge_web.dart';

InferenceDataSource createInferenceDataSource() => InferenceWebDataSource();

class InferenceWebDataSource implements InferenceDataSource {
  InferenceWebDataSource() : this.withBridge(createInferenceBridge());

  InferenceWebDataSource.withBridge(this._bridge);

  static const modelUrl = 'models/model.onnx';
  static const manifestUrl = 'models/model_manifest.json';
  static const _classes = ['low', 'medium', 'high', 'non_flood'];

  final InferenceBridge _bridge;
  Future<void>? _initialization;
  bool _ready = false;

  @override
  bool get ready => _ready;

  @override
  bool get pteReady => false;

  @override
  AiModelType get currentModel => AiModelType.onnx;

  @override
  bool get isDualComparison => false;

  @override
  ModelBenchmarkComparison? get latestComparison => null;

  @override
  void setModel(AiModelType model) {
    if (model == AiModelType.pte) {
      debugPrint('ExecuTorch PTE is Android-only; keeping ONNX Web active.');
    }
  }

  @override
  void setDualComparison(bool enabled) {
    if (enabled) {
      debugPrint('Dual ONNX/PTE comparison is Android-only.');
    }
  }

  @override
  Future<void> loadModel() => _initialization ??= _initializeOnce();

  Future<void> _initializeOnce() async {
    try {
      final response = await _bridge.initialize(modelUrl, manifestUrl);
      _validateProvider(response['executionProvider']);
      _ready = true;
    } catch (error) {
      _ready = false;
      _initialization = null;
      if (error is InferenceException) rethrow;
      throw InferenceException('Không thể tải mô hình AI trên web: $error');
    }
  }

  @override
  Future<InferenceResult?> classifyImage(Uint8List imageBytes) async {
    if (imageBytes.isEmpty) {
      throw const InferenceException('Ảnh không có dữ liệu.');
    }
    await loadModel();

    final Map<String, dynamic> response;
    try {
      response = await _bridge.predict(imageBytes);
    } catch (error) {
      if (error is InferenceException) rethrow;
      throw InferenceException('Không thể chạy nhận diện AI trên web: $error');
    }

    final rawProbabilities = response['probabilities'];
    if (rawProbabilities is! List ||
        rawProbabilities.length != _classes.length) {
      throw const InferenceException('Mô hình phải trả về đúng bốn xác suất.');
    }
    for (final value in rawProbabilities) {
      if (value is! num) {
        throw const InferenceException('Xác suất AI không phải là số.');
      }
      final probability = value.toDouble();
      if (!probability.isFinite || probability < 0 || probability > 1) {
        throw const InferenceException('Xác suất AI nằm ngoài khoảng hợp lệ.');
      }
    }

    final label = response['label'];
    final confidenceValue = response['confidence'];
    final durationValue = response['durationMs'];
    _validateProvider(response['executionProvider']);
    if (label is! String || !_classes.contains(label)) {
      throw const InferenceException('Nhãn AI không hợp lệ.');
    }
    if (confidenceValue is! num ||
        !confidenceValue.toDouble().isFinite ||
        confidenceValue < 0 ||
        confidenceValue > 1) {
      throw const InferenceException('Độ tin cậy AI không hợp lệ.');
    }
    if (durationValue is! num ||
        !durationValue.toDouble().isFinite ||
        durationValue < 0) {
      throw const InferenceException('Thời gian nhận diện không hợp lệ.');
    }

    return (
      label: label,
      confidence: confidenceValue.toDouble(),
      durationMs: durationValue.round(),
      modelType: AiModelType.onnx,
    );
  }

  void _validateProvider(Object? provider) {
    if (provider != 'webgpu' && provider != 'wasm') {
      throw const InferenceException('ONNX execution provider không hợp lệ.');
    }
  }

  @override
  List<AiTag> generateAiTags(String? label, double? confidence) {
    if (label == null || confidence == null) return [];
    return [AiTag(label: _translateLabel(label), confidence: confidence)];
  }

  String _translateLabel(String raw) {
    return switch (raw.toLowerCase()) {
      'low' => 'Ngập nhẹ (Low)',
      'medium' => 'Ngập vừa (Medium)',
      'high' => 'Ngập sâu (High)',
      'non_flood' => 'Không ngập nước',
      _ => raw,
    };
  }
}
