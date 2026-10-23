import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Android build targets match every packaged ExecuTorch runtime', () {
    const targetAbi = {'android-arm64': 'arm64-v8a', 'android-x64': 'x86_64'};
    final properties = File('android/gradle.properties').readAsStringSync();
    final defaultTargets = RegExp(
      r'^target-platform=([^\r\n]+)',
      multiLine: true,
    ).firstMatch(properties)!.group(1)!.split(',');
    final gradle = File('android/app/build.gradle.kts').readAsStringSync();
    final allowedTargets = RegExp(
      r'val supportedTargetPlatforms = mapOf\(([^)]+)\)',
    ).firstMatch(gradle)!.group(1)!;
    final targets = {
      for (final match in RegExp(
        r'"([^"]+)" to "([^"]+)"',
      ).allMatches(allowedTargets))
        match.group(1)!: match.group(2)!,
    };

    // ZIP entry names are stored uncompressed in its central directory.
    final archive = latin1.decode(
      File('android/app/libs/executorch-1.4.1-xnnpack.aar').readAsBytesSync(),
    );
    final runtimeAbis = RegExp(
      r'jni/([^/]+)/libexecutorch\.so',
    ).allMatches(archive).map((match) => match.group(1)!).toSet();

    expect(defaultTargets, unorderedEquals(targetAbi.keys));
    expect(targets, targetAbi);
    expect(
      runtimeAbis,
      unorderedEquals(defaultTargets.map((target) => targetAbi[target])),
    );
    expect(
      gradle,
      contains(
        'require(targetPlatforms.all { it in supportedTargetPlatforms })',
      ),
    );
    expect(
      gradle,
      contains(
        'if (project.findProperty("split-per-abi")?.toString()?.toBoolean() != true)',
      ),
    );
    expect(
      gradle,
      contains(
        'abiFilters.addAll(targetPlatforms.map { supportedTargetPlatforms.getValue(it) })',
      ),
    );
  });
}
