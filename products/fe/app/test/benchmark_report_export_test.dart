import 'dart:async';
import 'dart:convert';

import 'package:app/domain/services/model_benchmark.dart';
import 'package:app/presentation/widgets/benchmark_report_export_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

ModelBenchmarkReport report() => ModelBenchmarkReport(
  datasetName: 'Tập test mức ngập',
  split: 'test',
  runtime: BenchmarkRuntime.onnx,
  complete: true,
  expectedSamples: 256,
  processedSamples: 256,
  failedSamples: 0,
  warmupRuns: 5,
  warmupErrors: 0,
  accuracy: 1,
  macroF1: 1,
  confusionMatrix: const {
    'low': {'low': 256},
  },
  classMetrics: const {},
  meanLatencyMs: 10,
  medianLatencyMs: 10,
  p95LatencyMs: 10,
  elapsedMs: 2560,
  predictions: List.generate(
    256,
    (i) => {
      'id': 'mẫu-$i-${'x' * 64}',
      'truth': 'low',
      'prediction': 'low',
      'confidence': 0.9,
      'latencyMs': 10.0,
    },
  ),
);

void main() {
  const channel = MethodChannel('rescue/benchmark_export');
  final binding = TestWidgetsFlutterBinding.ensureInitialized();

  tearDown(() {
    binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, null);
  });

  testWidgets('exports all 256 predictions beyond clipboard size', (
    tester,
  ) async {
    final result = Completer<bool>();
    MethodCall? call;
    binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, (value) {
      call = value;
      return result.future;
    });
    final benchmark = report();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: BenchmarkReportExportButton(report: benchmark)),
      ),
    );
    await tester.tap(find.text('Tải JSON'));
    await tester.pump();

    expect(call!.method, 'saveJson');
    final arguments = call!.arguments as Map;
    expect(arguments['fileName'], matches(r'^benchmark_onnx_.*\.json$'));
    final content = arguments['json'] as String;
    expect(utf8.encode(content).length, greaterThan(20000));
    expect(jsonDecode(content), benchmark.toJson());
    expect((jsonDecode(content)['predictions'] as List).length, 256);
    expect(
      tester.widget<TextButton>(find.byType(TextButton)).onPressed,
      isNull,
    );

    result.complete(true);
    await tester.pumpAndSettle();
    expect(find.textContaining('Đã lưu file'), findsOneWidget);
    expect(
      tester.widget<TextButton>(find.byType(TextButton)).onPressed,
      isNotNull,
    );
    expect(tester.takeException(), isNull);
  });

  for (final fails in [false, true]) {
    testWidgets(fails ? 'save error allows retry' : 'cancel allows retry', (
      tester,
    ) async {
      var calls = 0;
      binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, (
        _,
      ) async {
        calls++;
        if (fails) throw PlatformException(code: 'export_failed');
        return false;
      });
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: BenchmarkReportExportButton(report: report())),
        ),
      );
      await tester.tap(find.text('Tải JSON'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Đã lưu file'), findsNothing);
      expect(
        find.text('Không lưu được file JSON. Vui lòng thử lại.'),
        fails ? findsOneWidget : findsNothing,
      );
      await tester.tap(find.text('Tải JSON'));
      await tester.pumpAndSettle();
      expect(calls, 2);
      expect(tester.takeException(), isNull);
    });
  }
}
