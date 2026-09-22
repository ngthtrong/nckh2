import 'dart:typed_data';

abstract interface class InferenceBridge {
  Future<Map<String, dynamic>> initialize(String modelUrl, String manifestUrl);

  Future<Map<String, dynamic>> predict(Uint8List imageBytes);
}

class InferenceException implements Exception {
  const InferenceException(this.message);

  final String message;

  @override
  String toString() => 'InferenceException: $message';
}
