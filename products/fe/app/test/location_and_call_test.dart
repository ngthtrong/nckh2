import 'dart:async';

import 'package:app/domain/repositories/inference_repository.dart';
import 'package:app/domain/repositories/network_repository.dart';
import 'package:app/domain/repositories/rescue_repository.dart';
import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/domain/entities/user.dart';
import 'package:app/data/models/rescue_record_payload.dart';
import 'package:app/data/datasources/sender_remote_datasource.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:app/presentation/widgets/emergency_call.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:geolocator/geolocator.dart';

class _Inference extends Fake implements InferenceRepository {}

class _Network extends Fake implements NetworkRepository {
  @override
  Future<String> getCurrentNetworkType() async => 'WiFi';
}

class _Rescue extends Fake implements RescueRepository {
  RescueRecord? stored;
  @override
  List<RescueRecord> getAllRecords() => [?stored];
  @override
  RescueRecord? getRecord(String id) => stored?.id == id ? stored : null;
  @override
  DateTime? get nextRetryAt => null;
  @override
  Future<void> saveRecord(RescueRecord record, {bool preparing = false}) async {
    stored = record;
  }

  @override
  Future<void> queueRecord(RescueRecord record) async {}
  @override
  Future<RescueRecord> sendRecord(RescueRecord record) async {
    stored = record.copyWith(metadataSynced: true, synced: true);
    return stored!;
  }

  @override
  Future<void> syncPendingRecords({bool immediate = true}) async {
    stored = stored?.copyWith(metadataSynced: true, synced: true);
  }

  @override
  Future<List<RescueRecord>> refreshStatuses() async => [];
}

class _Location extends GeolocatorPlatform {
  Future<Position> Function() read = () async => _position(10);
  LocationPermission permission = LocationPermission.whileInUse;
  LocationPermission grant = LocationPermission.whileInUse;
  bool enabled = true;
  int requests = 0, appSettings = 0, locationSettings = 0;
  @override
  Future<LocationPermission> checkPermission() async => permission;
  @override
  Future<LocationPermission> requestPermission() async {
    requests++;
    return permission = grant;
  }

  @override
  Future<bool> isLocationServiceEnabled() async => enabled;
  @override
  Future<bool> openAppSettings() async {
    appSettings++;
    return true;
  }

  @override
  Future<bool> openLocationSettings() async {
    locationSettings++;
    return true;
  }

  @override
  Future<Position> getCurrentPosition({LocationSettings? locationSettings}) =>
      read();
}

Position _position(double latitude, {double accuracy = 1}) => Position(
  longitude: 106,
  latitude: latitude,
  timestamp: DateTime.now(),
  accuracy: accuracy,
  altitude: 0,
  altitudeAccuracy: 1,
  heading: 0,
  headingAccuracy: 1,
  speed: 0,
  speedAccuracy: 1,
);

void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'denied GPS never blocks SOS; recovery requests permission and keeps accuracy',
    () async {
      final original = GeolocatorPlatform.instance;
      final location = _Location()..permission = LocationPermission.denied;
      GeolocatorPlatform.instance = location;
      addTearDown(() => GeolocatorPlatform.instance = original);
      final rescue = _Rescue();
      final controller = AppController(
        rescueRepository: rescue,
        inferenceRepository: _Inference(),
        networkRepository: _Network(),
      );
      addTearDown(controller.dispose);
      final sos = await controller.sendSos();
      expect(sos?.synced, isTrue);
      expect(sos?.lat, isNull);
      expect(location.requests, 0);
      expect(controller.locationLabel, contains('Chưa cấp quyền'));

      location.read = () async => _position(10, accuracy: 2000);
      await controller.recoverLocation();
      expect(location.requests, 1);
      expect(controller.locationLabel, contains('±2000 m'));
      expect(controller.locationLabel, contains('vị trí gần đúng'));
      final post = await controller.submitPost(
        trappedCount: 1,
        injuredCount: 0,
        vulnerableGroups: [],
        cannotMove: false,
        severeSigns: [],
        description: 'Cần cứu hộ',
        imagePath: null,
        aiTags: [],
      );
      expect(post?.locationAccuracyMeters, 2000);
      expect(rescueRecordPayload(post!)['locationAccuracyMeters'], 2000);
      expect(smsBody(post), contains('|acc:2000'));
      expect(post.locationText, contains('vị trí gần đúng'));
    },
  );

  test('blocked permission and disabled GPS open the right settings', () async {
    final original = GeolocatorPlatform.instance;
    final location = _Location()..permission = LocationPermission.deniedForever;
    GeolocatorPlatform.instance = location;
    addTearDown(() => GeolocatorPlatform.instance = original);
    final controller = AppController(
      rescueRepository: _Rescue(),
      inferenceRepository: _Inference(),
      networkRepository: _Network(),
    );
    addTearDown(controller.dispose);
    await controller.refreshLocation(requestPermission: true);
    expect(controller.currentLat, isNull);
    expect(controller.locationLabel, contains('bị chặn'));
    await controller.recoverLocation();
    expect(location.appSettings, 1);
    expect(location.requests, 0);
    location.permission = LocationPermission.denied;
    location.grant = LocationPermission.deniedForever;
    await controller.recoverLocation();
    expect(location.requests, 1);
    expect(location.appSettings, 2);
    location.permission = LocationPermission.whileInUse;
    location.enabled = false;
    await controller.recoverLocation();
    expect(location.locationSettings, 1);
  });

  test(
    'controller snapshots profile phone for SOS and ordinary reports',
    () async {
      final original = GeolocatorPlatform.instance;
      GeolocatorPlatform.instance = _Location();
      addTearDown(() => GeolocatorPlatform.instance = original);
      final rescue = _Rescue();
      final controller =
          AppController(
              rescueRepository: rescue,
              inferenceRepository: _Inference(),
              networkRepository: _Network(),
            )
            ..currentUser = User(
              username: 'local',
              phone: '0900000000',
              address: 'Local',
              passwordHash: 'not-used',
            );
      addTearDown(controller.dispose);
      final sos = await controller.sendSos();
      expect(sos?.contactPhone, '0900000000');
      final post = await controller.submitPost(
        trappedCount: 1,
        injuredCount: 0,
        vulnerableGroups: [],
        cannotMove: false,
        severeSigns: [],
        description: 'Cần cứu hộ',
        imagePath: null,
        aiTags: [],
      );
      expect(post?.contactPhone, '0900000000');
      controller.currentUser = null;
      expect(sos?.contactPhone, '0900000000');
      expect(rescue.stored?.contactPhone, '0900000000');
    },
  );

  test(
    'unreadable photo exposes an actionable error without saving a report',
    () async {
      final original = GeolocatorPlatform.instance;
      GeolocatorPlatform.instance = _Location();
      addTearDown(() => GeolocatorPlatform.instance = original);
      final rescue = _Rescue();
      final controller = AppController(
        rescueRepository: rescue,
        inferenceRepository: _Inference(),
        networkRepository: _Network(),
      );
      addTearDown(controller.dispose);
      final result = await controller.submitPost(
        trappedCount: 1,
        injuredCount: 0,
        vulnerableGroups: [],
        cannotMove: false,
        severeSigns: [],
        description: 'Cần cứu hộ',
        imagePath: 'missing-image.jpg',
        aiTags: [],
      );
      expect(result, isNull);
      expect(rescue.stored, isNull);
      expect(controller.submissionError, contains('bỏ ảnh hoặc chọn lại'));
      expect(controller.isBusy, isFalse);
    },
  );
  test(
    'data ACK refreshes submitted screen even when processing status is unchanged',
    () async {
      final rescue = _Rescue()
        ..stored = RescueRecord(
          id: 'post-1',
          createdAt: DateTime.now(),
          lat: null,
          lng: null,
          sendMode: 'queuedOffline',
        );
      final controller = AppController(
        rescueRepository: rescue,
        inferenceRepository: _Inference(),
        networkRepository: _Network(),
      );
      addTearDown(controller.dispose);
      controller.lastSubmittedPost = rescue.stored;
      await controller.syncPending();
      expect(controller.lastSubmittedPost?.synced, isTrue);
      expect(controller.lastSubmittedPost?.status, 'processing');
    },
  );

  test(
    'failed GPS clears old position; older request cannot replace newer GPS',
    () async {
      final original = GeolocatorPlatform.instance;
      final location = _Location();
      GeolocatorPlatform.instance = location;
      addTearDown(() => GeolocatorPlatform.instance = original);
      final controller = AppController(
        rescueRepository: _Rescue(),
        inferenceRepository: _Inference(),
        networkRepository: _Network(),
      );
      addTearDown(controller.dispose);
      await controller.refreshLocation();
      expect(controller.currentLat, 10);
      location.read = () async => throw StateError('GPS unavailable');
      await controller.refreshLocation();
      expect(controller.currentLat, isNull);
      expect(controller.currentLng, isNull);
      final old = Completer<Position>();
      location.read = () => old.future;
      final oldRequest = controller.refreshLocation();
      location.read = () async => _position(11);
      await controller.refreshLocation();
      old.complete(_position(99));
      await oldRequest;
      expect(controller.currentLat, 11);
    },
  );

  testWidgets('dialer opens directly and a launch failure shows the number', (
    tester,
  ) async {
    final calls = <MethodCall>[];
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      const MethodChannel('plugins.flutter.io/url_launcher'),
      (call) async {
        calls.add(call);
        return false;
      },
    );
    addTearDown(
      () => binding.defaultBinaryMessenger.setMockMethodCallHandler(
        const MethodChannel('plugins.flutter.io/url_launcher'),
        null,
      ),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Builder(
            builder: (context) => TextButton(
              onPressed: () => openEmergencyDialer(context, '112'),
              child: const Text('Call'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Call'));
    await tester.pump();
    expect(calls.map((call) => call.method), ['launch']);
    expect(
      find.text('Không mở được trình gọi. Hãy gọi trực tiếp 112.'),
      findsOneWidget,
    );
  });
}
