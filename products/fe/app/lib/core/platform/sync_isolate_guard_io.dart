import 'dart:async';
import 'dart:isolate';
import 'dart:ui';

const _foregroundPort = 'rescue_sync_foreground';
const _hiveOwnerPort = 'rescue_sync_hive_owner';

ReceivePort? _foregroundOwner;
ReceivePort? _foregroundRequests;
Future<void>? _foregroundAcquisition;
Future<void> _foregroundPending = Future.value();

/// Claim Hive before opening any foreground boxes, and keep the claim until all
/// writers and boxes are closed. A timeout never revokes another isolate's claim.
// shortcut: dead-isolate mappings need a restart, use native ownership if restart-free recovery is required.
Future<void> waitForBackgroundSync({
  Duration timeout = const Duration(minutes: 2),
}) {
  if (_foregroundOwner != null) return Future.value();
  return _foregroundAcquisition ??= _acquireForeground(timeout).whenComplete(
    () {
      _foregroundAcquisition = null;
    },
  );
}

Future<void> _acquireForeground(Duration timeout) async {
  final owner = ReceivePort();
  var timedOut = false;
  final timer = Timer(timeout, () => timedOut = true);
  try {
    while (!IsolateNameServer.registerPortWithName(
      owner.sendPort,
      _hiveOwnerPort,
    )) {
      if (timedOut) {
        throw TimeoutException(
          'Dữ liệu đang được đồng bộ. Hãy thử lại hoặc khởi động lại ứng dụng.',
          timeout,
        );
      }
      await Future<void>.delayed(const Duration(milliseconds: 200));
    }
    _foregroundOwner = owner;
  } catch (_) {
    owner.close();
    rethrow;
  } finally {
    timer.cancel();
  }
}

/// Register only after foreground initialization has completed. Requests are
/// serialized and acknowledged only after the requested sync has completed.
void registerForegroundSync(Future<void> Function() sync) {
  if (_foregroundOwner == null) {
    throw StateError(
      'Foreground must own Hive before accepting sync requests.',
    );
  }
  if (_foregroundRequests != null) {
    throw StateError('Foreground sync is already registered.');
  }
  final requests = ReceivePort();
  if (!IsolateNameServer.registerPortWithName(
    requests.sendPort,
    _foregroundPort,
  )) {
    requests.close();
    throw StateError('Foreground sync is owned by another isolate.');
  }
  _foregroundRequests = requests;
  requests.listen((reply) {
    if (reply is! SendPort) return;
    _foregroundPending = _foregroundPending.then((_) async {
      try {
        await sync();
        reply.send(true);
      } catch (error) {
        reply.send(error.toString());
      }
    });
  });
}

/// Stop the controller's own writers first. Never release on app pause: the
/// foreground boxes and pending requests still belong to this isolate.
Future<void> releaseForegroundSync({
  required Future<void> Function() closeHive,
}) async {
  final requests = _foregroundRequests;
  if (requests != null) {
    _removeOwnMapping(_foregroundPort, requests);
    requests.close();
    _foregroundRequests = null;
  }
  await _foregroundPending;
  // If closing fails, retain ownership instead of allowing concurrent writers.
  await closeHive();
  final owner = _foregroundOwner;
  if (owner != null) {
    _removeOwnMapping(_hiveOwnerPort, owner);
    owner.close();
    _foregroundOwner = null;
  }
}

/// False means no foreground handler exists. A failed or unanswered request is
/// an error, so callers retry later without starting a second Hive writer.
Future<bool> delegateSyncToForeground({
  Duration timeout = const Duration(minutes: 2),
}) async {
  final port = IsolateNameServer.lookupPortByName(_foregroundPort);
  if (port == null) return false;
  final reply = ReceivePort();
  try {
    port.send(reply.sendPort);
    final result = await reply.first.timeout(timeout);
    if (result != true) throw StateError('Foreground sync failed: $result');
    return true;
  } finally {
    reply.close();
  }
}

/// A busy owner asks Workmanager to retry. Atomic registration closes the race
/// between checking the foreground handler and opening background Hive boxes.
Future<bool> runBackgroundSync(
  Future<void> Function() task, {
  required Future<void> Function() closeHive,
}) async {
  final owner = ReceivePort();
  if (!IsolateNameServer.registerPortWithName(owner.sendPort, _hiveOwnerPort)) {
    owner.close();
    return false;
  }
  try {
    await task();
    return true;
  } finally {
    await closeHive();
    _removeOwnMapping(_hiveOwnerPort, owner);
    owner.close();
  }
}

void _removeOwnMapping(String name, ReceivePort port) {
  if (IsolateNameServer.lookupPortByName(name) == port.sendPort) {
    IsolateNameServer.removePortNameMapping(name);
  }
}
