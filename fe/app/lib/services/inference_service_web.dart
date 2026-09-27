import 'dart:typed_data';

/// Result shape shared with the native inference service.
typedef ClassifyResult = ({String label, double confidence, int durationMs});

/// Web-safe no-op implementation.
///
/// The native service uses `onnxruntime`, which is FFI-only. Returning null
/// allows the legacy controller to remain buildable on Web without pretending
/// that an on-device model ran.
class InferenceService {
  bool get ready => false;

  Future<void> load() async {}

  Future<ClassifyResult?> classify(Uint8List jpegBytes) async => null;
}
