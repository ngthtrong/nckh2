class SmsCapabilities {
  const SmsCapabilities({
    required this.available,
    this.recipient,
    this.provider,
    this.message,
  });

  final bool available;
  final String? recipient;
  final String? provider;
  final String? message;
}

class SmsSendResult {
  const SmsSendResult({required this.status, this.messageId});

  final String status;
  final String? messageId;
}

abstract interface class SmsGateway {
  Future<SmsCapabilities> capabilities();

  Future<SmsSendResult> sendConfirmed({
    required String reportId,
    required String recipient,
    required String idempotencyKey,
  });
}
