import 'package:app/domain/usecases/submit_rescue_post_usecase.dart';
import 'package:app/presentation/widgets/number_stepper_input.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('description limits accept boundaries, Unicode and whitespace', () {
    String? validate(String text) => SubmitRescuePostUseCase.validateInput(
      trappedCount: 10000,
      injuredCount: 0,
      description: text,
    );
    expect(validate(List.filled(300, 'cứu').join('\n\t')), isNull);
    expect(validate('á' * 2000), isNull);
    expect(validate('👍' * 2000), isNull);
    expect(validate('á' * 2001), contains('2000 ký tự'));
    expect(validate(List.filled(301, 'a').join(' ')), contains('300 từ'));
    expect(SubmitRescuePostUseCase.descriptionWordCount('  cứu\n\thộ  '), 2);
  });

  testWidgets('people input clamps typing and paste; buttons stop at limits', (
    tester,
  ) async {
    var value = 1;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StatefulBuilder(
            builder: (context, setState) => NumberStepperInput(
              label: 'Số người',
              value: value,
              icon: Icons.people,
              onChanged: (next) => setState(() => value = next),
            ),
          ),
        ),
      ),
    );
    final input = find.byType(TextField);
    await tester.enterText(input, '10001');
    await tester.pump();
    expect(value, 10000);
    expect(tester.widget<TextField>(input).controller!.text, '10000');
    expect(
      tester
          .widget<IconButton>(find.widgetWithIcon(IconButton, Icons.add))
          .onPressed,
      isNull,
    );
    await tester.enterText(input, '9' * 100);
    await tester.pump();
    expect(value, 10000);
    await tester.tap(find.byIcon(Icons.remove));
    await tester.pump();
    expect(value, 9999);
    await tester.enterText(input, '');
    await tester.pump();
    expect(value, 0);
    expect(
      tester
          .widget<IconButton>(find.widgetWithIcon(IconButton, Icons.remove))
          .onPressed,
      isNull,
    );
    await tester.tap(find.byIcon(Icons.add));
    await tester.pump();
    expect(value, 1);
  });
}
