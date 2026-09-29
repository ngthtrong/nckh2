import 'dart:io';
import 'dart:typed_data';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';

import '../config.dart';

/// Theo dõi trạng thái mạng + đo throughput 1 lần tại thời điểm gửi.
/// Event-driven (stream) — KHÔNG poll định kỳ để tiết kiệm pin.
class NetworkService {
  final Connectivity _conn = Connectivity();
  Dio? _probeDio;

  Stream<List<ConnectivityResult>> get changes => _conn.onConnectivityChanged;

  /// true nếu có data connection (wifi/mobile/ethernet).
  Future<bool> hasData() async {
    try {
      final r = await _conn.checkConnectivity();
      return r.any((e) =>
          e == ConnectivityResult.wifi ||
          e == ConnectivityResult.mobile ||
          e == ConnectivityResult.ethernet);
    } catch (_) {
      return false;
    }
  }

  String typeName(List<ConnectivityResult> results) {
    if (results.contains(ConnectivityResult.wifi)) return 'wifi';
    if (results.contains(ConnectivityResult.mobile)) return 'mobile';
    if (results.contains(ConnectivityResult.ethernet)) return 'ethernet';
    if (results.contains(ConnectivityResult.none)) return 'none';
    return 'unknown';
  }

  Future<String> currentTypeName() async {
    try {
      return typeName(await _conn.checkConnectivity());
    } catch (_) {
      return 'unknown';
    }
  }

  /// Probe throughput bằng cách tải file nhỏ từ server. Gọi MỘT lần duy nhất
  /// ngay trước khi gửi (không định kỳ — tiết kiệm pin + data).
  /// Trả về kbps; lỗi → 0 (bị coi là mạng yếu → chỉ gửi text: an toàn).
  Future<int> measureKbps() async {
    _probeDio ??= Dio(BaseOptions(
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 10),
      responseType: ResponseType.bytes,
    ));
    final sw = Stopwatch()..start();
    try {
      final resp = await _probeDio!.get<List<int>>(kProbeUrl);
      sw.stop();
      final kb = (resp.data?.length ?? 0) / 1024;
      final secs = sw.elapsedMilliseconds / 1000;
      return secs > 0 ? (kb / secs).round() : 0;
    } catch (_) {
      return 0;
    }
  }
}

/// Đọc bytes ảnh từ đường dẫn đã lưu (dùng khi sync lại bản ghi pending).
Future<Uint8List?> readImageBytes(String? path) async {
  if (path == null) return null;
  try {
    final f = File(path);
    if (!await f.exists()) return null;
    return await f.readAsBytes();
  } catch (_) {
    return null;
  }
}
