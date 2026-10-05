import 'package:dio/dio.dart';

import '../../config.dart';
import '../../core/platform/lan_candidates.dart';
import 'outbox_local_datasource.dart';

/// Tìm server Docker trong cùng mạng LAN và ghim mã DB để không gửi nhầm nơi.
class ServerLocator {
  static final Dio _dio = Dio(
    BaseOptions(
      connectTimeout: const Duration(milliseconds: 800),
      receiveTimeout: const Duration(milliseconds: 1500),
    ),
  );

  ServerLocator({
    Future<List<String>> Function(int port)? candidates,
    Future<String?> Function(String url)? probe,
  }) : _candidates = candidates ?? lanCandidates,
       _probe = probe ?? _probeServer;

  final Future<List<String>> Function(int port) _candidates;
  final Future<String?> Function(String url) _probe;
  OutboxLocalDataSource? _outbox;
  String? _connectedUrl;
  DateTime? _lastScan;

  String? get connectedUrl => _connectedUrl;

  Future<bool> init(OutboxLocalDataSource outbox) async {
    _outbox = outbox;
    return ensureConnected(force: true);
  }

  Future<bool> ensureConnected({bool force = false}) async {
    final outbox = _outbox!;
    final expectedId = outbox.serverId;
    final hints = <String>{
      ?_connectedUrl,
      ?outbox.serverUrl,
      kConfiguredServerUrl,
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
    final now = DateTime.now();
    if (!force &&
        _lastScan != null &&
        now.difference(_lastScan!) < const Duration(minutes: 1)) {
      return false;
    }
    _lastScan = now;

    final port = Uri.tryParse(kConfiguredServerUrl)?.port ?? 8000;
    late final List<String> urls;
    try {
      urls = await _candidates(port);
    } catch (_) {
      return false;
    }
    final found = <String, String>{};
    for (var i = 0; i < urls.length; i += 32) {
      final batch = urls.skip(i).take(32).toList();
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
