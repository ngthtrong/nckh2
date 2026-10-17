import 'dart:typed_data';
import 'dart:convert';

import 'package:cross_file/cross_file.dart';
import 'package:flutter/widgets.dart';

ImageProvider<Object> localImageProvider(String path) => NetworkImage(path);

bool localFileExists(String path) => path.isNotEmpty;

Future<Uint8List> readLocalFile(String path) => path.startsWith('data:')
    ? Future.value(UriData.parse(path).contentAsBytes())
    : XFile(path).readAsBytes();

/// The data URI is stored in Hive with the report and survives blob URL expiry.
Future<String> preserveLocalFile(String path, String name) async {
  final bytes = await readLocalFile(path);
  if (bytes.isEmpty) throw StateError('Ảnh đã chọn trống. Vui lòng chọn lại.');
  return 'data:application/octet-stream;base64,${base64Encode(bytes)}';
}
