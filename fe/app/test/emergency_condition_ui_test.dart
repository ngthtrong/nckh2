import 'package:app/presentation/widgets/emergency_condition_selector.dart';
import 'package:app/presentation/widgets/payload_demo_panel.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('tình trạng khẩn cấp dùng được ở màn hình mobile hẹp', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    var selected = <String>[];
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: StatefulBuilder(
                builder: (context, setState) => Column(
                  children: [
                    EmergencyConditionSelector(
                      cannotMove: false,
                      severeSigns: selected,
                      onCannotMoveChanged: (_) {},
                      onSevereSignsChanged: (values) =>
                          setState(() => selected = values),
                    ),
                    PayloadDemoPanel(
                      payload: {
                        'urgency_features': {
                          'cannot_move': false,
                          'severe_signs': selected,
                        },
                      },
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Chảy máu nhiều'));
    await tester.pump();
    expect(selected, ['heavy_bleeding']);

    await tester.ensureVisible(
      find.text('Xem payload demo (dành cho phát triển)'),
    );
    await tester.tap(find.text('Xem payload demo (dành cho phát triển)'));
    await tester.pumpAndSettle();
    expect(find.textContaining('heavy_bleeding'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
