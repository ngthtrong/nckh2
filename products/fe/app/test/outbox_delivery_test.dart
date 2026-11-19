import 'dart:async';
import 'dart:io';
import 'dart:typed_data';
import 'package:dio/dio.dart';

import 'package:app/config.dart';
import 'package:app/data/datasources/outbox_local_datasource.dart';
import 'package:app/data/datasources/record_local_datasource.dart';
import 'package:app/data/datasources/sender_remote_datasource.dart';
import 'package:app/data/datasources/server_locator.dart';
import 'package:app/data/datasources/sync_remote_datasource.dart';
import 'package:app/data/models/sync_message_model.dart';
import 'package:app/data/models/rescue_record_payload.dart';
import 'package:app/data/repositories/rescue_repository_impl.dart';
import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/domain/entities/sms_delivery.dart';
import 'package:app/domain/entities/send_mode.dart';
import 'package:app/domain/usecases/deliver_record.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_ce_flutter/hive_flutter.dart';

/// Server giả: trả kết quả theo hàng đợi [replies] (mỗi lần gửi lấy một mã), ghi
/// lại các batch và phát hiện hai request chạy chồng nhau.
class _FakeSync extends SyncRemoteDataSource {
  _FakeSync(this.replies, {this.afterReply});
  final List<String> replies;
  final void Function()? afterReply;
  var offline = false;
  var sendAttempts = 0;
  final batches = <List<SyncMessageModel>>[];
  final statusQueries = <List<String>>[];
  var inFlight = 0;
  var overlapped = false;

  @override
  Future<List<Map<String, dynamic>>> sendBatch(
    List<SyncMessageModel> messages,
  ) async {
    sendAttempts++;
    if (offline) throw const SocketException('mất mạng');
    if (++inFlight > 1) overlapped = true;
    batches.add(messages);
    await Future<void>.delayed(const Duration(milliseconds: 20));
    inFlight--;
    afterReply?.call();
    return [
      for (final m in messages)
        {
          'message_id': m.messageId,
          'status': replies.isEmpty || replies.first == 'accepted'
              ? 'accepted'
              : 'rejected',
          'retryable': false,
          'code': replies.isEmpty ? null : replies.removeAt(0),
        },
    ];
  }

  @override
  Future<Map<String, String>> fetchStatuses(List<String> ids) async {
    statusQueries.add(ids);
    return {for (final id in ids) id: 'dispatched'};
  }
}

class _CountingRecords extends RecordLocalDataSource {
  var scans = 0;

  @override
  List<RescueRecord> getAllRecords() {
    scans++;
    return super.getAllRecords();
  }
}

class _AheadSync extends _FakeSync {
  _AheadSync() : super([]);

  @override
  Future<List<Map<String, dynamic>>> sendBatch(
    List<SyncMessageModel> messages,
  ) async {
    if (messages.any((m) => m.sequenceNumber <= 1000)) {
      batches.add(List.of(messages));
      return [
        for (final message in messages)
          {
            'message_id': message.messageId,
            'status': 'rejected',
            'code': 'SEQUENCE_REUSED',
            'retryable': false,
            'result': {'next_sequence_number': 1001},
          },
      ];
    }
    return super.sendBatch(messages);
  }
}

class _HttpSync extends _FakeSync {
  _HttpSync({this.status, this.maxBatchSize = 50, this.oversizedId})
    : super([]);
  final int? status;
  final int maxBatchSize;
  final String? oversizedId;
  final requests = <List<SyncMessageModel>>[];

  @override
  Future<List<Map<String, dynamic>>> sendBatch(
    List<SyncMessageModel> messages,
  ) {
    requests.add(List.of(messages));
    final code =
        status ??
        (messages.length > maxBatchSize ||
                messages.any((m) => m.payload['id'] == oversizedId)
            ? 413
            : null);
    if (code != null) {
      final options = RequestOptions(path: '/sync/messages');
      throw DioException(
        requestOptions: options,
        response: Response<Object?>(requestOptions: options, statusCode: code),
        type: DioExceptionType.badResponse,
      );
    }
    return super.sendBatch(messages);
  }
}

class _FakeSender extends SenderRemoteDataSource {
  _FakeSender({this.status = 201});
  final int status;
  var uploads = 0;

  @override
  Future<UploadResult> upload(
    RescueRecord rec,
    Uint8List? image, {
    required String clientId,
  }) async {
    uploads++;
    return (
      ok: status == 201,
      bytesSent: image?.length ?? 0,
      durationMs: 1,
      status: status,
      permanent: isPermanentUploadFailure(status, null),
    );
  }
}

class _HoldingSender extends _FakeSender {
  final started = Completer<void>();
  final release = Completer<void>();
  final imageIds = <String>[];
  var smsCalls = 0;

  @override
  Future<UploadResult> upload(
    RescueRecord rec,
    Uint8List? image, {
    required String clientId,
  }) async {
    imageIds.add(rec.id);
    if (rec.id == 'old-image') {
      if (!started.isCompleted) started.complete();
      await release.future;
    }
    return super.upload(rec, image, clientId: clientId);
  }

  @override
  Future<SmsResult> sendSms(RescueRecord record) async {
    smsCalls++;
    return const SmsResult(SmsStatus.sent);
  }
}

class _HoldingStatusSync extends _FakeSync {
  _HoldingStatusSync() : super([]);
  final started = Completer<void>();
  final release = Completer<void>();

  @override
  Future<Map<String, String>> fetchStatuses(List<String> ids) async {
    started.complete();
    await release.future;
    return super.fetchStatuses(ids);
  }
}

class _SlowFirstImageSender extends _FakeSender {
  final imageIds = <String>[];

  @override
  Future<UploadResult> upload(
    RescueRecord rec,
    Uint8List? image, {
    required String clientId,
  }) async {
    imageIds.add(rec.id);
    if (imageIds.length == 1) {
      await Future<void>.delayed(const Duration(milliseconds: 20100));
    }
    return (
      ok: rec.id != 'large-image',
      bytesSent: image?.length ?? 0,
      durationMs: 1,
      status: rec.id == 'large-image' ? 503 : 201,
      permanent: false,
    );
  }
}

RescueRecord _record(String id, {String? imagePath}) => RescueRecord(
  id: id,
  createdAt: DateTime.utc(2026, 9, 29),
  lat: 16.05,
  lng: 108.2,
  imagePath: imagePath,
  sendMode: 'textOnly',
);

void main() {
  late Directory dir;
  late _CountingRecords records;
  late OutboxLocalDataSource outbox;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('outbox_test');
    records = _CountingRecords();
    outbox = OutboxLocalDataSource();
    await records.init(hivePath: dir.path);
    await outbox.init(hivePath: dir.path);
  });

  tearDown(() async {
    setServerBaseUrl(kConfiguredServerUrl);
    await Hive.deleteFromDisk();
    await dir.delete(recursive: true);
  });

  RescueRepositoryImpl repo(_FakeSync sync) => RescueRepositoryImpl(
    localDataSource: records,
    senderDataSource: SenderRemoteDataSource(),
    outboxDataSource: outbox,
    syncDataSource: sync,
  );

  for (final mode in [SendMode.textOnly, SendMode.smsFallback]) {
    test(
      'new SOS $mode finishes while an older image upload is blocked',
      () async {
        final sender = _HoldingSender();
        final sync = _FakeSync([]);
        final r = RescueRepositoryImpl(
          localDataSource: records,
          senderDataSource: sender,
          outboxDataSource: outbox,
          syncDataSource: sync,
        );
        final image = File('${dir.path}/old.jpg');
        await image.writeAsBytes([0xff, 0xd8, 0xff]);
        await records.saveRecord(
          _record(
            'old-image',
            imagePath: image.path,
          ).copyWith(metadataSynced: true, sendMode: 'fullImage'),
        );
        final syncing = r.syncPendingRecords();
        await sender.started.future.timeout(const Duration(seconds: 2));
        try {
          final sent = await deliverRecord(
            r,
            _record('sos-new'),
            mode,
          ).timeout(const Duration(seconds: 2));
          expect(sender.release.isCompleted, isFalse);
          if (mode == SendMode.smsFallback) {
            expect(sent.smsStatus, SmsStatus.sent);
            expect(sender.smsCalls, 1);
            expect(outbox.messageForRecord(sent.id), isNotNull);
          } else {
            expect(sent.metadataSynced, isTrue);
            expect(sent.synced, isTrue);
          }
        } finally {
          sender.release.complete();
          await syncing;
        }
        expect(records.getRecord('old-image')!.synced, isTrue);
      },
    );
  }

  test(
    'slow status response does not block a new SOS or overwrite its ACK',
    () async {
      final sync = _HoldingStatusSync();
      final r = repo(sync);
      await records.saveRecord(
        _record('old-report').copyWith(metadataSynced: true, synced: true),
      );
      final polling = r.refreshStatuses();
      await sync.started.future.timeout(const Duration(seconds: 2));
      try {
        final sent = await deliverRecord(
          r,
          _record('sos-new'),
          SendMode.textOnly,
        ).timeout(const Duration(seconds: 2));
        expect(sent.synced, isTrue);
      } finally {
        sync.release.complete();
        await polling;
      }
      expect(records.getRecord('sos-new')!.synced, isTrue);
      expect(records.getRecord('old-report')!.status, 'dispatched');
    },
  );

  test('concurrent sends and sync share the same attachment upload', () async {
    final sender = _HoldingSender();
    final r = RescueRepositoryImpl(
      localDataSource: records,
      senderDataSource: sender,
      outboxDataSource: outbox,
      syncDataSource: _FakeSync([]),
    );
    final image = File('${dir.path}/single-upload.jpg');
    await image.writeAsBytes([0xff, 0xd8, 0xff]);
    final record = _record(
      'old-image',
      imagePath: image.path,
    ).copyWith(sendMode: 'fullImage');
    await records.saveRecord(record);
    final first = r.sendRecord(record);
    await sender.started.future.timeout(const Duration(seconds: 2));
    final second = r.sendRecord(record);
    final syncing = r.syncPendingRecords();
    await Future<void>.delayed(const Duration(milliseconds: 50));
    sender.release.complete();
    await Future.wait([first, second, syncing]);
    expect(sender.imageIds, ['old-image']);
    expect(records.getRecord(record.id)!.synced, isTrue);
  });

  test(
    'slow failed image rotates behind older images after repository restart',
    () async {
      final sender = _SlowFirstImageSender();
      RescueRepositoryImpl createRepo() => RescueRepositoryImpl(
        localDataSource: records,
        senderDataSource: sender,
        outboxDataSource: outbox,
        syncDataSource: _FakeSync([]),
      );
      final image = File('${dir.path}/rotation.jpg');
      await image.writeAsBytes([0xff, 0xd8, 0xff]);
      final old = _record(
        'small-image',
        imagePath: image.path,
      ).copyWith(metadataSynced: true, sendMode: 'fullImage');
      final recent = old.copyWith(
        id: 'large-image',
        createdAt: old.createdAt.add(const Duration(days: 1)),
      );
      await records.saveRecord(old);
      await records.saveRecord(recent);
      await createRepo().syncPendingRecords();
      expect(sender.imageIds, ['large-image']);
      expect(outbox.lastAttachmentRecordId, 'large-image');
      await Hive.close();
      await records.init(hivePath: dir.path);
      await outbox.init(hivePath: dir.path);
      await createRepo().syncPendingRecords();
      expect(sender.imageIds, ['large-image', 'small-image', 'large-image']);
      expect(records.getRecord('small-image')!.synced, isTrue);
      expect(records.getRecord('large-image')!.synced, isFalse);
    },
  );

  test('contact phone survives restart, updates and offline queue', () async {
    final original = _record('contact').copyWith(contactPhone: '0900000000');
    await records.saveRecord(original);
    await Hive.close();
    await records.init(hivePath: dir.path);
    await outbox.init(hivePath: dir.path);
    final restored = records.getRecord(original.id)!;
    expect(restored.contactPhone, '0900000000');
    expect(restored.copyWith(synced: true).contactPhone, '0900000000');
    final r = repo(_FakeSync([]));
    await r.queueRecord(restored);
    expect(
      outbox.messageForRecord(original.id)!.payload['contactPhone'],
      '0900000000',
    );
    final legacy = _record('legacy-contact');
    await records.saveRecord(legacy);
    expect(records.getRecord(legacy.id)!.contactPhone, isNull);
    expect(rescueRecordPayload(legacy), isNot(contains('contactPhone')));
  });

  test('queueRecord persists metadata without probing or sending', () async {
    var probes = 0;
    final locator = ServerLocator(
      configuredUrl: 'https://rescue.example',
      candidates: (_) async => [],
      probe: (_) async {
        probes++;
        return null;
      },
    );
    await locator.init(outbox);
    probes = 0;
    final sync = _FakeSync([]);
    final r = RescueRepositoryImpl(
      localDataSource: records,
      senderDataSource: SenderRemoteDataSource(),
      outboxDataSource: outbox,
      syncDataSource: sync,
      serverLocator: locator,
    );
    final record = _record('offline-sos');
    await r.saveRecord(record);
    await r.queueRecord(record);
    expect(outbox.messageForRecord(record.id), isNotNull);
    expect(probes, 0);
    expect(sync.sendAttempts, 0);
  });

  test(
    'preparing GPS draft is durable but sync waits for the final snapshot',
    () async {
      final sync = _FakeSync([]);
      final r = repo(sync);
      final draft = RescueRecord(
        id: 'preparing-sos',
        createdAt: DateTime.utc(2026, 10, 22),
        lat: null,
        lng: null,
        sendMode: 'textOnly',
      );
      await r.saveRecord(draft, preparing: true);
      expect(records.getRecord(draft.id), isNotNull);
      await r.syncPendingRecords();
      await r.refreshStatuses();
      expect(outbox.messageForRecord(draft.id), isNull);
      expect(sync.sendAttempts, 0);
      expect(sync.statusQueries, isEmpty);
      final finalized = draft.copyWith(lat: 16.05, lng: 108.2);
      await r.saveRecord(finalized);
      // Saving GPS alone does not release the draft before the caller is ready.
      await r.syncPendingRecords();
      expect(sync.sendAttempts, 0);
      await r.queueRecord(finalized);
      await r.syncPendingRecords();
      final payload = sync.batches.single.single.payload;
      expect(payload['lat'], finalized.lat);
      expect(payload['lng'], finalized.lng);
      expect(records.getRecord(draft.id)!.metadataSynced, isTrue);
    },
  );

  test(
    'a new repository recovers a persisted preparing draft after process loss',
    () async {
      final sync = _FakeSync([]);
      final r = repo(sync);
      final draft = RescueRecord(
        id: 'interrupted-gps',
        createdAt: DateTime.utc(2026, 10, 22),
        lat: null,
        lng: null,
        sendMode: 'textOnly',
      );
      await r.saveRecord(draft, preparing: true);
      await r.syncPendingRecords();
      expect(sync.sendAttempts, 0);
      await Hive.close();
      await records.init(hivePath: dir.path);
      await outbox.init(hivePath: dir.path);
      final recovered = repo(sync);
      await recovered.syncPendingRecords();
      expect(sync.batches.single.single.payload['id'], draft.id);
      expect(sync.batches.single.single.payload['lat'], isNull);
      expect(records.getRecord(draft.id)!.synced, isTrue);
    },
  );

  test('new SOS is sent ahead of more than 50 queued reports', () async {
    final sync = _FakeSync([]);
    final r = repo(sync);
    for (var i = 0; i < 60; i++) {
      final old = _record('old-$i');
      await records.saveRecord(old);
      await r.queueRecord(old);
    }
    final sos = _record('new-sos');
    await r.saveRecord(sos);
    final sent = await r.sendRecord(sos);
    expect(sync.batches, hasLength(1));
    expect(sync.batches.single.first.payload['id'], sos.id);
    expect(sent.synced, isTrue);
    expect(outbox.messageForRecord(sos.id), isNull);
    expect(outbox.readyMessages(), hasLength(11));
  });

  test(
    'one sync drains multiple batches and reconciles the schedule once',
    () async {
      final sync = _FakeSync([]);
      final r = repo(sync);
      for (var i = 0; i < 121; i++) {
        final record = _record('bulk-$i');
        await records.saveRecord(record);
        await r.queueRecord(record);
      }
      records.scans = 0;
      await r.syncPendingRecords();
      expect(sync.batches.map((batch) => batch.length), [50, 50, 21]);
      // One scan to collect pending records and one to reconcile WorkManager.
      expect(records.scans, 2);
      expect(r.getPendingCount(), 0);
    },
  );

  test(
    'a worker stops after 20 successful batches and keeps the rest queued',
    () async {
      final sync = _FakeSync([]);
      final r = repo(sync);
      for (var i = 0; i < 1001; i++) {
        await outbox.enqueueCreate({'id': 'bounded-$i'});
      }
      await r.syncPendingRecords();
      expect(sync.batches, hasLength(20));
      expect(outbox.readyMessages(), hasLength(1));
    },
  );

  test(
    'a failed batch stops draining instead of retrying in the same loop',
    () async {
      final sync = _FakeSync([])..offline = true;
      final r = repo(sync);
      for (var i = 0; i < 121; i++) {
        await outbox.enqueueCreate({'id': 'offline-$i'});
      }
      await r.syncPendingRecords();
      expect(sync.sendAttempts, 1);
      expect(outbox.messageForRecord('offline-0')?.attemptCount, 1);
      expect(outbox.messageForRecord('offline-120')?.attemptCount, 0);
    },
  );

  test(
    'late foreground saves preserve acknowledged metadata and final status',
    () async {
      final original = _record('late-sms');
      await records.saveRecord(original);
      await records.saveRecord(
        original.copyWith(
          synced: true,
          metadataSynced: true,
          status: 'resolved',
        ),
      );
      await records.saveRecord(original.copyWith(sendMode: 'smsFallback'));
      final saved = records.getRecord(original.id)!;
      expect(saved.synced, isTrue);
      expect(saved.metadataSynced, isTrue);
      expect(saved.status, 'resolved');
      expect(saved.sendMode, 'smsFallback');
    },
  );

  test(
    'SMS state survives disk reopen and stale worker records do not reset it',
    () async {
      final original = _record('sms-status');
      await records.saveRecord(original.copyWith(smsStatus: SmsStatus.sent));
      await records.saveRecord(original.copyWith(metadataSynced: true));
      await Hive.close();
      await records.init(hivePath: dir.path);
      final saved = records.getRecord(original.id)!;
      expect(saved.smsStatus, SmsStatus.sent);
      expect(saved.metadataSynced, isTrue);
    },
  );

  test('legacy SMS success flags remain unconfirmed after migration', () async {
    final original = _record('legacy-sms').copyWith(sendMode: 'smsFallback');
    await records.saveRecord(original);
    final box = Hive.box<Map>(RecordLocalDataSource.boxName);
    final raw = Map<String, dynamic>.from(box.get(original.id)!);
    raw.remove('smsStatus');
    await box.put(original.id, raw);
    expect(records.getRecord(original.id)!.smsStatus, SmsStatus.unknown);
  });

  test(
    'a stale worker save cannot change a failed SMS back to sending',
    () async {
      final sending = _record(
        'sms-failed',
      ).copyWith(smsStatus: SmsStatus.sending);
      await records.saveRecord(sending);
      await records.saveRecord(
        sending.copyWith(smsStatus: SmsStatus.failed, smsError: 'NO_SERVICE'),
      );
      await records.saveRecord(sending.copyWith(metadataSynced: true));
      final saved = records.getRecord(sending.id)!;
      expect(saved.smsStatus, SmsStatus.failed);
      expect(saved.smsError, 'NO_SERVICE');
      expect(saved.metadataSynced, isTrue);
    },
  );

  test(
    'a newer SMS retry replaces failure while late old results are ignored',
    () async {
      final firstAt = DateTime.utc(2026, 10, 22, 10);
      final failed = _record('sms-retry').copyWith(
        smsStatus: SmsStatus.failed,
        smsError: 'NO_SERVICE',
        smsAttemptedAt: firstAt,
      );
      await records.saveRecord(failed);
      final retry = failed.copyWith(
        smsStatus: SmsStatus.sending,
        clearSmsError: true,
        smsAttemptedAt: firstAt.add(const Duration(seconds: 30)),
      );
      await records.saveRecord(retry);
      expect(records.getRecord(retry.id)!.smsStatus, SmsStatus.sending);
      expect(records.getRecord(retry.id)!.smsError, isNull);
      // An old callback can arrive while the user-requested retry is in flight.
      await records.saveRecord(failed.copyWith(smsStatus: SmsStatus.sent));
      expect(records.getRecord(retry.id)!.smsStatus, SmsStatus.sending);
      await records.saveRecord(retry.copyWith(smsStatus: SmsStatus.sent));
      await records.saveRecord(failed);
      await Hive.close();
      await records.init(hivePath: dir.path);
      final saved = records.getRecord(retry.id)!;
      expect(saved.smsStatus, SmsStatus.sent);
      expect(saved.smsError, isNull);
      expect(saved.smsAttemptedAt, retry.smsAttemptedAt);
    },
  );

  test(
    'status updates keep record ordering and date edits reorder correctly',
    () async {
      final old = _record('old');
      final recent = _record(
        'recent',
      ).copyWith(createdAt: old.createdAt.add(const Duration(days: 1)));
      await records.saveRecord(old);
      await records.saveRecord(recent);
      expect(records.getAllRecords().map((record) => record.id), [
        'recent',
        'old',
      ]);
      await records.saveRecord(old.copyWith(status: 'dispatched'));
      expect(records.getRecordsPage(offset: 0, limit: 1).single.id, 'recent');
      await records.saveRecord(
        old.copyWith(createdAt: recent.createdAt.add(const Duration(days: 1))),
      );
      expect(records.getRecordsPage(offset: 0, limit: 1).single.id, 'old');
    },
  );

  test('mất IP server: giữ message chờ rồi gửi khi tìm được IP mới', () async {
    const url = 'https://rescue-new.example';
    var serverUp = false;
    final locator = ServerLocator(
      allowInsecureLan: true,
      configuredUrl: url,
      candidates: (_) async => [url],
      probe: (candidate) async =>
          serverUp && candidate == url ? 'abcdef0123456789' : null,
    );
    await locator.init(outbox);
    final sync = _FakeSync([]);
    final r = RescueRepositoryImpl(
      localDataSource: records,
      senderDataSource: SenderRemoteDataSource(),
      outboxDataSource: outbox,
      syncDataSource: sync,
      serverLocator: locator,
    );
    await r.saveRecord(_record('ip-change'));
    final pending = await r.sendRecord(_record('ip-change'));
    expect(pending.synced, isFalse);
    expect(r.getPendingCount(), 1);
    expect(sync.batches, isEmpty);

    serverUp = true;
    expect(await r.reconnectServer(), isTrue);
    await r.syncPendingRecords();
    expect(r.getPendingCount(), 0);
    expect(sync.batches, hasLength(1));
    expect(kServerBaseUrl, url);
  });

  test(
    'new send bypasses failed LAN discovery backoff; worker does not',
    () async {
      const url = 'http://192.168.1.20:8000';
      var serverUp = false;
      var scans = 0;
      final locator = ServerLocator(
        allowInsecureLan: true,
        configuredUrl: '',
        candidates: (_) async {
          scans++;
          return [url];
        },
        probe: (_) async => serverUp ? 'abcdef0123456789' : null,
      );
      await locator.init(outbox);
      expect(scans, 1);
      final sync = _FakeSync([]);
      final r = RescueRepositoryImpl(
        localDataSource: records,
        senderDataSource: SenderRemoteDataSource(),
        outboxDataSource: outbox,
        syncDataSource: sync,
        serverLocator: locator,
      );
      final record = _record('sos-lan-recovered');
      await r.saveRecord(record);
      await r.queueRecord(record);
      serverUp = true;
      await r.syncPendingRecords(immediate: false);
      expect(scans, 1);
      expect(sync.batches, isEmpty);
      final sent = await r.sendRecord(record);
      expect(scans, 2);
      expect(sent.metadataSynced, isTrue);
      expect(sent.synced, isTrue);
      expect(sync.batches, hasLength(1));
    },
  );

  test(
    'location accuracy survives local storage and reaches the outbox',
    () async {
      final record = _record(
        'accurate-location',
      ).copyWith(locationAccuracyMeters: 250);
      await records.saveRecord(record);
      await records.init(hivePath: dir.path);
      final stored = records.getRecord(record.id)!;
      expect(stored.locationAccuracyMeters, 250);
      expect(stored.copyWith(status: 'dispatched').locationAccuracyMeters, 250);
      final message = await outbox.enqueueCreate(rescueRecordPayload(stored));
      expect(message.payload['locationAccuracyMeters'], 250);
    },
  );

  test('metadata đã ACK nhưng ảnh chỉ gửi sau khi xác minh IP mới', () async {
    const oldUrl = 'https://rescue-old.example';
    const newUrl = 'https://rescue-new.example';
    var currentUrl = oldUrl;
    var dropAfterAck = true;
    final locator = ServerLocator(
      allowInsecureLan: true,
      configuredUrl: oldUrl,
      candidates: (_) async => [oldUrl, newUrl],
      probe: (url) async => url == currentUrl ? 'abcdef0123456789' : null,
    );
    await locator.init(outbox);
    final sync = _FakeSync(
      [],
      afterReply: () {
        if (dropAfterAck) {
          currentUrl = '';
          dropAfterAck = false;
        }
      },
    );
    final sender = _FakeSender();
    final r = RescueRepositoryImpl(
      localDataSource: records,
      senderDataSource: sender,
      outboxDataSource: outbox,
      syncDataSource: sync,
      serverLocator: locator,
    );
    final image = File('${dir.path}/image.jpg');
    await image.writeAsBytes([0xFF, 0xD8, 0xFF]);
    final record = _record(
      'ip-image',
      imagePath: image.path,
    ).copyWith(sendMode: 'fullImage');
    await r.saveRecord(record);
    final pending = await r.sendRecord(record);
    expect(pending.synced, isFalse);
    expect(pending.metadataSynced, isTrue);
    expect(pending.attachmentError, isNull);
    expect(sender.uploads, 0);

    currentUrl = newUrl;
    expect(await r.reconnectServer(), isTrue);
    await r.syncPendingRecords();
    expect(sender.uploads, 1);
    expect(r.getPendingCount(), 0);
  });

  test('bị từ chối vĩnh viễn: ghi syncError, không còn chờ gửi', () async {
    final sync = _FakeSync(['INVALID_PAYLOAD']);
    final r = repo(sync);
    await r.saveRecord(_record('sos-1'));
    final sent = await r.sendRecord(_record('sos-1'));
    expect((sent.synced, sent.syncError), (false, 'INVALID_PAYLOAD'));
    expect(r.getPendingCount(), 0);
    // Đồng bộ lại không gửi báo cáo đã bị từ chối.
    await r.syncPendingRecords();
    expect(sync.batches, hasLength(1));
  });

  test('SEQUENCE_REUSED: tạo message mới và gửi lại ngay', () async {
    final sync = _FakeSync(['SEQUENCE_REUSED']);
    final r = repo(sync);
    final sent = await r.sendRecord(_record('sos-2'));
    expect(sent.synced, isTrue);
    expect(sync.batches, hasLength(2));
    final first = sync.batches[0].single, second = sync.batches[1].single;
    expect(second.messageId, isNot(first.messageId));
    expect(second.sequenceNumber, greaterThan(first.sequenceNumber));
    expect(second.payloadHash, first.payloadHash);
    expect(outbox.messageForRecord('sos-2'), isNull);
  });

  test(
    'restored sender jumps past the server sequence without changing owner',
    () async {
      final sync = _AheadSync();
      final r = repo(sync);
      final clientId = outbox.clientId;
      final sent = await r.sendRecord(_record('restored-sos'));
      expect(sent.synced, isTrue);
      expect(sync.batches, hasLength(2));
      final first = sync.batches.first.single;
      final recovered = sync.batches.last.single;
      expect(first.sequenceNumber, 1);
      expect(recovered.sequenceNumber, 1001);
      expect(recovered.clientId, clientId);
      expect(recovered.messageId, isNot(first.messageId));
      expect(recovered.payloadHash, first.payloadHash);
      expect(recovered.payload, first.payload);

      await Hive.close();
      await records.init(hivePath: dir.path);
      await outbox.init(hivePath: dir.path);
      final next = await outbox.enqueueCreate(
        rescueRecordPayload(_record('next-sos')),
      );
      expect(next.sequenceNumber, 1002);
      expect(next.clientId, clientId);
    },
  );

  test(
    'sequence reconciliation survives restart without changing queued data',
    () async {
      final firstPayload = rescueRecordPayload(_record('restored-first'));
      final secondPayload = rescueRecordPayload(_record('restored-second'));
      final first = await outbox.enqueueCreate(firstPayload);
      final second = await outbox.enqueueCreate(secondPayload);
      await outbox.reconcileSequence(1001);
      await outbox.markDeadLetter(first.messageId, 'SEQUENCE_REUSED');

      await Hive.close();
      await records.init(hivePath: dir.path);
      await outbox.init(hivePath: dir.path);
      final recovered = await outbox.enqueueCreate(firstPayload);
      expect(recovered.sequenceNumber, 1001);
      expect(recovered.clientId, first.clientId);
      expect(recovered.payloadHash, first.payloadHash);
      expect(recovered.payload, first.payload);
      expect(
        outbox.messageForRecord('restored-second')!.toStorageJson(),
        second.toStorageJson(),
      );
      for (final staleHint in [0, -1, 2, 1001]) {
        await outbox.reconcileSequence(staleHint);
      }
      final next = await outbox.enqueueCreate(
        rescueRecordPayload(_record('new-report')),
      );
      expect(next.sequenceNumber, 1002);
    },
  );

  test('gửi và đồng bộ cùng lúc chạy lần lượt, không gửi trùng', () async {
    final sync = _FakeSync([]);
    final r = repo(sync);
    await r.saveRecord(_record('sos-3'));
    await Future.wait([
      r.sendRecord(_record('sos-3')),
      r.syncPendingRecords(),
      r.refreshStatuses(),
    ]);
    expect(sync.overlapped, isFalse);
    expect(sync.batches.expand((b) => b).map((m) => m.payload['id']), [
      'sos-3',
    ]);
  });

  test(
    'hỏi trạng thái cả báo cáo đã ACK metadata nhưng ảnh chưa gửi xong',
    () async {
      final sync = _FakeSync([]);
      final r = repo(sync);
      // Metadata đã ACK (outbox trống) nhưng ảnh chưa xong nên synced = false.
      await r.saveRecord(_record('post-4', imagePath: '/khong/ton/tai.jpg'));
      await r.saveRecord(
        _record('post-5').copyWith(syncError: 'INVALID_PAYLOAD'),
      );
      final changed = await r.refreshStatuses();
      expect(sync.statusQueries.single, ['post-4']);
      expect(changed.single.status, 'dispatched');
    },
  );

  test('có mạng trở lại: gửi ngay message đang chờ backoff', () async {
    final sync = _FakeSync([])..offline = true;
    final r = repo(sync);
    await r.saveRecord(_record('sos-6'));
    final queued = await r.sendRecord(_record('sos-6'));
    expect((queued.synced, r.getPendingCount()), (false, 1));
    // Hẹn gửi lại theo backoff; lần hẹn giờ chưa đến hạn thì chưa gửi.
    sync.offline = false;
    for (var i = 0; i < 12; i++) {
      await outbox.scheduleRetry(
        outbox.messageForRecord('sos-6')!.messageId,
        'x',
      );
    }
    expect(r.nextRetryAt!.isAfter(DateTime.now().toUtc()), isTrue);
    await r.syncPendingRecords(immediate: false);
    expect(sync.batches, isEmpty);
    // Sự kiện có mạng lại / Workmanager: bỏ qua backoff.
    await r.syncPendingRecords();
    expect(sync.batches, hasLength(1));
    expect(r.getPendingCount(), 0);
    expect(r.nextRetryAt, isNull);
  });

  test('dead-letter do vận chuyển được tạo lại; do nội dung thì không', () {
    expect(isRecoverableDeadLetter('SEQUENCE_REUSED'), isTrue);
    expect(isRecoverableDeadLetter('ID_REUSED_WITH_DIFFERENT_PAYLOAD'), isTrue);
    for (final code in [
      'HTTP_400',
      'HTTP_401',
      'HTTP_403',
      'HTTP_404',
      'HTTP_413',
      'HTTP_422',
      'HTTP_600',
      'HTTP_null',
      'HTTP_bad',
    ]) {
      expect(isRecoverableDeadLetter(code), isFalse, reason: code);
    }
    for (final code in [
      'HTTP_408',
      'HTTP_429',
      'HTTP_500',
      'HTTP_503',
      'HTTP_599',
    ]) {
      expect(isRecoverableDeadLetter(code), isTrue, reason: code);
    }
    expect(isRecoverableDeadLetter('INVALID_PAYLOAD'), isFalse);
    expect(isRecoverableDeadLetter('REPORT_ID_CONFLICT'), isFalse);
    expect(isRecoverableDeadLetter('REQUEST_TOO_LARGE'), isFalse);
    expect(isRecoverableDeadLetter(null), isFalse);
  });

  for (final status in [400, 401, 403, 404, 413, 422]) {
    test(
      'HTTP $status finishes permanently without SMS or new messages',
      () async {
        final sync = _HttpSync(status: status);
        final sender = _HoldingSender();
        final r = RescueRepositoryImpl(
          localDataSource: records,
          senderDataSource: sender,
          outboxDataSource: outbox,
          syncDataSource: sync,
        );
        final sent = await deliverRecord(
          r,
          _record('http-$status'),
          SendMode.textOnly,
        );
        expect(
          sent.syncError,
          status == 413 ? 'REQUEST_TOO_LARGE' : 'HTTP_$status',
        );
        expect(sent.synced, isFalse);
        expect(r.getPendingCount(), 0);
        expect(sender.smsCalls, 0);
        final message = outbox.messageForRecord(sent.id)!;
        await r.syncPendingRecords();
        await r.syncPendingRecords();
        expect(sync.requests, hasLength(1));
        expect(outbox.messageForRecord(sent.id)!.messageId, message.messageId);
        expect(records.getRecord(sent.id)!.syncError, sent.syncError);
      },
    );
  }

  for (final status in [408, 429, 500, 503]) {
    test('HTTP $status retries with the same message ID and backoff', () async {
      final sync = _HttpSync(status: status);
      final r = repo(sync);
      await r.saveRecord(_record('retry-http-$status'));
      final sent = await r.sendRecord(_record('retry-http-$status'));
      expect(sent.syncError, isNull);
      final message = outbox.messageForRecord(sent.id)!;
      expect(message.deliveryStatus, 'pending');
      expect(message.attemptCount, 1);
      await r.syncPendingRecords();
      final retried = outbox.messageForRecord(sent.id)!;
      expect(retried.messageId, message.messageId);
      expect(retried.attemptCount, 2);
      expect(sync.requests, hasLength(2));
    });
  }

  test(
    'old permanent HTTP dead-letter is surfaced instead of recreated',
    () async {
      final sync = _HttpSync();
      final r = repo(sync);
      final record = _record('old-http-error');
      await r.saveRecord(record);
      await r.queueRecord(record);
      final message = outbox.messageForRecord(record.id)!;
      await outbox.markDeadLetter(message.messageId, 'HTTP_400');
      await Hive.close();
      await records.init(hivePath: dir.path);
      await outbox.init(hivePath: dir.path);
      await r.syncPendingRecords();
      expect(records.getRecord(record.id)!.syncError, 'HTTP_400');
      expect(outbox.messageForRecord(record.id)!.messageId, message.messageId);
      expect(sync.requests, isEmpty);
      expect(r.getPendingCount(), 0);
    },
  );

  test('413 shrinks batches while preserving every message ID', () async {
    final sync = _HttpSync(maxBatchSize: 2);
    final r = repo(sync);
    final originalIds = <String, String>{};
    for (var i = 0; i < 5; i++) {
      final record = _record('split-$i');
      await r.saveRecord(record);
      await r.queueRecord(record);
      originalIds[record.id] = outbox.messageForRecord(record.id)!.messageId;
    }
    await r.syncPendingRecords();
    expect(sync.requests.map((batch) => batch.length), [5, 3, 2, 2, 1]);
    for (final message in sync.requests.expand((batch) => batch)) {
      expect(message.messageId, originalIds[message.payload['id']]);
    }
    expect(sync.batches.expand((batch) => batch), hasLength(5));
    expect(r.getAllRecords().every((record) => record.synced), isTrue);
    expect(outbox.readyMessages(), isEmpty);
  });

  test(
    '413 for one oversized message does not reject its smaller neighbours',
    () async {
      final sync = _HttpSync(oversizedId: 'oversized');
      final r = repo(sync);
      for (final id in ['oversized', 'small-1', 'small-2']) {
        final record = _record(id);
        await r.saveRecord(record);
        await r.queueRecord(record);
      }
      await r.syncPendingRecords();
      expect(records.getRecord('oversized')!.syncError, 'REQUEST_TOO_LARGE');
      expect(records.getRecord('small-1')!.synced, isTrue);
      expect(records.getRecord('small-2')!.synced, isTrue);
      expect(r.getPendingCount(), 0);
      expect(
        sync.batches.expand((batch) => batch).map((m) => m.payload['id']),
        ['small-1', 'small-2'],
      );
    },
  );

  test(
    'missing attachment stays pending and retries without resending metadata',
    () async {
      final sync = _FakeSync([]);
      final sender = _FakeSender();
      final r = RescueRepositoryImpl(
        localDataSource: records,
        senderDataSource: sender,
        outboxDataSource: outbox,
        syncDataSource: sync,
      );
      final image = File('${dir.path}/missing.jpg');
      final record = _record(
        'missing-image',
        imagePath: image.path,
      ).copyWith(sendMode: 'fullImage');
      await r.saveRecord(record);
      final pending = await r.sendRecord(record);
      expect(pending.synced, isFalse);
      expect(pending.metadataSynced, isTrue);
      expect(pending.attachmentError, 'ATTACHMENT_UNAVAILABLE');
      expect(r.getPendingCount(), 1);
      expect(sender.uploads, 0);

      await Hive.close();
      await records.init(hivePath: dir.path);
      await outbox.init(hivePath: dir.path);
      expect(r.getAllRecords().single.metadataSynced, isTrue);
      expect(
        r.getAllRecords().single.attachmentError,
        'ATTACHMENT_UNAVAILABLE',
      );
      await image.writeAsBytes([]);
      await r.syncPendingRecords();
      expect(r.getPendingCount(), 1);
      expect(
        r.getAllRecords().single.attachmentError,
        'ATTACHMENT_UNAVAILABLE',
      );

      await image.writeAsBytes([0xFF, 0xD8, 0xFF]);
      await r.syncPendingRecords();
      expect(sender.uploads, 1);
      expect(r.getPendingCount(), 0);
      expect(sync.batches, hasLength(1));
      expect(r.getAllRecords().single.attachmentError, isNull);
    },
  );

  test('permanent 415 image rejection still completes the report', () async {
    final image = File('${dir.path}/rejected.jpg');
    await image.writeAsBytes([0xFF, 0xD8, 0xFF]);
    final sender = _FakeSender(status: 415);
    final r = RescueRepositoryImpl(
      localDataSource: records,
      senderDataSource: sender,
      outboxDataSource: outbox,
      syncDataSource: _FakeSync([]),
    );
    final record = _record(
      'unsupported-image',
      imagePath: image.path,
    ).copyWith(sendMode: 'fullImage');
    await r.saveRecord(record);
    final sent = await r.sendRecord(record);
    expect(sent.synced, isTrue);
    expect(sent.attachmentError, isNull);
    expect(sender.uploads, 1);
  });
}
