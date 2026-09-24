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
}
