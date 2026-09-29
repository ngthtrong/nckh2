import 'dart:async';
import 'dart:isolate';
import 'dart:ui';

import 'package:flutter/foundation.dart';

const _foregroundPort = 'rescue_sync_foreground';
const _backgroundPort = 'rescue_sync_background';

/// App đang mở: chờ tác vụ nền (nếu đang chạy) xong rồi mới mở Hive. Quá [timeout]
/// thì vẫn mở để người dùng gửi được SOS (tên cổng có thể còn sót khi tác vụ nền bị
/// hệ điều hành giết giữa chừng).
Future<void> waitForBackgroundSync({
  Duration timeout = const Duration(seconds: 10),
}) async {
  final deadline = DateTime.now().add(timeout);
  while (IsolateNameServer.lookupPortByName(_backgroundPort) != null) {
    if (DateTime.now().isAfter(deadline)) {
      debugPrint('Tác vụ đồng bộ nền chưa xong sau $timeout, vẫn mở dữ liệu.');
      IsolateNameServer.removePortNameMapping(_backgroundPort);
      return;
    }
    await Future<void>.delayed(const Duration(milliseconds: 200));
  }
}

/// App đang mở nhận yêu cầu đồng bộ từ tác vụ nền (chạy [sync] trên isolate UI).
void registerForegroundSync(Future<void> Function() sync) {
  final port = ReceivePort();
  IsolateNameServer.removePortNameMapping(_foregroundPort);
  IsolateNameServer.registerPortWithName(port.sendPort, _foregroundPort);
  port.listen((reply) {
    if (reply is SendPort) reply.send(true);
    unawaited(sync());
  });
}

/// Tác vụ nền: app đang mở thì nhờ app đồng bộ (true), không tự mở Hive. App không
/// trả lời (isolate UI đã bị hủy nhưng tên cổng còn trong process) thì tự chạy (false).
Future<bool> delegateSyncToForeground({
  Duration timeout = const Duration(seconds: 3),
}) async {
  final port = IsolateNameServer.lookupPortByName(_foregroundPort);
  if (port == null) return false;
  final reply = ReceivePort();
  try {
    port.send(reply.sendPort);
    await reply.first.timeout(timeout);
    return true;
  } on TimeoutException {
    IsolateNameServer.removePortNameMapping(_foregroundPort);
    return false;
  } finally {
    reply.close();
  }
}

/// Tác vụ nền tự đồng bộ; giữ tên cổng trong lúc chạy để app mở lên thì chờ.
Future<void> runBackgroundSync(Future<void> Function() task) async {
  final port = ReceivePort();
  IsolateNameServer.registerPortWithName(port.sendPort, _backgroundPort);
  try {
    await task();
  } finally {
    IsolateNameServer.removePortNameMapping(_backgroundPort);
    port.close();
  }
}
