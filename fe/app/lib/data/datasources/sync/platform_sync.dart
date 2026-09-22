abstract interface class PlatformSync {
  Future<void> start(Future<void> Function() syncPending);
  Future<void> dispose();
}
