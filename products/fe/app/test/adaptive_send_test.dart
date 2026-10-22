import 'package:app/data/datasources/sender_remote_datasource.dart';
import 'package:app/domain/entities/ai_tag.dart';
import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/domain/entities/rescue_status.dart';
import 'package:app/domain/entities/send_mode.dart';
import 'package:app/domain/entities/sms_delivery.dart';
import 'package:app/domain/repositories/network_repository.dart';
import 'package:app/domain/repositories/rescue_repository.dart';
import 'package:app/domain/services/adaptive_send_policy.dart';
import 'package:app/domain/usecases/deliver_record.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeNetwork implements NetworkRepository {
  _FakeNetwork(this.type, this.kbps);
  final String type;
  final int? kbps;
  int probes = 0;

  @override
  Stream<List<ConnectivityResult>> get networkChanges => const Stream.empty();
  @override
  Future<String> getCurrentNetworkType() async => type;
  @override
  Future<int?> probeThroughputKbps() async {
    probes++;
    return kbps;
  }
}

class _FakeRepo implements RescueRepository {
  _FakeRepo({
    required this.sendOk,
    required this.smsOk,
    this.metadataAck = false,
    this.rejection,
    this.smsStatus,
    this.ackOnQueue = false,
    this.ackOnSms = false,
  });
  final bool sendOk;
  final bool smsOk;
  final bool metadataAck;
  final String? rejection;
  final SmsStatus? smsStatus;
  final bool ackOnQueue;
  final bool ackOnSms;
  bool acknowledged = false;
  final saved = <RescueRecord>[];
  final sent = <RescueRecord>[];
  int smsCalls = 0;
  int queued = 0;

  @override
  List<RescueRecord> getAllRecords() =>
      {for (final r in saved) r.id: r}.values.toList();
  @override
  Future<void> queueRecord(RescueRecord record) async {
    expect(saved.last.id, record.id);
    queued++;
    if (ackOnQueue) {
      acknowledged = true;
      await saveRecord(record);
    }
  }

  @override
  Future<void> saveRecord(
    RescueRecord record, {
    bool preparing = false,
  }) async => saved.add(
    acknowledged ? record.copyWith(metadataSynced: true, synced: true) : record,
  );
  @override
  RescueRecord? getRecord(String id) =>
      getAllRecords().where((r) => r.id == id).firstOrNull;
  @override
  Future<RescueRecord> sendRecord(RescueRecord record) async {
    sent.add(record);
    return record.copyWith(
      synced: sendOk,
      metadataSynced: sendOk || metadataAck,
      syncError: rejection,
    );
  }

  @override
  Future<SmsResult> sendSmsFallback(RescueRecord record) async {
    expect(saved.last.smsStatus, SmsStatus.sending);
    expect(queued, greaterThan(0));
    smsCalls++;
    if (ackOnSms) acknowledged = true;
    return SmsResult(smsStatus ?? (smsOk ? SmsStatus.sent : SmsStatus.failed));
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

RescueRecord _record({double? lat = 16.05, List<AiTag> tags = const []}) =>
    RescueRecord(
      id: 'post-1',
      createdAt: DateTime.utc(2026, 9, 27),
      lat: lat,
      lng: lat == null ? null : 108.2,
      description: 'Nước dâng',
      trappedCount: 3,
      aiTags: tags,
      sendMode: 'textOnly',
    );

void main() {
  group('AdaptiveSendPolicy', () {
    Future<SendDecision> decide(
      String type,
      int? kbps, {
      bool image = true,
      double conf = 0,
    }) => AdaptiveSendPolicy(
      _FakeNetwork(type, kbps),
    ).decide(hasImage: image, confidence: conf);

    test('không có kết nối → SMS, không đo', () async {
      final network = _FakeNetwork('none', 5000);
      final d = await AdaptiveSendPolicy(
        network,
      ).decide(hasImage: true, confidence: 0);
      expect(d.mode, SendMode.smsFallback);
      expect(network.probes, 0);
    });
    test('không tới được /probe → SMS', () async {
      expect((await decide('WiFi', null)).mode, SendMode.smsFallback);
    });
    test('không có ảnh → text, không đo', () async {
      final d = await decide('4G/5G', 5000, image: false);
      expect(d.mode, SendMode.textOnly);
      expect(d.throughputKbps, isNull);
    });
    test('mạng mạnh, AI chưa chắc → ảnh gốc', () async {
      final d = await decide('WiFi', 5000, conf: 0.5);
      expect(d.mode, SendMode.fullImage);
      expect(d.throughputKbps, 5000);
    });
    test('mạng mạnh, AI chắc chắn → chỉ text', () async {
      expect((await decide('WiFi', 5000, conf: 0.95)).mode, SendMode.textOnly);
    });
    test('mạng trung bình → ảnh nén', () async {
      expect((await decide('4G/5G', 300)).mode, SendMode.compressedImage);
    });
    test('mạng rất yếu → chỉ text', () async {
      expect((await decide('4G/5G', 20)).mode, SendMode.textOnly);
    });
  });

  group('deliverRecord', () {
    test('có mạng: gửi theo chế độ đã chọn, không SMS', () async {
      final repo = _FakeRepo(sendOk: true, smsOk: true);
      final r = await deliverRecord(repo, _record(), SendMode.compressedImage);
      expect(repo.smsCalls, 0);
      expect(repo.sent.single.sendMode, 'compressedImage');
      expect(r.synced, isTrue);
    });
    test('mất data: SMS đi được → smsFallback, vẫn xếp hàng', () async {
      final repo = _FakeRepo(sendOk: false, smsOk: true);
      final r = await deliverRecord(repo, _record(), SendMode.smsFallback);
      expect(repo.smsCalls, 1);
      expect(r.sendMode, 'smsFallback');
      expect(r.synced, isFalse);
      expect(repo.sent, isEmpty);
    });
    test('mất data, SMS không gửi được → queuedOffline', () async {
      final repo = _FakeRepo(sendOk: false, smsOk: false);
      final r = await deliverRecord(repo, _record(), SendMode.smsFallback);
      expect(r.sendMode, 'queuedOffline');
      expect(r.smsStatus, SmsStatus.failed);
    });
    test(
      'WiFi without reachable server falls back once after durable queue',
      () async {
        final repo = _FakeRepo(sendOk: false, smsOk: true);
        final r = await deliverRecord(repo, _record(), SendMode.textOnly);
        expect(repo.sent, hasLength(1));
        expect(repo.smsCalls, 1);
        expect(r.smsStatus, SmsStatus.sent);
        expect(r.metadataSynced, isFalse);
      },
    );
    test('metadata ACK or permanent rejection never triggers SMS', () async {
      for (final repo in [
        _FakeRepo(sendOk: false, smsOk: true, metadataAck: true),
        _FakeRepo(sendOk: false, smsOk: true, rejection: 'INVALID_PAYLOAD'),
      ]) {
        await deliverRecord(repo, _record(), SendMode.textOnly);
        expect(repo.smsCalls, 0);
      }
    });
    test(
      'lost SMS callback remains unknown and does not resend on retry',
      () async {
        final repo = _FakeRepo(
          sendOk: false,
          smsOk: true,
          smsStatus: SmsStatus.unknown,
        );
        final r = await deliverRecord(repo, _record(), SendMode.smsFallback);
        expect(r.smsStatus, SmsStatus.unknown);
        expect(r.sendMode, 'queuedOffline');
        await deliverRecord(repo, r, SendMode.smsFallback);
        expect(repo.smsCalls, 1);
      },
    );
  });

  test('advancedStatus chỉ cho đi tiến', () {
    expect(advancedStatus('processing', 'dispatched'), 'dispatched');
    expect(advancedStatus('dispatched', 'resolved'), 'resolved');
    expect(advancedStatus('dispatched', 'processing'), isNull);
    expect(advancedStatus('resolved', 'resolved'), isNull);
    expect(advancedStatus('processing', null), isNull);
    expect(advancedStatus('processing', 'received'), isNull);
  });

  test('cancelled là trạng thái kết thúc, không đi tiếp', () {
    expect(advancedStatus('processing', 'cancelled'), 'cancelled');
    expect(advancedStatus('dispatched', 'cancelled'), 'cancelled');
    expect(advancedStatus('resolved', 'cancelled'), isNull);
    expect(advancedStatus('cancelled', 'resolved'), isNull);
    expect(advancedStatus('cancelled', 'cancelled'), isNull);
    expect(isFinalStatus('cancelled'), isTrue);
    expect(isFinalStatus('dispatched'), isFalse);
  });

  test('SMS chứa id, vị trí và số người; thiếu GPS ghi unknown', () {
    expect(
      smsBody(_record()),
      'SOS|id:post-1|pos:16.05000,108.20000|trapped:3|injured:0|note:Nước dâng',
    );
    expect(smsBody(_record(lat: null)), contains('|pos:unknown|'));
  });

  test('maxAiConfidence lấy nhãn tin cậy nhất', () {
    final r = _record(
      tags: const [
        AiTag(label: 'low', confidence: 0.3),
        AiTag(label: 'high', confidence: 0.8),
      ],
    );
    expect(r.maxAiConfidence, 0.8);
    expect(_record().maxAiConfidence, 0);
  });
  test('severe-only SMS keeps mobility and canonical signs before note', () {
    final text = smsBody(
      _record().copyWith(
        cannotMove: true,
        severeSigns: ['seizure', 'heavy_bleeding'],
        description: 'x|trapped:999',
      ),
    );
    expect(
      text,
      contains('|immobile:1|severe:active_convulsions,heavy_bleeding|note:'),
    );
    expect(text, endsWith('x|trapped:999'));
  });
  test('SMS retry is explicit, delayed, and keeps its report ID', () async {
    final repo = _FakeRepo(sendOk: false, smsOk: true);
    final firstAttempt = DateTime.utc(2026, 10, 22);
    final failed = _record().copyWith(
      smsStatus: SmsStatus.failed,
      smsAttemptedAt: firstAttempt,
    );
    await deliverRecord(
      repo,
      failed,
      SendMode.smsFallback,
      retrySms: true,
      now: () => firstAttempt.add(const Duration(seconds: 29)),
    );
    expect(repo.smsCalls, 0);
    final resent = await deliverRecord(
      repo,
      failed,
      SendMode.smsFallback,
      retrySms: true,
      now: () => firstAttempt.add(const Duration(seconds: 30)),
    );
    expect(repo.smsCalls, 1);
    expect(resent.id, failed.id);
    expect(resent.smsStatus, SmsStatus.sent);
    final unknown = failed.copyWith(smsStatus: SmsStatus.unknown);
    await deliverRecord(
      repo,
      unknown,
      SendMode.smsFallback,
      retrySms: true,
      now: () => firstAttempt.add(const Duration(minutes: 1)),
    );
    expect(repo.smsCalls, 1);
  });
  test('ACK while queueing prevents an unnecessary SMS', () async {
    final repo = _FakeRepo(sendOk: false, smsOk: true, ackOnQueue: true);
    final result = await deliverRecord(repo, _record(), SendMode.smsFallback);
    expect(repo.smsCalls, 0);
    expect(result.synced, isTrue);
  });
  test('ACK during native SMS wait is reflected in returned report', () async {
    final repo = _FakeRepo(sendOk: false, smsOk: true, ackOnSms: true);
    final result = await deliverRecord(repo, _record(), SendMode.smsFallback);
    expect(repo.smsCalls, 1);
    expect(result.metadataSynced, isTrue);
    expect(result.synced, isTrue);
  });
  test('legacy boolean callback never confirms sent', () {
    expect(SmsResult.fromNative(true).status, SmsStatus.unknown);
    expect(SmsResult.fromNative({'status': 'sent'}).status, SmsStatus.sent);
    expect(
      SmsResult.fromNative({'status': 'unknown'}).status,
      SmsStatus.unknown,
    );
  });
}
