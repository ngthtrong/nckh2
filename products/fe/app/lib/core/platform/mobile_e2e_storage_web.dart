// Giữ build web tương thích; không lưu hay giả chạy gói E2E Android trong trình duyệt.
import 'dart:typed_data';

class MobileE2eStorage {
  String get installationId => throw UnsupportedError('Chỉ hỗ trợ Android');
  static Future<MobileE2eStorage> open() async =>
      throw UnsupportedError('Chỉ hỗ trợ Android');
  String path(String name) => throw UnsupportedError('Chỉ hỗ trợ Android');
  Future<Uint8List?> readBytes(String name) async =>
      throw UnsupportedError('Chỉ hỗ trợ Android');
  Future<void> writeBytes(String name, Uint8List data) async =>
      throw UnsupportedError('Chỉ hỗ trợ Android');
  Future<Map<String, dynamic>?> readJson(String name) async =>
      throw UnsupportedError('Chỉ hỗ trợ Android');
  Future<void> writeJson(String name, Map<String, dynamic> data) async =>
      throw UnsupportedError('Chỉ hỗ trợ Android');
}
