import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/domain/entities/sms_delivery.dart';
import 'package:app/presentation/screens/submitted/submitted_screen.dart';
import 'package:app/presentation/widgets/status_tracker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
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

Future<void> _show(
  WidgetTester tester,
  RescueRecord record, {
  double textScale = 1,
}) => tester.pumpWidget(
  MaterialApp(
    builder: (context, child) => MediaQuery(
      data: MediaQuery.of(
        context,
      ).copyWith(textScaler: TextScaler.linear(textScale)),
      child: child!,
    ),
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

  for (final (width, textScale) in [(360.0, 1.0), (320.0, 2.0)]) {
    testWidgets('wraps the full summary at ${width}px and ${textScale}x text', (
      tester,
    ) async {
      tester.view.physicalSize = Size(width, 800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final record = _record().copyWith(
        lat: 10.123456,
        lng: 106.123456,
        locationAccuracyMeters: 12345,
        trappedCount: 15,
        injuredCount: 12,
        vulnerableGroups: const [
          'Người già',
          'Trẻ em',
          'Phụ nữ mang thai',
          'Người khuyết tật',
        ],
      );

      await _show(tester, record, textScale: textScale);

      expect(tester.takeException(), isNull);
      for (final text in [
        'Số người mắc kẹt',
        'Số người bị thương',
        'Đối tượng ưu tiên',
        '15 người',
        '12 người',
        record.locationText,
        record.vulnerableGroups.join(', '),
      ]) {
        final finder = find.text(text);
        expect(finder, findsOneWidget);
        final paragraph = tester.renderObject<RenderParagraph>(finder);
        expect(paragraph.didExceedMaxLines, isFalse);
      }
      await tester.ensureVisible(find.text(record.vulnerableGroups.join(', ')));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }
}
