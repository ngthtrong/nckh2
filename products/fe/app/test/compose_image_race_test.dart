import 'dart:async';
import 'dart:io';

import 'package:app/domain/entities/ai_tag.dart';
import 'package:app/domain/entities/ai_model_type.dart';
import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:app/presentation/screens/compose/compose_screen.dart';
import 'package:app/presentation/screens/main_navigation_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image_picker/image_picker.dart';

class Controller extends Fake implements AppController {
  @override
  void addListener(VoidCallback listener) {}
  @override
  void removeListener(VoidCallback listener) {}
  final analyses = <Completer<List<AiTag>>>[];
  Completer<String?>? picking;
  String? error;
  Completer<RescueRecord?>? submission;
  int submissions = 0;
  Map<String, dynamic>? savedDraft;
  Completer<void>? clearing;
  final discardedPaths = <String>[];
  @override
  Future<void> init() async {}
  bool authenticated = true;
  @override
  bool get isAuthenticated => authenticated;
  @override
  void continueAsGuest() {
    authenticated = true;
  }

  @override
  Map<String, dynamic>? get composeDraft => savedDraft;
  @override
  Future<void> saveComposeDraft(Map<String, dynamic> draft) async =>
      savedDraft = draft;
  @override
  Future<void> clearComposeDraft() async {
    if (clearing != null) await clearing!.future;
    savedDraft = null;
  }

  @override
  Future<void> discardComposeImage(String? path) async {
    if (path != null) discardedPaths.add(path);
  }

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

  List<String> photos() {
    final dir = Directory.systemTemp.createTempSync('compose_widget_images');
    addTearDown(() => dir.delete(recursive: true));
    final source = File('assets/images/app_logo.webp');
    return [
      source.copySync('${dir.path}/first.webp').path,
      source.copySync('${dir.path}/second.webp').path,
    ];
  }

  testWidgets(
    'form is saved before picker opens and restored after recreation',
    (tester) async {
      final controller = Controller()..picking = Completer<String?>();
      await show(tester, controller);
      await tester.enterText(find.byType(TextField).last, 'Cần xuồng ngay');
      await tester.ensureVisible(
        find.widgetWithIcon(IconButton, Icons.add).first,
      );
      await tester.tap(find.widgetWithIcon(IconButton, Icons.add).first);
      await tester.pump();
      await pick(tester);
      expect(controller.savedDraft!['description'], 'Cần xuồng ngay');
      expect(controller.savedDraft!['trappedCount'], 1);
      await tester.pumpWidget(const SizedBox());
      final restarted = Controller()..savedDraft = controller.savedDraft;
      await show(tester, restarted);
      expect(
        tester.widget<TextField>(find.byType(TextField).last).controller!.text,
        'Cần xuồng ngay',
      );
      expect(
        tester.widget<TextField>(find.byType(TextField).first).controller!.text,
        '1',
      );
      controller.picking!.complete(null);
      await tester.pump();
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('startup opens the recovered draft form', (tester) async {
    final controller = Controller()
      ..savedDraft = {'description': 'Bản nháp đã lưu'};
    await tester.pumpWidget(
      MaterialApp(home: MainNavigationScreen(controller: controller)),
    );
    await tester.pump();
    expect(find.byType(ComposeScreen), findsOneWidget);
    expect(
      tester.widget<TextField>(find.byType(TextField).last).controller!.text,
      'Bản nháp đã lưu',
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('guest entry after restart still opens the recovered draft', (
    tester,
  ) async {
    final controller = Controller()
      ..authenticated = false
      ..savedDraft = {'description': 'Bản nháp của khách'};
    await tester.pumpWidget(
      MaterialApp(home: MainNavigationScreen(controller: controller)),
    );
    await tester.pump();
    final guest = find.textContaining('Bỏ qua');
    await tester.ensureVisible(guest);
    await tester.tap(guest);
    await tester.pump();
    expect(find.byType(ComposeScreen), findsOneWidget);
    expect(
      tester.widget<TextField>(find.byType(TextField).last).controller!.text,
      'Bản nháp của khách',
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('picker blocks form back until the picker is cancelled', (
    tester,
  ) async {
    var backs = 0;
    final controller = Controller()..picking = Completer<String?>();
    await show(tester, controller, onBack: () => backs++);
    await tester.enterText(find.byType(TextField).last, 'Giữ bản nháp');
    await pick(tester);
    final close = find.widgetWithIcon(IconButton, Icons.close);
    expect(tester.widget<IconButton>(close).onPressed, isNull);
    await tester.binding.handlePopRoute();
    expect(backs, 0);
    controller.picking!.complete(null);
    await tester.pump();
    expect(tester.widget<IconButton>(close).onPressed, isNotNull);
    expect(controller.savedDraft, isNull);
    expect(
      tester.widget<TextField>(find.byType(TextField).last).controller!.text,
      'Giữ bản nháp',
    );
  });

  testWidgets(
    'submit waits for snapshot deletion before persisting the report',
    (tester) async {
      final controller = Controller()
        ..savedDraft = {'description': 'Cần cứu hộ'}
        ..submission = Completer<RescueRecord?>()
        ..clearing = Completer<void>();
      await show(tester, controller);
      await tester.tap(find.text('Gửi ngay'));
      await tester.pump();
      expect(controller.submissions, 0);
      controller.clearing!.complete();
      await tester.pump();
      expect(controller.savedDraft, isNull);
      expect(controller.submissions, 1);
      controller.submission!.complete(
        RescueRecord(
          id: 'post-saved',
          sendMode: 'queuedOffline',
          createdAt: DateTime(2026),
          lat: null,
          lng: null,
        ),
      );
      await tester.pump();
      expect(
        tester
            .widget<ElevatedButton>(find.byType(ElevatedButton).first)
            .onPressed,
        isNull,
      );
      await tester.pump();
      expect(controller.savedDraft, isNull);
      expect(controller.submissions, 1);
    },
  );

  testWidgets('restored photo is displayed and analyzed with the saved form', (
    tester,
  ) async {
    final path = File('assets/images/app_logo.webp').absolute.path;
    final controller = Controller()
      ..savedDraft = {
        'description': 'Cần cứu hộ',
        'imagePath': path,
        'cannotMove': true,
        'severeSigns': ['heavy_bleeding'],
      };
    await show(tester, controller);
    await tester.pump();
    expect(controller.analyses, hasLength(1));
    expect(find.byType(Image), findsOneWidget);
    expect(
      tester.widget<TextField>(find.byType(TextField).last).controller!.text,
      'Cần cứu hộ',
    );
    controller.analyses.single.complete([
      const AiTag(label: 'RESTORED', confidence: 0.9),
    ]);
    await tester.pump();
    expect(find.text('RESTORED'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

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
    expect(backs, 1);
    expect(tester.takeException(), isNull);
  });

  testWidgets('closing a recovered form discards its snapshot', (tester) async {
    var backs = 0;
    final controller = Controller()
      ..savedDraft = {'description': 'Recovered camera form'};
    await show(tester, controller, onBack: () => backs++);
    await tester.tap(find.widgetWithIcon(IconButton, Icons.close));
    await tester.pump();
    expect(controller.savedDraft, isNull);
    expect(backs, 1);
  });

  testWidgets('pending submit locks input and restores editing on failure', (
    tester,
  ) async {
    final controller = Controller()..submission = Completer<RescueRecord?>();
    await show(tester, controller);
    final description = find.byType(TextField).last;
    await tester.enterText(description, 'Cần cứu hộ');
    await tester.pump();
    await tester.tap(find.text('Gửi ngay'));
    await tester.pump();

    final addPerson = find.widgetWithIcon(IconButton, Icons.add).first;
    await tester.ensureVisible(addPerson);
    await tester.tap(addPerson, warnIfMissed: false);
    await tester.pump();
    expect(
      tester.widget<TextField>(find.byType(TextField).first).controller!.text,
      '0',
    );

    final gallery = find.text('Chọn từ máy');
    await tester.ensureVisible(gallery);
    await tester.tap(gallery, warnIfMissed: false);
    await tester.pump();
    expect(controller.analyses, isEmpty);
    final editor = tester.widget<EditableText>(find.byType(EditableText).last);
    editor.focusNode.requestFocus();
    await tester.pump();
    expect(editor.focusNode.hasFocus, isFalse);

    controller.submission!.complete(null);
    await tester.pump();
    await tester.enterText(description, 'Cần xuồng');
    expect(tester.widget<TextField>(description).controller!.text, 'Cần xuồng');
    await tester.ensureVisible(addPerson);
    await tester.tap(addPerson);
    await tester.pump();
    expect(
      tester.widget<TextField>(find.byType(TextField).first).controller!.text,
      '1',
    );
    expect(controller.submissions, 1);
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
          .widget<ElevatedButton>(find.byType(ElevatedButton).first)
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

  testWidgets(
    'replacing a photo discards the prior compose copy after picking',
    (tester) async {
      final paths = photos();
      final controller = Controller()
        ..savedDraft = {'imagePath': paths[0]}
        ..picking = Completer<String?>();
      await show(tester, controller);
      await pick(tester);
      expect(controller.discardedPaths, isEmpty);

      controller.picking!.complete(paths[1]);
      await tester.pump();

      expect(controller.discardedPaths, [paths[0]]);
      expect(controller.savedDraft, isNull);
      expect(controller.analyses, hasLength(2));
      expect(tester.takeException(), isNull);
    },
  );

  for (final fails in [false, true]) {
    testWidgets(
      'picker ${fails ? 'failure' : 'cancellation'} keeps the prior photo',
      (tester) async {
        final paths = photos();
        final controller = Controller()
          ..savedDraft = {'imagePath': paths[0]}
          ..picking = Completer<String?>();
        await show(tester, controller);
        await pick(tester);
        if (fails) {
          controller.picking!.completeError(StateError('picker failed'));
        } else {
          controller.picking!.complete(null);
        }
        await tester.pump();

        expect(controller.discardedPaths, isEmpty);
        expect(controller.analyses, hasLength(1));
        expect(find.byType(Image), findsOneWidget);
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets('removing a photo clears its snapshot before discarding it', (
    tester,
  ) async {
    final paths = photos();
    final controller = Controller()
      ..savedDraft = {'imagePath': paths[0]}
      ..clearing = Completer<void>();
    await show(tester, controller);
    final remove = find.byIcon(Icons.close).last;
    await tester.ensureVisible(remove);
    await tester.tap(remove);
    await tester.pump();
    expect(controller.discardedPaths, isEmpty);

    controller.clearing!.complete();
    await tester.pump();

    expect(controller.savedDraft, isNull);
    expect(controller.discardedPaths, [paths[0]]);
    expect(find.byType(Image), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('leaving a recovered form discards its photo', (tester) async {
    final paths = photos();
    var backs = 0;
    final controller = Controller()..savedDraft = {'imagePath': paths[0]};
    await show(tester, controller, onBack: () => backs++);

    await tester.tap(find.widgetWithIcon(IconButton, Icons.close));
    await tester.pump();

    expect(controller.savedDraft, isNull);
    expect(controller.discardedPaths, [paths[0]]);
    expect(backs, 1);
  });

  testWidgets('disposing an idle form discards its current photo', (
    tester,
  ) async {
    final paths = photos();
    final controller = Controller()
      ..savedDraft = {'imagePath': paths[0]}
      ..clearing = Completer<void>();
    await show(tester, controller);

    await tester.pumpWidget(const SizedBox());
    await tester.pump();
    expect(controller.savedDraft!['imagePath'], paths[0]);
    expect(controller.discardedPaths, isEmpty);

    controller.clearing!.complete();
    await tester.pump();

    expect(controller.savedDraft, isNull);
    expect(controller.discardedPaths, [paths[0]]);
  });

  testWidgets('successful submit discards source photo after persistence', (
    tester,
  ) async {
    final paths = photos();
    final controller = Controller()
      ..savedDraft = {'imagePath': paths[0]}
      ..submission = Completer<RescueRecord?>();
    await show(tester, controller);
    await tester.tap(find.text('Gửi ngay'));
    await tester.pump();
    expect(controller.discardedPaths, isEmpty);

    controller.submission!.complete(
      RescueRecord(
        id: 'post-saved',
        sendMode: 'queuedOffline',
        createdAt: DateTime(2026),
        lat: null,
        lng: null,
        imagePath: paths[1],
      ),
    );
    await tester.pump();

    expect(controller.discardedPaths, [paths[0]]);
    expect(controller.savedDraft, isNull);
    expect(tester.takeException(), isNull);
  });

  testWidgets('failed submit keeps source photo for retry while form is open', (
    tester,
  ) async {
    final paths = photos();
    final controller = Controller()
      ..savedDraft = {'imagePath': paths[0]}
      ..submission = Completer<RescueRecord?>();
    await show(tester, controller);
    await tester.tap(find.text('Gửi ngay'));
    await tester.pump();
    controller.submission!.complete(null);
    await tester.pump();

    expect(controller.discardedPaths, isEmpty);
    expect(find.byType(Image), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'dispose defers photo cleanup until the pending submit finishes',
    (tester) async {
      final paths = photos();
      final controller = Controller()
        ..savedDraft = {'imagePath': paths[0]}
        ..submission = Completer<RescueRecord?>();
      await show(tester, controller);
      await tester.tap(find.text('Gửi ngay'));
      await tester.pump();
      await tester.pumpWidget(const SizedBox());
      expect(controller.discardedPaths, isEmpty);

      controller.submission!.complete(null);
      await tester.pump();

      expect(controller.discardedPaths, [paths[0]]);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('late picker result discards both photos after form disposal', (
    tester,
  ) async {
    final paths = photos();
    final controller = Controller()
      ..savedDraft = {'imagePath': paths[0]}
      ..picking = Completer<String?>();
    await show(tester, controller);
    await pick(tester);
    await tester.pumpWidget(const SizedBox());
    expect(controller.discardedPaths, isEmpty);

    controller.picking!.complete(paths[1]);
    await tester.pump();

    expect(controller.savedDraft, isNull);
    expect(controller.discardedPaths, unorderedEquals(paths));
    expect(controller.analyses, hasLength(1));
    expect(tester.takeException(), isNull);
  });
}
