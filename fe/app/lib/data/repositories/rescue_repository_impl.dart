import '../../domain/entities/rescue_record.dart';
import '../../domain/repositories/rescue_repository.dart';
import '../datasources/record_local_datasource.dart';
import '../datasources/sender_remote_datasource.dart';

class RescueRepositoryImpl implements RescueRepository {
  final RecordLocalDataSource localDataSource;
  final SenderRemoteDataSource senderDataSource;

  RescueRepositoryImpl({
    required this.localDataSource,
    required this.senderDataSource,
  });

  @override
  Future<void> init() async {
    await localDataSource.init();
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
    final result = await senderDataSource.upload(record, record.image?.bytes);
    if (result.ok) {
      return true;
    }
    await saveRecord(
      record.copyWith(
        synced: false,
        status: 'pending',
        lastError: result.error ?? 'Không thể gửi báo cáo.',
      ),
    );
    return false;
  }

  @override
  Future<void> syncPendingRecords() async {
    final pending = getAllRecords().where(
      (r) => !r.synced || r.status == 'pending',
    );
    for (final record in pending) {
      final success = await sendRecord(record);
      if (success) {
        await saveRecord(
          record.copyWith(synced: true, status: 'dispatched', lastError: null),
        );
      }
    }
  }
}
