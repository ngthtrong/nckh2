class SyncMessage {
  final String messageId;
  final String clientId;
  final int sequenceNumber;
  final String operationType;
  final DateTime createdAt;
  final DateTime? expiresAt;
  final String payloadHash;
  final Map<String, dynamic> payload;
  final String deliveryStatus;
  final int attemptCount;
  final DateTime nextAttemptAt;
  final String? lastError;

  const SyncMessage({
    required this.messageId,
    required this.clientId,
    required this.sequenceNumber,
    required this.operationType,
    required this.createdAt,
    this.expiresAt,
    required this.payloadHash,
    required this.payload,
    this.deliveryStatus = 'pending',
    this.attemptCount = 0,
    required this.nextAttemptAt,
    this.lastError,
  });
}
