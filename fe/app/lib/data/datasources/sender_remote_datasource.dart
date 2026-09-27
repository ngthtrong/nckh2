import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../config.dart';
import '../../domain/entities/rescue_record.dart';

typedef UploadResult = ({bool ok, int bytesSent, int durationMs});

class SenderRemoteDataSource {
  static const _smsChannel = MethodChannel('rescue/sms');

  final Dio _dio = Dio(
    BaseOptions(
      connectTimeout: const Duration(seconds: 10),
      sendTimeout: const Duration(seconds: 60),
      receiveTimeout: const Duration(seconds: 30),
    ),
  );

  Future<UploadResult> upload(RescueRecord rec, Uint8List? jpeg) async {
    final meta = jsonEncode({
      'id': rec.id,
      // meta chính là payload CREATE_RESCUE_RECORD: thời gian UTC ISO 8601 (contact_connect.md).
      'createdAt': rec.createdAt.toUtc().toIso8601String(),
      'lat': rec.lat,
      'lng': rec.lng,
      'trappedCount': rec.trappedCount,
      'injuredCount': rec.injuredCount,
      'vulnerableGroups': rec.vulnerableGroups,
      'description': rec.description,
      'aiTags': rec.aiTags.map((e) => e.toJson()).toList(),
      'sendMode': rec.sendMode,
      if (jpeg != null) 'imageSha256': 'sha256:${sha256.convert(jpeg)}',
      if (jpeg != null) 'imageSizeBytes': jpeg.length,
    });
    final sw = Stopwatch()..start();
    final form = FormData.fromMap({
      'meta': meta,
      if (jpeg != null)
        'image': MultipartFile.fromBytes(jpeg, filename: '${rec.id}.jpg'),
    });
    var bytesSent = meta.length;
    try {
      bytesSent = form.length;
    } catch (_) {}
    try {
      await _dio.post(
        '$kServerBaseUrl/api/reports',
        data: form,
        options: Options(headers: {'X-Message-Contract-Version': '1'}),
      );
      sw.stop();
      return (
        ok: true,
        bytesSent: jpeg != null ? bytesSent + jpeg.length : bytesSent,
        durationMs: sw.elapsedMilliseconds,
      );
    } catch (_) {
      sw.stop();
      return (ok: false, bytesSent: 0, durationMs: sw.elapsedMilliseconds);
    }
  }

  Future<Uint8List?> compress(
    Uint8List src, {
    int quality = kCompressQualityMedium,
    int maxSide = kCompressMaxSideMedium,
  }) async {
    try {
      return await FlutterImageCompress.compressWithList(
        src,
        minWidth: maxSide,
        minHeight: maxSide,
        quality: quality,
        format: CompressFormat.jpeg,
      );
    } catch (_) {
      return null;
    }
  }

  /// SMS dự phòng tới tổng đài khi không có data. Chỉ Android có kênh
  /// `rescue/sms`; web/desktop, số tổng đài chưa cấu hình hoặc bị từ chối quyền
  /// thì trả false để báo cáo nằm lại hàng đợi.
  Future<bool> sendSms(RescueRecord record) async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) return false;
    if (kEmergencyPhone == kPlaceholderEmergencyPhone) {
      debugPrint('SMS fallback bỏ qua: chưa đặt EMERGENCY_PHONE.');
      return false;
    }
    try {
      if (!await Permission.sms.request().isGranted) return false;
      final ok = await _smsChannel.invokeMethod<bool>('sendSms', {
        'to': kEmergencyPhone,
        'body': smsBody(record),
      });
      return ok ?? false;
    } catch (e) {
      debugPrint('SMS fallback lỗi: $e');
      return false;
    }
  }
}

/// Nội dung SMS: gọn, đủ để tổng đài điều phối; `id` để khớp với bản ghi đồng
/// bộ sau này khi có mạng.
String smsBody(RescueRecord r) {
  final lat = r.lat, lng = r.lng;
  final pos = lat != null && lng != null
      ? '${lat.toStringAsFixed(5)},${lng.toStringAsFixed(5)}'
      : 'unknown';
  final vulnerable = r.vulnerableGroups.join(',');
  return 'SOS|id:${r.id}|pos:$pos|trapped:${r.trappedCount}|injured:${r.injuredCount}'
      '${vulnerable.isNotEmpty ? '|vuln:$vulnerable' : ''}'
      '${r.description.isNotEmpty ? '|note:${r.description}' : ''}';
}
