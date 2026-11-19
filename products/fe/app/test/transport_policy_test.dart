import 'dart:async';

import 'package:app/config.dart';
import 'package:app/data/datasources/admin_session.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

class _Adapter implements HttpClientAdapter {
  int calls = 0;
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<List<int>>? stream,
    Future<void>? cancel,
  ) async {
    calls++;
    throw StateError('Credentials must never reach HTTP');
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  test(
    'HTTPS required by default; demo HTTP only permits loopback/private LAN',
    () {
      expect(isAllowedServerUrl('https://rescue.example'), isTrue);
      for (final url in [
        'http://192.168.1.2:8000',
        'http://localhost:8000',
        'http://10.0.2.2:8000',
        'http://172.16.0.1:8000',
      ]) {
        expect(isAllowedServerUrl(url), isFalse);
        expect(isAllowedServerUrl(url, allowInsecureLan: true), isTrue);
      }
      for (final url in [
        '',
        'file:///tmp/model',
        'http://example.com',
        'http://8.8.8.8',
        'https://user:pass@rescue.example',
        'https://rescue.example?token=abc',
        'http://192.168.999.1',
      ]) {
        expect(isAllowedServerUrl(url, allowInsecureLan: true), isFalse);
      }
    },
  );

  test('admin HTTP login rejected before any credentials are sent', () async {
    final adapter = _Adapter();
    final session = AdminSession(dio: Dio()..httpClientAdapter = adapter);
    addTearDown(session.dispose);
    await expectLater(
      session.login('http://192.168.1.2:8000', 'admin', 'secret'),
      throwsStateError,
    );
    expect(adapter.calls, 0);
    expect(session.isAdmin, isFalse);
  });
}
