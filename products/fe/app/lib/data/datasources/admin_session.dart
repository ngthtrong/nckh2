import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../../config.dart';

/// Admin privilege comes from the backend, never from the local profile name.
class AdminSession extends ChangeNotifier {
  AdminSession({Dio? dio})
    : _dio =
          dio ??
          Dio(
            BaseOptions(
              connectTimeout: const Duration(seconds: 8),
              receiveTimeout: const Duration(seconds: 15),
              followRedirects: false,
            ),
          );

  final Dio _dio;
  String? _token;
  String? server;
  String? username;
  DateTime? _expires;
  Timer? _expiryTimer;
  int _generation = 0;

  bool get isAdmin =>
      _token != null && _expires != null && DateTime.now().isBefore(_expires!);
  String? get token => isAdmin ? _token : null;

  Future<void> login(String baseUrl, String name, String password) async {
    await logout();
    final generation = _generation;
    final origin = baseUrl.replaceAll(RegExp(r'/+$'), '');
    requireAllowedServerUrl(origin);
    final response = await _dio.post<dynamic>(
      '$origin/api/auth/login',
      data: {'username': name.trim(), 'password': password},
      options: Options(contentType: Headers.jsonContentType),
    );
    final data = response.data;
    final receivedToken = data is Map ? data['token'] : null;
    final expires = data is Map
        ? DateTime.tryParse('${data['expiresAt']}')
        : null;
    if (generation != _generation ||
        data is! Map ||
        data['role'] != 'admin' ||
        receivedToken is! String ||
        receivedToken.isEmpty ||
        expires == null ||
        !DateTime.now().isBefore(expires)) {
      if (receivedToken is String) await _revoke(origin, receivedToken);
      throw StateError('Cần tài khoản có quyền admin trên server.');
    }
    _token = receivedToken;
    server = origin;
    username = data['username'] as String? ?? name.trim();
    _expires = expires;
    _expiryTimer = Timer(
      expires.difference(DateTime.now()),
      () => unawaited(logout()),
    );
    notifyListeners();
  }

  Future<bool> validate() async {
    final currentToken = token;
    final origin = server;
    if (currentToken == null || origin == null) {
      await logout();
      return false;
    }
    try {
      final response = await _dio.get<dynamic>(
        '$origin/api/auth/me',
        options: Options(headers: {'Authorization': 'Bearer $currentToken'}),
      );
      if (_token != currentToken) return false;
      final data = response.data;
      if (data is Map &&
          data['authenticated'] == true &&
          data['role'] == 'admin') {
        return true;
      }
      await logout();
      return false;
    } on DioException catch (error) {
      if (_token == currentToken &&
          const [401, 403].contains(error.response?.statusCode)) {
        await logout();
      }
      rethrow;
    }
  }

  Future<void> logout() async {
    final oldToken = _token;
    final oldServer = server;
    _generation++;
    _token = null;
    server = null;
    username = null;
    _expires = null;
    _expiryTimer?.cancel();
    notifyListeners();
    if (oldToken != null && oldServer != null) {
      await _revoke(oldServer, oldToken);
    }
  }

  Future<void> _revoke(String origin, String value) async {
    try {
      await _dio.post<void>(
        '$origin/api/auth/logout',
        options: Options(headers: {'Authorization': 'Bearer $value'}),
      );
    } catch (_) {
      // Offline logout clears local access immediately; server expiry revokes the remote session.
    }
  }

  @override
  void dispose() {
    _generation++;
    _expiryTimer?.cancel();
    _dio.close(force: true);
    super.dispose();
  }
}
