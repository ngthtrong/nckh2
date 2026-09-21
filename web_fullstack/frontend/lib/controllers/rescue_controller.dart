import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:uuid/uuid.dart';

import '../config/app_config.dart';
import '../domain/inference_result.dart';
import '../domain/report.dart';
import '../services/offline_report_store.dart';
import '../services/report_api_client.dart';
import '../services/sync_coordinator.dart';
import '../services/web_inference_service.dart';

class RescueController extends ChangeNotifier {
  RescueController._(this.store, this.api, this.inference)
    : syncCoordinator = SyncCoordinator(store: store, uploader: api);

  static Future<RescueController> create() async {
    final store = await OfflineReportStore.initialize();
    return RescueController._(
      store,
      ReportApiClient(AppConfig.apiBaseUrl),
      WebInferenceService(),
    );
  }

  final OfflineReportStore store;
  final ReportApiClient api;
  final WebInferenceService inference;
  final SyncCoordinator syncCoordinator;
  final _picker = ImagePicker();
  final _uuid = const Uuid();

  List<RescueReport> reports = const [];
  Map<String, dynamic> capabilities = const {};
  Uint8List? imageBytes;
  String? imageName;
  String? imageMimeType;
  InferenceResult? inferenceResult;
  Position? position;
  bool initializing = true;
  bool analyzing = false;
  bool submitting = false;
  String? message;

  bool get smsEnabled => capabilities['sms'] == true;
  bool get backendAvailable => capabilities.isNotEmpty;

  Future<void> initialize() async {
    initializing = true;
    notifyListeners();
    try {
      reports = await store.listAll();
      try {
        capabilities = await api.capabilities();
        await syncCoordinator.syncPending();
        reports = await store.listAll();
      } catch (_) {
        capabilities = const {};
      }
      try {
        await inference.initialize();
      } catch (error) {
        message = error.toString();
      }
    } finally {
      initializing = false;
      notifyListeners();
    }
  }

  Future<void> pickImage(ImageSource source) async {
    final file = await _picker.pickImage(source: source, imageQuality: 95);
    if (file == null) return;
    imageBytes = await file.readAsBytes();
    imageName = file.name;
    imageMimeType = _mimeForName(file.name);
    inferenceResult = null;
    analyzing = true;
    message = null;
    notifyListeners();
    try {
      inferenceResult = await inference.analyze(imageBytes!);
    } catch (error) {
      message = error.toString();
    } finally {
      analyzing = false;
      notifyListeners();
    }
  }

  Future<void> locate() async {
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      message = 'Chrome chưa được cấp quyền vị trí.';
    } else {
      position = await Geolocator.getCurrentPosition();
      message = 'Đã lấy vị trí hiện tại.';
    }
    notifyListeners();
  }

  Future<void> submit({
    required String description,
    required int trappedCount,
    required int injuredCount,
  }) async {
    submitting = true;
    message = null;
    notifyListeners();
    final report = RescueReport(
      id: _uuid.v4(),
      createdAt: DateTime.now().toUtc(),
      description: description.trim(),
      trappedCount: trappedCount,
      injuredCount: injuredCount,
      aiLabel: inferenceResult?.label,
      aiConfidence: inferenceResult?.confidence,
      latitude: position?.latitude,
      longitude: position?.longitude,
      imageBytes: imageBytes,
      imageName: imageName,
      imageMimeType: imageMimeType,
    );
    await store.save(report);
    reports = await store.listAll();
    notifyListeners();
    await syncCoordinator.syncPending();
    reports = await store.listAll();
    imageBytes = null;
    imageName = null;
    imageMimeType = null;
    inferenceResult = null;
    submitting = false;
    message = reports.firstWhere((item) => item.id == report.id).syncState == SyncState.synced
        ? 'Báo cáo đã được gửi.'
        : 'Đã lưu báo cáo. Ứng dụng sẽ gửi lại khi có mạng.';
    notifyListeners();
  }

  Future<void> retrySync() async {
    await syncCoordinator.syncPending();
    reports = await store.listAll();
    notifyListeners();
  }

  Future<void> sendSms(RescueReport report, String recipient) async {
    final result = await api.requestSms(
      reportId: report.id,
      recipient: recipient,
      idempotencyKey: _uuid.v4(),
    );
    message = 'SMS: ${result['status'] ?? 'đã tiếp nhận'}';
    notifyListeners();
  }
}

String _mimeForName(String name) {
  final lower = name.toLowerCase();
  if (lower.endsWith('.png')) return 'image/png';
  if (lower.endsWith('.webp')) return 'image/webp';
  return 'image/jpeg';
}
