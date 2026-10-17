import 'package:dio/dio.dart';

Future<int> pruneModelDownloads({
  String? keepOnnxSha256,
  bool deleteBenchmark = false,
}) async => 0;

Future<String> downloadAdminOnnx({
  required String server,
  required String token,
  required CancelToken cancelToken,
  required void Function(int, int) onProgress,
}) async {
  throw UnsupportedError('Web không chạy model on-device.');
}
