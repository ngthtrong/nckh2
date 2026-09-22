import 'package:app/presentation/widgets/sms_confirmation_dialog.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('SMS requires the final confirmation and masks the recipient', (
    tester,
  ) async {
    bool? result;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: FilledButton(
              onPressed: () async {
                result = await showSmsConfirmation(
                  context,
                  recipient: '+84901234567',
                );
              },
              child: const Text('Mở xác nhận'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Mở xác nhận'));
    await tester.pumpAndSettle();
    expect(result, isNull);
    expect(find.textContaining('4567'), findsOneWidget);
    expect(find.textContaining('+8490123'), findsNothing);

    await tester.tap(find.widgetWithText(FilledButton, 'Gửi báo cáo + SMS'));
    await tester.pumpAndSettle();
    expect(result, isTrue);
  });
}
