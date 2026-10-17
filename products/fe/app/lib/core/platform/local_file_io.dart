import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/widgets.dart';
import 'package:path_provider/path_provider.dart';

ImageProvider<Object> localImageProvider(String path) => FileImage(File(path));

bool localFileExists(String path) => File(path).existsSync();

Future<Uint8List> readLocalFile(String path) => File(path).readAsBytes();

/// Picker paths can disappear when the OS clears its cache.
Future<String> preserveLocalFile(String path, String name) async {
  final bytes = await readLocalFile(path);
  if (bytes.isEmpty) throw StateError('Ảnh đã chọn trống. Vui lòng chọn lại.');
  final documents = await getApplicationDocumentsDirectory();
  final directory = await Directory(
    '${documents.path}/rescue_attachments',
  ).create(recursive: true);
  final saved = File('${directory.path}/$name');
  await saved.writeAsBytes(bytes, flush: true);
  return saved.path;
}
