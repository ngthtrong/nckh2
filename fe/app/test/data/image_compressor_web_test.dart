import 'dart:typed_data';

import 'package:app/data/datasources/image/image_compressor_web.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as image;

void main() {
  test(
    'web compressor returns a real JPEG no wider than 1280 pixels',
    () async {
      final source = image.Image(width: 1600, height: 20);
      final sourceBytes = Uint8List.fromList(image.encodePng(source));

      final compressed = await WebImageCompressor().compress(sourceBytes);
      final decoded = image.decodeImage(compressed.bytes);

      expect(decoded, isNotNull);
      expect(decoded!.width, 1280);
      expect(compressed.mimeType, 'image/jpeg');
      expect(compressed.fileName, endsWith('.jpg'));
    },
  );
}
