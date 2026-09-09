import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../domain/entities/ai_tag.dart';
import '../../domain/entities/rescue_record.dart';
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

  AppController({
    required this.rescueRepository,
    required this.inferenceRepository,
    required this.networkRepository,
  }) {
    _sendSosUseCase = SendSosUseCase(rescueRepository);
    _submitRescuePostUseCase = SubmitRescuePostUseCase(rescueRepository);
    _getRescueRecordsUseCase = GetRescueRecordsUseCase(rescueRepository);
    _analyzeImageUseCase = AnalyzeImageUseCase(inferenceRepository);
    _syncPendingRecordsUseCase = SyncPendingRecordsUseCase(rescueRepository);
  }

  List<RescueRecord> get records => _getRescueRecordsUseCase();
  int get pendingCount => rescueRepository.getPendingCount();

  Future<void> init() async {
    await rescueRepository.init();
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
