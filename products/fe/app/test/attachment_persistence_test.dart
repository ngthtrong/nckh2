import 'dart:io';

import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/core/platform/local_file_web.dart' as web;
import 'package:app/domain/entities/send_mode.dart';
import 'package:app/domain/repositories/rescue_repository.dart';
import 'package:app/domain/usecases/submit_rescue_post_usecase.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

class _Repository implements RescueRepository {
  final saved = <RescueRecord>[];

  @override
  Future<void> saveRecord(RescueRecord record) async => saved.add(record);
  @override
  Future<RescueRecord> sendRecord(RescueRecord record) async => record;
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('plugins.flutter.io/path_provider');
  late Directory dir;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('attachment_test');
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      channel,
      (_) async => '${dir.path}/documents',
    );
  });
  tearDown(() async {
    binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, null);
    await dir.delete(recursive: true);
  });

  test('queued post survives deletion of the picker temporary image', () async {
    final image = File('${dir.path}/picker.jpg');
    await image.writeAsBytes([0xFF, 0xD8, 0xFF, 42]);
    final repo = _Repository();
    final record = await SubmitRescuePostUseCase(repo)(
      lat: null,
      lng: null,
      imagePath: image.path,
      images: [image.path],
      sendMode: SendMode.queuedOffline,
    );
    await image.delete();
    expect(await File(record.imagePath!).readAsBytes(), [0xFF, 0xD8, 0xFF, 42]);
    expect(record.images, [record.imagePath]);
    expect(repo.saved.single.imagePath, record.imagePath);
  });

  test('missing or empty picker image fails before saving a report', () async {
    final image = File('${dir.path}/empty.jpg');
    final repo = _Repository();
    for (var i = 0; i < 2; i++) {
      await expectLater(
        SubmitRescuePostUseCase(repo)(
          lat: null,
          lng: null,
          imagePath: image.path,
          sendMode: SendMode.queuedOffline,
        ),
        throwsA(anything),
      );
      await image.writeAsBytes([]);
    }
    expect(repo.saved, isEmpty);
  });

  test(
    'web attachment data survives expired picker URLs without dart:io',
    () async {
      final path = await web.preserveLocalFile(
        'data:image/jpeg;base64,/9j/Kg==',
        'report',
      );
      expect(await web.readLocalFile(path), [0xFF, 0xD8, 0xFF, 42]);
      await expectLater(
        web.preserveLocalFile('data:image/jpeg;base64,', 'empty'),
        throwsStateError,
      );
    },
  );
}
