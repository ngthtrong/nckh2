import 'dart:async';
import 'dart:convert';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';

import '../../config.dart';
import '../../data/datasources/user_local_datasource.dart';
import '../../data/datasources/compose_draft_local_datasource.dart';
import '../../data/datasources/admin_session.dart';
import '../../data/datasources/admin_model_download.dart';
import '../../core/platform/local_file.dart';
import '../../core/platform/sync_isolate_guard.dart';
import '../../domain/entities/ai_model_type.dart';
import '../../domain/entities/ai_tag.dart';
import '../../domain/entities/record_id.dart';
import '../../domain/entities/rescue_record.dart';
import '../../domain/entities/send_mode.dart';
import '../../domain/services/adaptive_send_policy.dart';
import '../../domain/services/urgency_logistic_model.dart';
import '../../domain/services/sync_activity.dart';
import '../../domain/entities/user.dart';
import '../../domain/usecases/analyze_image_usecase.dart';
import '../../domain/usecases/get_rescue_records_usecase.dart';
import '../../domain/usecases/send_sos_usecase.dart';
import '../../domain/usecases/deliver_record.dart';
import '../../domain/usecases/submit_rescue_post_usecase.dart';
import '../../domain/usecases/sync_pending_records_usecase.dart';
import '../../domain/repositories/inference_repository.dart';
import '../../domain/repositories/network_repository.dart';
import '../../domain/repositories/rescue_repository.dart';

class AppController extends ChangeNotifier with WidgetsBindingObserver {
  final RescueRepository rescueRepository;
  final InferenceRepository inferenceRepository;
  final NetworkRepository networkRepository;
  final UserLocalDataSource userLocalDataSource;
  final ComposeDraftLocalDataSource composeDraftLocalDataSource;
  final AdminSession adminSession;
  CancelToken? _modelDownload;
  bool isDownloadingOnnx = false;
  bool isDeletingBenchmarkResources = false;
  bool isPreparingBenchmark = false;
  int benchmarkResourcesRevision = 0;

  void setPreparingBenchmark(bool preparing) {
    isPreparingBenchmark = preparing;
    if (!_disposed) notifyListeners();
  }

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

  final ImagePicker _picker;
  StreamSubscription<List<ConnectivityResult>>? _connSub;
  Timer? _statusTimer;

  /// Hẹn giờ gửi lại message đang chờ backoff (retry scheduler của contract).
  Timer? _retryTimer;
  bool _refreshingStatuses = false;
  Future<void>? _initialization;
  Future<void>? _onlineWork;
  Future<void>? _modelLoad;
  bool _modelLoadAttempted = false;
  bool _foreground = true;
  bool _watchingStatus = false;
  bool _disposed = false;

  bool isBusy = false;
  String networkLabel = 'WiFi';
  bool isModelReady = false;
  bool isBenchmarking = false;
  bool isModelLoading = false;
  String locationLabel = 'Đang lấy vị trí GPS...';
  // Không có tọa độ mặc định: gửi tọa độ giả sẽ dẫn đội cứu hộ tới sai chỗ.
  double? currentLat;
  double? currentLng;
  double? currentLocationAccuracyMeters;
  int _locationRequest = 0;

  RescueRecord? lastSubmittedPost;
  String? submissionError;

  /// Throughput đo qua /probe ở lần gửi gần nhất (kbit/s), null nếu không đo.
  int? lastThroughputKbps;
  User? currentUser;
  bool isGuest = false;

  bool get isAuthenticated => currentUser != null || isGuest || isAdmin;
  String get adminServerUrl =>
      (connectedServerUrl ?? kServerBaseUrl).replaceAll(RegExp(r'/+$'), '');
  bool get isAdmin =>
      kAdminModelTools &&
      adminSession.isAdmin &&
      adminSession.server == adminServerUrl;

  AppController({
    required this.rescueRepository,
    required this.inferenceRepository,
    required this.networkRepository,
    UserLocalDataSource? userLocalDataSource,
    ComposeDraftLocalDataSource? composeDraftLocalDataSource,
    ImagePicker? picker,
    AdminSession? adminSession,
  }) : userLocalDataSource = userLocalDataSource ?? UserLocalDataSource(),
       composeDraftLocalDataSource =
           composeDraftLocalDataSource ?? ComposeDraftLocalDataSource(),
       _picker = picker ?? ImagePicker(),
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
    if (!kAdminModelTools) return;
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
      await ensureModelLoaded();
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
        isDownloadingOnnx ||
        isPreparingBenchmark) {
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
    if (isDeletingBenchmarkResources ||
        isPreparingBenchmark ||
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
      final bytes = await pruneModelDownloads(deleteBenchmark: true);
      benchmarkResourcesRevision++;
      return bytes;
    } finally {
      isDeletingBenchmarkResources = false;
      inferenceRepository.setComparisonAccess(isAdmin);
      isModelReady = inferenceRepository.ready;
      notifyListeners();
    }
  }

  Future<bool> login(String username, String password) async {
    final saved = await userLocalDataSource.authenticate(username, password);
    if (saved == null) return false;
    currentUser = saved;
    isGuest = false;
    notifyListeners();
    return true;
  }

  Future<bool> register(User user) async {
    try {
      currentUser = await userLocalDataSource.saveUser(user);
    } catch (_) {
      return false;
    }
    isGuest = false;
    notifyListeners();
    return true;
  }

  Future<void> updateUser(User user) async {
    currentUser = await userLocalDataSource.saveUser(user);
    notifyListeners();
  }

  Future<bool> changePassword(String current, String next) async {
    final updated = await userLocalDataSource.changePassword(current, next);
    if (updated == null) return false;
    currentUser = updated;
    notifyListeners();
    return true;
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
  RescueRecord? get latestSos =>
      records.where((record) => record.id.startsWith('sos-')).firstOrNull;
  String? get connectedServerUrl => rescueRepository.connectedServerUrl;

  Future<void> reconnectServer() async {
    final connected = await rescueRepository.reconnectServer(force: true);
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
    await composeDraftLocalDataSource.init();
    await recoverPickerDraft();
    currentUser = userLocalDataSource.isSignedIn
        ? userLocalDataSource.getUser()
        : null;
    networkLabel = await networkRepository.getCurrentNetworkType();
    unawaited(_loadUrgencyModel());
    WidgetsBinding.instance.addObserver(this);
    _foreground =
        WidgetsBinding.instance.lifecycleState == null ||
        WidgetsBinding.instance.lifecycleState == AppLifecycleState.resumed;

    unawaited(refreshLocation(requestPermission: true));

    _connSub = networkRepository.networkChanges.listen((results) async {
      final previousNetwork = networkLabel;
      networkLabel = await networkRepository.getCurrentNetworkType();
      notifyListeners();
      final hasNet = results.any((result) => result != ConnectivityResult.none);
      _scheduleStatusPoll();
      _scheduleRetry();
      if (hasNet) {
        if (!hasSyncWork(records)) return;
        await _connectAndSync(force: previousNetwork != networkLabel);
      }
    });

    notifyListeners();

    // Người gửi thấy được khi trung tâm điều phối / hoàn thành báo cáo của mình.
    _scheduleStatusPoll();
    _scheduleRetry(); // message còn chờ từ lần chạy trước
    registerForegroundSync(syncPending);
    if (hasSyncWork(records)) unawaited(_connectAndSync());
  }

  Future<void> ensureModelLoaded() {
    if (inferenceRepository.pteReady) return Future.value();
    return _modelLoad ??= _loadModelOnce().whenComplete(
      () => _modelLoad = null,
    );
  }

  Future<void> _loadModelOnce() async {
    _modelLoadAttempted = true;
    isModelLoading = true;
    notifyListeners();
    try {
      await inferenceRepository.loadModel();
    } catch (error) {
      debugPrint('Không nạp được PTE: $error');
    } finally {
      isModelReady = inferenceRepository.ready;
      isModelLoading = false;
      if (!_disposed) notifyListeners();
    }
  }

  void setWatchingStatus(bool watching) {
    if (_watchingStatus == watching) return;
    _watchingStatus = watching;
    _scheduleStatusPoll();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _foreground = state == AppLifecycleState.resumed;
    _scheduleStatusPoll();
    _scheduleRetry();
    if (_foreground && networkLabel != 'none' && hasSyncWork(records)) {
      unawaited(_connectAndSync());
    }
  }

  void _scheduleStatusPoll() {
    _statusTimer?.cancel();
    if (_disposed ||
        !_foreground ||
        networkLabel == 'none' ||
        !hasTrackedReports(records)) {
      return;
    }
    _statusTimer = Timer(
      _watchingStatus ? kStatusPollInterval : const Duration(seconds: 60),
      () => unawaited(refreshStatuses()),
    );
  }

  Future<void> _connectAndSync({bool force = false}) =>
      _onlineWork ??= _connectAndSyncOnce(force: force).whenComplete(() {
        _onlineWork = null;
      });

  Future<void> _connectAndSyncOnce({bool force = false}) async {
    try {
      if (!await rescueRepository.reconnectServer(force: force)) return;
      notifyListeners();
      await syncPending(immediate: force);
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
      _scheduleStatusPoll();
    }
  }

  /// Chọn cách gửi theo mạng hiện tại (đo /probe khi có ảnh).
  Future<SendMode> _decideSendMode({
    required bool hasImage,
    required double confidence,
  }) async {
    // A plain SOS needs no throughput probe; its real metadata send decides fallback.
    if (hasImage && !await rescueRepository.reconnectServer()) {
      return SendMode.smsFallback;
    }
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
    if (_modelLoadAttempted) return 'AI chưa sẵn sàng · vẫn có thể gửi báo cáo';
    return 'AI sẽ được chuẩn bị khi tạo báo cáo';
  }

  /// Lấy vị trí GPS hiện tại. Thất bại thì giữ vị trí trống (không dùng tọa độ
  /// giả); server đưa báo cáo thiếu vị trí vào hàng cần xem xét thủ công.
  Future<void> refreshLocation({
    bool requestPermission = false,
    Duration timeLimit = const Duration(seconds: 5),
  }) async {
    final request = ++_locationRequest;
    try {
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied && requestPermission) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        throw PermissionDeniedException(
          permission == LocationPermission.deniedForever
              ? 'Quyền vị trí bị chặn · mở Cài đặt > Vị trí để cấp lại'
              : 'Chưa cấp quyền vị trí · vào Cài đặt > Vị trí để cấp quyền',
        );
      }
      final pos = await Geolocator.getCurrentPosition(
        locationSettings: LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: timeLimit,
        ),
      );
      if (request != _locationRequest || _disposed) return;
      currentLat = pos.latitude;
      currentLng = pos.longitude;
      currentLocationAccuracyMeters = pos.accuracy.isFinite && pos.accuracy > 0
          ? pos.accuracy
          : null;
      locationLabel = formatReportLocation(
        currentLat,
        currentLng,
        currentLocationAccuracyMeters,
      );
    } catch (e) {
      if (request != _locationRequest || _disposed) return;
      debugPrint('Không lấy được GPS: $e');
      currentLat = null;
      currentLng = null;
      currentLocationAccuracyMeters = null;
      locationLabel = e is PermissionDeniedException
          ? e.message ?? 'Chưa cấp quyền vị trí'
          : e is LocationServiceDisabledException
          ? 'Dịch vụ vị trí đang tắt · vào Cài đặt > Vị trí để bật'
          : 'Chưa có GPS · trung tâm sẽ xác minh vị trí';
    }
    notifyListeners();
  }

  Future<void> recoverLocation() async {
    if (isBusy) return;
    try {
      var permission = await Geolocator.checkPermission();
      // Android may only reveal a permanent denial after a permission request.
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.deniedForever) {
        await Geolocator.openAppSettings();
        return;
      }
      if (permission != LocationPermission.denied &&
          !await Geolocator.isLocationServiceEnabled()) {
        await Geolocator.openLocationSettings();
        return;
      }
      await refreshLocation();
    } catch (error) {
      debugPrint('Không mở được cài đặt vị trí: $error');
    }
  }

  @override
  void dispose() {
    _disposed = true;
    WidgetsBinding.instance.removeObserver(this);
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
      final record = await _sendSosUseCase(
        contactPhone: currentUser?.phone,
        lat: null,
        lng: null,
        sendMode: SendMode.queuedOffline,
        locate: () async {
          await refreshLocation(timeLimit: const Duration(seconds: 3));
          return (
            lat: currentLat,
            lng: currentLng,
            accuracyMeters: currentLocationAccuracyMeters,
          );
        },
        chooseMode: () => _decideSendMode(hasImage: false, confidence: 0),
      );
      isBusy = false;
      notifyListeners();
      _scheduleRetry();
      _scheduleStatusPoll();
      return record;
    } catch (_) {
      isBusy = false;
      notifyListeners();
      return null;
    }
  }

  Future<RescueRecord?> retrySosSms() async {
    if (isBusy) return null;
    final record = latestSos;
    if (record == null) return null;
    isBusy = true;
    notifyListeners();
    try {
      return await deliverRecord(
        rescueRepository,
        record,
        SendMode.smsFallback,
        retrySms: true,
      );
    } finally {
      isBusy = false;
      _scheduleRetry();
      if (!_disposed) notifyListeners();
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
    submissionError = null;
    isBusy = true;
    notifyListeners();

    try {
      await refreshLocation(timeLimit: const Duration(seconds: 3));
      final urgencyModel = await _loadUrgencyModel();
      final record = await _submitRescuePostUseCase(
        contactPhone: currentUser?.phone,
        lat: currentLat,
        lng: currentLng,
        locationAccuracyMeters: currentLocationAccuracyMeters,
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
        sendMode: SendMode.queuedOffline,
        chooseMode: () => _decideSendMode(
          hasImage: imagePath != null,
          confidence: aiTags.fold(
            0.0,
            (best, tag) => tag.confidence > best ? tag.confidence : best,
          ),
        ),
      );
      lastSubmittedPost = record;
      _scheduleRetry();
      _scheduleStatusPoll();
      isBusy = false;
      notifyListeners();
      return record;
    } catch (error) {
      submissionError = error is FormatException
          ? error.message
          : 'Chưa hoàn tất gửi báo cáo. Nội dung form vẫn được giữ; hãy thử lại.';
      isBusy = false;
      notifyListeners();
      return null;
    }
  }

  Future<List<AiTag>> analyzeImage(String imagePath) async {
    try {
      await ensureModelLoaded();
      final bytes = await readLocalFile(imagePath);
      return await _analyzeImageUseCase(bytes);
    } catch (_) {
      return [];
    }
  }

  Map<String, dynamic>? get composeDraft => composeDraftLocalDataSource.read();

  Future<void> saveComposeDraft(Map<String, dynamic> draft) =>
      composeDraftLocalDataSource.save(draft);

  Future<void> clearComposeDraft() => composeDraftLocalDataSource.clear();

  Future<void> discardComposeImage(String? path) async {
    if (path != null) await _cleanupComposeImages(onlyPath: path);
  }

  Future<void> _cleanupComposeImages({String? onlyPath}) async {
    try {
      final draftPath = composeDraft?['imagePath'];
      await cleanupComposeImages(
        onlyPath: onlyPath,
        keepPaths: {
          if (draftPath is String) draftPath,
          for (final record in rescueRepository.getAllRecords()) ...[
            ?record.imagePath,
            ...record.images,
          ],
        },
      );
    } catch (error) {
      // A busy file can be reclaimed on the next startup without failing a report.
      debugPrint('Chưa dọn được ảnh tạm của form: $error');
    }
  }

  Future<void> recoverPickerDraft() async {
    await _recoverPickerDraft();
    await _cleanupComposeImages();
  }

  Future<void> _recoverPickerDraft() async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      await clearComposeDraft();
      return;
    }
    try {
      final lost = await _picker.retrieveLostData();
      if (lost.isEmpty) {
        await clearComposeDraft();
        return;
      }
      final draft = composeDraft ?? <String, dynamic>{};
      final files = lost.files ?? [?lost.file];
      if (files.isNotEmpty) {
        // Store the recoverable cache path before attempting the durable copy.
        draft['imagePath'] = files.first.path;
        await saveComposeDraft(draft);
        draft['imagePath'] = await preserveLocalFile(
          files.first.path,
          newRecordId('compose-image'),
        );
        draft.remove('recoveryError');
      } else {
        draft['recoveryError'] =
            'Chưa khôi phục được ảnh. Nội dung bản nháp được giữ; hãy chọn lại ảnh.';
      }
      await saveComposeDraft(draft);
    } catch (error) {
      debugPrint('Chưa khôi phục được ảnh/bản nháp: $error');
      final draft = composeDraft;
      if (draft != null) {
        draft['recoveryError'] =
            'Chưa lưu được ảnh khôi phục. Nội dung bản nháp được giữ; hãy chọn lại ảnh nếu ảnh không còn.';
        try {
          await saveComposeDraft(draft);
        } catch (saveError) {
          debugPrint('Không ghi được cảnh báo khôi phục bản nháp: $saveError');
        }
      }
    }
  }

  Future<String?> pickImage({required ImageSource source}) async {
    String? copiedPath;
    try {
      final picked = await _picker.pickImage(
        source: source,
        maxWidth: 1200,
        maxHeight: 1200,
        imageQuality: 80,
      );
      if (picked == null) return null;
      final draft = composeDraft ?? <String, dynamic>{};
      draft['imagePath'] = picked.path;
      await saveComposeDraft(draft);
      final path = await preserveLocalFile(
        picked.path,
        newRecordId('compose-image'),
      );
      copiedPath = path;
      draft['imagePath'] = path;
      await saveComposeDraft(draft);
      return path;
    } catch (_) {
      if (copiedPath != null && composeDraft?['imagePath'] == copiedPath) {
        try {
          await clearComposeDraft();
        } catch (_) {
          debugPrint('Chưa xóa được snapshot của ảnh chọn lỗi.');
        }
      }
      await discardComposeImage(copiedPath);
      throw const FormatException(
        'Không lưu được ảnh đã chọn. Bản nháp vẫn được giữ; hãy chọn lại ảnh.',
      );
    }
  }

  Future<InferenceResult?> testModelBenchmark() async {
    if (!beginBenchmark()) return null;

    try {
      if (!await validateAdmin()) return null;
      await ensureModelLoaded();
      final ByteData raw = await rootBundle.load('assets/images/app_logo.webp');
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
      final last = lastSubmittedPost;
      if (last != null) {
        lastSubmittedPost = rescueRepository.getRecord(last.id) ?? last;
      }
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
    if (_disposed || !_foreground || networkLabel == 'none') return;
    final due =
        rescueRepository.nextRetryAt ??
        (records.any((r) => r.awaitingSync && r.metadataSynced)
            ? DateTime.now().toUtc().add(const Duration(seconds: 30))
            : null);
    if (due == null) return;
    final wait = due.difference(DateTime.now().toUtc());
    _retryTimer = Timer(
      // A missing server leaves the message overdue; avoid a zero-delay loop.
      wait <= Duration.zero
          ? const Duration(seconds: 30)
          : wait + const Duration(milliseconds: 50),
      () async {
        try {
          await syncPending(immediate: false);
        } catch (error) {
          debugPrint('Chưa gửi lại được báo cáo: $error');
        }
      },
    );
  }
}
