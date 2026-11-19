import '../repositories/rescue_repository.dart';

class SyncPendingRecordsUseCase {
  final RescueRepository repository;

  SyncPendingRecordsUseCase(this.repository);

  Future<void> call({bool immediate = true}) async {
    await repository.syncPendingRecords(immediate: immediate);
  }
}
