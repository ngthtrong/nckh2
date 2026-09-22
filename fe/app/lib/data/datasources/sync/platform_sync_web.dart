import 'dart:async';

import 'browser_online_events_web.dart';
import 'platform_sync.dart';
import 'serialized_sync_runner.dart';

PlatformSync createPlatformSync() => WebPlatformSync();

class WebPlatformSync implements PlatformSync {
  WebPlatformSync({Stream<void>? onlineEvents})
    : _onlineEvents = onlineEvents ?? browserOnlineEvents();

  final Stream<void> _onlineEvents;
  StreamSubscription<void>? _subscription;
  final SerializedSyncRunner _syncRunner = SerializedSyncRunner();

  @override
  Future<void> start(Future<void> Function() syncPending) async {
    await _subscription?.cancel();
    _subscription = _onlineEvents.listen((_) {
      unawaited(_syncRunner.run(syncPending));
    });
    await _syncRunner.run(syncPending);
  }

  @override
  Future<void> dispose() async {
    await _subscription?.cancel();
    _subscription = null;
    await _syncRunner.waitForIdle();
  }
}
