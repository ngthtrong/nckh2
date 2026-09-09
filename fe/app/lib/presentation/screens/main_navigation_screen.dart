import 'package:flutter/material.dart';

import '../../core/constants/app_colors.dart';
import '../controllers/app_controller.dart';
import 'compose/compose_screen.dart';
import 'guide/guide_screen.dart';
import 'history/history_screen.dart';
import 'home/home_screen.dart';
import 'submitted/submitted_screen.dart';

enum AppViewMode { tabs, compose, submitted }

class MainNavigationScreen extends StatefulWidget {
  final AppController controller;

  const MainNavigationScreen({super.key, required this.controller});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentTab = 0;
  AppViewMode _viewMode = AppViewMode.tabs;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onControllerChange);
    widget.controller.init();
  }

  void _onControllerChange() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onControllerChange);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_viewMode == AppViewMode.compose) {
      return ComposeScreen(
        controller: widget.controller,
        onBack: () => setState(() => _viewMode = AppViewMode.tabs),
        onSuccess: () => setState(() => _viewMode = AppViewMode.submitted),
      );
    }

    if (_viewMode == AppViewMode.submitted &&
        widget.controller.lastSubmittedPost != null) {
      return SubmittedScreen(
        record: widget.controller.lastSubmittedPost!,
        onHomePressed: () => setState(() {
          _viewMode = AppViewMode.tabs;
          _currentTab = 0;
        }),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      body: SafeArea(
        bottom: false,
        child: IndexedStack(
          index: _currentTab,
          children: [
            HomeScreen(
              controller: widget.controller,
              onComposePressed: () => setState(() => _viewMode = AppViewMode.compose),
            ),
            HistoryScreen(controller: widget.controller),
            const GuideScreen(),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentTab,
        onTap: (index) => setState(() => _currentTab = index),
        selectedItemColor: AppColors.primaryRed,
        unselectedItemColor: const Color(0xFF9CA3AF),
        selectedLabelStyle: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12),
        unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_rounded),
            label: 'Trang chủ',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.history_rounded),
            label: 'Lịch sử',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.menu_book_rounded),
            label: 'Hướng dẫn',
          ),
        ],
      ),
    );
  }
}
