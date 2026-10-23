// Both fixtures are bundled in the APK; the coordinator binds each to a live benchmark.
import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:flutter/services.dart';
import '../../domain/services/mobile_e2e_runner.dart';

class MobileE2eBundle {
  static const assetRoot = 'assets/benchmarks/mobile';
  final List<Map<String, dynamic>> runs;
  final Map<String, MobileE2ePackage> packages;
  MobileE2eBundle._(this.runs, this.packages);

  static Future<MobileE2eBundle> load({AssetBundle? bundle}) async {
    final source = bundle ?? rootBundle;
    final catalog =
        jsonDecode(await source.loadString('$assetRoot/catalog.json')) as Map;
    final runs = (catalog['runs'] as List)
        .map((r) => Map<String, dynamic>.from(r as Map))
        .toList();
    if (catalog['schemaVersion'] != 1 ||
        jsonEncode(runs.map((r) => r['goldRun']).toList()) !=
            jsonEncode(['run_001', 'run_002'])) {
      throw const FormatException('APK cần chứa đủ run_001 và run_002.');
    }
    final packages = <String, MobileE2ePackage>{};
    for (final run in runs) {
      final name = run['goldRun'] as String;
      if (run['file'] != '$name.rhe') {
        throw const FormatException('Đường dẫn gói run không hợp lệ.');
      }
      final bytes = await source.load('$assetRoot/${run['file']}');
      final package = MobileE2ePackage.decode(
        bytes.buffer.asUint8List(bytes.offsetInBytes, bytes.lengthInBytes),
        run['packageSha256'] as String,
      );
      if (package.manifest['schemaVersion'] != 2 ||
          package.manifest['goldRun'] != name ||
          jsonEncode(package.manifest['image']) != jsonEncode(run['image']) ||
          jsonEncode(package.manifest['model']) != jsonEncode(run['model'])) {
        throw const FormatException('Catalog và gói run không khớp.');
      }
      for (final input in run['inputs'] as List) {
        final filename = input['file'] as String;
        if (!RegExp(r'^run_00[12]_[a-z_]+\.json$').hasMatch(filename)) {
          throw const FormatException('Tên đầu vào không hợp lệ.');
        }
        final data = await source.load('$assetRoot/$filename');
        if (sha256.convert(Uint8List.sublistView(data)).toString() !=
            input['sha256']) {
          throw const FormatException('Đầu vào gold trong APK sai hash.');
        }
      }
      packages[name] = package;
    }
    return MobileE2eBundle._(runs, packages);
  }
}
