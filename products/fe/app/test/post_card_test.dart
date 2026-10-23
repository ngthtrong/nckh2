import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/domain/entities/sms_delivery.dart';
import 'package:app/presentation/widgets/post_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

RescueRecord record({
  bool ack = false,
  bool synced = false,
  String? error,
  String status = 'processing',
  SmsStatus sms = SmsStatus.notAttempted,
}) => RescueRecord(
  id: 'history-report',
  createdAt: DateTime(2026),
  lat: 10,
  lng: 106,
  locationAccuracyMeters: 2000,
  sendMode: 'queuedOffline',
  metadataSynced: ack,
  synced: synced,
  syncError: error,
  status: status,
  smsStatus: sms,
);

Future<void> show(
  WidgetTester tester,
  RescueRecord record, {
  double scale = 1,
}) => tester.pumpWidget(
  MaterialApp(
    home: MediaQuery(
      data: MediaQueryData(textScaler: TextScaler.linear(scale)),
      child: Scaffold(
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: PostCard(record: record),
        ),
      ),
    ),
  ),
);

void main() {
  for (final sms in [
    SmsStatus.notAttempted,
    SmsStatus.sent,
    SmsStatus.unknown,
  ]) {
    testWidgets('unacknowledged $sms report never claims server receipt', (
      tester,
    ) async {
      await show(tester, record(sms: sms));
      expect(find.text('Đã nhận'), findsNothing);
      expect(find.text('Chờ gửi'), findsOneWidget);
    });
  }
  testWidgets('permanent rejection is visible in history', (tester) async {
    await show(tester, record(error: 'HTTP_400'));
    expect(find.text('Đã nhận'), findsNothing);
    expect(find.text('Bị từ chối'), findsOneWidget);
    expect(find.textContaining('HTTP_400'), findsOneWidget);
    expect(find.textContaining('112'), findsOneWidget);
  });
  for (final (value, label) in [
    ('processing', 'Đã nhận'),
    ('dispatched', 'Đang đến'),
    ('resolved', 'Hoàn thành'),
    ('cancelled', 'Đã đóng'),
  ]) {
    testWidgets('metadata ACK preserves server status $value', (tester) async {
      await show(tester, record(ack: true, status: value));
      expect(find.text(label), findsOneWidget);
      expect(find.text('Chờ gửi'), findsNothing);
    });
  }
  testWidgets('legacy synced report counts as received without metadata flag', (
    tester,
  ) async {
    await show(tester, record(synced: true));
    expect(find.text('Đã nhận'), findsOneWidget);
  });
  testWidgets('long location wraps on a narrow screen with large text', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(320, 800));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await show(tester, record(), scale: 2);
    expect(find.textContaining('±2000 m'), findsOneWidget);
    expect(find.textContaining('vị trí gần đúng'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
