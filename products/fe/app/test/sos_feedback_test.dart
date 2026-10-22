import 'dart:async';

import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/domain/entities/sms_delivery.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:app/presentation/screens/home/home_screen.dart';
import 'package:app/presentation/widgets/sos_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _Controller extends ChangeNotifier implements AppController {
  _Controller(this.result);

  Future<RescueRecord?> Function() result;
  int sends = 0;

  @override
  bool get isBusy => false;
  @override
  String get networkLabel => 'none';
  @override
  bool get isModelReady => false;
  @override
  bool get isModelLoading => false;
  @override
  String get modelStatusHint => 'Model chưa sẵn sàng';
  @override
  bool get isAdmin => false;
  @override
  RescueRecord? get latestSos => null;
  @override
  int get pendingCount => 0;

  @override
  Future<RescueRecord?> sendSos() {
    sends++;
    return result();
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

RescueRecord _record({
  bool synced = false,
  String sendMode = 'queuedOffline',
  String? syncError,
  SmsStatus smsStatus = SmsStatus.notAttempted,
}) => RescueRecord(
  id: 'sos-test',
  createdAt: DateTime(2026),
  lat: null,
  lng: null,
  synced: synced,
  sendMode: sendMode,
  syncError: syncError,
  smsStatus: smsStatus,
);

Future<void> _show(WidgetTester tester, _Controller controller) =>
    tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: HomeScreen(controller: controller, onComposePressed: () {}),
        ),
      ),
    );

Finder _buttonText(String text) => find.descendant(
  of: find.byType(SosButtonSection),
  matching: find.text(text),
);

void main() {
  for (final (name, result, message, snack) in [
    (
      'accepted by backend',
      _record(synced: true, sendMode: 'textOnly'),
      'Máy chủ đã tiếp nhận SOS.',
      'Máy chủ đã tiếp nhận SOS.',
    ),
    (
      'queued offline',
      _record(),
      'SOS trong hàng đợi, sẽ gửi khi có mạng.',
      'SOS trong hàng đợi, sẽ gửi khi có mạng.',
    ),
    (
      'sent by SMS',
      _record(sendMode: 'smsFallback', smsStatus: SmsStatus.sent),
      'Đã gửi SMS; chưa xác nhận tiếp nhận.',
      'Đã gửi SMS; chưa xác nhận tiếp nhận. SOS sẽ đồng bộ khi có mạng.',
    ),
    (
      'SMS result unknown',
      _record(smsStatus: SmsStatus.unknown),
      'Chưa xác nhận kết quả SMS. SOS vẫn chờ đồng bộ; không tự gửi SMS lặp.',
      smsStatusMessage(SmsStatus.unknown),
    ),
    (
      'SMS failed',
      _record(smsStatus: SmsStatus.failed),
      'Không gửi được SMS. SOS đã được lưu; hãy gọi 112 nếu cần trợ giúp ngay.',
      smsStatusMessage(SmsStatus.failed),
    ),
    (
      'failed',
      null,
      'Chưa gửi được SOS. Hãy gọi 112.',
      'Không gửi được SOS, hãy gọi 112.',
    ),
    (
      'rejected by backend',
      _record(syncError: 'INVALID_PAYLOAD'),
      'Chưa gửi được SOS. Hãy gọi 112.',
      'Máy chủ từ chối SOS (INVALID_PAYLOAD), hãy gọi 112.',
    ),
  ]) {
    testWidgets('SOS shows truthful feedback when $name', (tester) async {
      final controller = _Controller(() async => result);
      await _show(tester, controller);
      await tester.tap(_buttonText('SOS'));
      await tester.pump();

      expect(_buttonText(message), findsOneWidget);
      expect(find.widgetWithText(SnackBar, snack), findsOneWidget);
      expect(find.textContaining('Đội cứu hộ đã nhận'), findsNothing);
      await tester.pump(const Duration(seconds: 3));
      expect(_buttonText('SOS'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
      controller.dispose();
    });
  }

  testWidgets('SOS blocks only an in-flight send and restarts feedback timer', (
    tester,
  ) async {
    final pending = Completer<RescueRecord?>();
    final controller = _Controller(() => pending.future);
    await _show(tester, controller);
    await tester.tap(_buttonText('SOS'));
    await tester.pump();
    await tester.tap(_buttonText('Đang gửi'));
    expect(controller.sends, 1);

    pending.complete(_record(synced: true));
    await tester.pump();
    await tester.pump(const Duration(seconds: 2));
    controller.result = () async => _record();
    await tester.tap(_buttonText('Đã tiếp nhận'));
    await tester.pump();
    expect(controller.sends, 2);
    await tester.pump(const Duration(seconds: 1));
    expect(_buttonText('Đã xếp hàng'), findsOneWidget);
    await tester.pump(const Duration(seconds: 2));
    expect(_buttonText('SOS'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
    controller.dispose();
  });

  testWidgets('SOS completion and feedback timer are safe after disposal', (
    tester,
  ) async {
    final pending = Completer<RescueRecord?>();
    final controller = _Controller(() => pending.future);
    await _show(tester, controller);
    await tester.tap(_buttonText('SOS'));
    await tester.pumpWidget(const SizedBox());
    pending.complete(_record());
    await tester.pump();
    expect(tester.takeException(), isNull);

    controller.result = () async => _record();
    await _show(tester, controller);
    await tester.tap(_buttonText('SOS'));
    await tester.pump();
    await tester.pumpWidget(const SizedBox());
    await tester.pump(const Duration(seconds: 3));
    expect(tester.takeException(), isNull);
    controller.dispose();
  });
}
