import 'dart:convert';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/services.dart';
import 'package:onnxruntime/onnxruntime.dart';

/// Kết quả phân loại on-device.
typedef ClassifyResult = ({String label, double confidence, int durationMs});

/// Chạy model ONNX ngay trên thiết bị — hoạt động offline hoàn toàn.
///
/// Preprocessing phải KHỚP với lúc train: resize 224x224 + normalize
/// ImageNet mean/std. Nếu bạn train với mean/std khác, sửa [mean]/[std].
class InferenceService {
  static const int _inputSize = 224;
  static const _mean = [0.485, 0.456, 0.406];
  static const _std = [0.229, 0.224, 0.225];

  OrtSession? _session;
  List<String> _labels = [];

  bool get ready => _session != null;

  Future<void> load() async {
    try {
      final raw = await rootBundle.load('assets/models/model.onnx');
      OrtEnv.instance.init();
      _session = OrtSession.fromBuffer(raw.buffer.asUint8List(), OrtSessionOptions());
    } catch (_) {
      // ponytail: chưa có assets/models/model.onnx → app vẫn chạy để test
      // flow gửi/queue/metrics; nạp model khi convert xong (.pth → ONNX INT8).
      _session = null;
    }
    try {
      final s = await rootBundle.loadString('assets/labels.json');
      _labels = List<String>.from(jsonDecode(s) as List);
    } catch (_) {
      _labels = [];
    }
  }

  /// Trả null nếu model chưa nạp hoặc decode lỗi.
  Future<ClassifyResult?> classify(Uint8List jpegBytes) async {
    final session = _session;
    if (session == null) return null;
    final sw = Stopwatch()..start();
    try {
      // Decode + resize bằng decoder native của Flutter (nhanh, không cần package).
      final codec = await ui.instantiateImageCodec(jpegBytes,
          targetWidth: _inputSize, targetHeight: _inputSize);
      final frame = await codec.getNextFrame();
      final bd =
          await frame.image.toByteData(format: ui.ImageByteFormat.rawStraightRgba);
      frame.image.dispose();
      if (bd == null) return null;
      final rgba = bd.buffer.asUint8List();
      final pxCount = rgba.length ~/ 4;

      // NCHW float32 normalize ImageNet.
      final data = Float32List(3 * pxCount);
      for (var i = 0; i < pxCount; i++) {
        data[i] = ((rgba[i * 4] / 255.0) - _mean[0]) / _std[0];
        data[pxCount + i] = ((rgba[i * 4 + 1] / 255.0) - _mean[1]) / _std[1];
        data[2 * pxCount + i] = ((rgba[i * 4 + 2] / 255.0) - _mean[2]) / _std[2];
      }

      final input = OrtValueTensor.createTensorWithDataList(
          data, [1, 3, _inputSize, _inputSize]);
      final runOptions = OrtRunOptions();
      try {
        final inputName = session.inputNames.first;
        final outputs =
            await session.runAsync(runOptions, {inputName: input});
        final probs = _firstRow(outputs?[0]?.value);
        for (final o in outputs ?? const []) {
          o?.release();
        }
        if (probs == null || probs.isEmpty) return null;
        var best = 0;
        for (var i = 1; i < probs.length; i++) {
          if (probs[i] > probs[best]) best = i;
        }
        sw.stop();
        final label =
            (best >= 0 && best < _labels.length) ? _labels[best] : 'class_$best';
        return (
          label: label,
          confidence: probs[best].toDouble(),
          durationMs: sw.elapsedMilliseconds,
        );
      } finally {
        input.release();
        runOptions.release();
      }
    } catch (_) {
      return null;
    }
  }

  /// Output có thể là [[p0,p1,...]] hoặc [p0,p1,...].
  static List<double>? _firstRow(dynamic value) {
    if (value is List && value.isNotEmpty) {
      if (value.first is List) {
        final row = (value.first as List).cast<num>();
        return row.map((e) => e.toDouble()).toList();
      }
      return value.cast<num>().map((e) => e.toDouble()).toList();
    }
    if (value is Map) {
      // Một số model trả {label: prob} — lấy giá trị lớn nhất theo thứ tự.
      return value.values.cast<num>().map((e) => e.toDouble()).toList();
    }
    return null;
  }
}
