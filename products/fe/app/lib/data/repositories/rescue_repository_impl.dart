import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../../config.dart';
import '../../domain/entities/rescue_record.dart';
import '../../domain/entities/rescue_status.dart';
import '../../domain/entities/send_mode.dart';
import '../../domain/repositories/rescue_repository.dart';
import '../../domain/services/adaptive_send_policy.dart';
import '../../core/platform/local_file.dart';
import '../datasources/outbox_local_datasource.dart';
import '../datasources/record_local_datasource.dart';
import '../datasources/server_locator.dart';
import '../datasources/sender_remote_datasource.dart';
import '../datasources/sync_remote_datasource.dart';
import '../models/sync_message_model.dart';
import '../models/rescue_record_payload.dart';

class RescueRepositoryImpl implements RescueRepository {
  final RecordLocalDataSource localDataSource;
  final SenderRemoteDataSource senderDataSource;
  final OutboxLocalDataSource outboxDataSource;
  final SyncRemoteDataSource syncDataSource;
  final ServerLocator? serverLocator;

  /// Chọn cách gửi ảnh cho bản ghi đồng bộ muộn (xếp hàng khi offline).
  /// Null thì gửi ảnh gốc như trước.
  final AdaptiveSendPolicy? sendPolicy;

  RescueRepositoryImpl({
    required this.localDataSource,
    required this.senderDataSource,
    OutboxLocalDataSource? outboxDataSource,
    SyncRemoteDataSource? syncDataSource,
    this.serverLocator,
    this.sendPolicy,
  }) : outboxDataSource = outboxDataSource ?? OutboxLocalDataSource(),
       syncDataSource = syncDataSource ?? SyncRemoteDataSource();

  @override
  Future<void> init() async {
    await localDataSource.init();
    await outboxDataSource.init();
    if (serverLocator != null) await serverLocator!.init(outboxDataSource);
  }

  @override
  String? get connectedServerUrl =>
      serverLocator?.connectedUrl ??
      (serverLocator == null ? kServerBaseUrl : null);

  @override
  Future<bool> reconnectServer() => _serial(
    () => serverLocator?.ensureConnected(force: true) ?? Future.value(true),
  );

  @override
  List<RescueRecord> getAllRecords() {
    return localDataSource.getAllRecords();
  }

  @override
  List<RescueRecord> getRecordsPage({required int offset, required int limit}) {
    return localDataSource.getRecordsPage(offset: offset, limit: limit);
  }

  @override
  int get recordCount => localDataSource.recordCount;

  @override
  int getPendingCount() {
    return localDataSource.getPendingCount();
  }

  @override
  Future<void> saveRecord(RescueRecord record) async {
    await localDataSource.saveRecord(record);
  }

  /// Gửi, đồng bộ và cập nhật trạng thái cùng đọc-ghi outbox và bản ghi: chạy lần
  /// lượt để hai luồng (người dùng bấm gửi, có mạng trở lại, hẹn giờ 15 s) không
  /// gửi trùng message hay ghi đè bản ghi của nhau.
  Future<void> _lock = Future.value();

  Future<T> _serial<T>(Future<T> Function() action) {
    final result = _lock.then((_) => action());
    _lock = result.then<void>((_) {}, onError: (_) {});
    return result;
  }

  @override
  Future<RescueRecord> sendRecord(RescueRecord record) => _serial(() async {
    // Dead-letter do vận chuyển (vd. SEQUENCE_REUSED) được tạo message mới và gửi lại ngay một lần.
    for (var attempt = 0; attempt < 2; attempt++) {
      await _enqueue(record);
      await _flushOutbox();
      if (!_hasRecoverableDeadLetter(record)) break;
    }
    return _settle(record);
  });

  @override
  DateTime? get nextRetryAt => outboxDataSource.nextAttemptAt;

  @override
  Future<void> syncPendingRecords({bool immediate = true}) => _serial(() async {
    if (immediate) await outboxDataSource.makePendingReady();
    final pending = getAllRecords().where((r) => r.awaitingSync).toList();
    for (final record in pending) {
      await _enqueue(record);
    }
    await _flushOutbox();
    for (final record in pending) {
      await _settle(record);
    }
  });

  bool _hasRecoverableDeadLetter(RescueRecord record) {
    final message = outboxDataSource.messageForRecord(record.id);
    return message != null &&
        message.deliveryStatus == 'dead_letter' &&
        isRecoverableDeadLetter(message.lastError);
  }

  /// Chốt kết quả gửi: server từ chối vĩnh viễn → ghi `syncError` để bản ghi không
  /// nằm mãi trong "chờ gửi"; metadata đã ACK và xong ảnh → `synced`.
  Future<RescueRecord> _settle(RescueRecord record) async {
    final message = outboxDataSource.messageForRecord(record.id);
    if (message != null &&
        message.deliveryStatus == 'dead_letter' &&
        !isRecoverableDeadLetter(message.lastError)) {
      final failed = record.copyWith(
        syncError: message.lastError ?? 'REJECTED',
      );
      await saveRecord(failed);
      return failed;
    }
    if (await _finishAttachment(record)) {
      final done = record.copyWith(synced: true);
      await saveRecord(done);
      return done;
    }
    return record;
  }

  @override
  Future<bool> sendSmsFallback(RescueRecord record) =>
      senderDataSource.sendSms(record);

  @override
  Future<List<RescueRecord>> refreshStatuses() => _serial(() async {
    // Hỏi cả báo cáo đã có metadata trên server (hết message trong outbox) nhưng
    // ảnh còn chờ gửi: điều phối viên đã thấy và có thể đã điều đội.
    final tracked = getAllRecords()
        .where(
          (r) =>
              !isFinalStatus(r.status) &&
              r.syncError == null &&
              (r.synced || outboxDataSource.messageForRecord(r.id) == null),
        )
        .toList();
    if (tracked.isEmpty) return [];
    if (serverLocator != null && !await serverLocator!.ensureConnected()) {
      return [];
    }
    final changed = <RescueRecord>[];
    for (var i = 0; i < tracked.length; i += 100) {
      final chunk = tracked.sublist(i, (i + 100).clamp(0, tracked.length));
      final statuses = await syncDataSource.fetchStatuses([
        for (final record in chunk) record.id,
      ]);
      for (final record in chunk) {
        final next = advancedStatus(record.status, statuses[record.id]);
        if (next == null) continue;
        final updated = record.copyWith(status: next);
        await saveRecord(updated);
        changed.add(updated);
      }
    }
    return changed;
  });

  Future<void> _enqueue(RescueRecord record) =>
      outboxDataSource.enqueueCreate(rescueRecordPayload(record));

  Future<void> _flushOutbox() async {
    var batch = outboxDataSource.readyMessages();
    if (batch.isEmpty) return;
    if (serverLocator != null && !await serverLocator!.ensureConnected()) {
      return;
    }

    while (batch.length > 1 && _requestSize(batch) > 256 * 1024) {
      batch = batch.sublist(0, batch.length - 1);
    }
    if (_requestSize(batch) > 256 * 1024) {
      await outboxDataSource.markDeadLetter(
        batch.first.messageId,
        'REQUEST_TOO_LARGE',
      );
      return;
    }

    await outboxDataSource.markInFlight(batch);
    try {
      final results = await syncDataSource.sendBatch(batch);
      final byId = {
        for (final result in results) result['message_id'] as String: result,
      };
      for (final message in batch) {
        final result = byId[message.messageId];
        final status = result?['status'];
        if (status == 'accepted' || status == 'duplicate') {
          await outboxDataSource.acknowledge(message.messageId);
        } else if (status == 'retry_later' || result?['retryable'] == true) {
          await outboxDataSource.scheduleRetry(
            message.messageId,
            result?['code'] as String?,
          );
        } else if (result != null) {
          await outboxDataSource.markDeadLetter(
            message.messageId,
            result['code'] as String?,
          );
        } else {
          await outboxDataSource.scheduleRetry(
            message.messageId,
            'MISSING_ACK',
          );
        }
      }
    } on DioException catch (error) {
      final status = error.response?.statusCode;
      final retryable =
          status == null || status == 408 || status == 429 || status >= 500;
      for (final message in batch) {
        if (retryable) {
          await outboxDataSource.scheduleRetry(
            message.messageId,
            'HTTP_$status',
          );
        } else {
          await outboxDataSource.markDeadLetter(
            message.messageId,
            'HTTP_$status',
          );
        }
      }
    } catch (error) {
      for (final message in batch) {
        await outboxDataSource.scheduleRetry(
          message.messageId,
          error.toString(),
        );
      }
    }
  }

  Future<bool> _finishAttachment(RescueRecord record) async {
    if (outboxDataSource.messageForRecord(record.id) != null) return false;
    final path = record.imagePath;
    if (path == null || path.isEmpty) return true;
    if (serverLocator != null && !await serverLocator!.ensureConnected()) {
      return false;
    }
    late final Uint8List imageBytes;
    try {
      imageBytes = await readLocalFile(path);
    } catch (_) {
      return true;
    }
    if (imageBytes.isEmpty) return true;

    // Chế độ đã chọn lúc gửi; bản ghi xếp hàng khi offline (hoặc bản cũ) thì
    // quyết định lại theo mạng hiện tại.
    var mode = sendModeFromName(record.sendMode);
    if (mode == null ||
        mode == SendMode.queuedOffline ||
        mode == SendMode.smsFallback) {
      mode = sendPolicy == null
          ? SendMode.fullImage
          : (await sendPolicy!.decide(
              hasImage: true,
              confidence: record.maxAiConfidence,
            )).mode;
    }
    switch (mode) {
      case SendMode.textOnly:
        return true; // metadata đã có ACK; bỏ ảnh để tiết kiệm băng thông
      case SendMode.smsFallback || SendMode.queuedOffline:
        return false; // chưa tới được server, thử lại lần đồng bộ sau
      case SendMode.compressedImage:
        final compressed = await senderDataSource.compress(imageBytes);
        return _deliverImage(
          record,
          compressed ?? imageBytes,
          allowShrink: false,
        );
      case SendMode.fullImage:
        var bytes = imageBytes;
        if (!isServerSupportedImage(bytes)) {
          // HEIC hoặc định dạng server không nhận: chuyển sang JPEG, giữ độ phân giải.
          bytes =
              await senderDataSource.compress(
                bytes,
                quality: kConvertJpegQuality,
                maxSide: kConvertMaxSide,
              ) ??
              bytes;
        }
        return _deliverImage(record, bytes);
    }
  }

  Future<bool> _deliverImage(
    RescueRecord record,
    Uint8List bytes, {
    bool allowShrink = true,
  }) => deliverImage(
    bytes,
    upload: (data) => senderDataSource.upload(
      record,
      data,
      clientId: outboxDataSource.clientId,
    ),
    shrink: (data) => senderDataSource.compress(data),
    allowShrink: allowShrink,
    onGiveUp: (status) => debugPrint(
      'Server từ chối ảnh của ${record.id} (HTTP $status); bỏ ảnh, báo cáo vẫn đã gửi.',
    ),
  );

  int _requestSize(List<SyncMessageModel> messages) => utf8
      .encode(
        jsonEncode({
          'messages': messages
              .map((message) => message.toRequestJson())
              .toList(),
        }),
      )
      .length;
}
