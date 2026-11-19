import 'dart:async';
import 'dart:io';

import 'package:app/config.dart';
import 'package:app/data/datasources/admin_session.dart';
import 'package:app/domain/repositories/inference_repository.dart';
import 'package:app/domain/repositories/network_repository.dart';
import 'package:app/domain/repositories/rescue_repository.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:app/presentation/widgets/model_benchmark_card.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

class _Inference extends Fake implements InferenceRepository {
  @override
  bool get ready => true;
  @override
  bool get pteReady => true;
  @override
  bool get onnxReady => true;
  @override
  void setComparisonAccess(bool enabled) {}
  @override
  Future<void> unloadComparisonModel() async {}
}

class _Admin extends AdminSession {
  _Admin() {
    server = 'https://backend';
  }

  @override
  bool get isAdmin => true;
  @override
  String get token => 'test-token';
  @override
  Future<bool> validate() async => true;
}

class _Rescue extends Fake implements RescueRepository {
  @override
  String get connectedServerUrl => 'https://backend';
}

class _Network extends Fake implements NetworkRepository {}

class _StalledAdapter implements HttpClientAdapter {
  _StalledAdapter(this.controller);

  final AppController controller;
  final receiveTimeouts = <Duration?>[];
  final preparingDuringDownload = <bool>[];
  final benchmarkBlockedDuringDownload = <bool>[];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    receiveTimeouts.add(options.receiveTimeout);
    preparingDuringDownload.add(controller.isPreparingBenchmark);
    benchmarkBlockedDuringDownload.add(!controller.beginBenchmark());
    // Exercise Dio's stream timeout without waiting the production 60 seconds.
    options.receiveTimeout = const Duration(milliseconds: 50);
    final stream = StreamController<Uint8List>()..add(Uint8List.fromList([1]));
    return ResponseBody(
      stream.stream,
      200,
      headers: {
        Headers.contentLengthHeader: ['100'],
      },
      onClose: () => unawaited(stream.close()),
    );
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  testWidgets(
    'stalled package download times out, removes partial file and unlocks retry',
    (tester) async {
      final directory = Directory.systemTemp.createTempSync(
        'benchmark-timeout-',
      );
      const pathChannel = MethodChannel('plugins.flutter.io/path_provider');
      final messenger =
          TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
      var storageRequests = 0;
      messenger.setMockMethodCallHandler(pathChannel, (_) async {
        if (storageRequests++ == 0) {
          throw PlatformException(code: 'no-cached-package');
        }
        return directory.path;
      });
      final controller = AppController(
        rescueRepository: _Rescue(),
        inferenceRepository: _Inference(),
        networkRepository: _Network(),
        adminSession: _Admin(),
      );
      final adapter = _StalledAdapter(controller);
      final dio = Dio()..httpClientAdapter = adapter;
      addTearDown(() async {
        await tester.pumpWidget(const SizedBox());
        controller.dispose();
        messenger.setMockMethodCallHandler(pathChannel, null);
        await tester.runAsync(() => directory.delete(recursive: true));
      });

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ModelBenchmarkCard(controller: controller, dio: dio),
          ),
        ),
      );
      await tester.pumpAndSettle();

      final downloadButton = find.widgetWithText(
        FilledButton,
        'Tải gói benchmark (~40 MB)',
      );
      final cleanupButton = find.widgetWithText(
        TextButton,
        'Xóa ONNX và tập benchmark đã tải',
      );
      for (var attempt = 1; attempt <= 2; attempt++) {
        final download =
            tester.widget<FilledButton>(downloadButton).onPressed!
                as Future<void> Function();
        await tester.runAsync(download);
        await tester.pump();

        expect(adapter.receiveTimeouts, hasLength(attempt));
        expect(adapter.receiveTimeouts.last, const Duration(seconds: 60));
        expect(controller.isPreparingBenchmark, isFalse);
        expect(
          File('${directory.path}/benchmark.rhb.part').existsSync(),
          isFalse,
        );
        expect(
          tester.widget<FilledButton>(downloadButton).onPressed,
          isNotNull,
        );
        expect(tester.widget<TextButton>(cleanupButton).onPressed, isNotNull);
        expect(controller.beginBenchmark(), isTrue);
        controller.endBenchmark();
      }
      expect(adapter.preparingDuringDownload, [true, true]);
      expect(adapter.benchmarkBlockedDuringDownload, [true, true]);
      expect(
        find.text('Không tải được gói benchmark từ server.'),
        findsOneWidget,
      );

      final cleanup =
          tester.widget<TextButton>(cleanupButton).onPressed!
              as Future<void> Function();
      await tester.runAsync(cleanup);
      await tester.pump();
      expect(controller.isDeletingBenchmarkResources, isFalse);
      expect(controller.benchmarkResourcesRevision, 1);
      expect(tester.widget<FilledButton>(downloadButton).onPressed, isNotNull);
      expect(tester.widget<TextButton>(cleanupButton).onPressed, isNotNull);
    },
    skip: !kAdminModelTools,
  );
}
