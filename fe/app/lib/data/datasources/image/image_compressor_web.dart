import 'dart:typed_data';

import 'package:image/image.dart' as image;

import '../../../domain/entities/rescue_image.dart';
import 'image_compressor.dart';

ImageCompressor createImageCompressor() => WebImageCompressor();

class WebImageCompressor implements ImageCompressor {
  @override
  Future<RescueImage> compress(Uint8List source) async {
    final decoded = image.decodeImage(source);
    if (decoded == null) {
      throw const FormatException('Không thể đọc ảnh để nén trên web.');
    }
    final resized = decoded.width > 1280
        ? image.copyResize(
            decoded,
            width: 1280,
            interpolation: image.Interpolation.linear,
          )
        : decoded;
    return RescueImage(
      bytes: Uint8List.fromList(image.encodeJpg(resized, quality: 72)),
      fileName: 'rescue-compressed.jpg',
      mimeType: 'image/jpeg',
    );
  }
}
