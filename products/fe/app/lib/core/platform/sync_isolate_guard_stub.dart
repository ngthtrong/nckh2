/// Bản cho web: không có tác vụ nền, không cần phối hợp.
Future<void> waitForBackgroundSync({
  Duration timeout = const Duration(seconds: 10),
}) async {}

void registerForegroundSync(Future<void> Function() sync) {}

Future<bool> delegateSyncToForeground({
  Duration timeout = const Duration(seconds: 3),
}) async => false;

Future<void> runBackgroundSync(Future<void> Function() task) => task();
