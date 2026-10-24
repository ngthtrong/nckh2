// Smoke UI trên Android thật: người chạy đăng nhập admin, test điều khiển tải gói và chạy bước online qua giao diện.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:app/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('admin tải gói E2E và chạy online trên Android', (tester) async {
    await app.main();
    // No password/token in dart-defines: sign in on the device while the test waits.
    Future<void> waitFor(Finder finder, {int seconds = 120}) async {
      final deadline = DateTime.now().add(Duration(seconds: seconds));
      while (finder.evaluate().isEmpty && DateTime.now().isBefore(deadline)) {
        await tester.pump(const Duration(milliseconds: 500));
        await Future<void>.delayed(const Duration(milliseconds: 500));
      }
      expect(finder, findsWidgets);
    }

    await waitFor(find.text('Cài đặt'), seconds: 180);
    await tester.tap(find.text('Cài đặt').last);
    await tester.pump(const Duration(seconds: 1));
    final section = find.byKey(const Key('admin-e2e-section'));
    // Settings is available before admin login. Wait for the user to sign in here.
    await waitFor(section, seconds: 180);
    await tester.ensureVisible(section);
    await tester.tap(
      find.descendant(of: section, matching: find.text('Thực nghiệm E2E')),
    );
    await tester.pump(const Duration(milliseconds: 350));
    final selectRun = find.byKey(const Key('mobile-e2e-select-run'));
    await tester.scrollUntilVisible(
      selectRun,
      350,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(selectRun);
    final confirmSelection = find.byKey(const Key('mobile-e2e-run-run_001'));
    await waitFor(confirmSelection);
    await tester.tap(confirmSelection);
    await tester.pumpAndSettle();
    final download = find.byKey(const Key('mobile-e2e-download'));
    await tester.ensureVisible(download);
    await tester.tap(download);
    await waitFor(find.byKey(const Key('mobile-e2e-next')));
    await tester.ensureVisible(find.byKey(const Key('mobile-e2e-next')));
    await tester.tap(find.byKey(const Key('mobile-e2e-next')));
    await waitFor(find.text('online: PASS'), seconds: 180);
    expect(find.text('online: FAIL'), findsNothing);
    // Other stages require a deliberate network/permission exercise; not claimed PASS here.
  }, timeout: const Timeout(Duration(minutes: 8)));
}
