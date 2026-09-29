import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../config.dart';
import '../../domain/entities/rescue_record.dart';
import '../models/rescue_record_payload.dart';

/// Kết quả gửi ảnh. `status` là mã HTTP khi server trả lời; `permanent` khi server
/// từ chối vĩnh viễn (gửi lại y hệt cũng vô ích, xem [isPermanentUploadFailure]).
typedef UploadResult = ({
  bool ok,
  int bytesSent,
  int durationMs,
  int? status,
  bool permanent,
});

/// Định dạng ảnh server nhận (JPEG, PNG, WebP), xác định theo byte đầu file như server.
bool isServerSupportedImage(Uint8List bytes) {
  bool startsWith(List<int> prefix, [int offset = 0]) {
    if (bytes.length < offset + prefix.length) return false;
    for (var i = 0; i < prefix.length; i++) {
      if (bytes[offset + i] != prefix[i]) return false;
    }
    return true;
  }

  return startsWith(const [0xFF, 0xD8, 0xFF]) ||
      startsWith(const [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]) ||
      (startsWith(const [0x52, 0x49, 0x46, 0x46]) &&
          startsWith(const [0x57, 0x45, 0x42, 0x50], 8));
}

/// Lỗi 4xx là vĩnh viễn, trừ 408/429 (tạm thời) và `IMAGE_HASH_MISMATCH` (dữ liệu
/// hỏng trên đường truyền, gửi lại có thể thành công). Lỗi mạng và 5xx luôn thử lại.
bool isPermanentUploadFailure(int? status, Object? body) {
  if (status == null || status < 400 || status >= 500) return false;
  if (status == 408 || status == 429) return false;
  if (uploadErrorCode(body) == 'IMAGE_HASH_MISMATCH') return false;
  return true;
}

/// Mã lỗi server: `{"detail": {"code": ...}}`; server bản cũ trả `{"detail": "..."}`.
String? uploadErrorCode(Object? body) {
  final detail = body is Map ? body['detail'] : null;
  final code = detail is Map ? detail['code'] : detail;
  return code is String ? code : null;
}

/// Gửi ảnh cho báo cáo đã có metadata trên server. Trả về `true` khi xong phần ảnh
/// (đã gửi, hoặc server từ chối vĩnh viễn nên bỏ ảnh để bản ghi không kẹt mãi), `false`
/// khi cần thử lại ở lần đồng bộ sau. Ảnh quá lớn (413) được nén rồi gửi lại một lần.
Future<bool> deliverImage(
  Uint8List bytes, {
  required Future<UploadResult> Function(Uint8List bytes) upload,
  required Future<Uint8List?> Function(Uint8List bytes) shrink,
  bool allowShrink = true,
  void Function(int? status)? onGiveUp,
}) async {
  var result = await upload(bytes);
  if (result.ok) return true;
  if (!result.permanent) return false;
  if (allowShrink && result.status == 413) {
    final smaller = await shrink(bytes);
    if (smaller != null) {
      result = await upload(smaller);
      if (result.ok) return true;
      if (!result.permanent) return false;
    }
  }
  onGiveUp?.call(result.status);
  return true;
}

class SenderRemoteDataSource {
  static const _smsChannel = MethodChannel('rescue/sms');

  final Dio _dio = Dio(
    BaseOptions(
      connectTimeout: const Duration(seconds: 10),
      sendTimeout: const Duration(seconds: 60),
      receiveTimeout: const Duration(seconds: 30),
    ),
  );

  /// [clientId] là ID thiết bị trong outbox: server chỉ cho chủ báo cáo gắn ảnh.
  Future<UploadResult> upload(
    RescueRecord rec,
    Uint8List? jpeg, {
    required String clientId,
  }) async {
    final meta = jsonEncode({
      ...rescueRecordPayload(rec),
      'clientId': clientId,
      if (jpeg != null) 'imageSha256': 'sha256:${sha256.convert(jpeg)}',
      if (jpeg != null) 'imageSizeBytes': jpeg.length,
    });
    final sw = Stopwatch()..start();
    final form = FormData.fromMap({
      'meta': meta,
      if (jpeg != null)
        'image': MultipartFile.fromBytes(jpeg, filename: '${rec.id}.jpg'),
    });
    // form.length đã gồm cả ảnh; ước lượng khi không tính được.
    var bytesSent = utf8.encode(meta).length + (jpeg?.length ?? 0);
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
        bytesSent: bytesSent,
        durationMs: sw.elapsedMilliseconds,
        status: 201,
        permanent: false,
      );
    } on DioException catch (error) {
      sw.stop();
      final status = error.response?.statusCode;
      return (
        ok: false,
        bytesSent: 0,
        durationMs: sw.elapsedMilliseconds,
        status: status,
        permanent: isPermanentUploadFailure(status, error.response?.data),
      );
    } catch (_) {
      sw.stop();
      return (
        ok: false,
        bytesSent: 0,
        durationMs: sw.elapsedMilliseconds,
        status: null,
        permanent: false,
      );
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
