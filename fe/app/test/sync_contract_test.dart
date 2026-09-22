import 'package:app/core/sync/payload_hash.dart';
import 'package:app/data/models/sync_message_model.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('payload hash dùng RFC 8785 và SHA-256', () {
    final payload = <String, dynamic>{
      'lng': 106.7009,
      'id': 'rescue-10492',
      'lat': 10.7769,
      'trappedCount': 2,
    };

    expect(
      computePayloadHash(payload),
      'sha256:2295b9a5bf05f463672c40f7c74127ff5db7110a27965f22cbc1ae53b3043cdf',
    );
  });

  test('message chỉ xuất các field thuộc wire contract', () {
    final message = SyncMessageModel(
      messageId: 'message-1',
      clientId: 'client-1',
      sequenceNumber: 7,
      operationType: 'CREATE_RESCUE_RECORD',
      createdAt: DateTime.utc(2026, 9, 22),
      payloadHash: 'sha256:test',
      payload: const {'id': 'rescue-1'},
      nextAttemptAt: DateTime.utc(2026, 9, 22),
    );

    expect(message.toRequestJson().keys, {
      'message_id',
      'client_id',
      'sequence_number',
      'operation_type',
      'created_at',
      'payload_hash',
      'payload',
    });
    expect(message.toRequestJson(), isNot(contains('attempt_count')));
  });
}
