import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:app/core/platform/mobile_e2e_bundle.dart';
import 'package:app/domain/services/mobile_e2e_runner.dart';
import 'package:app/config.dart' show kAdminModelTools;

class CorruptedBundle extends CachingAssetBundle {
  @override
  Future<ByteData> load(String key) async {
    final original = await rootBundle.load(key);
    if (!key.endsWith('run_002.rhe')) return original;
    final bytes = Uint8List.fromList(Uint8List.sublistView(original));
    bytes[bytes.length - 1] ^= 1;
    return ByteData.sublistView(bytes);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test(
    'APK chứa hai run, dùng lại được cho nhiều lượt và giữ seed1024',
    () async {
      final bundle = await MobileE2eBundle.load();
      expect(bundle.runs.map((r) => r['goldRun']), ['run_001', 'run_002']);
      for (final name in ['run_001', 'run_002']) {
        final fixture = bundle.packages[name]!;
        expect(fixture.manifest.containsKey('sessionId'), isFalse);
        expect((fixture.manifest['model'] as Map)['seed'], 1024);
        final first = fixture.forBenchmark('2026-10-23_16-00-00_mobile_$name');
        final second = fixture.forBenchmark('2026-10-24_16-00-00_mobile_$name');
        expect(first.hash, second.hash);
        expect(first.image, second.image);
        final progress = MobileE2eCheckpoint(first, 'phone').toJson();
        expect(
          () => MobileE2eCheckpoint.restore(second, 'phone', progress),
          throwsStateError,
        );
        expect(fixture.manifest.containsKey('sessionId'), isFalse);
      }
    },
  );
  test('run 2 sai dữ liệu thì không mở gói benchmark', () async {
    await expectLater(
      MobileE2eBundle.load(bundle: CorruptedBundle()),
      throwsFormatException,
    );
  });
  test('E2E mặc định theo bản admin khi không thêm dart define', () {
    expect(mobileE2eEnabled, kAdminModelTools);
  });
}
