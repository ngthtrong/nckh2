import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../config.dart';
import '../../data/datasources/user_local_datasource.dart';
import '../../core/platform/local_file.dart';
import '../../domain/entities/ai_model_type.dart';
import '../../domain/entities/ai_tag.dart';
import '../../domain/entities/rescue_record.dart';
import '../../domain/entities/send_mode.dart';
import '../../domain/services/adaptive_send_policy.dart';
import '../../domain/entities/user.dart';
import '../../domain/usecases/analyze_image_usecase.dart';
import '../../domain/usecases/get_rescue_records_usecase.dart';
import '../../domain/usecases/send_sos_usecase.dart';
import '../../domain/usecases/submit_rescue_post_usecase.dart';
import '../../domain/usecases/sync_pending_records_usecase.dart';
import '../../domain/repositories/inference_repository.dart';
import '../../domain/repositories/network_repository.dart';
import '../../domain/repositories/rescue_repository.dart';

class AppController extends ChangeNotifier {
  final RescueRepository rescueRepository;
  final InferenceRepository inferenceRepository;
  final NetworkRepository networkRepository;
  final UserLocalDataSource userLocalDataSource;

  late final SendSosUseCase _sendSosUseCase;
  late final SubmitRescuePostUseCase _submitRescuePostUseCase;
  late final GetRescueRecordsUseCase _getRescueRecordsUseCase;
  late final AnalyzeImageUseCase _analyzeImageUseCase;
  late final SyncPendingRecordsUseCase _syncPendingRecordsUseCase;
  late final AdaptiveSendPolicy _sendPolicy;

  final ImagePicker _picker = ImagePicker();
  StreamSubscription<List<ConnectivityResult>>? _connSub;
  Timer? _statusTimer;
  bool _refreshingStatuses = false;

  bool isBusy = false;
  String networkLabel = 'WiFi';
  bool isModelReady = false;
  bool isBenchmarking = false;
  bool isModelLoading = true;
  String locationLabel = 'Đang lấy vị trí GPS...';
  // Không có tọa độ mặc định: gửi tọa độ giả sẽ dẫn đội cứu hộ tới sai chỗ.
  double? currentLat;
  double? currentLng;

  RescueRecord? lastSubmittedPost;

  /// Throughput đo qua /probe ở lần gửi gần nhất (kbit/s), null nếu không đo.
  int? lastThroughputKbps;
  User? currentUser;
  bool isGuest = false;

  bool get isAuthenticated => currentUser != null || isGuest;

  AppController({
    required this.rescueRepository,
    required this.inferenceRepository,
    required this.networkRepository,
    UserLocalDataSource? userLocalDataSource,
  }) : userLocalDataSource = userLocalDataSource ?? UserLocalDataSource() {
    _sendSosUseCase = SendSosUseCase(rescueRepository);
    _submitRescuePostUseCase = SubmitRescuePostUseCase(rescueRepository);
    _getRescueRecordsUseCase = GetRescueRecordsUseCase(rescueRepository);
    _analyzeImageUseCase = AnalyzeImageUseCase(inferenceRepository);
    _syncPendingRecordsUseCase = SyncPendingRecordsUseCase(rescueRepository);
    _sendPolicy = AdaptiveSendPolicy(networkRepository);
  }

  Future<bool> login(String username, String password) async {
    final saved = userLocalDataSource.getUser();
    if (saved != null) {
      if (saved.username == username.trim() && saved.password == password) {
        currentUser = saved;
        isGuest = false;
        notifyListeners();
        return true;
      }
    }
    // Demo fallback account if not registered yet
    if (username.trim() == 'cuuho' && password == '123456') {
      final demoUser = User(
        username: 'cuuho',
        password: password,
        phone: '0901234567',
        address: 'Quận 1, TP. Hồ Chí Minh',
      );
      await userLocalDataSource.saveUser(demoUser);
      currentUser = demoUser;
      isGuest = false;
      notifyListeners();
      return true;
    }
    return false;
  }

  Future<bool> register(User user) async {
    await userLocalDataSource.saveUser(user);
    currentUser = user;
    isGuest = false;
    notifyListeners();
    return true;
  }

  Future<void> updateUser(User user) async {
    await userLocalDataSource.saveUser(user);
    currentUser = user;
    notifyListeners();
  }

  Future<void> logout() async {
    await userLocalDataSource.deleteUser();
    currentUser = null;
    isGuest = false;
    notifyListeners();
  }

  void continueAsGuest() {
    isGuest = true;
    notifyListeners();
  }

  List<RescueRecord> get records => _getRescueRecordsUseCase();
  int get pendingCount => rescueRepository.getPendingCount();

  AiModelType get currentModel => inferenceRepository.currentModel;
  bool get isPteReady => inferenceRepository.pteReady;
  bool get isDualComparison => inferenceRepository.isDualComparison;
  ModelBenchmarkComparison? get latestComparison =>
      inferenceRepository.latestComparison;

  void switchAiModel(AiModelType model) {
    inferenceRepository.setModel(model);
    notifyListeners();
  }

  void toggleDualComparison(bool enabled) {
    inferenceRepository.setDualComparison(enabled);
    notifyListeners();
  }

  Future<void> init() async {
    await rescueRepository.init();
    await userLocalDataSource.init();
    currentUser = userLocalDataSource.getUser();
    unawaited(
      inferenceRepository
          .loadModel()
          .then((_) {
            isModelReady = inferenceRepository.ready;
            isModelLoading = false;
            notifyListeners();
          })
          .catchError((e) {
            debugPrint('Notice loading AI model: $e');
            isModelReady = inferenceRepository.ready;
            isModelLoading = false;
            notifyListeners();
          }),
    );

    unawaited(refreshLocation(requestPermission: true));

    _connSub = networkRepository.networkChanges.listen((results) async {
      networkLabel = await networkRepository.getCurrentNetworkType();
      notifyListeners();
      final hasNet = results.any(
        (e) =>
            e == ConnectivityResult.wifi ||
            e == ConnectivityResult.mobile ||
            e == ConnectivityResult.ethernet,
      );
      if (hasNet) {
        if (pendingCount > 0) await syncPending();
        await refreshStatuses();
      }
    });

    networkLabel = await networkRepository.getCurrentNetworkType();
    notifyListeners();

    // Người gửi thấy được khi trung tâm điều phối / hoàn thành báo cáo của mình.
    unawaited(refreshStatuses());
    _statusTimer = Timer.periodic(
      kStatusPollInterval,
      (_) => unawaited(refreshStatuses()),
    );
  }

  /// Hỏi server trạng thái điều phối của các báo cáo đã gửi (chỉ cập nhật tiến).
  Future<void> refreshStatuses() async {
    if (_refreshingStatuses) return;
    _refreshingStatuses = true;
    try {
      final changed = await rescueRepository.refreshStatuses();
      if (changed.isEmpty) return;
      final last = lastSubmittedPost;
      if (last != null) {
        for (final record in changed) {
          if (record.id == last.id) lastSubmittedPost = record;
        }
      }
      notifyListeners();
    } catch (e) {
      debugPrint('Không lấy được trạng thái điều phối: $e');
    } finally {
      _refreshingStatuses = false;
    }
  }

  /// Chọn cách gửi theo mạng hiện tại (đo /probe khi có ảnh).
  Future<SendMode> _decideSendMode({
    required bool hasImage,
    required double confidence,
  }) async {
    final decision = await _sendPolicy.decide(
      hasImage: hasImage,
      confidence: confidence,
    );
    lastThroughputKbps = decision.throughputKbps;
    return decision.mode;
  }

  /// Trạng thái mô hình AI để hiển thị: đang nạp, sẵn sàng hoặc lý do không khả dụng.
  String get modelStatusHint {
    if (isModelReady) return 'Chạm để đổi ONNX/PTE và benchmark';
    if (isModelLoading) return 'Đang tải model on-device...';
    if (kIsWeb) return 'Bản web không chạy AI on-device';
    return 'Thiếu file model trong assets/models';
  }

  /// Lấy vị trí GPS hiện tại. Thất bại thì giữ vị trí trống (không dùng tọa độ
  /// giả); server đưa báo cáo thiếu vị trí vào hàng cần xem xét thủ công.
  Future<void> refreshLocation({
    bool requestPermission = false,
    Duration timeLimit = const Duration(seconds: 5),
  }) async {
    if (requestPermission) {
      try {
        await Permission.locationWhenInUse.request();
      } catch (e) {
        // permission_handler không hỗ trợ web/desktop; Geolocator tự xin quyền ở đó.
        debugPrint('Bỏ qua permission_handler cho vị trí: $e');
      }
    }
    try {
      final pos = await Geolocator.getCurrentPosition(
        locationSettings: LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: timeLimit,
        ),
      );
      currentLat = pos.latitude;
      currentLng = pos.longitude;
      locationLabel =
          '${pos.latitude.toStringAsFixed(4)}° N, ${pos.longitude.toStringAsFixed(4)}° E · GPS';
    } catch (e) {
      debugPrint('Không lấy được GPS: $e');
      if (currentLat == null) {
        locationLabel = 'Chưa có GPS · trung tâm sẽ xác minh vị trí';
      }
    }
    notifyListeners();
  }

  @override
  void dispose() {
    _connSub?.cancel();
    _statusTimer?.cancel();
    super.dispose();
  }

  Future<RescueRecord?> sendSos() async {
    if (isBusy) return null;
    isBusy = true;
    notifyListeners();

    try {
      if (currentLat == null) {
        await refreshLocation(timeLimit: const Duration(seconds: 3));
      }
      final record = await _sendSosUseCase(
        lat: currentLat,
        lng: currentLng,
        sendMode: await _decideSendMode(hasImage: false, confidence: 0),
      );
      isBusy = false;
      notifyListeners();
      return record;
    } catch (_) {
      isBusy = false;
      notifyListeners();
      return null;
    }
  }

  Future<RescueRecord?> submitPost({
    required int trappedCount,
    required int injuredCount,
    required List<String> vulnerableGroups,
    required String description,
    required String? imagePath,
    required List<AiTag> aiTags,
  }) async {
    if (isBusy) return null;
    isBusy = true;
    notifyListeners();

    try {
      if (currentLat == null) {
        await refreshLocation(timeLimit: const Duration(seconds: 3));
      }
      final record = await _submitRescuePostUseCase(
        lat: currentLat,
        lng: currentLng,
        imagePath: imagePath,
        images: imagePath != null ? [imagePath] : [],
        aiTags: aiTags,
        trappedCount: trappedCount,
        injuredCount: injuredCount,
        vulnerableGroups: vulnerableGroups,
        description: description,
        sendMode: await _decideSendMode(
          hasImage: imagePath != null,
          confidence: aiTags.fold(
            0.0,
            (best, tag) => tag.confidence > best ? tag.confidence : best,
          ),
        ),
      );
      lastSubmittedPost = record;
      isBusy = false;
      notifyListeners();
      return record;
    } catch (_) {
      isBusy = false;
      notifyListeners();
      return null;
    }
  }

  Future<List<AiTag>> analyzeImage(String imagePath) async {
    try {
      final bytes = await readLocalFile(imagePath);
      return await _analyzeImageUseCase(bytes);
    } catch (_) {
      return [];
    }
  }

  Future<String?> pickImage({required ImageSource source}) async {
    try {
      final picked = await _picker.pickImage(
        source: source,
        maxWidth: 1200,
        maxHeight: 1200,
        imageQuality: 80,
      );
      return picked?.path;
    } catch (_) {
      return null;
    }
  }

  Future<InferenceResult?> testModelBenchmark() async {
    if (isBenchmarking) return null;
    isBenchmarking = true;
    notifyListeners();

    try {
      final ByteData raw = await rootBundle.load('assets/images/app_logo.png');
      final bytes = raw.buffer.asUint8List(
        raw.offsetInBytes,
        raw.lengthInBytes,
      );
      final result = await inferenceRepository.classifyImage(bytes);
      isBenchmarking = false;
      notifyListeners();
      return result;
    } catch (e) {
      debugPrint('Benchmark test error: $e');
      isBenchmarking = false;
      notifyListeners();
      return null;
    }
  }

  Future<void> syncPending() async {
    await _syncPendingRecordsUseCase();
    notifyListeners();
    await refreshStatuses();
  }
}
