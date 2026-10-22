import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:hive_ce_flutter/hive_flutter.dart';
import 'package:workmanager/workmanager.dart';

import 'core/platform/sync_isolate_guard.dart';
import 'core/platform/background_sync_schedule.dart';
import 'domain/services/sync_activity.dart';

import 'data/datasources/inference_local_datasource.dart';
import 'data/datasources/network_remote_datasource.dart';
import 'data/datasources/record_local_datasource.dart';
import 'data/datasources/sender_remote_datasource.dart';
import 'data/datasources/server_locator.dart';
import 'data/repositories/inference_repository_impl.dart';
import 'data/repositories/network_repository_impl.dart';
import 'data/repositories/rescue_repository_impl.dart';
import 'domain/services/adaptive_send_policy.dart';
import 'presentation/controllers/app_controller.dart';
import 'presentation/screens/splash_screen.dart';

@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    try {
      if (await delegateSyncToForeground()) return true;
      return await runBackgroundSync(_syncInBackground, closeHive: Hive.close);
    } catch (error) {
      debugPrint('Đồng bộ nền chưa hoàn tất, sẽ thử lại: $error');
      return false;
    }
  });
}

Future<void> _syncInBackground() async {
  final recordLocalDS = RecordLocalDataSource();
  final senderRemoteDS = SenderRemoteDataSource();
  final rescueRepo = RescueRepositoryImpl(
    localDataSource: recordLocalDS,
    senderDataSource: senderRemoteDS,
    serverLocator: !kIsWeb && defaultTargetPlatform == TargetPlatform.android
        // Worker holds the Hive lease; avoid subnet scans while it is held.
        ? ServerLocator(allowLanScan: false)
        : null,
    sendPolicy: AdaptiveSendPolicy(
      NetworkRepositoryImpl(NetworkRemoteDataSource()),
    ),
  );
  await rescueRepo.init();
  if (!hasSyncWork(rescueRepo.getAllRecords())) return;
  await rescueRepo.syncPendingRecords();
  try {
    await rescueRepo.refreshStatuses();
  } catch (_) {
    // Mất mạng giữa chừng: lần chạy sau (15 phút) sẽ thử lại.
  }
  await updateBackgroundSync(hasSyncWork(rescueRepo.getAllRecords()));
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (!kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS)) {
    await Workmanager().initialize(callbackDispatcher);
  }

  final recordLocalDS = RecordLocalDataSource();
  final senderRemoteDS = SenderRemoteDataSource();
  final inferenceLocalDS = InferenceLocalDataSource();
  final networkRemoteDS = NetworkRemoteDataSource();

  final networkRepository = NetworkRepositoryImpl(networkRemoteDS);
  final rescueRepository = RescueRepositoryImpl(
    localDataSource: recordLocalDS,
    senderDataSource: senderRemoteDS,
    serverLocator: !kIsWeb && defaultTargetPlatform == TargetPlatform.android
        ? ServerLocator()
        : null,
    sendPolicy: AdaptiveSendPolicy(networkRepository),
  );
  final inferenceRepository = InferenceRepositoryImpl(inferenceLocalDS);

  final controller = AppController(
    rescueRepository: rescueRepository,
    inferenceRepository: inferenceRepository,
    networkRepository: networkRepository,
  );

  runApp(RescueApp(controller: controller));
}

class RescueApp extends StatelessWidget {
  final AppController controller;

  const RescueApp({super.key, required this.controller});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Cứu hộ khẩn cấp',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Roboto',
        colorSchemeSeed: const Color(0xFFC62828),
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF7F7F7),
        splashFactory: NoSplash.splashFactory,
        hoverColor: Colors.transparent,
        highlightColor: Colors.transparent,
      ),
      home: SplashScreen(controller: controller),
    );
  }
}
