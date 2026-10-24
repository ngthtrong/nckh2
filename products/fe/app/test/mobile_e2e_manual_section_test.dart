import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:app/presentation/widgets/mobile_e2e_manual_section.dart';

void main() {
  testWidgets('hướng dẫn click Case 7/8 và xác nhận Case 9 riêng từng run', (
    tester,
  ) async {
    var dashboardConfirmed = false;
    String? manual;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: MobileE2eManualSection(
              checks: {
                for (final stage in [
                  'manual_android_ui',
                  'manual_physical_network',
                  'dashboard',
                ])
                  stage: {'status': 'NOT_RUN'},
              },
              goldRun: 'run_002',
              busy: false,
              onManual: (stage) => manual = stage,
              onDashboard: () => dashboardConfirmed = true,
            ),
          ),
        ),
      ),
    );
    expect(find.text(mobileManualGuides['manual_android_ui']!), findsOneWidget);
    expect(
      find.text(mobileManualGuides['manual_physical_network']!),
      findsOneWidget,
    );
    expect(find.textContaining('dashboard --run 2'), findsOneWidget);
    await tester.tap(find.byKey(const Key('manual-result-manual_android_ui')));
    expect(manual, 'manual_android_ui');
    final confirm = find.byKey(const Key('manual-dashboard-confirm'));
    await tester.ensureVisible(confirm);
    await tester.tap(confirm);
    expect(dashboardConfirmed, isTrue);
  });
  testWidgets('FAIL phải có mô tả; hủy hộp thoại không tự ghi nhận đạt', (
    tester,
  ) async {
    ManualCheckResult? result;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Builder(
            builder: (context) => TextButton(
              onPressed: () async =>
                  result = await showDialog<ManualCheckResult>(
                    context: context,
                    builder: (_) =>
                        const MobileE2eManualDialog(stage: 'manual_android_ui'),
                  ),
              child: const Text('Mở'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Mở'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('manual-fail')));
    await tester.pump();
    expect(find.text('Nhập mô tả lỗi trước khi ghi FAIL.'), findsOneWidget);
    expect(result, isNull);
    await tester.enterText(
      find.byKey(const Key('manual-note')),
      'Lịch sử thiếu ảnh',
    );
    await tester.tap(find.byKey(const Key('manual-fail')));
    await tester.pumpAndSettle();
    expect(result!.passed, isFalse);
    expect(result!.detail, 'Lịch sử thiếu ảnh');
  });
}
