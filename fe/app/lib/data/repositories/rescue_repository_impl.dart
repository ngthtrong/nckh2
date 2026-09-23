import 'dart:convert';

import 'package:dio/dio.dart';

import '../../domain/entities/rescue_record.dart';
import '../../domain/repositories/rescue_repository.dart';
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

  RescueRepositoryImpl({
    required this.localDataSource,
    required this.senderDataSource,
    OutboxLocalDataSource? outboxDataSource,
    SyncRemoteDataSource? syncDataSource,
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
    if (!outboxDataSource.ready) await outboxDataSource.init();
    await _enqueue(record);
    await _flushOutbox();
    final success = await _finishAttachment(record);
    if (!success) {
      await saveRecord(
        record.copyWith(
          synced: false,
          status: 'pending',
          lastError: 'Không thể gửi báo cáo.',
        ),
      );
    }
    return success;
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
    final image = record.image;
    if (image == null || image.bytes.isEmpty) return true;
    return (await senderDataSource.upload(record, image.bytes)).ok;
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
