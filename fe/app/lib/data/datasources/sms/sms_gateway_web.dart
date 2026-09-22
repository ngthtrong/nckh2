import 'package:dio/dio.dart';

import '../../../config.dart';
import 'sms_gateway.dart';

SmsGateway createSmsGateway() => WebSmsGateway();

class WebSmsGateway implements SmsGateway {
  WebSmsGateway({Dio? dio, String? configuredRecipient})
    : _dio = dio ?? Dio(BaseOptions(baseUrl: kServerBaseUrl)),
      _configuredRecipient = configuredRecipient ?? kSmsRecipient;

  final Dio _dio;
  final String _configuredRecipient;

  @override
  Future<SmsCapabilities> capabilities() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/api/capabilities',
      );
      final data = response.data ?? const <String, dynamic>{};
      final recipientValid = _configuredRecipient.startsWith('+');
      final available = data['sms'] == true && recipientValid;
      return SmsCapabilities(
        available: available,
        recipient: recipientValid ? _configuredRecipient : null,
        provider: data['sms_provider'] as String?,
        message: available
            ? null
            : 'SMS backend chưa được bật hoặc SMS_RECIPIENT chưa hợp lệ.',
      );
    } catch (error) {
      return SmsCapabilities(
        available: false,
        message: 'Không thể kiểm tra SMS backend: $error',
      );
    }
  }

  @override
  Future<SmsSendResult> sendConfirmed({
    required String reportId,
    required String recipient,
    required String idempotencyKey,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/reports/$reportId/sms',
      data: {
        'recipient': recipient,
        'idempotency_key': idempotencyKey,
        'confirmed': true,
      },
    );
    final data = response.data ?? const <String, dynamic>{};
    return SmsSendResult(
      status: data['status'] as String? ?? 'queued',
      messageId: data['id'] as String?,
    );
  }
}
