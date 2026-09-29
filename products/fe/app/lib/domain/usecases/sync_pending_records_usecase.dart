import '../repositories/rescue_repository.dart';

class SyncPendingRecordsUseCase {
  final RescueRepository repository;

  SyncPendingRecordsUseCase(this.repository);

  Future<void> call() async {
    await repository.syncPendingRecords();
  }
}
