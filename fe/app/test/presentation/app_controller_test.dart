import 'dart:async';
import 'dart:typed_data';

import 'package:app/data/datasources/location/location_data_source.dart';
import 'package:app/data/datasources/sms/sms_gateway.dart';
import 'package:app/data/datasources/sync/platform_sync.dart';
import 'package:app/data/datasources/user_local_datasource.dart';
import 'package:app/domain/entities/ai_model_type.dart';
import 'package:app/domain/entities/ai_tag.dart';
import 'package:app/domain/entities/rescue_record.dart';
import 'package:app/domain/entities/user.dart';
import 'package:app/domain/repositories/inference_repository.dart';
import 'package:app/domain/repositories/network_repository.dart';
import 'package:app/domain/repositories/rescue_repository.dart';
import 'package:app/presentation/controllers/app_controller.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeLocationDataSource implements LocationDataSource {
  @override
  Future<LocationPoint> current() async =>
      const LocationPoint(latitude: 10.1234, longitude: 106.5678);
}

class FakePlatformSync implements PlatformSync {
  final reconnects = StreamController<void>();
  StreamSubscription<void>? _subscription;

  @override
  Future<void> start(Future<void> Function() syncPending) async {
    _subscription = reconnects.stream.listen((_) async {
      await syncPending();
    });
  }

  @override
  Future<void> dispose() async {
    await _subscription?.cancel();
  }

  Future<void> close() => reconnects.close();
}

class FakeSmsGateway implements SmsGateway {
  int sendCalls = 0;

  @override
  Future<SmsCapabilities> capabilities() async => const SmsCapabilities(
    available: true,
    recipient: '+84901234567',
    provider: 'test',
  );

  @override
  Future<SmsSendResult> sendConfirmed({
    required String reportId,
    required String recipient,
    required String idempotencyKey,
  }) async {
    sendCalls++;
    return const SmsSendResult(status: 'queued');
  }
}

class FakeRescueRepository implements RescueRepository {
  int syncCalls = 0;

  @override
  Future<void> init() async {}

  @override
  List<RescueRecord> getAllRecords() => const [];

  @override
  int getPendingCount() => 1;

  @override
  Future<void> saveRecord(RescueRecord record) async {}

  @override
  Future<bool> sendRecord(RescueRecord record) async => true;

  @override
  Future<void> syncPendingRecords() async {
    syncCalls++;
  }
}

class FakeInferenceRepository implements InferenceRepository {
  @override
  bool get ready => true;

  @override
  bool get pteReady => false;

  @override
  AiModelType get currentModel => AiModelType.onnx;

  @override
  bool get isDualComparison => false;

  @override
  ModelBenchmarkComparison? get latestComparison => null;

  @override
  Future<void> loadModel() async {}

  @override
  Future<InferenceResult?> classifyImage(Uint8List imageBytes) async => null;

  @override
  List<AiTag> generateAiTags(String? label, double? confidence) => const [];

  @override
  void setDualComparison(bool enabled) {}

  @override
  void setModel(AiModelType model) {}
}

class FakeNetworkRepository implements NetworkRepository {
  @override
  Stream<List<ConnectivityResult>> get networkChanges => const Stream.empty();

  @override
  Future<String> getCurrentNetworkType() async => 'WiFi';
}

class FakeUserLocalDataSource extends UserLocalDataSource {
  @override
  Future<void> init() async {}

  @override
  User? getUser() => null;
}

void main() {
  late FakeRescueRepository rescueRepository;
  late FakePlatformSync platformSync;
  late FakeSmsGateway smsGateway;
  late AppController controller;

  setUp(() {
    rescueRepository = FakeRescueRepository();
    platformSync = FakePlatformSync();
    smsGateway = FakeSmsGateway();
    controller = AppController(
      rescueRepository: rescueRepository,
      inferenceRepository: FakeInferenceRepository(),
      networkRepository: FakeNetworkRepository(),
      userLocalDataSource: FakeUserLocalDataSource(),
      locationDataSource: FakeLocationDataSource(),
      platformSync: platformSync,
      smsGateway: smsGateway,
    );
  });

  tearDown(() async {
    controller.dispose();
    await platformSync.close();
  });

  test(
    'initialization publishes the location returned by the platform',
    () async {
      await controller.init();

      expect(controller.currentLat, 10.1234);
      expect(controller.currentLng, 106.5678);
      expect(controller.locationLabel, contains('10.1234'));
      expect(controller.locationError, isNull);
    },
  );

  test('browser reconnect synchronizes pending rescue records', () async {
    await controller.init();

    platformSync.reconnects.add(null);
    await Future<void>.delayed(Duration.zero);

    expect(rescueRepository.syncCalls, 1);
    expect(controller.syncError, isNull);
  });

  test('SMS is sent only after explicit confirmation', () async {
    await controller.init();

    await controller.sendSos(sendSmsConfirmed: false);
    expect(smsGateway.sendCalls, 0);

    await controller.sendSos(sendSmsConfirmed: true);
    expect(smsGateway.sendCalls, 1);
  });
}
