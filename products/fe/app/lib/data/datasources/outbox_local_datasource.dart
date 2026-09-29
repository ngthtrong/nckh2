import 'dart:math';

import 'package:hive_ce_flutter/hive_flutter.dart';
import 'package:uuid/uuid.dart';

import '../../core/sync/payload_hash.dart';
import '../models/sync_message_model.dart';

class OutboxLocalDataSource {
  static const boxName = 'sync_outbox';
  static const _clientIdKey = '_meta:client_id';
  static const _sequenceKey = '_meta:sequence_number';

  final Uuid _uuid;
  final Random _random;
  Box<dynamic>? _box;

  OutboxLocalDataSource({Uuid? uuid, Random? random})
    : _uuid = uuid ?? const Uuid(),
      _random = random ?? Random.secure();

  Future<void> init() async {
    await Hive.initFlutter();
    _box = await Hive.openBox<dynamic>(boxName);
    if (_box!.get(_clientIdKey) == null) {
      await _box!.put(_clientIdKey, _uuid.v4());
    }
    await _recoverInFlight();
  }

  Future<SyncMessageModel> enqueueCreate(Map<String, dynamic> payload) async {
    final existing = messageForRecord(payload['id'] as String);
    if (existing != null) return existing;

    final sequence = ((_box!.get(_sequenceKey) as num?)?.toInt() ?? 0) + 1;
    final now = DateTime.now().toUtc();
    final message = SyncMessageModel(
      messageId: _uuid.v4(),
      clientId: _box!.get(_clientIdKey) as String,
      sequenceNumber: sequence,
      operationType: 'CREATE_RESCUE_RECORD',
      createdAt: now,
      payloadHash: computePayloadHash(payload),
      payload: payload,
      nextAttemptAt: now,
    );
    await _box!.putAll({
      _sequenceKey: sequence,
      message.messageId: message.toStorageJson(),
    });
    return message;
  }

  List<SyncMessageModel> readyMessages({int limit = 50}) {
    final now = DateTime.now().toUtc();
    final messages =
        _messages()
            .where(
              (m) =>
                  m.deliveryStatus == 'pending' &&
                  !m.nextAttemptAt.isAfter(now),
            )
            .toList()
          ..sort((a, b) => a.sequenceNumber.compareTo(b.sequenceNumber));
    return messages.take(limit).toList();
  }

  SyncMessageModel? messageForRecord(String recordId) {
    for (final message in _messages()) {
      if (message.operationType == 'CREATE_RESCUE_RECORD' &&
          message.payload['id'] == recordId) {
        return message;
      }
    }
    return null;
  }

  Future<void> markInFlight(Iterable<SyncMessageModel> messages) async {
    await _box!.putAll({
      for (final message in messages)
        message.messageId: message
            .copyWith(deliveryStatus: 'in_flight')
            .toStorageJson(),
    });
  }

  Future<void> acknowledge(String messageId) => _box!.delete(messageId);

  Future<void> markDeadLetter(String messageId, String? error) async {
    final message = _read(messageId);
    if (message == null) return;
    await _box!.put(
      messageId,
      message
          .copyWith(deliveryStatus: 'dead_letter', lastError: error)
          .toStorageJson(),
    );
  }

  Future<void> scheduleRetry(String messageId, String? error) async {
    final message = _read(messageId);
    if (message == null) return;
    final attempt = message.attemptCount + 1;
    final ceilingSeconds = min(300, 1 << min(attempt, 9));
    final delay = Duration(
      milliseconds: _random.nextInt(ceilingSeconds * 1000 + 1),
    );
    await _box!.put(
      messageId,
      message
          .copyWith(
            deliveryStatus: 'pending',
            attemptCount: attempt,
            nextAttemptAt: DateTime.now().toUtc().add(delay),
            lastError: error,
          )
          .toStorageJson(),
    );
  }

  Future<void> _recoverInFlight() async {
    final updates = <String, dynamic>{};
    for (final message in _messages()) {
      if (message.deliveryStatus == 'in_flight') {
        updates[message.messageId] = message
            .copyWith(
              deliveryStatus: 'pending',
              nextAttemptAt: DateTime.now().toUtc(),
            )
            .toStorageJson();
      }
    }
    if (updates.isNotEmpty) await _box!.putAll(updates);
  }

  Iterable<SyncMessageModel> _messages() sync* {
    for (final key in _box!.keys.whereType<String>()) {
      if (key.startsWith('_meta:')) continue;
      final message = _read(key);
      if (message != null) yield message;
    }
  }

  SyncMessageModel? _read(String id) {
    final raw = _box!.get(id);
    if (raw is! Map) return null;
    return SyncMessageModel.fromStorageJson(Map<String, dynamic>.from(raw));
  }
}
