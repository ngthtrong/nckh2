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
