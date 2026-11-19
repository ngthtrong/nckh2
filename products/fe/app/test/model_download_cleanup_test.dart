import 'dart:io';

import 'package:app/data/datasources/admin_model_download_native.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  late Directory root;
  final currentHash = List.filled(64, 'a').join();
  final oldHash = List.filled(64, 'b').join();

  setUp(() async {
    root = await Directory.systemTemp.createTemp('model-cleanup-');
    await Directory('${root.path}/admin_models').create();
  });
  tearDown(() async => root.delete(recursive: true));

  Future<File> write(String name, int length) =>
      File('${root.path}/$name').writeAsBytes(List.filled(length, 1));

  test('Startup removes only old ONNX and interrupted downloads', () async {
    final pte = await write('model.pte', 10);
    final current = await write('admin_models/$currentHash.onnx', 11);
    await write('model.onnx', 12);
    await write('model.onnx.version', 2);
    await write('model.onnx.tmp', 3);
    await write('admin_models/$oldHash.onnx', 13);
    await write('admin_models/$currentHash.onnx.part', 4);
    final benchmark = await write('benchmark.rhb', 14);
    final unknown = await write('admin_models/notes.txt', 15);
    final profile = await write('user_profile.hive', 16);
    final report = await write('benchmark_result.json', 17);

    expect(
      await pruneModelDownloads(directory: root, keepOnnxSha256: currentHash),
      34,
    );
    for (final file in [pte, current, benchmark, unknown, profile, report]) {
      expect(await file.exists(), isTrue, reason: file.path);
    }
    expect(await File('${root.path}/model.onnx').exists(), isFalse);
    expect(
      await File('${root.path}/admin_models/$oldHash.onnx').exists(),
      isFalse,
    );
    expect(
      await pruneModelDownloads(directory: root, keepOnnxSha256: currentHash),
      0,
    );
  });

  test(
    'Manual cleanup frees benchmark and ONNX while preserving PTE and reports',
    () async {
      await write('admin_models/$currentHash.onnx', 11);
      await write('benchmark.rhb', 12);
      await write('benchmark.rhb.part', 3);
      final pte = await write('model.pte', 14);
      final report = await write('benchmark_result.json', 15);
      final records = await write('records.hive', 16);
      expect(
        await pruneModelDownloads(directory: root, deleteBenchmark: true),
        26,
      );
      expect(await pte.exists(), isTrue);
      expect(await report.exists(), isTrue);
      expect(await records.exists(), isTrue);
      expect(await File('${root.path}/benchmark.rhb').exists(), isFalse);
      expect(
        await pruneModelDownloads(directory: root, deleteBenchmark: true),
        0,
      );
    },
  );

  test('Invalid hash is rejected before touching stored models', () async {
    final legacy = await write('model.onnx', 12);
    await expectLater(
      pruneModelDownloads(directory: root, keepOnnxSha256: '../outside'),
      throwsFormatException,
    );
    expect(await legacy.exists(), isTrue);
  });
}
