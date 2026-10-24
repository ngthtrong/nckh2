// Kiểm tra đọc gói RHE1, ràng buộc checkpoint và phát hiện báo cáo trùng; không chạy AI giả.
import 'dart:convert';
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:crypto/crypto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:app/domain/services/mobile_e2e_runner.dart';
import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:dio/dio.dart';
import 'package:app/data/models/rescue_record_payload.dart';
import 'package:app/domain/entities/ai_tag.dart';

class RecoveryController extends Fake implements AppController {
  int syncCalls = 0;
  int unlocks = 0;
  int pending = 0;
  @override
  int get pendingCount => pending;
  @override
  bool get isBusy => false;
  @override
  bool beginBenchmark() => true;
  @override
  void endBenchmark() {
    unlocks++;
  }

  @override
  Future<void> syncPending({bool immediate = true}) async {
    syncCalls++;
  }
}

class RetryRunner extends RecoveryRunner {
  int executions = 0;
  RetryRunner(super.controller, super.package, super.state, super.existing);
  @override
  Future<String> onlineStage(String stage, String network) async {
    executions++;
    if (executions == 1) throw StateError('Lỗi mạng');
    return 'Đã gửi lại';
  }
}

class RecoveryRunner extends MobileE2eRunner {
  final RescueRecord existing;
  RecoveryRunner(
    RecoveryController controller,
    MobileE2ePackage package,
    MobileE2eCheckpoint state,
    this.existing,
  ) : super(
        controller: controller,
        package: package,
        state: state,
        dio: Dio(),
        server: 'http://test',
        imagePath: 'test.jpg',
        save: (_) async {},
        cancelled: () => false,
      );
  @override
  Future<void> preflight() async {}
  @override
  Future<void> profile(String value) async {}
  @override
  Future<RescueRecord> report(String stage, {required bool image}) async =>
      existing;
  @override
  Future<Map<String, dynamic>> observations() async => {
    'reports': [
      {'id': existing.id, 'description': existing.description},
    ],
    'review': [],
  };
  @override
  Future<Map<String, dynamic>> waitReport(
    String id, {
    bool image = false,
  }) async => {'id': existing.id};
}

Uint8List packageBytes() {
  final image = Uint8List.fromList([1, 2, 3]);
  final manifest = {
    'schemaVersion': 1,
    'sessionId': '2026-10-23_14-30-00-123456_mobile_run_001',
    'goldRun': 'run_001',
    'stages': mobileE2eStages,
    'model': {
      'runtime': 'pte',
      'seed': 1024,
      'variant': 'pruning',
      'sha256': 'a' * 64,
    },
    'image': {
      'relativePath': 'high/test.jpg',
      'label': 'high',
      'length': 3,
      'sha256': sha256.convert(image).toString(),
    },
  };
  final header = utf8.encode(jsonEncode(manifest));
  final length = ByteData(4)..setUint32(0, header.length, Endian.big);
  return Uint8List.fromList([
    ...ascii.encode('RHE1'),
    ...length.buffer.asUint8List(),
    ...header,
    ...image,
  ]);
}

void main() {
  test(
    'lỗi thủ công cần ghi chú và giữ lịch sử khi kiểm tra lại đạt',
    () async {
      final data = packageBytes();
      final package = MobileE2ePackage.decode(
        data,
        sha256.convert(data).toString(),
      );
      final state = MobileE2eCheckpoint(package, 'phone');
      final runner = RecoveryRunner(
        RecoveryController(),
        package,
        state,
        RescueRecord(
          id: 'manual',
          createdAt: DateTime(2026),
          lat: null,
          lng: null,
          description: 'manual',
          sendMode: 'textOnly',
        ),
      );
      await expectLater(
        runner.recordManual('manual_android_ui', passed: false),
        throwsArgumentError,
      );
      expect(state.checks['manual_android_ui']!['status'], 'NOT_RUN');
      await runner.recordManual(
        'manual_android_ui',
        passed: false,
        detail: 'Lịch sử thiếu ảnh',
        reportId: 'post-1',
        evidenceFile: 'case7.png',
      );
      expect(state.checks['manual_android_ui']!['status'], 'FAIL');
      await runner.recordManual(
        'manual_android_ui',
        passed: true,
        detail: 'Đã kiểm tra lại',
      );
      expect(state.checks['manual_android_ui']!['status'], 'PASS');
      final history = state.evidence['manualChecks'] as List;
      expect(history.length, 2);
      expect(history.first['detail'], 'Lịch sử thiếu ảnh');
      expect(history.first['reportId'], 'post-1');
      await expectLater(
        runner.recordManual('dashboard', passed: true),
        throwsArgumentError,
      );
    },
  );
  TestWidgetsFlutterBinding.ensureInitialized();
  test(
    'case FAIL chạy lại thành PASS, tiếp tục case sau và không mất lỗi cũ',
    () async {
      final bytes = packageBytes();
      final fixture = MobileE2ePackage.decode(
        bytes,
        sha256.convert(bytes).toString(),
      );
      final state = MobileE2eCheckpoint(fixture, 'installation');
      final runner = RetryRunner(
        RecoveryController(),
        fixture,
        state,
        RescueRecord(
          id: 'test',
          sendMode: 'textOnly',
          createdAt: DateTime(2026),
          lat: null,
          lng: null,
        ),
      );
      await expectLater(runner.runNext(), throwsStateError);
      expect(state.checks['online']!['status'], 'FAIL');
      await runner.retryStage('online');
      expect(state.checks['online']!['status'], 'PASS');
      expect(state.nextStage, 'offline_recovery');
      final previous = (state.evidence['attemptHistory'] as List).single;
      expect((previous['checks'] as List).first['status'], 'FAIL');
    },
  );
  test('hàng đợi chưa đồng bộ thì không reset run hoặc case', () async {
    final bytes = packageBytes();
    final fixture = MobileE2ePackage.decode(
      bytes,
      sha256.convert(bytes).toString(),
    );
    final state = MobileE2eCheckpoint(fixture, 'installation');
    state.checks['online']!['status'] = 'PASS';
    final runner = RetryRunner(
      RecoveryController()..pending = 1,
      fixture,
      state,
      RescueRecord(
        id: 'test',
        sendMode: 'textOnly',
        createdAt: DateTime(2026),
        lat: null,
        lng: null,
      ),
    );
    await expectLater(runner.restart(), throwsStateError);
    await expectLater(runner.retryStage('online'), throwsStateError);
    expect(state.checks['online']!['status'], 'PASS');
    expect(state.evidence.containsKey('attemptHistory'), isFalse);
  });
  test('chạy lại case giữ lịch sử, tạo marker mới và hủy feedback cũ', () {
    final bytes = packageBytes();
    final fixture = MobileE2ePackage.decode(
      bytes,
      sha256.convert(bytes).toString(),
    );
    final state = MobileE2eCheckpoint(fixture, 'installation');
    state.checks['online']!['status'] = 'FAIL';
    state.checks['feedback']!['status'] = 'PASS';
    state.reports['online'] = 'old-report';
    state.intents['online'] = 'old-marker';
    state.checks['adaptive_300']!['status'] = 'PASS';
    state.resetStage('online');
    expect(state.checks['online']!['status'], 'NOT_RUN');
    expect(state.checks['feedback']!['status'], 'NOT_RUN');
    expect(state.checks['adaptive_300']!['status'], 'PASS');
    expect(state.reports.containsKey('online'), isFalse);
    expect(
      state.intents['online'],
      startsWith('Benchmark ${state.sessionId} online attempt '),
    );
    expect(
      (state.evidence['attemptHistory'] as List).single['reports']['online'],
      'old-report',
    );
    final restored = MobileE2eCheckpoint.restore(
      fixture,
      'installation',
      state.toJson(),
    );
    expect(restored.intents['online'], state.intents['online']);
  });
  test('chạy lại toàn run mở lại mọi case và giữ môi trường/lịch sử', () {
    final bytes = packageBytes();
    final fixture = MobileE2ePackage.decode(
      bytes,
      sha256.convert(bytes).toString(),
    );
    final state = MobileE2eCheckpoint(fixture, 'installation');
    state.environment = {'device': 'real-device'};
    for (final check in state.checks.values) {
      check['status'] = 'PASS';
    }
    state.skipped.add('no_gps');
    state.evidence['offlineObserved'] = {'reportId': 'old'};
    state.restart();
    expect(state.nextStage, 'online');
    expect(state.checks.values.every((c) => c['status'] == 'NOT_RUN'), isTrue);
    expect(state.skipped, isEmpty);
    expect(state.evidence.containsKey('offlineObserved'), isFalse);
    expect(state.environment['device'], 'real-device');
    expect(state.evidence['attemptHistory'], hasLength(1));
    expect(state.intents, hasLength(6));
  });
  test('đối chiếu nội dung ảnh nén và từ chối ảnh khác', () async {
    Future<Uint8List> picture(ui.Color color) async {
      final recorder = ui.PictureRecorder();
      ui.Canvas(recorder).drawColor(color, ui.BlendMode.src);
      final painting = recorder.endRecording();
      final image = await painting.toImage(8, 8);
      try {
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        return bytes!.buffer.asUint8List();
      } finally {
        image.dispose();
        painting.dispose();
      }
    }

    final red = await picture(const ui.Color(0xffff0000));
    final blue = await picture(const ui.Color(0xff0000ff));
    expect(
      (await verifyMobileE2eImage(red, red, fullImage: false))['pixelMae'],
      0,
    );
    await expectLater(
      verifyMobileE2eImage(red, blue, fullImage: false),
      throwsStateError,
    );
  });
  test('ảnh gốc nhận sai byte thì không được PASS', () async {
    final image = Uint8List.fromList([1, 2, 3]);
    expect(
      (await verifyMobileE2eImage(image, image, fullImage: true))['method'],
      'sha256',
    );
    await expectLater(
      verifyMobileE2eImage(
        image,
        Uint8List.fromList([3, 2, 1]),
        fullImage: true,
      ),
      throwsStateError,
    );
  });
  test('server đổi metadata hoặc AI tag thì không được PASS', () {
    final record = RescueRecord(
      id: 'post-1',
      createdAt: DateTime.utc(2026),
      lat: 10,
      lng: 106,
      trappedCount: 1,
      description: 'Benchmark 2026-10-23_14-30-00-123456_mobile_run_001 online',
      sendMode: 'textOnly',
      aiTags: [const AiTag(label: 'high', confidence: .95)],
    );
    final remote = rescueRecordPayload(record);
    validateMobileE2eMetadata(record, remote);
    expect(
      () => validateMobileE2eMetadata(record, {...remote, 'trappedCount': 5}),
      throwsStateError,
    );
    expect(
      () => validateMobileE2eMetadata(record, {...remote, 'aiTags': []}),
      throwsStateError,
    );
  });
  for (final stage in ['online', 'offline_recovery']) {
    test(
      'gián đoạn $stage phục hồi cùng ID và giữ NOT_RUN khi mất bằng chứng',
      () async {
        final bytes = packageBytes();
        final package = MobileE2ePackage.decode(
          bytes,
          sha256.convert(bytes).toString(),
        );
        final state = MobileE2eCheckpoint(package, 'installation');
        if (stage == 'offline_recovery') {
          state.checks['online']!['status'] = 'PASS';
        }
        final record = RescueRecord(
          id: 'post-existing',
          createdAt: DateTime(2026),
          lat: null,
          lng: null,
          description:
              'Benchmark 2026-10-23_14-30-00-123456_mobile_run_001 $stage',
          sendMode: 'queuedOffline',
        );
        state.reports[stage] = record.id;
        state.intents[stage] = record.description;
        final controller = RecoveryController();
        final runner = RecoveryRunner(controller, package, state, record);
        await runner.runNext();
        expect(state.checks[stage]!['status'], 'NOT_RUN');
        expect(state.skipped, contains(stage));
        expect(state.reports[stage], 'post-existing');
        expect(controller.syncCalls, 1);
        expect(controller.unlocks, 1);
      },
    );
  }
  test('đọc đúng gói và từ chối ảnh bị sửa', () {
    final bytes = packageBytes();
    final hash = sha256.convert(bytes).toString();
    expect(MobileE2ePackage.decode(bytes, hash).manifest['goldRun'], 'run_001');
    bytes[bytes.length - 1] ^= 1;
    expect(() => MobileE2ePackage.decode(bytes, hash), throwsFormatException);
  });
  test('checkpoint không được dùng cho gói/session khác', () {
    final data = packageBytes();
    final fixture = MobileE2ePackage.decode(
      data,
      sha256.convert(data).toString(),
    );
    final state = MobileE2eCheckpoint(fixture, 'installation');
    expect(
      MobileE2eCheckpoint.restore(
        fixture,
        'installation',
        state.toJson(),
      ).sessionId,
      '2026-10-23_14-30-00-123456_mobile_run_001',
    );
    expect(
      () => MobileE2eCheckpoint.restore(fixture, 'other-phone', state.toJson()),
      throwsStateError,
    );
    final changed = state.toJson()..['packageSha256'] = 'b' * 64;
    expect(
      () => MobileE2eCheckpoint.restore(fixture, 'installation', changed),
      throwsStateError,
    );
  });
  test('resume dùng lại báo cáo đã tạo; phát hiện trùng thay vì gửi thêm', () {
    final record = RescueRecord(
      id: 'post-test',
      createdAt: DateTime(2026),
      lat: null,
      lng: null,
      description: 'Benchmark 2026-10-23_14-30-00-123456_mobile_run_001 online',
      sendMode: 'queuedOffline',
    );
    expect(findMobileE2eRecord([record], record.description)?.id, record.id);
    expect(
      () => findMobileE2eRecord([
        record,
        record.copyWith(id: 'post-other'),
      ], record.description),
      throwsStateError,
    );
  });
}
