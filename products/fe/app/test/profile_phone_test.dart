import 'package:app/domain/entities/user.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:app/presentation/screens/auth/register_screen.dart';
import 'package:app/presentation/screens/settings/settings_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _Controller extends Fake implements AppController {
  User? saved;
  @override
  User get currentUser =>
      const User(username: 'user', phone: '0901234567', address: 'Nhà A');
  @override
  bool get isAdmin => false;
  @override
  String? get connectedServerUrl => null;
  @override
  bool get isDeletingBenchmarkResources => false;
  @override
  bool get isPreparingBenchmark => false;
  @override
  bool get isDownloadingOnnx => false;
  @override
  bool get isBenchmarking => false;
  @override
  bool get isModelLoading => false;
  @override
  Future<void> updateUser(User user) async => saved = user;
  @override
  Future<bool> register(User user) async {
    saved = user;
    return true;
  }
}

void main() {
  test(
    'phone normalization accepts only 9 to 11 digits and removes spaces',
    () {
      for (final value in ['', 'abc', '1', '12345678', '123456789012']) {
        expect(User.normalizePhone(value), isNull, reason: value);
      }
      for (final value in ['123456789', '1234567890', '12345678901']) {
        expect(User.normalizePhone(value), value);
      }
      expect(User.normalizePhone(' 0901 234 567 '), '0901234567');
    },
  );

  testWidgets('profile rejects invalid phone and saves normalized digits', (
    tester,
  ) async {
    final controller = _Controller();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: SettingsScreen(controller: controller)),
      ),
    );
    final edit = find.text('Chỉnh sửa thông tin');
    await tester.ensureVisible(edit);
    await tester.tap(edit);
    await tester.pumpAndSettle();
    final phone = find.byType(TextField).first;
    final save = find.text('Lưu thay đổi');
    for (final value in ['abc', '1']) {
      await tester.enterText(phone, value);
      await tester.ensureVisible(save);
      await tester.tap(save);
      await tester.pumpAndSettle();
      expect(
        find.text('Số điện thoại không hợp lệ (9-11 chữ số).'),
        findsOneWidget,
      );
      expect(controller.saved, isNull);
    }
    await tester.enterText(phone, ' 0901 234 567 ');
    await tester.ensureVisible(save);
    await tester.tap(save);
    await tester.pumpAndSettle();
    expect(controller.saved?.phone, '0901234567');
    expect(controller.saved?.address, 'Nhà A');
    expect(find.text('Lưu thay đổi'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('registration uses the same phone validation and normalization', (
    tester,
  ) async {
    final controller = _Controller();
    await tester.pumpWidget(
      MaterialApp(
        home: RegisterScreen(
          controller: controller,
          onGoLogin: () {},
          onRegisterSuccess: () {},
        ),
      ),
    );
    final fields = find.byType(TextField);
    await tester.enterText(fields.at(0), 'user');
    await tester.enterText(fields.at(1), 'password');
    await tester.enterText(fields.at(2), 'password');
    await tester.enterText(fields.at(4), 'Nhà A');
    final create = find.widgetWithText(ElevatedButton, 'Tạo tài khoản');
    for (final value in ['abc', '1']) {
      await tester.enterText(fields.at(3), value);
      await tester.ensureVisible(create);
      await tester.tap(create);
      await tester.pump();
      expect(
        find.text('Số điện thoại không hợp lệ (9-11 chữ số).'),
        findsOneWidget,
      );
      expect(controller.saved, isNull);
    }
    await tester.enterText(fields.at(3), ' 0901 234 567 ');
    await tester.ensureVisible(create);
    await tester.tap(create);
    await tester.pump();
    expect(controller.saved?.phone, '0901234567');
    expect(tester.takeException(), isNull);
  });
}
