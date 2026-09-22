import 'package:flutter/material.dart';

import '../../core/constants/app_colors.dart';
import '../controllers/app_controller.dart';
import 'auth/login_screen.dart';
import 'auth/register_screen.dart';
import 'compose/compose_screen.dart';
import 'guide/guide_screen.dart';
import 'history/history_screen.dart';
import 'home/home_screen.dart';
import 'settings/settings_screen.dart';
import 'submitted/submitted_screen.dart';

enum AppViewMode { tabs, compose, submitted }

enum AuthViewMode { login, register }

class MainNavigationScreen extends StatefulWidget {
  final AppController controller;

  const MainNavigationScreen({super.key, required this.controller});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentTab = 0;
  AppViewMode _viewMode = AppViewMode.tabs;
  AuthViewMode _authMode = AuthViewMode.login;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onControllerChange);
    widget.controller.init();
  }

  void _onControllerChange() {
    if (mounted) setState(() {});
  }

  void _returnToTabs() {
    setState(() {
      _viewMode = AppViewMode.tabs;
      _currentTab = 0;
    });
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onControllerChange);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // 1. Auth Flow (if not authenticated and not in guest mode)
    if (!widget.controller.isAuthenticated) {
      if (_authMode == AuthViewMode.register) {
        return RegisterScreen(
          controller: widget.controller,
          onGoLogin: () => setState(() => _authMode = AuthViewMode.login),
          onRegisterSuccess: () => setState(() {
            _viewMode = AppViewMode.tabs;
            _currentTab = 0;
          }),
        );
      }
      return LoginScreen(
        controller: widget.controller,
        onGoRegister: () => setState(() => _authMode = AuthViewMode.register),
        onLoginSuccess: () => setState(() {
          _viewMode = AppViewMode.tabs;
          _currentTab = 0;
        }),
      );
    }

    // 2. Compose Flow
    if (_viewMode == AppViewMode.compose) {
      return PopScope(
        canPop: false,
        onPopInvokedWithResult: (didPop, result) {
          if (!didPop) _returnToTabs();
        },
        child: ComposeScreen(
          controller: widget.controller,
          onBack: _returnToTabs,
          onSuccess: () => setState(() => _viewMode = AppViewMode.submitted),
        ),
      );
    }

    // 3. Submitted Flow
    if (_viewMode == AppViewMode.submitted &&
        widget.controller.lastSubmittedPost != null) {
      return PopScope(
        canPop: false,
        onPopInvokedWithResult: (didPop, result) {
          if (!didPop) _returnToTabs();
        },
        child: SubmittedScreen(
          record: widget.controller.lastSubmittedPost!,
          onHomePressed: _returnToTabs,
        ),
      );
    }

    // 4. Main App with 4 Tabs
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      body: SafeArea(
        bottom: false,
        child: IndexedStack(
          index: _currentTab,
          children: [
            HomeScreen(
              controller: widget.controller,
              onComposePressed: () =>
                  setState(() => _viewMode = AppViewMode.compose),
            ),
            const GuideScreen(),
            HistoryScreen(controller: widget.controller),
            SettingsScreen(
              controller: widget.controller,
              onGoAuth: () => setState(() => _authMode = AuthViewMode.login),
            ),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentTab,
        onTap: (index) => setState(() => _currentTab = index),
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppColors.primaryRed,
        unselectedItemColor: const Color(0xFF9CA3AF),
        selectedLabelStyle: const TextStyle(
          fontWeight: FontWeight.w800,
          fontSize: 12,
        ),
        unselectedLabelStyle: const TextStyle(
          fontWeight: FontWeight.w600,
          fontSize: 12,
        ),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_rounded),
            label: 'Trang chủ',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.menu_book_rounded),
            label: 'Hướng dẫn',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.history_rounded),
            label: 'Lịch sử',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings_rounded),
            label: 'Cài đặt',
          ),
        ],
      ),
    );
  }
}
