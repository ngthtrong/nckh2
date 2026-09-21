import 'package:flutter_test/flutter_test.dart';
import 'package:flood_rescue_web/services/send_mode_selector.dart';

void main() {
  test('uses original image on a fast connection', () {
    expect(
      selectSendMode(bytesPerSecond: 300 * 1024, hasImage: true),
      SendMode.original,
    );
  });

  test('uses compressed image on a slow connection', () {
    expect(
      selectSendMode(bytesPerSecond: 64 * 1024, hasImage: true),
      SendMode.compressed,
    );
  });

  test('uses text only on a very slow connection or without image', () {
    expect(
      selectSendMode(bytesPerSecond: 10 * 1024, hasImage: true),
      SendMode.textOnly,
    );
    expect(
      selectSendMode(bytesPerSecond: 1024 * 1024, hasImage: false),
      SendMode.textOnly,
    );
  });
}
