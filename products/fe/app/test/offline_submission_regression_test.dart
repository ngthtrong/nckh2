import 'dart:async';
import 'dart:io';

import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/domain/entities/send_mode.dart';
import 'package:app/domain/entities/sms_delivery.dart';
import 'package:app/domain/repositories/inference_repository.dart';
import 'package:app/domain/repositories/network_repository.dart';
import 'package:app/domain/repositories/rescue_repository.dart';
import 'package:app/domain/services/adaptive_send_policy.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:flutter_test/flutter_test.dart';

class _Records extends Fake implements RescueRepository {
  final saved = <String, RescueRecord>{};
  final sending = Completer<void>();
  final response = Completer<void>();
  final syncing = Completer<void>();
  final syncResponse = Completer<void>();

  @override
  List<RescueRecord> getAllRecords() => saved.values.toList();
  @override
  RescueRecord? getRecord(String id) => saved[id];
  @override
  Future<void> saveRecord(RescueRecord record, {bool preparing = false}) async {
    saved[record.id] = record;
  }

  @override
  Future<void> queueRecord(RescueRecord record) async =>
      saved[record.id] = record;
  @override
  Future<RescueRecord> sendRecord(RescueRecord record) async {
    if (!sending.isCompleted) sending.complete();
    await response.future;
    return saved[record.id]!;
  }

  @override
  Future<SmsResult> sendSmsFallback(RescueRecord record) async =>
      const SmsResult(SmsStatus.unknown, 'TEST_NO_MODEM');
  @override
  DateTime? get nextRetryAt => null;
  @override
  Future<void> syncPendingRecords({bool immediate = true}) async {
    syncing.complete();
    await syncResponse.future;
  }

  @override
  Future<List<RescueRecord>> refreshStatuses() async => [];
}

class _Inference extends Fake implements InferenceRepository {}

class _Network extends Fake implements NetworkRepository {
  final bool probeFails;
  _Network({this.probeFails = false});
  @override
  Future<String> getCurrentNetworkType() async => 'WiFi';
  @override
  Future<int?> probeThroughputKbps() async {
    if (probeFails) throw const SocketException('Link lost during probe');
    return null;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _Records records;
  late AppController controller;

  setUp(() {
    records = _Records();
    controller = AppController(
      rescueRepository: records,
      inferenceRepository: _Inference(),
      networkRepository: _Network(),
    );
  });

  Future<RescueRecord?> submitPost() => controller.submitPost(
    trappedCount: 2,
    injuredCount: 0,
    vulnerableGroups: const [],
    cannotMove: false,
    severeSigns: const [],
    description: 'Nước đang dâng, cần hỗ trợ',
    imagePath: null,
    aiTags: const [],
  );

  for (final isSos in [true, false]) {
    test(
      '${isSos ? 'SOS' : 'post'} survives disposal during a lost ACK',
      () async {
        final result = isSos ? controller.sendSos() : submitPost();
        await records.sending.future;
        expect(records.saved, hasLength(1));
        controller.dispose();
        records.response.complete();
        final queued = await result;
        expect(queued, isNotNull);
        expect(queued!.metadataSynced, isFalse);
        expect(records.getRecord(queued.id), isNotNull);
        expect(queued.smsStatus, SmsStatus.unknown);
      },
    );

    test('${isSos ? 'SOS' : 'post'} does not start after disposal', () async {
      controller.dispose();
      expect(await (isSos ? controller.sendSos() : submitPost()), isNull);
      expect(records.saved, isEmpty);
    });
  }

  test('sync finishing after disposal leaves the queue intact', () async {
    final result = controller.syncPending();
    await records.syncing.future;
    controller.dispose();
    records.syncResponse.complete();
    await result;
    expect(records.saved, isEmpty);
  });

  test(
    'probe failure selects fallback rather than failing submission',
    () async {
      try {
        final decision = await AdaptiveSendPolicy(
          _Network(probeFails: true),
        ).decide(hasImage: true, confidence: 0.8);
        expect(decision.mode, SendMode.smsFallback);
        expect(decision.throughputKbps, isNull);
      } finally {
        controller.dispose();
      }
    },
  );
}
