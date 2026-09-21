import 'package:flutter/material.dart';

import 'app.dart';
import 'controllers/rescue_controller.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final controller = await RescueController.create();
  runApp(RescueApp(controller: controller));
}

