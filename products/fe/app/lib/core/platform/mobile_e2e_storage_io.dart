// Lưu gói, ảnh và checkpoint theo session trong vùng riêng của app; không xóa dữ liệu báo cáo.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:path_provider/path_provider.dart';
import 'package:uuid/uuid.dart';

class MobileE2eStorage {
  final Directory folder;
  final String installationId;
  MobileE2eStorage._(this.folder, this.installationId);
  static Future<MobileE2eStorage> open() async {
    final root = await getApplicationSupportDirectory();
    final folder = Directory('${root.path}/mobile_e2e');
    await folder.create(recursive: true);
    final identity = File('${folder.path}/installation.txt');
    if (!await identity.exists()) {
      await identity.writeAsString(const Uuid().v4(), flush: true);
    }
    return MobileE2eStorage._(folder, (await identity.readAsString()).trim());
  }

  String path(String name) {
    if (!RegExp(r'^[A-Za-z0-9_.-]+$').hasMatch(name)) {
      throw ArgumentError('Tên file không an toàn');
    }
    return '${folder.path}/$name';
  }

  Future<Uint8List?> readBytes(String name) async {
    final file = File(path(name));
    return await file.exists() ? await file.readAsBytes() : null;
  }

  Future<void> writeBytes(String name, Uint8List bytes) async {
    final part = File('${path(name)}.part');
    await part.writeAsBytes(bytes, flush: true);
    await part.rename(path(name));
  }

  Future<Map<String, dynamic>?> readJson(String name) async {
    final bytes = await readBytes(name);
    return bytes == null
        ? null
        : Map<String, dynamic>.from(jsonDecode(utf8.decode(bytes)) as Map);
  }

  Future<void> writeJson(String name, Map<String, dynamic> data) => writeBytes(
    name,
    Uint8List.fromList(
      utf8.encode(const JsonEncoder.withIndent('  ').convert(data)),
    ),
  );
}
