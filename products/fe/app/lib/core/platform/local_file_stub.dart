import 'dart:typed_data';

import 'package:flutter/widgets.dart';

ImageProvider<Object> localImageProvider(String path) => NetworkImage(path);

bool localFileExists(String path) => path.isNotEmpty;

Future<Uint8List> readLocalFile(String path) async {
  throw UnsupportedError('Local file access is unavailable on this platform.');
}
