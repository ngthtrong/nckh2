import 'package:flutter/foundation.dart';
import 'package:workmanager/workmanager.dart';

const backgroundSyncName = 'rescue-outbox-sync';

Future<void> updateBackgroundSync(bool needed) async {
  if (kIsWeb ||
      (defaultTargetPlatform != TargetPlatform.android &&
          defaultTargetPlatform != TargetPlatform.iOS)) {
    return;
  }
  try {
    if (needed) {
      await Workmanager().registerPeriodicTask(
        backgroundSyncName,
        'syncPendingMessages',
        frequency: const Duration(minutes: 15),
        existingWorkPolicy: ExistingPeriodicWorkPolicy.keep,
        constraints: Constraints(networkType: NetworkType.connected),
      );
    } else {
      await Workmanager().cancelByUniqueName(backgroundSyncName);
    }
  } catch (error) {
    // Scheduling failure must not block a report already saved locally.
    debugPrint('Không cập nhật được lịch đồng bộ nền: $error');
  }
}
