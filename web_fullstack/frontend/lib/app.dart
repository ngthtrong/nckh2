import 'dart:async';

import 'package:flutter/material.dart';

import 'controllers/rescue_controller.dart';
import 'screens/home_screen.dart';
import 'services/browser_online_events.dart';

class RescueApp extends StatefulWidget {
  const RescueApp({super.key, required this.controller});

  final RescueController controller;

  @override
  State<RescueApp> createState() => _RescueAppState();
}

class _RescueAppState extends State<RescueApp> {
  StreamSubscription<void>? _onlineSubscription;

  @override
  void initState() {
    super.initState();
    widget.controller.initialize();
    _onlineSubscription = browserOnlineEvents.listen((_) {
      unawaited(widget.controller.retrySync());
    });
  }

  @override
  void dispose() {
    _onlineSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Cứu hộ lũ lụt',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFB42318),
          primary: const Color(0xFFB42318),
          secondary: const Color(0xFF2D6A8A),
          surface: Colors.white,
        ),
        scaffoldBackgroundColor: const Color(0xFFF4F7F8),
        fontFamily: 'Segoe UI',
        useMaterial3: true,
        inputDecorationTheme: const InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(),
        ),
      ),
      home: HomeScreen(controller: widget.controller),
    );
  }
}
