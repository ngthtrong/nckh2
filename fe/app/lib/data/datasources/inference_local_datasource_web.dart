import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../../domain/entities/ai_model_type.dart';
import '../../domain/entities/ai_tag.dart';
import '../../domain/repositories/inference_repository.dart';

/// Web-safe inference data source.
///
/// `onnxruntime` currently depends on `dart:ffi`, so it cannot be imported by
/// Flutter Web. The web build keeps the inference contract intact and returns
/// no local result; callers can continue to exercise the queue/network flow
/// while native builds use the real ONNX/ExecuTorch implementation.
class InferenceLocalDataSource {
  bool _isLoaded = false;
  bool _pteReady = false;
  AiModelType _currentModel = AiModelType.onnx;
  bool _isDualComparison = false;
  ModelBenchmarkComparison? _latestComparison;

  bool get ready => _isLoaded;
  bool get pteReady => _pteReady;
  AiModelType get currentModel => _currentModel;
  bool get isDualComparison => _isDualComparison;
  ModelBenchmarkComparison? get latestComparison => _latestComparison;

  void setModel(AiModelType model) {
    if (model == AiModelType.pte) {
      debugPrint(
        'ExecuTorch is unavailable on Flutter Web; keeping ONNX active.',
      );
      return;
    }
    _currentModel = model;
    _latestComparison = null;
  }

  void setDualComparison(bool enabled) {
    _isDualComparison = false;
    _latestComparison = null;
    if (enabled) {
      debugPrint('Dual model comparison is unavailable on Flutter Web.');
    }
  }

  Future<void> loadModel() async {
    // Loading labels is harmless on Web and keeps the asset contract visible,
    // but there is intentionally no FFI-backed local model to initialize.
    try {
      await rootBundle.loadString('assets/labels.json');
    } catch (_) {
      // The model assets are optional for the Web UI.
    }
    _isLoaded = false;
    _pteReady = false;
  }

  Future<List<double>?> verifyAndroidLogits(Float32List inputTensor) async {
    return null;
  }

  Future<InferenceResult?> classifyImage(Uint8List imageBytes) async {
    return null;
  }

  List<AiTag> generateAiTags(String? label, double? confidence) {
    if (label == null || confidence == null) return [];
    return [AiTag(label: _translateLabel(label), confidence: confidence)];
  }

  String _translateLabel(String raw) {
    switch (raw.toLowerCase()) {
      case 'low':
        return 'Ngập nhẹ (Low)';
      case 'medium':
        return 'Ngập vừa (Medium)';
      case 'high':
        return 'Ngập sâu (High)';
      case 'non_flood':
        return 'Không ngập nước';
      default:
        return raw;
    }
  }
}
