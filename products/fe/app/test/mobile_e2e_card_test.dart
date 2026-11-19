// Kiểm tra card E2E chỉ xuất hiện cho admin trên Android; không biến widget test thành bằng chứng thiết bị thật.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:app/presentation/widgets/mobile_e2e_card.dart';
import 'package:app/domain/services/mobile_e2e_runner.dart'
    show mobileE2eEnabled;

class Controller extends Fake implements AppController {
  final bool admin;
  Controller(this.admin);
  @override
  bool get isAdmin => admin;
  @override
  bool get isBenchmarking => false;
  @override
  Future<bool> validateAdmin() async => admin;
  @override
  String get adminServerUrl => 'http://192.168.137.1:18101';
}

void main() {
  testWidgets(
    'chọn được run 2 từ assets trước khi tải gói',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: MobileE2eCard(controller: Controller(true))),
        ),
      );
      await tester.tap(find.byKey(const Key('mobile-e2e-select-run')));
      final option = find.byKey(const Key('mobile-e2e-run-run_002'));
      for (
        var attempt = 0;
        attempt < 100 && option.evaluate().isEmpty;
        attempt++
      ) {
        await tester.runAsync(
          () => Future<void>.delayed(const Duration(milliseconds: 10)),
        );
        await tester.pump();
      }
      expect(find.text('run_001'), findsOneWidget);
      expect(find.text('run_002'), findsOneWidget);
      await tester.tap(option);
      await tester.pumpAndSettle();
      expect(find.text('Đã chọn: run_002'), findsOneWidget);
      expect(
        tester
            .widget<FilledButton>(find.byKey(const Key('mobile-e2e-download')))
            .onPressed,
        isNotNull,
      );
      expect(find.byKey(const Key('mobile-e2e-next')), findsNothing);
    },
    variant: TargetPlatformVariant.only(TargetPlatform.android),
    skip: !mobileE2eEnabled,
  );
  testWidgets('người thường không thấy công cụ E2E', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: MobileE2eCard(controller: Controller(false))),
      ),
    );
    expect(find.byKey(const Key('mobile-e2e-select-run')), findsNothing);
    expect(find.byKey(const Key('mobile-e2e-download')), findsNothing);
  }, variant: TargetPlatformVariant.only(TargetPlatform.android));
  testWidgets(
    'admin thấy tải gói trong APK thử nghiệm',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: MobileE2eCard(controller: Controller(true))),
        ),
      );
      expect(find.text('Chọn run'), findsOneWidget);
      expect(find.text('Tải gói benchmark'), findsOneWidget);
      expect(find.text('Chọn run / Tải hoặc mở gói'), findsNothing);
      expect(
        tester
            .widget<OutlinedButton>(
              find.byKey(const Key('mobile-e2e-select-run')),
            )
            .onPressed,
        isNotNull,
      );
      expect(
        tester
            .widget<FilledButton>(find.byKey(const Key('mobile-e2e-download')))
            .onPressed,
        isNull,
      );
      expect(find.text('Chọn run trước khi tải gói.'), findsOneWidget);
      expect(find.byKey(const Key('mobile-e2e-download')), findsOneWidget);
      expect(find.textContaining('backend flood-rescue'), findsOneWidget);
    },
    variant: TargetPlatformVariant.only(TargetPlatform.android),
    skip: !mobileE2eEnabled,
  );
}
