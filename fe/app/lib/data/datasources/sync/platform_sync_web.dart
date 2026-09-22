import 'dart:async';

import 'browser_online_events_web.dart';
import 'platform_sync.dart';

PlatformSync createPlatformSync() => WebPlatformSync();

class WebPlatformSync implements PlatformSync {
  WebPlatformSync({Stream<void>? onlineEvents})
    : _onlineEvents = onlineEvents ?? browserOnlineEvents();

  final Stream<void> _onlineEvents;
  StreamSubscription<void>? _subscription;

  @override
  Future<void> start(Future<void> Function() syncPending) async {
    await _subscription?.cancel();
    _subscription = _onlineEvents.listen((_) async {
      await syncPending();
    });
    await syncPending();
  }

  @override
  Future<void> dispose() async {
    await _subscription?.cancel();
    _subscription = null;
  }
}
