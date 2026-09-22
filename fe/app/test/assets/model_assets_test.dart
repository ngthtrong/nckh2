import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('bundles the ONNX, PTE and manifest assets', () async {
    for (final path in const [
      'assets/models/model.onnx',
      'assets/models/model.pte',
      'assets/models/model_manifest.json',
    ]) {
      final data = await rootBundle.load(path);
      expect(data.lengthInBytes, greaterThan(0), reason: path);
    }

    final manifest =
        jsonDecode(
              await rootBundle.loadString('assets/models/model_manifest.json'),
            )
            as Map<String, dynamic>;
    expect(manifest['input_size'], 224);
    expect(manifest['class_order'], ['low', 'medium', 'high', 'non_flood']);
  });
}
