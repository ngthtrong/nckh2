import 'image_compressor.dart';
import 'image_compressor_native.dart'
    if (dart.library.js_interop) 'image_compressor_web.dart'
    as platform;

ImageCompressor createImageCompressor() => platform.createImageCompressor();
