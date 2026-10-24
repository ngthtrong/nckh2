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

/// Only generated compose copies in the app's attachment directory are disposable.
Future<void> cleanupComposeImages({
  required Iterable<String> keepPaths,
  String? onlyPath,
}) async {
  final documents = await getApplicationDocumentsDirectory();
  final directory = Directory('${documents.path}/rescue_attachments');
  if (await FileSystemEntity.type(directory.path, followLinks: false) !=
      FileSystemEntityType.directory) {
    return;
  }
  String key(String path) {
    final uri = File(path).absolute.uri.normalizePath().toString();
    return Platform.isWindows ? uri.toLowerCase() : uri;
  }

  final keep = keepPaths.map(key).toSet();
  final target = onlyPath == null ? null : key(onlyPath);
  final ownedName = RegExp(r'^compose-image-[0-9]+-[a-f0-9]{12}$');
  await for (final entry in directory.list(followLinks: false)) {
    if (entry is! File || !ownedName.hasMatch(entry.uri.pathSegments.last)) {
      continue;
    }
    final path = key(entry.path);
    if ((target != null && path != target) || keep.contains(path)) continue;
    await entry.delete();
  }
}
