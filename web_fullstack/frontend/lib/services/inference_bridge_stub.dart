import 'dart:typed_data';

import 'inference_contract.dart';

InferenceBridge createInferenceBridge() => const UnsupportedInferenceBridge();

class UnsupportedInferenceBridge implements InferenceBridge {
  const UnsupportedInferenceBridge();

  @override
  Future<Map<String, dynamic>> initialize(String modelUrl, String manifestUrl) {
    throw const InferenceException('AI trên trình duyệt chỉ hỗ trợ bản Flutter Web.');
  }

  @override
  Future<Map<String, dynamic>> predict(Uint8List imageBytes) {
    throw const InferenceException('AI trên trình duyệt chỉ hỗ trợ bản Flutter Web.');
  }
}

