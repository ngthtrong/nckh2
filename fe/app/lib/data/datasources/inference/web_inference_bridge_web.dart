import 'dart:js_interop';
import 'dart:typed_data';

import 'web_inference_bridge.dart';

@JS('floodAi.initialize')
external JSPromise<JSAny?> _initialize(JSString modelUrl, JSString manifestUrl);

@JS('floodAi.predict')
external JSPromise<JSAny?> _predict(JSUint8Array imageBytes);

InferenceBridge createInferenceBridge() => const BrowserInferenceBridge();

class BrowserInferenceBridge implements InferenceBridge {
  const BrowserInferenceBridge();

  @override
  Future<Map<String, dynamic>> initialize(
    String modelUrl,
    String manifestUrl,
  ) async {
    final value = await _initialize(modelUrl.toJS, manifestUrl.toJS).toDart;
    return _asMap(value);
  }

  @override
  Future<Map<String, dynamic>> predict(Uint8List imageBytes) async {
    final value = await _predict(imageBytes.toJS).toDart;
    return _asMap(value);
  }

  Map<String, dynamic> _asMap(JSAny? value) {
    final converted = value?.dartify();
    if (converted is! Map) {
      throw const InferenceException('ONNX Web trả về dữ liệu không hợp lệ.');
    }
    return Map<String, dynamic>.from(converted);
  }
}
