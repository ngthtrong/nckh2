import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../../config.dart';
import '../../core/platform/background_sync_schedule.dart';
import '../../domain/services/sync_activity.dart';
import '../../domain/entities/rescue_record.dart';
import '../../domain/entities/rescue_status.dart';
import '../../domain/entities/send_mode.dart';
import '../../domain/entities/sms_delivery.dart';
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
  final _preparingRecords = <String>{};

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
    _preparingRecords.clear();
    await localDataSource.init();
    await outboxDataSource.init();
    serverLocator?.attach(outboxDataSource);
    await updateBackgroundSync(hasSyncWork(getAllRecords()));
  }

  @override
  String? get connectedServerUrl =>
      serverLocator?.connectedUrl ??
      (serverLocator == null ? kServerBaseUrl : null);

  @override
  Future<bool> reconnectServer({bool force = true}) => _serial(
    () => serverLocator?.ensureConnected(force: force) ?? Future.value(true),
  );

  @override
  List<RescueRecord> getAllRecords() {
    return localDataSource.getAllRecords();
  }

  @override
  RescueRecord? getRecord(String id) => localDataSource.getRecord(id);

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
  Future<void> saveRecord(RescueRecord record, {bool preparing = false}) async {
    if (preparing) _preparingRecords.add(record.id);
    await localDataSource.saveRecord(record);
    await _updateSchedule();
  }

  Future<void> _updateSchedule() =>
      updateBackgroundSync(hasSyncWork(getAllRecords()));

  bool _scheduleDirty = false;
  bool _syncing = false;
  Future<void>? _syncWork;
  Future<List<RescueRecord>>? _statusWork;
  final _settling = <String, Future<RescueRecord>>{};

  Future<void> _saveLocalRecord(RescueRecord record) async {
    await localDataSource.saveRecord(record);
    _scheduleDirty = true;
  }

  /// Serialize metadata/outbox writes; slow image/status requests cannot hold up SOS.
  Future<void> _lock = Future.value();

  Future<T> _serial<T>(Future<T> Function() action) {
    final result = _lock.then((_) async {
      try {
        return await action();
      } finally {
        if (_scheduleDirty && !_syncing) {
          _scheduleDirty = false;
          await _updateSchedule();
        }
      }
    });
    _lock = result.then<void>((_) {}, onError: (_) {});
    return result;
  }

  @override
  Future<void> queueRecord(RescueRecord record) => _serial(() async {
    await _enqueue(record);
    _preparingRecords.remove(record.id);
  });

  @override
  Future<RescueRecord> sendRecord(RescueRecord record) async {
    await _serial(() async {
      // Recoverable transport rejection gets one new message and immediate retry.
      for (var attempt = 0; attempt < 2; attempt++) {
        await _enqueue(record);
        _preparingRecords.remove(record.id);
        await _flushOutbox(priorityRecordId: record.id);
        if (!_hasRecoverableDeadLetter(record)) break;
      }
    });
    return _settle(record);
  }

  @override
  DateTime? get nextRetryAt => outboxDataSource.nextAttemptAt;

  @override
  Future<void> syncPendingRecords({bool immediate = true}) =>
      _syncWork ??= _syncPendingRecords(
        immediate: immediate,
      ).whenComplete(() => _syncWork = null);

  Future<void> _syncPendingRecords({required bool immediate}) async {
    final elapsed = Stopwatch()..start();
    _syncing = true;
    try {
      final pending = await _serial(() async {
        if (immediate) await outboxDataSource.makePendingReady();
        final pending = getAllRecords()
            .where((r) => r.awaitingSync && !_preparingRecords.contains(r.id))
            .toList();
        for (final record in pending) {
          await _enqueue(record);
        }
        await _flushOutbox(maxBatches: 20, budget: elapsed);
        return pending;
      });
      final cursor = pending.indexWhere(
        (record) => record.id == outboxDataSource.lastAttachmentRecordId,
      );
      for (var i = 0; i < pending.length; i++) {
        if (elapsed.elapsed >= const Duration(seconds: 20)) break;
        final record = pending[(cursor + 1 + i) % pending.length];
        if (record.imagePath?.isNotEmpty == true) {
          // Persist before upload so a timed-out image cannot lead every worker run.
          await _serial(
            () => outboxDataSource.rememberAttachmentAttempt(record.id),
          );
        }
        await _settle(record);
      }
    } finally {
      _syncing = false;
      await _serial(() async {});
    }
  }

  bool _hasRecoverableDeadLetter(RescueRecord record) {
    final message = outboxDataSource.messageForRecord(record.id);
    return message != null &&
        message.deliveryStatus == 'dead_letter' &&
        isRecoverableDeadLetter(message.lastError);
  }

  /// Chốt kết quả gửi: server từ chối vĩnh viễn → ghi `syncError` để bản ghi không
  /// nằm mãi trong "chờ gửi"; metadata đã ACK và xong ảnh → `synced`.
  Future<RescueRecord> _settle(RescueRecord record) =>
      _settling[record.id] ??= _settleOnce(record).whenComplete(() {
        _settling.remove(record.id);
      });

  Future<RescueRecord> _settleOnce(RescueRecord record) async {
    var current = await _serial(() async {
      final latest = localDataSource.getRecord(record.id) ?? record;
      final message = outboxDataSource.messageForRecord(record.id);
      if (message != null &&
          message.deliveryStatus == 'dead_letter' &&
          !isRecoverableDeadLetter(message.lastError)) {
        final failed = latest.copyWith(
          syncError: message.lastError ?? 'REJECTED',
        );
        await _saveLocalRecord(failed);
        return localDataSource.getRecord(failed.id) ?? failed;
      }
      return message != null ? latest : latest.copyWith(metadataSynced: true);
    });
    if (!current.metadataSynced ||
        current.synced ||
        current.syncError != null) {
      return current;
    }
    try {
      final done = await _finishAttachment(current);
      current = current.copyWith(synced: done, clearAttachmentError: true);
    } catch (error) {
      debugPrint('Không đọc/gửi được ảnh ${record.id}: $error');
      current = current.copyWith(attachmentError: 'ATTACHMENT_UNAVAILABLE');
    }
    return _serial(() async {
      await _saveLocalRecord(current);
      return localDataSource.getRecord(current.id) ?? current;
    });
  }

  @override
  Future<SmsResult> sendSmsFallback(RescueRecord record) =>
      senderDataSource.sendSms(record);

  @override
  Future<List<RescueRecord>> refreshStatuses() =>
      _statusWork ??= _refreshStatuses().whenComplete(() => _statusWork = null);

  Future<List<RescueRecord>> _refreshStatuses() async {
    // Hỏi cả báo cáo đã có metadata trên server (hết message trong outbox) nhưng
    // ảnh còn chờ gửi: điều phối viên đã thấy và có thể đã điều đội.
    final tracked = getAllRecords()
        .where(
          (r) =>
              !_preparingRecords.contains(r.id) &&
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
      await _serial(() async {
        for (final record in chunk) {
          final latest = localDataSource.getRecord(record.id) ?? record;
          final next = advancedStatus(latest.status, statuses[record.id]);
          if (next == null) continue;
          final updated = latest.copyWith(status: next);
          await _saveLocalRecord(updated);
          changed.add(localDataSource.getRecord(updated.id) ?? updated);
        }
      });
    }
    return changed;
  }

  Future<void> _enqueue(RescueRecord record) async {
    record = localDataSource.getRecord(record.id) ?? record;
    if (!record.metadataSynced) {
      await outboxDataSource.enqueueCreate(rescueRecordPayload(record));
    }
  }

  Future<void> _flushOutbox({
    String? priorityRecordId,
    int maxBatches = 1,
    Stopwatch? budget,
  }) async {
    final elapsed = budget ?? (Stopwatch()..start());
    var batchLimit = 50;
    // Bound worker time and leave retries to backoff rather than a tight loop.
    for (
      var i = 0;
      i < maxBatches && elapsed.elapsed < const Duration(seconds: 20);
      i++
    ) {
      var batch = outboxDataSource.readyMessages(
        limit: batchLimit,
        priorityRecordId: priorityRecordId,
      );
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
        continue;
      }

      await outboxDataSource.markInFlight(batch);
      var retryLater = false;
      try {
        final results = await syncDataSource.sendBatch(batch);
        final byId = {
          for (final result in results) result['message_id'] as String: result,
        };
        for (final message in batch) {
          final result = byId[message.messageId];
          final status = result?['status'];
          if (status == 'accepted' || status == 'duplicate') {
            final recordId = message.payload['id'];
            final record = localDataSource.getRecord(recordId as String);
            if (record != null) {
              // Persist the ACK before deleting its message so image retries do not re-enqueue it.
              await _saveLocalRecord(record.copyWith(metadataSynced: true));
            }
            await outboxDataSource.acknowledge(message.messageId);
          } else if (status == 'retry_later' || result?['retryable'] == true) {
            retryLater = true;
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
            retryLater = true;
            await outboxDataSource.scheduleRetry(
              message.messageId,
              'MISSING_ACK',
            );
          }
        }
      } on DioException catch (error) {
        final status = error.response?.statusCode;
        if (status == 413 && batch.length > 1) {
          await outboxDataSource.releaseInFlight(batch);
          batchLimit = (batch.length + 1) ~/ 2;
          i--; // Splitting is bounded by batch size; only sent batches use the pass limit.
          continue;
        }
        final retryable =
            status == null ||
            status == 408 ||
            status == 429 ||
            (status >= 500 && status < 600);
        retryLater = retryable;
        for (final message in batch) {
          if (retryable) {
            await outboxDataSource.scheduleRetry(
              message.messageId,
              'HTTP_$status',
            );
          } else {
            await outboxDataSource.markDeadLetter(
              message.messageId,
              status == 413 ? 'REQUEST_TOO_LARGE' : 'HTTP_$status',
            );
          }
        }
      } catch (error) {
        retryLater = true;
        for (final message in batch) {
          await outboxDataSource.scheduleRetry(
            message.messageId,
            error.toString(),
          );
        }
      }
      if (retryLater) return;
    }
  }

  Future<bool> _finishAttachment(RescueRecord record) async {
    if (outboxDataSource.messageForRecord(record.id) != null) return false;
    final path = record.imagePath;
    if (path == null || path.isEmpty) return true;
    if (serverLocator != null && !await serverLocator!.ensureConnected()) {
      return false;
    }
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
        final imageBytes = await _attachmentBytes(path);
        final compressed = await senderDataSource.compress(imageBytes);
        return _deliverImage(
          record,
          compressed ?? imageBytes,
          allowShrink: false,
        );
      case SendMode.fullImage:
        var bytes = await _attachmentBytes(path);
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

  Future<Uint8List> _attachmentBytes(String path) async {
    final bytes = await readLocalFile(path);
    if (bytes.isEmpty) throw StateError('Ảnh đính kèm trống.');
    return bytes;
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
