import 'dart:async';
import 'dart:io';

import 'package:app/config.dart';
import 'package:app/data/datasources/outbox_local_datasource.dart';
import 'package:app/data/datasources/server_locator.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_ce_flutter/hive_flutter.dart';

void main() {
  late Directory dir;
  late OutboxLocalDataSource outbox;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('server_locator_test');
    outbox = OutboxLocalDataSource();
    await outbox.init(hivePath: dir.path);
  });

  tearDown(() async {
    setServerBaseUrl(kConfiguredServerUrl);
    await Hive.deleteFromDisk();
    await dir.delete(recursive: true);
  });

  for (final savedServer in [false, true]) {
    test(
      '${savedServer ? 'saved' : 'configured'} server may take over 700ms to answer health',
      () async {
        final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
        addTearDown(() => server.close(force: true));
        server.listen((request) async {
          await Future<void>.delayed(const Duration(milliseconds: 900));
          request.response.headers.contentType = ContentType.json;
          request.response.write(
            '{"status":"ok","serverId":"abcdef0123456789"}',
          );
          await request.response.close();
        });
        final url = 'http://127.0.0.1:${server.port}';
        if (savedServer) await outbox.saveServer('abcdef0123456789', url);
        final locator = ServerLocator(
          allowInsecureLan: true,
          allowLanScan: false,
          configuredUrl: savedServer ? '' : url,
        );

        expect(await locator.init(outbox), isTrue);
        expect(locator.connectedUrl, url);
        expect(outbox.serverId, 'abcdef0123456789');
      },
    );
  }

  test(
    'known server health timeout still finishes with no connection',
    () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      addTearDown(() => server.close(force: true));
      server.listen((_) {});
      final locator = ServerLocator(
        allowInsecureLan: true,
        allowLanScan: false,
        configuredUrl: 'http://127.0.0.1:${server.port}',
      );

      expect(
        await locator.init(outbox).timeout(const Duration(seconds: 8)),
        isFalse,
      );
      expect(locator.connectedUrl, isNull);
      expect(outbox.serverId, isNull);
    },
  );

  test('LAN discovery retains a short health timeout', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(() => server.close(force: true));
    server.listen((_) {});
    final locator = ServerLocator(
      allowInsecureLan: true,
      configuredUrl: '',
      candidates: (_) async => ['http://127.0.0.1:${server.port}'],
    );

    expect(
      await locator.init(outbox).timeout(const Duration(seconds: 2)),
      isFalse,
    );
  });

  test(
    'concurrent connection requests share the same identity probe',
    () async {
      final response = Completer<String?>();
      var probes = 0;
      final locator = ServerLocator(
        configuredUrl: 'https://rescue.example',
        probe: (_) {
          probes++;
          return response.future;
        },
      );
      locator.attach(outbox);

      final first = locator.ensureConnected();
      final second = locator.ensureConnected(force: true);
      expect(probes, 1);
      response.complete('abcdef0123456789');

      expect(await Future.wait([first, second]), [true, true]);
      expect(locator.connectedUrl, 'https://rescue.example');
      expect(await locator.ensureConnected(force: true), isTrue);
      expect(probes, 2);
    },
  );

  test(
    'failed LAN scans back off 1/2/5 minutes; manual reconnect bypasses delay',
    () async {
      var now = DateTime(2026);
      var scans = 0;
      final locator = ServerLocator(
        allowInsecureLan: true,
        now: () => now,
        candidates: (_) async {
          scans++;
          return [];
        },
        probe: (_) async => null,
      );
      locator.attach(outbox);
      await locator.ensureConnected();
      expect(scans, 1);
      now = now.add(const Duration(seconds: 59));
      await locator.ensureConnected();
      expect(scans, 1);
      now = now.add(const Duration(seconds: 1));
      await locator.ensureConnected();
      expect(scans, 2);
      now = now.add(const Duration(minutes: 1));
      await locator.ensureConnected();
      expect(scans, 2);
      now = now.add(const Duration(minutes: 1));
      await locator.ensureConnected();
      expect(scans, 3);
      now = now.add(const Duration(minutes: 4));
      await locator.ensureConnected();
      expect(scans, 3);
      await locator.ensureConnected(force: true);
      expect(scans, 4);
    },
  );

  test('tìm lại đúng DB khi IP đổi, từ chối server khác ở IP cũ', () async {
    const oldUrl = 'https://192.168.6.10:8000';
    const newUrl = 'https://192.168.6.20:8000';
    const id = 'abcdef0123456789';
    var currentUrl = oldUrl;
    final locator = ServerLocator(
      allowInsecureLan: true,
      candidates: (_) async => [oldUrl, newUrl],
      probe: (url) async {
        if (url == currentUrl) return id;
        if (url == oldUrl) return '9876543210abcdef';
        return null;
      },
    );

    expect(await locator.init(outbox), isTrue);
    expect(outbox.serverId, id);
    expect(kServerBaseUrl, oldUrl);

    currentUrl = newUrl;
    expect(await locator.ensureConnected(force: true), isTrue);
    expect(outbox.serverUrl, newUrl);
    expect(kServerBaseUrl, newUrl);

    currentUrl = '';
    expect(await locator.ensureConnected(force: true), isFalse);
    expect(locator.connectedUrl, isNull);
    expect(outbox.serverId, id);
    expect(kServerBaseUrl, 'http://127.0.0.1:1');
  });

  test('nhiều server mới cùng LAN thì không tự chọn bừa', () async {
    final locator = ServerLocator(
      allowInsecureLan: true,
      candidates: (_) async => [
        'https://192.168.6.10:8000',
        'https://192.168.6.20:8000',
      ],
      probe: (url) async => url.contains('.10:')
          ? 'abcdef0123456789'
          : url.contains('.20:')
          ? '9876543210abcdef'
          : null,
    );

    expect(await locator.init(outbox), isFalse);
    expect(outbox.serverId, isNull);
    expect(locator.connectedUrl, isNull);
  });

  test('background chỉ thử URL đã biết, không quét LAN khi giữ Hive', () async {
    const savedUrl = 'http://192.168.1.20:8000';
    const configuredUrl = 'http://192.168.1.10:8000';
    await outbox.saveServer('abcdef0123456789', savedUrl);
    final probed = <String>[];
    var scannedLan = false;
    final locator = ServerLocator(
      allowInsecureLan: true,
      allowLanScan: false,
      configuredUrl: configuredUrl,
      candidates: (_) async {
        scannedLan = true;
        return [];
      },
      probe: (url) async {
        probed.add(url);
        return null;
      },
    );

    locator.attach(outbox);
    expect(probed, isEmpty);
    expect(await locator.ensureConnected(force: true), isFalse);
    expect(probed, [savedUrl, configuredUrl]);
    expect(scannedLan, isFalse);
  });

  test(
    'production probes only configured HTTPS origin, never saved URL or LAN',
    () async {
      await outbox.saveServer('abcdef0123456789', 'http://192.168.1.2:8000');
      final probed = <String>[];
      final locator = ServerLocator(
        configuredUrl: 'https://rescue.example',
        candidates: (_) async => throw StateError('must not scan'),
        probe: (url) async {
          probed.add(url);
          return 'abcdef0123456789';
        },
      );
      expect(await locator.init(outbox), isTrue);
      expect(probed, ['https://rescue.example']);
    },
  );

  test(
    'production rejects HTTP before probing even with a pinned DB id',
    () async {
      await outbox.saveServer('abcdef0123456789', 'http://192.168.1.2:8000');
      final locator = ServerLocator(
        configuredUrl: 'http://192.168.1.2:8000',
        candidates: (_) async => throw StateError('must not scan'),
        probe: (_) async => throw StateError('must not probe'),
      );
      expect(await locator.init(outbox), isFalse);
    },
  );
}
