import 'package:app/presentation/screens/guide/guide_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('số điện thoại không tràn trên màn hình hẹp', (tester) async {
    tester.view.physicalSize = const Size(360, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      const MaterialApp(home: Scaffold(body: GuideScreen())),
    );
    await tester.tap(find.text('Số điện thoại'));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
  });
}
