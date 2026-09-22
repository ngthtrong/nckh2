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
import 'package:app/presentation/screens/main_navigation_screen.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _Location implements LocationDataSource {
  @override
  Future<LocationPoint> current() async =>
      const LocationPoint(latitude: 10, longitude: 106);
}

class _Sms implements SmsGateway {
  @override
  Future<SmsCapabilities> capabilities() async =>
      const SmsCapabilities(available: false);

  @override
  Future<SmsSendResult> sendConfirmed({
    required String reportId,
    required String recipient,
    required String idempotencyKey,
  }) async => const SmsSendResult(status: 'disabled');
}

class _Sync implements PlatformSync {
  @override
  Future<void> start(Future<void> Function() syncPending) async {}

  @override
  Future<void> dispose() async {}
}

class _Users extends UserLocalDataSource {
  @override
  Future<void> init() async {}

  @override
  User? getUser() => null;
}

class _Inference implements InferenceRepository {
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

class _Network implements NetworkRepository {
  @override
  Stream<List<ConnectivityResult>> get networkChanges => const Stream.empty();
  @override
  Future<String> getCurrentNetworkType() async => 'WiFi';
}

class _Rescue implements RescueRepository {
  @override
  Future<void> init() async {}
  @override
  List<RescueRecord> getAllRecords() => const [];
  @override
  int getPendingCount() => 0;
  @override
  Future<void> saveRecord(RescueRecord record) async {}
  @override
  Future<bool> sendRecord(RescueRecord record) async => true;
  @override
  Future<void> syncPendingRecords() async {}
}

void main() {
  testWidgets('Android system back returns from compose to the tab shell', (
    tester,
  ) async {
    final controller = AppController(
      rescueRepository: _Rescue(),
      inferenceRepository: _Inference(),
      networkRepository: _Network(),
      userLocalDataSource: _Users(),
      locationDataSource: _Location(),
      platformSync: _Sync(),
      smsGateway: _Sms(),
    )..continueAsGuest();
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(home: MainNavigationScreen(controller: controller)),
    );
    await tester.pump();
    await tester.tap(find.text('Gửi bài cứu hộ'));
    await tester.pump();
    expect(find.text('SỐ LƯỢNG NGƯỜI CẦN CỨU HỘ'), findsOneWidget);

    await tester.binding.handlePopRoute();
    await tester.pump();

    expect(find.text('Nhấn SOS để gọi cứu hộ ngay'), findsOneWidget);
  });
}
