import 'dart:io';

import 'package:app/data/datasources/outbox_local_datasource.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_ce_flutter/hive_flutter.dart';

void main() {
  late Directory dir;
  late OutboxLocalDataSource outbox;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('outbox_index_test');
    outbox = OutboxLocalDataSource();
    await outbox.init(hivePath: dir.path);
  });

  tearDown(() async {
    await Hive.deleteFromDisk();
    await dir.delete(recursive: true);
  });

  test('record lookup does not parse unrelated messages', () async {
    final first = await outbox.enqueueCreate({'id': 'first'});
    for (var i = 0; i < 300; i++) {
      await outbox.enqueueCreate({'id': 'record-$i'});
    }
    // A full scan would parse this unrelated entry and fail.
    final box = Hive.box<dynamic>(OutboxLocalDataSource.boxName);
    final damaged = Map<String, dynamic>.from(box.get(first.messageId) as Map);
    damaged['payload'] = 'damaged';
    await box.put(first.messageId, damaged);
    for (var i = 0; i < 300; i++) {
      expect(outbox.messageForRecord('record-$i')?.payload['id'], 'record-$i');
    }
    expect(outbox.messageForRecord('unknown'), isNull);
  });

  test(
    'index follows recovery, retry, dead letter replacement and ACK',
    () async {
      final first = await outbox.enqueueCreate({'id': 'report'});
      await outbox.markInFlight([first]);
      expect(outbox.messageForRecord('report')?.deliveryStatus, 'in_flight');
      await Hive.close();
      outbox = OutboxLocalDataSource();
      await outbox.init(hivePath: dir.path);
      expect(outbox.messageForRecord('report')?.deliveryStatus, 'pending');

      await outbox.scheduleRetry(first.messageId, 'NETWORK');
      expect(outbox.messageForRecord('report')?.attemptCount, 1);
      expect(outbox.messageForRecord('report')?.lastError, 'NETWORK');
      await outbox.makePendingReady();
      expect(outbox.readyMessages().single.messageId, first.messageId);

      await outbox.markDeadLetter(first.messageId, 'SEQUENCE_REUSED');
      expect(outbox.messageForRecord('report')?.deliveryStatus, 'dead_letter');
      final replacement = await outbox.enqueueCreate({'id': 'report'});
      expect(replacement.messageId, isNot(first.messageId));
      expect(
        outbox.messageForRecord('report')?.messageId,
        replacement.messageId,
      );
      expect(
        Hive.box<dynamic>(OutboxLocalDataSource.boxName).get(first.messageId),
        isNull,
      );

      await outbox.markDeadLetter(replacement.messageId, 'INVALID_PAYLOAD');
      expect(
        (await outbox.enqueueCreate({'id': 'report'})).messageId,
        replacement.messageId,
      );
      await outbox.acknowledge(replacement.messageId);
      expect(outbox.messageForRecord('report'), isNull);
      final next = await outbox.enqueueCreate({'id': 'report'});
      expect(next.sequenceNumber, greaterThan(replacement.sequenceNumber));
      expect(outbox.messageForRecord('report')?.messageId, next.messageId);
    },
  );

  test(
    'legacy duplicate messages remain indexed when the first one is ACKed',
    () async {
      final first = await outbox.enqueueCreate({'id': 'report'});
      final duplicate = await outbox.enqueueCreate({'id': 'duplicate'});
      final box = Hive.box<dynamic>(OutboxLocalDataSource.boxName);
      final raw = Map<String, dynamic>.from(
        box.get(duplicate.messageId) as Map,
      );
      raw['payload'] = {'id': 'report'};
      await box.put(duplicate.messageId, raw);
      await Hive.close();
      outbox = OutboxLocalDataSource();
      await outbox.init(hivePath: dir.path);
      expect(outbox.messageForRecord('report')?.messageId, first.messageId);
      await outbox.acknowledge(first.messageId);
      expect(outbox.messageForRecord('report')?.messageId, duplicate.messageId);
    },
  );
}
