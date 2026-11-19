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

  testWidgets('số điện thoại vẫn đọc được khi tăng cỡ chữ trên màn hình hẹp', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: const TextScaler.linear(1.5)),
          child: child!,
        ),
        home: const Scaffold(body: GuideScreen()),
      ),
    );
    await tester.tap(find.text('Số điện thoại'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });
}
