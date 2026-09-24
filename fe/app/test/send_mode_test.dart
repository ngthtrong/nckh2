import 'package:flutter_test/flutter_test.dart';
import 'package:app/send_mode.dart';

void main() {
  const base = (
    strongKbps: 1000,
    minUsefulKbps: 50,
    highConfidence: 0.90,
    preferTextWhenConfident: true,
  );

  test('offline → SMS fallback', () {
    expect(
      chooseMode(
          hasData: false,
          confidence: 0.99,
          throughputKbps: 0,
          strongKbps: base.strongKbps,
          minUsefulKbps: base.minUsefulKbps,
          highConfidence: base.highConfidence),
      SendMode.smsFallback,
    );
  });

  test('mạng mạnh + confident cao → chỉ text', () {
    expect(
      chooseMode(
          hasData: true,
          confidence: 0.95,
          throughputKbps: 5000,
          strongKbps: base.strongKbps,
          minUsefulKbps: base.minUsefulKbps,
          highConfidence: base.highConfidence),
      SendMode.textOnly,
    );
  });

  test('mạng mạnh + confident thấp → ảnh gốc để server xác minh', () {
    expect(
      chooseMode(
          hasData: true,
          confidence: 0.40,
          throughputKbps: 5000,
          strongKbps: base.strongKbps,
          minUsefulKbps: base.minUsefulKbps,
          highConfidence: base.highConfidence),
      SendMode.fullImage,
    );
  });

  test('preferTextWhenConfident=false → mạng mạnh luôn gửi ảnh gốc', () {
    expect(
      chooseMode(
          hasData: true,
          confidence: 0.99,
          throughputKbps: 5000,
          strongKbps: base.strongKbps,
          minUsefulKbps: base.minUsefulKbps,
          highConfidence: base.highConfidence,
          preferTextWhenConfident: false),
      SendMode.fullImage,
    );
  });

  test('mạng trung bình → ảnh nén', () {
    expect(
      chooseMode(
          hasData: true,
          confidence: 0.95,
          throughputKbps: 200,
          strongKbps: base.strongKbps,
          minUsefulKbps: base.minUsefulKbps,
          highConfidence: base.highConfidence),
      SendMode.compressedImage,
    );
  });

  test('mạng rất yếu (EDGE) → chỉ text', () {
    expect(
      chooseMode(
          hasData: true,
          confidence: 0.95,
          throughputKbps: 30,
          strongKbps: base.strongKbps,
          minUsefulKbps: base.minUsefulKbps,
          highConfidence: base.highConfidence),
      SendMode.textOnly,
    );
  });

  test('resolveOfflineMode', () {
    expect(resolveOfflineMode(SendMode.smsFallback, true), SendMode.smsFallback);
    expect(
        resolveOfflineMode(SendMode.smsFallback, false), SendMode.queuedOffline);
  });
}
