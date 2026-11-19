import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/domain/entities/send_mode.dart';
import 'package:app/domain/entities/sms_delivery.dart';
import 'package:app/domain/repositories/rescue_repository.dart';
import 'package:app/domain/usecases/send_sos_usecase.dart';
import 'package:flutter_test/flutter_test.dart';

class _Repository implements RescueRepository {
  final records = <String, RescueRecord>{};
  final queued = <String>{};
  int smsCalls = 0;
  int sends = 0;

  @override
  List<RescueRecord> getAllRecords() => records.values.toList();
  @override
  Future<void> saveRecord(
    RescueRecord record, {
    bool preparing = false,
  }) async => records[record.id] = record;
  @override
  RescueRecord? getRecord(String id) => records[id];
  @override
  Future<void> queueRecord(RescueRecord record) async => queued.add(record.id);
  @override
  Future<SmsResult> sendSmsFallback(RescueRecord record) async {
    expect(records[record.id]?.smsStatus, SmsStatus.sending);
    expect(queued, contains(record.id));
    smsCalls++;
    return const SmsResult(SmsStatus.sent);
  }

  @override
  Future<RescueRecord> sendRecord(RescueRecord record) async {
    sends++;
    final sent = record.copyWith(metadataSynced: true, synced: true);
    await saveRecord(sent);
    return sent;
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  test('interrupted SOS before SMS resumes once with the same ID', () async {
    final repo = _Repository();
    final clock = DateTime.utc(2026, 10, 22);
    final draft = RescueRecord(
      id: 'sos-interrupted',
      createdAt: clock,
      lat: null,
      lng: null,
      sendMode: 'queuedOffline',
    );
    await repo.saveRecord(draft);
    final resumed = await SendSosUseCase(
      repo,
      now: () => clock.add(const Duration(seconds: 1)),
    )(lat: null, lng: null, sendMode: SendMode.smsFallback);
    expect(resumed.id, draft.id);
    expect(repo.smsCalls, 1);
    expect(repo.records, hasLength(1));
  });
  test(
    'SOS is durable before GPS/discovery and repeated taps reuse after restart',
    () async {
      final repo = _Repository();
      var clock = DateTime.utc(2026, 10, 22);
      var locationReads = 0;
      Future<RescueRecord> send(SendSosUseCase useCase) => useCase(
        lat: null,
        lng: null,
        sendMode: SendMode.smsFallback,
        contactPhone: '0900000000',
        locate: () async {
          expect(repo.records, isNotEmpty);
          expect(repo.records.values.last.lat, isNull);
          locationReads++;
          return (lat: 10.0, lng: 106.0, accuracyMeters: 25.0);
        },
        chooseMode: () async {
          expect(repo.records.values.last.lat, 10.0);
          return SendMode.smsFallback;
        },
      );
      final first = await send(SendSosUseCase(repo, now: () => clock));
      expect(first.contactPhone, '0900000000');
      expect(first.locationAccuracyMeters, 25);
      clock = clock.add(const Duration(seconds: 2));
      for (var i = 0; i < 5; i++) {
        final again = await send(SendSosUseCase(repo, now: () => clock));
        expect(again.id, first.id);
      }
      expect(repo.records, hasLength(1));
      expect(repo.smsCalls, 1);
      expect(locationReads, 1);
      clock = clock.add(const Duration(seconds: 30));
      final next = await send(SendSosUseCase(repo, now: () => clock));
      expect(next.id, isNot(first.id));
      expect(repo.smsCalls, 2);
    },
  );

  test(
    'each new SOS captures a new location; unavailable GPS stays null',
    () async {
      final repo = _Repository();
      var clock = DateTime.utc(2026, 10, 22);
      final useCase = SendSosUseCase(repo, now: () => clock);
      for (final lat in <double?>[10, 11, null]) {
        final result = await useCase(
          lat: null,
          lng: null,
          sendMode: SendMode.textOnly,
          locate: () async =>
              (lat: lat, lng: lat == null ? null : 106.0, accuracyMeters: null),
        );
        expect(result.lat, lat);
        expect(result.lng, lat == null ? null : 106.0);
        clock = clock.add(const Duration(seconds: 31));
      }
      expect(repo.smsCalls, 0);
      expect(repo.sends, 3);
    },
  );
}
