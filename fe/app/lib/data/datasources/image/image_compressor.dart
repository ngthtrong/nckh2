import 'dart:typed_data';

import '../../../domain/entities/rescue_image.dart';

abstract interface class ImageCompressor {
  Future<RescueImage> compress(Uint8List source);
}
