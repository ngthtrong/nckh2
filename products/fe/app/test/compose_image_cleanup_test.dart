import 'dart:io';

import 'package:app/core/platform/local_file_io.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();
  const pathChannel = MethodChannel('plugins.flutter.io/path_provider');
  late Directory dir;
  late Directory attachments;

  Future<File> write(String name) async =>
      File('${attachments.path}/$name').writeAsBytes([1, 2, 3]);

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('compose_cleanup_test');
    attachments = await Directory(
      '${dir.path}/documents/rescue_attachments',
    ).create(recursive: true);
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      pathChannel,
      (_) async => '${dir.path}/documents',
    );
  });

  tearDown(() async {
    binding.defaultBinaryMessenger.setMockMethodCallHandler(pathChannel, null);
    await dir.delete(recursive: true);
  });

  test('sweep deletes only unreferenced generated compose files', () async {
    final orphan = await write('compose-image-1-abcdef012345');
    final kept = await write('compose-image-2-abcdef012345');
    final report = await write('post-3-abcdef012345');
    final unrelated = await write('compose-image-not-generated.jpg');
    final external = await File(
      '${dir.path}/compose-image-4-abcdef012345',
    ).writeAsBytes([4]);
    final nested = await Directory('${attachments.path}/nested').create();
    final nestedPhoto = await File(
      '${nested.path}/compose-image-5-abcdef012345',
    ).writeAsBytes([5]);

    await cleanupComposeImages(keepPaths: [kept.path]);

    expect(await orphan.exists(), isFalse);
    for (final file in [kept, report, unrelated, external, nestedPhoto]) {
      expect(await file.exists(), isTrue, reason: file.path);
    }
  });

  test('discard targets one generated compose file only', () async {
    final discarded = await write('compose-image-1-abcdef012345');
    final other = await write('compose-image-2-abcdef012345');
    final report = await write('post-3-abcdef012345');
    final external = await File(
      '${dir.path}/compose-image-4-abcdef012345',
    ).writeAsBytes([4]);

    await cleanupComposeImages(keepPaths: [], onlyPath: discarded.path);
    await cleanupComposeImages(keepPaths: [], onlyPath: report.path);
    await cleanupComposeImages(keepPaths: [], onlyPath: external.path);

    expect(await discarded.exists(), isFalse);
    for (final file in [other, report, external]) {
      expect(await file.exists(), isTrue, reason: file.path);
    }
  });

  test('discard preserves a referenced compose file', () async {
    final kept = await write('compose-image-1-abcdef012345');

    await cleanupComposeImages(keepPaths: [kept.path], onlyPath: kept.path);

    expect(await kept.exists(), isTrue);
  });

  test('sweep does not follow a generated compose symlink', () async {
    final external = await File('${dir.path}/external.jpg').writeAsBytes([9]);
    final link = Link('${attachments.path}/compose-image-1-abcdef012345');
    try {
      await link.create(external.path);
    } on FileSystemException {
      markTestSkipped('Creating symlinks is unavailable on this host.');
      return;
    }

    await cleanupComposeImages(keepPaths: []);

    expect(await external.readAsBytes(), [9]);
    expect(await link.exists(), isTrue);
  });

  test('sweep does not follow a symlinked attachment directory', () async {
    final external = await Directory('${dir.path}/external').create();
    final photo = await File(
      '${external.path}/compose-image-1-abcdef012345',
    ).writeAsBytes([9]);
    await attachments.delete();
    final link = Link(attachments.path);
    try {
      await link.create(external.path);
    } on FileSystemException {
      markTestSkipped('Creating symlinks is unavailable on this host.');
      return;
    }

    await cleanupComposeImages(keepPaths: []);

    expect(await photo.readAsBytes(), [9]);
    expect(await link.exists(), isTrue);
  });
}
