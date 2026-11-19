import 'dart:convert';
import 'dart:io';

import 'package:app/data/datasources/inference_local_datasource_native.dart';
import 'package:crypto/crypto.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();
  const pathChannel = MethodChannel('plugins.flutter.io/path_provider');
  test(
    'corrupt PTE cache is repaired even when its version file is current',
    () async {
      final directory = await Directory.systemTemp.createTemp('pte-integrity-');
      binding.defaultBinaryMessenger.setMockMethodCallHandler(
        pathChannel,
        (_) async => directory.path,
      );
      addTearDown(() async {
        binding.defaultBinaryMessenger.setMockMethodCallHandler(
          pathChannel,
          null,
        );
        await directory.delete(recursive: true);
      });
      final manifest =
          jsonDecode(
                await rootBundle.loadString(
                  'assets/models/model_manifest.json',
                ),
              )
              as Map;
      final cached = File('${directory.path}/model.pte');
      await cached.writeAsBytes([1, 2, 3], flush: true);
      await File(
        '${cached.path}.version',
      ).writeAsString(manifest['version'] as String);
      await InferenceLocalDataSource().loadModel();
      expect(
        (await sha256.bind(cached.openRead()).first).toString(),
        manifest['pte_sha256'],
      );
      expect(await File('${cached.path}.tmp').exists(), isFalse);
    },
  );
}
