import '../../domain/entities/sync_message.dart';

/// Persistence/wire representation of a [SyncMessage].
///
/// The message contract uses snake_case keys and UTC ISO-8601 timestamps,
/// while delivery fields are kept locally by the durable outbox.
class SyncMessageModel extends SyncMessage {
  const SyncMessageModel({
    required super.messageId,
    required super.clientId,
    required super.sequenceNumber,
    required super.operationType,
    required super.createdAt,
    super.expiresAt,
    required super.payloadHash,
    required super.payload,
    super.deliveryStatus,
    super.attemptCount,
    required super.nextAttemptAt,
    super.lastError,
  });

  /// Rehydrates a message stored in the Hive outbox.
  ///
  /// Stored timestamps are ISO-8601 strings.  DateTime values are accepted as
  /// well to make migration/recovery from older Hive values safe.
  factory SyncMessageModel.fromStorageJson(Map<String, dynamic> json) {
    final payload = json['payload'];
    if (payload is! Map) {
      throw const FormatException('Sync message payload must be an object');
    }

    return SyncMessageModel(
      messageId: _requiredString(json, 'message_id'),
      clientId: _requiredString(json, 'client_id'),
      sequenceNumber: _requiredInt(json, 'sequence_number'),
      operationType: _requiredString(json, 'operation_type'),
      createdAt: _requiredDateTime(json, 'created_at'),
      expiresAt: _optionalDateTime(json['expires_at']),
      payloadHash: _requiredString(json, 'payload_hash'),
      payload: Map<String, dynamic>.from(payload),
      deliveryStatus: json['delivery_status'] as String? ?? 'pending',
      attemptCount: _intOrDefault(json['attempt_count'], 0),
      nextAttemptAt:
          _optionalDateTime(json['next_attempt_at']) ?? DateTime.now().toUtc(),
      lastError: json['last_error'] as String?,
    );
  }

  /// Serializes all fields required to restore the durable outbox entry.
  Map<String, dynamic> toStorageJson() => {
    ...toRequestJson(),
    'delivery_status': deliveryStatus,
    'attempt_count': attemptCount,
    'next_attempt_at': nextAttemptAt.toUtc().toIso8601String(),
    'last_error': lastError,
  };

  /// Serializes only the fields accepted by `POST /sync/messages`.
  ///
  /// Local delivery state (`delivery_status`, retry counters, and errors) is
  /// intentionally omitted from this map.
  Map<String, dynamic> toRequestJson() {
    final result = <String, dynamic>{
      'message_id': messageId,
      'client_id': clientId,
      'sequence_number': sequenceNumber,
      'operation_type': operationType,
      'created_at': createdAt.toUtc().toIso8601String(),
      'payload_hash': payloadHash,
      'payload': payload,
    };
    if (expiresAt != null) {
      result['expires_at'] = expiresAt!.toUtc().toIso8601String();
    }
    return result;
  }

  SyncMessageModel copyWith({
    String? messageId,
    String? clientId,
    int? sequenceNumber,
    String? operationType,
    DateTime? createdAt,
    DateTime? expiresAt,
    String? payloadHash,
    Map<String, dynamic>? payload,
    String? deliveryStatus,
    int? attemptCount,
    DateTime? nextAttemptAt,
    String? lastError,
  }) {
    return SyncMessageModel(
      messageId: messageId ?? this.messageId,
      clientId: clientId ?? this.clientId,
      sequenceNumber: sequenceNumber ?? this.sequenceNumber,
      operationType: operationType ?? this.operationType,
      createdAt: createdAt ?? this.createdAt,
      expiresAt: expiresAt ?? this.expiresAt,
      payloadHash: payloadHash ?? this.payloadHash,
      payload: payload ?? this.payload,
      deliveryStatus: deliveryStatus ?? this.deliveryStatus,
      attemptCount: attemptCount ?? this.attemptCount,
      nextAttemptAt: nextAttemptAt ?? this.nextAttemptAt,
      lastError: lastError ?? this.lastError,
    );
  }
}

String _requiredString(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value is String && value.isNotEmpty) return value;
  throw FormatException('Sync message field "$key" must be a non-empty string');
}

int _requiredInt(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value is num) return value.toInt();
  throw FormatException('Sync message field "$key" must be an integer');
}

int _intOrDefault(Object? value, int fallback) {
  return value is num ? value.toInt() : fallback;
}

DateTime _requiredDateTime(Map<String, dynamic> json, String key) {
  final value = _optionalDateTime(json[key]);
  if (value != null) return value;
  throw FormatException('Sync message field "$key" must be an ISO-8601 date');
}

DateTime? _optionalDateTime(Object? value) {
  if (value == null) return null;
  if (value is DateTime) return value.toUtc();
  if (value is String && value.isNotEmpty) {
    return DateTime.parse(value).toUtc();
  }
  throw const FormatException('Sync message date must be an ISO-8601 value');
}
