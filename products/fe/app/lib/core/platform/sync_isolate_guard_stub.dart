/// Bản cho web: không có tác vụ nền, không cần phối hợp.
Future<void> waitForBackgroundSync({
  Duration timeout = const Duration(minutes: 2),
}) async {}

void registerForegroundSync(Future<void> Function() sync) {}

Future<void> releaseForegroundSync({
  required Future<void> Function() closeHive,
}) => closeHive();

Future<bool> delegateSyncToForeground({
  Duration timeout = const Duration(minutes: 2),
}) async => false;

Future<bool> runBackgroundSync(
  Future<void> Function() task, {
  required Future<void> Function() closeHive,
}) async {
  try {
    await task();
    return true;
  } finally {
    await closeHive();
  }
}
