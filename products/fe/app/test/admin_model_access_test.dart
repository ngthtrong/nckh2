import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:app/config.dart';

import 'package:app/data/datasources/admin_model_download_native.dart';
import 'package:app/data/datasources/admin_session.dart';
import 'package:app/data/datasources/inference_local_datasource.dart';
import 'package:app/data/repositories/inference_repository_impl.dart';
import 'package:app/domain/entities/ai_model_type.dart';
import 'package:app/domain/entities/user.dart';
import 'package:app/domain/repositories/network_repository.dart';
import 'package:app/domain/repositories/rescue_repository.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:app/presentation/screens/settings/settings_screen.dart';
import 'package:app/presentation/widgets/model_benchmark_card.dart';
import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

class _Adapter implements HttpClientAdapter {
  _Adapter(this.handler);
  final FutureOr<ResponseBody> Function(RequestOptions) handler;
  final requests = <RequestOptions>[];
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    return handler(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody _json(Object value) => ResponseBody.fromString(
  jsonEncode(value),
  200,
  headers: {
    Headers.contentTypeHeader: ['application/json'],
  },
);
Map<String, Object> _session({String role = 'admin'}) => {
  'token': 'test-token',
  'role': role,
  'username': 'admin',
  'expiresAt': DateTime.now()
      .toUtc()
      .add(const Duration(hours: 1))
      .toIso8601String(),
};

class _Rescue extends Fake implements RescueRepository {
  @override
  String? get connectedServerUrl => 'https://backend';
}

class _Network extends Fake implements NetworkRepository {}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('Local-looking admin name cannot grant operator admin access', () async {
    final adapter = _Adapter(
      (request) => _json(
        request.path.endsWith('/login')
            ? _session(role: 'operator')
            : {'status': 'ok'},
      ),
    );
    final session = AdminSession(dio: Dio()..httpClientAdapter = adapter);
    addTearDown(session.dispose);
    await expectLater(
      session.login('https://backend', 'admin', 'password'),
      throwsStateError,
    );
    expect(session.isAdmin, isFalse);
    expect(session.token, isNull);
    expect(adapter.requests.last.path, endsWith('/logout'));
  });

  test('Admin role revocation clears the in-memory session', () async {
    var role = 'admin';
    final adapter = _Adapter(
      (request) => _json(
        request.path.endsWith('/login')
            ? _session()
            : {'authenticated': true, 'role': role},
      ),
    );
    final session = AdminSession(dio: Dio()..httpClientAdapter = adapter);
    addTearDown(session.dispose);
    await session.login('https://backend/', 'someone', 'password');
    expect(session.isAdmin, isTrue);
    expect(await session.validate(), isTrue);
    role = 'operator';
    expect(await session.validate(), isFalse);
    expect(session.token, isNull);
    expect(
      adapter.requests
          .where((r) => r.path.endsWith('/me'))
          .first
          .headers['Authorization'],
      'Bearer test-token',
    );
  });

  test(
    'Logout while login is pending cannot restore admin privileges',
    () async {
      final pending = Completer<ResponseBody>();
      final started = Completer<void>();
      final adapter = _Adapter((request) {
        if (request.path.endsWith('/login')) {
          started.complete();
          return pending.future;
        }
        return _json({'status': 'ok'});
      });
      final session = AdminSession(dio: Dio()..httpClientAdapter = adapter);
      addTearDown(session.dispose);
      final login = session.login('https://backend', 'admin', 'password');
      final rejected = expectLater(login, throwsStateError);
      await started.future;
      await session.logout();
      pending.complete(_json(_session()));
      await rejected;
      expect(session.isAdmin, isFalse);
    },
  );

  testWidgets(
    'Ordinary local admin name sees no comparison; backend admin does',
    (tester) async {
      const pathChannel = MethodChannel('plugins.flutter.io/path_provider');
      final messenger =
          TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
      messenger.setMockMethodCallHandler(pathChannel, (_) async {
        throw PlatformException(code: 'test-storage-unavailable');
      });
      addTearDown(() => messenger.setMockMethodCallHandler(pathChannel, null));
      final session = AdminSession(
        dio: Dio()
          ..httpClientAdapter = _Adapter(
            (request) => _json(
              request.path.endsWith('/login') ? _session() : {'status': 'ok'},
            ),
          ),
      );
      final controller = AppController(
        rescueRepository: _Rescue(),
        inferenceRepository: InferenceRepositoryImpl(
          InferenceLocalDataSource(),
        ),
        networkRepository: _Network(),
        adminSession: session,
      );
      controller.currentUser = const User(
        username: 'admin',
        password: 'local',
        phone: '',
        address: '',
      );
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ListenableBuilder(
              listenable: controller,
              builder: (_, _) => SettingsScreen(controller: controller),
            ),
          ),
        ),
      );
      expect(controller.isAdmin, isFalse);
      expect(find.byType(ModelBenchmarkCard), findsNothing);
      expect(find.text('So sánh ONNX và PTE thật'), findsNothing);
      controller.switchAiModel(AiModelType.onnx);
      expect(controller.currentModel, AiModelType.pte);
      await tester.runAsync(
        () => controller.loginAdmin('admin', 'server-password'),
      );
      await tester.pump();
      if (!kAdminModelTools) {
        expect(controller.isAdmin, isFalse);
        expect(find.byType(ModelBenchmarkCard), findsNothing);
        expect(
          find.text('Dọn ONNX và dữ liệu benchmark đã tải'),
          findsOneWidget,
        );
        await tester.pumpWidget(const SizedBox());
        controller.dispose();
        return;
      }
      expect(controller.isAdmin, isTrue);
      expect(find.text('Thực nghiệm model'), findsOneWidget);
      expect(find.byType(ModelBenchmarkCard), findsNothing);
      final modelSection = find.byKey(const Key('admin-model-section'));
      await tester.ensureVisible(modelSection);
      await tester.tap(find.text('Thực nghiệm model'));
      await tester.pumpAndSettle();
      expect(find.byType(ModelBenchmarkCard), findsOneWidget);
      expect(find.text('So sánh ONNX và PTE thật'), findsOneWidget);
      controller.isModelLoading = false;
      expect(controller.beginBenchmark(), isTrue);
      await tester.pump();
      final deleteButton = find.widgetWithText(
        TextButton,
        'Xóa ONNX và tập benchmark đã tải',
      );
      expect(tester.widget<TextButton>(deleteButton).onPressed, isNull);
      controller.endBenchmark();
      await tester.pumpAndSettle();
      expect(tester.widget<TextButton>(deleteButton).onPressed, isNotNull);
      await tester.runAsync(session.logout);
      await tester.pump();
      expect(find.byType(ModelBenchmarkCard), findsNothing);
      expect(controller.currentModel, AiModelType.pte);
      await tester.pumpWidget(const SizedBox());
      controller.dispose();
    },
  );

  group('Verified model download', () {
    late Directory root;
    late Map<String, dynamic> manifest;
    final good = utf8.encode('verified ONNX model');
    late String hash;
    setUp(() async {
      root = await Directory.systemTemp.createTemp('admin-model-test-');
      hash = sha256.convert(good).toString();
      manifest = {'onnx_sha256': hash, 'pte_sha256': 'bundled-pte'};
    });
    tearDown(() async => root.delete(recursive: true));

    Future<String> download(_Adapter adapter, {CancelToken? cancel}) =>
        downloadAdminOnnx(
          server: 'https://backend',
          token: 'secret',
          cancelToken: cancel ?? CancelToken(),
          onProgress: (_, _) {},
          client: Dio()..httpClientAdapter = adapter,
          directory: root,
          bundledManifest: manifest,
        );
    ResponseBody catalog() => _json({
      'manifest': manifest,
      'artifacts': {
        'onnx': {'sha256': hash, 'bytes': good.length},
      },
    });
    ResponseBody binary(List<int> data) => ResponseBody.fromBytes(
      data,
      200,
      headers: {
        Headers.contentLengthHeader: ['${data.length}'],
      },
    );

    test(
      'Full valid download is reused only after protected catalog request',
      () async {
        final adapter = _Adapter(
          (r) => r.path.endsWith('/onnx') ? binary(good) : catalog(),
        );
        final path = await download(adapter);
        expect(await File(path).readAsBytes(), good);
        expect(await download(adapter), path);
        expect(
          adapter.requests.where((r) => r.path.endsWith('/onnx')).length,
          1,
        );
        expect(adapter.requests.length, 3);
        expect(
          adapter.requests.every(
            (r) =>
                r.headers['Authorization'] == 'Bearer secret' &&
                !r.followRedirects,
          ),
          isTrue,
        );
      },
    );

    test(
      'Corrupt bytes are rejected and partial file removed; retry succeeds',
      () async {
        final adapter = _Adapter(
          (r) => r.path.endsWith('/onnx')
              ? binary(List<int>.filled(good.length, 0))
              : catalog(),
        );
        await expectLater(download(adapter), throwsFormatException);
        expect(
          await root.list(recursive: true).where((f) => f is File).toList(),
          isEmpty,
        );
        final path = await download(
          _Adapter((r) => r.path.endsWith('/onnx') ? binary(good) : catalog()),
        );
        expect(await File(path).readAsBytes(), good);
      },
    );

    test(
      'A different model pair is rejected before downloading any bytes',
      () async {
        final adapter = _Adapter(
          (r) => _json({
            'manifest': {'onnx_sha256': hash, 'pte_sha256': 'different'},
            'artifacts': {
              'onnx': {'sha256': hash, 'bytes': good.length},
            },
          }),
        );
        await expectLater(download(adapter), throwsFormatException);
        expect(adapter.requests.length, 1);
      },
    );
  });

  test('APK asset manifest keeps PTE and excludes ONNX', () async {
    final assets = (await AssetManifest.loadFromAssetBundle(
      rootBundle,
    )).listAssets();
    expect(assets, contains('assets/models/model.pte'));
    expect(assets, isNot(contains('assets/models/model.onnx')));
  });
}
