import 'dart:convert';
import 'dart:typed_data';

import 'package:app/data/datasources/sms/sms_gateway_web.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

class SmsRecordingAdapter implements HttpClientAdapter {
  RequestOptions? smsRequest;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    if (options.path == '/api/capabilities') {
      return _json({'sms': true, 'sms_provider': 'twilio'});
    }
    if (options.path == '/api/reports/report-1/sms') {
      smsRequest = options;
      return _json({'status': 'queued'});
    }
    return ResponseBody.fromString('', 404);
  }

  ResponseBody _json(Map<String, dynamic> value) => ResponseBody.fromString(
    jsonEncode(value),
    200,
    headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    },
  );

  @override
  void close({bool force = false}) {}
}

void main() {
  test(
    'web SMS checks capability and sends only a confirmed request',
    () async {
      final adapter = SmsRecordingAdapter();
      final dio = Dio(BaseOptions(baseUrl: 'http://localhost'));
      dio.httpClientAdapter = adapter;
      final gateway = WebSmsGateway(
        dio: dio,
        configuredRecipient: '+84901234567',
      );

      final capabilities = await gateway.capabilities();
      final result = await gateway.sendConfirmed(
        reportId: 'report-1',
        recipient: capabilities.recipient!,
        idempotencyKey: 'sms-key-1',
      );
      final body = adapter.smsRequest!.data as Map<String, dynamic>;

      expect(capabilities.available, isTrue);
      expect(body['recipient'], '+84901234567');
      expect(body['idempotency_key'], 'sms-key-1');
      expect(body['confirmed'], isTrue);
      expect(result.status, 'queued');
    },
  );
}
