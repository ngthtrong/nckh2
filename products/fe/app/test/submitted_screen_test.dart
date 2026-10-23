import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/domain/entities/sms_delivery.dart';
import 'package:app/presentation/screens/submitted/submitted_screen.dart';
import 'package:app/presentation/widgets/status_tracker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

RescueRecord _record({
  bool synced = false,
  bool metadataSynced = false,
  String? syncError,
  String status = 'processing',
  String? imagePath,
  SmsStatus smsStatus = SmsStatus.notAttempted,
}) => RescueRecord(
  id: 'submitted-test',
  createdAt: DateTime(2026),
  lat: null,
  lng: null,
  sendMode: 'queuedOffline',
  synced: synced,
  metadataSynced: metadataSynced,
  syncError: syncError,
  status: status,
  imagePath: imagePath,
  smsStatus: smsStatus,
);

Future<void> _show(WidgetTester tester, RescueRecord record) =>
    tester.pumpWidget(
      MaterialApp(
        home: SubmittedScreen(record: record, onHomePressed: () {}),
      ),
    );

void main() {
  for (final (name, record) in [
    ('queued offline', _record()),
    ('rejected', _record(syncError: 'INVALID_PAYLOAD')),
    ('SMS sent without server ACK', _record(smsStatus: SmsStatus.sent)),
  ]) {
    testWidgets('does not claim reception when $name', (tester) async {
      await _show(tester, record);

      expect(find.byType(StatusTracker), findsNothing);
      expect(find.text('Đã nhận'), findsNothing);
      expect(find.text('Về trang chủ'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('shows reception after metadata ACK while an image is pending', (
    tester,
  ) async {
    await _show(
      tester,
      _record(metadataSynced: true, imagePath: 'pending.jpg'),
    );

    expect(find.textContaining('Máy chủ đã nhận nội dung'), findsOneWidget);
    expect(find.byType(StatusTracker), findsOneWidget);
    expect(find.byIcon(Icons.check), findsOneWidget);
  });

  for (final (status, checks) in [
    ('processing', 1),
    ('dispatched', 2),
    ('resolved', 3),
  ]) {
    testWidgets('keeps server progress for synced $status reports', (
      tester,
    ) async {
      await _show(tester, _record(synced: true, status: status));

      expect(find.byType(StatusTracker), findsOneWidget);
      expect(find.byIcon(Icons.check), findsNWidgets(checks));
    });
  }

  testWidgets('keeps the server cancellation message', (tester) async {
    await _show(tester, _record(metadataSynced: true, status: 'cancelled'));

    expect(find.textContaining('Điều phối viên đã đóng'), findsOneWidget);
    expect(find.text('Đã nhận'), findsNothing);
    expect(find.byIcon(Icons.check), findsNothing);
  });
}
