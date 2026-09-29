import 'dart:io';

import 'package:app/data/datasources/outbox_local_datasource.dart';
import 'package:app/data/datasources/record_local_datasource.dart';
import 'package:app/data/datasources/sender_remote_datasource.dart';
import 'package:app/data/datasources/sync_remote_datasource.dart';
import 'package:app/data/models/sync_message_model.dart';
import 'package:app/data/repositories/rescue_repository_impl.dart';
import 'package:app/domain/entities/rescue_record.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_ce_flutter/hive_flutter.dart';

/// Server giả: trả kết quả theo hàng đợi [replies] (mỗi lần gửi lấy một mã), ghi
/// lại các batch và phát hiện hai request chạy chồng nhau.
class _FakeSync extends SyncRemoteDataSource {
  _FakeSync(this.replies);
  final List<String> replies;
  var offline = false;
  final batches = <List<SyncMessageModel>>[];
  final statusQueries = <List<String>>[];
  var inFlight = 0;
  var overlapped = false;

  @override
  Future<List<Map<String, dynamic>>> sendBatch(
    List<SyncMessageModel> messages,
  ) async {
    if (offline) throw const SocketException('mất mạng');
    if (++inFlight > 1) overlapped = true;
    batches.add(messages);
    await Future<void>.delayed(const Duration(milliseconds: 20));
    inFlight--;
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
  late RecordLocalDataSource records;
  late OutboxLocalDataSource outbox;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('outbox_test');
    records = RecordLocalDataSource();
    outbox = OutboxLocalDataSource();
    await records.init(hivePath: dir.path);
    await outbox.init(hivePath: dir.path);
  });

  tearDown(() async {
    await Hive.deleteFromDisk();
    await dir.delete(recursive: true);
  });

  RescueRepositoryImpl repo(_FakeSync sync) => RescueRepositoryImpl(
    localDataSource: records,
    senderDataSource: SenderRemoteDataSource(),
    outboxDataSource: outbox,
    syncDataSource: sync,
  );

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
    expect(isRecoverableDeadLetter('HTTP_400'), isTrue);
    expect(isRecoverableDeadLetter('INVALID_PAYLOAD'), isFalse);
    expect(isRecoverableDeadLetter('REPORT_ID_CONFLICT'), isFalse);
    expect(isRecoverableDeadLetter('REQUEST_TOO_LARGE'), isFalse);
    expect(isRecoverableDeadLetter(null), isFalse);
  });
}
