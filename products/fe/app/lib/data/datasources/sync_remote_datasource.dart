import 'package:dio/dio.dart';

import '../../config.dart';
import '../models/sync_message_model.dart';

class SyncRemoteDataSource {
  final Dio _dio;

  SyncRemoteDataSource({Dio? dio})
    : _dio =
          dio ??
          Dio(
            BaseOptions(
              connectTimeout: const Duration(seconds: 10),
              sendTimeout: const Duration(seconds: 30),
              receiveTimeout: const Duration(seconds: 30),
            ),
          );

  Future<List<Map<String, dynamic>>> sendBatch(
    List<SyncMessageModel> messages,
  ) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '$kServerBaseUrl/sync/messages',
      data: {'messages': messages.map((m) => m.toRequestJson()).toList()},
      options: Options(headers: {'X-Message-Contract-Version': '1'}),
    );
    final results = response.data?['results'];
    if (results is! List) throw const FormatException('Response thiếu results');
    return results
        .map((item) => Map<String, dynamic>.from(item as Map))
        .toList();
  }

  /// Trạng thái điều phối hiện tại của các báo cáo (`GET /api/reports/status`).
  /// Id server không biết sẽ không có trong kết quả.
  Future<Map<String, String>> fetchStatuses(List<String> ids) async {
    if (ids.isEmpty) return {};
    final response = await _dio.get<Map<String, dynamic>>(
      '$kServerBaseUrl/api/reports/status',
      queryParameters: {'ids': ids.join(',')},
    );
    final reports = response.data?['reports'];
    if (reports is! List) throw const FormatException('Response thiếu reports');
    return {
      for (final item in reports.cast<Map>())
        item['id'] as String: item['status'] as String,
    };
  }
}
