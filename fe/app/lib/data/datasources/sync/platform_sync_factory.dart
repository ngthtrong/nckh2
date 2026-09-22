import 'platform_sync.dart';
import 'platform_sync_native.dart'
    if (dart.library.js_interop) 'platform_sync_web.dart'
    as platform;

PlatformSync createPlatformSync() => platform.createPlatformSync();
