import 'dart:async';
import 'dart:typed_data';

import '../entities/ai_model_type.dart';
import '../repositories/inference_repository.dart';

enum BenchmarkRuntime { onnx, pte, both }

class BenchmarkSample {
  final String id;
  final String label;
  final int offset;
  final int length;

  const BenchmarkSample({
    required this.id,
    required this.label,
    required this.offset,
    required this.length,
  });

  factory BenchmarkSample.fromJson(Map<String, dynamic> json) {
    final id = json['id'];
    final label = json['label'];
    final offset = json['offset'];
    final length = json['length'];
    if (id is! String || label is! String || offset is! int || length is! int) {
      throw const FormatException('Invalid benchmark sample.');
    }
    if (offset < 8 || length <= 0) {
      throw const FormatException('Invalid benchmark sample range.');
    }
    return BenchmarkSample(
      id: id,
      label: label,
      offset: offset,
      length: length,
    );
  }
}

class ModelBenchmarkReport {
  final String datasetName;
  final String split;
  final BenchmarkRuntime runtime;
  final bool complete;
  final int expectedSamples;
  final int processedSamples;
  final int failedSamples;
  final int warmupRuns;
  final int warmupErrors;
  final double? accuracy;
  final double? macroF1;
  final Map<String, Map<String, int>> confusionMatrix;
  final Map<String, Map<String, double?>> classMetrics;
  final double? meanLatencyMs;
  final double? medianLatencyMs;
  final double? p95LatencyMs;
  final double elapsedMs;
  final List<Map<String, Object?>> predictions;

  const ModelBenchmarkReport({
    required this.datasetName,
    required this.split,
    required this.runtime,
    required this.complete,
    required this.expectedSamples,
    required this.processedSamples,
    required this.failedSamples,
    required this.warmupRuns,
    required this.warmupErrors,
    required this.accuracy,
    required this.macroF1,
    required this.confusionMatrix,
    required this.classMetrics,
    required this.meanLatencyMs,
    required this.medianLatencyMs,
    required this.p95LatencyMs,
    required this.elapsedMs,
    required this.predictions,
  });

  Map<String, Object?> toJson() => {
    'dataset': datasetName,
    'split': split,
    'runtime': runtime.name,
    'complete': complete,
    'expectedSamples': expectedSamples,
    'processedSamples': processedSamples,
    'failedSamples': failedSamples,
    'warmupRuns': warmupRuns,
    'warmupErrors': warmupErrors,
    'accuracy': accuracy,
    'macroF1': macroF1,
    'confusionMatrix': confusionMatrix,
    'classMetrics': classMetrics,
    'latency': {
      'meanMs': meanLatencyMs,
      'medianMs': medianLatencyMs,
      'p95Ms': p95LatencyMs,
    },
    'elapsedMs': elapsedMs,
    'predictions': predictions,
  };
}

class ModelBenchmarkProgress {
  final BenchmarkRuntime runtime;
  final int completed;
  final int total;

  const ModelBenchmarkProgress(this.runtime, this.completed, this.total);
}

class ModelBenchmarkRunner {
  const ModelBenchmarkRunner();

  Future<List<ModelBenchmarkReport>> run({
    required InferenceRepository repository,
    required List<BenchmarkSample> samples,
    required List<String> labels,
    required String datasetName,
    required BenchmarkRuntime runtime,
    required Future<Uint8List> Function(BenchmarkSample sample) loadImage,
    required bool Function() cancelled,
    required void Function(ModelBenchmarkProgress progress) onProgress,
    int warmupRuns = 5,
  }) async {
    if (samples.isEmpty || labels.isEmpty) {
      throw ArgumentError('Benchmark needs labeled samples.');
    }
    if (samples.any((sample) => !labels.contains(sample.label))) {
      throw ArgumentError('A sample label is not in the benchmark manifest.');
    }
    if (runtime != BenchmarkRuntime.both &&
        runtime == BenchmarkRuntime.pte &&
        !repository.pteReady) {
      throw StateError('ExecuTorch is not ready on this device.');
    }

    final oldModel = repository.currentModel;
    final oldDual = repository.isDualComparison;
    final models = runtime == BenchmarkRuntime.both
        ? const [AiModelType.onnx, AiModelType.pte]
        : [
            runtime == BenchmarkRuntime.onnx
                ? AiModelType.onnx
                : AiModelType.pte,
          ];
    final reports = <ModelBenchmarkReport>[];
    try {
      repository.setDualComparison(false);
      for (final model in models) {
        if (model == AiModelType.pte && !repository.pteReady) {
          throw StateError('ExecuTorch is not ready on this device.');
        }
        repository.setModel(model);
        reports.add(
          await _runModel(
            repository: repository,
            samples: samples,
            labels: labels,
            datasetName: datasetName,
            runtime: model == AiModelType.onnx
                ? BenchmarkRuntime.onnx
                : BenchmarkRuntime.pte,
            warmupRuns: warmupRuns,
            loadImage: loadImage,
            cancelled: cancelled,
            onProgress: onProgress,
          ),
        );
        if (cancelled()) break;
      }
      return reports;
    } finally {
      repository.setDualComparison(oldDual);
      repository.setModel(oldModel);
    }
  }

  Future<ModelBenchmarkReport> _runModel({
    required InferenceRepository repository,
    required List<BenchmarkSample> samples,
    required List<String> labels,
    required String datasetName,
    required BenchmarkRuntime runtime,
    required int warmupRuns,
    required Future<Uint8List> Function(BenchmarkSample sample) loadImage,
    required bool Function() cancelled,
    required void Function(ModelBenchmarkProgress progress) onProgress,
  }) async {
    final clock = Stopwatch()..start();
    var warmupErrors = 0;
    var warmupCompleted = 0;
    if (warmupRuns > 0) {
      final firstImage = await loadImage(samples.first);
      for (var i = 0; i < warmupRuns && !cancelled(); i++) {
        if (await repository.classifyImage(firstImage) == null) warmupErrors++;
        warmupCompleted++;
      }
    }

    final matrix = {
      for (final truth in labels)
        truth: {
          for (final prediction in [...labels, 'unclassified']) prediction: 0,
        },
    };
    final latencies = <double>[];
    final predictions = <Map<String, Object?>>[];
    var failures = 0;
    var processed = 0;

    for (final sample in samples) {
      if (cancelled()) break;
      String? predicted;
      double? confidence;
      double? latency;
      String? error;
      try {
        final bytes = await loadImage(sample);
        final call = Stopwatch()..start();
        final result = await repository.classifyImage(bytes);
        call.stop();
        latency = result == null ? null : call.elapsedMicroseconds / 1000;
        predicted = result?.label;
        confidence = result?.confidence;
        if (predicted == null || !labels.contains(predicted)) {
          predicted = null;
          error = 'Inference returned no valid label';
        } else if (latency != null) {
          latencies.add(latency);
        }
      } catch (e) {
        error = e.toString();
      }

      processed++;
      if (predicted == null) failures++;
      matrix[sample.label]![predicted ?? 'unclassified'] =
          matrix[sample.label]![predicted ?? 'unclassified']! + 1;
      predictions.add({
        'id': sample.id,
        'truth': sample.label,
        'prediction': predicted,
        'confidence': confidence,
        'latencyMs': latency,
        'error': ?error,
      });
      onProgress(ModelBenchmarkProgress(runtime, processed, samples.length));
    }

    final classMetrics = <String, Map<String, double?>>{};
    var correct = 0;
    final f1s = <double>[];
    for (final label in labels) {
      final truePositives = matrix[label]![label]!;
      correct += truePositives;
      final predictedCount = matrix.values.fold<int>(
        0,
        (sum, row) => sum + row[label]!,
      );
      final support = matrix[label]!.values.fold<int>(
        0,
        (sum, count) => sum + count,
      );
      final precision = predictedCount == 0
          ? 0.0
          : truePositives / predictedCount;
      final recall = support == 0 ? 0.0 : truePositives / support;
      final f1 = precision + recall == 0
          ? 0.0
          : 2 * precision * recall / (precision + recall);
      classMetrics[label] = {
        'precision': precision,
        'recall': recall,
        'f1': f1,
      };
      f1s.add(f1);
    }

    clock.stop();
    return ModelBenchmarkReport(
      datasetName: datasetName,
      split: 'test',
      runtime: runtime,
      complete: processed == samples.length,
      expectedSamples: samples.length,
      processedSamples: processed,
      failedSamples: failures,
      warmupRuns: warmupCompleted,
      warmupErrors: warmupErrors,
      accuracy: processed == 0 ? null : correct / processed,
      macroF1: f1s.isEmpty ? null : f1s.reduce((a, b) => a + b) / f1s.length,
      confusionMatrix: matrix,
      classMetrics: classMetrics,
      meanLatencyMs: latencies.isEmpty
          ? null
          : latencies.reduce((a, b) => a + b) / latencies.length,
      medianLatencyMs: _percentile(latencies, .5),
      p95LatencyMs: _percentile(latencies, .95),
      elapsedMs: clock.elapsedMicroseconds / 1000,
      predictions: predictions,
    );
  }

  static double? _percentile(List<double> values, double p) {
    if (values.isEmpty) return null;
    final sorted = [...values]..sort();
    return sorted[((sorted.length * p).ceil() - 1).clamp(0, sorted.length - 1)];
  }
}
