import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Capture once before timing, so platform/asset reads do not affect latency.
Future<Map<String, Object?>> benchmarkEnvironment() async {
  final manifest =
      jsonDecode(
            await rootBundle.loadString('assets/models/model_manifest.json'),
          )
          as Map<String, dynamic>;
  Map<String, Object?> environment;
  try {
    environment = Map<String, Object?>.from(
      await const MethodChannel(
            'rescue/benchmark_export',
          ).invokeMapMethod<String, Object?>('getEnvironment') ??
          {},
    );
  } on MissingPluginException {
    environment = {
      'platform': kIsWeb ? 'web' : defaultTargetPlatform.name,
      'deviceInfoAvailable': false,
      'appInfoAvailable': false,
    };
  } on PlatformException {
    environment = {
      'platform': kIsWeb ? 'web' : defaultTargetPlatform.name,
      'deviceInfoAvailable': false,
      'appInfoAvailable': false,
    };
  }
  return {'model': manifest, ...environment};
}
