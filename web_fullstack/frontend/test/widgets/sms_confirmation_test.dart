import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flood_rescue_web/widgets/sms_confirmation_button.dart';

void main() {
  testWidgets('SMS callback only runs after final confirmation', (tester) async {
    var calls = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SmsConfirmationButton(
            recipient: '+84901234567',
            onConfirmed: () async => calls++,
          ),
        ),
      ),
    );

    await tester.tap(find.text('Gửi SMS khẩn cấp'));
    await tester.pumpAndSettle();
    expect(calls, 0);
    expect(find.textContaining('4567'), findsOneWidget);

    await tester.tap(find.widgetWithText(FilledButton, 'Xác nhận gửi SMS'));
    await tester.pumpAndSettle();
    expect(calls, 1);
  });
}
