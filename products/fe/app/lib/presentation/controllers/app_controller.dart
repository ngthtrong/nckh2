import 'dart:async';
import 'dart:convert';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../config.dart';
import '../../data/datasources/user_local_datasource.dart';
import '../../data/datasources/admin_session.dart';
import '../../data/datasources/admin_model_download.dart';
import '../../core/platform/local_file.dart';
import '../../core/platform/sync_isolate_guard.dart';
import '../../domain/entities/ai_model_type.dart';
import '../../domain/entities/ai_tag.dart';
import '../../domain/entities/rescue_record.dart';
import '../../domain/entities/send_mode.dart';
import '../../domain/services/adaptive_send_policy.dart';
import '../../domain/services/urgency_logistic_model.dart';
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
  final AdminSession adminSession;
  CancelToken? _modelDownload;
  bool isDownloadingOnnx = false;
  bool isDeletingBenchmarkResources = false;
  double? onnxDownloadProgress;
  String? onnxDownloadError;

  late final SendSosUseCase _sendSosUseCase;
  late final SubmitRescuePostUseCase _submitRescuePostUseCase;
  late final GetRescueRecordsUseCase _getRescueRecordsUseCase;
  late final AnalyzeImageUseCase _analyzeImageUseCase;
  late final SyncPendingRecordsUseCase _syncPendingRecordsUseCase;
  late final AdaptiveSendPolicy _sendPolicy;
  Future<UrgencyLogisticModel?>? _urgencyModelFuture;
  UrgencyLogisticModel? _urgencyModel;

  final ImagePicker _picker = ImagePicker();
  StreamSubscription<List<ConnectivityResult>>? _connSub;
  Timer? _statusTimer;

  /// Hẹn giờ gửi lại message đang chờ backoff (retry scheduler của contract).
  Timer? _retryTimer;
  bool _refreshingStatuses = false;
  Future<void>? _initialization;
  Future<void>? _onlineWork;

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

  bool get isAuthenticated => currentUser != null || isGuest || isAdmin;
  String get adminServerUrl =>
      (connectedServerUrl ?? kServerBaseUrl).replaceAll(RegExp(r'/+$'), '');
  bool get isAdmin =>
      adminSession.isAdmin && adminSession.server == adminServerUrl;

  AppController({
    required this.rescueRepository,
    required this.inferenceRepository,
    required this.networkRepository,
    UserLocalDataSource? userLocalDataSource,
    AdminSession? adminSession,
  }) : userLocalDataSource = userLocalDataSource ?? UserLocalDataSource(),
       adminSession = adminSession ?? AdminSession() {
    this.adminSession.addListener(_adminChanged);
    _sendSosUseCase = SendSosUseCase(rescueRepository);
    _submitRescuePostUseCase = SubmitRescuePostUseCase(rescueRepository);
    _getRescueRecordsUseCase = GetRescueRecordsUseCase(rescueRepository);
    _analyzeImageUseCase = AnalyzeImageUseCase(inferenceRepository);
    _syncPendingRecordsUseCase = SyncPendingRecordsUseCase(rescueRepository);
    _sendPolicy = AdaptiveSendPolicy(networkRepository);
  }

  void _adminChanged() {
    if (!isAdmin) _modelDownload?.cancel('Đã đăng xuất admin.');
    inferenceRepository.setComparisonAccess(
      isAdmin && !isDeletingBenchmarkResources,
    );
    isModelReady = inferenceRepository.ready;
    notifyListeners();
  }

  Future<void> loginAdmin(String username, String password) async {
    if (connectedServerUrl == null) await reconnectServer();
    await adminSession.login(adminServerUrl, username, password);
  }

  Future<bool> validateAdmin() async {
    if (!isAdmin) return false;
    return adminSession.validate();
  }

  Future<void> downloadOnnx() async {
    if (isDownloadingOnnx ||
        isDeletingBenchmarkResources ||
        isModelLoading ||
        isBenchmarking ||
        !isAdmin) {
      return;
    }
    isDownloadingOnnx = true;
    onnxDownloadProgress = null;
    onnxDownloadError = null;
    final cancel = CancelToken();
    _modelDownload = cancel;
    final sessionToken = adminSession.token;
    notifyListeners();
    try {
      if (!await validateAdmin()) return;
      final path = await downloadAdminOnnx(
        server: adminServerUrl,
        token: sessionToken!,
        cancelToken: cancel,
        onProgress: (received, total) {
          onnxDownloadProgress = total > 0 ? received / total : null;
          notifyListeners();
        },
      );
      if (!isAdmin ||
          adminSession.token != sessionToken ||
          cancel.isCancelled) {
        return;
      }
      await inferenceRepository.loadComparisonModel(path);
    } catch (error) {
      if (!cancel.isCancelled) {
        onnxDownloadError = 'Không tải được ONNX: $error';
      }
    } finally {
      _modelDownload = null;
      isDownloadingOnnx = false;
      notifyListeners();
    }
  }

  bool beginBenchmark() {
    if (!isAdmin ||
        isBenchmarking ||
        isDeletingBenchmarkResources ||
        isDownloadingOnnx) {
      return false;
    }
    isBenchmarking = true;
    notifyListeners();
    return true;
  }

  void endBenchmark() {
    isBenchmarking = false;
    notifyListeners();
  }

  Future<int> deleteBenchmarkResources() async {
    if (!isAdmin ||
        isDeletingBenchmarkResources ||
        isDownloadingOnnx ||
        isBenchmarking ||
        isModelLoading) {
      throw StateError(
        'Chờ tác vụ model hoặc benchmark kết thúc trước khi xóa.',
      );
    }
    isDeletingBenchmarkResources = true;
    notifyListeners();
    try {
      await inferenceRepository.unloadComparisonModel();
      return await pruneModelDownloads(deleteBenchmark: true);
    } finally {
      isDeletingBenchmarkResources = false;
      inferenceRepository.setComparisonAccess(isAdmin);
      isModelReady = inferenceRepository.ready;
      notifyListeners();
    }
  }

  Future<bool> login(String username, String password) async {
    final saved = userLocalDataSource.getUser();
    if (saved != null) {
      if (saved.username == username.trim() && saved.password == password) {
        await userLocalDataSource.saveUser(saved);
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
    final adminLogout = adminSession.logout();
    await userLocalDataSource.clearSession();
    currentUser = null;
    isGuest = false;
    notifyListeners();
    await adminLogout;
  }

  void continueAsGuest() {
    isGuest = true;
    notifyListeners();
  }

  List<RescueRecord> get records => _getRescueRecordsUseCase();
  List<RescueRecord> getRecordsPage({
    required int offset,
    required int limit,
  }) => rescueRepository.getRecordsPage(offset: offset, limit: limit);
  int get recordCount => rescueRepository.recordCount;
  int get pendingCount => rescueRepository.getPendingCount();
  String? get connectedServerUrl => rescueRepository.connectedServerUrl;

  Future<void> reconnectServer() async {
    final connected = await rescueRepository.reconnectServer();
    if (adminSession.server != null && adminSession.server != adminServerUrl) {
      unawaited(adminSession.logout());
    }
    notifyListeners();
    if (connected && pendingCount > 0) await syncPending();
  }

  AiModelType get currentModel => inferenceRepository.currentModel;
  bool get isPteReady => inferenceRepository.pteReady;
  bool get isOnnxReady => isAdmin && inferenceRepository.onnxReady;
  bool get isDualComparison => isAdmin && inferenceRepository.isDualComparison;
  ModelBenchmarkComparison? get latestComparison =>
      isAdmin ? inferenceRepository.latestComparison : null;

  double? urgencyScore(Iterable<String> severeSigns) =>
      _urgencyModel?.score(severeSigns);

  Future<UrgencyLogisticModel?> _loadUrgencyModel() =>
      _urgencyModelFuture ??= _readUrgencyModel();

  Future<UrgencyLogisticModel?> _readUrgencyModel() async {
    try {
      final raw = await rootBundle.loadString(
        'assets/models/urgency_logistic.json',
      );
      final model = UrgencyLogisticModel.fromJson(
        jsonDecode(raw) as Map<String, dynamic>,
      );
      _urgencyModel = model;
      if (hasListeners) notifyListeners();
      return model;
    } catch (error) {
      debugPrint('Không tải được urgency logistic model: $error');
      return null;
    }
  }

  void switchAiModel(AiModelType model) {
    if (!isAdmin || isBenchmarking || isDeletingBenchmarkResources) return;
    inferenceRepository.setModel(model);
    isModelReady = inferenceRepository.ready;
    notifyListeners();
  }

  void toggleDualComparison(bool enabled) {
    if (!isAdmin || isBenchmarking || isDeletingBenchmarkResources) return;
    inferenceRepository.setDualComparison(enabled);
    notifyListeners();
  }

  Future<void> init() =>
      _initialization ??= _initialize().onError((error, stack) {
        _initialization = null;
        Error.throwWithStackTrace(
          error ?? StateError('Initialization failed.'),
          stack,
        );
      });

  Future<void> _initialize() async {
    // Tác vụ Workmanager đang ghi outbox ở isolate khác: chờ xong mới mở Hive.
    await waitForBackgroundSync();
    await rescueRepository.init();
    await userLocalDataSource.init();
    currentUser = userLocalDataSource.isSignedIn
        ? userLocalDataSource.getUser()
        : null;
    networkLabel = await networkRepository.getCurrentNetworkType();
    unawaited(_loadUrgencyModel());
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
        await _connectAndSync();
      }
    });

    notifyListeners();

    // Người gửi thấy được khi trung tâm điều phối / hoàn thành báo cáo của mình.
    _statusTimer = Timer.periodic(
      kStatusPollInterval,
      (_) => unawaited(refreshStatuses()),
    );
    _scheduleRetry(); // message còn chờ từ lần chạy trước
    registerForegroundSync(syncPending);
    unawaited(_connectAndSync());
  }

  Future<void> _connectAndSync() =>
      _onlineWork ??= _connectAndSyncOnce().whenComplete(() {
        _onlineWork = null;
      });

  Future<void> _connectAndSyncOnce() async {
    try {
      if (!await rescueRepository.reconnectServer()) return;
      notifyListeners();
      await syncPending(immediate: false);
    } catch (error) {
      debugPrint('Kết nối/đồng bộ nền chưa hoàn tất: $error');
    }
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
    await rescueRepository.reconnectServer();
    final decision = await _sendPolicy.decide(
      hasImage: hasImage,
      confidence: confidence,
    );
    lastThroughputKbps = decision.throughputKbps;
    return decision.mode;
  }

  /// Trạng thái mô hình AI để hiển thị: đang nạp, sẵn sàng hoặc lý do không khả dụng.
  String get modelStatusHint {
    if (isModelReady) {
      return isAdmin
          ? 'Chạm để đổi ONNX/PTE và benchmark'
          : 'AI PTE sẵn sàng trên thiết bị';
    }
    if (isModelLoading) return 'Đang tải model on-device...';
    if (kIsWeb) return 'Bản web không chạy AI on-device';
    return 'Model PTE chưa sẵn sàng trên thiết bị';
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
    _retryTimer?.cancel();
    _modelDownload?.cancel();
    adminSession.removeListener(_adminChanged);
    adminSession.dispose();
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
      _scheduleRetry();
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
    required bool cannotMove,
    required List<String> severeSigns,
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
      final urgencyModel = await _loadUrgencyModel();
      final record = await _submitRescuePostUseCase(
        lat: currentLat,
        lng: currentLng,
        imagePath: imagePath,
        images: imagePath != null ? [imagePath] : [],
        aiTags: aiTags,
        trappedCount: trappedCount,
        injuredCount: injuredCount,
        vulnerableGroups: vulnerableGroups,
        cannotMove: cannotMove,
        severeSigns: severeSigns,
        urgencyScore: urgencyModel?.score(severeSigns),
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
      _scheduleRetry();
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
    if (!beginBenchmark()) return null;

    try {
      if (!await validateAdmin()) return null;
      final ByteData raw = await rootBundle.load('assets/images/app_logo.png');
      final bytes = raw.buffer.asUint8List(
        raw.offsetInBytes,
        raw.lengthInBytes,
      );
      final result = await inferenceRepository.classifyImage(bytes);
      return result;
    } catch (e) {
      debugPrint('Benchmark test error: $e');
      return null;
    } finally {
      endBenchmark();
    }
  }

  Future<void> syncPending({bool immediate = true}) async {
    try {
      await _syncPendingRecordsUseCase(immediate: immediate);
    } finally {
      _scheduleRetry();
    }
    notifyListeners();
    await refreshStatuses();
  }

  /// Hẹn lần gửi lại tại thời điểm message sớm nhất hết backoff. Không có hẹn này,
  /// message lỗi tạm (mất mạng giữa chừng, 5xx) nằm chờ tới lần có mạng lại, lần gửi
  /// bài kế tiếp hoặc Workmanager (15 phút).
  void _scheduleRetry() {
    _retryTimer?.cancel();
    final due = rescueRepository.nextRetryAt;
    if (due == null) return;
    final wait = due.difference(DateTime.now().toUtc());
    _retryTimer = Timer(
      wait.isNegative ? Duration.zero : wait + const Duration(milliseconds: 50),
      () => unawaited(syncPending(immediate: false)),
    );
  }
}
