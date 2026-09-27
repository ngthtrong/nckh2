// The native implementation imports dart:io and onnxruntime, both of which
// are unavailable to a Flutter Web build. Keep that dependency behind a
// conditional export so the rest of the app can use one stable API.
export 'inference_local_datasource_web.dart'
    if (dart.library.io) 'inference_local_datasource_native.dart';
