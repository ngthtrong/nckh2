import 'package:dio/dio.dart';

import '../../config.dart';
import '../../core/platform/lan_candidates.dart';
import 'outbox_local_datasource.dart';

/// Tìm server Docker trong cùng mạng LAN và ghim mã DB để không gửi nhầm nơi.
class ServerLocator {
  static final Dio _dio = Dio(
    BaseOptions(
      connectTimeout: const Duration(milliseconds: 400),
      receiveTimeout: const Duration(milliseconds: 700),
      followRedirects: false,
    ),
  );

  ServerLocator({
    Future<List<String>> Function(int port)? candidates,
    Future<String?> Function(String url)? probe,
    this.allowInsecureLan = kAllowInsecureLan,
    this.allowLanScan = true,
    this.configuredUrl = kConfiguredServerUrl,
  }) : _candidates = candidates ?? lanCandidates,
       _probe = probe ?? _probeServer;

  final Future<List<String>> Function(int port) _candidates;
  final Future<String?> Function(String url) _probe;
  final bool allowInsecureLan;
  final bool allowLanScan;
  final String configuredUrl;
  OutboxLocalDataSource? _outbox;
  String? _connectedUrl;
  DateTime? _lastScan;

  String? get connectedUrl => _connectedUrl;

  void attach(OutboxLocalDataSource outbox) {
    _outbox = outbox;
    _connectedUrl = null;
    setServerBaseUrl(null);
  }

  Future<bool> init(OutboxLocalDataSource outbox) async {
    attach(outbox);
    return ensureConnected(force: true);
  }

  Future<bool> ensureConnected({bool force = false}) async {
    final outbox = _outbox!;
    final expectedId = outbox.serverId;
    final hints = <String>{
      if (allowInsecureLan) ...[?_connectedUrl, ?outbox.serverUrl],
      configuredUrl,
    };
    for (final url in hints) {
      final id = await _identity(url);
      if (id != null && (expectedId == null || id == expectedId)) {
        await _connect(outbox, id, url);
        return true;
      }
    }

    _connectedUrl = null;
    setServerBaseUrl(null);
    if (!allowInsecureLan || !allowLanScan) return false;
    final now = DateTime.now();
    if (!force &&
        _lastScan != null &&
        now.difference(_lastScan!) < const Duration(minutes: 1)) {
      return false;
    }
    _lastScan = now;

    final configured = Uri.tryParse(configuredUrl);
    final port = configured?.hasPort == true ? configured!.port : 8000;
    late final List<String> urls;
    try {
      urls = await _candidates(port);
    } catch (_) {
      return false;
    }
    final found = <String, String>{};
    for (var i = 0; i < urls.length; i += 128) {
      final batch = urls.skip(i).take(128).toList();
      final identities = await Future.wait(batch.map(_identity));
      for (var j = 0; j < identities.length; j++) {
        final id = identities[j];
        if (id == null) continue;
        final url = batch[j];
        if (expectedId != null && id == expectedId) {
          await _connect(outbox, id, url);
          return true;
        }
        if (expectedId == null) found[id] = url;
      }
    }
    // Chưa từng ghim server: nhiều DB cùng mạng thì không thể chọn an toàn.
    if (expectedId == null && found.length == 1) {
      final entry = found.entries.single;
      await _connect(outbox, entry.key, entry.value);
      return true;
    }
    return false;
  }

  Future<String?> _identity(String url) async {
    if (!isAllowedServerUrl(url, allowInsecureLan: allowInsecureLan)) {
      return null;
    }
    try {
      return await _probe(url);
    } catch (_) {
      return null;
    }
  }

  Future<void> _connect(
    OutboxLocalDataSource outbox,
    String id,
    String url,
  ) async {
    await outbox.saveServer(id, url);
    _connectedUrl = url;
    setServerBaseUrl(url);
  }

  static Future<String?> _probeServer(String url) async {
    final response = await _dio.get<Map<String, dynamic>>('$url/healthz');
    final data = response.data;
    final id = data?['serverId'];
    if (data?['status'] != 'ok' || id is! String) return null;
    return RegExp(r'^[0-9a-f]{16}$').hasMatch(id) ? id : null;
  }
}
