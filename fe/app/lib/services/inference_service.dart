// Keep the FFI-backed implementation out of Flutter Web compilation.
export 'inference_service_web.dart'
    if (dart.library.io) 'inference_service_native.dart';
