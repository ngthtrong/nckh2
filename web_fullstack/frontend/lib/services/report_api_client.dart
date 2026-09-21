import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:image/image.dart' as image;

import '../domain/report.dart';
import 'send_mode_selector.dart';
import 'sync_coordinator.dart';

class ReportApiClient implements ReportUploader {
  ReportApiClient(String baseUrl) : _dio = Dio(BaseOptions(baseUrl: baseUrl));

  final Dio _dio;

  Future<Map<String, dynamic>> capabilities() async {
    final response = await _dio.get<Map<String, dynamic>>('/api/capabilities');
    return response.data ?? const {};
  }

  Future<double> measureBytesPerSecond() async {
    final stopwatch = Stopwatch()..start();
    final response = await _dio.get<List<int>>(
      '/probe',
      options: Options(responseType: ResponseType.bytes),
    );
    stopwatch.stop();
    final bytes = response.data?.length ?? 0;
    final seconds = stopwatch.elapsedMicroseconds / Duration.microsecondsPerSecond;
    return seconds <= 0 ? double.infinity : bytes / seconds;
  }

  @override
  Future<void> upload(RescueReport report) async {
    double throughput = 0;
    try {
      throughput = await measureBytesPerSecond();
    } catch (_) {
      rethrow;
    }
    final mode = selectSendMode(
      bytesPerSecond: throughput,
      hasImage: report.imageBytes != null,
    );
    Uint8List? uploadBytes;
    String? uploadName;
    String? uploadType;
    if (mode == SendMode.original) {
      uploadBytes = report.imageBytes;
      uploadName = report.imageName;
      uploadType = report.imageMimeType;
    } else if (mode == SendMode.compressed && report.imageBytes != null) {
      uploadBytes = _compressJpeg(report.imageBytes!);
      uploadName = '${report.id}.jpg';
      uploadType = 'image/jpeg';
    }

    final fields = <String, dynamic>{
      'report_id': report.id,
      'created_at': report.createdAt.toUtc().toIso8601String(),
      'description': report.description,
      'trapped_count': report.trappedCount,
      'injured_count': report.injuredCount,
      'vulnerable_groups': _jsonStringList(report.vulnerableGroups),
      if (report.aiLabel != null) 'ai_label': report.aiLabel,
      if (report.aiConfidence != null) 'ai_confidence': report.aiConfidence,
      if (report.latitude != null) 'latitude': report.latitude,
      if (report.longitude != null) 'longitude': report.longitude,
      if (uploadBytes != null)
        'image': MultipartFile.fromBytes(
          uploadBytes,
          filename: uploadName ?? '${report.id}.jpg',
          contentType: uploadType == null ? null : DioMediaType.parse(uploadType),
        ),
    };
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/reports',
      data: FormData.fromMap(fields),
    );
    if (response.data?['id'] != report.id) {
      throw StateError('Backend returned a different report ID.');
    }
  }

  Future<Map<String, dynamic>> requestSms({
    required String reportId,
    required String recipient,
    required String idempotencyKey,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/reports/$reportId/sms',
      data: {
        'recipient': recipient,
        'idempotency_key': idempotencyKey,
        'confirmed': true,
      },
    );
    return response.data ?? const {};
  }
}

Uint8List _compressJpeg(Uint8List bytes) {
  final decoded = image.decodeImage(bytes);
  if (decoded == null) throw const FormatException('Không thể đọc ảnh để nén.');
  final resized = decoded.width > 1280
      ? image.copyResize(decoded, width: 1280, interpolation: image.Interpolation.linear)
      : decoded;
  return Uint8List.fromList(image.encodeJpg(resized, quality: 72));
}

String _jsonStringList(List<String> values) {
  final escaped = values.map((value) => '"${value.replaceAll('"', '\\"')}"');
  return '[${escaped.join(',')}]';
}
