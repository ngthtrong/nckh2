import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:onnxruntime/onnxruntime.dart';
import 'package:path_provider/path_provider.dart';

import '../../../domain/entities/ai_model_type.dart';
import '../../../domain/entities/ai_tag.dart';
import '../../../domain/repositories/inference_repository.dart';
import 'inference_data_source.dart';

InferenceDataSource createInferenceDataSource() => InferenceNativeDataSource();

class InferenceNativeDataSource implements InferenceDataSource {
  static const int _inputSize = 224;
  static const _mean = [0.485, 0.456, 0.406];
  static const _std = [0.229, 0.224, 0.225];
  static const _pteChannel = MethodChannel('rescue/executorch');

  OrtSession? _onnxSession;
  List<String> _labels = [];
  bool _isLoaded = false;
  bool _pteReady = false;
  AiModelType _currentModel = AiModelType.onnx;
  bool _isDualComparison = false;
  ModelBenchmarkComparison? _latestComparison;

  @override
  bool get ready => _isLoaded;

  @override
  bool get pteReady => _pteReady;

  @override
  AiModelType get currentModel => _currentModel;

  @override
  bool get isDualComparison => _isDualComparison;

  @override
  ModelBenchmarkComparison? get latestComparison => _latestComparison;

  @override
  void setModel(AiModelType model) {
    if (model == AiModelType.pte && !_pteReady) {
      debugPrint('ExecuTorch is unavailable; keeping ONNX active.');
      return;
    }
    _currentModel = model;
    _latestComparison = null;
  }

  @override
  void setDualComparison(bool enabled) {
    _isDualComparison = enabled && _pteReady;
    _latestComparison = null;
  }

  @override
  Future<void> loadModel() async {
    try {
      OrtEnv.instance.init();
    } catch (_) {}

    final docDir = await getApplicationSupportDirectory();
    final manifest =
        jsonDecode(
              await rootBundle.loadString('assets/models/model_manifest.json'),
            )
            as Map<String, dynamic>;
    final version = manifest['version'] as String;
    final onnxFile = await _syncAsset(
      directory: docDir,
      assetPath: 'assets/models/model.onnx',
      fileName: 'model.onnx',
      version: version,
    );
    final pteFile = await _syncAsset(
      directory: docDir,
      assetPath: 'assets/models/model.pte',
      fileName: 'model.pte',
      version: version,
    );

    try {
      _onnxSession = OrtSession.fromFile(onnxFile, OrtSessionOptions());
      debugPrint('✓ ONNX model loaded: $version');
    } catch (error) {
      debugPrint('ONNX file load failed, trying bundled bytes: $error');
      try {
        final raw = await rootBundle.load('assets/models/model.onnx');
        final bytes = raw.buffer.asUint8List(
          raw.offsetInBytes,
          raw.lengthInBytes,
        );
        _onnxSession = OrtSession.fromBuffer(bytes, OrtSessionOptions());
      } catch (fallbackError) {
        debugPrint('ONNX load failed: $fallbackError');
        _onnxSession = null;
      }
    }

    _pteReady = false;
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      try {
        _pteReady =
            await _pteChannel.invokeMethod<bool>('load', {
              'modelPath': pteFile.path,
            }) ??
            false;
        debugPrint('✓ ExecuTorch PTE loaded: $_pteReady');
      } on PlatformException catch (error) {
        debugPrint('ExecuTorch load failed: ${error.code}: ${error.message}');
      } on MissingPluginException {
        debugPrint('ExecuTorch native bridge is unavailable on this platform.');
      }
    }

    try {
      final rawLabels = await rootBundle.loadString('assets/labels.json');
      _labels = List<String>.from(jsonDecode(rawLabels) as List);
    } catch (error) {
      debugPrint('Labels load failed: $error');
      _labels = ['low', 'medium', 'high', 'non_flood'];
    }

    _isLoaded = _onnxSession != null && _labels.length == 4;
    if (_onnxSession != null) {
      unawaited(
        verifyAndroidLogits(Float32List(1 * 3 * _inputSize * _inputSize)),
      );
    }
  }

  Future<File> _syncAsset({
    required Directory directory,
    required String assetPath,
    required String fileName,
    required String version,
  }) async {
    final target = File('${directory.path}/$fileName');
    final versionFile = File('${target.path}.version');
    final installedVersion = await versionFile.exists()
        ? (await versionFile.readAsString()).trim()
        : '';
    if (!await target.exists() ||
        await target.length() == 0 ||
        installedVersion != version) {
      final raw = await rootBundle.load(assetPath);
      final bytes = raw.buffer.asUint8List(
        raw.offsetInBytes,
        raw.lengthInBytes,
      );
      final temporary = File('${target.path}.tmp');
      await temporary.writeAsBytes(bytes, flush: true);
      if (await target.exists()) await target.delete();
      await temporary.rename(target.path);
      await versionFile.writeAsString(version, flush: true);
    }
    return target;
  }

  Future<List<double>?> verifyAndroidLogits(Float32List inputTensor) async {
    final output = await _runOnnx(inputTensor);
    debugPrint('📱 [ANDROID ONNX RUNTIME OUTPUT]: ${output?.scores}');
    return output?.scores;
  }

  @override
  Future<InferenceResult?> classifyImage(Uint8List imageBytes) async {
    try {
      final rgba = await _letterboxRgba(imageBytes);
      if (rgba == null) return null;
      final tensor = _normalizeRgba(rgba);

      _EngineOutput? onnxOutput;
      _EngineOutput? pteOutput;
      if (_currentModel == AiModelType.onnx || _isDualComparison) {
        onnxOutput = await _runOnnx(tensor);
      }
      if ((_currentModel == AiModelType.pte || _isDualComparison) &&
          _pteReady) {
        pteOutput = await _runPte(tensor);
      }

      final onnxResult = _toResult(onnxOutput, AiModelType.onnx);
      final pteResult = _toResult(pteOutput, AiModelType.pte);
      if (onnxResult != null && pteResult != null) {
        _latestComparison = ModelBenchmarkComparison(
          activeModel: _currentModel,
          labelOnnx: onnxResult.label,
          confOnnx: onnxResult.confidence,
          durationMsOnnx: onnxResult.durationMs,
          labelPte: pteResult.label,
          confPte: pteResult.confidence,
          durationMsPte: pteResult.durationMs,
          isIdentical: onnxResult.label == pteResult.label,
        );
      } else {
        _latestComparison = null;
      }

      return _currentModel == AiModelType.onnx ? onnxResult : pteResult;
    } catch (error) {
      debugPrint('Classification error: $error');
      return null;
    }
  }

  Future<_EngineOutput?> _runOnnx(Float32List data) async {
    final session = _onnxSession;
    if (session == null) return null;
    final input = OrtValueTensor.createTensorWithDataList(data, [
      1,
      3,
      _inputSize,
      _inputSize,
    ]);
    final options = OrtRunOptions();
    final stopwatch = Stopwatch()..start();
    try {
      final outputs = await session.runAsync(options, {
        session.inputNames.first: input,
      });
      stopwatch.stop();
      final scores = _firstRow(outputs?[0]?.value);
      for (final output in outputs ?? const []) {
        output?.release();
      }
      return scores == null
          ? null
          : _EngineOutput(
              _probabilities(scores),
              stopwatch.elapsedMilliseconds,
            );
    } finally {
      input.release();
      options.release();
    }
  }

  Future<_EngineOutput?> _runPte(Float32List data) async {
    final stopwatch = Stopwatch()..start();
    try {
      final output = await _pteChannel.invokeMethod<List<dynamic>>('forward', {
        'input': data,
      });
      stopwatch.stop();
      if (output == null || output.isEmpty) return null;
      final scores = output
          .cast<num>()
          .map((value) => value.toDouble())
          .toList();
      return _EngineOutput(
        _probabilities(scores),
        stopwatch.elapsedMilliseconds,
      );
    } on PlatformException catch (error) {
      debugPrint(
        'ExecuTorch inference failed: ${error.code}: ${error.message}',
      );
      return null;
    }
  }

  InferenceResult? _toResult(_EngineOutput? output, AiModelType modelType) {
    if (output == null || output.scores.isEmpty) return null;
    var best = 0;
    for (var index = 1; index < output.scores.length; index++) {
      if (output.scores[index] > output.scores[best]) best = index;
    }
    if (best >= _labels.length) return null;
    return (
      label: _labels[best],
      confidence: output.scores[best],
      durationMs: output.durationMs,
      modelType: modelType,
    );
  }

  Float32List _normalizeRgba(Uint8List rgba) {
    final pixels = rgba.length ~/ 4;
    final tensor = Float32List(3 * pixels);
    for (var index = 0; index < pixels; index++) {
      tensor[index] = ((rgba[index * 4] / 255) - _mean[0]) / _std[0];
      tensor[pixels + index] =
          ((rgba[index * 4 + 1] / 255) - _mean[1]) / _std[1];
      tensor[2 * pixels + index] =
          ((rgba[index * 4 + 2] / 255) - _mean[2]) / _std[2];
    }
    return tensor;
  }

  Future<Uint8List?> _letterboxRgba(Uint8List encoded) async {
    final codec = await ui.instantiateImageCodec(encoded);
    final frame = await codec.getNextFrame();
    codec.dispose();
    final source = frame.image;
    try {
      final scale = math.min(
        _inputSize / source.width,
        _inputSize / source.height,
      );
      final width = source.width * scale;
      final height = source.height * scale;
      final recorder = ui.PictureRecorder();
      final canvas = ui.Canvas(recorder);
      canvas.drawColor(
        const ui.Color.fromARGB(255, 124, 116, 104),
        ui.BlendMode.src,
      );
      canvas.drawImageRect(
        source,
        ui.Rect.fromLTWH(
          0,
          0,
          source.width.toDouble(),
          source.height.toDouble(),
        ),
        ui.Rect.fromLTWH(
          (_inputSize - width) / 2,
          (_inputSize - height) / 2,
          width,
          height,
        ),
        ui.Paint()..filterQuality = ui.FilterQuality.high,
      );
      final image = await recorder.endRecording().toImage(
        _inputSize,
        _inputSize,
      );
      try {
        final bytes = await image.toByteData(
          format: ui.ImageByteFormat.rawStraightRgba,
        );
        if (bytes == null) return null;
        return bytes.buffer.asUint8List(
          bytes.offsetInBytes,
          bytes.lengthInBytes,
        );
      } finally {
        image.dispose();
      }
    } finally {
      source.dispose();
    }
  }

  List<double> _probabilities(List<double> scores) {
    final sum = scores.fold<double>(0, (total, value) => total + value);
    final alreadyProbabilities =
        scores.every((value) => value >= 0 && value <= 1) &&
        (sum - 1).abs() < 0.001;
    if (alreadyProbabilities) return scores;
    final maxScore = scores.reduce(math.max);
    final exponents = scores
        .map((value) => math.exp(value - maxScore))
        .toList();
    final denominator = exponents.fold<double>(
      0,
      (total, value) => total + value,
    );
    return exponents.map((value) => value / denominator).toList();
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

  @override
  List<AiTag> generateAiTags(String? label, double? confidence) {
    if (label == null || confidence == null) return [];
    return [AiTag(label: _translateLabel(label), confidence: confidence)];
  }

  static List<double>? _firstRow(dynamic value) {
    if (value is List && value.isNotEmpty) {
      if (value.first is List) {
        return (value.first as List)
            .cast<num>()
            .map((item) => item.toDouble())
            .toList();
      }
      return value.cast<num>().map((item) => item.toDouble()).toList();
    }
    return null;
  }
}

class _EngineOutput {
  final List<double> scores;
  final int durationMs;

  const _EngineOutput(this.scores, this.durationMs);
}
