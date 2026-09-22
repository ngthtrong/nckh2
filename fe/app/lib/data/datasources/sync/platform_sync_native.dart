import 'package:flutter/foundation.dart';
import 'package:workmanager/workmanager.dart';

import '../../repositories/rescue_repository_impl.dart';
import '../record_local_datasource.dart';
import '../sender_remote_datasource.dart';
import 'platform_sync.dart';

const _uniqueSyncName = 'rescue-pending-sync';
const _syncTaskName = 'syncPendingRecords';

@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    final local = RecordLocalDataSource();
    final sender = SenderRemoteDataSource();
    final repository = RescueRepositoryImpl(
      localDataSource: local,
      senderDataSource: sender,
    );
    await repository.init();
    await repository.syncPendingRecords();
    return true;
  });
}

PlatformSync createPlatformSync() => NativePlatformSync();

class NativePlatformSync implements PlatformSync {
  @override
  Future<void> start(Future<void> Function() syncPending) async {
    if (defaultTargetPlatform == TargetPlatform.android) {
      await Workmanager().initialize(callbackDispatcher);
      await Workmanager().registerPeriodicTask(
        _uniqueSyncName,
        _syncTaskName,
        frequency: const Duration(minutes: 15),
        existingWorkPolicy: ExistingPeriodicWorkPolicy.keep,
        constraints: Constraints(networkType: NetworkType.connected),
      );
    }
    await syncPending();
  }

  @override
  Future<void> dispose() async {}
}
