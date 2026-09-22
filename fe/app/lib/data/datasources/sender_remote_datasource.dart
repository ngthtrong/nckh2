import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:flutter/services.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';

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
      'createdAt': rec.createdAt.toIso8601String(),
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

  Future<void> sendSms(String to, String body) async {
    await _smsChannel.invokeMethod<bool>('sendSms', {'to': to, 'body': body});
  }

  String smsBody(RescueRecord r) {
    final pos = '${r.lat.toStringAsFixed(5)},${r.lng.toStringAsFixed(5)}';
    final vulnerable = r.vulnerableGroups.join(',');
    return 'SOS|pos:$pos|trapped:${r.trappedCount}|injured:${r.injuredCount}'
        '${vulnerable.isNotEmpty ? '|vuln:$vulnerable' : ''}'
        '${r.description.isNotEmpty ? '|note:${r.description}' : ''}';
  }
}
