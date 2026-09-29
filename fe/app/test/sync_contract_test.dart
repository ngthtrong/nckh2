import 'package:app/core/sync/payload_hash.dart';
import 'package:app/data/models/sync_message_model.dart';
import 'package:app/data/models/rescue_record_payload.dart';
import 'package:app/domain/entities/rescue_record.dart';
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

  test('payload cứu hộ chứa tình trạng khẩn cấp đã chọn', () {
    final payload = rescueRecordPayload(
      RescueRecord(
        id: 'rescue-1',
        createdAt: DateTime.utc(2026, 9, 27),
        lat: 10.0405,
        lng: 105.7606,
        trappedCount: 2,
        injuredCount: 1,
        vulnerableGroups: const ['Trẻ em'],
        cannotMove: true,
        severeSigns: const ['unresponsive', 'heavy_bleeding'],
        urgencyScore: 0.75,
        description: 'Nước đang dâng',
        sendMode: 'direct',
      ),
    );

    expect(payload['L_i'], {'lat': 10.0405, 'lon': 105.7606});
    expect(payload['N_i'], 2);
    expect(payload['injury_count'], 1);
    expect(payload['E_i'], 0.75);
    expect(payload['urgency_features'], {
      'cannot_move': true,
      'severe_condition': true,
      'severe_signs': ['unresponsive', 'heavy_bleeding'],
    });
    expect(payload['image_attached'], false);
  });

  test('payload đổi mã dấu hiệu cũ sang mã dataset v5', () {
    final payload = rescueRecordPayload(
      RescueRecord(
        id: 'rescue-old',
        createdAt: DateTime.utc(2026, 9, 27),
        lat: null,
        lng: null,
        severeSigns: const ['respiratory_distress', 'seizure', 'major_trauma'],
        sendMode: 'direct',
      ),
    );

    expect(payload['urgency_features']['severe_signs'], [
      'respiratory_distress_or_cyanosis',
      'active_convulsions',
      'high_risk_trauma',
    ]);
    expect(payload['E_i'], isNull);
  });
}
