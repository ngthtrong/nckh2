import 'dart:async';
import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../data/datasources/user_local_datasource.dart';
import '../../domain/entities/ai_model_type.dart';
import '../../domain/entities/ai_tag.dart';
import '../../domain/entities/rescue_record.dart';
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

  final ImagePicker _picker = ImagePicker();
  StreamSubscription<List<ConnectivityResult>>? _connSub;

  bool isBusy = false;
  String networkLabel = 'WiFi';
  bool isModelReady = false;
  String locationLabel = 'GPS tự động · TP. Hồ Chí Minh';
  double currentLat = 10.7769;
  double currentLng = 106.7009;

  RescueRecord? lastSubmittedPost;
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
  bool get isDualComparison => inferenceRepository.isDualComparison;
  ModelBenchmarkComparison? get latestComparison => inferenceRepository.latestComparison;

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
    unawaited(inferenceRepository.loadModel().then((_) {
      isModelReady = inferenceRepository.ready;
      notifyListeners();
    }));

    unawaited(Permission.locationWhenInUse.request().then((_) async {
      try {
        final pos = await Geolocator.getCurrentPosition(
          desiredAccuracy: LocationAccuracy.high,
          timeLimit: const Duration(seconds: 5),
        );
        currentLat = pos.latitude;
        currentLng = pos.longitude;
        locationLabel =
            '${currentLat.toStringAsFixed(4)}° N, ${currentLng.toStringAsFixed(4)}° E · TP. Hồ Chí Minh';
        notifyListeners();
      } catch (_) {}
    }));

    _connSub = networkRepository.networkChanges.listen((results) async {
      networkLabel = await networkRepository.getCurrentNetworkType();
      notifyListeners();
      final hasNet = results.any((e) =>
          e == ConnectivityResult.wifi || e == ConnectivityResult.mobile);
      if (hasNet && pendingCount > 0) {
        await syncPending();
      }
    });

    networkLabel = await networkRepository.getCurrentNetworkType();
    notifyListeners();
  }

  @override
  void dispose() {
    _connSub?.cancel();
    super.dispose();
  }

  Future<RescueRecord?> sendSos() async {
    if (isBusy) return null;
    isBusy = true;
    notifyListeners();

    try {
      final record = await _sendSosUseCase(
        lat: currentLat,
        lng: currentLng,
        sendMode: networkLabel == 'none' ? 'queuedOffline' : 'direct',
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
        sendMode: networkLabel == 'none' ? 'queuedOffline' : 'direct',
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
      final bytes = await File(imagePath).readAsBytes();
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

  Future<void> syncPending() async {
    await _syncPendingRecordsUseCase();
    notifyListeners();
  }
}
