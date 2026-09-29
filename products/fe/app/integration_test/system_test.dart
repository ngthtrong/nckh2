// Kiểm thử tích hợp app ↔ server thật (Docker) trên thiết bị desktop Linux/WSLg.
//
//   docker compose up -d                       # backend ở cổng 8000
//   cd products/fe/app
//   flutter test integration_test/system_test.dart -d linux \
//     --dart-define=SERVER_URL=http://127.0.0.1:8099 \
//     --dart-define=E2E_IMAGE=$PWD/../model/Dataset_Flood/high/flood_4791.jpg
//
// App gọi server qua cổng chuyển tiếp 8099 do chính test mở/đóng để giả lập mất mạng
// rồi có mạng lại; test kiểm tra kết quả trực tiếp ở cổng 8000 bằng tài khoản quản trị
// (E2E_ADMIN_USER / E2E_ADMIN_PASSWORD, mặc định admin / cuuho2026). Chạy code thật
// của app: Hive outbox, Dio, JCS, gửi thích ứng (/probe), upload ảnh kèm clientId.
// Test ghi báo cáo thật vào DB của container be.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:app/config.dart';
import 'package:app/data/datasources/network_remote_datasource.dart';
import 'package:app/data/datasources/outbox_local_datasource.dart';
import 'package:app/data/datasources/record_local_datasource.dart';
import 'package:app/data/datasources/sender_remote_datasource.dart';
import 'package:app/data/repositories/network_repository_impl.dart';
import 'package:app/data/repositories/rescue_repository_impl.dart';
import 'package:app/domain/entities/send_mode.dart';
import 'package:app/domain/services/adaptive_send_policy.dart';
import 'package:app/domain/usecases/send_sos_usecase.dart';
import 'package:app/domain/usecases/submit_rescue_post_usecase.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

const _backend = String.fromEnvironment(
  'E2E_BACKEND',
  defaultValue: 'http://127.0.0.1:8000',
);
const _image = String.fromEnvironment('E2E_IMAGE');
const _adminUser = String.fromEnvironment(
  'E2E_ADMIN_USER',
  defaultValue: 'admin',
);
const _adminPassword = String.fromEnvironment(
  'E2E_ADMIN_PASSWORD',
  defaultValue: 'cuuho2026',
);

/// Cổng TCP chuyển tiếp tới backend: [up] = có mạng, [down] = mất mạng (đóng cả
/// kết nối đang mở để Dio không dùng lại kết nối cũ).
class _Link {
  _Link(this.port, this.target);
  final int port;
  final Uri target;
  ServerSocket? _server;
  final _sockets = <Socket>{};

  Future<void> up() async {
    _server = await ServerSocket.bind(InternetAddress.loopbackIPv4, port);
    _server!.listen((client) async {
      try {
        final upstream = await Socket.connect(target.host, target.port);
        _sockets.addAll([client, upstream]);
        unawaited(client.cast<List<int>>().pipe(upstream).catchError((_) {}));
        unawaited(upstream.cast<List<int>>().pipe(client).catchError((_) {}));
      } catch (_) {
        client.destroy();
      }
    });
  }

  Future<void> down() async {
    await _server?.close();
    _server = null;
    for (final s in _sockets) {
      s.destroy();
    }
    _sockets.clear();
  }
}

/// Gọi thẳng backend (cổng 8000) để kiểm chứng, như điều phối viên / kẻ tấn công.
class _Api {
  final _http = HttpClient();
  String? token;

  Future<(int, dynamic)> send(
    String method,
    String path, {
    Object? json,
    Map<String, String> headers = const {},
    (String, List<int>)? multipart,
  }) async {
    final req = await _http.openUrl(method, Uri.parse('$_backend$path'));
    if (token != null) req.headers.set('Authorization', 'Bearer $token');
    headers.forEach(req.headers.set);
    if (json != null) {
      req.headers.contentType = ContentType.json;
      req.write(jsonEncode(json));
    } else if (multipart != null) {
      const boundary = 'e2e-boundary';
      req.headers.set(
        'content-type',
        'multipart/form-data; boundary=$boundary',
      );
      req.add(
        utf8.encode(
          '--$boundary\r\nContent-Disposition: form-data; name="${multipart.$1}"'
          '\r\n\r\n',
        ),
      );
      req.add(multipart.$2);
      req.add(utf8.encode('\r\n--$boundary--\r\n'));
    }
    final res = await req.close();
    final body = await utf8.decodeStream(res);
    return (res.statusCode, body.isEmpty ? null : jsonDecode(body));
  }

  Future<Map<String, dynamic>> report(String id) async {
    final (status, body) = await send('GET', '/api/reports/$id');
    expect(status, 200, reason: 'server phải có báo cáo $id');
    return body as Map<String, dynamic>;
  }
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  late Directory dir;
  late RescueRepositoryImpl repo;
  late AdaptiveSendPolicy policy;
  final link = _Link(Uri.parse(kServerBaseUrl).port, Uri.parse(_backend));
  final api = _Api();

  setUpAll(() async {
    expect(
      Uri.parse(kServerBaseUrl).port,
      isNot(Uri.parse(_backend).port),
      reason: 'build với --dart-define=SERVER_URL=http://127.0.0.1:8099',
    );
    final (status, body) = await api.send(
      'POST',
      '/api/auth/login',
      json: {'username': _adminUser, 'password': _adminPassword},
    );
    expect(status, 200, reason: 'đăng nhập quản trị để kiểm chứng: $body');
    api.token = (body as Map)['token'] as String;

    dir = await Directory.systemTemp.createTemp('rescue_e2e');
    final records = RecordLocalDataSource();
    final outbox = OutboxLocalDataSource();
    await records.init(hivePath: dir.path);
    await outbox.init(hivePath: dir.path);
    policy = AdaptiveSendPolicy(
      NetworkRepositoryImpl(NetworkRemoteDataSource()),
    );
    repo = RescueRepositoryImpl(
      localDataSource: records,
      senderDataSource: SenderRemoteDataSource(),
      outboxDataSource: outbox,
      sendPolicy: policy,
    );
  });

  tearDownAll(() async {
    await link.down();
    await dir.delete(recursive: true);
  });

  Future<SendMode> decide({required bool hasImage}) async =>
      (await policy.decide(hasImage: hasImage, confidence: 0)).mode;

  testWidgets('SOS khi mất mạng nằm trong outbox, có mạng thì tới server', (
    _,
  ) async {
    await link.down();
    final mode = await decide(hasImage: false);
    final sos = await SendSosUseCase(
      repo,
    ).call(lat: 16.0544, lng: 108.2022, sendMode: mode);
    expect(sos.synced, isFalse);
    expect(sos.syncError, isNull);
    expect(repo.getPendingCount(), 1);
    // Desktop không có SMS: bản ghi được ghi là xếp hàng offline.
    expect(sos.sendMode, anyOf('queuedOffline', 'textOnly'));

    await link.up();
    await repo.syncPendingRecords();
    expect(repo.getPendingCount(), 0);
    final onServer = await api.report(sos.id);
    expect(onServer['lat'], 16.0544);
    expect(onServer['status'], 'processing');
    expect((onServer['payload'] as Map).containsKey('clientId'), isFalse);
  });

  testWidgets('bài có ảnh: đo /probe, upload ảnh, điều phối và chặn giả mạo', (
    _,
  ) async {
    expect(_image, isNotEmpty, reason: 'truyền --dart-define=E2E_IMAGE=...');
    await link.up().catchError((_) {}); // có thể đã mở từ test trước
    final mode = await decide(hasImage: true);
    expect(mode, isIn([SendMode.fullImage, SendMode.compressedImage]));
    final post = await SubmitRescuePostUseCase(repo).call(
      lat: null,
      lng: null,
      imagePath: _image,
      trappedCount: 0,
      injuredCount: 2,
      vulnerableGroups: const ['elderly'],
      description: 'Nhà ngập tới mái, không có GPS',
      sendMode: mode,
    );
    expect(post.synced, isTrue, reason: 'metadata + ảnh phải gửi xong');

    var onServer = await api.report(post.id);
    expect(onServer['imageUrl'], isNotNull);
    expect(onServer['lat'], isNull, reason: 'không GPS → hàng xác minh');
    expect(onServer['trappedCount'], 0);

    // Người ngoài biết id: không sửa được vị trí / số người / SĐT (S1).
    final forged = {
      'id': post.id,
      'lat': 21.0,
      'lng': 105.8,
      'trappedCount': 50,
      'contactPhone': '+84999',
    };
    final (conflict, detail) = await _Api().send(
      'POST',
      '/api/reports',
      headers: {'X-Message-Contract-Version': '1'},
      multipart: ('meta', utf8.encode(jsonEncode(forged))),
    );
    expect(conflict, 409, reason: '$detail');
    onServer = await api.report(post.id);
    expect(
      (onServer['lat'], onServer['trappedCount'], onServer['contactPhone']),
      (null, 0, null),
    );

    // Điều phối viên điều đội; app nhận trạng thái mới qua GET /api/reports/status.
    final (patched, patchBody) = await api.send(
      'PATCH',
      '/api/reports/${post.id}/status',
      json: {'status': 'dispatched', 'statusVersion': 2},
    );
    expect(patched, 200, reason: '$patchBody');
    final changed = await repo.refreshStatuses();
    expect(changed.where((r) => r.id == post.id).single.status, 'dispatched');
  });
}
