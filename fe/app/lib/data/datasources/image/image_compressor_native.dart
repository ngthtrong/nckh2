import 'dart:typed_data';

import 'package:flutter_image_compress/flutter_image_compress.dart';

import '../../../domain/entities/rescue_image.dart';
import 'image_compressor.dart';

ImageCompressor createImageCompressor() => NativeImageCompressor();

class NativeImageCompressor implements ImageCompressor {
  @override
  Future<RescueImage> compress(Uint8List source) async {
    final bytes = await FlutterImageCompress.compressWithList(
      source,
      minWidth: 1280,
      minHeight: 1280,
      quality: 72,
      format: CompressFormat.jpeg,
    );
    if (bytes.isEmpty) {
      throw const FormatException('Không thể nén ảnh trên thiết bị.');
    }
    return RescueImage(
      bytes: bytes,
      fileName: 'rescue-compressed.jpg',
      mimeType: 'image/jpeg',
    );
  }
}
