import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../../domain/entities/rescue_record.dart';
import '../../domain/entities/rescue_status.dart';
import '../../domain/entities/send_mode.dart';
import '../../domain/repositories/rescue_repository.dart';
import '../../domain/services/adaptive_send_policy.dart';
import '../../core/platform/local_file.dart';
import '../datasources/outbox_local_datasource.dart';
import '../datasources/record_local_datasource.dart';
import '../datasources/sender_remote_datasource.dart';
import '../datasources/sync_remote_datasource.dart';
import '../models/sync_message_model.dart';

class RescueRepositoryImpl implements RescueRepository {
  final RecordLocalDataSource localDataSource;
  final SenderRemoteDataSource senderDataSource;
  final OutboxLocalDataSource outboxDataSource;
  final SyncRemoteDataSource syncDataSource;

  /// Chọn cách gửi ảnh cho bản ghi đồng bộ muộn (xếp hàng khi offline).
  /// Null thì gửi ảnh gốc như trước.
  final AdaptiveSendPolicy? sendPolicy;

  RescueRepositoryImpl({
    required this.localDataSource,
    required this.senderDataSource,
    OutboxLocalDataSource? outboxDataSource,
    SyncRemoteDataSource? syncDataSource,
    this.sendPolicy,
  }) : outboxDataSource = outboxDataSource ?? OutboxLocalDataSource(),
       syncDataSource = syncDataSource ?? SyncRemoteDataSource();

  @override
  Future<void> init() async {
    await localDataSource.init();
    await outboxDataSource.init();
  }

  @override
  List<RescueRecord> getAllRecords() {
    return localDataSource.getAllRecords();
  }

  @override
  int getPendingCount() {
    return localDataSource.getPendingCount();
  }

  @override
  Future<void> saveRecord(RescueRecord record) async {
    await localDataSource.saveRecord(record);
  }

  @override
  Future<bool> sendRecord(RescueRecord record) async {
    await _enqueue(record);
    await _flushOutbox();
    return _finishAttachment(record);
  }

  @override
  Future<void> syncPendingRecords() async {
    final pending = getAllRecords().where((record) => !record.synced).toList();
    for (final record in pending) {
      await _enqueue(record);
    }
    await _flushOutbox();
    for (final record in pending) {
      if (await _finishAttachment(record)) {
        await saveRecord(record.copyWith(synced: true));
      }
    }
  }

  @override
  Future<bool> sendSmsFallback(RescueRecord record) =>
      senderDataSource.sendSms(record);

  @override
  Future<List<RescueRecord>> refreshStatuses() async {
    final tracked = getAllRecords()
        .where((r) => r.synced && !isFinalStatus(r.status))
        .toList();
    if (tracked.isEmpty) return [];
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
  }

  Future<void> _enqueue(RescueRecord record) =>
      outboxDataSource.enqueueCreate(_payload(record));

  Future<void> _flushOutbox() async {
    var batch = outboxDataSource.readyMessages();
    if (batch.isEmpty) return;

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
        return (await senderDataSource.upload(
          record,
          compressed ?? imageBytes,
        )).ok;
      case SendMode.fullImage:
        return (await senderDataSource.upload(record, imageBytes)).ok;
    }
  }

  int _requestSize(List<SyncMessageModel> messages) => utf8
      .encode(
        jsonEncode({
          'messages': messages
              .map((message) => message.toRequestJson())
              .toList(),
        }),
      )
      .length;

  Map<String, dynamic> _payload(RescueRecord record) => {
    'id': record.id,
    'createdAt': record.createdAt.toUtc().toIso8601String(),
    'lat': record.lat,
    'lng': record.lng,
    'trappedCount': record.trappedCount,
    'injuredCount': record.injuredCount,
    'vulnerableGroups': record.vulnerableGroups,
    'description': record.description,
    'aiTags': record.aiTags.map((tag) => tag.toJson()).toList(),
    'sendMode': record.sendMode,
    'status': record.status,
  };
}
