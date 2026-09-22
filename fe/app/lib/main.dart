import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:workmanager/workmanager.dart';

import 'data/datasources/inference_local_datasource.dart';
import 'data/datasources/network_remote_datasource.dart';
import 'data/datasources/record_local_datasource.dart';
import 'data/datasources/sender_remote_datasource.dart';
import 'data/repositories/inference_repository_impl.dart';
import 'data/repositories/network_repository_impl.dart';
import 'data/repositories/rescue_repository_impl.dart';
import 'presentation/controllers/app_controller.dart';
import 'presentation/screens/splash_screen.dart';

@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    final recordLocalDS = RecordLocalDataSource();
    final senderRemoteDS = SenderRemoteDataSource();
    final rescueRepo = RescueRepositoryImpl(
      localDataSource: recordLocalDS,
      senderDataSource: senderRemoteDS,
    );
    await rescueRepo.init();
    await rescueRepo.syncPendingRecords();
    return true;
  });
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (!kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS)) {
    await Workmanager().initialize(callbackDispatcher);
    await Workmanager().registerPeriodicTask(
      'rescue-outbox-sync',
      'syncPendingMessages',
      frequency: const Duration(minutes: 15),
      constraints: Constraints(networkType: NetworkType.connected),
    );
  }

  final recordLocalDS = RecordLocalDataSource();
  final senderRemoteDS = SenderRemoteDataSource();
  final inferenceLocalDS = InferenceLocalDataSource();
  final networkRemoteDS = NetworkRemoteDataSource();

  final rescueRepository = RescueRepositoryImpl(
    localDataSource: recordLocalDS,
    senderDataSource: senderRemoteDS,
  );
  final inferenceRepository = InferenceRepositoryImpl(inferenceLocalDS);
  final networkRepository = NetworkRepositoryImpl(networkRemoteDS);

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
      ),
      home: SplashScreen(controller: controller),
    );
  }
}
