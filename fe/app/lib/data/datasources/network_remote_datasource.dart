import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';

import '../../config.dart';

class NetworkRemoteDataSource {
  final Connectivity _connectivity = Connectivity();
  final Dio _probeDio;

  NetworkRemoteDataSource({Dio? probeDio})
    : _probeDio =
          probeDio ??
          Dio(
            BaseOptions(
              connectTimeout: const Duration(seconds: 5),
              receiveTimeout: const Duration(seconds: 10),
              responseType: ResponseType.bytes,
            ),
          );

  Stream<List<ConnectivityResult>> get changes =>
      _connectivity.onConnectivityChanged;

  Future<String> currentTypeName() async {
    final results = await _connectivity.checkConnectivity();
    return typeName(results);
  }

  String typeName(List<ConnectivityResult> results) {
    if (results.contains(ConnectivityResult.wifi)) return 'WiFi';
    if (results.contains(ConnectivityResult.mobile)) return '4G/5G';
    if (results.contains(ConnectivityResult.ethernet)) return 'Ethernet';
    return 'none';
  }

  /// Tải `GET /probe` (64 KB) trong tối đa [budget] và trả throughput theo
  /// kilobit/giây. Mạng quá chậm để tải hết trong [budget] vẫn được đo từ phần
  /// đã nhận (để chọn "chỉ text"); null khi không nhận được byte nào.
  Future<int?> probeThroughputKbps({
    Duration budget = const Duration(seconds: 6),
  }) async {
    final cancel = CancelToken();
    final timer = Timer(budget, () => cancel.cancel('probe budget'));
    final stopwatch = Stopwatch()..start();
    var received = 0;
    try {
      final response = await _probeDio.get<List<int>>(
        kProbeUrl,
        queryParameters: {'t': DateTime.now().millisecondsSinceEpoch},
        cancelToken: cancel,
        onReceiveProgress: (count, _) => received = count,
      );
      received = response.data?.length ?? received;
    } catch (_) {
      // Hết thời gian hoặc lỗi giữa chừng: dùng phần đã nhận nếu có.
    } finally {
      timer.cancel();
      stopwatch.stop();
    }
    if (received == 0) return null;
    final ms = stopwatch.elapsedMilliseconds < 1
        ? 1
        : stopwatch.elapsedMilliseconds;
    return (received * 8 / ms).round(); // bit/ms = kbit/s
  }
}
