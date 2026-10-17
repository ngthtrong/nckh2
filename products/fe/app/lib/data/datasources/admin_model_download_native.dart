import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';

import '../../config.dart';

Future<int> pruneModelDownloads({
  String? keepOnnxSha256,
  bool deleteBenchmark = false,
  Directory? directory,
}) async {
  if (keepOnnxSha256 != null &&
      !RegExp(r'^[a-f0-9]{64}$').hasMatch(keepOnnxSha256)) {
    throw const FormatException('SHA-256 model không hợp lệ.');
  }
  final root = directory ?? await getApplicationSupportDirectory();
  var removedBytes = 0;
  Future<void> removeFile(File file) async {
    // Only regular files owned by this feature; never follow a link outside app storage.
    if (await FileSystemEntity.type(file.path, followLinks: false) !=
        FileSystemEntityType.file) {
      return;
    }
    final size = await file.length();
    await file.delete();
    removedBytes += size;
  }

  for (final name in [
    'model.onnx',
    'model.onnx.version',
    'model.onnx.tmp',
    'model.onnx.part',
  ]) {
    await removeFile(File('${root.path}/$name'));
  }
  final folder = Directory('${root.path}/admin_models');
  if (await FileSystemEntity.type(folder.path, followLinks: false) ==
      FileSystemEntityType.directory) {
    await for (final entry in folder.list(followLinks: false)) {
      final name = entry.uri.pathSegments.last;
      if (entry is File &&
          RegExp(r'^[a-f0-9]{64}\.onnx(?:\.part)?$').hasMatch(name) &&
          name != '$keepOnnxSha256.onnx') {
        await removeFile(entry);
      }
    }
  }
  if (deleteBenchmark) {
    for (final name in ['benchmark.rhb', 'benchmark.rhb.part']) {
      await removeFile(File('${root.path}/$name'));
    }
  }
  return removedBytes;
}

Future<String> downloadAdminOnnx({
  required String server,
  required String token,
  required CancelToken cancelToken,
  required void Function(int, int) onProgress,
  Dio? client,
  Directory? directory,
  Map<String, dynamic>? bundledManifest,
}) async {
  requireAllowedServerUrl(server);
  final dio =
      client ??
      Dio(
        BaseOptions(
          connectTimeout: const Duration(seconds: 8),
          receiveTimeout: const Duration(seconds: 60),
          followRedirects: false,
        ),
      );
  File? partial;
  try {
    final expected =
        bundledManifest ??
        jsonDecode(
              await rootBundle.loadString('assets/models/model_manifest.json'),
            )
            as Map<String, dynamic>;
    final options = Options(
      headers: {'Authorization': 'Bearer $token'},
      followRedirects: false,
    );
    final response = await dio.get<dynamic>(
      '$server/api/admin/models',
      options: options,
      cancelToken: cancelToken,
    );
    final catalog = response.data as Map;
    final manifest = catalog['manifest'] as Map;
    final info = (catalog['artifacts'] as Map)['onnx'] as Map;
    final hash = expected['onnx_sha256'];
    final bytes = info['bytes'];
    // Pair the downloaded ONNX with the PTE shipped in this APK.
    if (hash is! String ||
        !RegExp(r'^[a-f0-9]{64}$').hasMatch(hash) ||
        manifest['onnx_sha256'] != hash ||
        info['sha256'] != hash ||
        manifest['pte_sha256'] != expected['pte_sha256'] ||
        bytes is! int ||
        bytes <= 0) {
      throw const FormatException(
        'ONNX trên server không khớp PTE của ứng dụng.',
      );
    }
    final root = directory ?? await getApplicationSupportDirectory();
    final folder = Directory('${root.path}/admin_models');
    await folder.create(recursive: true);
    final target = File('${folder.path}/$hash.onnx');
    Future<bool> valid(File file) async =>
        await file.exists() &&
        await file.length() == bytes &&
        (await sha256.bind(file.openRead()).first).toString() == hash;
    if (await valid(target)) return target.path;
    partial = File('${target.path}.part');
    await dio.download(
      '$server/api/admin/models/onnx',
      partial.path,
      options: options,
      cancelToken: cancelToken,
      onReceiveProgress: (received, total) {
        if (received > bytes) {
          cancelToken.cancel('Model vượt kích thước khai báo.');
        }
        onProgress(received, bytes);
      },
    );
    if (!await valid(partial)) {
      throw const FormatException('File ONNX thiếu dữ liệu hoặc sai SHA-256.');
    }
    if (cancelToken.isCancelled) {
      throw cancelToken.cancelError!;
    }
    await partial.rename(target.path);
    partial = null;
    return target.path;
  } finally {
    if (partial != null && await partial.exists()) await partial.delete();
    if (client == null) dio.close(force: true);
  }
}
