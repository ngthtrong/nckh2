import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/services.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';

import '../config.dart';
import '../models/rescue_record.dart';

/// Kết quả một lần upload.
typedef UploadResult = ({bool ok, int bytesSent, int durationMs});

/// Gửi dữ liệu lên server + SMS fallback (qua platform channel Android).
class SenderService {
  static const _smsChannel = MethodChannel('rescue/sms');

  final Dio _dio = Dio(BaseOptions(
    connectTimeout: const Duration(seconds: 10),
    sendTimeout: const Duration(seconds: 60),
    receiveTimeout: const Duration(seconds: 30),
  ));

  /// POST multipart: meta JSON luôn gửi; ảnh kèm theo nếu [jpeg] != null.
  /// Đo thời gian bằng Stopwatch, đo dung lượng thực của payload.
  Future<UploadResult> upload(RescueRecord rec, Uint8List? jpeg) async {
    final meta = jsonEncode(rec.toMap());
    final sw = Stopwatch()..start();
    final form = FormData.fromMap({
      'meta': meta,
      if (jpeg != null)
        'image': MultipartFile.fromBytes(jpeg, filename: '${rec.id}.jpg'),
    });
    var bytesSent = meta.length; // fallback nếu không đọc được content-length
    try {
      bytesSent = form.length;
    } catch (_) {}
    try {
      await _dio.post('$kServerBaseUrl/api/reports', data: form);
      sw.stop();
      return (
        ok: true,
        bytesSent: jpeg != null ? bytesSent + jpeg.length : bytesSent,
        durationMs: sw.elapsedMilliseconds,
      );
    } catch (_) {
      return (ok: false, bytesSent: 0, durationMs: sw.elapsedMilliseconds);
    }
  }

  /// Nén thích ứng cho mạng trung bình/yếu. Trả null nếu nén lỗi
  /// (bên gọi sẽ rơi về gửi text-only).
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

  /// SMS fallback — chỉ hoạt động Android có SIM. Ném exception nếu thất bại.
  Future<void> sendSms(String to, String body) async {
    await _smsChannel.invokeMethod<bool>('sendSms', {'to': to, 'body': body});
  }

  /// Nội dung SMS siêu nhỏ (~vài trăm byte).
  String smsBody(RescueRecord r) {
    final pos = (r.lat != null && r.lng != null)
        ? '${r.lat!.toStringAsFixed(5)},${r.lng!.toStringAsFixed(5)}'
        : 'no_gps';
    return 'SOS|${r.label}|$pos|${DateTime.fromMillisecondsSinceEpoch(r.createdAtMs).toIso8601String()}'
        '${r.note.isNotEmpty ? '|${r.note}' : ''}';
  }
}
