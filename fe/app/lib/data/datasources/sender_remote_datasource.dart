import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../../config.dart';
import '../../domain/entities/rescue_image.dart';
import '../../domain/entities/rescue_record.dart';
import 'image/image_compressor.dart';
import 'image/image_compressor_factory.dart';

typedef UploadResult = ({
  bool ok,
  int bytesSent,
  int durationMs,
  String? error,
});

enum UploadImageMode { original, compressed, textOnly }

UploadImageMode selectUploadImageMode({
  required double bytesPerSecond,
  required bool hasImage,
}) {
  if (!hasImage || bytesPerSecond < 32 * 1024) {
    return UploadImageMode.textOnly;
  }
  if (bytesPerSecond < 256 * 1024) {
    return UploadImageMode.compressed;
  }
  return UploadImageMode.original;
}

class SenderRemoteDataSource {
  SenderRemoteDataSource({Dio? dio, ImageCompressor? imageCompressor})
    : _dio =
          dio ??
          Dio(
            BaseOptions(
              baseUrl: kServerBaseUrl,
              connectTimeout: const Duration(seconds: 10),
              sendTimeout: const Duration(seconds: 60),
              receiveTimeout: const Duration(seconds: 30),
            ),
          ),
      _imageCompressor = imageCompressor ?? createImageCompressor();

  final Dio _dio;
  final ImageCompressor _imageCompressor;

  Future<UploadResult> upload(
    RescueRecord record,
    Uint8List? imageBytes,
  ) async {
    final stopwatch = Stopwatch()..start();
    try {
      final throughput = await _measureBytesPerSecond();
      final mode = selectUploadImageMode(
        bytesPerSecond: throughput,
        hasImage: imageBytes != null,
      );
      RescueImage? uploadImage;
      if (mode == UploadImageMode.original && record.image != null) {
        uploadImage = record.image;
      } else if (mode == UploadImageMode.compressed && imageBytes != null) {
        uploadImage = await _imageCompressor.compress(imageBytes);
      }

      final fields = <String, dynamic>{
        'report_id': record.id,
        'created_at': record.createdAt.toUtc().toIso8601String(),
        'description': record.description,
        'trapped_count': record.trappedCount,
        'injured_count': record.injuredCount,
        'vulnerable_groups': jsonEncode(record.vulnerableGroups),
        if (record.aiLabel != null) 'ai_label': record.aiLabel,
        if (record.aiConfidence != null) 'ai_confidence': record.aiConfidence,
        'latitude': record.lat,
        'longitude': record.lng,
        if (uploadImage != null)
          'image': MultipartFile.fromBytes(
            uploadImage.bytes,
            filename: uploadImage.fileName,
            contentType: DioMediaType.parse(uploadImage.mimeType),
          ),
      };
      final form = FormData.fromMap(fields);
      final response = await _dio.post<Map<String, dynamic>>(
        '/api/reports',
        data: form,
      );
      if (response.data?['id'] != record.id) {
        throw StateError('Backend trả về report ID không khớp.');
      }
      stopwatch.stop();
      return (
        ok: true,
        bytesSent: form.length,
        durationMs: stopwatch.elapsedMilliseconds,
        error: null,
      );
    } catch (error) {
      stopwatch.stop();
      return (
        ok: false,
        bytesSent: 0,
        durationMs: stopwatch.elapsedMilliseconds,
        error: 'Không thể gửi báo cáo: $error',
      );
    }
  }

  Future<double> _measureBytesPerSecond() async {
    final stopwatch = Stopwatch()..start();
    final response = await _dio.get<List<int>>(
      '/probe',
      options: Options(responseType: ResponseType.bytes),
    );
    stopwatch.stop();
    final length = response.data?.length ?? 0;
    final seconds =
        stopwatch.elapsedMicroseconds / Duration.microsecondsPerSecond;
    return seconds <= 0 ? double.infinity : length / seconds;
  }
}
