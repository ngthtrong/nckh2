import 'dart:async';
import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:uuid/uuid.dart';
import 'package:workmanager/workmanager.dart';

import 'background_sync.dart';
import 'config.dart';
import 'models/rescue_record.dart';
import 'send_mode.dart';
import 'services/inference_service.dart';
import 'services/network_service.dart';
import 'services/record_store.dart';
import 'services/sender_service.dart';

/// Entry-point cho background isolate (workmanager).
@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    await BackgroundSync.perform();
    return true;
  });
}

/// Bộ điều phối trung tâm: chụp → inference → GPS → quyết định gửi → metrics.
class AppController extends ChangeNotifier {
  final RecordStore _store = RecordStore();
  final InferenceService _inference = InferenceService();
  final NetworkService _network = NetworkService();
  final SenderService _sender = SenderService();
  final ImagePicker _picker = ImagePicker();
  final Uuid _uuid = const Uuid();

  StreamSubscription<List<ConnectivityResult>>? _connSub;
  bool busy = false;
  String netLabel = '?';
  bool modelReady = false;
  String note = '';
  String? lastMessage;

  bool get storeReady => _store.ready;
  List<RescueRecord> get records => _store.all;
  int get pendingCount => _store.pendingCount;

  Future<void> init() async {
    await _store.init();
    // Model nạp nền sau frame đầu — UI hiện ngay (load nhanh).
    unawaited(_inference.load().then((_) {
      modelReady = _inference.ready;
      notifyListeners();
    }));

    // Xin quyền vị trí (khi dùng app) — SMS xin tại thời điểm gửi.
    unawaited(Permission.locationWhenInUse.request());

    // Event-driven: chỉ phản ứng khi trạng thái mạng ĐỔI (không poll — pin).
    _connSub = _network.changes.listen((results) async {
      netLabel = _network.typeName(results);
      notifyListeners();
      final hasNet = results.any((e) =>
          e == ConnectivityResult.wifi || e == ConnectivityResult.mobile);
      if (hasNet && _store.pendingCount > 0) await syncAll();
    });
    netLabel = await _network.currentTypeName();

    // Sync nền cả khi app đóng (mỗi 15 phút, chỉ khi có mạng).
    await Workmanager().initialize(callbackDispatcher);
    await Workmanager().registerPeriodicTask(
      'rescue-periodic-sync',
      'rescueSync',
      frequency: const Duration(minutes: 15),
      constraints: Constraints(networkType: NetworkType.connected),
      existingWorkPolicy: ExistingPeriodicWorkPolicy.keep,
    );

    notifyListeners();
  }

  @override
  void dispose() {
    _connSub?.cancel();
    super.dispose();
  }

  /// Luồng chính: bấm SOS → chụp → nhận diện on-device → GPS → gửi.
  Future<void> sos() async {
    if (busy || !_store.ready) return;
    busy = true;
    notifyListeners();
    try {
      final picked = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1600,
        maxHeight: 1600,
        imageQuality: 85,
      );
      if (picked == null) return;
      final bytes = await File(picked.path).readAsBytes();
      final originalLen = bytes.length;

      // Copy bền — ảnh temp của picker có thể bị xoá trước khi sync.
      final support = await getApplicationSupportDirectory();
      final savedPath =
          '${support.path}${Platform.pathSeparator}${DateTime.now().millisecondsSinceEpoch}.jpg';
      await File(savedPath).writeAsBytes(bytes);

      var lat = 0.0, lng = 0.0;
      try {
        final pos = await Geolocator.getCurrentPosition(
          locationSettings: const LocationSettings(
            accuracy: LocationAccuracy.low, // tiết kiệm pin
            timeLimit: Duration(seconds: 8),
          ),
        );
        lat = pos.latitude;
        lng = pos.longitude;
      } catch (_) {/* không có GPS vẫn tiếp tục */}

      // Inference on-device — chạy được cả khi offline.
      final res = await _inference.classify(bytes);
      var rec = RescueRecord(
        id: _uuid.v4(),
        createdAtMs: DateTime.now().millisecondsSinceEpoch,
        label: res?.label ?? 'unknown',
        confidence: res?.confidence ?? 0,
        lat: lat,
        lng: lng,
        note: note.trim(),
        imagePath: savedPath,
        mode: SendMode.queuedOffline,
        status: 'pending',
        bytesOriginal: originalLen,
        bytesSent: 0,
        durationUploadMs: 0,
        durationInferenceMs: res?.durationMs ?? 0,
        networkType: await _network.currentTypeName(),
        throughputKbps: 0,
        attempts: 0,
      );
      await _store.upsert(rec);
      lastMessage =
          'Đã nhận diện: ${rec.label} (${(rec.confidence * 100).toStringAsFixed(0)}%)';

      await _dispatch(rec, bytes);
      await syncAll(); // đẩy nốt các bản cũ đang pending
    } catch (e) {
      lastMessage = 'Lỗi: $e';
    } finally {
      busy = false;
      notifyListeners();
    }
  }

  /// Quyết định và thực thi việc gửi cho một bản ghi vừa tạo.
  Future<void> _dispatch(RescueRecord rec, Uint8List bytes) async {
    final hasNet = await _network.hasData();
    if (!hasNet) {
      // Offline hoàn toàn → thử SMS, thất bại thì ở lại queue.
      final smsOk = await _trySms(rec);
      final mode = resolveOfflineMode(SendMode.smsFallback, smsOk);
      await _store.upsert(rec.copyWith(mode: mode));
      lastMessage = smsOk
          ? 'Không có data — đã gửi SMS fallback'
          : 'Offline hoàn toàn — lưu queue, tự gửi khi có mạng';
      notifyListeners();
      return;
    }

    // Probe throughput MỘT lần tại thời điểm gửi (tiết kiệm pin + data).
    final kbps = await _network.measureKbps();
    final mode = chooseMode(
      hasData: true,
      confidence: rec.confidence,
      throughputKbps: kbps,
      strongKbps: kStrongKbps,
      minUsefulKbps: kMinUsefulKbps,
      highConfidence: kHighConfidence,
      preferTextWhenConfident: kPreferTextWhenConfident,
    );
    await _sendByMode(rec, bytes, mode, kbps);
  }

  Future<void> _sendByMode(
      RescueRecord rec, Uint8List original, SendMode mode, int kbps) async {
    Uint8List? payload;
    switch (mode) {
      case SendMode.fullImage:
        payload = original;
        break;
      case SendMode.compressedImage:
        payload = await _sender.compress(original) ?? original;
        break;
      case SendMode.textOnly:
      case SendMode.smsFallback:
      case SendMode.queuedOffline:
        payload = null;
        break;
    }

    final result = await _sender.upload(rec, payload);
    rec = rec.copyWith(
      mode: mode,
      status: result.ok ? 'sent' : 'pending',
      bytesSent: result.ok ? result.bytesSent : 0,
      durationUploadMs: result.durationMs,
      throughputKbps: kbps,
      attempts: rec.attempts + 1,
    );
    await _store.upsert(rec);
    lastMessage = result.ok
        ? 'Đã gửi (${mode.name}): ${(result.bytesSent / 1024).toStringAsFixed(1)} KB / ${result.durationMs} ms'
        : 'Gửi thất bại — giữ trong queue để thử lại';
    notifyListeners();
  }

  /// SMS fallback qua platform channel Android. Trả true nếu thành công.
  Future<bool> _trySms(RescueRecord rec) async {
    try {
      final p = await Permission.sms.request();
      if (!p.isGranted) return false;
      await _sender.sendSms(kEmergencyPhone, _sender.smsBody(rec));
      return true;
    } catch (_) {
      return false; // iOS / máy không SIM / user từ chối → về queue
    }
  }

  /// Đẩy toàn bộ bản ghi pending khi có mạng (event mạng hoặc thủ công).
  Future<void> syncAll() async {
    if (!_store.ready || _store.pendingCount == 0) return;
    if (!await _network.hasData()) return;
    await BackgroundSync.perform(requireNetwork: false);
    lastMessage = 'Đã đồng bộ queue';
    notifyListeners();
  }
}
