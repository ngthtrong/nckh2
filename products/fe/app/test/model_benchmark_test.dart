import 'package:app/core/platform/benchmark_environment.dart';
import 'package:app/data/datasources/admin_session.dart';
import 'package:app/domain/entities/ai_model_type.dart';
import 'package:app/domain/repositories/inference_repository.dart';
import 'package:app/domain/repositories/network_repository.dart';
import 'package:app/domain/repositories/rescue_repository.dart';
import 'package:app/domain/services/model_benchmark.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

class _Inference extends Fake implements InferenceRepository {
  @override
  bool get ready => true;
  @override
  AiModelType currentModel = AiModelType.pte;
  @override
  bool isDualComparison = true;
  @override
  bool get onnxReady => true;
  @override
  bool get pteReady => true;
  AiModelType? wrongResultType;

  @override
  void setModel(AiModelType model) => currentModel = model;
  @override
  void setDualComparison(bool value) => isDualComparison = value;
  @override
  void setComparisonAccess(bool value) {}
  @override
  Future<InferenceResult?> classifyImage(Uint8List bytes) async => (
    label: 'low',
    confidence: 1.0,
    durationMs: 2,
    modelType: wrongResultType ?? currentModel,
  );
}

class _Admin extends AdminSession {
  _Admin() {
    server = 'https://backend';
  }
  @override
  bool get isAdmin => true;
}

class _Rescue extends Fake implements RescueRepository {
  @override
  String get connectedServerUrl => 'https://backend';
}

class _Network extends Fake implements NetworkRepository {}

void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('rescue/benchmark_export');
  tearDown(
    () =>
        binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, null),
  );
  final samples = List.generate(
    2,
    (i) => BenchmarkSample(id: '$i', label: 'low', offset: 8, length: 1),
  );

  Future<List<ModelBenchmarkReport>> run(
    _Inference repository, {
    BenchmarkRuntime runtime = BenchmarkRuntime.onnx,
    int warmups = 0,
    Map<String, Object?> provenance = const {},
    void Function(ModelBenchmarkProgress)? onProgress,
  }) => const ModelBenchmarkRunner().run(
    repository: repository,
    samples: samples,
    labels: ['low'],
    datasetName: 'fixed split',
    runtime: runtime,
    warmupRuns: warmups,
    provenance: provenance,
    loadImage: (_) async => Uint8List(1),
    cancelled: () => false,
    onProgress: onProgress ?? (_) {},
  );

  test(
    'wrong runtime result aborts and restores settings, including warmup',
    () async {
      for (final warmups in [0, 1]) {
        final repo = _Inference()..wrongResultType = AiModelType.pte;
        await expectLater(run(repo, warmups: warmups), throwsStateError);
        expect(repo.currentModel, AiModelType.pte);
        expect(repo.isDualComparison, isTrue);
      }
    },
  );

  test(
    'controller refuses runtime and dual switches while a benchmark holds the lock',
    () {
      final repo = _Inference()..isDualComparison = false;
      final controller = AppController(
        rescueRepository: _Rescue(),
        inferenceRepository: repo,
        networkRepository: _Network(),
        adminSession: _Admin(),
      );
      addTearDown(controller.dispose);
      controller.isModelLoading = false;
      expect(controller.beginBenchmark(), isTrue);
      controller.switchAiModel(AiModelType.onnx);
      controller.toggleDualComparison(true);
      expect(repo.currentModel, AiModelType.pte);
      expect(repo.isDualComparison, isFalse);
      controller.endBenchmark();
      controller.switchAiModel(AiModelType.onnx);
      controller.toggleDualComparison(true);
      expect(repo.currentModel, AiModelType.onnx);
      expect(repo.isDualComparison, isTrue);
    },
  );

  test('runtime changed mid-run cannot produce a mislabeled report', () async {
    final repo = _Inference();
    await expectLater(
      run(repo, onProgress: (_) => repo.setModel(AiModelType.pte)),
      throwsStateError,
    );
    expect(repo.currentModel, AiModelType.pte);
  });

  test(
    'both runtimes retain shared run provenance and their own artifact hash',
    () async {
      binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, (
        call,
      ) async {
        expect(call.method, 'getEnvironment');
        return {
          'device': {'model': 'Redmi test', 'androidSdk': 33},
          'app': {'versionName': '0.1.0', 'versionCode': 1},
        };
      });
      final environment = await benchmarkEnvironment();
      final reports = await run(
        _Inference(),
        runtime: BenchmarkRuntime.both,
        provenance: {...environment, 'splitCsvSha256': 'split-sha'},
      );
      expect(reports.length, 2);
      expect(reports[0].provenance['runId'], reports[1].provenance['runId']);
      for (final report in reports) {
        final json = report.toJson();
        final provenance = json['provenance'] as Map;
        expect(json['schemaVersion'], 2);
        expect(json['accuracy'], 1);
        expect((json['predictions'] as List).length, 2);
        expect(provenance['splitCsvSha256'], 'split-sha');
        expect(provenance['device'], {'model': 'Redmi test', 'androidSdk': 33});
        expect(
          (provenance['model'] as Map)['checkpoint_sha256'],
          matches(r'^[a-f0-9]{64}$'),
        );
        expect(
          provenance['artifactSha256'],
          (environment['model'] as Map)['${report.runtime.name}_sha256'],
        );
        expect(
          DateTime.parse(
            provenance['finishedAtUtc'] as String,
          ).isBefore(DateTime.parse(provenance['startedAtUtc'] as String)),
          isFalse,
        );
      }
    },
  );
}
