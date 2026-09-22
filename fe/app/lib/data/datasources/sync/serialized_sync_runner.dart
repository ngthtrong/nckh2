class SerializedSyncRunner {
  Future<void>? _activeRun;
  bool _rerunRequested = false;

  Future<void> run(Future<void> Function() syncPending) {
    final active = _activeRun;
    if (active != null) {
      _rerunRequested = true;
      return active;
    }

    final run = _drain(syncPending);
    _activeRun = run;
    return run.whenComplete(() {
      if (identical(_activeRun, run)) _activeRun = null;
    });
  }

  Future<void> waitForIdle() async => _activeRun;

  Future<void> _drain(Future<void> Function() syncPending) async {
    do {
      _rerunRequested = false;
      await syncPending();
    } while (_rerunRequested);
  }
}
