import 'dart:async';
import 'dart:isolate';
import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';

import 'package:app/core/platform/sync_isolate_guard.dart';

Future<void> _closeHive() async {}

void main() {
  tearDown(() => releaseForegroundSync(closeHive: _closeHive));

  test('foreground cannot accept sync before acquiring Hive', () {
    expect(() => registerForegroundSync(_closeHive), throwsStateError);
  });

  test(
    'foreground owns Hive during initialization before registering sync',
    () async {
      await waitForBackgroundSync();
      expect(await delegateSyncToForeground(), isFalse);
      var backgroundOpenedHive = false;
      expect(
        await runBackgroundSync(
          () async => backgroundOpenedHive = true,
          closeHive: _closeHive,
        ),
        isFalse,
      );
      expect(backgroundOpenedHive, isFalse);
    },
  );

  testWidgets(
    'foreground waits beyond ten seconds until background boxes close',
    (tester) async {
      var backgroundClosed = false;
      final background = runBackgroundSync(
        () => Future<void>.delayed(const Duration(seconds: 60)),
        closeHive: () async {
          await Future<void>.delayed(const Duration(seconds: 5));
          backgroundClosed = true;
        },
      );
      var foregroundOpenedHive = false;
      var foregroundObservedClosed = false;
      final foreground = waitForBackgroundSync().then((_) {
        foregroundOpenedHive = true;
        foregroundObservedClosed = backgroundClosed;
      });

      await tester.pump(const Duration(seconds: 11));
      expect(foregroundOpenedHive, isFalse);
      var secondBackgroundOpenedHive = false;
      expect(
        await runBackgroundSync(
          () async => secondBackgroundOpenedHive = true,
          closeHive: _closeHive,
        ),
        isFalse,
      );
      expect(secondBackgroundOpenedHive, isFalse);

      await tester.pump(const Duration(seconds: 49));
      expect(foregroundOpenedHive, isFalse);
      await tester.pump(const Duration(seconds: 4));
      expect(foregroundOpenedHive, isFalse);
      await tester.pump(const Duration(seconds: 1));
      await tester.pump(const Duration(milliseconds: 200));
      expect(await background, isTrue);
      await foreground;
      expect(foregroundOpenedHive, isTrue);
      expect(foregroundObservedClosed, isTrue);
    },
  );

  test('delegated success acknowledges completed sync', () async {
    await waitForBackgroundSync();
    final started = Completer<void>();
    final finished = Completer<void>();
    registerForegroundSync(() {
      started.complete();
      return finished.future;
    });
    var acknowledged = false;
    final delegated = delegateSyncToForeground().then((value) {
      acknowledged = true;
      return value;
    });
    await started.future;
    expect(acknowledged, isFalse);
    finished.complete();
    expect(await delegated, isTrue);
  });

  test(
    'delegation timeout preserves the foreground owner and handler',
    () async {
      await waitForBackgroundSync();
      final started = Completer<void>();
      final finished = Completer<void>();
      var syncs = 0;
      registerForegroundSync(() async {
        syncs++;
        if (syncs == 1) {
          started.complete();
          await finished.future;
        }
      });
      final delegated = delegateSyncToForeground(
        timeout: const Duration(milliseconds: 20),
      );
      await started.future;
      await expectLater(delegated, throwsA(isA<TimeoutException>()));
      expect(
        await runBackgroundSync(_closeHive, closeHive: _closeHive),
        isFalse,
      );
      finished.complete();
      expect(await delegateSyncToForeground(), isTrue);
      expect(syncs, 2);
    },
  );

  test(
    'failed foreground sync does not authorize background Hive access',
    () async {
      await waitForBackgroundSync();
      registerForegroundSync(() async => throw StateError('sync failed'));
      await expectLater(delegateSyncToForeground(), throwsStateError);
      expect(
        await runBackgroundSync(_closeHive, closeHive: _closeHive),
        isFalse,
      );
    },
  );

  test(
    'stale owner times out safely and can be retried after release',
    () async {
      final staleOwner = ReceivePort();
      const ownerName = 'rescue_sync_hive_owner';
      expect(
        IsolateNameServer.registerPortWithName(staleOwner.sendPort, ownerName),
        isTrue,
      );
      try {
        await expectLater(
          waitForBackgroundSync(timeout: const Duration(milliseconds: 20)),
          throwsA(isA<TimeoutException>()),
        );
        expect(
          IsolateNameServer.lookupPortByName(ownerName),
          staleOwner.sendPort,
        );
        expect(
          await runBackgroundSync(_closeHive, closeHive: _closeHive),
          isFalse,
        );
      } finally {
        IsolateNameServer.removePortNameMapping(ownerName);
        staleOwner.close();
      }
      await waitForBackgroundSync();
    },
  );

  test(
    'failed Hive close retains ownership until a successful close',
    () async {
      await waitForBackgroundSync();
      await expectLater(
        releaseForegroundSync(
          closeHive: () async => throw StateError('close failed'),
        ),
        throwsStateError,
      );
      expect(
        await runBackgroundSync(_closeHive, closeHive: _closeHive),
        isFalse,
      );
      await releaseForegroundSync(closeHive: _closeHive);
      expect(
        await runBackgroundSync(_closeHive, closeHive: _closeHive),
        isTrue,
      );
    },
  );

  test(
    'failed background task closes Hive before another task starts',
    () async {
      var closed = false;
      await expectLater(
        runBackgroundSync(
          () async => throw StateError('upload failed'),
          closeHive: () async => closed = true,
        ),
        throwsStateError,
      );
      expect(closed, isTrue);
      expect(
        await runBackgroundSync(_closeHive, closeHive: _closeHive),
        isTrue,
      );
    },
  );
}
