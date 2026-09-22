import 'dart:async';

import 'package:app/data/datasources/sync/serialized_sync_runner.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'concurrent browser online events share one synchronization run',
    () async {
      final firstRunStarted = Completer<void>();
      final finishFirstRun = Completer<void>();
      var calls = 0;
      final runner = SerializedSyncRunner();

      Future<void> synchronize() async {
        calls++;
        if (calls == 1) {
          firstRunStarted.complete();
          await finishFirstRun.future;
        }
      }

      final start = runner.run(synchronize);

      await firstRunStarted.future;
      final reconnect1 = runner.run(synchronize);
      final reconnect2 = runner.run(synchronize);
      await Future<void>.delayed(Duration.zero);
      expect(calls, 1);

      finishFirstRun.complete();
      await Future.wait([start, reconnect1, reconnect2]);
      expect(calls, 2);
    },
  );
}
