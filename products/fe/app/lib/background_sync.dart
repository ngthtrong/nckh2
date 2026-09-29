import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:hive_ce_flutter/hive_flutter.dart';

import 'config.dart';
import 'models/rescue_record.dart';
import 'services/network_service.dart';
import 'services/record_store.dart';

/// Sync nền tối giản: mở lại Hive, đẩy các bản ghi pending lên server.
/// Dùng chung cho foreground syncAll() và background task (workmanager).
class BackgroundSync {
  static Future<void> perform({bool requireNetwork = true}) async {
    if (requireNetwork) {
      final net = NetworkService();
      if (!await net.hasData()) return;
    }
    await Hive.initFlutter();
    final box = await Hive.openBox<Map>(RecordStore.boxName);
    final dio = Dio(BaseOptions(
      connectTimeout: const Duration(seconds: 10),
      sendTimeout: const Duration(seconds: 60),
    ));

    for (final raw in box.values) {
      final rec = RescueRecord.fromMap(Map<dynamic, dynamic>.from(raw));
      if (rec.status != 'pending') continue;

      // Đọc lại ảnh đã lưu bền; mất file thì vẫn gửi text meta.
      Uint8List? jpeg;
      if (rec.imagePath != null) {
        try {
          final f = File(rec.imagePath!);
          if (await f.exists()) jpeg = await f.readAsBytes();
        } catch (_) {}
      }

      final sw = Stopwatch()..start();
      try {
        final form = FormData.fromMap({
          'meta': jsonEncode(rec.toMap()),
          if (jpeg != null)
            'image': MultipartFile.fromBytes(jpeg, filename: '${rec.id}.jpg'),
        });
        await dio.post('$kServerBaseUrl/api/reports', data: form);
        sw.stop();
        var bytesSent = 0;
        try {
          bytesSent = form.length;
        } catch (_) {}
        await box.put(
          rec.id,
          rec
              .copyWith(
                status: 'sent',
                bytesSent: bytesSent,
                durationUploadMs: sw.elapsedMilliseconds,
              )
              .toMap(),
        );
      } catch (_) {
        await box.put(
          rec.id,
          rec.copyWith(attempts: rec.attempts + 1).toMap(),
        );
      }
    }
  }
}
