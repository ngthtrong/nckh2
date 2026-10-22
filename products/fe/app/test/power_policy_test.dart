import 'dart:async';

import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/core/platform/background_sync_schedule.dart';
import 'package:app/domain/repositories/inference_repository.dart';
import 'package:app/domain/repositories/network_repository.dart';
import 'package:app/domain/repositories/rescue_repository.dart';
import 'package:app/domain/services/sync_activity.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:workmanager/workmanager.dart';

RescueRecord record({
  String status = 'processing',
  bool synced = true,
  String? syncError,
}) => RescueRecord(
  id: 'r1',
  createdAt: DateTime(2026),
  lat: null,
  lng: null,
  sendMode: 'textOnly',
  status: status,
  synced: synced,
  syncError: syncError,
);

class Rescue extends Fake implements RescueRepository {
  List<RescueRecord> saved = [record()];
  int polls = 0;
  int syncs = 0;
  @override
  List<RescueRecord> getAllRecords() => saved;
  @override
  Future<List<RescueRecord>> refreshStatuses() async {
    polls++;
    return [];
  }

  @override
  Future<void> syncPendingRecords({bool immediate = true}) async {
    syncs++;
  }

  DateTime? retryAt;
  @override
  DateTime? get nextRetryAt => retryAt;
  @override
  Future<bool> reconnectServer({bool force = false}) async => true;
}

class Inference extends Fake implements InferenceRepository {
  int loads = 0;
  bool loaded = false;
  Completer<void>? pending;
  @override
  bool get ready => loaded;
  @override
  bool get pteReady => loaded;
  @override
  Future<void> loadModel() async {
    loads++;
    if (pending != null) await pending!.future;
    loaded = true;
  }
}

class Network extends Fake implements NetworkRepository {}

class Scheduler extends WorkmanagerPlatform {
  final calls = <String>[];
  @override
  Future<void> registerPeriodicTask(
    String uniqueName,
    String taskName, {
    Duration? frequency,
    Duration? flexInterval,
    Map<String, dynamic>? inputData,
    Duration? initialDelay,
    Constraints? constraints,
    ExistingPeriodicWorkPolicy? existingWorkPolicy,
    BackoffPolicy? backoffPolicy,
    Duration? backoffPolicyDelay,
    String? tag,
    ForegroundServiceConfig? foregroundServiceConfig,
  }) async {
    expect(uniqueName, backgroundSyncName);
    expect(frequency, const Duration(minutes: 15));
    expect(existingWorkPolicy, ExistingPeriodicWorkPolicy.keep);
    expect(constraints?.networkType, NetworkType.connected);
    calls.add('keep');
  }

  @override
  Future<void> cancelByUniqueName(String uniqueName) async {
    expect(uniqueName, backgroundSyncName);
    calls.add('cancel');
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  testWidgets(
    'pending attachment retries without outbox messages and stops when done',
    (tester) async {
      final rescue = Rescue()
        ..saved = [
          record(
            status: 'resolved',
            synced: false,
          ).copyWith(metadataSynced: true, imagePath: 'attachment.jpg'),
        ];
      final controller = AppController(
        rescueRepository: rescue,
        inferenceRepository: Inference(),
        networkRepository: Network(),
      );
      addTearDown(controller.dispose);
      await controller.syncPending();
      expect(rescue.retryAt, isNull);
      await tester.pump(const Duration(seconds: 29));
      expect(rescue.syncs, 1);
      await tester.pump(const Duration(milliseconds: 1100));
      expect(rescue.syncs, 2);
      controller.didChangeAppLifecycleState(AppLifecycleState.paused);
      await tester.pump(const Duration(minutes: 2));
      expect(rescue.syncs, 2);
      rescue.saved = [record(status: 'resolved')];
      controller.didChangeAppLifecycleState(AppLifecycleState.resumed);
      await controller.syncPending();
      await tester.pump(const Duration(minutes: 2));
      expect(rescue.syncs, 3);
    },
  );
  testWidgets(
    'overdue outbox waits 30 seconds and stops retrying while offline',
    (tester) async {
      final rescue = Rescue()..retryAt = DateTime(2020);
      final controller = AppController(
        rescueRepository: rescue,
        inferenceRepository: Inference(),
        networkRepository: Network(),
      );
      addTearDown(controller.dispose);
      await controller.syncPending();
      expect(rescue.syncs, 1);
      await tester.pump(const Duration(seconds: 29));
      expect(rescue.syncs, 1);
      await tester.pump(const Duration(seconds: 1));
      expect(rescue.syncs, 2);
      controller.networkLabel = 'none';
      controller.didChangeAppLifecycleState(AppLifecycleState.resumed);
      await tester.pump(const Duration(minutes: 2));
      expect(rescue.syncs, 2);
    },
  );
  test(
    'register, retain, cancel, and rearm the unique background schedule',
    () async {
      final previous = WorkmanagerPlatform.instance;
      final scheduler = Scheduler();
      WorkmanagerPlatform.instance = scheduler;
      debugDefaultTargetPlatformOverride = TargetPlatform.android;
      addTearDown(() {
        WorkmanagerPlatform.instance = previous;
        debugDefaultTargetPlatformOverride = null;
      });
      await updateBackgroundSync(hasSyncWork([record()]));
      await updateBackgroundSync(hasSyncWork([record(status: 'dispatched')]));
      await updateBackgroundSync(hasSyncWork([record(status: 'resolved')]));
      await updateBackgroundSync(hasSyncWork([record(synced: false)]));
      expect(scheduler.calls, ['keep', 'keep', 'cancel', 'keep']);
    },
  );
  test(
    'background schedule remains needed for dispatched reports or pending images',
    () {
      expect(hasSyncWork([]), isFalse);
      expect(hasSyncWork([record()]), isTrue);
      expect(hasSyncWork([record(status: 'dispatched')]), isTrue);
      expect(hasSyncWork([record(status: 'resolved')]), isFalse);
      expect(hasSyncWork([record(status: 'cancelled')]), isFalse);
      expect(hasSyncWork([record(status: 'resolved', synced: false)]), isTrue);
      expect(
        hasSyncWork([record(synced: false, syncError: 'REJECTED')]),
        isFalse,
      );
    },
  );

  testWidgets(
    'polling changes 60/15 seconds, pauses in background, refreshes on resume',
    (tester) async {
      final rescue = Rescue();
      final controller = AppController(
        rescueRepository: rescue,
        inferenceRepository: Inference(),
        networkRepository: Network(),
      );
      addTearDown(controller.dispose);
      await controller.refreshStatuses();
      expect(rescue.polls, 1);
      await tester.pump(const Duration(seconds: 59));
      expect(rescue.polls, 1);
      await tester.pump(const Duration(seconds: 1));
      expect(rescue.polls, 2);
      controller.setWatchingStatus(true);
      await tester.pump(const Duration(seconds: 15));
      expect(rescue.polls, 3);
      controller.didChangeAppLifecycleState(AppLifecycleState.paused);
      await tester.pump(const Duration(minutes: 2));
      expect(rescue.polls, 3);
      controller.didChangeAppLifecycleState(AppLifecycleState.resumed);
      await tester.pump();
      expect(rescue.syncs, 1);
      expect(rescue.polls, 4);
      rescue.saved = [record(status: 'resolved')];
      await controller.refreshStatuses();
      await tester.pump(const Duration(minutes: 2));
      expect(rescue.polls, 5);
    },
  );

  testWidgets(
    'PTE is loaded once on demand, concurrent requests share the load',
    (tester) async {
      final inference = Inference()..pending = Completer<void>();
      final controller = AppController(
        rescueRepository: Rescue(),
        inferenceRepository: inference,
        networkRepository: Network(),
      );
      addTearDown(controller.dispose);
      expect(inference.loads, 0);
      final first = controller.ensureModelLoaded();
      final second = controller.ensureModelLoaded();
      expect(inference.loads, 1);
      inference.pending!.complete();
      await Future.wait([first, second]);
      await controller.ensureModelLoaded();
      expect(inference.loads, 1);
      expect(controller.isModelLoading, isFalse);
      expect(controller.isPteReady, isTrue);
    },
  );
}
