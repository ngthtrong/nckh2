import 'dart:typed_data';

import 'package:app/domain/entities/rescue_image.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('RescueImage preserves bytes and metadata through Hive map', () {
    final image = RescueImage(
      bytes: Uint8List.fromList([1, 2, 3]),
      fileName: 'scene.jpg',
      mimeType: 'image/jpeg',
    );

    final restored = RescueImage.fromMap(image.toMap());

    expect(restored.bytes, image.bytes);
    expect(restored.fileName, 'scene.jpg');
    expect(restored.mimeType, 'image/jpeg');
  });
}
