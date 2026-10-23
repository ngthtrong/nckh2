import 'dart:async';
import 'dart:io';

import 'package:app/domain/entities/ai_tag.dart';
import 'package:app/domain/entities/ai_model_type.dart';
import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:app/presentation/screens/compose/compose_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image_picker/image_picker.dart';

class Controller extends Fake implements AppController {
  final analyses = <Completer<List<AiTag>>>[];
  Completer<String?>? picking;
  String? error;
  Completer<RescueRecord?>? submission;
  int submissions = 0;
  @override
  String? get submissionError => error;
  @override
  Future<RescueRecord?> submitPost({
    required int trappedCount,
    required int injuredCount,
    required List<String> vulnerableGroups,
    required bool cannotMove,
    required List<String> severeSigns,
    required String description,
    required String? imagePath,
    required List<AiTag> aiTags,
  }) async {
    submissions++;
    if (submission != null) return submission!.future;
    return null;
  }

  @override
  String get locationLabel => 'GPS';
  @override
  ModelBenchmarkComparison? get latestComparison => null;
  @override
  Future<void> ensureModelLoaded() async {}
  @override
  Future<String?> pickImage({required ImageSource source}) async =>
      picking == null
      ? File('assets/images/app_logo.webp').absolute.path
      : picking!.future;
  @override
  Future<List<AiTag>> analyzeImage(String path) {
    final pending = Completer<List<AiTag>>();
    analyses.add(pending);
    return pending.future;
  }
}

void main() {
  Future<void> show(
    WidgetTester tester,
    Controller controller, {
    VoidCallback? onBack,
  }) => tester.pumpWidget(
    MaterialApp(
      home: ComposeScreen(
        controller: controller,
        onBack: onBack ?? () {},
        onSuccess: () {},
      ),
    ),
  );
  Future<void> pick(WidgetTester tester) async {
    final button = find.text('Chọn từ máy');
    await tester.ensureVisible(button);
    await tester.tap(button);
    await tester.pump();
  }

  testWidgets('pending submit blocks close and system back until failure', (
    tester,
  ) async {
    var backs = 0;
    final controller = Controller()
      ..submission = Completer<RescueRecord?>()
      ..error = 'Không lưu được ảnh đính kèm.';
    await show(tester, controller, onBack: () => backs++);
    final description = find.byType(TextField).last;
    await tester.enterText(description, 'Cần cứu hộ');
    await tester.pump();
    await tester.tap(find.text('Gửi ngay'));
    await tester.pump();
    final close = find.widgetWithIcon(IconButton, Icons.close);
    expect(tester.widget<IconButton>(close).onPressed, isNull);
    await tester.binding.handlePopRoute();
    await tester.pump();
    expect(backs, 0);
    expect(find.byType(ComposeScreen), findsOneWidget);

    controller.submission!.complete(null);
    await tester.pump();
    expect(find.text(controller.error!), findsOneWidget);
    expect(
      tester.widget<TextField>(description).controller!.text,
      'Cần cứu hộ',
    );
    expect(tester.widget<IconButton>(close).onPressed, isNotNull);
    await tester.tap(close);
    expect(backs, 1);
    await tester.binding.handlePopRoute();
    expect(backs, 2);
    expect(tester.takeException(), isNull);
  });

  testWidgets('finishing submit after form disposal is safe', (tester) async {
    final controller = Controller()..submission = Completer<RescueRecord?>();
    await show(tester, controller);
    await tester.enterText(find.byType(TextField).last, 'Cần cứu hộ');
    await tester.pump();
    await tester.tap(find.text('Gửi ngay'));
    await tester.pumpWidget(const SizedBox());
    controller.submission!.complete(null);
    await tester.pump();
    expect(tester.takeException(), isNull);
  });

  testWidgets('failed submission shows an error and keeps form input', (
    tester,
  ) async {
    final controller = Controller()
      ..error =
          'Không lưu được ảnh đính kèm. Hãy bỏ ảnh hoặc chọn lại ảnh rồi gửi lại.';
    await show(tester, controller);
    final description = find.byType(TextField).last;
    await tester.enterText(description, 'Cần cứu hộ');
    await tester.pump();
    await tester.tap(find.text('Gửi ngay'));
    await tester.pump();
    expect(find.text(controller.error!), findsOneWidget);
    expect(
      tester.widget<TextField>(description).controller!.text,
      'Cần cứu hộ',
    );
    expect(controller.submissions, 1);
  });

  testWidgets('description counts words and blocks more than 300', (
    tester,
  ) async {
    await show(tester, Controller());
    final description = find.byType(TextField).last;
    await tester.enterText(description, List.filled(300, 'a').join(' '));
    await tester.pump();
    expect(
      tester
          .widget<ElevatedButton>(
            find.widgetWithText(ElevatedButton, 'Gửi ngay'),
          )
          .onPressed,
      isNotNull,
    );
    expect(find.text('300/300 từ · 599/2000 ký tự'), findsOneWidget);
    await tester.enterText(description, List.filled(301, 'a').join(' '));
    await tester.pump();
    expect(find.text('Mô tả tối đa 300 từ.'), findsOneWidget);
    expect(
      tester
          .widget<ElevatedButton>(
            find.widgetWithText(ElevatedButton, 'Gửi ngay'),
          )
          .onPressed,
      isNull,
    );
    await tester.enterText(description, 'a' * 2001);
    await tester.pump();
    expect(tester.widget<TextField>(description).controller!.text.length, 2000);
    expect(
      tester
          .widget<ElevatedButton>(
            find.widgetWithText(ElevatedButton, 'Gửi ngay'),
          )
          .onPressed,
      isNotNull,
    );
  });

  testWidgets('late AI results cannot replace the newer image tags', (
    tester,
  ) async {
    final controller = Controller();
    await show(tester, controller);
    await pick(tester);
    await pick(tester);
    controller.analyses[1].complete([
      const AiTag(label: 'NEW', confidence: 0.9),
    ]);
    await tester.pump();
    controller.analyses[0].complete([
      const AiTag(label: 'OLD', confidence: 0.8),
    ]);
    await tester.pump();
    expect(find.text('NEW'), findsOneWidget);
    expect(find.text('OLD'), findsNothing);
    expect(tester.takeException(), isNull);
  });
  testWidgets('returning from image picker after leaving form is safe', (
    tester,
  ) async {
    final controller = Controller()..picking = Completer<String?>();
    await show(tester, controller);
    await pick(tester);
    await tester.pumpWidget(const SizedBox());
    controller.picking!.complete('unused');
    await tester.pump();
    expect(controller.analyses, isEmpty);
    expect(tester.takeException(), isNull);
  });
}
